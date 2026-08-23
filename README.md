# Does your allocation rule manufacture disparity?

**Track C** — tiny simulation / model-behaviour check.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
python3 test_simulation.py   #verification checks!!
```

## What it is

One Streamlit page answering one question: if a patrol allocation rule learns from
*arrest records*, what does it do to an imbalance it inherits? Two districts, identical
underlying incident rates, one starts with more patrol. You slide the rule's
**concentration** — how sharply patrol follows the leading district and watch.
In basic terms, it decides where enforcement allocation goes based on learned behavior from past arrest records. It's a simulation of a patrol allocation rule that learns from arrest data, and it shows that how aggressively the rule follows its own signal determines whether an existing racial disparity gets erased, frozen, or blown up.

Three regimes:

- **below 1.0, hedged** — erases the inherited imbalance
- **1.0, proportional** — *holds it, indefinitely*. A 60/40 split stays 60/40, and identical behaviour is arrested 1.40× more often on one side forever.
- **above 1.0, concentrating** — amplifies it to capture: 100% of patrol and 21× disparity at 2.0.

## Who it's for

Anyone specifying or reviewing a hotspot rule before it ships. How sharply to follow the
signal gets treated as a tuning detail. It decides whether the system launders its own
history.

## Data

None. Fully synthetic, seeded, generated at runtime. No real crime, arrest, or personal
records — deliberate: the question needs a counterfactual (true incident rates) that no
real dataset contains.

## Assumptions

Arrests scale linearly with patrol. That one assumption drives everything. Reasonable for
proximity-discovered offences, weak for victim-reported ones.

## Issues noticed

I expected proportional allocation to run away. It does not — it is a Pólya urn and
preserves shares in expectation. Amplification requires concentration above 1.0. The test
suite caught this and the model changed. Individual runs still drift (mean 0.611 from a
0.60 start across 40 seeds).

Race appears nowhere in the model. The link to real disparities is an argument, not a
result computed here.

## Next

A victim-reported crime channel; more than two districts; detection calibrated to a
published stop-rate study.