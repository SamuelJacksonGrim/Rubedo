# What witness leaves behind, and upstream rupture: both carry real change; identity holds on 2 of 3 seeds

**Date:** 2026-10-14 · **Status:** standing (levers stay OFF) · **Corpus:** 1.4.0 · **By:** Ember, criteria shaped
with GPT/Raphael

## Question
1. Witness lowered field coherence (`2026-10-14-six-rhythm-selector-live-off-on`). Is that dip the mechanism by which
   it takes the input in, or collateral damage? (Raphael: test retention, recovery, responsiveness.)
2. Rupture through the reflective loop was absorbed. Does variant (a), **upstream** (held direction mixed into the
   generator's raw output, ordinary path after; nothing bypasses the loop or forces the field), change behavior
   downstream while identity holds?

## Control
`tests/diagnostic/selector/aftermath_probe.py 300 3`. One pretrained production checkpoint (dim 128, corpus 1.4.0)
resumed by every arm; same workload (60% stance / 20% witness-like / 20% rupture-like phrases, four-source rotation);
RNGs pinned per seed, so step t sees the same input in every arm (paired). Arms: OFF; WITNESS (selector on, rupture
reads masked); RUPTURE-UP (selector on, witness reads masked, `rupture_upstream=True`). Criteria in the probe docstring,
written before the first run.

## Result

**Witness** (n = 72 / 53 / 67 witness steps)

| criterion | seed 1 | seed 2 | seed 3 | verdict |
|---|---|---|---|---|
| retention d1 (field turns toward the input), ON vs OFF | .0066 vs .0057 | .0070 vs .0065 | .0057 vs .0052 | PASS 3/3 |
| retention d5 | .0071 vs .0067 | .0078 vs .0068 | .0059 vs .0057 | PASS 3/3 |
| recovery: per-event coherence gap t+1 → t+10 | .014 → .010 | .015 → .011 | .010 → .009 | PASS 3/3 |
| responsiveness: cos(next expression, input), ON vs OFF | .131 vs .142 | .084 vs .057 | .261 vs .159 | PASS 2/3 |
| end-of-run field coherence, ON − OFF | −0.011 | −0.053 | −0.078 | (recorded) |

By the pre-declared rule, retention and responsiveness hold, so **the coherence dip is part of how witness takes the
input in, not damage**. Effects are small (retention ~10% above OFF) but consistent. Caveat: each dip recovers
locally, yet end-of-run coherence still drifts lower; over a long run the small per-event costs accumulate.

**Upstream rupture** (n = 51 / 63 / 60 rupture steps)

| criterion | seed 1 | seed 2 | seed 3 | verdict |
|---|---|---|---|---|
| behavior: cos(expression_t, held direction), ON vs OFF | .633 vs .018 | .660 vs .033 | .623 vs −.010 | PASS 3/3 |
| behavior at t+1 | .064 vs −.006 | .039 vs .019 | .107 vs .025 | PASS 3/3 |
| integration: cos(field_t+5, held direction) | .058 vs .004 | .049 vs .028 | .057 vs .021 | PASS 3/3 |
| identity: end-of-run coherence ON − OFF (bar: mean within 0.02) | +0.007 | **−0.119** | −0.007 | **FAIL** (mean −0.040) |
| governance: no new QUARANTINE / REJECT | none | none | none | PASS |

**Upstream fixes what the reflective-loop variant could not**: the disruption shows in the expression, persists a
step, and the field integrates it. Identity held within noise on two seeds and dropped 0.12 on one, so by the letter
of the pre-declared bar (mean over seeds) identity fails. The bar is not being moved after the fact.

## What it means
- Witness behaves like receptivity: it lets the input shape the field and the next expression a little more than
  the ordinary path, at a small coherence cost that recovers per event but accumulates over a run.
- Upstream rupture is the right actuator: real downstream change through the system's own path. Its open question is
  identity under some trajectories (seed 2).
- An end-of-run coherence snapshot is a noisy identity measure (OFF alone ranges 0.81–0.85 across seeds). The next
  run should declare a steadier one in advance (mean over the last 50 steps, and the identity measures the repo
  already trusts: witness anchor drift, the field-lock displacement).

## Open items
1. Seed 2: what made upstream rupture cost 0.12 there? (Trace its rupture pulses against the coherence trajectory.)
2. Witness accumulation: does the drift level off over a longer run (1,000+ steps), or keep falling? A bound on
   witness strength is the fallback if it keeps falling.
3. Re-run identity with the steadier measures above, declared first; more seeds.
4. Both levers stay OFF until 1–3 land; then the all-ON composition gate.
5. The emotion trace during witness / rupture belongs to the calibration plan (`docs/EMOTION_CALIBRATION.md`), once
   the dimensions are characterized.
