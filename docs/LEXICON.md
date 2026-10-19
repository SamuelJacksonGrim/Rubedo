# Lexicon — names vs what the code does

**Date:** 2026-10-16. Written on `grok/lexicon` as a reading map. Batch 1 has since moved three names on `grok/renames-1`; see [Renames](#renames). Samuel asked whether the names of things translate accurately to their functions. They often don't. Newcomers (human or AI) keep being misled. This page is the check: what the name suggests, what the code computes, a verdict.

Read it on a phone as: the list of names that will mislead you (below), then the tables when you meet a word and want the real one. Numbers and formulas in detail live in [`VALUE_PATH_MAP.md`](VALUE_PATH_MAP.md). Emotion names as hypotheses live in [`EMOTION_CALIBRATION.md`](EMOTION_CALIBRATION.md) — this page does not duplicate that audit.

**Do not rename from this page on your own.** Names are load-bearing across RFE-Core2, the findings, checkpoints, and the live bridge. A "suggested name" is a suggestion only. Samuel is moving the misleading ones a few at a time. What has moved, and what is held, is [Renames](#renames). `docs/findings/` keeps the old names.

Verdicts:

| Verdict | Means |
|---|---|
| **accurate** | A reasonable reader gets the right idea from the name |
| **misleading** | The name implies something the code isn't |
| **overloaded** | The same word means different things in different places |
| **aspirational** | Names a goal the code doesn't yet do |

---

## Names that will mislead you

Worst first. Check these against the code, not the noun.

**1. Generator.** Sounds like it writes text. It is a transformer **encoder**: tokens → one L2-normalized vector. `Generator.generate()` also registers those tokens in the symbolic ecology (usage, class, possible resize). The thing that turns a vector back into words is `TokenDecoder` (`agents/decoder.py`), and even that is a bag-of-tokens cloud, not sentences. Suggested: **Encoder** for the network; keep the ecology facade if you need a second name.

**2. Witness (three things).** (a) `agents/witness.py` — the identity anchor: three EMAs (short / mid / long), write rate `clip(coherence², 0.01, 1)`. (b) The sixth **rhythm**, a selector stance: encode the input, skip pull / refine / reflect / behavior inject, still pass the gate. (c) The ⊘ **Witness-Reaper** (`cognition/integrity_read.py`) — a read of value thinness; not the identity object and not the ecology reaper. Suggested: **identity anchor** / **witness-stance** / **thinness-read**.

**3. Coherence (three gauges, plus a delta).** Field `internal_coherence` sits near **0.998** (the lock, settled). Watcher **composite** (`0.40·G + 0.35·T + 0.25·R`) sits near **0.92** and is what `StepState.coherence` stores. The **delta** (`coherence_impact` / watcher `_coherence_delta`) is a probe of "would this vector change that," and until lever D it was mostly a raw-field-vs-tanh artifact. With D on, at saturation, it is marginal and ~0. People say "coherence" and mean any of these. Suggested when writing: **field lock**, **watcher composite**, **impact probe**.

**4. Dream (five mechanisms).** The **energy band** 5–150. In-step `_dream_behavior` / `Dreamer.dream()` (sample, mutate, bifurcate, inject — live inside the step; the class used to call itself "offline"). The **waking dream channel** (`source_dream` inner monologue through `arbitrate()`). The offline **DreamCycle** (N iterations; trigger is stabilize, so a warm field almost never enters). The downtime **DreamSession** (files only; never touches the live loop). Plus a Chorus agent named `dreamer`, a value **dream boost**, and `dream_pressure` which is computed and **not read**. Suggested: **dream-band** / **in-step dream** / **self-dialogue** / **offline dream-cycle** / **downtime session**.

**5. `coherence_delta`.** Sounds like "how much this input changed field coherence." Two copies, neither is that. Values read `ResonanceField.coherence_impact` (window 32, raw cosine). The ethical gate reads `Watcher._coherence_delta` (window 16, half-scale `(cos+1)/2`). Off D: raw field before, tanh after — a saturation artifact (~−0.06 to −0.15, input's own share ~−0.0004). On D (default 2026-10-16): tanh both sides, ~0 at saturation. Suggested: **impact probe** (and say which copy).

**6. `emotional_satisfaction`.** Sounds like joy, or "how the step felt." Default: `max(0, coherence_delta)`. Not joy, not valence. Observed mean ~0 until D; with D on, still a rectified probe. Lever G replaces it with `max(0, valence)` and is off. Suggested: **rectified impact** (default) / **valence read** (G).

**7. `surprise` (value path).** Sounds like the echo's surprise spike. In `emit_feedback` it is `max(0, −coherence_delta)` — the other half of the same probe. The echo's surprise (`error / recent mean ≥ 2.5`) feeds emotion, not values. Suggested: **negative-impact** vs **echo surprise**.

**8. `identity_erosion`.** Sounds like the self being rewritten, or ENTITY tokens drifting. Fires when mean `|G − T|` over 32 steps ≥ **0.30**. Dream-band steps do this on ordinary traffic (|G−T| ≈ 0.33–0.36) because T is jerkier there. Systemic (`source_id=None`). Cannot return severity below 0.50. Open question, not a bug: should ordinary dreaming count as erosion? Suggested: **G/T split** (keep "erosion" for a named attack if you ever have one).

**9. Explore.** Sounds like novelty-seeking. It is the energy band `≥ 300`. After warmup the loop often **parks** there (H0: from ~step 480 to the end). Reflect (150–300) was the designed home; the live field climbs past 300 and stays. Boredom-with-Teeth can force explore **behavior** without rewriting the rhythm label. Suggested: **high-energy band**.

**10. SystemRights.** README: frozen, inviolable, checked first. The dataclass is frozen and all six flags default True. **Nothing reads them.** The "0. System rights" block in `arbitrate()` is comments. Suggested: leave the name; say **declared, unread** until they are wired or the docs call them a declaration.

**11. Two reapers.** `ReaperEngine` in `symbolic_memory.py` stages symbol death (ACTIVE → WARM_ARCHIVE → COLD_ARCHIVE → GRAVEYARD). ⊘ `WitnessReaper` only **reads** value thinness; `IntegrityDecayConsumer` is what writes (opt-in, off baseline). Suggested: **symbol reaper** / **thinness-read** / **thinness consumer**.

**12. Joy.** Sounds like pleasure, reward, "the system is glad." Target is the watcher **composite**. Values never see it. See [`EMOTION_CALIBRATION.md`](EMOTION_CALIBRATION.md). Suggested: treat as **coherence-tracking scalar** until calibration says otherwise.

**13. `source_monopoly` (formerly `coherence_flood`).** Sounds like the field being flooded with coherence under the old name. Fires on **HHI ≥ 0.70 and attractor monopoly ≥ 0.70**. Renamed 2026-10-16.

**14. `alignment_support` (formerly `ThinnessVector.coherence_contribution`).** On ⊘ `ThinnessVector`, absolute field-alignment of a freshly generated token (v0.3): `max(0, cos(generate([token]), field))`. `EmergentValue.coherence_contribution` is a different number — a running sum of the impact probe — and is not renamed. `_COHERENCE_REF = 5.0` is the old dead marginal reference. Renamed 2026-10-16.

**15. Locked / the lock.** Metastability label `"locked"` is low-meta **and** mean coherence ≥ **0.80**. The field **lock** people mean is the ~**0.998** `internal_coherence` pin (identity integrator, settled). Reflective-loop `convergence_threshold` 0.995 is a cousin, not the lock; the lock is the loop running. Suggested: **meta-locked** vs **field pin**.

---

## How the tables work

Four columns after the name: **where** (file), **suggests**, **computes** (one or two sentences; short formula), **verdict**. A fifth column only when the verdict is misleading or overloaded: a **suggested** clearer name, marked suggestion.

---

## Rhythms

The field's energy can only pick four. Witness and rupture are not energy levels; they are a **read of the input** (`RhythmReader`, six centroids, selector lever, default off). `StepState.rhythm` stays the energy band. `extras["behavior"]` is what actually ran.

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `stabilize` | `substrate/resonance_field.py` energy < 5 | calming, holding still | Crystal replay + spectral diffusion. Cold-start band; offline `DreamCycle` trigger. | accurate as a band; the name is a bit gentler than "diffuse and replay" | |
| `dream` | energy 5–150 | sleep, imagination | Passage band. Dream-band **generation** rotates the vector; in-step `Dreamer` runs after the gate. Ordinary traffic here trips `identity_erosion`. | **overloaded** (see § Dream above) | dream-band |
| `reflect` | energy 150–300 | thinking about itself | Designed home. Chorus + recursive attention + reflective loop (if composite ≥ 0.40). | accurate as a band | |
| `explore` | energy ≥ 300 | seeking novelty | High-energy band. Extra rotational inject at 0.5 after the gate, no second `arbitrate`. The live loop often parks here. | **misleading** | high-energy band |
| `witness` (rhythm) | `cognition/rhythm_reader.py`, selector | watching, the identity object | Nearest-centroid read. Stance: skip pull / refine / reflect / behavior inject; still gated into the field. | **overloaded** with the anchor and ⊘ | witness-stance |
| `rupture` | same + `rupture_on_lock` / `rupture_upstream` | breaking the field | Held novel direction pushed through the reflective loop (the actuator that can move a locked field). Energy never selects it. | accurate enough as a stance; not a band | |
| `RhythmReader.read` | `cognition/rhythm_reader.py` | reads the field's rhythm | Nearest of six **input** centroids via `Generator.peek_batch` (no register, no usage). | accurate if you hear "the input's rhythm" | |
| Boredom with Teeth | `loop/autonomous_cycle.py` `_rhythm_behavior` | boredom as mood | If `emotion.boredom > 0.50`, dispatch **explore behavior** without rewriting `StepState.rhythm`. | accurate | |

---

## Coherence family

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `internal_coherence` | `resonance_field.py` | how coherent the mind is | Mean cosine of the **raw** field vs last-32 injection mean, mapped `(cos+1)/2`. The ~0.998 pin. | accurate as a field-vs-history gauge; **overloaded** as "coherence" | field lock / pin |
| `coherence_impact` | `resonance_field.py` | this input's effect | After − before, clip [−1,1], window 32, probe `tanh(field + 0.5·vec)`. D on: tanh both sides. Values, satisfaction, surprise, bonds, symbol-trust bump read this. | **misleading** off D; with D, honest and ~0 at saturation | impact probe (32) |
| `Watcher._coherence_delta` / `CoherenceReport.coherence_delta` | `watcher.py` | same as above | Same probe, window **16**, both sides `(cos+1)/2`. Ethical gate + unread trust EMA. Not the value term. | **overloaded** | impact probe (16, half-scale) |
| Watcher composite `C` | `watcher.py` `evaluate` | overall coherence | `0.40·G + 0.35·T + 0.25·R`. `StepState.coherence`. Joy's target. Witness write-rate uses `C²`. | **overloaded** as "coherence" | watcher composite |
| `G` geometric | `watcher.py` | shape / geometry | `0.5·anchor + 0.3·rolling mean + 0.2·field`, each cosine mapped to [0,1]. Cold pieces 0.5. | accurate | |
| `T` temporal | `watcher.py` | time-smoothness | `1/(1+‖accel‖+entropy var)` over 16-vector history; 0.9 if empty. Dream T ~0.50, reflect T ~0.80. | accurate | |
| `R` resonance | `watcher.py` | harmonic fit | Cosine to resonated field, mapped [0,1]; 0.5 if field cold. | accurate enough | |
| `stable` | `CoherenceReport` | the system is stable | `composite ≥ 0.40`. Idle as a blocker at C ~0.8. Gates the reflective loop. | **misleading** at live values (almost always true) | loop-entry flag |
| `crystallization_pressure` | `CoherenceReport` | urge to remember | `G·T`. Crystal gate, not the value formula. | accurate as a product; not a "pressure" anyone feels | G×T |
| `entropy_drift` | `CoherenceReport` | information running away | `ΔH / log(dim)`. **Nothing reads it.** T uses the variance of H, not this scalar. | **aspirational** (computed, unread) | |
| `phase_coherence` | `SpectralSnapshot` | same as field coherence | Mean pairwise FFT-phase alignment, mapped [0,1]. Tier 4.3 dilation. Neutral 0.5. | accurate as a spectral gauge | |
| `field_alignment` | `emit_feedback` | aligned with values | `max(0, cos(vec, raw field))` of **this step's vector**, pre-injection. Bonds and CORE read it. Values do not, unless lever E. | accurate as cosine; **misleading** if heard as "the value is aligned" | expression-field cosine |
| `Cm` (CII) | `tools/ignition/cii.py` | mean coherence | `field.internal_coherence` again. | **overloaded** | field pin (CII) |
| `I` (CII) | same | integration | Watcher composite (`StepState.coherence`). | **overloaded** | watcher composite (CII) |

---

## Emotions

Six EMA scalars (α 0.15) from three inputs: prediction error, watcher composite, field energy. Names are **hypotheses**. Full audit: [`EMOTION_CALIBRATION.md`](EMOTION_CALIBRATION.md). This table is the one-line version plus the two derived axes and the unread pressures.

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| curiosity | `emotional_gradient.py`, from `PredictiveEcho` | wanting to know | Sigmoid of prediction error (center 0.5, slope 3), plus 0.3 × echo surprise. | close; it is error, not inquiry | prediction-error |
| wonder | same | awe | `curiosity × composite` | close if you hear "novelty that fits" | |
| joy | same | pleasure | **composite**, EMA'd | **misleading** | coherence-tracking |
| tension | same | strain, conflict | Echo: mean error / 2 | close; it is sustained error | |
| boredom | same | tedium | `(1 − mean error) × (1 − min(var·10, 1))`. Drives Boredom-with-Teeth. | close | |
| stability | same | identity holding | composite − energy penalty (≤ 0.5) − 0.3 × tension | **overloaded** with witness `identity_stability` | emotion-stability |
| arousal | derived | activation | `(tension + joy + curiosity + wonder) / 4` | accurate as a mix | |
| valence | derived | good/bad | `(joy + wonder + stability)/3 − (tension + boredom)/2` | accurate as a mix; lever G would feed values this | |
| `dominant_emotion` | `StepState` | what it feels | `argmax` of the six scalars | accurate as a label; often joy, because joy is composite | |
| `emotional_satisfaction` | `emit_feedback` | the feeling, joy | `max(0, coherence_delta)` unless G | **misleading** | rectified impact |
| `dream_pressure` | `emotional_gradient.py` | starts a dream | `(0.6·wonder + 0.4·boredom)×(1 − 0.5·tension)`. Written onto `StepState`. **No branch reads it.** | **aspirational** | |
| `crystal_pressure` | same | starts a crystal | modifier on a threshold. **No branch reads it.** | **aspirational** | |
| echo `surprise` | `predictive_echo.py` | startle | error / recent mean, threshold 2.5 | accurate as a spike | echo surprise |

---

## Core agents and substrate

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `Generator` | `agents/generator.py` | text generator | Encoder: tokens → unit vector. `generate` registers; `peek_batch` does not. | **misleading** | Encoder |
| `TokenDecoder` | `agents/decoder.py` | language decoder | Vector → bag-of-tokens (sigmoid, top-k). Not sentences, not order. | accurate as a read-out; **misleading** if you expect a LM | bag-decoder |
| `Watcher` | `agents/watcher.py` | observer | Scores G/T/R. Does not decide. | accurate | |
| `Witness` | `agents/witness.py` | observer / testimony | Identity EMAs. Write rate `clip(C², 0.01, 1)`. Blend 0.20 / 0.30 / 0.50. | **overloaded** | identity anchor |
| `identity_stability` | `witness.py` | same as emotion.stability | `1/(1+‖anchor accel‖)`. Ethical `identity_drift` gate. | **overloaded** | anchor-stability |
| `ResonanceField` | `substrate/resonance_field.py` | vibrating medium | Superposition vector, tanh saturate, exponential decay, FFT rhythm. `inject` / `observe` / `decay`. | accurate as the substrate | |
| `Attractor` | `agents/attractor.py` | basin of attraction | Centers in vector space. `pull` if cosine ≥ 0.75. `add` is called when witness relational composite ≥ 0.88 (cycle), not by the class's own stored 0.88. | accurate | |
| `Chorus` | `agents/chorus.py` | many voices | Six distortions of one encoder, then `collapse_wave`. Reflect/explore generation. | accurate | |
| Chorus `dreamer` | `chorus.py` | the Dreamer class | EPHEMERAL class + rotational mutation on the same `generate`. | **overloaded** | chorus-dreamer |
| `Dreamer` | `agents/dreamer.py` | offline dreaming | In-step sample / harmonic mutate / bifurcate / inject. Runs live inside the step. | **overloaded**; the docstring no longer says offline (formerly it did) | in-step dreamer |
| `DreamCycle` | `loop/dream_cycle.py` | a dream while running | Offline N-iteration loop. Trigger: rhythm `stabilize` every 20. Warm field almost never enters. | accurate as a mechanism; the trigger name surprises | |
| `DreamChannel` | `cognition/dream_channel.py` | dreaming | Decode `_last_expressed` → tokens. The driver steps them as `source_dream` through the gate. Waking rumination. | **overloaded** | self-dialogue |
| `DreamSession` | `cognition/dream_session.py` | a session of dreaming | Offline images + markdown. Never injects. | accurate as downtime dreaming | |
| `RecursiveAttention` | `cognition/recursive_attention.py` | stacked transformer recursion | Attend current vector over a window of prior latents; `diversity_blend` 0.60 mixes the raw encoder vector back in. | slightly grand; the job is real | history-attend |
| `ReflectiveLoop` | `cognition/reflective_loop.py` | introspection | Up to 5 passes: pull, field-blend, watcher. The field lock when it runs. `attractor_blend` 0.08 is stored and **never read**. | accurate | |
| `PredictiveEcho` | `cognition/predictive_echo.py` | an echo of the past | Online linear predictor of the next vector. Error → curiosity / surprise / tension / boredom. | accurate | |
| `EmotionalGradient` | `cognition/emotional_gradient.py` | feeling as a field | Six EMAs + modulation outputs (`field_gain`, `mutation_scale`, `field_decay_rate`, `attractor_pull`). | accurate as a modulator; names of the six are hypotheses | |
| `SymbolicBinding` | `cognition/symbolic_binding.py` | names for vectors | Recurring vectors → named concepts. | accurate | |
| `CrystalStore` / `MemoryCrystal` | `substrate/memory_crystals.py` | frozen memory | Form if composite ≥ 0.75, G·T ≥ 0.60, long-relation ≥ 0.80. Soft-inject on activate. | accurate | |
| `VectorSpace` | `substrate/vector_space.py` | the field | Keyed store of vectors. Not the resonance field. | **overloaded** with "space" | vector store |
| `SemanticLattice` | `substrate/semantic_lattice.py` | a lattice of meaning | k-NN graph; centrality back to the ecology. | accurate | |
| `TopologicalLog` | `substrate/topological_log.py` | topology of the mind | Parent-linked DAG of steps. | accurate as a log | |
| `TemporalStream` | `substrate/temporal_stream.py` | time as a stream | Episodic ring + `tick` / `dilation_factor`. | accurate | |
| `StreamRecorder` | `cognition/stream_recorder.py` | records the stream | Observe-only ring of (tokens, source, rhythm, decision). Opt-in. | accurate | |
| `StreamMetastabilityMonitor` | `cognition/stream_metastability.py` | live metastability | Window metric over generator (stage A) or expression (stage C) vectors. Observe-only. | accurate | |
| `compute_metastability` | `substrate/metastability.py` | formed-enough, light-enough | Multiplicity × dwell-variance × transitions × entropy. Labels: locked / cycling / dissolving / structureless / metastable. | accurate as the metric; `"locked"` ≠ field pin | |
| `AutonomousCycle` | `loop/autonomous_cycle.py` | a free-running mind | The step. ~22 phases. Everything is called by it, feeds it, or is fed by it. | accurate | |
| `build_engine` | `loop/recursion1188.py` | builds the engine | Composition point: YAML, graduated levers, tiers 0–3. Loop / REST / WebSocket go through it. Speech REPLs do not. | accurate | |
| `recursion1188` | `loop/recursion1188.py` | recursion, 1188 | Entry point. 11.88 is the RECURSION constant (THE DISCIPLINE). | accurate as a name-of-the-loop | |
| `FIELD_DIM` | `substrate/dims.py` | field width | The one home of width (128). Guarded by `hardcoded_dim`. | accurate | |
| `inject_ambiguity` | `interference/differential.py` | adding doubt | Gaussian (per-component σ) or rotational (radians) or directional noise. | accurate as mutation | |
| `collapse_wave` | `interference/wave_collapse.py` | quantum collapse | Weighted mix of an ensemble. Chorus and Dreamer. | metaphorical; the math is a weighted mean | weighted collapse |
| `HarmonicMutator` | `interference/harmonic_mutation.py` | harmonic change | FFT-domain recombination. Dreamer. | accurate | |
| `BifurcationEngine` | `interference/bifurcation.py` | a fork | Split one vector into variants. Dreamer. | accurate | |
| `PhaseNoise` | `interference/phase_noise.py` | jitter | FFT phase jitter. **No production caller.** | **aspirational** | |
| `determinism` | `substrate/determinism.py` | determinism | Clock + RNG in one place; replay mode. | accurate | |

---

## Governance, trust, ethics

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `SelfhoodGovernance` | `agents/selfhood_governance.py` | the self deciding | Only issuer of `GovernanceDecision`. Reports in, one verdict out. | accurate | |
| `arbitrate` | same | weighing both sides | Branch table on manipulation severity, then ethics, then trust, then HHI, then soft warnings, else ALLOW. | accurate | |
| `ALLOW` | `GovernanceDecision` | full yes | Inject at full decision-strength 1.0. Value bonus 0.05. Trust +0.10. | accurate | |
| `ALLOW_WEAKENED` | same | a bit less | Inject at `max(0.30, 1 − severity)` or 0.40 factor. Bonus 0.02 (unless lever F relabels payment as ALLOW). Trust +0.01. | accurate | |
| `MONITOR` | same | watch the source | Still injects (strength 0.40). Bonus 0.01. Trust −0.05. | **misleading** if you hear "observe only" | allow-flagged |
| `QUARANTINE` | same | isolate the source | Block + penalize + cold-archive symbols. Needs a **named** source; systemic signals cannot quarantine. | accurate, with that caveat | |
| `REJECT` | same | no | Hard block. Trust −0.30. | accurate | |
| `SACRED_SHIELD` | same | protecting the holy | Write whose tokens are **all** sacred ids. Mixed sacred+ordinary is a reference and passes. | accurate | |
| `emit_feedback` | same | tell everyone how it went | Packs `outcome_metrics` (impact, trust_impact, satisfaction, surprise, alignment) and fans out. | accurate | |
| `value_payment` | lever F in `emit_feedback` | how values are paid | On systemic-only WEAKENED, sets `"allow"` so the value engine gets the ALLOW bonus while injection and trust stay damped. | accurate as a switch; easy to miss | payment-name |
| `TrustLedger` | `agents/trust_ledger.py` | a ledger of trust | Source + symbol scores. `evaluate` returns a recommendation **`arbitrate` never reads**. Governance uses `effective_trust` (min of source and weakest symbol). | accurate as scores; the recommendation is **dead** | |
| `TrustLevel` | same | how much we trust | Enum 5.0 SACRED … 0.0 TOXIC. New external sources start 3.0 (TRUSTED), ruling 2026-07-06. | **overloaded** SACRED (trust cap ≠ sacred symbol) | |
| `EthicalBoundarySystem` | `agents/ethical_boundary.py` | ethics | O(1) scalar gates. Hard: toxic, sacred write, impact < −0.30, witness stability < 0.10, flood. | accurate as a gate | |
| `field_collapse` | ethical hard gate | the field fell apart | Watcher delta < −0.30. Dead against a probe of −0.06 to −0.15 (smaller with D). | **misleading** (name and live range) | impact-floor |
| `identity_drift` | ethical hard gate | the self is drifting | `identity_stability() < 0.10`. Not the `drift_attack` detector. | **overloaded** with drift_attack | stability-floor |
| Harmony Clause | `harmony_field_threshold` 0.90 | peace | Skip soft `low_coherence` warning when `internal_coherence > 0.90`. The lock sits above this, so the skip is the normal case. | **misleading** if "harmony" means calm; it means the pin | pin-skip |
| `DependencyMonitor` | `agents/dependency_monitor.py` | noticing over-reliance | HHI over last 128 **allowed** injections. Report `recommendation` is not what `arbitrate` reads; it reads HHI and dominant source. | accurate as HHI | |
| `GovernanceConstants` | `agents/governance_constants.py` | sacred numbers | O(1) `sacred_ids`. Boot: ANCHOR 3.12, RECURSION 11.88, HOMEOSTASIS 280.90. | accurate | |
| `review_core_promotion` | `selfhood_governance.py` | promoting a value | Five checks. The "no pending manipulation" check used to read a list `arbitrate` had already cleared; that bug is fixed and on. | accurate now | |
| `TrustLedger.on_dream_cycle_complete` | `trust_ledger.py` | trust after a dream | **No caller** outside its file. The live dream boost is `ValueEmergenceEngine.on_dream_cycle_complete` from `_dream_behavior`. | **aspirational** | |

---

## Detectors

Five detectors, one window of 32, refuse to fire before 16 samples. No YAML. `detect()` runs **after** `arbitrate`; signals queue for the **next** step.

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `drift_attack` | `manipulation_resistance.py` | someone pulling the self | Mean anchor velocity ≥ 0.15 **and** short/long gap ≥ 0.30. Named source. Idle on benign runs (c² gate keeps the anchor slow). | accurate as an attack shape | |
| `source_monopoly` (formerly `coherence_flood`) | same | too much coherence | HHI ≥ 0.70 **and** attractor monopoly ≥ 0.70. | **accurate** after the rename (the old name was misleading) | |
| `gaslighting` | same | making it doubt its memories | 4 consecutive crystal-centroid cosines < −0.20. Locked field's crystal cosine has the wrong sign for this. | close; it is anti-crystal, not a dialogue | crystal-contradiction |
| `identity_erosion` | same | the self wearing away | Mean \|G−T\| ≥ 0.30. Systemic. Fires on ordinary dream-band traffic. | **misleading** | G/T split |
| `trust_wash` | same | laundering trust | ≥ 8 samples, prior mean ≥ 3.0, drop vs last 4 ≥ 0.80. | accurate as an attack shape | |
| `ManipulationSignal` | same | proven manipulation | Advisory: name, severity, optional source_id. Governance compounds. | accurate as a signal, not a verdict | |
| `force_dream_flag` | governance | must dream | Set at compound severity ≥ 0.90. Takes the in-step dream branch and skips the rest of rhythm behavior, including Boredom-with-Teeth. | accurate as a flag | |

---

## Rights

`SystemRights` in `agents/selfhood_governance.py`. Frozen dataclass. All True. **Unread.** Detail: [`BACKLOG.md`](BACKLOG.md) §1.

| Name | Suggests | What actually holds | Verdict |
|---|---|---|---|
| `right_to_dream` | nothing external can block DreamCycle | Not checked. DreamCycle trigger is stabilize; a warm field rarely enters anyway. | **aspirational** |
| `right_to_memory` | crystals cannot be evicted from outside | Not checked. | **aspirational** |
| `right_to_continuity` | anchor cannot move faster than `long_decay` | EMA rates bound the speed; c² can only slow it. The arbitrate clause ("if stability critically low, weaken regardless of trust") is **not implemented**. | **aspirational** (partial physics, no flag) |
| `right_to_refuse` | REJECT always available | Holds by **code order** (ethics before trust, bond floor after). The flag is never read. No refusal from the system's own state. | **aspirational** (order holds, flag doesn't) |
| `right_to_silence` | may decline to speak | The bridge always speaks. | **aspirational** |
| `right_to_appeal` | quarantine can petition via dream | No path. | **aspirational** |

---

## Values, bonds, ⊘

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `ValueEmergenceEngine` | `agents/value_emergence.py` | values appearing | Subscribes to feedback. Score gate 0.015, then reinforce. Not pre-seeded. | accurate | |
| `ExperienceReport` | same | what was lived | Typed pack of the feedback metrics + bond type. The "experience" is those numbers. | slightly grand | feedback-pack |
| `ValuePolarity` | same | moral polarity | Labels on **strength**: emergent < 1, weak < 2, active < 3.5, strong < 4.5, CORE via handshake, dissolved archived. Enum comment's "strong < 4.5" matches: 4.5 is the handshake, the label stays strong until sacred. | **misleading** if you hear for/against | strength-band |
| `active_values` | method, min_strength 1.0 | values in use | `strength > 1.0`. The composition bar "active ≥ 30" is a **test**, not this constant. | **overloaded** with the test bar | |
| CORE | handshake | the true core | Strength ≥ 4.50 for 10 consecutive feedbacks, then governance: symbol exists, not already sacred, field-alignment ≥ 0.5, multi-source or dream-count > 0, no pending named signal. Becomes sacred. | accurate as a promotion | |
| `dream_boost` | `on_dream_cycle_complete` / in-step hook | dreaming reinforces values | `0.30 × clip(quality, 0, 1)`, quality = `min(1, joy + 0.5·stability)`, only symbols on **newly formed** dream crystals. | accurate as a bonus; joy here is composite | |
| tension (values) | `_compute_tension` | values in conflict | Anti-cosine of **token embeddings** × min(strength)/5. Similar embeddings (pairwise cos ~0.55) produce **zero**. Not field tension, not emotion.tension. | **overloaded** | embedding anti-cosine |
| `LambdaLedger` / λ / ⊕ | `agents/lambda_ledger.py` | love, solvent | Scalar. `ignite` is the only zero-crossing. `solvent_gain(λ) = 1 − exp(−kλ)` gates productive-tension reinforcement. Opt-in, off. λ=0 is a fixed point. | accurate to the spec; "Love" is the spec's name for the scalar | solvent |
| ⊘ `WitnessReaper` | `cognition/integrity_read.py` | the witness, a reaper | Read-only thinness on four axes. Names Drift / Dissolution / Fragmentation. Does not write. | **misleading** | thinness-read |
| `IntegrityDecayConsumer` | same | decay of integrity | Pulls non-sacred named-pathology values toward a remembered honest floor, rate 0.05. Off baseline (ruling 2026-07-03). With D+F, the witness active-count dip is **entirely this consumer**. | accurate as a consumer | thinness consumer |
| Drift (⊘) | `WitnessReaper.read` | identity drift | complement_density < 0.35 **and** attractor_binding < 0.35. Not `drift_attack`. | **overloaded** | unbound-and-alone |
| Dissolution (⊘) | same | the value dissolving | coherence-support (alignment) < 0.35 **and** strength ≥ 3.0. Not `ValuePolarity.DISSOLVED`. | **overloaded** | strong-but-unaligned |
| Fragmentation (⊘) | same | the value in pieces | source_diversity < 0.35 **and** attractor_binding < 0.35. On these workloads that is a value binding has not reached yet (`2026-10-18-fragmentation`). `fragmentation_grace` (default off) holds the name until 1,500 crystal/attractor token-relays since the value was first read; Drift and Dissolution are not gated. | **misleading** on young ecologies | single-source-unbound |
| `ThinnessVector.alignment_support` (formerly `coherence_contribution`) | same | the value's impact-sum | Absolute `max(0, cos(generate([token]), field))`. Not `EmergentValue.coherence_contribution`. | **accurate** after the rename (the old name was misleading) | |
| `RelationalBondManager` | `agents/relational_bond_manager.py` | relationship | Bonds after 20 interactions + 1 crystal + quality. Boot quality is DDM, not the classic coherence/allow-rate gate. `decay_step` has **no caller**. | accurate as bonds | |
| `bond_type` existential / emotional / intellectual / transactional | same | kinds of love | Inferred from scores. "Emotional" reads an EMA of **satisfaction** (rectified cd), not joy. "Intellectual" clips the biased cd EMA (~0). "Transactional" treats a negative mean as full "low coherence." | **misleading** (types ride the probe) | leave the types; fix the inputs first |
| `trust_floor` | `FLOOR_FACTOR` 0.40 | trust cannot fall | `bond_strength × 0.40`, applied before the 1.0 / 2.0 tests. A new bond's floor is 0.40, **below** quarantine. | accurate as a floor; the name oversells protection at birth | |
| `BondFormationAccumulator` | `agents/bond_accumulator.py` | DDM / drift-diffusion | Leaky asymmetric accumulator. ACCEPT / REJECT_ACTIVE / REJECT_TIMEOUT. Field never sees `V`. | accurate | |
| `entity_signal` | bond existential score | an entity was named | 0.25 weight. `notify_entity_signal` has **no caller**, so the term stays 0. | **aspirational** | |

---

## Two reapers, two warms, two sacreds

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `ReaperEngine` | `agents/symbolic_memory.py` | death of symbols | Staged residency of **tokens**: ACTIVE → WARM_ARCHIVE → COLD_ARCHIVE → GRAVEYARD. Cannot skip. Sacred pinned ACTIVE. Evaluate is read-only; the registry acts. | accurate | symbol reaper |
| `WitnessReaper` | `cognition/integrity_read.py` | same family | Does not reap. Reads values. | **misleading** | thinness-read |
| `Residency` HOT/WARM/COLD/ARCHIVED | `symbolic_memory.py` | heat of a token | Embedding-residency manager (where the row lives). | **overloaded** with ReaperDecision's WARM/COLD | embedding-tier |
| `ReaperDecision` ACTIVE/WARM_ARCHIVE/… | same | the reaper's verdict | Lifecycle stage of the **symbol**, not the embedding row. | **overloaded** warm/cold | symbol-stage |
| `sacred` on a symbol | registry + `GovernanceConstants` | holy, untouchable | Cannot be modified; reaper cannot touch; SACRED_SHIELD on an all-sacred write. Boot three + CORE-promoted. | accurate | |
| `TrustLevel.SACRED` | `trust_ledger.py` | the source is sacred | Score ≥ 5.0. A source, not a symbol. | **overloaded** | trust-cap |
| `TokenClass.EPHEMERAL` | `symbolic_memory.py` | fleeting | Fastest decay profile. Dream-band generation and Chorus dreamer use this class. | accurate as a class | |
| `TokenClass.ENTITY` | same | a being | Protected from GRAVEYARD. The three philosophical constants are ENTITY. `identity_erosion`'s docstring claims ENTITY-adjacent; the code does not filter by class. | accurate as a class; the detector comment lies | |

---

## Report fields a reader meets

`StepState`, `CoherenceReport`, `GovernanceFeedback.outcome_metrics`, `FieldState`, status cards.

| Field | On | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `StepState.coherence` | `autonomous_cycle.py` | field coherence | Watcher **composite** | **misleading** | watcher composite |
| `StepState.rhythm` | same | what it did | Energy band. Selector puts what-ran in `extras["behavior"]`. | **overloaded** with behavior | energy-band |
| `StepState.relation_composite` | same | relationship quality | Witness relational blend of short/mid/long cosines to the anchors | accurate as a witness read | |
| `StepState.relation_pattern` | same | the kind of thought | Label from short/long cut 0.7: identity_reinforcement / transient_thought / archetypal_recurrence / novelty_intrusion | accurate as a label | |
| `StepState.dream_pressure` | same | about to dream | Unread scalar (see emotions) | **aspirational** | |
| `StepState.converged` | same | the thought settled | Reflective loop cosine ≥ 0.995, or the loop didn't run (False) | accurate when the loop ran | |
| `FieldState.energy` | `resonance_field.py` | vitality | L2 of the **raw** field. Rhythm classifier. | accurate | |
| `FieldState.rhythm` | same | cognitive mode | Band of that energy | **overloaded** | energy-band |
| `outcome_metrics.trust_impact` | `emit_feedback` | trust changed with the content | Lookup on the **decision name** only: +0.10 / +0.01 / −0.05 / −0.50 / −0.30 / −1.00 | **misleading** if heard as "the input was trustworthy" | decision-delta |
| `EmergentValue.emotional_resonance` | `value_emergence.py` | it resonates emotionally | EMA of `emotional_satisfaction` (rectified impact) | **misleading** | satisfaction-EMA |
| `CoherenceReport.stable` | `watcher.py` | stable identity | composite ≥ 0.40 | **misleading** at live C | loop-entry |

---

## Config levers (the ones whose names hide the job)

Full switch table: [`EXPERIMENTAL_LEVERS.md`](EXPERIMENTAL_LEVERS.md). Letters C–G are arbitrary.

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| lever C `dream_consolidation` | CONFIG, default **False** | dreams consolidate memory | Off: dream crystals use `long_relation=0.5` (cannot clear 0.80) and a `dream_<hex>` key. On: relation is cosine with the witness long layer; credit the sampled memories' tokens. | accurate once you read the row | |
| lever D `coherence_impact_like_for_like` | CONFIG, default **True** (2026-10-16) | a fairness flag | Tanh-vs-tanh on **both** impact probes. Off is the raw-vs-tanh artifact. | opaque letter; the flag name is honest | like-for-like impact |
| lever E `value_alignment_signal` | CONFIG, default False | values from alignment | Gate and reinforcement read `field_alignment` minus an EMA of itself, not `coherence_delta`. | accurate | |
| lever F `systemic_damp_pays_full` | CONFIG, default **True** (2026-10-16) | damp still pays | Injection and trust stay WEAKENED; value engine is paid as ALLOW, only for systemic-only damps. Alone, inert until D makes the probe ~0. | accurate | |
| lever G `satisfaction_from_emotion` | CONFIG, default False | satisfaction from feeling | `emotional_satisfaction = max(0, valence)`. Valence is nearly constant, so every value gets the same bonus. | accurate as a switch; the read is indiscriminate | |
| `six_rhythm_selector` | CONFIG, default False | six rhythms in the field | Input-read of witness/rupture **before** acting. `StepState.rhythm` stays four-band. | slightly oversold | stance selector |
| `pretrain_on_corpus` | CONFIG, default True | train the generator | Supervised rhythm pretrain of the **encoder** at boot. | **misleading** "generator" | encoder pretrain |
| `reflect_novelty_attenuation` | CONFIG, default True | less novelty when reflecting | Blend the loop's converged vector **back toward** the novel input, cap 0.30. Loosens the lock. | accurate if you hear "keep some novelty" | |
| `bond_ddm_formation` | CONFIG, default True | DDM bonds | Quality of a new bond is the accumulator, not the snapshot gate. Counts 20 / 1 stay. | accurate | |
| `fix0b_diversity_fitness` | CONFIG, default False | diversity as fitness | Reaper reinforcement gains a census term. Composed-runtime gates still required. | accurate as a lever | |
| ITG `IgnitionGate` | `tools/ignition/gate.py` | lights the mind | Scaffold. Permanently off-baseline (ruling 2026-07-03). | **aspirational** | |
| CII | `tools/ignition/cii.py` | consciousness index | `R × I × (Cm × g(Cs))` from live telemetry. Observe-only. Gauges are v0.1-fragile; trust regime labels, not magnitudes. | **aspirational** as "consciousness" | ignition reading |

---

## Alchemical and project names that appear in code

Lens, not spec: [`alchemical_correspondence.md`](alchemical_correspondence.md). These are the ones a reader hits in identifiers, comments, or CONFIG.

| Name | Where | Suggests | Computes / names | Verdict |
|---|---|---|---|---|
| Rubedo | repo, `docs/` | reddening, the last stage of the Work | This tree: RFE-Core2 slimmed to widen 128 → 256/768. The engine inside is still the Recursive Field Engine. | accurate as a project stage; not a class |
| RFE / Recursive Field Engine | everywhere | a recursive field | The system. Recursion is the loop; the field is `ResonanceField`. | accurate |
| 1188 / 11.88 | `loop/recursion1188.py`, `RECURSION` | a magic number | THE DISCIPLINE. Token `"11.88"`, sacred ENTITY. DDM RNG seed 1188. | accurate as an identity token |
| 3.12 `ANCHOR` | `governance_constants.py` | an anchor | THE BRIDGE. Sacred. | accurate as a token; not the witness anchor |
| 280.90 `HOMEOSTASIS` | same | return to rest | HOMEOSTATIC RETURN. Sacred. Boredom-with-Teeth comments point here. | accurate as a token |
| λ Love / solvent | `lambda_ledger.py` | love | The scalar that opens ⊕ composition. Off until ignited. | spec-accurate; easy to mystify |
| ⊕ solvent gate | `ValueEmergenceEngine.set_lambda_ledger` | union of opposites | `productive_tension_bonus × solvent_gain(λ)`. At λ=0, co-present values don't compose. | accurate to the spec |
| ⊘ | `integrity_read.py` | without, integrity | Thinness-read. The without-side dual of composition. | accurate to the spec; the class name WitnessReaper is the problem |
| Nigredo / Albedo / Rubedo (tiers) | `alchemical_correspondence.md` | the three stages | A reading of Tiers 0 → 1–2 → 3–4. Not enforced in code. | lens |
| Ouroboros | comments, findings | the closed circle | Survival-by-coherence lock-in. The closed circle is the **pathology**; opening it is the work. | lens |
| smith / smithing | `docs/self_model_thesis.md`, README | forging the self | The thesis: don't dissolve the self, smith it. Not a function. | lens |
| North Star | `docs/north_star.md` | the goal | Communicating, self-understanding, safely self-modifying. Three voices. | accurate as a compass doc |
| speech cortex | `tools/voice/repl_qwen.py` | a language brain | Separate boot: local LLM speaks from the **state card** and recall. The mouth never sees the 128-d vector. | **aspirational** as "cortex of the field" |
| state card / larynx | `tools/voice/state_card.py` | a throat | Deterministic first-person render of telemetry. `repl.py` uses this; `repl_qwen` uses a chat model. | accurate as a read-out |
| Resonance Family | `tests/_common.py`, workloads | a family of minds | The canonical multi-source 500-step workload (samuel/claude/gemini/grok weights). Not a kinship system. | **misleading** if heard as architecture | 
| Garage Program | STATE.md, findings | a program in a garage | Reaper/selection economy workstream (G0–G5). Dormant at harness scale (~2000 steps). | project slang |

---

## Methods whose names oversell

| Name | Where | Suggests | Computes | Verdict | Suggested |
|---|---|---|---|---|---|
| `Generator.generate` | `generator.py` | generate text | Encode + register. | **misleading** | encode |
| `Generator.encode_batch` | same | encode | Encode + register (same side effects as generate, batched). | slightly better | |
| `Generator.peek_batch` | same | peek | Read-only encode. No register, no usage, no maintenance. | accurate | |
| `Chorus.harmonize` | `chorus.py` | make harmony | Run six agents, collapse. | slightly pretty | collapse-ensemble |
| `Witness.update` | `witness.py` | notice | Write the three EMAs, gated by C². | accurate | |
| `field.resonate` | `resonance_field.py` | resonate | `tanh(field)`. | accurate as the saturate | |
| `field.inject` | same | add to the field | `field += strength · vec`, then the live field is the raw accumulator; observers often see tanh. | accurate | |
| `TrustLedger.evaluate` | `trust_ledger.py` | the trust decision | Scores + a recommendation string. Decision is `arbitrate`. | **misleading** ("evaluate" as if it decides) | score-source |
| `DependencyMonitor.get_report` | `dependency_monitor.py` | the dependency decision | HHI snapshot + recommendation. `arbitrate` ignores the string. | the report is real; the recommendation is advisory in name only | |
| `Dreamer.dream` | `dreamer.py` | sleep | Live in-step recombination + inject. | **overloaded** | in-step-dream |
| `ValueEmergenceEngine.on_dream_cycle_complete` | `value_emergence.py` | the offline cycle finished | Called from **in-step** `_dream_behavior` (new crystals only). The method name is the offline cycle; the live caller is not. TrustLedger's copy has no caller. | **misleading** | dream-boost hook |
| `identity_stability` | `witness.py` | the self is stable | Inverse of anchor acceleration. | **overloaded** with emotion.stability | anchor-stability |
| `ManipulationResistanceEngine.detect` | `manipulation_resistance.py` | catch an attack | Five window tests, including ordinary G/T split. | accurate as "run detectors"; not all fires are attacks | |

---

## If you only remember five

1. The **Generator** encodes. The **Decoder** is a bag. Speech is a different boot.
2. **Witness** is an anchor, a stance, and a thinness-read. Say which.
3. **Coherence** is a pin (~0.998), a composite (~0.92), and a probe (~0 with D). Say which.
4. **Dream** is a band, a live inject, a self-talk channel, an offline cycle, and a file session. Say which.
5. **Satisfaction** and value-path **surprise** are halves of the impact probe. **Joy** is the composite. **Erosion** is a G/T split on ordinary dreaming.

When a name and a function disagree, believe the function. What has actually moved is [Renames](#renames). Leave the rest.

---

## Renames

A rename must not change behaviour. The proof, before and after, is `python -m tests.diagnostic.rename_digest` (400 steps, seed 42). The combined digest has to match the one recorded on the branch before that batch touched a name. `docs/findings/` is a dated ledger and keeps the old names. A row in the tables above is not permission to rename. Only **done** here has moved.

| Old | New | Date | Commit | Status |
|---|---|---|---|---|
| `coherence_flood` | `source_monopoly` | 2026-10-16 | `c1b92c7` | **done.** The detector (HHI ≥ 0.70 and attractor monopoly ≥ 0.70): the string, the method, and the docs that name the live detector. `canonical_detector()` still accepts `coherence_flood` on read. |
| `ThinnessVector.coherence_contribution` | `alignment_support` | 2026-10-16 | `7bf2428` | **done.** The ⊘ axis, absolute field-alignment. `as_dict` writes the new key. The constructor keyword and `from_dict` still accept the old key. Not `EmergentValue.coherence_contribution`. |
| `Dreamer` docstring "offline" | runs live inside the step | 2026-10-16 | `454e4ef` | **done.** Text only. The class is called from the cycle step. |
| Batch 2, the aspirational names: `dream_pressure`, `crystal_pressure`, `entropy_drift`, `ReflectiveLoop.attractor_blend`, `CoherenceReport.stable` | names kept; their docstrings now say nothing reads the first four, and that `stable` is the reflective-loop entry floor (composite ≥ 0.40), not a stability verdict. CLAUDE.md no longer says the emotions scale `crystal_pressure` / `dream_pressure` every step | 2026-10-18 | `3dd691a` | **done.** Text only; each "unread" claim checked against every call site first. Digest bit-identical (combined `48f877d8…` at OMP/MKL = 1). `agents/rhythm_config.json` still lists `dream_pressure` under `wonder_drives` / `boredom_drives`; no code reads those lists. |

Held, on purpose:

| Name | Why it stays |
|---|---|
| `Generator` | Samuel decides last. It is everywhere. |
| `emotional_satisfaction` | Not this batch. |
| `surprise` (value path) | Not this batch. The echo's surprise is a different number. |
| `identity_erosion` | Open question (does ordinary dreaming count), not a rename yet. |
| `EmergentValue.coherence_contribution` | Waiting on what values should read. The ⊘ axis that shared this string has already moved. |
| witness | An anchor, a stance, and the thinness-read. No rename until that split is decided. |
| coherence | A pin, a composite, and a probe. No rename until that split is decided. |
| dream, past the Dreamer docstring | The band, the waking channel, `DreamCycle`, and `DreamSession` stay. Only the in-step class's "offline" wording moved. |

Current digest baseline (2026-10-19, after witness activation, OMP/MKL = 1): combined `ae907b9a…`
(`findings/2026-10-19-witness-activated.md`). A rename batch records its own before/after on the same machine.

When a name and a function disagree, believe the function, and leave the name until this table says **done**.
