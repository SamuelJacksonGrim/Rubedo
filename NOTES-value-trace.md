# Value reinforcement trace (OPEN_METASTABILITY item 0)

**Date:** 2026-10-15 · **By:** Grok (on `grok/value-trace`) · **Code unchanged:** witness/rupture stay OFF; probe-only wraps.

Replay-exact REF vs WIT, all-ON stack, workload B, seeds 0/1/2. Instrumentation is instance wraps on `_birth_or_strengthen`, `_update_all_values` / tension / dissolve / cap, `on_dream_cycle_complete`, `IntegrityDecayConsumer.apply`, and `Witness.update`. Traced REF matched `witness_composition_gate.run(seed, "B", False)` bit-for-bit on seeds 0 and 1.

Scratch (not committed):
- seed 0: `%TEMP%\value_reinforcement_trace_p0q1q86m`
- seeds 1–2: `%TEMP%\value_reinforcement_trace_v209ptiu`

Accounting: per live `value_id` (current generation, not a token's dissolve/reborn churn). Additive budget closed to ~1e-15 on every seed.

## Decomposition (values that end weaker under WIT)

Applied strength, WIT minus REF. `decision_bonus` is the unit-bond term `db * reinforcement_lr`; `coherence_delta` / `emotional_satisfaction` are the unit-bond `cd*0.6*lr` and `es*0.4*lr`; `bond_weight` is the extra from `bw ≠ 1`.

| seed | fired | active R/W | mean R/W | Δsum | Δcd | Δes | Δbw | **Δdb** | Δdecay | Δ⊘ | Δbirth | unexp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 100 | 24/11 | 1.090/0.715 | **−21.383** | −3.824 | −0.718 | −0.168 | **−19.275** | +3.290 | −0.688 | 0 | ~0 |
| 1 | 69 | 24/12 | 0.996/0.785 | **−13.776** | −4.336 | +0.170 | +1.159 | **−13.320** | +3.399 | +0.652 | −1.500 | ~0 |
| 2 | 93 | 22/9 | 0.920/0.766 | **−12.033** | +1.214 | +0.217 | −0.213 | **−13.440** | +2.288 | −0.600 | −1.500 | ~0 |

ACTIVE polarity: 3→0 / 5→0 / 0→0. Seed 2 is not “every value”: 41 weaker, **16 stronger**. Seeds 0 and 1 were 57/57 and 54/54 weaker.

**The majority term on every seed is decision_bonus** (70–90% of the weaker-values drop). ALLOW→ALLOW_WEAKENED:

| seed | REF allow/weakened | WIT allow/weakened |
|---|---|---|
| 0 | 319 / 181 | 197 / 303 |
| 1 | 229 / 270 (+1 monitor) | 176 / 323 (+1 monitor) |
| 2 | 223 / 277 | 149 / 351 |

Each ALLOW event that actually reinforces pays `0.05 * 1.50 = 0.075` strength; WEAKENED pays `0.02 * 1.50 = 0.030`. Missing the event pays 0. WIT both shifts the mix toward WEAKENED **and** fails the emergence gate more often (score includes `db`, so WEAKENED sits closer to the 0.015 line):

| | REF fail | WIT fail | WIT fire fail |
|---|---|---|---|
| 0 | 36.2% | 60.6% | 63.0% |
| 1 | 53.8% | 64.0% | 63.8% |
| 2 | 55.4% | 69.4% | 67.7% |

When cd is negative, `es = max(0, cd) = 0` and `surprise = −cd`, so the emergence score collapses to `0.25*cd*bw + db`. At cd ≈ −0.10 that is −0.025 + 0.05 = 0.025 (ALLOW, still passes) or −0.025 + 0.02 = −0.005 (WEAKENED, fails). So the mix shift does not just pay a smaller bonus — it often **drops the event entirely**, including the still-positive lump.

Positive applied reinforcement (all generations): REF +59.7 / +43.2 / +43.2 vs WIT +31.6 / +27.9 / +29.7. Negative applied reinforcement: seed 0 had some, and **REF had more of it than WIT** (−5.04 vs −0.79). Seeds 1 and 2 had **zero** negative reinforcement events in either arm.

## What this does to Ember’s suspects

1. **`emotional_satisfaction` does not read joy.** `SelfhoodGovernance.emit_feedback` sets `es = max(0.0, coherence_delta)` (and `surprise = max(0.0, −cd)`). Confirmed 500/500 steps, every arm, every seed. Joy *does* track watcher composite (REF ~0.80–0.82, WIT ~0.74–0.78) but it never enters this path. Mean `es` is ~0.000–0.001 because `cd` is typically negative, so ReLU zeros it. Δes is small and mixed-sign. The “slightly less coherent field lowers satisfaction for every value at once” mechanism is **not what this code does**.

2. **`coherence_delta` is real, not the majority, and not even the same sign every seed.** −3.8 / −4.3 / **+1.2** on the weaker set (seed 2’s weaker values got a *better* cd term and still dropped, because of Δdb). “Every later input lands in a slightly less coherent field and every value’s reinforcement tips negative” is too strong: cd is more negative on average (mean cd REF −0.074/−0.087/−0.087 vs WIT −0.106/−0.108/−0.103), but applied reinforcement does not tip negative.

3. **“Reinforcement tips negative” is false as a description of applied strength.** The drop is **less positive reinforcement** (fewer events, smaller `db`), not a wave of negative hits. The finding’s more-negative `coherence_contribution` is a different quantity: lifetime sum of `cd` on steps that *did* reinforce. That can go more negative while applied strength from the cd term stays small, because `cd * 0.6 * lr` is only 60% of a number that is already ~−0.1, and those steps often never get in.

4. **Decay, ⊘, tension, dream, dissolve of the current live generation are not the cause.** Decay actually runs the other way (WIT current-generation values lost *less* to decay: +2.3 to +3.4). Integrity is small and mixed. Tension = 0, dream = 0, dissolve_remove = 0 for live values. There *is* dissolve/reborn churn in archived generations; it does not explain the live ecology.

5. **Option (b) as phrased (judge cd against the field’s own level) is still a no-op for cd** — it is already `field.coherence_impact(vec)` before injection. It would also not touch the majority term, which is `db`.

6. **Option (a) (witness steps don’t feed value reinforcement) is already half-true** — fire-step emergence fail is 63–68% — and is **not sufficient**: WIT’s non-fire steps fail at the same rate (60–70%). The regime shift is field-wide (ALLOW_WEAKENED mix + slightly worse cd), not a per-witness-token hit. That is why non-witness values drop. Turning (a) on as a policy would not fix the other 400 steps.

## Temporal shape

Not a trickle. Share of the end-gap coming from small same-sign steps (`|d|<0.05`) is 8% / 7% / 16%. Hundreds of steps move the gap by ≥0.10 (births landing on different steps, plus lumpy reinforcement).

Witness-fire steps are **not** uniquely where the gap grows:
- seed 0: fire d(gap) −0.069 vs other −0.036 (fire worse)
- seed 1: fire **+0.067** vs other −0.043 (gap grows on the other steps)
- seed 2: fire +0.010 vs other −0.030

Recovery stretches (a fire to the next fire, min 3 steps): mean gap change −0.26 / −0.33 / −0.15; gap shrank in 15/65, 15/55, 14/70. **Values do not recover after witness stops firing.** The mix shift persists.

## effective_lr = clip(coherence², 0.01, 1)

| | REF mean | WIT mean | fire | 1 after | 2 after | 3 after | 10+ |
|---|---|---|---|---|---|---|---|
| 0 | 0.691 | 0.581 | **0.311** | 0.628 | 0.640 | 0.652 | 0.679 |
| 1 | 0.682 | 0.623 | **0.399** | 0.657 | 0.666 | 0.680 | 0.637 |
| 2 | 0.652 | 0.564 | **0.363** | 0.604 | 0.616 | 0.626 | 0.554 |

The mechanical “steadier anchor” confound is real **on the fire steps**: elr roughly halves, so the identity write is ~2× slower those steps. One step later it is mostly back. Mean elr over the whole run is only modestly lower. The identity PASS (anchor drifts less under witness) is therefore *partly* this c² gate on the ~70–100 fire steps, not entirely “steadiness earned.” It is not the whole run.

## What surprised me

- The gate’s post-step `watcher.evaluate(field, …)` **writes Watcher temporal history**. A traced loop that skipped it did not replay the gate’s REF (bonds 1 vs 2, mean strength, demotions). Observe-only it is not. The probe now issues the same extra call.
- Decision bonus, not cd, is the drop. I went in expecting Ember’s cd/es story to be at least half of it.
- Seeds 1 and 2 never applied a negative reinforcement in either arm. “Tips negative” cannot be the general mechanism.
- Seed 2 had 16 values *stronger* under WIT. “Every value weakens” was true on 0 and 1, not 2. The composition-gate finding used 43/44.

## What I’d look at next

1. **Which `arbitrate` branch produces the extra ALLOW_WEAKENED.** Candidates in `selfhood_governance.py`: manipulation `total_severity >= 0.30` (ambient `identity_erosion` is already ~0.55 in ordinary dream-band — the F9 comment is sitting right there), dependency CRITICAL, ethical soft warnings. Witness skips attractor pull and recursive attention, so the expressed vector is rawer; that is a plausible identity-erosion / soft-warning trigger, and it would hit *every subsequent step’s mix*, not just fire steps. A one-seed wrap on `arbitrate` that logs the branch name would settle it in a minute.
2. **Do not start with (a) or (b).** (b) does not touch `db`. (a) does not touch the 400 non-fire steps that already fail as often as the fire steps. If the architect still wants a value-formation change, the live question is whether a missed ALLOW lump (governance being cautious) *should* starve every value — that is a semantics question, not a bug in witness.
3. **Identity PASS confound.** The identity probe should log `effective_lr` the same way. If you recompute anchor drift with elr held at REF’s mean, you will know how much of the “steadier under witness” bar is the c² write-slowing.
4. **H0 / H0′ measurement** is still the next OPEN_METASTABILITY item. This trace only says: the value ecology’s complaint about witness is mostly “governance paid WEAKENED more often, so the per-event bonus and the emergence gate both shrunk,” not “joy fell” and not “⊘ ate them.”
