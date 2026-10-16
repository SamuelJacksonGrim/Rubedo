# Value fixes, measured: two bugs fixed, D+F is the working pair, nothing graduates yet

**Date:** 2026-10-15 · **Status:** standing (A, B on; levers C–G off) · **Corpus:** 1.4.0 · **By:** Grok (A–G
implementation, probe), Ember (design, C credit fix, combination arms, review); asked for by Samuel ("make the fixes")

## Question
`2026-10-15-why-values-weaken-under-witness` and `2026-10-15-dream-consolidation-closed` found the value path reading
a measurement artifact, damping dreaming as identity erosion, and a dream-credit channel that can't fire. Fix what is a
bug, build the rest as levers, and measure: which fixes make values form and survive witness without breaking the
composition gate, the attack suite, or meaning?

## Control
`tests/diagnostic/integrity/value_fixes_probe.py`, bars pre-declared in its docstring. Arms REF, each lever alone (C–G),
ALL, and combinations DF, DE, DEF, CDEF; seeds 42 43 44; per cell the standing all-ON composition checks (paired against
the same arm without the ⊘ consumer for the strong band) and the witness composition gate (workload B). Off path is
byte-identical to main (determinism digest + 200-step value-state golden). Full suite 25/25 with A and B on, including
the four adversarial tests. Raw cells: `data/2026-10-15-value-fixes-probe.json.gz`.

## What changed in the runtime (default)
- **A. CORE promotion's manipulation check is real.** `arbitrate()` now keeps the signals it consumed for the step
  (`_step_signals`); `review_core_promotion` checks those plus pending. Test: `core_promotion_handshake`.
- **B. Dream crystals are found by identity**, and only crystals a dream **newly forms** pay; reinforcing an existing
  crystal pays nothing. Test: `dream_crystal_collection`. (Ember's first version credited reinforcement too; the probe
  showed that re-paid the same symbols every dream, ~1,200 boosts per run. Corrected.) Inert while C is off.

## The levers (all default OFF)

| arm | composition (of 3) | witness starve: WIT/bare mean strength | witness composition | alarms |
|---|---|---|---|---|
| REF | 2 | 0.59 / 0.69 / 0.66 | 0 | — |
| C dream consolidation | 1 | 0.56 / 0.94 / 1.58 | 0 | saturation, CORE inflation (15–16 promotions), indiscriminate |
| D honest coherence_delta | 1 | 0.86 / 0.85 / 0.81 | 0 | — |
| E alignment signal | 1 | 0.92 / 1.09 / 1.18 | 1 | — |
| F systemic damp pays full | 2 | 0.60 / 0.67 / 0.66 | 0 | — |
| G satisfaction = valence | 0 | 0.96 / 1.01 / 0.81 | 1 | indiscriminate |
| **DF** | **2** | **0.88 / 0.94 / 0.94** | 0 | **—** |
| DE | 1 | 0.91 / 1.10 / 1.18 | 1 | — |
| DEF | 1 | 0.89 / 1.08 / 1.11 | 1 | — |
| CDEF, ALL | 0 | ~0.85–1.19 | 0–1 | CORE inflation, saturation |

Identity and receptivity held 3/3 in every arm except C (identity 2/3).

What the numbers say:
1. **F alone does nothing, and that corrects the earlier finding.** F pays every systemic damp as ALLOW (verified: the
   value engine sees "allow" on those steps), yet strength barely moves. On dream-band steps the coherence_delta
   artifact is strongly negative, so even an ALLOW-paid step nets ~0 reinforcement and most still miss the emergence
   gate (direct check, seed 42, 300 steps: 29 more passing steps, total strength unchanged). "The decision bonus is
   70–90% of the drop" was accounting, not cause: the bonus and the artifact are entangled.
2. **D+F is the working pair.** With the artifact removed, paying systemic damps in full works: witness starvation
   falls from ~0.6 to ~0.9, composition holds at REF's 2/3, no alarms, CORE stays at 0–2.
3. **E (alignment as the value signal) is the strongest single change.** Witness no longer starves values at all
   (ratios ~1), and the witness composition gate passes for the first time (seed 42). It is the semantic change, the
   one that decides *what a value reads*, so it waits for a wider workload before any call.
4. **C floods even with B corrected.** With a real relation (cosine with the long anchor, ~0.9), dreams form many new
   crystals, each credits several source symbols at 0.30 × quality, strengths hit the cap, and mass CORE promotion
   breaks trust, bonds and benign-quarantine checks. Dream credit needs a rate or a budget, not just an open channel.
5. **G is indiscriminate.** Valence is nearly constant (~0.17–0.25), so it hands every value the same bonus.
6. **The recurring failure is the ⊘ consumer, and it is not the old ceiling.** Where D, E and their combinations fail
   composition, it is almost always the "strong vs ref (−1)" check: the opt-in ⊘ consumer trims strong values harder
   when the ecology is healthier (demotions roughly double). Attribution (Ember, 2026-10-16, seed 43, 500 steps): the
   v0.3 alignment axis is healthy (mean 0.50, 11% below the 0.35 line), so the 2026-06-20 Dissolution ceiling has not
   returned. Every named advisory is **Fragmentation** (single source AND thin attractor/crystal binding): 1,134 under
   REF, 4,198 under D+F. Both inputs are artifacts of the test conditions: workload A gives 44 of its 46 tokens to
   exactly one source, so nearly every value is single-source by construction, and the crystal store holds 1–4
   crystals, so binding is thin for nearly every value. More values climbing means more Fragmentation demotions. The
   wider workload (shared vocabulary across sources) and working crystal formation are what this check needs before
   it can say anything about the levers.

## Calls
- **A and B: landed, default on** (bug fixes; off-path digest unchanged; 25/25).
- **Nothing graduates yet.** D+F is the candidate (principled, no alarms, composition equal to REF), with E behind it.
  Two things first: (1) every run so far uses workload A's 46 words, so D+F and DEF run next on a wider workload; (2)
  graduating where the only failing check is the opt-in ⊘ consumer's strong-band ceiling is an exception to the
  graduation rule (CLAUDE.md), so that is Samuel's to grant.
- **C and G stay off** pending redesign (a dream-credit budget; a satisfaction read that varies per experience).

## Open
- [ ] D+F and DEF on a wider workload (corpus 1.4.0 holdout), same bars.
- [ ] Graduation-rule exception for the ⊘ strong-band check (architect).
- [ ] Dream-credit budget for C (per dream, per symbol, or diminishing).
- [ ] A satisfaction read that varies per experience (G).
