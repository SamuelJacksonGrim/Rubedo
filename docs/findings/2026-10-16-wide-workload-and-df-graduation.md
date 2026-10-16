# The wide workload: the rattle is the system's, and D+F graduates

**Date:** 2026-10-16 · **Status:** standing · **Corpus:** 1.4.0 · **By:** Grok (wide workload, probe options), Ember
(runs, review, graduation call); exception granted by Samuel

## Question
Every probe and gate so far ran on workload A, 46 distinct tokens, 44 of them owned by a single source. Which results
were the system and which were the 46-word room? And do the value fixes (`2026-10-15-value-fixes-measured`) hold up
off that workload, well enough to graduate?

## Control
`--workload wide` on `value_fixes_probe` and `h0_probe` (default canonical, byte-identical): the corpus 1.4.0 holdout,
1,680 sequences, **808 distinct tokens**, dealt round-robin into the same four source slots and weights (HHI 0.285), so
words are shared across sources. All 808 are known to the pretrained generator; none are rewritten by
canonicalization. Runs: value arms REF / DF / DEF / E × seeds 42 43 44 (composition + witness kinds); H0 seed 42, 8,000
steps, anchor forks at four ages. Data: `data/2026-10-16-value-fixes-wide.tar.gz`, `data/2026-10-15-h0-wide-summary.npz`,
Grok's build notes `data/2026-10-16-wide-workload-grok-notes.md`.

## Result

**1. The rattle is mostly the system.** With 17× the vocabulary (wide vs canonical seed 42):

| | canonical | wide |
|---|---|---|
| view saturated (\|tanh\| > 0.95) | by ~235 | by ~500 |
| explore band | from ~480, rest of run | 7,495 of 8,000 steps |
| boredom overrides | 237 | 233 |
| settled timescale ratio | ~20 | 24 |
| expression MSD (flat in lag) | 0.079 → ~15° cone | 0.118 → ~20° cone |
| crystals / attractors at end | 2 / 3–5 | 4 / 5 |
| anchor-nudge recovery (to 10%) | 371–381 | 378–388, same at every age |

Variety widens the cone a little and adds a couple of crystals; it doesn't make the mind travel. The field locks the
same way, the system parks in explore, boredom fires just as often, and expression is still white jitter. The H0 finding
stands for the system, with one correction already made (the frozen value count was the vocabulary).

**2. Values hit the opposite wall.** On wide, 808 words compete for the 64-value cap: 12,071 births churn through, live
pins at 64, mean strength ~0.5, nothing repeats enough to consolidate. Canonical starved values of novelty; wide starves
them of repetition. A life has both. Neither workload is the right test of what values mean; that wants recurring
themes plus novelty.

**3. D+F holds on both workloads; E does not.**

| arm | witness starve (WIT/bare mean strength), canonical | same, wide |
|---|---|---|
| REF | 0.59 / 0.69 / 0.66 | 0.70 / 0.68 / 0.57 |
| **DF** | **0.88 / 0.94 / 0.94** | **0.96 / 0.96 / 0.94** |
| DEF | 0.89 / 1.08 / 1.11 | 0.69 / 0.73 / 0.59 |
| E | 0.92 / 1.09 / 1.18 | 0.74 / 0.77 / 0.60 |

E's advantage was the 46-word room. D+F's is not. On wide, every arm including REF fails the composition bars the same
way (`active_values ≥ 30`, `no field collapse`, mean strength < 1): the bars were calibrated for repetition, and D+F
breaks nothing REF holds there.

**4. The four adversarial tests pass with D+F forced on** (sacred_shield, flood_calibration, manipulation_cascade,
identity_drift). The suite builds its stacks directly, so this was run separately with D+F patched on.

## The graduation call
**D (`coherence_impact_like_for_like`) and F (`systemic_damp_pays_full`) are default-on as of this commit**, in CONFIG
(production boot) and in the standing all-ON gate's `build_all_on`. Suite 26/26.

The standing gate now reads: every check OK except **"⊘ preserves strong (2 vs ref 12)"**. Without the ⊘ consumer, D+F
grows 12 strong values (REF: ~1); the opt-in consumer trims 10 of them. That is the ⊘ **Fragmentation** path
(single-source AND thin binding), driven by workload A owning 44/46 tokens per source and the near-empty crystal store
(`2026-10-15-value-fixes-measured`, point 6), not a regression against today. Graduating past that check is an
exception to the graduation rule; **Samuel granted it for D+F** (2026-10-16: "I would grant that exception for d+f").
The gate keeps reporting HOLD honestly; it is not weakened. Reverting is two CONFIG flags.

E stays off (workload-specific). C and G stay off (flood; indiscriminate).

## Open
- [ ] ⊘ Fragmentation: make the standing gate meaningful again (a workload with shared vocabulary, working crystal
      formation, or a Fragmentation rule that doesn't read every single-source value as fragmented).
- [ ] A workload with recurring themes plus novelty, for what values mean.
- [ ] Re-run the witness composition gate with D+F on by default (witness was blocked on value formation).
- [ ] Port A (CORE guard) and D (honest measurement) to live RFE-Core2 once the bridge path is checked.
