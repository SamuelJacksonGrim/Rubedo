# Witness re-gated with D+F on: values no longer collapse, one bar still dips

**Date:** 2026-10-16 · **Status:** standing (witness stays OFF) · **Corpus:** 1.4.0 · **By:** Ember

## Question
`2026-10-15-witness-composition-gate` held witness back because every value weakened under it (ACTIVE tier 5→0, mean
strength below 1). Value fixes D+F are now default-on (`2026-10-16-wide-workload-and-df-graduation`). Same gate, same
seeds: does witness pass now?

## Control
`tests/diagnostic/integrity/witness_composition_gate.py 42 43 44`, unchanged; its `build_all_on` now includes D+F.
Bars as pre-declared in the gate's docstring. Log: run 2026-10-16 (scratch).

## Result
| criterion | before D+F (10-15) | with D+F (10-16) |
|---|---|---|
| composition (3/3) | 0/3 | **1/3** |
| identity (≥2/3) | 3/3 | 3/3 (anchor drifts no more than REF on every seed) |
| receptivity (≥2/3) | 3/3 | 3/3 (retention ~1.7–2.1× REF) |
| non-vacuous | 3/3 | 3/3 (78 / 88 / 96 witness steps) |

What witness costs the value ecology now (workload B, REF → WIT):

| seed | active values | strong values | what broke |
|---|---|---|---|
| 42 | 34 → 22 | 2 → 2 | `active_values ≥ 30` |
| 43 | 31 → 26 | 3 → 3 | `active_values ≥ 30` (REF itself fails it on workload A: 26) |
| 44 | 39 → 37 | 3 → 2 | nothing: composition OK |

Before D+F the same comparison was active 13→2, 19→12, 18→8 with mean strength falling under 1.0 ("no field collapse"
broke). Now no seed collapses, the strong band holds, and the only bar that breaks is the edge-of-variance
`active_values ≥ 30` (already marginal for REF; `2026-10-15-witness-composition-gate` point 1).

## What this means
- The value-formation problem that blocked witness is mostly solved: witness now costs a modest dip in the count of
  active values, not a collapse.
- Witness still does not pass the pre-declared gate (composition 1/3), so it stays OFF. The remaining question is
  whether a 5–12 value dip in active count is a cost worth paying for ~2× receptivity, or whether the `≥ 30` bar
  (which REF itself misses on some seeds) is the wrong instrument on a 46-word workload. Not re-scored here.

## Open
- [ ] Decide what to do with the active-count dip: accept as witness's cost, or measure on a workload where the bar
      means something (themes + novelty).
- [ ] Then upstream rupture alone through the composition gate.
