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

**Attribution: the dip is entirely the ⊘ consumer** (same gate, same seeds, consumer removed; Samuel asked whether D+F
were really on — verified from inside the run: D on in field and watcher, F on, consumer attached in the run above):

| seed | active values, REF → WIT | strong values, REF → WIT | broke vs REF |
|---|---|---|---|
| 42 | 54 → 54 | 5 → 5 | nothing |
| 43 | 51 → 51 | 7 → 7 | nothing |
| 44 | 54 → 54 | 9 → 9 | nothing |

Identity 3/3 and receptivity 3/3 (retention ~1.7–2.1×) are unchanged, as they must be. Composition "fails" only on
`consumer used` (vacuous with no consumer) and on seed 43's HHI, which REF misses too. So with D+F, **witness costs the
value ecology nothing measurable**; the active-count dip is the opt-in ⊘ consumer demoting values witness shifts
(demotions 7,940 → 9,487 etc.), through the same Fragmentation path as the D+F strong-band exception. Production boot
(`build_engine`) does not attach the consumer.

## What this means
- The value-formation problem that blocked witness is solved on the production composition: with D+F and no ⊘
  consumer, witness gives ~2× receptivity, holds identity, and costs values nothing measurable.
- Witness still does not pass the pre-declared all-ON gate (composition 1/3), so it stays OFF. Every remaining failure,
  for witness and for D+F, runs through one place: ⊘ Fragmentation reading single-source, unbound values as fragmented.
  That rule is now the critical path. Samuel (2026-10-16) is fine with the dip for 2× retention; Rubedo-A/B (witness
  on/off, trained encoder) is the planned lived comparison.

## Open
- [ ] Fix ⊘ Fragmentation (the shared cause of the witness dip and the D+F strong-band exception). A default-off grace exists (`2026-10-18-fragmentation`); the dip is gone with it on, and the flag is not graduated.
- [ ] Then upstream rupture alone through the composition gate.
