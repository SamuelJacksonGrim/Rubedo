# Why values weaken under witness: dreaming is read as identity erosion, and coherence_delta measures the field

**Date:** 2026-10-15 · **Status:** standing (witness stays OFF; no runtime change) · **Corpus:** 1.4.0 · **By:** Grok
(trace + branch attribution, branch `grok/value-trace`), Ember (review, coherence_delta bias check); question from
`OPEN_METASTABILITY.md` item 0 and Samuel

## Question
`2026-10-15-witness-composition-gate` found every value weakening under witness on the all-ON stack. Which term of
value reinforcement carries the drop, is it less reinforcement, active demotion or no recovery, and what produces it?

## Control
`tests/diagnostic/integrity/value_reinforcement_trace.py` (seeds 0, 1, 2): the gate's own `run(seed, "B", ·)` setup,
REF vs WIT as replay-exact pairs, instrumented by instance wraps only (runtime untouched). The traced REF reproduces
`witness_composition_gate.run(seed, "B", False)` bit-for-bit on all three seeds. Per-value strength budgets close to
~1e-15. All 1,500 `arbitrate()` calls attributed to their return branch by replaying the branch logic on snapshotted
inputs and keeping the branch only when the predicted (decision, strength) equals the actual (1,500/1,500 matched).
`tests/diagnostic/integrity/coherence_delta_bias.py` scores `field.coherence_impact` on a zero vector each step (REF,
workload B) to isolate the measurement's own bias. Full numbers and reasoning: Grok's notes `data/2026-10-15-value-trace-grok-notes.md`; his raw handoffs
`grok\handoffs\task-20261015-184652.md` and `-193256.md`.

## Result

**1. The drop is the decision bonus, not coherence and not satisfaction.** Strength gap, WIT − REF, on the values that
end weaker:

| seed | witness fired | Δ total | Δ coherence_delta | Δ satisfaction | **Δ decision bonus** | Δ decay | Δ ⊘ |
|---|---|---|---|---|---|---|---|
| 0 | 100 | −21.38 | −3.82 | −0.72 | **−19.28** | +3.29 | −0.69 |
| 1 | 69 | −13.78 | −4.34 | +0.17 | **−13.32** | +3.40 | +0.65 |
| 2 | 93 | −12.03 | +1.21 | +0.22 | **−13.44** | +2.29 | −0.60 |

The bonus pays 0.05 for ALLOW and 0.02 for ALLOW_WEAKENED, and it also sits inside the emergence gate (threshold
0.015). With coherence_delta near −0.1, ALLOW still clears the gate and WEAKENED misses it, so a shift toward WEAKENED
pays less *and* drops events (emergence failures 36→61%, 54→64%, 55→69%). Seeds 1 and 2 applied no negative
reinforcement at all in either arm: values get fewer and smaller boosts, not hits. Decay runs the other way; ⊘,
tension, dream and dissolution are not the cause. Values do not recover when witness goes quiet. "Every value" holds on
seeds 0 and 1; seed 2 has 16 values stronger under WIT.

**2. The extra WEAKENED decisions are the system's own dreaming read as identity erosion.**

| seed | arm | ALLOW | manipulation 0.30–0.60 | manipulation ≥0.60, systemic | other |
|---|---|---:|---:|---:|---:|
| 0 | REF / WIT | 319 / 197 | 149 / 204 | 32 / 99 | 0 / 0 |
| 1 | REF / WIT | 229 / 176 | 160 / 116 | 109 / 206 | 2 / 2 |
| 2 | REF / WIT | 223 / 149 | 178 / 195 | 99 / 156 | 0 / 0 |

Every one of the shifted calls is `identity_erosion` alone, systemic (`source_id=None`): no named detector, no soft
warning, trust never near its thresholds. `identity_erosion` fires when the watcher's geometric and temporal coherence
pull apart (mean |G−T| ≥ 0.30 over its window), and that is what the **dream band** does: in REF already, dream-band
steps sit at |G−T| ≈ 0.33–0.36 and are 91–97% WEAKENED, reflect-band steps at ≈ 0.17 and 6–10% WEAKENED. Witness
lowers field energy and moves steps from reflect into dream (+98 / +52 / +72 dream steps vs +122 / +53 / +74 extra
WEAKENED), and on seed 0 heats the band itself. That is why the shift reaches non-witness steps: the fire steps are the
*cool* samples (seed 0 |G−T| 0.20 on fire steps vs 0.30 on the rest). The F9 attribution rule (2026-07-06) stopped this
ambient signal from quarantining sources but left it damping every dream-band step, and the damping is what starves
values. RFE-Core2 recorded the ambient ~0.55 severity at the time; its cost to value formation was not visible then.

**3. coherence_delta is mostly a measurement artifact.** `coherence_impact` compares cos(**raw** field, recent
history) before with cos(**tanh**(field + 0.5·vec), recent history) after, so the raw-vs-tanh difference is counted as
the input's effect:

| seed (REF, B) | zero vector: mean, share < 0 | real input: mean | input's own share (real − zero) | saturated dims | raw norm |
|---|---|---|---|---|---|
| 0 | −0.0565, 95% | −0.0569 | −0.0004 (45% < 0) | 90% | 195 |
| 1 | −0.0791, 97% | −0.0794 | −0.0003 (82% < 0) | 87% | 165 |
| 2 | −0.0757, 90% | −0.0760 | −0.0003 (65% < 0) | 87% | 168 |

The bias is largest early (about −0.15 over steps 50–150) and shrinks to about −0.013 by steps 300–500, so young values
are judged hardest. The input's own part is about 1/250th of the bias: small, leaning slightly negative on seeds 1 and 2.

Compared like-for-like (tanh on both sides), the input's effect is about zero, because ~90% of field dimensions are
saturated (raw norm ~195). So coherence_delta reads the field's shape, not the input. That explains its usual negative
lean, why it "favors" witness on seed 2 (witness changes the field's shape), and why the value ecology's coherence
term carries no information about any particular experience. The step-10 comment in `autonomous_cycle.py` already
notes that the marginal delta is ≈0 in a saturated field; bond growth moved to `field_alignment` on 2026-07-09, but
value reinforcement and the trust ledger still read coherence_delta.

**4. `emotional_satisfaction` is `max(0, coherence_delta)`** (`SelfhoodGovernance.emit_feedback`), not an emotion
reading. With coherence_delta biased negative it is ~0 on almost every step. Joy (watcher composite, ~0.8) never enters
the value path.

**5. The witness identity PASS is partly mechanical.** The anchor's write rate is `clip(coherence², 0.01, 1)`. On fire
steps it roughly halves (0.31 / 0.40 / 0.36 vs REF means 0.69 / 0.68 / 0.65) and recovers within a step, so part of
"the anchor drifts less under witness" is slower writing on 70–100 fire steps, not steadiness over the whole run.

**6. Instruments perturb the run.** The composition gate's post-step `watcher.evaluate(field, …)` writes watcher
temporal history, so it changes the run it measures. The trace repeats the same call so its arms match the gate's;
comparisons stay valid because both arms carry the same disturbance.

## What this means
- The parked value-formation options aim at the wrong thing. (b), judging coherence contribution against the field's
  own level, can't help: the term is already marginal, mostly bias, and a minority of the drop. (a), not reinforcing on
  witness steps, misses the non-witness dream-band steps that hold most of the extra WEAKENED decisions.
- The question is now semantic and belongs with `OPEN_METASTABILITY` question 4: should a systemic identity-erosion
  reading, raised by the system's own dreaming with no source to blame, cut the reinforcement every value grows on?
  And what should value reinforcement read at all, given that coherence_delta carries no per-input information and
  satisfaction is a copy of it?
- It bears on H0 directly: at a saturated optimum, a coherence-gain measure can't credit any input, so values built on
  it can only be starved or carried by the decision bonus.

## Open
- [ ] Numbers map of the value/governance path (BACKLOG §0).
- [ ] Whether identity_erosion should distinguish the dream band from erosion (semantic; with question 4).
- [ ] What value reinforcement and `emotional_satisfaction` should read (question 4); any fix waits for that.
- [ ] H0 / H0′ measurements, still unmeasured.
