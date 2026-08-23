"""
Predictive patrol allocation: a feedback loop simulation.

ALL DATA HERE IS SYNTHETIC. Nothing in this module reads, contains, or
approximates real crime records, arrest records, or personal data. The point
is to demonstrate a mechanism, not to describe any real police department.

The mechanism, in one sentence: if a system allocates patrol using *arrests*
as its signal, and arrests only happen where patrol already is, then the
system's own output becomes its next input and small initial differences
compound.
"""

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd


@dataclass
class SimConfig:
    """Parameters for one run of the simulation."""

    district_names: List[str] = field(default_factory=lambda: ["District A", "District B"])

    # Expected underlying incidents per district per round. Equal by default:
    # the demonstration is that disparity emerges WITHOUT any difference here.
    true_incidents: List[float] = field(default_factory=lambda: [100.0, 100.0])

    # Where patrol starts. Represents historical allocation, not present policy.
    initial_patrol_share: List[float] = field(default_factory=lambda: [0.60, 0.40])

    rounds: int = 30

    # P(an incident becomes an arrest) when a district receives its exactly
    # proportional share of patrol. Scales linearly with patrol from there.
    detection_base: float = 0.10

    # Floor on allocation: 0.0 = pure exploitation of the signal,
    # 1.0 = ignore the signal entirely and split patrol evenly.
    exploration: float = 0.0

    # How sharply the allocator favours the leading district. See _allocate.
    concentration: float = 1.0

    # "arrests"   -> the system learns from its own enforcement output (biased)
    # "incidents" -> the system learns from underlying incidents (ground truth)
    train_on: str = "arrests"

    # How many rounds' worth of prior records the system was trained on before it
    # was switched on. Small values leave the Polya urn free to drift a long way
    # from its starting share, which swamps the effect being demonstrated.
    prior_rounds: float = 10.0

    seed: int = 0


def _allocate(signal: np.ndarray, exploration: float, concentration: float) -> np.ndarray:
    """Turn an accumulated signal into patrol shares.

    `concentration` is the exponent applied to the signal before normalising,
    and it is the parameter that matters most:

      < 1.0  hedged      -- pulls allocation back toward an even split
      = 1.0  proportional -- patrol in proportion to recorded arrests
      > 1.0  concentrating -- favours the leading district superlinearly,
                             approaching "send everyone to the top hotspot"

    At exactly 1.0 the loop is a Polya urn: each district's signal grows by the
    same expected factor each round, so an initial imbalance is preserved rather
    than amplified. Amplification requires concentration > 1.0. This was not
    obvious to me until the simulation contradicted my expectation.
    """
    n = len(signal)
    safe = np.clip(signal, 1e-12, None)
    weights = safe**concentration
    raw = weights / weights.sum()
    return (1.0 - exploration) * raw + exploration * (1.0 / n)


def run_simulation(cfg: SimConfig) -> pd.DataFrame:
    """Run the loop and return one row per district per round."""
    if cfg.train_on not in ("arrests", "incidents"):
        raise ValueError("train_on must be 'arrests' or 'incidents'")

    rng = np.random.default_rng(cfg.seed)
    n = len(cfg.district_names)
    true_rates = np.asarray(cfg.true_incidents, dtype=float)

    init_share = np.asarray(cfg.initial_patrol_share, dtype=float)
    init_share = init_share / init_share.sum()

    # Seed the signal with roughly one round's worth of history, split according
    # to the initial patrol allocation. This stands in for "the records the
    # system was trained on before it was switched on".
    prior_strength = float(true_rates.sum() * cfg.detection_base * cfg.prior_rounds)
    signal = init_share * prior_strength

    rows = []
    for t in range(1, cfg.rounds + 1):
        patrol = _allocate(signal, cfg.exploration, cfg.concentration)

        # Detection scales with patrol relative to an even split.
        p_detect = np.clip(cfg.detection_base * patrol * n, 0.0, 1.0)

        incidents = rng.poisson(true_rates)
        arrests = rng.binomial(incidents, p_detect)

        signal = signal + (arrests if cfg.train_on == "arrests" else incidents)

        for i, name in enumerate(cfg.district_names):
            rows.append(
                {
                    "round": t,
                    "district": name,
                    "patrol_share": patrol[i],
                    "incidents": int(incidents[i]),
                    "arrests": int(arrests[i]),
                    "detection_prob": p_detect[i],
                }
            )

    df = pd.DataFrame(rows)
    df["cum_arrests"] = df.groupby("district")["arrests"].cumsum()
    df["cum_incidents"] = df.groupby("district")["incidents"].cumsum()
    # The number that matters: of everything that actually happened here,
    # what fraction resulted in an arrest?
    df["enforcement_rate"] = df["cum_arrests"] / df["cum_incidents"].replace(0, np.nan)
    return df


def disparity_ratio(df: pd.DataFrame, numerator: str = "District A",
                    denominator: str = "District B") -> float:
    """Final-round enforcement rate of one district divided by another's.

    Reads as: someone doing the same thing in `numerator` is this many times more
    likely to be arrested than in `denominator`.

    Directional on purpose. An earlier version returned max/min, which took the
    absolute value of random drift and so reported a ratio above 1.0 even when the
    districts were treated identically, biasing the average upward.

    Returns inf when the denominator district records no arrests at all — total
    capture is not parity, and an earlier version reported exactly that by
    dropping zero rates before comparing.
    """
    final = df[df["round"] == df["round"].max()].set_index("district")
    num = float(final.loc[numerator, "enforcement_rate"])
    den = float(final.loc[denominator, "enforcement_rate"])
    if not np.isfinite(num) or not np.isfinite(den):
        return float("nan")
    if den == 0:
        return float("inf") if num > 0 else float("nan")
    return num / den