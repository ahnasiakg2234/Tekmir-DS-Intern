# AI note

**Did I use AI?** Yes. I used Claude to do most of the typing: the simulation module, the
Streamlit app, the test suite, and a first pass at this README.

**How.** I brought the domain and the framing. I cycled through three ideas — mental
health access, environmental justice, policing, and used Claude to pressure-test each
one against what was actually buildable in the time. Two died on data access, which was
the right reason to kill them. Once committed, I used it as a fast pair of hands and
argued with its output.

**A moment it helped.** Scoping. My original framing was "how are minority communities
targeted by automated policing." Claude pushed back that *targeting* is a causal claim
that cross-sectional data cannot support, and that the defensible version is a mechanism
demonstration with a stated assumption. That reframe is why this artifact has a limit
section it can actually defend instead of an implied claim it cannot.

**What I decided or verified myself.** The headline finding was wrong on the first pass.
Claude confidently predicted that a proportional allocation rule would produce runaway
amplification of an initial patrol imbalance. I insisted on writing sanity checks before
building any UI, and check 2 failed: patrol drifted 0.60 → 0.583 instead of exploding.
The reason is that proportional allocation over cumulative arrest counts is a Pólya urn,
which preserves shares in expectation. Amplification needs a concentrating rule.

I had two options: quietly tune parameters until the demo looked dramatic, or change the
claim. I changed the claim, and the app is better for it — "this rule locks in bias
permanently" is a more useful finding than "bias explodes."

Related: one check kept failing at 40 seeds (mean 0.583, expected 0.50). Rather than
loosen the threshold, I checked the statistics — z = 1.60, not significant — and raised
the seed count to 400 instead, which resulted in z=.50. The test was underpowered, not the code wrong.
