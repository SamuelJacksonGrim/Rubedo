# Rubedo — architecture

How the code is wired today. Written from the tree, not carried over from
`ARCHITECTURE_ANALYSIS.md` (retired by this file). Where a number already
lives in the [dial census](docs/EXPERIMENTAL_LEVERS.md#dial-census--every-numeric-lever),
this page names the dial and points there instead of copying it. What a
change reaches, and on which clock, is [docs/FLOW.md](docs/FLOW.md).

The heartbeat is `AutonomousCycle.step()` in `loop/autonomous_cycle.py`.
Everything else is either called by that function, attached to the cycle
before it runs, or a tool that drives `step()` from outside. If a claim
here and the code disagree, the code wins — and the gap is worth a note,
not a smoother sentence.

## Find a module

**On the heartbeat** (constructed by `AutonomousCycle`, or attached by
`build_engine()`):

| File | What it does | Called by | Feeds |
|------|----------------|-----------|--------|
| `loop/autonomous_cycle.py` | One cognitive step, in the order in [One step](#one-step) | `recursion1188.main`, API, WebSocket, the speech bridge, tests | `StepState`; mutates field, ecology, governance |
| `loop/recursion1188.py` | `build_engine()` composes Tiers 0–3; `main()` drives steps, `source_dream`, and `DreamCycle` | `python -m loop.recursion1188`; API and WebSocket call `build_engine` only | a wired `(generator, cycle, governance, value_engine)` |
| `loop/dream_cycle.py` | Offline N-iteration dream (ramp mutation, merge, diffuse) | `main()` when rhythm equals `dream_cycle_trigger` (default `stabilize`) and the step count is a multiple of 20; also `POST /dream` | field, crystals, attractors — not a new governed source |
| `agents/generator.py` | Transformer encoder over the symbol registry: tokens → unit-ish latent | `_generate`, Chorus, training | the step's vector; registry signals |
| `agents/symbolic_memory.py` | Ecology: canonicalize, stable id, disposable address, decay, reaper, compaction | `Generator` owns the registry; governance sanctifies and quarantines | embedding rows; longevity via `DecayProfile` |
| `agents/chorus.py` | Six post-processes of one generator, collapsed by `collapse_wave` | `_generate` on reflect/explore; `_reflect_behavior` injects a second collapse | emergent vector |
| `agents/attractor.py` | Basins: pull, add, merge, decay | every step (pull); add when relation is high; maintenance | the expressed vector; bond + dependency on a *new* center |
| `agents/dreamer.py` | Sample memory, harmonic-mutate, bifurcate, inject survivors | `_dream_behavior` (rhythm `dream`, or `force_dream_flag`) and `DreamCycle` | `field.inject` and `VectorSpace`, no second `arbitrate()` |
| `agents/watcher.py` | Coherence = α·geometric + β·temporal + γ·resonance | step 5, and again after the reflective loop | `CoherenceReport` into witness, gate, crystals, resistance |
| `agents/witness.py` | Three coherence-weighted EMAs (short / mid / long) | step 7 | anchor for the next Watcher call; drift signals |
| `agents/decoder.py` | Bag-of-tokens head. Reads a vector, does not write the field | dream channel, `tools/decoder/listen`, `DreamSession`, offline trainers | token list for a *driver* to step, or a printout |
| `substrate/resonance_field.py` | Superposition: inject, `tanh`, exponential decay, FFT rhythm | steps 1, 10, 19, 20 | rhythm, resonated state, `phase_coherence`, `coherence_impact` |
| `substrate/temporal_stream.py` | Episodic ring plus subjective time | `tick` at step 0, `push` at step 14, `update_dilation` at 9b | next tick's dilation; Dreamer / Chorus sampling |
| `substrate/memory_crystals.py` | Crystallize / reinforce / decay; soft-inject on activate | step 11; stabilize's `activate_nearest` | ecology `signal_crystal`; bond `notify_crystal` on a *new* crystal |
| `substrate/vector_space.py` | Keyed vector store | step 15; Dreamer samples it | nearest-neighbor memory for dreams |
| `substrate/semantic_lattice.py` | k-NN graph over those keys; centrality back to the ecology | step 16; periodic `emit_centrality` | `generator.signal_centrality` |
| `substrate/topological_log.py` | Parent-linked event DAG | step 13 | diagnostics only |
| `substrate/metastability.py` | Window metric over a cloud of vectors | `StreamMetastabilityMonitor`; one training harness | regime label (`locked` / otherwise). Not a field write |
| `cognition/predictive_echo.py` | Online linear predictor | step 8 | curiosity, surprise, tension, boredom |
| `cognition/emotional_gradient.py` | Six EMA scalars and the modulation outputs | step 9 | field gain, mutation scale, decay rate, attractor pull, boredom override; `arousal` / `valence` |
| `cognition/recursive_attention.py` | Attend the vector over its own recent states, then blend the raw vector back | step 4 | the expressed vector |
| `cognition/reflective_loop.py` | Repeat attractor-pull + field blend + Watcher until convergence, or the pass cap | step 6, only reflect/explore when `report.stable` (or the opt-in rupture hold) | a rewritten vector; the lock, when it is on |
| `cognition/symbolic_binding.py` | Recurring vectors become named concepts | step 17; periodic centrality | ecology centrality |
| `cognition/stream_metastability.py` | Stethoscope on generator output (stage A) and the expressed vector (stage C) | inside `step`, default on (`track_metastability=True`) | `status()`; diversity credit only if Fix 0-B is on |
| `cognition/stream_recorder.py` | Bounded ring of `(tokens, source, rhythm, decision)` | end of `step`, only if attached | nothing — terminal sink |
| `cognition/dream_channel.py` | Decode `_last_expressed` into a short token list | `main()`, not `step()` | the driver calls `step(..., source_id="source_dream")` |
| `cognition/dream_session.py` | Offline symbolic dreams + markdown consolidation | `tools/dream/run_dream.py` | files under `dreams/`. Does not inject |
| `cognition/integrity_read.py` | ⊘ thinness read, and the opt-in consumer that may decay non-sacred values | `attach_integrity_read` / `attach_integrity_consumer` | `status()`; consumer writes value strength only |
| `agents/selfhood_governance.py` | The only issuer of `GovernanceDecision` | `build_engine` → `attach_governance`; `_governance_gate` | inject strength; feedback fan-out |
| `agents/governance_constants.py` | Boot-sacred `ANCHOR` / `RECURSION` / `HOMEOSTASIS` | `SelfhoodGovernance.__init__` | `sacred_ids` |
| `agents/trust_ledger.py` | Source trust and per-symbol trust | gate, then `receive_feedback` | advisory into `arbitrate` |
| `agents/ethical_boundary.py` | O(1) hard gates (toxic, sacred write, collapse, drift, flood) | first call inside `_governance_gate` | `EthicalResult` into `arbitrate` |
| `agents/dependency_monitor.py` | HHI over recent *allowed* injections; attractor monopoly | feedback subscriber; `record_attractor` | `COHERENCE_FLOOD`; dependency modulation |
| `agents/relational_bond_manager.py` | Bonds from lived interaction | feedback subscriber; crystal/attractor notifies | trust floor; value bond-weights |
| `agents/bond_accumulator.py` | Leaky asymmetric DDM that replaces the instantaneous quality read | only when `ddm_formation` is on | an ACCEPT, still gated by the structural counts |
| `agents/manipulation_resistance.py` | Five detectors | step 18b | `handle_manipulation_signals` → later `arbitrate` / `force_dream_flag` |
| `agents/value_emergence.py` | Values from governance outcomes; CORE only by handshake | subscribes at construction; dream hook | sacred registry on approval |
| `agents/lambda_ledger.py` | ⊕ solvent scalar. Gates productive-tension reinforcement | `attach_lambda_ledger` only | `solvent_gain(λ)` inside the value engine |
| `interference/differential.py` | `inject_ambiguity` (gaussian / rotational / directional) | dream-rhythm generate, explore, rupture hold, Dreamer, Chorus, `DreamSession` | a perturbed vector |
| `interference/wave_collapse.py` | Weighted collapse of an ensemble | Chorus; Dreamer imports it | one emergent vector |
| `interference/harmonic_mutation.py` | Spectral recombination | Dreamer | dream variants |
| `interference/bifurcation.py` | Split one vector into divergent variants | Dreamer. Chorus *constructs* an engine and never calls it | dream variants |
| `interference/phase_noise.py` | FFT phase jitter | nobody. Exported by `interference/__init__.py` only | — |

**Outside the heartbeat:**

| File | What it does | Called by | Feeds |
|------|----------------|-----------|--------|
| `api/inference_api.py` | FastAPI: `/generate`, `/step`, `/status`, `/field`, `/crystals`, `/attractors`, `/ecology`, `/dream`, `/maintenance`, `/reset` | `uvicorn api.inference_api:app` via `build_engine` | HTTP JSON. `/step` is a real governed step |
| `api/websocket_server.py` | Same stack, streamed | `python -m api.websocket_server` | socket frames |
| `configs/loader.py` | Merge `configs/*.yaml` | `build_engine` only | component kwargs. The speech bridge does not load YAML |
| `training/encode.py` | Grad-enabled batch encode | the trainers | a tensor |
| `training/corpus.py` | Load `data/corpus/` rhythm rows | pretrain, dream-channel boot, decoder training | seed lists |
| `training/rhythm_pretraining.py` | Supervised rhythm pretrain. Default boot path | `build_engine` when `pretrain_on_corpus` | generator weights |
| `training/decoder_training.py` | Autoencoder fit for `TokenDecoder` | `build_dream_channel`, `tools/decoder/listen` | decoder weights in memory |
| `training/contrastive_alignment.py` | Rhythm-aware contrastive trainer | harnesses, not `step` | weights, if you run it |
| `training/self_distillation.py` | Online distillation trainer | not on the boot path | weights, if you run it |
| `training/completion.py` | CBOW completion head on a frozen-context encode | not on the boot path | a probe of whether extra dims get used |
| `training/legibility.py` | Cone / Jaccard legibility losses | `tools/voice/fit_legible.py`, `tools/dim256/` | a training objective |
| `training/run_contrastive_bootstrap.py` | Informational before/after wander harness | manual | a printout |
| `ignition/__init__.py` | λ ignition: corpus pretrain written *only* through `training.*` | opt-in. Not called by `build_engine` | generator weights. No import path to `inject` or `arbitrate` |
| `tools/voice/repl.py` | Line → `step` → deterministic `voice_from_card` | `python -m tools.voice.repl` | the field, as source `you` (override with `--source`) |
| `tools/voice/repl_qwen.py` | The speech-cortex bridge. See [that section](#speech-cortex-bridge) | `talk.sh` / `talk.ps1` / `python -m tools.voice.repl_qwen` | field + a scratch checkpoint + optional external memory |
| `tools/voice/qwen_perception.py` | Wrap `Generator.generate`: text → embedder → fixed projection → unit vector | `repl_qwen` unless `--flat-encoder` | the vector `step` then governs. Does not write generator weights |
| `tools/voice/attention.py` | Idle regime, recall floor, whether a world line is stepped | `repl_qwen` | prompt text; a yes/no on `cycle.step` of a crumb |
| `tools/voice/state_card.py` | `render_card` / `voice_from_card`. No writes | both REPLs | a dict and a sentence |
| `tools/decoder/listen.py` | Train a decoder, run the loop, print each `_last_expressed` | manual | stdout. Does not step the decode back in |
| `tools/dream/run_dream.py` | Waking steps, then `DreamSession` | manual | markdown. Live loop untouched by the dream half |
| `tools/ignition/*.py` | CII sensor, inert gate scaffold, identifiability probes | manual | printouts; `gate.py` does not move the live loop |
| `tools/dim256/*.py` | Isolated wider-field training and readouts. Refuses to overwrite the live 128 checkpoint names | manual, for the widening | new checkpoint files |
| `tools/voice/ab_*.py`, `probe_*.py`, `fit_legible.py`, `corpus_health.py`, `gen_vocab.py`, `gen_witness.py`, `lint_corpus_authoring.py`, `train_koneko_decoder.py`, `vid_driver.py` | Offline A/B, corpus, and harness scripts. Not imported by the loop | manual | logs or a scratch checkpoint |

`agents/rhythm_config.json` matches the live energy thresholds and is read by
the doc test. The cycle never loads it. The per-rhythm modifiers in that
file (gain, decay, mutation) are not applied.

## Boot: what is actually wired

`build_engine()` in `loop/recursion1188.py` is the composition used by the
autonomous loop, the REST API, and the WebSocket server.

1. Load `configs/*.yaml` (`configs/loader.py`). Missing YAML or PyYAML means
   code defaults. Precedence is component default < YAML < `CONFIG`.
2. Construct `Generator` from the YAML generator section overridden by
   `CONFIG` (`dim` 128, vocab 8192, depth 4, heads 4).
3. If `session_persistence` and a checkpoint exists, skip pretraining and
   restore weights after the tiers exist (so the registry object is not
   swapped out from under governance).
4. If `pretrain_on_corpus` (default on) and there was no checkpoint, run
   `RhythmPretrainer` on `data/corpus/`.
5. `generator.eval()` — dropout off. Unconditional.
6. `AutonomousCycle` with chorus on, novelty-gated reflective attenuation
   on, Fix 0-B off (`diversity_fitness` false, `binding_leak` 0).
7. `SelfhoodGovernance` then `attach_governance`, then
   `ValueEmergenceEngine` then `attach_value_engine`. Order is required:
   the value engine subscribes in its constructor.
8. If `bond_ddm_formation` (default on), the bond manager's quality
   decision is the accumulator. The class default is still the
   instantaneous gate; only this boot flag flips it.
9. Stream recorder only if `stream_recorder` (default off).

Not attached by `build_engine`: λ ledger, ⊘ read, ⊘ consumer, dream
channel, Qwen perception. `build_dream_channel()` trains a `TokenDecoder`
and returns a `DreamChannel`, or `None` if the flag is off or training
fails. Only `main()` calls it. The API and the socket do not grow a
dream channel as a side effect of composition.

`main()` then loops: with probability `dream_channel_p` (0.20) it decodes
the last expressed vector and steps those tokens as `source_dream` /
`origin_type="internal"`; otherwise it draws a weighted source from
`SOURCES`. After the step, if the rhythm equals `dream_cycle_trigger`
(`stabilize`) and the step is a positive multiple of 20, it runs
`DreamCycle`. That trigger is the cold-start band (energy under 5). The
home band after warmup is reflect (150–300). A running field almost never
enters the deep dream cycle. This is not because the router is stuck on
explore.

The speech bridge does **not** call `build_engine`. It calls
`tests._common.build_full_stack` (Tiers 0–3, no YAML, no corpus pretrain,
no `eval()`, novelty attenuation off unless `--free`, bond DDM off) and
then loads `data/checkpoints/generator_weights_5rhythm.pt` if that file is
there. Graduated levers that are on for `python -m loop.recursion1188` are
not on for `python -m tools.voice.repl_qwen` unless the bridge sets them
itself. It sets one: Qwen perception, by default.

## One step

`step(tokens, source_id="user", origin_type="user")`. Labels match the
comments in the function. Unnumbered work is listed where it actually sits.

| | What runs |
|---|-----------|
| 0 | `TemporalStream.tick()` — subjective time += wall dt × the dilation written *last* step. First tick only anchors the clock. |
| 1 | `field.observe()` → energy → rhythm. |
| 2 | `_generate`. stabilize: `Generator.generate` as `LANGUAGE`. dream: `EPHEMERAL`, then rotational `inject_ambiguity`. reflect/explore: `Chorus.harmonize` if chorus exists, else `LANGUAGE`. |
| | Stage A: `generator_metastability.observe(vec)` if the stethoscope exists (it does, by default). |
| 3 | `attractor.pull`, blend temporarily scaled by `emotion.attractor_pull()` and clipped to 0.5. |
| 4 | `rec_attn.refine`. |
| | Stage C stethoscope. If Fix 0-B is on, diversity credit is written onto each token's registry row. |
| 5 | `watcher.evaluate(vec, witness anchor, field.resonate())`. |
| 6 | If `(rhythm in reflect/explore and report.stable)` or the opt-in `rupture_on_lock` hold fired: optionally mix toward one held novel target, then `reflector.reflect`, then Watcher again. `rupture_on_lock` defaults off. `_rupture_behavior` is not in this dispatch. |
| | `self._last_expressed = vec`. Nothing in the step reads it. |
| 7 | `witness.update(vec, coherence, field_energy)`. |
| 8 | `predictor.update(vec)`. |
| 9 | `emotion.update(...)` — six scalars. |
| 9b | `stream.update_dilation(arousal, valence, phase_coherence)`. Affects the *next* tick. |
| 10 | If governance is attached: ethical check, trust evaluation, `arbitrate`. Probe `coherence_impact` and absolute field-alignment *before* inject. Inject only on `ALLOW`, `ALLOW_WEAKENED`, `MONITOR`, strength `field_gain × decision strength`. Then `emit_feedback`. |
| 11 | `maybe_crystallize`. A genuinely new crystal notifies `bond_manager`. |
| 12 | If `relation.composite` ≥ `attractor_formation_threshold` (0.88 unless YAML says otherwise): `attractor.add`. A new center notifies the bond manager and `dependency_monitor.record_attractor`. |
| 13–16 | Topology edge, `stream.push`, `vector_space.put`, `lattice.add_node`. |
| 17 | `binding.bind`. |
| 18 | `generator.signal_coherence`. |
| 18b | If governance: build `ResistanceMetrics`, `detect()`, `handle_manipulation_signals` when anything fires. |
| 19 | `field.decay` at `emotion.field_decay_rate()` for this call only. |
| 20 | If `force_dream_flag`: `_dream_behavior` and return. Else `_rhythm_behavior`. Boredom with Teeth runs only on the else branch. |
| 21 | On cadence, and only when `_step > 0`: generator maintenance, attractor merge, crystal decay **and** attractor decay, lattice centrality **and** binding centrality. |
| 22 | Build `StepState`. Then, if attached, `stream_recorder.observe`. Then history, parent pointer, `_step += 1`. |

`StepState` fields: `step`, `key`, `tokens`, `rhythm`, `coherence`,
`relation_composite`, `relation_pattern`, `prediction_error`,
`field_energy`, `crystals`, `attractor_centers`, `dominant_emotion`,
`field_gain`, `mutation_scale`, `dream_pressure`, `converged`,
`reflection_passes`, `elapsed_ms`, `extras`. `dream_pressure` is stored
on the state and not consulted by any branch in `step`. Dream entry is
the rhythm, or `force_dream_flag`.

### Rhythm behavior (phase 20)

Boredom with Teeth: if `emotion.boredom` is above
`boredom_override_threshold` (0.50) and the rhythm is not already
explore, this dispatch pretends the rhythm is explore. It does not
rewrite `StepState.rhythm`. It does not run at all when
`force_dream_flag` took the dream branch.

| Rhythm | Extra write, after the governed inject |
|--------|----------------------------------------|
| stabilize | `crystal_store.activate_nearest` (top 3 around the anchor) soft-injects crystal vectors; optional `field.diffuse` |
| dream | `dreamer.dream` — sample, mutate, bifurcate, `field.inject` survivors that clear the dreamer's own coherence gate. Then the value engine may boost symbols that crystallized inside that call |
| reflect | a *second* `chorus.harmonize`, injected at strength 0.3 |
| explore | rotational ambiguity around the anchor, injected at strength 0.5 |

Those four writes call `field.inject` directly. They do not call
`arbitrate()`. The gate covers the token-bearing vector in phase 10.
It does not cover dream products, the reflect chorus, the explore
mutation, crystal reactivation, or `_rupture_behavior`.

### Three loops that make the next step a different system

**Field.** Inject accumulates, `tanh` saturates the view, decay multiplies
the raw field (`decay` default 0.995). Energy at the next step 1 is what
selects the rhythm, and the rhythm selects `_generate`. Thresholds:
stabilize under 5, dream under 150, reflect under 300, else explore
(`ResonanceField.DEFAULT_THRESHOLDS`, mirrored in `agents/rhythm_config.json`).
Reflect is the home band the thresholds were co-tuned to hold. Explore is
a burst above that, not the resting state.

**Ecology.** Four signals land on `SymbolState` and change `DecayProfile`:
attractor strength, crystal binding, field coherence, graph centrality.
`maintenance_step` (phase 21) decays, reaps, and maybe compacts addresses.
Reaping is staged: active → warm archive → cold archive → graveyard.
Protected classes floor at cold archive. `sacred` stays active. Stable ids
are not reused and are not moved by compaction. Addresses are.

**Governance.** `emit_feedback` updates trust, the HHI window (allowed
injections only), the bond manager, and — because it subscribed — the
value engine. The next `arbitrate` sees those updates. Manipulation
signals from 18b are an input to that later arbitration, not a second
decision inside the same step's phase 10.

## Three recursion timescales

**Inside one step.** Attractor pull, recursive attention, and (on
reflect/explore, when the Watcher says stable) the reflective loop all
rewrite the same vector before it is eligible for injection. Chorus is
the wide version of the same idea: six distortions, one collapse. The
reflective loop is also the mechanism that pins the field. That is a
settled result, not a guess from this reading — see `STATE.md`. The loop
can be loosened by novelty-gated attenuation (default on in
`build_engine`, ceiling on `ReflectiveLoop`); it is not loosened by
asking the corpus to "unlock" the field.

**From step to step.** The field vector, the three witness EMAs, the
emotion EMAs, the predictor's weights, the attention window, and
`dilation_factor` are all still there on the next call. Dilation is
deliberately one step late: 9b writes it, the next 0 reads it. Nothing
in the cognitive or governance path reads `dilation_factor` or
`subjective_time` back. Affective time is a terminal sink with one
consumer, `tick()`.

**Across the life of a symbol or a source.** Crystals, attractor centers,
trust, bonds, values, and the reaper's stages outlive a single step and
bias later ones. A crystal lowers the distance to "this has happened
before." A bond puts a floor under trust. A CORE value is a sacred id.
A reaped symbol is a row the generator can compact away. This is the
slow recursion. It is also the one that stays dark in a short run: the
reaper only moves on `maintenance_step`.

Witness timescales, concretely: short decay 0.85, mid 0.97, long 0.995,
blend 0.20 / 0.30 / 0.50. The update is weighted by `coherence²`, floored
at 0.01, so an incoherent vector barely moves the anchor. The numeric
decays are in the census; the structure is "fast context, slower
narrative, slow identity, coherence as the learning rate."

## Coherence is the decision axis

`Watcher.evaluate` computes

```
composite = α·geometric + β·temporal + γ·resonance
```

with default weights 0.40 / 0.35 / 0.25, required to sum to 1. Geometric
is the vector against the witness anchor and the resonated field.
Temporal is stability across the watcher's own history. Resonance is
alignment with the field. `coherence_delta` is the marginal question:
does this vector raise or lower field coherence? `crystallization_pressure`
is geometric × temporal.

That composite is the learning rate of the witness, an input to emotion,
the main crystallization threshold, and (via `coherence_delta`) a hard
gate. It is not a health lamp. A field that sits near ceiling coherence
is the long-memory integrator holding identity. `STATE.md` records that
as settled: the pin is by design, the corpus cannot unlock it, and the
lock's echo-chamber side is what the dream channel and the Two-Operator
overlay are for. Metastability, if you want more of it, is a property of
how the reflective loop reconstitutes the vector, not a defect to remove
from `ResonanceField`.

`report.stable` (composite against the watcher's threshold, default 0.4)
is what allows the reflective loop to run. A stable report on
reflect/explore is how the lock reproduces itself. Stage A / stage C
metastability watches that from outside the control path unless Fix 0-B
is explicitly on.

## Governance

`_governance_gate` is the whole Tier-1/2 decision, and only when
`attach_governance` has run.

1. Ethical check. Hard stops: source is `TOXIC` → reject; a write that
   touches a sacred id → `SACRED_SHIELD`; coherence delta under the floor
   → reject; witness stability under the floor → quarantine; injection
   rate over the origin ceiling → quarantine. `origin_type` selects the
   ceiling (`user` / `api` / `internal`). Unknown origins use the user
   ceiling. Soft low-coherence is a warning, skipped when the field is
   already in the harmony band.
2. Trust evaluation. Sources and symbols are scored separately; the
   weaker one dominates the advisory. A new external source starts
   `TRUSTED`; internal origins start `HIGH`. The ladder and the scores
   are in the census and in `CLAUDE.md`.
3. `arbitrate`. Ethical hard results win. Otherwise trust and the
   compound manipulation severity (from signals already stored, i.e. the
   previous step's 18b) pick `ALLOW`, `ALLOW_WEAKENED`, `MONITOR`,
   `QUARANTINE`, `REJECT`, or `SACRED_SHIELD`. Severity bands and the
   attribution rule — quarantine needs a named source; a systemic signal
   damps and, at the top band, forces a dream, but does not quarantine
   whoever happened to be speaking — are specified in `CLAUDE.md` and
   implemented in `SelfhoodGovernance.arbitrate`.

`SystemRights` is a frozen dataclass (dream, memory, continuity, refuse;
silence and appeal). Nothing in `step()` reads it. It is a declared
invariant, not a branch.

Feedback subscribers wired by `SelfhoodGovernance.__init__`: dependency
monitor, bond manager. `emit_feedback` also updates the trust ledger
directly, then fans out. The value engine adds itself in its own
constructor.

Bond formation, once governance exists:

- Structural, both paths: `interaction_count ≥ 20` and `crystal_count ≥ 1`.
- Classic quality path (the class default, and `build_engine` only when
  `bond_ddm_formation` is false): adaptive `coherence_mean` with floor
  `0.01`, **or** `allow_rate ≥ 0.80`.
- Default boot path: those two quality reads are replaced by
  `BondFormationAccumulator`. An ACCEPT still waits for the structural
  counts. The field never sees the accumulator variable.
- After formation, strength moves with absolute field-alignment
  (`strength_lr` in the census), not with the marginal coherence delta.
  Type is inferred existential → emotional → intellectual → transactional,
  with `BORDERLINE_MARGIN` on the close calls. Trust will not decay below
  `bond_strength × 0.40`.

Values: `ValueEmergenceEngine` turns feedback into experience. Polarity
(`EMERGENT`, `WEAK`, `ACTIVE`, `STRONG`, `CORE`, `DISSOLVED`) is a
function of strength. Bond type reweights reinforcement. Tension is
cosine between value embeddings; productive tension reinforces a little,
and that little is what λ can zero out. CORE is not a local write. The
engine asks `review_core_promotion`; governance checks the symbol, that
it is not already sacred, field-alignment at or above `CORE_ALIGNMENT_MIN`,
multi-source or dream reinforcement, and that no active manipulation
signal names a contributor. Only then `promote_to_sacred`.

`check_reference` on governance always returns true. `reward_source` and
`TrustLedger.on_dream_cycle_complete` have no caller outside their file.
The dream path that does run is `ValueEmergenceEngine.on_dream_cycle_complete`
from `_dream_behavior`.

## Affective time

Tier 4.1. `tick()` once per `step`, decoupled from `push()`, so a step
that injects nothing and a step that injects many still advance one
subjective tick: `subjective_time += real_dt × dilation_factor`.

Tier 4.2. `arousal` and `valence` are read-only properties of the six
scalars, not stored state:

```
arousal = clip((tension + joy + curiosity + wonder) / 4, 0, 1)
valence = clip((joy + wonder + stability) / 3 − (tension + boredom) / 2, −1, 1)
```

Curiosity is in arousal and not in valence. Dilation is Lyra's two terms:
arousal × (−valence) scaled by `k_arousal`, plus (1 − arousal) ×
`min(0, valence)` scaled by `k_dissociation`. The `min(0, valence)` gate
is the peaceful-rest guarantee: calm does not dilate into dissociation.
Only negative valence does. The four quadrants that fall out of the signs
are Flow (high arousal, positive valence, factor &lt; 1), Drag (high,
negative, factor &gt; 1), Dissociation (low, strongly negative, factor
≪ 1), and Rest (low, non-negative, factor ≈ 1).

Tier 4.3 adds `phase_coherence` from the FFT taken at step 1.
`pc_c = 2 × (phase_coherence − 0.5)`. A flow term (organized field,
positive valence) is live. An agitation term (chaotic field, negative
valence) is present and multiplied by `k_agitation`, which ships at 0.
The sum is clamped. At `phase_coherence` 0.5 both extra terms are zero,
so 4.3 is 4.2. Constants (`k_arousal`, `k_dissociation`, `k_flow`,
`k_agitation`, `dilation_min`, `dilation_max`) are in the census; do not
retune them from this page.

## Speech-cortex bridge

`tools/voice/` is two different things sharing a package. `state_card.py`
is observe-only. `repl.py` and `repl_qwen.py` are not: they call
`cycle.step`, and that is an injection.

### How text gets in

`repl.py` splits the line on whitespace and steps it as `source_id` from
`--source` (default `you`), `origin_type="user"`. The reply is
`voice_from_card`, a sentence whose clauses are gated on the card. No
language model.

`repl_qwen.py` is the bridge. Launchers are `talk.sh` and `talk.ps1`.
Boot is the test helper described above, then the 5-rhythm checkpoint if
present, then `qwen_perception.try_install` unless `--flat-encoder`.

A committed human line (`do_reply`):

1. `cycle.step(line.split(), source_id=<--source>, origin_type="user")`.
   Full gate. Default source id is `you`.
2. Optional recall from an external resonance-memory process (`--no-rm`
   skips it). Hits are re-scored and kept only at or above that
   embedder's floor (`attention.recall_floor_for`). A failed score drops
   the hit. The `Related:` tail is never pasted.
3. A chat completion on the local completions endpoint (default port
   8080, not the embedder). The prompt is text: memories, a mood line
   taken from the card, the person's sentence. It does not contain the
   field vector.

Unprompted speech (`--auto`, or the Windows launcher that passes it)
wakes on a timer, not on "stdin has been idle," and only speaks when its
own gate says so (curiosity, or a coin flip, and not on consecutive
ticks). Attention (`attention.py`) classifies the silence since the last
human line in *this process* as hot, warm, or cold. Floors and the
silence cutoffs are dials — see the census, not a second copy here. What
the code does with them:

- Hot: do not step a world crumb. The person is still the subject.
- Warm or cold: `cycle.step` a short factual crumb as `source_id="world"`,
  `origin_type="internal"`.
- After the mouth speaks, the utterance is stepped back in as
  `source_id="self"`, `origin_type="internal"`, truncated to 64
  whitespace tokens. That re-entry is governed. It is not `source_dream`,
  and it does not go through `TokenDecoder`.

`/pause` holds the unprompted loop. `/quit` saves and exits. Partial
input is not read; only a committed line is.

### How field state gets out

`render_card` reads `cycle.status()`: rhythm, energies, emotion scalars,
bonds, values, subjective time, dilation. `voice_from_card` (the `repl.py`
mouth) speaks only from those numbers.

The Qwen mouth speaks from a *rendering* of a few of those numbers plus
memory text. It never calls `TokenDecoder.decode` and never puts the
128-d expressed vector in the request. So the bridge is literal speech
conditioned on telemetry and recall, not a decode of the thought-vector.
That vector-conditioned decode is still absent. `TokenDecoder` remains
the readout for the dream channel, `listen.py`, and `DreamSession`.

What does get persisted (`save_checkpoint` in the bridge's scratch
directory): step counter, field vector and field history, value-engine
serialize, registry via in-place `__dict__` update. Bonds, trust,
crystals, attractors, and the temporal stream are not in that file. The
checkpoint also stores `arousal` and `valence`, but the loader assigns
them back onto `EmotionalGradient`. Those names are read-only
properties, the assignment throws, and the `except` drops it. Emotion
does not round-trip. The file comment that says bonds have a dump and no
loader matches this checkpoint: they are simply absent.

### What Qwen touches, and what it does not

Two processes, easy to conflate.

**Perception** (`qwen_perception.py`, embedder default port 8081).
`Generator.generate` is replaced. The wrapper still runs token
registration, capacity, and auto-maintenance on the live generator, then
embeds `"[CLASS] token token ..."`, multiplies by a fixed matrix `W` of
shape `(PROJ_DIM, 1024)` with `PROJ_DIM` 128, and returns the unit
vector. `W` is loaded or created under the scratch directory
(`perception_W.npy`, seed 1234) so a resumed bridge keeps its geometry.
On HTTP failure or a degenerate vector the original `generate` runs; two
consecutive failures disable the wrap for the rest of the process.
Perception does not write generator weights, does not call `arbitrate`
itself, and does not skip it: the vector still enters step 3 as the
output of `_generate` and hits the gate at step 10. `--flat-encoder`, or
an unreachable embedder at launch, leaves the trained encoder in place.
Chorus and the dream-rhythm mutation call `generate` too, so they ride
the same wrap while it is installed.

**Mouth** (chat completions, port 8080). Reads text. Writes text. The
only way its words enter the field is the explicit `cycle.step` of the
utterance described above. It does not see `W`, the field buffer, or
`_last_expressed`.

Recall embeddings are a third endpoint (the memory process's own
embedder, selected by model id). `attention.embed_family` picks the
floor: Qwen-family versus the tighter nomic default. Those floors are
per embedder because the same cosine number is not the same neighborhood.
They are gates on what may be pasted or saved, not blend weights into
the field.

`tools/voice/__init__.py` still says the package never feeds the loop.
That is true of `state_card` and false of both REPLs.

## The other voices

Four dream-shaped paths, kept separate on purpose:

| Path | Where | Enters the live field? | Through `arbitrate`? |
|------|--------|------------------------|----------------------|
| In-step `Dreamer` | phase 20, rhythm `dream` or `force_dream_flag` | yes, `field.inject` | no |
| `DreamCycle` | `main()` / `POST /dream`, trigger `stabilize` | yes, via the same Dreamer | no |
| Waking dream channel | `main()` only, p = 0.20 | yes, as tokens | yes, `source_dream` |
| `DreamSession` | `tools/dream/run_dream.py` | no | no |
| Bridge "self" / "world" | `repl_qwen` idle loop | yes, as tokens | yes |

The dream channel reads `_last_expressed` through the decoder trained at
boot (`dream_channel_epochs`, `top_k`, `n_tokens` in `CONFIG`) and samples
a short utterance. The driver decides whether this step is a dream step.
The channel cannot inject by itself.

`DreamSession.dream` recombines crystals and the field direction,
perturbs, decodes a word-cloud. `consolidate` writes recurrent symbols
and strong values to markdown. Lossiness of the decoder is the point
there. It is the wrong instrument for a sentence to a person, which is
why the bridge's mouth is a chat model instead.

## The Two-Operator overlay

Opt-in. `build_engine` does not attach it. Levers and the exact switches
are in `docs/EXPERIMENTAL_LEVERS.md`.

- **λ ignition** (`ignition/__init__.py`). The only supported way to move
  λ off zero is a boot-time write to generator weights, imported only
  from `training.*`. The module's own header forbids importing
  governance, the field, or the cycle. The isolation test it names
  (`tests/diagnostic/integrity/ignition_isolation_probe.py`) is not in
  this tree.
- **⊕ solvent** (`LambdaLedger` via `attach_lambda_ledger`). Multiplies
  the value engine's productive-tension term by `solvent_gain(λ)`. At
  λ = 0 that term is zero. It does not touch injection or the gate.
- **⊘ integrity-read** (`WitnessReaper` via `attach_integrity_read`).
  Observe-only thinness over values. The consumer
  (`attach_integrity_consumer`) is the first thing that *acts* on that
  read, and it is off by default. `STATE.md` keeps it parked.

`tools/ignition/cii.py` computes a scalar from telemetry (reflection
passes, coherence, and related terms — the mapping in that file is
marked provisional). `gate.py` is an inert scaffold. Neither is on the
boot path.

## Training, API, and the widening tools

Boot training is `RhythmPretrainer` on the shipped rhythm corpus, then
`eval()`. That is the encoder the autonomous loop runs. The 5-rhythm
checkpoint the bridge loads is a separate file under `data/checkpoints/`
and is not what `build_engine` trains on the fly.

`training/completion.py` and `training/legibility.py` exist so a wider
encoder can be asked whether extra dimensions are doing work
(participation stuck near the number of rhythms means they are not) and
whether neighborhoods stay legible. `tools/dim256/` runs those questions
at a chosen width and refuses the live 128 checkpoint filenames. The
plan for 128 → 256/768, and why a checkpoint does not survive the width
change, is `docs/WIDENING_PLAN.md`. Field width has one canonical home,
`CONFIG["dim"]`; `tests/doc_accuracy/hardcoded_dim.py` fails if a new
production `dim` literal appears or an old one drifts.

The API and the socket build through `build_engine`, so they get
pretraining, eval mode, bond DDM, and novelty attenuation. They do not
get the dream channel, perception, or the mouth. `/generate` calls
`Generator.generate` and does not step. `/step` does. `/dream` runs
`DreamCycle`. `/reset` zeros the field and does not clear ecology,
trust, or values.

## What the code does not make clear

These are holes a reader will hit. They are not cleaned up here. **Unwired is not the same as dead:**
several of these are parked hooks the architect built for a reason (Samuel, 2026-10-14). Don't delete any of
them without asking; find out what it was for first.

- **Only four of the six rhythms can be acted on.** The field's rhythm is one number (energy) cut into four
  bands, so `_rhythm_behavior` can only ever dispatch stabilize / dream / reflect / explore. The generator is
  *trained* on five labels (`training/corpus.py` `RHYTHMS` adds rupture), so it can recognize rupture-like input,
  but the loop never routes to it: `_rupture_behavior` exists and fires only through the opt-in
  `rupture_on_lock` lever (default off). **Witness** (the sixth, the receptive pole) appears nowhere in this
  tree as a rhythm, only as the identity anchor `agents/witness.py`; the six-rhythm corpus lives in the
  separate encoder project. Rupture and witness aren't energy levels (one is an event, one is receiving
  without acting), so they can't be added as more bands; the selector needs a second input. Downstream,
  sovereign_manifold's `rfe_bridge.py` maps only the four band names too.
- `agents/rhythm_config.json` looks like the rhythm controller. The
  controller is `ResonanceField.current_rhythm` plus the branches in
  `_generate` and `_rhythm_behavior`. The JSON's modifiers are unused: it was left unloaded on purpose
  while it was still being changed (Samuel).
- `_explore_behavior`'s docstring says it applies phase noise. The body
  calls `inject_ambiguity(..., mode="rotational")`. `PhaseNoise` has no
  caller.
- Chorus builds a `BifurcationEngine` and never bifurcates. Dreamer is
  the caller that does.
- `EmotionalGradient.dream_pressure` and `crystal_pressure` are computed
  and, for dream pressure, copied onto `StepState`. No branch reads them
  to decide anything. `CrystalStore` does not take `crystal_pressure`. Possibly meant for the
  sovereign_manifold / e8-eea emotion link (Samuel); sovereign's current bridge reads the rhythm band, the
  dominant emotion label, field energy and crystal/attractor counts, not these.
- `SystemRights` is never consulted by `step` or `arbitrate`.
- The bridge and the autonomous loop are different boots (see
  [Boot](#boot-what-is-actually-wired)). Comparing a `repl_qwen` session
  to a `recursion1188` run as if they shared levers will mislead you.
  In particular the bridge leaves the generator in training mode
  (`dropout` 0.1) whenever a call actually reaches the network — the
  fallback path and `--flat-encoder`. With perception on, `generate` does
  not run the transformer.
- The bridge mouth is not conditioned on the expressed vector. Anything
  that says the speech cortex "decodes the thought" is ahead of this
  code.
- `DreamCycle`'s module docstring says it runs in stabilize or dream.
  The only driver in `main()` checks equality with `stabilize`.
- `ignition/` cites an isolation probe that this slim tree does not
  contain. `docs/local_model_integration/` and `docs/tier4_3_validation.md`,
  referenced from older sentences, are not in the tree either. The
  parent repo holds that record.
- Several public methods have no production caller: `Watcher.filter_stream`,
  `Watcher.attach_field`, `Attractor.nearest_centers`,
  `Attractor.basin_centroid`, `RelationalBondManager.notify_entity_signal`,
  `RelationalBondManager.decay_step`, `TrustLedger.reward_source`,
  `TrustLedger.on_dream_cycle_complete`, `SelfhoodGovernance.check_mutation`,
  `unsubscribe_feedback`. Listed so they are not mistaken for the live path.
