"""Sanity checks for the simulation.

These are not unit tests for their own sake. Each one rules out a specific way
the headline result could be an artifact of my code rather than the mechanism
I claim to show. Run with: python test_simulation.py
"""

import numpy as np

from simulation import SimConfig, disparity_ratio, run_simulation


def final_patrol(df, district="District A"):
    last = df["round"].max()
    return float(df[(df["round"] == last) & (df["district"] == district)]["patrol_share"].iloc[0])


def mean_final_patrol(seeds=40, **kw):
    return float(np.mean([final_patrol(run_simulation(SimConfig(seed=s, **kw))) for s in range(seeds)]))


def check(name, condition, detail=""):
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    return condition


results = []

# 1. Arrests can never exceed the incidents that generated them.
df = run_simulation(SimConfig(seed=1))
results.append(check("arrests never exceed incidents", bool((df["arrests"] <= df["incidents"]).all())))

# --- The three regimes. Underlying incident rates are EQUAL in all of them, so
# --- any divergence is produced entirely by the allocation rule.

# 2. Proportional (concentration = 1.0) preserves the initial 60/40 imbalance.
m = mean_final_patrol(concentration=1.0, train_on="arrests")
results.append(check("proportional allocation preserves imbalance", abs(m - 0.60) < 0.05,
                     f"0.60 -> {m:.3f} mean"))

# 3. Concentrating (> 1.0) amplifies it toward capture.
m = mean_final_patrol(concentration=2.0, train_on="arrests")
results.append(check("concentrating allocation amplifies imbalance", m > 0.85,
                     f"0.60 -> {m:.3f} mean"))

# 4. Hedged (< 1.0) erases it.
m = mean_final_patrol(concentration=0.5, train_on="arrests")
results.append(check("hedged allocation erases imbalance", m < 0.55, f"0.60 -> {m:.3f} mean"))

# 5. Training on ground-truth incidents self-corrects regardless of the start.
df = run_simulation(SimConfig(train_on="incidents", seed=1))
results.append(check("ground-truth signal self-corrects", abs(final_patrol(df) - 0.5) < 0.02,
                     f"-> {final_patrol(df):.3f}"))
r = disparity_ratio(df)
results.append(check("no disparity under ground truth", 0.9 < r < 1.1, f"ratio {r:.2f}x"))

# 5b. REGRESSION. Total capture must not report as parity. An earlier version of
#     disparity_ratio dropped zero rates before comparing, so a district with 100%
#     of enforcement scored 1.00x -- the exact opposite of the truth.
df_cap = run_simulation(SimConfig(initial_patrol_share=[0.9, 0.1], concentration=2.5,
                                  train_on="arrests", seed=1))
r_cap = disparity_ratio(df_cap)
results.append(check("total capture does not report as parity", r_cap > 10,
                     f"ratio {r_cap:.1f}x at {final_patrol(df_cap):.0%} enforcement share"))

# 5c. The ratio is directional: swapping the arguments inverts it.
results.append(check("disparity ratio is directional",
                     abs(disparity_ratio(df_cap, "District B", "District A") - 1 / r_cap) < 1e-9))

# 6. THE IMPORTANT ONE. With a symmetric start, amplification must not
#    systematically favour District A. If it does, the divergence in check 3 is
#    a bug in my allocator, not a feedback loop.
#    Under amplification each run is effectively a coin flip, so this needs real
#    statistical power: at 40 seeds the standard error is 0.079 and a 0.58 result
#    is indistinguishable from fair. 400 seeds gives SE 0.025.
N_SEEDS = 400
m = mean_final_patrol(seeds=N_SEEDS, initial_patrol_share=[0.5, 0.5],
                      concentration=2.0, train_on="arrests")
z = abs(m - 0.5) / (0.25 / N_SEEDS) ** 0.5
results.append(check("symmetric start picks a winner at random, not District A",
                     z < 1.96, f"mean share {m:.3f} over {N_SEEDS} seeds, z = {z:.2f}"))

# 7. Full exploration pins allocation to an even split whatever else is set.
df = run_simulation(SimConfig(exploration=1.0, concentration=2.0, train_on="arrests", seed=1))
results.append(check("exploration=1.0 forces even patrol", abs(final_patrol(df) - 0.5) < 1e-9))

# 8. Disparity falls as exploration rises. Averaged over seeds to avoid reading
#    sampling noise as a trend.
ratios = [float(np.mean([disparity_ratio(run_simulation(
              SimConfig(exploration=e, concentration=2.0, train_on="arrests", seed=s)))
              for s in range(15)])) for e in (0.0, 0.25, 0.5, 0.75, 1.0)]
results.append(check("disparity decreases monotonically with exploration",
                     all(a >= b - 1e-6 for a, b in zip(ratios, ratios[1:])),
                     " -> ".join(f"{r:.2f}" for r in ratios)))

print(f"\n{sum(results)}/{len(results)} checks passed")
raise SystemExit(0 if all(results) else 1)