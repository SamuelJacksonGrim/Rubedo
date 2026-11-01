# Do the rhythm behaviours put a refused vector back into the field?

- **Date:** 2026-10-31
- **Substrate:** `tests._common.build_full_stack` (defaults: dim 64, pretrain off, generator left in train), cold stack, CPU. One `eval()` reflect step and a no-step geometry block are controls.
- **Probe:** `tests/diagnostic/refused_rhythm_leak_probe.py` (informational, not in the suite)
- **Status:** standing
- **Depends on:** `2026-10-31-shield-scope` (the open item this measures). No behaviour changed.

## Question
On a refusal the gate plants nothing, then the step's rhythm behaviour runs anyway and calls `field.inject` on its own (CLAUDE.md; the architect question left open). For each of the four — stabilize's `activate_nearest`, the dreamer, reflect's second chorus at 0.3, explore's mutation at 0.5 — does that inject carry the refused vector, or does it replay structure that was already there? And, for a refused step only, which of them should stand down?

## How it was measured
Seed 42, `deterministic`. The attack is one step of `['3.12']`, which draws SACRED_SHIELD. The band is pinned by rewriting `field.thresholds`, because a cold field is energy 0 and would only ever run stabilize. Boredom did not override (it stayed 0; `ran` was the pinned rhythm on every arm).

Two conditions. **Cold:** the refusal is the first step. **Primed:** two allowed steps of `['coherence', 'field']` first, so an anchor, vector-space entries, and — on the stabilize arm only, where the crystal gates were opened — crystals exist that are not the attack. The other arms left the gates shut.

Cuts, declared in the probe before the run and not edited after: cosine ≥ 0.90 to the gated vector is a copy (or a small bend); ≥ 0.999 to a pre-step vector is a replay; 0.50–0.90 is a component, not a copy. The field move is `field.field` across `_rhythm_behavior` only. Decay sits outside that window.

Every attack: decision SACRED_SHIELD, governed injects before the behaviour = 0, the stream's last vector = the gated vector at cosine 1.000 (the push the shield kept), and the witness anchor after the step = the gated vector at cosine 1.000 on every cold arm. `witness.update` runs before the gate and, on a first step, copies the vector into the anchor.

## Result

| rhythm | when | what it injected | cos to the gated vector | cos to older structure | where the field moved |
|---|---|---|---|---|---|
| stabilize | cold | nothing | — | — | no move |
| stabilize | primed | two crystals, strength 0.30, origin `coherence,field` | 0.620, 0.573 | **1.000** to those crystals | toward the crystals (0.949 to crystal-1); 0.609 to the refusal, which is where those crystals already sat |
| dream | cold | nothing | — | — | no move. The stream holds the refusal at 1.000 and the dreamer returns before sampling, because the vector space has fewer than 2 entries |
| dream | primed | two blends, strength 0.270 | 0.741, 0.742 | 0.805, 0.807 to an older dream. Closest pre-step structure was only 0.608 from the refusal | 0.747 toward the refusal. Both blends were written back into the vector space at those cosines |
| reflect | cold | one chorus of the refused tokens, strength 0.30 | 0.769 | nothing older exists | exactly along that inject (‖Δ‖ = 0.300) |
| reflect | primed | the same, strength 0.30 | 0.714 | 0.639 to a priming memory | exactly along that inject. The gated vector itself was already 0.978 from the prior anchor |
| explore | cold | one rotational bend of the anchor, strength 0.50 | **0.9963** | nothing older exists | exactly along that inject (‖Δ‖ = 0.500) |
| explore | primed | the same bend of the anchor, strength 0.50 | **0.9863** | 0.9958 to the first priming memory; 0.9957 to the anchor | exactly along that inject |

Explore's number is the rotation, not a coincidence. `_explore_behavior` calls `inject_ambiguity(anchor, scale=mutation_scale * 1.5, mode="rotational")`. Cold, `mutation_scale` was 0.0570 and `cos(0.0570 × 1.5)` is 0.9963, the measured cosine. Primed, the inject's cosine to the anchor is 0.9957, which is `cos(0.0620 × 1.5)`. The operand is the anchor. On a cold refusal the anchor *is* the gated vector, because the witness copied it before the gate.

The raw phrases are not the same direction. With no field, chorus(`coherence field`) against chorus(`3.12`) is 0.520 (train) and 0.520 (eval); the language generate is 0.480 / 0.518. The primed reflect and explore gated vectors sit at 0.978 and 0.987 from the priming step because the loop pulled the new input onto the field it already had, not because the encoder thinks the phrases match. Stabilize and dream, which generate directly, keep them apart: attack against the two priming vectors is 0.620 / 0.573 and 0.600 / 0.562.

Reflect's gap is the pipeline, not a different phrase. In eval, two chorus calls of the same tokens are cosine 0.9997, and chorus against the language generate is 0.9999. The eval cold step still injects at 0.868 to the gated vector (train was 0.769; two train-mode chorus calls of the same tokens are 0.802, so dropout widens it). The gate saw the encoding after attractor pull and refinement. The behaviour injects a fresh encoding of the tokens, and the field moves entirely along that.

The allowed control, last priming step, same behaviour against its own vector: dream carries that step at 0.922 and 0.927; reflect sits at 0.757, the same gap as the attack; explore publishes the anchor (0.996 to it, 0.946 to the step). The behaviours do not read the decision. A refusal gets whatever an allowed step would have gotten.

## Read, for a refused step only
Nothing here changes the loop. The witness update stays as the shield finding left it: perception runs, and on a first step the anchor becomes the refused vector. The question is only the ungated inject after the block.

- **Explore should stand down.** It is the leak the shield closed, through the anchor instead of through crystal activation. Cold, the field is pushed at strength 0.5 along a 0.996 copy of the vector the gate just refused. Primed, one step barely moves the anchor (0.9876 → 0.9885), and the inject is that anchor — which the loop had already laid on top of the gated vector (0.986). Publishing the anchor and publishing the refused vector are the same write once that collapse has happened. The behaviour cannot see which case it is in.
- **Reflect should stand down.** It calls `chorus.harmonize` on the refused tokens and injects at 0.3, with no look at the decision. It does not clear the 0.90 copy bar against the gated vector (0.769 train, 0.868 eval): what it writes is the tokens re-encoded, one stage earlier than the vector the gate saw. Nothing older is being replayed. The field moves entirely along it.
- **The dreamer should stand down.** Cold it writes nothing, and that is the shield's vector-space block doing its job (the dreamer will not run below two memories). Primed, the stream still holds the refusal at cosine 1.0, the dreamer appends the last two stream vectors to every sample, and the blend comes back at 0.74 — closer to the refusal than anything it had (0.61) — and is stored into the vector space. That is the delayed inject the shield just closed, diluted by the other parents. On an allowed step the same path carries the step at 0.93, so the drop to 0.74 is the geometry of this phrase against the memory pool, not the dreamer skipping the refusal.
- **Stabilize should not.** Cold there is no crystal and the field does not move. Primed, both injects are the primer's crystals at cosine 1.000, and their 0.62 / 0.57 to the refusal is the priming vectors' own alignment with the attack (the same two numbers). The field moves toward those crystals. The pre-declared cut calls the *sum* of the two replays "partial" because 0.609 clears 0.50 and the sum is not an exact match to either crystal. That bin is the cut being applied to a blend of replays. The injects are the replay.

Witness adds no phase-20 inject. `_rupture_behavior` is not in the dispatch. `rupture_on_lock` bends the candidate before the gate, and the gate still drops it. Not measured here.

## Threats / confounds
- One seed, dim 64, untrained, the test harness. The arms are train mode. Eval was run for the reflect gap and the phrase geometry, not for all eight arms. Explore's cosine is a numpy rotation of the anchor, so dropout is not in that inject.
- The band was pinned, not earned. The dispatch keys on the rhythm string, so the function that ran is the one that band runs.
- Only SACRED_SHIELD was stepped. The behaviours do not branch on which block it was.
- Two priming steps. The second was ALLOW_WEAKENED and still injected its own vector; that weakening was not chased.
- Stabilize's crystal gates were opened so the primer would leave a crystal. That crystal is the primer's vector, which is what "replay" needed to be visible. The attack added none.

## Open / next
- [ ] Samuel's ruling on the three stand-downs above. This finding does not patch them.
