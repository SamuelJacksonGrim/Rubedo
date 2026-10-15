# Witness composition gate: identity and receptivity pass; the value ecology pays for receptivity

**Date:** 2026-10-15 · **Status:** standing (witness stays OFF) · **Corpus:** 1.4.0 · **By:** Ember; gate
requirements from GPT/Raphael

## Question
Does witness (selector, witness mode only; rupture masked) hold on the full all-ON runtime stack (production dim,
corpus pretrain, eval mode, novelty attenuation, bond DDM, Build A ignition, Build B λ gate, ⊘ consumer)?

## Control
`tests/diagnostic/integrity/witness_composition_gate.py 42 43 44`, built on the standing all-levers gate's own
`build_all_on`. Per seed, two replay-exact paired arms (REF = all-ON; WIT = all-ON + witness), two workloads (A =
the standing gate's canonical 500 steps; B = the same with 20% witness phrases so witness actually fires). Criteria in
the gate's docstring, written before the run.

## Result
| criterion | result |
|---|---|
| non-vacuous (witness fires ≥ 50 on B) | PASS 3/3 (59, 88, 96) |
| identity (B): anchor ≤ 2×REF+.01, lock ≤ 2×REF+1e-5, coherence mean ≥ −.05, worst 10-step ≥ −.10 | **PASS 3/3**; anchor drift again lower with witness (.166 vs .186, .097 vs .112, .085 vs .109) |
| receptivity (B): retention WIT > REF | **PASS 3/3** (.0046 vs .0024, .0042 vs .0029, .0048 vs .0024) |
| composition: every standing health check holds for WIT, none that holds for REF breaks | **FAIL 3/3** |

Composition, attributed:
1. **A (canonical): witness never fired, so WIT ≡ REF.** REF itself missed `active_values ≥ 30` on two seeds (23,
   29). Not a regression: the standing gate passes in Rubedo now, Rubedo before corpus 1.4.0, and the live RFE-Core2
   (active 31–34, two runs each). The bar sits at the edge of normal seed variation.
2. **B (witnessing): witness weakens the value ecology.** Active values fall (13→2, 19→12, 18→8) and mean value
   strength drops under 1.0 ("no field collapse" breaks vs REF on 2 seeds).

## Mechanism (`witness_value_breakdown.py 43 44`, same replay-exact arms)
Hypothesis written before the run: the loss concentrates in values built on witness tokens. **Refuted.**

| | REF mean strength | WIT mean strength | coherence contribution REF → WIT | ACTIVE-polarity values |
|---|---|---|---|---|
| witness-token values (s43 / s44) | .822 / 1.003 | .561 / .576 | −.050 → −.085 / −.077 → −.207 | none either arm |
| all other values (s43 / s44) | 1.060 / 1.107 | .816 / .760 | −.082 → −.128 / −.085 → −.189 | **5 → 0 / 7 → 0** |

Every value weakens, and the top tier vanishes. Totals barely change (no dissolution, no wave of demotions): values
receive weaker, more negative reinforcement. Values accumulate the **coherence change** of the steps their tokens
appear in; witness lowers field coherence a little (~−0.03), every later input then lands in a slightly less coherent
field, and every value's reinforcement tips negative.

## What it means
**In the current architecture, value is coherence contribution, so the system cannot value something that does not
raise coherence.** Witness does what it is for (receptivity up, anchor steadier, identity intact), and the value
system reads that receptivity as harm. This is a design question about what values should be built from, not a
witness bug, and it reaches past witness: any mechanism that legitimately lowers coherence (upstream rupture too) will
tax the value ecology the same way.

## Open items
1. Architect question: should value formation stay coherence-only? Options to measure: (a) witness steps do not feed
   value reinforcement (received, not acted on); (b) value reinforcement measured against a coherence baseline that
   tracks the field's own level, so a uniformly lower field doesn't penalize everything; (c) leave values as they are
   and keep witness off. (b) addresses the broad effect; (a) alone likely does not (the drop reaches non-witness values).
2. Trace one value's reinforcement over the run (sign, timing, any ⊘ demotion) to confirm the mechanism step by step
   and check for later recovery.
3. The `active_values ≥ 30` bar is marginal across seeds; record the distribution over more seeds before treating it
   as a hard gate.
4. Witness stays OFF.
