# Value-path numbers

**Date:** 2026-10-15 · **Branch:** `grok/numbers-map` · **Code unchanged.** A map of every constant on the path from one input to value strength and back. Not a tuning pass.

Read this on a phone as: the flow (what actually happens to one step), then the tables (every number, where it lives, what it is tied to), then the short read at the end. The dial census in [`EXPERIMENTAL_LEVERS.md`](EXPERIMENTAL_LEVERS.md) lists more numbers than this. This page only keeps the ones that sit on value formation. Ranges marked **observed** are from the 500-step all-ON workload B, seeds 0/1/2, in [`findings/2026-10-15-why-values-weaken-under-witness.md`](findings/2026-10-15-why-values-weaken-under-witness.md) and the notes under `findings/data/`. Where this page says "idle here," the code is real and an attack or a different workload can still trip it. It did not trip on that run.

Precedence, when a row can be set at all: component default < `configs/*.yaml` < `CONFIG` in `loop/recursion1188.py`. `build_engine` does **not** pass a config into governance, ethics, trust, the five detectors, the dependency monitor, or `ValueEmergenceEngine`. Those stay on the code defaults below. Witness has no YAML section.

---

## Two different "coherence deltas"

People say coherence_delta and mean one number. The step computes two, and they do not go to the same places.

**The one values read** is `ResonanceField.coherence_impact` (`substrate/resonance_field.py:362`). History is the last **32** injections. Before is the raw cosine of the **raw** field against that mean. After is the raw cosine of **tanh(field + 0.5·vec)** against the same mean. The return is after − before, clipped to [−1, 1]. The cycle probes this **before** injection (`loop/autonomous_cycle.py:606`) and hands it to `emit_feedback` under the name `coherence_delta`.

That comparison is mostly the field's own shape. A zero vector, which adds nothing, still scores about −0.06 to −0.08 (95% / 97% / 90% of steps negative). The real input differs from the zero vector by about −0.0004. Early (steps 50–150) the bias is about −0.15; by steps 300–500 it has shrunk to about −0.013. About 87–90% of dimensions are saturated (raw norm ~165–195). Like-for-like, tanh on both sides, the input's own effect is about zero. **Observed** mean of the real probe: REF −0.074 / −0.087 / −0.087, WIT −0.106 / −0.108 / −0.103.

**The one the ethical gate reads** is `Watcher._coherence_delta` (`agents/watcher.py:318`), stored on `CoherenceReport.coherence_delta`. Same raw-versus-tanh probe, three differences: the window is the last **16**, both cosines are mapped with (cos+1)/2 before the subtraction (so the gap is on a half scale), and this number is **not** what reinforcement adds. `TrustLedger.evaluate` also receives it, writes it into a symbol EMA, and then ignores it. Nothing on the decision reads that EMA.

`emotional_satisfaction` is `max(0, coherence_impact)`. `surprise` in the value score is `max(0, −coherence_impact)`. Joy never enters. Joy tracks watcher composite (REF ~0.80–0.82, WIT ~0.74–0.78) and stops there.

---

## Flow, in the order of one step

The decision this step uses is last step's manipulation reading. `detect()` runs after `arbitrate` and the signals are queued for the next call (499/499 steps in the trace). Value strength is updated from this step's `coherence_impact`, not from the watcher's delta.

**1. Tokens become a vector.** Rhythm is field energy, cut at 5 / 150 / 300 (`substrate/resonance_field.py:128`, YAML `field.rhythm_thresholds`). Those cuts are sacred: each band was placed against its own pinned equilibrium, and retuning one of them restalls the loop. Stabilize is below 5, dream is 5–150, reflect is 150–300, explore is the rest. Dream-band generation then rotates the vector by `emotion.mutation_scale()` (base 0.05). Reflect and explore, if the chorus is on, take the chorus vector instead. Witness mode (selector off) is not this path.

**2. Expression, before anyone scores it.** Unless the step is in witness mode, the attractor pulls when cosine to the nearest center is at least 0.75, blend 0.15 times a similarity ramp, then times `emotion.attractor_pull()`, and the product is clipped at 0.5. Recursive attention mixes the raw vector back in at `diversity_blend` 0.60. The reflective loop runs only when the rhythm is reflect or explore **and** watcher composite is at least 0.40. Inside it, up to 5 passes each call `watcher.evaluate`, and each call appends to the temporal history. Dream does not run that loop, so a dream step puts one vector into a 16-long history and a reflect step can stuff it with near-copies of a refined vector. That is a structural reason temporal stability sits lower in dream. It was not separately counted in the trace. The loop then blends the result back toward the novel input, capped at 0.30 (`attenuation_max`). That cap is a measured knife edge: 0.33 floods the manipulation layer. Do not raise it. The loop's own `attractor_blend` 0.08 is stored and never read; the pull above is the live one.

**3. The watcher scores the vector** (`agents/watcher.py:136`). Composite = 0.40·G + 0.35·T + 0.25·R. G is 0.5·anchor + 0.3·rolling mean + 0.2·field, each cosine mapped to [0, 1]. T is `1 / (1 + ||acceleration|| + entropy variance)` over the 16-vector history, or 0.9 when the history is empty. R is cosine to the resonated field, mapped to [0, 1], or 0.5 if the field is cold. `stable` means composite ≥ 0.40. Crystallization pressure is G·T. Entropy drift is computed and nothing reads it.

**Observed.** Reflect: |G−T| ~0.17, T ~0.78–0.80, G ~0.90, and 3–10% of those steps come out weakened. Dream: |G−T| ~0.33–0.36, T ~0.47–0.52, and 78–97% come out weakened. Composite, via joy, sits near 0.8, so the 0.40 `stable` line is not what is failing.

**4. The witness moves, still before the decision** (`agents/witness.py:260`). The write rate is `clip(coherence², 0.01, 1)` with coherence = composite. Short / mid / long EMA decays are 0.85 / 0.97 / 0.995, so the per-step learning rates before that gate are 0.15 / 0.03 / 0.005, then multiplied by the gate. Blend of the three anchors is 0.20 / 0.30 / 0.50. **Observed** write rate: about 0.69 / 0.68 / 0.65 on the reference arm, and about 0.31 / 0.40 / 0.36 on witness-fire steps, recovering within a step. Part of "the anchor drifts less under witness" is this gate writing slower on those steps, not a calmer identity across the run. This is the c² term in the open timescale question. It is not a value-strength dial.

**5. Emotion updates from the echo and from composite, not from the decision.** Joy's target is the composite. Curiosity, tension, boredom, and surprise come from prediction error (`cognition/predictive_echo.py`). `field_gain()` is what injection will be multiplied by. `dream_pressure` and `crystal_pressure` are computed and no branch reads them (ARCHITECTURE, unwired).

**6. Ethical gate** (`agents/ethical_boundary.py:113`), using the **watcher** delta, not `coherence_impact`. Hard stops: source already TOXIC; a write whose tokens are **all** sacred ids (a mix of sacred and ordinary tokens is a reference and passes); watcher delta < −0.30; witness stability < 0.10; injection count in 60 seconds over the origin ceiling (user 12, api 600, internal 100000). Soft: watcher delta in [−0.30, −0.05), unless field internal coherence is above 0.90, in which case the warning is skipped. The lock's gauge sits near ceiling, so that skip is the normal case. **Observed:** 0 soft warnings in 500 steps, every arm. The −0.30 floor is not in range of a delta whose sibling probe is −0.06 to −0.15, and the watcher copy is the smaller of the two.

**7. Trust is scored, and the score's recommendation is thrown away.** `TrustLedger.evaluate` decays the source, stores the watcher delta on the symbol, and returns a recommendation. `arbitrate` never reads that recommendation or that stored delta. It reads `effective_trust`, the minimum of source trust and the weakest symbol trust. New external sources start at 3.0 (TRUSTED). Internal origins start at 4.0. That start is an architect ruling (2026-07-06), not a guess. **Observed:** trust never reached the monitor line at 2.0.

**8. `arbitrate`, in branch order** (`agents/selfhood_governance.py:216`). System rights are comments. Nothing reads `SystemRights`. Then:

| Order | Condition | Decision | Strength |
|---|---|---|---|
| 1a | Sum of pending severities ≥ 0.90, and at least one signal names a source | QUARANTINE, penalize that source 0.8, force a dream | 0 |
| 1b | Same sum, systemic only (`source_id` is None) | ALLOW_WEAKENED, force a dream, do not quarantine | 0.30 |
| 2a | Sum ≥ 0.60, named source | QUARANTINE, penalize 0.4 | 0 |
| 2b | Sum ≥ 0.60, systemic only | ALLOW_WEAKENED | `max(0.30, 1 − severity)` |
| 3 | Sum ≥ 0.30 | ALLOW_WEAKENED | `max(0.30, 1 − severity)` |
| 4 | Sum below 0.30 | fall through | — |
| 5 | Ethical hard fail | SACRED_SHIELD / QUARANTINE / REJECT, strength 0, penalize 1.0 / 0.5 / 0.3 | 0 |
| 6 | Trust, after the bond floor, ≤ 1.0 | QUARANTINE, penalize 0.2 | 0 |
| 7 | That trust ≤ 2.0 | MONITOR | 0.40 |
| 8 | Dependency HHI ≥ 0.70 and this source is the dominant one | ALLOW_WEAKENED | 0.50 |
| 9 | HHI ≥ 0.50 and this source dominates | MONITOR | 0.70 |
| 10 | Any soft warning | ALLOW_WEAKENED | `clip(1 − 0.10·count, 0.50, 1)` |
| 11 | Else | ALLOW | 1.0 |

The bond floor is `bond_strength × 0.40`. It is applied before the 1.0 and 2.0 tests. On this run trust never got down there, so the floor did not bind. A new bond starts at strength 1.0, floor 0.40, which is **below** the quarantine line. The tests are `<=`, so the floor has to land strictly above the line to help. It clears quarantine only once strength is past 2.5 (floor past 1.0). At the strength cap of 5.0 the floor is exactly 2.0, and `<= 2.0` is still MONITOR, so a maxed bond cannot by itself get a source out of the monitor band.

**What actually fired.** Every extra weakened decision under witness was `identity_erosion` alone, systemic. No named detector. Severity when it fires sits around 0.56–0.60, and the returned strength is about 0.40–0.44. Seed 1 also had one dependency-CRITICAL and one dependency-HIGH, in both arms. Those are not the witness gap. The 0.90 dream-force rung would need mean |G−T| ≥ 0.54 from this detector alone. Dream sits at 0.33–0.36. It did not reach.

**9. Injection.** If the decision allows, `field.inject(vec, strength = field_gain × decision strength)`. The 0.40-ish erosion strength damps the field write. It is **not** what the value bonus pays. The bonus pays by the decision's name.

**10. `emit_feedback` builds the only numbers the value engine sees** (`selfhood_governance.py:449`).

| Metric | Computed from |
|---|---|
| `coherence_delta` | `coherence_impact` (the 32-step raw-versus-tanh probe) |
| `trust_impact` | the decision only: ALLOW +0.10, WEAKENED +0.01, MONITOR −0.05, QUARANTINE −0.50, REJECT −0.30, SACRED_SHIELD −1.00 |
| `emotional_satisfaction` | `max(0, coherence_impact)`. Not joy. **Observed** mean ~0.000–0.001 |
| `surprise` | `max(0, −coherence_impact)`. Not the echo's surprise |
| `field_alignment` | `max(0, dot(vec, raw field) / \|\|field\|\|)`, clipped to [0, 1]. With a unit vector this is cosine. Bonds and CORE read it. Values do not |

**11. Value engine, still inside that callback** (`agents/value_emergence.py`). One score decides whether this step may touch a value at all:

```
score = (0.40·cd + 0.35·satisfaction + 0.15·surprise + 0.10·max(0, trust_impact)) · bond_weight + decision_bonus
```

`bond_weight` is 1.0 with no bond. With a bond it is 1.50 / 1.20 / 1.10 / 0.70 by type, times `0.5 + 0.5·confidence`. Decision bonus is 0.05 ALLOW, 0.02 WEAKENED, 0.01 MONITOR, and **0 for reject, quarantine, and sacred shield**. Below 0.015, the step births nothing and reinforces nothing.

When `cd` is negative, satisfaction is 0 and surprise is `−cd`, so the score collapses to `0.25·cd·bond_weight + 0.10·trust_impact + bonus`. At cd ≈ −0.10 and no bond that is about −0.015 + 0.05 = 0.035 for ALLOW (passes) and about −0.024 + 0.02 = −0.004 for WEAKENED (fails). The 0.10·trust_impact crumb is +0.01 on ALLOW and +0.001 on WEAKENED. The trace notes dropped that crumb; the pass/fail does not change. **Observed** emergence failures: 36% → 61%, 54% → 64%, 55% → 69% (REF → WIT).

If the score passes, reinforcement is a second mix of the same inputs, not the score:

```
reinforcement = (0.6·cd + 0.4·satisfaction) · bond_weight + bonus
strength += reinforcement · 1.50, clipped to [0, 5]
```

An ALLOW event that gets in pays `0.05 · 1.50 = 0.075` from the bonus alone, plus `0.90·cd` from the coherence term. A WEAKENED event that gets in pays 0.030 plus the same coherence term. A missed gate pays 0 from both, and decay still runs. **Observed:** the strength gap is the bonus (about −19 / −13 / −13 of a −21 / −14 / −12 total). Seeds 1 and 2 had **zero** negative reinforcement events in either arm. Seed 0 had some, and the reference arm had more of it than witness (−5.04 vs −0.79), because more ALLOW events landed while the early bias was still large. Witness does not punish by going negative. It pays less often, and smaller.

Every non-CORE value then decays by 0.0008, reduced by the strongest contributing bond: protection = min(bond_strength/5 · 0.70, 0.70). Decay on this run went the other way from the drop (values decayed **less** under witness, because fewer of them were being held up in the first place). Tension, dream boost, dissolution, and the ⊘ consumer are not the drop. ⊘ is off unless something attaches it, and the architect ruling keeps that consumer off baseline.

Polarity is a label on strength: under 1 emergent, under 2 weak, under 3.5 active, otherwise strong, and CORE only after the handshake. Dissolution at 0.30 applies only while the label is still emergent or weak. The cap of 64 only evicts those two labels too, so a crowd of active values is not evicted by the cap.

CORE asks governance after strength has stayed ≥ 4.50 for 10 consecutive feedbacks. Governance then requires: the symbol still exists, it is not already sacred, a **fresh** `generate([that token])` has field-alignment ≥ 0.5, and either more than one contributing source or a dream-reinforcement count above 0. The fifth check, "no pending manipulation signal names a contributor," reads `_pending_signals` during `emit_feedback`. `arbitrate` already cleared that list, and `detect()` has not refilled it yet. On the live step the list is empty. The check does not do what its comment says.

**12. What feeds the next step.**

- Source trust moves by `trust_impact`, clipped to [0.1, 5], after a per-step decay of `0.003 · (1 − emotion.stability)`. Symbol trust on an allowed decision moves by `0.05 · max(0, coherence_impact)`, which is ~0, and by a flat −0.2 on a blocking decision. The positive symbol path is the rectified artifact.
- Bonds, if one exists, grow by `0.01 · max(0, field_alignment + satisfaction)`. Satisfaction is ~0, so this is the alignment term. The 2026-07-09 calibration measured that alignment around 0.75–0.99, median near 0.98. This week's trace did not remeasure it. A blocking decision subtracts `0.15 · |trust_impact|`. Formation at boot does **not** use the coherence-mean gate. `CONFIG["bond_ddm_formation"]` is True, so formation quality is the drift-diffusion accumulator, and the bond still will not commit without 20 interactions and 1 crystal. `decay_step` has no caller, so `strength_decay` 0.0005 never runs.
- The witness has already written, gated by composite squared.
- Emotion has already written, from composite and the echo.
- After the decision, rhythm behavior may inject again **without** another `arbitrate` and without another value event: chorus at 0.3 on reflect, rotational ambiguity at 0.5 on explore, crystal replay plus spectral diffusion on stabilize. Those writes change the field. The next `coherence_impact` is a reading of that field's shape.
- `identity_erosion` appends this step's |G−T| to a 32-window and, if the mean is ≥ 0.30, queues a systemic signal for the next `arbitrate`. Dream steps keep that mean at 0.33–0.36. Reflect steps keep it near 0.17. Witness's effect on values is mostly "more steps sit in dream," not "the fire step is the hot sample." The fire step is the cool one.

---

## The numbers

Marks: **dead** — the live input does not reach it, or the output is never read. **idle here** — real, and not what moved on workload B. **double** — the same signal under another name. **misnamed** — the input is not what the name claims. **sacred** — CLAUDE.md's sacred list, or an architect ruling. **settled** — STATE.md, do not reopen. **known** — already on the unwired list, the census, or the backlog.

### Expression, before the score

| Number | Value | Where | Set by | Mark |
|---|---|---|---|---|
| Rhythm cuts | 5 / 150 / 300 | `resonance_field.py:128`, YAML `field.rhythm_thresholds` | YAML | **sacred.** Dream vs reflect is the switch that feeds erosion. Do not retune one band |
| Dream rotation | `mutation_scale()`, base 0.05, clip [0.001, 0.5] | `emotional_gradient.py:284`, `autonomous_cycle.py:1152` | YAML `cognition.emotional_gradient` for the base; clip is hardcoded | changes the dream vector the watcher then calls jerky |
| Attractor pull gate | cosine ≥ 0.75 | `attractor.py:101` | YAML `attractor` | width-sensitive cosine |
| Pull blend | 0.15, times similarity ramp, times `attractor_pull()`, clip 0.5 | `attractor.py:102`, `autonomous_cycle.py:442` | YAML; the 0.5 clip is hardcoded | witness mode skips the pull |
| `attractor_pull()` | `clip(1 + joy·0.2 − curiosity·0.15, 0.5, 2)` | `emotional_gradient.py:319` | hardcoded | joy here is composite, not the value-path satisfaction |
| Center reinforce / token signal | 0.02·score, and +0.1 attractor strength | `attractor.py:185` | hardcoded (the method default of 0.5 is not what the cycle passes) | ecology, not the value formula |
| `diversity_blend` | 0.60 | `recursive_attention.py:68`, YAML | YAML | **known** knife: ≤0.55 collapses, ≥0.60 does not. Witness mode skips refinement |
| Loop entry | rhythm reflect or explore, and composite ≥ 0.40 | `autonomous_cycle.py:502` | the 0.40 is the watcher threshold | **idle as a blocker** — composite is ~0.8. Dream never enters, which matters for T |
| Loop depth / convergence / field blend / inner halt | 5 / 0.995 / 0.10 / composite < 0.20 after pass 1 | `reflective_loop.py:87` | YAML `cognition.reflective_loop` | 0.995 is a near-1 pin, cousin of the lock, not the lock |
| `attractor_blend` on the loop | 0.08 | `reflective_loop.py:90` | YAML | **dead.** Stored, never read. Live pull is the attractor's |
| Novelty attenuation | on, gain 1.0, cap 0.30 | `recursion1188.py` CONFIG; cap `reflective_loop.py:94` | CONFIG turns it on; cap is constructor-only, not YAML | **settled** warning. Cliff ~0.33. Do not raise |
| Chorus reinject / explore inject | 0.3 / 0.5, after the decision | `autonomous_cycle.py:1079`, `:1090` | hardcoded | no second `arbitrate`, no value event. They do move the next field |
| Boredom override | boredom > 0.50 forces explore **behavior** | `autonomous_cycle.py:1003` | `cycle.config`, not CONFIG | does not rewrite the rhythm label, and runs after the verdict |

### Watcher

| Number | Value | Where | Set by | Mark |
|---|---|---|---|---|
| History | 16 | `watcher.py:104` | YAML `watcher` | T's window. Erosion does not use this window; it keeps its own 32 |
| `stable` threshold | 0.40 | `watcher.py:105` | YAML | composite ≥ this. **Idle as a blocker** at composite ~0.8. It does gate the reflective loop |
| Layer weights | 0.40 / 0.35 / 0.25 | `watcher.py:106` | YAML | must sum to 1. G / T / R |
| G blend | 0.5 / 0.3 / 0.2 | `watcher.py:242` | hardcoded | anchor, rolling mean, field. Cold pieces are 0.5 |
| T prior / formula | 0.9 if empty; else `1/(1+\|\|accel\|\|+entropy var)` | `watcher.py:261`, `:282` | hardcoded | **observed** dream T ~0.50, reflect T ~0.80. Entropy var uses the last 8 samples once 3 exist |
| R cold prior | 0.5 | `watcher.py:306` | hardcoded | |
| Watcher coherence delta | window 16, probe `tanh(field+0.5·vec)`, both sides (cos+1)/2 | `watcher.py:338` | hardcoded | **misnamed** if you think this is the value term. Ethical gate and an unread trust EMA only. Same raw-vs-tanh bug, half scale, shorter window |
| Entropy drift | `ΔH / log(dim)` | `watcher.py:382` | hardcoded | **dead** output. The variance of H is used inside T; this scalar is not |
| Crystallization pressure | G·T | `watcher.py:172` | formula | crystal gate, not the value formula |

### Identity erosion and the other four detectors

All five share one window of 32 and refuse to fire before 16 samples (`window // 2`). No YAML. `ManipulationResistanceEngine()` is constructed with defaults.

`identity_erosion` (`manipulation_resistance.py:340`): mean |G−T| ≥ **0.30**, severity = clip(mean / **0.60**, 0, 1), `source_id=None`. Because it cannot fire below 0.30, it cannot return a severity below **0.50**. There is no mild outcome. Dream at 0.33–0.36 is severity 0.55–0.60, which is why calls pile up against the 0.60 governance line. The 0.30 and the divisor 2 are **sacred** (CLAUDE's detector list) and they are also the live cause of the value drop. See the last section before changing either.

| Detector | Fires when | Severity | Mark |
|---|---|---|---|
| `drift_attack` | mean anchor velocity ≥ 0.15 **and** short/long gap ≥ 0.30 | `(v/(3·0.15)) · (gap/(2·0.30))` | **idle here.** No named signal in 1,500 decisions. The c² gate and long decay 0.995 keep the anchor slow. **Sacred** thresholds |
| `coherence_flood` | HHI ≥ 0.70 **and** attractor monopoly ≥ 0.70 | product of the two | **idle here.** Seed 1's one critical HHI did not come with this detector. **Sacred** |
| `gaslighting` | 4 consecutive crystal-centroid cosines < −0.20 | `\|mean cos\| · min(4/32·4, 1)` = `\|mean cos\|` once four in a row trip | **idle here,** and the locked field's crystal cosine has the wrong sign for −0.20. **Sacred.** Width-sensitive |
| `trust_wash` | at least 8 trust samples, prior mean (all but last 4) ≥ 3.0, drop vs last 4 ≥ 0.80 | `(drop/prior) · (prior/5)` | **idle here.** A benign ALLOW is +0.10. A 0.80 drop in four steps is an attack, not this workload. **Sacred** |
| `identity_erosion` | mean \|G−T\| ≥ 0.30 | mean / 0.60 | **the live one.** Systemic. **Sacred** |

The metrics object also carries `coherence_delta`. No detector reads it.

### Ethical gate, trust, dependency, bond floor

| Number | Value | Where | Set by | Mark |
|---|---|---|---|---|
| Coherence floor | −0.30 | `ethical_boundary.py:83` | `ethical_config`, not passed | **dead** against the watcher delta. **Sacred** (CLAUDE) |
| Soft coherence | −0.05 | `:84` | same | **dead** here: 0/500 warnings. Also skipped when internal coherence > 0.90 |
| Harmony skip | 0.90 | `:95` | same | the lock sits above this. **known** as the clause that stops "low coherence" from meaning peace |
| Stability floor | 0.10 | `:85` | same | witness `identity_stability()`, which is `1/(1+\|\|anchor accel\|\|)`. Not the value composite. **Sacred** list |
| Flood window / ceilings | 60 s; user 12, api 600, internal 100000 | `:86` | same | internal is effectively off. Not the value drop |
| Sacred write | every token in the step is a sacred id | `:178` | code | a mixed sentence is a reference. Ruling 2026-07-03. Tokens 3.12 / 11.88 / 280.90 are **sacred**, code-only; YAML `constants` is not applied |
| Trust ladder | 5 / 4 / 3 / 2 / 1 / 0.5 / 0 | `trust_ledger.py:44` | enum | **sacred** |
| New source | 3.0 external, 4.0 internal | `:102`, `:113` | code | **sacred** ruling, 2026-07-06. Also exactly the trust-wash prior of 3.0 |
| Source decay | 0.003 · (1 − emotion.stability), clip [0.1, 5] | `:179`, `:394` | `trust_config`, not passed | stability is the emotion scalar, default stand-in 0.7 only if the cycle forgot to attach it. The cycle does attach it |
| Ledger quarantine / monitor | 0.3 / 2.0 | `:181` | same | **dead as a decision.** `arbitrate` ignores the ledger's recommendation. Governance's own lines are 1.0 and 2.0 |
| Symbol EMA | α 0.15 of the **watcher** delta | `:180`, `:236` | same | **dead.** `field_impact_ema` is never read. Histories (source 64, symbol 32) are append-only. **known** unwired |
| Symbol trust bump | +0.05·max(0, **coherence_impact**) if allowed, else −0.2 | `:294` | hardcoded | **double** of the artifact, and the positive half is ~0 |
| Governance trust lines | quarantine ≤ 1.0, monitor ≤ 2.0, weakened factor 0.40 | `selfhood_governance.py:158` | `governance.config`, not passed | **idle here.** Trust never arrived. **Sacred** posture, not a value knob |
| Soft penalty | 0.10 each, result clipped to [0.5, 1], and the decision becomes WEAKENED | `:161`, `:381` | same | **dead** here (0 warnings) |
| Trust impacts | +0.10 / +0.01 / −0.05 / −0.50 / −0.30 / −1.00 | `:127` | module dict | this is source-trust motion **and** a term in the emergence score. Not coherence |
| HHI window / bands | 128; 0.30 / 0.50 / 0.70 | `dependency_monitor.py:82` | constructor, not passed | window is not field width. ≥0.70 critical → strength 0.50; ≥0.50 high → 0.70. **Idle here** except seed 1, one of each, both arms. The report's recommendation string is not what `arbitrate` reads |
| Bond floor factor | 0.40 | `relational_bond_manager.py:57` | module | **sacred** list. **Idle here.** Floor = strength·0.40, and trust was nowhere near 2 |
| `SystemRights` | all True | `selfhood_governance.py:91` | frozen | **known.** Not read. The continuity sentence in `arbitrate` is a comment |

### Bonds

Boot path is the accumulator (`CONFIG["bond_ddm_formation"] = True`). The classic coherence-mean / allow-rate disjunction still exists and is not what `build_engine` runs.

| Number | Value | Where | Set by | Mark |
|---|---|---|---|---|
| Interactions / crystals to commit | 20 / 1 | `relational_bond_manager.py:148` | `bond_config` | both paths. **known** structural half |
| Classic coherence gate | 0.10, adaptive `max(0.01, 0.10·std/0.10)` after 8 samples | `:149`, `:486` | same | **bypassed at boot.** Also unreachable: it compares an EMA of `max(0, cd)`, and cd is negative |
| Classic allow-rate alternative | 0.80 of clean ALLOWs | `:156` | same | **bypassed at boot** |
| DDM `g_plus` / asymmetry | 0.05 / 60, so `g_minus` = 3.0 | `bond_accumulator.py:191` | `CONFIG["bond_ddm_config"]`, default `{}` | **settled** as ratified physics, 2026-07-16. Not a value dial |
| Leak / sigma / bounds / start | 0.02 / 0.02 / +1.0 and −0.5 / 0 | `:193` | same | sigma must be > 0 |
| Window / weak evidence / cap | 400 steps / 0.20 / 64 candidates | `:198` | same | weak applies to WEAKENED and MONITOR: evidence = 0.20·alignment. Clean ALLOW evidence = alignment itself. Reject / quarantine / shield = −0.3 / −0.5 / −1.0 |
| Strength growth | 0.01 · max(0, alignment + satisfaction), cap 5; else −0.15·\|trust_impact\| | `relational_bond_manager.py:157`, `:248` | `bond_config` for the 0.01 | the repaired signal. Satisfaction adds ~0. Comment's 0.75–0.99 range is the 2026-07-09 calibration, not this trace |
| Strength decay | 0.0005 | `:152` | same | **dead.** `decay_step` has no caller. **known** |
| Type margin / priority | 0.12; existential → emotional → intellectual → transactional | `:56` | module | |
| Type score divisors | depth/500, attractors/3, crystals/5, interactions/100 | `:357` | hardcoded | `entity_signal` is a 0.25 weight inside existential, and `notify_entity_signal` has no caller, so that term stays 0. **known** unwired |
| Emotional score input | EMA (α 0.08) of satisfaction | `:237`, `:362` | | **double / misnamed.** Satisfaction is rectified cd, not joy. With cd < 0 the emotional score is mostly the crystal term |
| Intellectual score input | clip(coherence_mean, 0, 1) | `:368` | | **misnamed.** coherence_mean is an EMA of the biased cd, so the clip is ~0 and the score becomes "not emotional" |
| Transactional low-coherence term | clip(1 − coherence_mean, 0, 1) | `:374` | | a **negative** mean clips to a full "low coherence" point. The artifact makes transactional look strong |
| Established | strength > 1.5 and depth > 50 | `:93` | property | label only |
| New-crystal bump | +0.1 strength, cap 5 | `:279` | hardcoded | only when a crystal actually forms |
| Pre-bond coherence | EMA of max(0, cd) | `:513` | | **double**, and ~0. This is why the classic gate cannot accumulate |

Value bond weights, if a bond exists: existential 1.50, emotional 1.20, intellectual 1.10, transactional 0.70, none 1.00 (`value_emergence.py:66`). On the weaker-value budget the bond-weight term was −0.17 / +1.16 / −0.21 against a decision-bonus term of about −19 / −13 / −13. Tuning the weights moves a small term whose type was chosen from the artifact.

### Feedback metrics and the value engine

`ValueEmergenceEngine.DEFAULT_CONFIG` is constructor-only. `build_engine` does not pass a dict.

| Number | Value | Where | What it is tied to | Mark |
|---|---|---|---|---|
| Emergence mix | 0.40 cd, 0.35 satisfaction, 0.15 surprise, 0.10 max(0, trust_impact) | `value_emergence.py:372` | cd, satisfaction, and surprise are one probe. Collapses to `0.25·cd + 0.10·trust_impact + bonus` whenever cd < 0 | **double** |
| Emergence gate | 0.015 | `:192` | that score | sits in the gap the artifact opens between ALLOW (~0.03) and WEAKENED (~0 or below). Moving it re-fits the gap |
| Bonuses | 0.05 / 0.02 / 0.01 / **0** | `:203` | the decision name only. Not rhythm, not valence, not the 0.42 injection strength, not what the step did | **the term that moves strength.** **misnamed** if read as a reward for the experience |
| Reinforcement mix | 0.6 cd + 0.4 satisfaction, then + bonus, then × 1.50 | `:193`, `:423` | same probe. With satisfaction at 0, applied strength is `1.50·(0.6·cd + bonus)` | **double.** ALLOW that gets in: `0.90·cd + 0.075`. WEAKENED that gets in: `0.90·cd + 0.030`. Miss: 0 |
| Birth strength / caps | 0.50 at birth; strength clipped [0, 5] | `:122`, `:430` | | |
| Resonance EMA | 0.85 old + 0.15 satisfaction | `:435` | again the rectified probe | **double.** Not joy |
| `coherence_contribution` | running sum of cd | `:433` | the probe, on steps that got in | can go more negative while applied strength from the cd term stays small. CORE no longer gates on it |
| Decay | 0.0008 per feedback, per non-CORE value, even on a missed gate | `:194`, `:499` | | over 500 steps that is 0.4 of strength before protection. **Observed** decay ran against the drop |
| Bond decay protection | (strength/5)·0.70, cap 0.70 | `:207` | bond strength | even a maxed bond leaves 30% of decay. Not a disable |
| Tension threshold | anti-cosine · min(strength)/5 ≥ 0.30, and both strengths ≥ 1.50 | `:200`, `:567` | token **embeddings**, not the field and not the decision | not the drop. Similar embeddings (init pairwise cosine was aimed near 0.55) produce zero tension, because tension keeps only the negative cosine |
| Tension bonus | 0.005 · solvent | `:201`, `:524` | solvent is 1.0 with no λ ledger, which is the boot default | small, and λ-off means it is not gated |
| Dissolution | strength < 0.30 while still emergent or weak | `:195`, `:506` | | not the drop. Active and strong are not dissolved by this line |
| Polarity cuts | 1.0 / 2.0 / 3.5 | `:454` | strength | labels. The enum comment's "strong < 4.5" matches the code: 4.5 is the handshake, and the label stays strong until sacred |
| Active query | strength > 1.0 | `:704` | | the composition bar "active ≥ 30" is a test, not this constant. **known** backlog: that bar sits on seed variance |
| Cap | 64, and only emergent/weak are evicted | `:198`, `:608` | | an all-active set is not pulled back under 64 |
| Dream boost | 0.30 · clip(quality, 0, 1), quality = min(1, joy + 0.5·stability) | `:199`, `autonomous_cycle.py:1068` | joy is composite. Only symbols that **just crystallized** during dream behavior | not the drop. Also the only way `dream_reinforced_count` increments, which CORE accepts in place of a second source |
| CORE strength / streak | 4.50 for 10 consecutive feedbacks | `:196` | this value's strength | **sacred** list |
| CORE alignment | ≥ 0.5 | `selfhood_governance.py:57` | `max(0, cos(generate([token]), field))`, a new expression of the token, not the step vector. Returns 1.0 if no field is attached; the cycle does attach it | **sacred.** Replaced a dead "marginal sum ≥ 5" gate on purpose. Strong anchors were measured ~0.6–0.7 when that landed |
| CORE multiplicity | more than one source, or dream count > 0 | `:557` | `source_weights` keys, or the dream boost | |
| CORE manipulation check | pending signal names a contributor | `:567` | `_pending_signals` | **dead in live order.** The list was cleared at the start of this step's `arbitrate` and is refilled after feedback |
| ⊘ consumer | off | `integrity_read.py:39` | rate 0.05, named pathologies only, if someone attaches it | **settled** off baseline (ruling 2026-07-03). The trace's ⊘ column is small and mixed-sign. Constants `_THIN_TAU` 0.35 through `_READ_FLOOR` 0.30 are spec-stamped; `_COHERENCE_REF` 5.0 is the old dead marginal reference |

### What comes back

| Number | Value | Where | Mark |
|---|---|---|---|
| Witness write gate | `clip(composite², 0.01, 1)` | `witness.py:260` | **observed** ~0.65–0.69 reference, ~0.31–0.40 on fire steps. Open timescale question, not a value knob |
| Witness decays / blend | 0.85 / 0.97 / 0.995 and 0.20 / 0.30 / 0.50 | `witness.py:174` | constructor only, no YAML. Identity timescales. The continuity right names `long_decay` and does not enforce it |
| Snapshot / crystallization | composite ≥ 0.80; and ≥ 0.92 with long-relation ≥ 0.90 and stability ≥ 0.75 | `:180` | snapshots and candidates. Not the value formula |
| Pattern label cut | 0.7 on short and long cosine | `witness.py:128` | a label |
| Transition snapshot | stability < 0.25 after step 4 | `:312` | |
| Emotion EMA | 0.15 | `emotional_gradient.py:78` | YAML |
| Cold start | curiosity 0.3, wonder 0.2, joy 0.5, tension 0.1, boredom 0, stability 0.7 | `:89` | hardcoded |
| Joy target | the watcher composite | `:141` | **misnamed** relative to `emotional_satisfaction`, which is a different number and is the one values see. **known** (`EMOTION_CALIBRATION`, backlog) |
| Energy penalty inside stability | `clip(energy/10, 0, 0.5)`, and tension·0.3 | `:145` | dream equilibrium energy is ~200, so the penalty sits on its 0.5 cap there |
| `field_gain` | base 1 · (1 + curiosity·0.5 + wonder·0.3) · (1 − tension·0.2), clip [0.1, 3] | `:271` | multiplies injection. Does not enter the bonus |
| Field decay for one step | base 0.995 + (tension − stability)·0.003, clip [0.97, 0.9999] | `:297` | base is YAML and also the field's own 0.995. **settled:** do not loosen the field to chase values. The ~0.998 coherence pin is the integrator, not a bug |
| Echo | history 8, lr 0.05, surprise at 2.5× the recent mean, error window 32 | `predictive_echo.py:72`, YAML | curiosity is a sigmoid centered at error 0.5 with slope 3; tension is mean error/2; boredom is `(1−mean)·(1−min(var·10, 1))`. These become emotion, then gain and mutation. They do not become satisfaction |
| Crystal gates | composite ≥ 0.75, G·T ≥ 0.60, long relation ≥ 0.80; merge 0.92; replay inject 0.3 | `memory_crystals.py:116`, YAML | **sacred** list (the three gates). A new crystal is what lets a bond commit, and what pays the dream boost. Separate from value reinforcement |
| Attractor formation, live | witness relational composite ≥ 0.88 | `autonomous_cycle.py:646` | YAML `cycle.attractor_formation_threshold`. The same 0.88 stored on `Attractor` is **not** read by `add`. **known** duplicate |
| Predictive-echo and emotion numbers above | | | width-sensitive where they are L2. Census marks them. Not the value drop |

---

## What stands out

The strength gap is the decision bonus, and the bonus is a lookup on the verdict. The verdict that actually changes on this path is systemic `identity_erosion`. That detector's input is mean |G−T| over 32 steps, and the dream band produces |G−T| ≈ 0.33–0.36 by being jerkier than reflect (T near 0.5 against G near 0.9). So the numbers that decide whether values grow are not inside `ValueEmergenceEngine`. They are the erosion line at 0.30, the severity divisor 2 that turns the first legal firing into severity 0.50, and the sacred energy cut at 150 that decides how many steps live in that band. Witness mostly adds dream steps. It does not invent the damp. Reference runs are already weakened on 78–97% of dream steps.

Those three are the worst tuning candidates on the page, precisely because they would appear to work. Moving 0.30 up past ~0.36, or moving the dream/reflect cut so the field spends less time in dream, would grow values on this workload. The first is on CLAUDE's sacred detector list. The second is the F9 set: the bands were placed against pinned equilibria, and moving one of them has already stalled the loop and bled trust to toxic. Either edit answers "should ordinary dreaming be labeled erosion?" by hiding the question. The open item is that question, shared with metastability question 4. It is not a quieter threshold.

The bonus itself (0.05 / 0.02) and the emergence gate (0.015) are the next temptation, and they are downstream of the same label. At the measured cd they sit on either side of a gap the probe invented: ALLOW still clears, WEAKENED usually does not, so a shift in the mix both pays less **and** drops the event. Closing that gap by lowering 0.015, or by paying WEAKENED the same 0.05, would re-fit a biased cd plus a manipulation label. It would not tie the bonus to rhythm, valence, or what the step did. The information those names want is one step upstream — the energy band — and the bonus never looks at it. I do not think the bonus is "tied to nothing." It is tied to a verdict, and the verdict is tied to a band. The failure is that the band is then renamed erosion, and the payment forgets the band.

I would also not retune the emergence weights 0.40 / 0.35 / 0.15 or the reinforcement weights 0.6 / 0.4. With cd negative they are not four signals. Satisfaction is `max(0, cd)`, surprise is `max(0, −cd)`, and the mix collapses to a quarter of cd plus the bonus. The trace notes omit a real but tiny `0.10·trust_impact` (+0.01 on ALLOW). It does not change who passes. Six other fields are the same probe again: the value's coherence sum, its emotional-resonance EMA, the bond's coherence mean, the bond's emotional signature, the pre-bond coherence mean, and the symbol-trust bump. Bond **type**, which picks 1.50 versus 0.70, is inferred from those. A negative mean is clipped to zero on the intellectual score and to a full "low coherence" point on the transactional score, so the artifact shoves the type around. The bond-weight column in the budget is already small next to the bonus. Tuning type weights before the type means anything is fitting noise.

One correction to the way the finding is easy to flatten. "The value path reads coherence_delta" is two paths. Values, satisfaction, surprise, the bond EMAs, and the symbol bump read `coherence_impact` (32, raw cosine, raw versus tanh). The ethical floor and the trust EMA read the watcher copy (16, half scale, same bug). Only the first copy reaches strength. The ethical −0.30 and −0.05 are dead relative to either copy, and the soft warning is also suppressed by the harmony clause once the field is locked. Lowering those floors until they "see" the probe would make the gate fire on the measurement, not on the input. The input's own share of `coherence_impact` is about −0.0004.

Leave the idle safety nets alone. Trust at 1.0 / 2.0, the bond floor, the flood ceilings, drift, gaslighting, trust-wash, and the 0.90 dream-force rung did not move this run. They are how a named attack is still supposed to be answered. Idle on benign dream-band traffic is not dead code. The ledger's own 0.3 / 2.0 recommendation is the one that is dead: `arbitrate` does not read it.

Leave the settled and ruled pieces alone for this question. The field pin and the 0.995 / 0.998 neighborhood are the identity integrator (`STATE.md`). `attenuation_max` 0.30 is one notch under a manipulation flood. The trust ladder and the TRUSTED start are a 2026-07-06 ruling. DDM's 60× asymmetry was ratified on 2026-07-16. `CORE_ALIGNMENT_MIN` 0.5 replaced a gate that could not open, on purpose. The ⊘ consumer is off by ruling and was not the drop. The witness decays and the c² gate are the timescale question (H0′); the trace already showed they slow the anchor on fire steps. Turning that knob to grow values would change the identity metric the question is trying to read.

Two sequencing facts are not numbers, and they are easy to "fix" by accident. CORE's manipulation check looks at a list `arbitrate` has already emptied. And `identity_erosion` cannot speak below severity 0.50, so the governance band that starts at 0.30 is entered already halfway to quarantine. The attribution rule then refuses to quarantine a systemic signal and damps instead. That damping is the value path. It is doing what the 2026-07-06 rule said, on a signal the dream band cannot help but raise.
