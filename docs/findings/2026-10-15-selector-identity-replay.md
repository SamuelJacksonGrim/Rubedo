# Selector identity, replay-exact: each mode passes alone; together their costs add and fail

**Date:** 2026-10-15 · **Status:** standing (levers stay OFF) · **Corpus:** 1.4.0 · **By:** Ember

## Question
With runs now replay-exact (`2026-10-15-reproducible-runs`), and steadier identity measures declared before the
run, does identity hold under witness, upstream rupture, and both together?

## Control
`tests/diagnostic/selector/identity_probe.py 600 3`. One pretrained checkpoint (dim 128, corpus 1.4.0); every run
deterministic, arms paired step for step. Arms: OFF, WITNESS, RUPTURE-UP, BOTH (witness + upstream rupture live).
Bars in the probe docstring, written before the run: anchor drift (1 − cos of the identity anchor, step 100 → end)
≤ 2× OFF + 0.01; field lock (median per-step field turn, last 200 steps) ≤ 2× OFF + 1e-5; matched coherence mean
≥ −0.05 and no 10-step mean below −0.10; QUARANTINE + REJECT ≤ OFF + 2. Pass = all four on ≥ 2 of 3 seeds.

## Result

| arm | anchor drift (OFF .141 / .176 / .181) | field lock (OFF ~8e-7) | matched coherence mean / worst 10-step | governance | verdict |
|---|---|---|---|---|---|
| WITNESS | .101 / .161 / .147 — ok 3/3 | 5.5–6.9e-6 — ok | −.036/−.101 ✗, −.032/−.095, −.030/−.077 | 0 — ok | **PASS 2/3** |
| RUPTURE-UP | .140 / .292 / .154 — ok 3/3 | 1.5–3.2e-6 — ok | −.019/−.086, −.022/−.069, −.026/−.092 | 0 — ok | **PASS 3/3** |
| BOTH | .062 / .258 / .079 — ok 3/3 | 7.5–8.1e-6 — ok | −.062/−.130, −.064/−.125, −.060/−.128 | 0 — ok | **FAIL 0/3** |

- **Each mode alone holds identity.** Upstream rupture passes on every seed; witness passes 2/3 (seed 1's worst
  10-step window −0.101 against the −0.10 bar).
- **Together they fail on coherence, 3/3.** The costs add (witness ≈ −0.03, rupture ≈ −0.02, both ≈ −0.06): the
  composition crosses a bar each mode clears alone. This is the interaction the composition gate exists to catch, and
  it surfaced before the formal gate.
- **The identity anchor drifts less with witness on** (seeds 1 and 3: .101 and .062 vs OFF .141; .147 and .079 vs
  .181). Witness keeps the field more receptive *and* the anchor steadier. Field lock stays tiny everywhere (≤ 8e-6
  per step): the identity integrator holds in every arm.

## What it means
Witness and upstream rupture are each individually safe by these bars, and witness looks like it actively steadies
the anchor. Running both at full strength stacks their coherence costs past the bar. If both are wanted together,
the combination needs a budget (e.g. a gentler witness when ruptures are active, or a shared coherence floor), designed
and measured as its own change.

## Open items
1. Composition design for BOTH (a shared budget), measured with this probe before the formal gate.
2. Witness alone → the repo's all-levers composition gate (`tests/diagnostic/integrity/all_levers_composition_probe.py`)
   with the selector added as a lever, witness-only first.
3. Upstream rupture alone → same gate after witness.
4. All levers stay OFF until their gate passes.
