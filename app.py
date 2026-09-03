"""
What does your allocation rule do to an imbalance it inherits?

Run with:  streamlit run app.py
"""

import math
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from simulation import SimConfig, disparity_ratio, run_simulation

st.set_page_config(page_title="Allocation rule check", layout="wide")


@st.cache_data
def load_calibration() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).parent / "data" / "aclu_marijuana_arrests_2018.csv")


CAL = load_calibration()

st.title("What does your allocation rule do to an imbalance it inherits?")
st.caption(
    "Two districts with identical underlying incident rates. One starts with more "
    "enforcement attention than the other. You choose how the rule responds to its own "
    "arrest records, and watch what happens to the gap."
)

with st.sidebar:
    st.header("Starting imbalance")
    options = ["Custom"] + CAL["state"].tolist()
    choice = st.selectbox(
        "Calibrate to observed disparity", options, index=options.index("United States"),
        help="Sets the starting gap to match a real jurisdiction's recorded Black/white "
             "marijuana possession arrest ratio (ACLU 2018).",
    )
    if choice == "Custom":
        observed = None
        start_a = st.slider("District A's initial share of enforcement", 0.50, 0.95, 0.60, 0.01)
    else:
        observed = float(CAL.loc[CAL["state"] == choice, "black_white_rate_ratio"].iloc[0])
        start_a = observed / (1.0 + observed)
        st.caption(
            f"{choice} recorded a **{observed:.2f}×** disparity. Reproducing that under this "
            f"model implies a **{start_a:.0%}/{1 - start_a:.0%}** split in enforcement attention."
        )

    st.header("The rule")
    concentration = st.slider(
        "Concentration", 0.0, 3.0, 1.0, 0.05,
        help="How sharply enforcement follows the leading district. 1.0 is strict "
             "proportional allocation. Above 1.0 approaches send-everyone-to-the-hotspot.",
    )
    train_on = st.radio(
        "Signal the rule learns from",
        ["arrests", "incidents"],
        format_func=lambda v: "Recorded arrests" if v == "arrests" else "Underlying incidents (unobtainable)",
        help="Arrests record where enforcement went. Underlying incidents are what actually "
             "happened. No real system can observe the second one.",
    )
    exploration = st.slider("Guaranteed even coverage", 0.0, 1.0, 0.0, 0.05)

    st.header("Mechanics")
    rounds = st.slider("Rounds", 5, 100, 30, 5)
    detection = st.slider("Detection rate at even enforcement", 0.01, 0.50, 0.10, 0.01)
    seed = st.number_input("Random seed", 0, 9999, 1, 1)
    st.caption("Underlying incident rates are held equal — SAMHSA finds Black and white "
               "marijuana use rates do not significantly differ. Any gap below is the rule's doing.")

cfg = SimConfig(
    true_incidents=[100.0, 100.0],
    initial_patrol_share=[start_a, 1.0 - start_a],
    rounds=int(rounds),
    detection_base=float(detection),
    exploration=float(exploration),
    concentration=float(concentration),
    train_on=train_on,
    seed=int(seed),
)
df = run_simulation(cfg)

final = df[df["round"] == df["round"].max()].set_index("district")
final_a = float(final.loc["District A", "patrol_share"])
ratio = disparity_ratio(df)

if concentration < 0.95:
    regime, verdict = "Hedged", "pulls the gap back toward parity"
elif concentration <= 1.05:
    regime, verdict = "Proportional", "holds the gap it started with, indefinitely"
else:
    regime, verdict = "Concentrating", "widens the gap it started with"

st.subheader(f"{regime} rule — {verdict}")

c1, c2, c3 = st.columns(3)
c1.metric("Enforcement share, District A", f"{final_a:.0%}", f"{final_a - start_a:+.0%} from start")
ratio_label = ("\u2014" if math.isnan(ratio)
               else "total capture" if math.isinf(ratio)
               else f"{ratio:.2f}\u00d7")
c2.metric("Simulated disparity", ratio_label)
if observed is None:
    c3.metric("Starting disparity", f"{start_a / (1 - start_a):.2f}\u00d7")
else:
    c3.metric(f"{choice}, recorded 2018", f"{observed:.2f}\u00d7")

if math.isfinite(ratio):
    st.markdown(
        f"Residents of both districts did the same things at the same rate. After {rounds} "
        f"rounds, a person in District A was **{ratio:.2f} times** as likely to be arrested "
        f"for it."
    )
else:
    st.markdown(
        "Residents of both districts did the same things at the same rate. District B now "
        "receives so little enforcement that it records no arrests at all, so the ratio is "
        "undefined rather than equal."
    )

left, right = st.columns(2)
with left:
    st.markdown("**Where enforcement goes**")
    st.altair_chart(
        alt.Chart(df).mark_line(strokeWidth=2).encode(
            x=alt.X("round:Q", title="Round"),
            y=alt.Y("patrol_share:Q", title="Share of enforcement",
                    scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")),
            color=alt.Color("district:N", title=None),
        ).properties(height=300), width="stretch")
with right:
    st.markdown("**Share of incidents that ended in an arrest**")
    st.altair_chart(
        alt.Chart(df).mark_line(strokeWidth=2).encode(
            x=alt.X("round:Q", title="Round"),
            y=alt.Y("enforcement_rate:Q", title="Cumulative arrests / incidents",
                    axis=alt.Axis(format="%")),
            color=alt.Color("district:N", title=None),
        ).properties(height=300), width="stretch")

with st.expander("What this model assumes, and what it cannot tell you"):
    st.markdown(
        """
**The load-bearing assumption.** Arrests scale with enforcement attention: double the
attention, record roughly double the arrests for the same underlying behaviour. Everything
follows from that. It is reasonable for offences discovered through proximity and stops,
and much weaker for offences that reach police through victim reports.

**The real numbers are a starting point, not a result.** The ACLU figures record what
*happened*. This model does not explain why. Converting an observed ratio into an implied
enforcement split assumes the entire gap is produced by differential attention under equal
underlying behaviour — the second half is supported by SAMHSA usage data, the first half is
an assumption this model makes and cannot test. Real disparities also run through charging
decisions, prosecutorial discretion, differential reporting, and more.

**Why the proportional case is not obvious.** At concentration 1.0 both districts' arrest
counts grow by the same expected factor each round, so their shares stay put. The rule
never corrects the imbalance it inherited and never explodes it either. I expected a
runaway and the simulation corrected me; amplification needs concentration above 1.0.

**The ground-truth setting is a control, not an option.** No department can observe
underlying incidents. It shows what the rule would do with a signal uncontaminated by its
own past decisions.

**What this is not.** Not evidence about any real department, tool, or vendor. Race appears
nowhere in the simulation — the districts are abstract, and the bridge to real disparities
is the calibration step and the argument around it, not a computed finding. Nothing here
shows any allocation rule was chosen with intent.

Data: ACLU, *A Tale of Two Countries* (2020), Table 7 — FBI UCR and Census. See
`data/SOURCE.md` for gaps and caveats.
        """
    )