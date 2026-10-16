# The post-dream value boost is closed by construction

**Date:** 2026-10-15 · **Status:** standing (no runtime change) · **Corpus:** 1.4.0 · **By:** Ember; direction from
Samuel ("post-dream consolidation"), lead from Grok's trace (dream boost contributed 0)

## Question
`ValueEmergenceEngine.on_dream_cycle_complete` is the one place where dreaming is meant to credit values: values whose
symbols crystallize during a dream behaviour get `dream_boost_factor` (0.30) × quality, four times what an ALLOW event
pays. In `2026-10-15-why-values-weaken-under-witness` it paid nothing. Why?

## Control
`tests/diagnostic/integrity/dream_consolidation_probe.py 0 1 2`: the composition gate's REF arm (all-ON stack, workload
B, no witness, deterministic), instance wraps only. Counts dream behaviours, the dreamer's offers to the crystal store,
which threshold rejected each, dream crystals formed, whether dream keys resolve to a symbol, and boost calls.

## Result
| seed | dream behaviours | offers | rejected: coherence < .75 | stability < .60 | **relation < .80** | crystals formed | boosts |
|---|---|---|---|---|---|---|---|
| 0 | 160 | 320 | 120 | 37 | **163** | 0 | 0 |
| 1 | 243 | 486 | 85 | 137 | **264** | 0 | 0 |
| 2 | 232 | 464 | 152 | 78 | **234** | 0 | 0 |

The channel is closed three ways, any one of which is enough:
1. **The relation gate can never pass.** `agents/dreamer.py` offers variants with `long_relation = 0.5` hard-coded
   ("dreams don't have long-relation yet"); the store requires 0.80 (`configs/field.yaml`). Half of all offers (163 /
   264 / 234) cleared coherence and stability and were refused only by that constant. Offered coherence averages
   0.78–0.81, above the 0.75 line: the dreams are good enough by the store's own measure.
2. **A dream crystal could not name a value.** Its `origin_tokens` is a synthetic key (`dream_<hex>`), never a
   registered token, so `stable_ids_for_tokens` returns nothing (0 resolutions in every run).
3. **New crystals are found by list length** (`crystals[before:]` in `_dream_behavior`), which misses a reinforced
   crystal and any crystal formed once the store is at its cap (512) and evicting.

Side observation: the whole crystal store ends these runs with 1–4 crystals (cap 512).

## What this means
Dreaming has a consolidation channel on paper and none in practice, like `SystemRights`. It sharpens the earlier
finding: the dream band starves values through the identity-erosion damp, and the one path built to pay them back for
dreaming cannot fire. Fixing it is a design decision, not a constant: what a dream's "relation" should be (its
recombined sources' relation to the anchor?), which symbols a dream crystal should credit (the sampled memories it was
recombined from, `DreamProduct.origin_keys`?), and finding new crystals by identity rather than position. It belongs
with question 4 (what values should read), and nothing changes until that is answered.

## Open
- [ ] Design what a dream credits and how (with question 4).
- [ ] Why the crystal store holds only 1–4 crystals over 500 steps.
