"""
What does your patrol allocation rule do to an imbalance it inherits?

Run with:  streamlit run app.py
"""

import altair as alt
import pandas as pd
import streamlit as st

from generated_data import SimConfig, disparity_ratio, run_simulation

st.set_page_config(page_title="Allocation rule check", layout="wide")

st.title("What does your allocation rule do to an imbalance it inherits?")
st.caption(
    "Two districts. Identical underlying incident rates. The only difference is "
    "how much patrol each one started with, and how the rule responds to its own "
    "arrest records. Synthetic data throughout — this is a check on a rule, not a "
    "description of any real place."
)

with st.sidebar:
    st.header("The rule")
    concentration = st.slider(
        "Concentration", 0.0, 3.0, 1.0, 0.05,
        help="How sharply patrol follows the leading district. 1.0 is strict "
             "proportional allocation. Above 1.0 approaches send-everyone-to-the-hotspot.",
    )
    train_on = st.radio(
        "Signal the rule learns from",
        ["arrests", "incidents"],
        format_func=lambda v: "Recorded arrests" if v == "arrests" else "Underlying incidents (unobtainable)",
        help="Arrests are a record of where patrol went. Underlying incidents are what "
             "actually happened. No real system can observe the second one directly.",
    )
    exploration = st.slider(
        "Guaranteed even coverage", 0.0, 1.0, 0.0, 0.05,
        help="Fraction of patrol allocated evenly regardless of the signal.",
    )

    st.header("Starting conditions")
    start_a = st.slider("District A's initial patrol share", 0.50, 0.90, 0.60, 0.01)
    rounds = st.slider("Rounds", 5, 100, 30, 5)
    detection = st.slider(
        "Detection rate at even patrol", 0.01, 0.50, 0.10, 0.01,
        help="Chance an incident becomes an arrest when a district gets exactly "
             "its proportional share of patrol.",
    )
    seed = st.number_input("Random seed", 0, 9999, 1, 1)

    st.header("Underlying incidents")
    st.caption("Equal by default. Any disparity below is produced by the rule, not by this.")
    rate_a = st.number_input("District A per round", 10, 500, 100, 10)
    rate_b = st.number_input("District B per round", 10, 500, 100, 10)

cfg = SimConfig(
    true_incidents=[float(rate_a), float(rate_b)],
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
drift = final_a - start_a

if concentration < 0.95:
    regime, verdict = "Hedged", "pulls allocation back toward an even split"
elif concentration <= 1.05:
    regime, verdict = "Proportional", "holds the imbalance it started with, indefinitely"
else:
    regime, verdict = "Concentrating", "amplifies the imbalance it started with"

st.subheader(f"{regime} rule — {verdict}")

c1, c2, c3 = st.columns(3)
c1.metric("District A patrol share", f"{final_a:.0%}", f"{drift:+.0%} from start")
c2.metric("Enforcement disparity", f"{ratio:.2f}\u00d7")
c3.metric(
    "Underlying incident share",
    f"{df[df.district == 'District A'].incidents.sum() / df.incidents.sum():.0%}",
)

if rate_a == rate_b:
    st.markdown(
        f"Residents of the two districts did the same things. A person in the "
        f"more heavily patrolled district was **{ratio:.2f} times** as likely to be "
        f"arrested for it."
    )

left, right = st.columns(2)

with left:
    st.markdown("**Where patrol goes**")
    st.altair_chart(
        alt.Chart(df).mark_line(strokeWidth=2).encode(
            x=alt.X("round:Q", title="Round"),
            y=alt.Y("patrol_share:Q", title="Share of patrol",
                    scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")),
            color=alt.Color("district:N", title=None),
        ).properties(height=300),
        width="stretch",
    )

with right:
    st.markdown("**Share of incidents that ended in an arrest**")
    st.altair_chart(
        alt.Chart(df).mark_line(strokeWidth=2).encode(
            x=alt.X("round:Q", title="Round"),
            y=alt.Y("enforcement_rate:Q", title="Cumulative arrests / incidents",
                    axis=alt.Axis(format="%")),
            color=alt.Color("district:N", title=None),
        ).properties(height=300),
        width="stretch",
    )

with st.expander("What this model assumes, and what it cannot tell you"):
    st.markdown(
        """
**The load-bearing assumption.** Arrests scale with patrol: send twice the officers,
record roughly twice the arrests for the same underlying behaviour. Everything here
follows from that. It is well supported for offences that are roughly evenly
distributed and discovered through proximity, and much weaker for offences that come
to police through victim reports.

**Why the proportional case is not obvious.** At concentration 1.0 both districts'
arrest counts grow by the same expected factor each round, so their shares stay put.
The rule never corrects the imbalance it inherited and never explodes it either. I
expected a runaway here and the simulation corrected me; amplification needs
concentration above 1.0.

**The ground-truth setting is a control, not an option.** No department can observe
underlying incidents. It is in the app to show what the rule would do with a signal
that is not contaminated by its own past decisions.

**What this is not.** It is not evidence about any real department, tool, or vendor.
It is not calibrated to real arrest rates. Race appears nowhere in the model — the
districts are abstract, and the connection to real disparities is an argument made in
the README, not a result computed here. Nothing here shows that any allocation rule
was chosen with intent.
        """
    )