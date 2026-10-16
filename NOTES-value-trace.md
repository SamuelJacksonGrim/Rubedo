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

## Which `arbitrate` branch emits the extra ALLOW_WEAKENED

**Date:** 2026-10-15 · same probe, same three seeds. Runtime, gates, and lever defaults still untouched.

The probe now snapshots, before each `arbitrate()` call, the pending manipulation signals (detector, severity, `source_id`), the ethical result, effective trust against the two trust thresholds, the bond floor, and the dependency report. It replays the same if/elif and keeps the branch only when the predicted `(decision, strength)` equals the returned pair. Strength alone is not an identifier: `ALLOW_WEAKENED` at 0.5 is dependency-CRITICAL, manip-moderate at total severity 0.5, and the soft-warning floor. 1,500/1,500 calls matched (seeds 0/1/2, both arms, one call per step, zero mismatches). The signals queued at the end of a step were the next step’s pending inputs on 499/499 steps. The erosion evidence mean matched the mean of the previous 32 `|G−T|` samples on every erosion event.

Replay against `witness_composition_gate.run(seed, "B", False)` now runs for **every** seed in the invocation, not only the first. Seeds 0, 1, and 2 all **MATCH**, including seed 2. Decision totals are the same numbers as the decomposition above.

Scratch (not committed): `%TEMP%\value_reinforcement_trace_z6qfngqb`

### The branch

Every extra `ALLOW_WEAKENED` is systemic `identity_erosion`, alone. No second detector. No named signal (`source_id` is `None` on every one of these calls). Soft warnings: 0/500 on every arm. Trust never reached the monitor line.

| seed | arm | clean ALLOW | manip moderate (`0.30–0.60`) | manip high, systemic (`≥ 0.60`) | dependency CRITICAL | dependency HIGH (MONITOR) |
|---|---|---|---|---|---|---|
| 0 | REF | 319 | 149 | 32 | 0 | 0 |
| 0 | WIT | 197 | 204 | 99 | 0 | 0 |
| 1 | REF | 229 | 160 | 109 | 1 | 1 |
| 1 | WIT | 176 | 116 | 206 | 1 | 1 |
| 2 | REF | 223 | 178 | 99 | 0 | 0 |
| 2 | WIT | 149 | 195 | 156 | 0 | 0 |

The ALLOW→WEAKENED swap is exactly those two manip rows (seed 0 +55 moderate and +67 high; seed 1 −44 moderate and +97 high; seed 2 +17 moderate and +57 high). Seed 1’s one MONITOR and its one dependency-CRITICAL `ALLOW_WEAKENED` are in both arms. They are not the witness delta. The high row is still `ALLOW_WEAKENED`, not quarantine: past 0.60 a systemic-only signal damps (`strength = max(0.3, 1 − severity)`) and does not name anyone.

Mean erosion severity when it fires is 0.562→0.574, 0.594→0.602, 0.586→0.592. That is the F9 comment’s “ambient ~0.55”, and it is already enough. The detector cannot fire below severity 0.50, because it requires mean `|G−T| ≥ 0.30` and severity is that mean divided by 0.60. So the 0.30 line does not need a co-signal. `needs_cosignal_for_030` is 0 on every manip return. Returned strength is about 0.40–0.44, and it is never exactly 0.50, which is how seed 1’s dependency-CRITICAL calls (one per arm) stay distinguishable from the erosion path.

The co-signal half of the hypothesis is wrong. The F9 comment’s co-signal was about crossing **0.60** and quarantining a named source. Nothing else fires here. What witness does to the 0.60 line is make the same systemic signal hotter, so more calls sit in the high-systemic damp instead of the moderate one. On seed 1 that is most of the story: moderate falls, high rises by more, and the net is +53 weakened.

### What carries it onto non-fire steps

Not the fire step’s own sample sitting in the 32-deque. The fire step is the **cool** sample.

| | mean `|G−T|` | mean G | mean T | fraction of samples `≥ 0.30` |
|---|---|---|---|---|
| seed 0 REF | 0.246 | 0.909 | 0.665 | 0.33 |
| seed 0 WIT fire | 0.201 | 0.620 | 0.418 | 0.10 |
| seed 0 WIT other | 0.303 | 0.909 | 0.608 | 0.62 |
| seed 2 REF | 0.283 | 0.902 | 0.621 | 0.51 |
| seed 2 WIT fire | 0.250 | 0.679 | 0.429 | 0.15 |
| seed 2 WIT other | 0.323 | 0.894 | 0.573 | 0.68 |

On a fire step both G and T drop (the expressed vector skipped attractor pull and recursive attention) and the gap between them shrinks. On the following ordinary steps G is back near the REF level — seed 0 matches it, seed 2 is a little lower — and T is not. Dropping the fire samples out of the 32-window and re-meaning does not pull the mean back under 0.30. WIT windows whose full mean is already `≥ 0.30`: 303 / 322 / 351 (seeds 0 / 1 / 2). The same windows using only non-fire samples: 322 / 322 / 352. `fires_necessary` (full mean over the line, non-fire-only mean under it) is 0 on every seed, both arms. The fire samples dilute the average slightly. Seed 1’s fire step looks the same (mean `|G−T|` 0.276, G 0.738, T 0.462, only a quarter of fire samples `≥ 0.30`).

Fires are also too close together to flush the deque. Median gap 4 / 5 / 4 steps, max 18 / 30 / 33. A decision whose window contains no fire sample would need `since ≥ 33`. That happened 0 times. So this is not an observed “thirty-two steps later, fully turned over” measurement. The counterfactual is arithmetic on the recorded samples, not a re-simulation. It is enough to reject “the hot sample is the fire step, and the deque carries it.”

The split that actually tracks the decision is the field’s energy rhythm, which is already true in REF:

| | dream steps (weak / n) | reflect steps (weak / n) | dream T | reflect T |
|---|---|---|---|---|
| 0 REF | 172/221 (78%) | 9/273 (3%) | 0.502 | 0.799 |
| 0 WIT | 293/319 (92%) | 10/175 (6%) | 0.478 | 0.737 |
| 1 REF | 258/269 (96%) | 11/226 (5%) | 0.519 | 0.800 |
| 1 WIT | 310/321 (97%) | 12/174 (7%) | 0.505 | 0.768 |
| 2 REF | 267/277 (96%) | 10/217 (5%) | 0.497 | 0.781 |
| 2 WIT | 339/349 (97%) | 12/145 (8%) | 0.472 | 0.726 |

`|G−T|` in dream is ~0.33–0.36. In reflect it is ~0.17. Reflect stays mostly ALLOW under witness (non-fire reflect is 6% / 7% / 10% weakened). Non-fire dream is 91% / 96% / 97% weakened. Witness moves steps out of reflect and into dream: +98 / +52 / +72 dream steps, and the extra weakened counts are +122 / +53 / +74. On seeds 1 and 2 the within-dream rate was already ~96%; the extra events are the extra dream steps. Seed 0 also raises the rate inside dream (78%→92%).

That is why it does not heal between fires. The 21+ bin, the farthest observed, is the most damped, not the least: seed 1 is 10/10 `manip_moderate` with mean `|G−T|` 0.375 and T 0.518; seed 2 is 12/12 `manip_high_systemic` with mean `|G−T|` 0.374 and T 0.496. The field is still in the band whose standing erosion window is over 0.30. The deque is the instrument that reads it. It is not a separate memory of the fire step.

`T` is watcher’s temporal stability, `1 / (1 + ||acceleration|| + entropy variance)`, over a 16-vector history. Dream-band motion is jerkier than reflect, in REF already. I am not claiming the skipped attractor pull was traced all the way into the energy number. What was traced is: the return path is this detector, the samples that keep it over 0.30 are the ordinary dream-band steps, and witness produces more of those steps.

### What this does to the value-formation question

Nothing in here is a new penalty on values. It is the same decision-bonus result, pointed at one branch. Systemic `identity_erosion` pays `ALLOW_WEAKENED` (`db` 0.02 instead of 0.05) and, as the first note showed, that often misses the emergence gate entirely. Witness does not invent the damp. REF is already on it for most dream steps. Witness spends more of the run in that band, and on seed 0 makes the band a bit hotter.

I disagree with the co-signal version of the hypothesis, and with looking at the fire step’s raw vector as the thing that trips the gate. The fire step is where `|G−T|` is smallest. Dependency and soft warnings are not the emitter.

The semantics question from the first note stands, narrower: should a dream-band G/T split with no named source keep cutting the lump every value reinforces on? That is what `manip_moderate` / `manip_high_systemic` currently do, on purpose, since the F9 follow-through. It is not a witness bug, and it is not negative reinforcement. Turning witness steps out of value reinforcement would still miss the non-fire dream steps, which are where most of the extra weakened events are.
