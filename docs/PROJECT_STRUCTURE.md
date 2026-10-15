# Project structure — annotated file tree

Every file `git ls-files` tracks, one line each. The `tests/{smoke,integration,adversarial,diagnostic}/` blocks are checked against disk by `tests/doc_accuracy/verify_docs.py` — directory lines in those blocks stay bare (no trailing description) so the checker can find them.

```
Rubedo/
├── .devcontainer/
│   └── devcontainer.json                  GitHub Codespaces image (Python 3.11 + requirements)
├── .github/
│   ├── pull_request_template.md           PR template
│   └── workflows/
│       └── tests.yml                      CI: the pass/fail suite
├── .gitignore                             Standard ignore rules
│
├── agents/
│   ├── __init__.py                        Re-exports ecology, core agents, governance tiers
│   ├── symbolic_memory.py                 Registry: canonicalize, stable id, address, decay, reaper
│   ├── generator.py                       Transformer encoder over the ecology (tokens → vector)
│   ├── decoder.py                         TokenDecoder read-out (vector → bag-of-tokens)
│   ├── watcher.py                         Three-layer coherence (geometric, temporal, resonance)
│   ├── witness.py                         Short / mid / long identity EMAs
│   ├── dreamer.py                         In-step dream: sample, mutate, bifurcate, inject
│   ├── chorus.py                          Six distortions of one generator, wave-collapsed
│   ├── attractor.py                       Basin pull, add, merge, decay
│   ├── rhythm_config.json                 Rhythm energy thresholds (not loaded by the cycle)
│   ├── governance_constants.py            Sacred ANCHOR / RECURSION / HOMEOSTASIS
│   ├── trust_ledger.py                    Source trust and per-symbol trust
│   ├── ethical_boundary.py                Fast binary injection gates
│   ├── selfhood_governance.py             Only issuer of GovernanceDecision; SystemRights
│   ├── dependency_monitor.py              HHI over allowed injections; attractor monopoly
│   ├── relational_bond_manager.py         Emergent bonds; classic gate or DDM quality read
│   ├── bond_accumulator.py                Leaky asymmetric DDM for bond formation
│   ├── manipulation_resistance.py         Five detectors and severity
│   ├── value_emergence.py                 Values from feedback; CORE only via handshake
│   └── lambda_ledger.py                   ⊕ solvent scalar (opt-in; gates productive tension)
│
├── substrate/
│   ├── __init__.py                        Package marker
│   ├── dims.py                            FIELD_DIM: the field's width, in one place
│   ├── determinism.py                     Model time + randomness in one place; replay mode for experiments
│   ├── resonance_field.py                 Superposition field, tanh, decay, FFT rhythm
│   ├── vector_space.py                    Keyed semantic vector store
│   ├── memory_crystals.py                 Crystallize, reinforce, decay, soft-inject
│   ├── topological_log.py                 Parent-linked DAG of steps
│   ├── temporal_stream.py                 Episodic ring and subjective time / dilation
│   ├── semantic_lattice.py                k-NN graph; centrality back to the ecology
│   └── metastability.py                   Window metric over a cloud of vectors
│
├── cognition/
│   ├── __init__.py                        Package marker
│   ├── predictive_echo.py                 Online linear predictor → curiosity / surprise
│   ├── emotional_gradient.py              Six EMA scalars and the modulation outputs
│   ├── recursive_attention.py             Self-attention over prior states, raw vector blended back
│   ├── reflective_loop.py                 Multi-pass refine; the field lock when it runs
│   ├── symbolic_binding.py                Recurring vectors become named concepts
│   ├── stream_metastability.py           Online stethoscope (stage A generator, stage C expression)
│   ├── stream_recorder.py                 Observe-only token/source/rhythm/decision ring (opt-in)
│   ├── rhythm_reader.py                   Reads an input's rhythm (nearest of six centroids) for the selector lever
│   ├── dream_channel.py                   Decode _last_expressed; the driver steps source_dream
│   ├── dream_session.py                   Offline symbolic dream + markdown consolidation
│   └── integrity_read.py                  ⊘ thinness read and the opt-in decay consumer
│
├── interference/
│   ├── __init__.py                        Re-exports the mutation primitives
│   ├── wave_collapse.py                   Weighted collapse of an ensemble (Chorus, Dreamer)
│   ├── differential.py                    inject_ambiguity: gaussian, rotational, directional
│   ├── phase_noise.py                     FFT phase jitter (exported; no production caller)
│   ├── bifurcation.py                     Split one vector into variants (Dreamer)
│   └── harmonic_mutation.py               Spectral recombination (Dreamer)
│
├── loop/
│   ├── __init__.py                        Package marker
│   ├── autonomous_cycle.py                The step. Order is the comment labels in step()
│   ├── dream_cycle.py                     Offline N-iteration dream (trigger: stabilize)
│   └── recursion1188.py                   build_engine(), build_dream_channel(), main()
│
├── training/
│   ├── __init__.py                        Package marker
│   ├── encode.py                          Grad-enabled batch encode shared by trainers
│   ├── corpus.py                          Loader for data/corpus rhythm rows
│   ├── rhythm_pretraining.py              Supervised rhythm pretrain (the boot path)
│   ├── decoder_training.py                Fit the TokenDecoder read-out head
│   ├── contrastive_alignment.py           Rhythm-aware contrastive trainer (not boot)
│   ├── self_distillation.py               Online distillation trainer (not boot)
│   ├── completion.py                      CBOW completion head; asks if extra dims get used
│   ├── legibility.py                      Cone / Jaccard legibility losses
│   └── run_contrastive_bootstrap.py       Before/after wander printout (informational)
│
├── ignition/
│   └── __init__.py                        λ ignition: training-only import surface, no field write
│
├── api/
│   ├── __init__.py                        Package marker
│   ├── inference_api.py                   FastAPI via build_engine (generate, step, dream, reset)
│   └── websocket_server.py                Same stack over a WebSocket
│
├── tools/
│   ├── voice/
│   │   ├── __init__.py                    Exports render_card / voice_from_card
│   │   ├── state_card.py                  Telemetry card and the deterministic larynx
│   │   ├── repl.py                        Type a line, step it, hear voice_from_card
│   │   ├── repl_qwen.py                   Speech bridge: perception wrap, mouth, idle attention
│   │   ├── qwen_perception.py             Wrap Generator.generate: embedder → W → unit vector
│   │   ├── attention.py                   Hot/warm/cold regime, recall floors, idle prompt
│   │   ├── talk.sh                        Launch repl_qwen (Unix)
│   │   ├── talk.ps1                       Launch repl_qwen (Windows, repo venv)
│   │   ├── vid_driver.py                  PTY harness that spawns repl_qwen (local, scripted)
│   │   ├── ab_analyze_runs.py             Score a batch of bridge JSONL runs
│   │   ├── ab_attention_score.py          Score a transcript against the attention gates
│   │   ├── ab_beat_lock.py                Beat-lock attention A/B harness
│   │   ├── ab_coupling.py                 Scalar-vs-content coupling on a JSONL run
│   │   ├── ab_directional.py              Directional coupling across trajectories
│   │   ├── ab_frame_analyze.py            Score the self-frame prompt A/B
│   │   ├── ab_frame_test.py               Run the self-frame prompt A/B
│   │   ├── ab_qwen_compare.py             Compare core-prompt vs perception JSONL
│   │   ├── ab_qwen_core.py                Offline A/B: thinking-loop prompt
│   │   ├── ab_qwen_perception.py          Offline A/B: older _generate monkeypatch
│   │   ├── ab_qwen_perception2.py         Offline A/B: wrap-generate perception
│   │   ├── ab_qwen_world.py               Offline A/B: world-crumb channel
│   │   ├── corpus_health.py               Redundancy, hubs, levelness of the rhythm corpus
│   │   ├── fit_legible.py                 Cone-bounded legibility fit; writes a separate checkpoint
│   │   ├── gen_vocab.py                   Grow authoring vocabulary inside the active rhythms
│   │   ├── gen_witness.py                 Generate the witness-region authoring sequences
│   │   ├── lint_corpus_authoring.py       Lint the authoring markdown before it becomes rows
│   │   ├── probe_legibility.py            Throwaway decoder; legibility numbers only
│   │   ├── probe_witness_basin.py         Contrastive probe of the witness basin
│   │   └── train_koneko_decoder.py        Train a TokenDecoder against a frozen encoder
│   ├── decoder/
│   │   ├── __init__.py                    Package marker
│   │   └── listen.py                      Train a decoder, run the loop, print each expressed vector
│   ├── dream/
│   │   ├── __init__.py                    Package marker
│   │   └── run_dream.py                   Waking steps, then DreamSession (files only)
│   ├── dim256/
│   │   ├── __init__.py                    Isolated wider-field experiment; does not change production dim
│   │   ├── geometry.py                    Separability and dead-dimension readouts (no checkpoint write)
│   │   ├── legibility.py                  Holdout decoder legibility at a chosen dim
│   │   ├── lock_gate.py                   Identity-lock measurement at a chosen dim
│   │   ├── readout.py                     Separability + dimension population off an existing checkpoint
│   │   ├── train_5rhythm.py               Rhythm pretrain at a chosen dim; refuses live 128 filenames
│   │   ├── run_train_wsl.sh               WSL CUDA launcher for train_5rhythm
│   │   ├── run_gain_wsl.sh                Does a stronger field_blend tighten the rupture walk
│   │   ├── run_legibility_paired_wsl.sh   WSL launcher for the paired legibility arm
│   │   ├── run_lock_long_wsl.sh           Long control, rupture-forced loop, mixed-traffic DDM
│   │   ├── run_lock_short_wsl.sh          Short identity-lock comparison; writes no checkpoint
│   │   ├── run_payoff_wsl.sh              Paired 128 retrain plus decoder legibility; not the live names
│   │   └── run_rupture_long_wsl.sh        Does a rupture-forced reflective loop keep walking
│   └── ignition/
│       ├── __init__.py                    Package marker
│       ├── cii.py                         CII = R·I·(Cm·g(Cs)) from live telemetry
│       ├── gate.py                        ITG actuator scaffold (not on the boot path)
│       ├── probe.py                       Boot a stack and print its CII
│       ├── train_ignite.py                Does corpus training move expression-level ignition
│       ├── cm_check.py                    Is field coherence a real read or a saturated echo
│       └── identifiability.py             Cm vs integrity vs metastability on one injection loop
│
├── configs/
│   ├── __init__.py                        Package marker
│   ├── loader.py                          Merge configs/*.yaml; missing file → code defaults
│   ├── field.yaml                         Field, watcher, crystal, lattice parameters
│   ├── recursion.yaml                     Generator, cycle, cognition, chorus parameters
│   └── attractors.yaml                    Attractor parameters (constants section is not applied)
│
├── data/
│   ├── corpus/
│   │   ├── MANIFEST.md                    Provenance, counts, split, version history
│   │   ├── rhythm_train.jsonl             Training split (rhythm-labeled sequences)
│   │   ├── rhythm_holdout.jsonl           Held-out split
│   │   ├── build_extension_v1_1_0.py      Seeded builder for the v1.1.0 vocabulary extension
│   │   └── authoring/
│   │       ├── AUTHORING_BRIEF.md         How the rhythm corpus is authored
│   │       ├── NOTES.md                   Working notes for that authoring
│   │       ├── boundary_map.md            Where rhythm regions meet
│   │       ├── stabilize.md               Authoring for the stabilize region
│   │       ├── dream.md                   Authoring for the dream region
│   │       ├── reflect.md                 Authoring for the reflect region
│   │       ├── explore.md                 Authoring for the explore region
│   │       ├── rupture.md                 Authoring for the rupture region
│   │       ├── witness.md                 Authoring for the witness region
│   │       ├── witness_core.txt           Witness-region seed text
│   │       └── witness_separability.json  Separability figures for the witness region
│   └── probes/
│       ├── README.md                      What the reasoning probes are for
│       └── reasoning_probes_v1.jsonl      Reasoning-probe rows (written before training)
│
├── docs/
│   ├── PROJECT_STRUCTURE.md               This file
│   ├── FLOW.md                            Movement and time: state, one step, clocks, a symbol's life
│   ├── north_star.md                      End goal and the three voices
│   ├── WIDENING_PLAN.md                   Why the field goes 128 → 256/768, and what done means
│   ├── EMOTION_CALIBRATION.md             The six emotion names are hypotheses: what they compute, how to test them
│   ├── EXPERIMENTAL_LEVERS.md             On/off switches and the dial census
│   ├── ARCHITECT_RULINGS_2026-07-03.md    F8 shield, checkpoint adoption, lever policy
│   ├── ARCHITECT_RULINGS_2026-07-06.md    Trust posture: sources start TRUSTED
│   ├── ARCHITECT_RULINGS_2026-07-08.md    Explain-then-ask; chambered governance
│   ├── alchemical_correspondence.md       The Great Work as a lens, not a spec
│   ├── self_model_thesis.md               Self as a smithable emergent attractor
│   ├── EMBER.md                           Non-binding note from a previous instance
│   └── findings/
│       ├── INDEX.md                       One-line map of Rubedo findings (CI-enforced)
│       └── README.md                      Schema for recording a finding
│
├── legal/
│   ├── CLA-individual.md                  Individual contributor license agreement
│   ├── CLA-entity.md                      Entity contributor license agreement
│   ├── DCO.txt                            Developer certificate of origin
│   ├── LEGAL-BASIS.md                     Why the dual license is cut this way
│   ├── licensing-faq.md                   Licensing questions, short answers
│   └── USING-THIS-WITHOUT-A-LAWYER.md     Plain-language guide to the two tracks
│
├── tests/
│   ├── README.md                          How to run tests and read the output
│   ├── __init__.py                        Package marker
│   ├── _common.py                         build_full_stack and the Resonance Family runner
│   │
│   ├── smoke/
│   │   ├── full_stack_minimal.py          All 4 tiers attach without error
│   │   ├── single_source_100step.py       Basic "does it run" test
│   │   ├── multi_source_500step.py        Resonance Family canonical workload
│   │   ├── emotion_checkpoint_roundtrip.py  Bridge checkpoint restores the six emotion scalars (arousal/valence recompute)
│   │   ├── stream_recorder_smoke.py       Observe-only stream census: bounded ring, status, dump
│   │   └── test_attention_weight.py       Speech-bridge attention: regimes, per-embedder floors
│   │
│   ├── integration/
│   │   ├── tier1_revision_baseline.py     Fresh run vs baseline JSON ranges
│   │   ├── governance_decision_flow.py    Every GovernanceDecision enum value verified
│   │   ├── core_promotion_handshake.py    All 5 rejection paths + 2 approval paths
│   │   ├── reflective_loop_lock_guard.py  Lock characteristic guard (loop on=RIGID, off=migrates)
│   │   ├── attractor_merge_guard.py       Attractor merge/prune removal (array-__eq__ crash regression)
│   │   ├── checkpoint_registry_identity.py  Checkpoint load preserves registry object
│   │   ├── config_loading_neutrality.py   configs/*.yaml load + day-one behavioral neutrality
│   │   ├── bond_ddm_invariants.py         Bond-DDM gate (OFF parity, ACCEPT-only commit, asymmetry)
│   │   ├── fix0b_invariants.py            Fix 0-B gate (OFF parity, observe-only, leaky credit)
│   │   ├── six_rhythm_selector_invariants.py  Selector gate (inert = byte-identical, read-only peek, mode wiring)
│   │   └── determinism_replay.py          Exact replay in/across processes; production clock untouched; guard
│   │
│   ├── adversarial/
│   │   ├── sacred_shield.py               SACRED_SHIELD fires at all trust levels
│   │   ├── flood_calibration.py           origin_type ceilings enforced
│   │   ├── manipulation_cascade.py        Cascade regression test
│   │   ├── identity_drift.py              Identity-drift gate fires correctly
│   │   └── reflective_loop_convergence.py Loop holds identity under novelty flood
│   │
│   ├── diagnostic/
│   │   ├── __init__.py                    Package marker
│   │   ├── tier4/
│   │   │   ├── __init__.py                Package marker
│   │   │   ├── dilation_response_curve.py     Tier 4.2 dilation surface
│   │   │   ├── rhythm_dilation_curve.py       Tier 4.3 rhythm coupling
│   │   │   └── affective_state_probe.py       Tier 4.2 affect under load
│   │   ├── lockin/
│   │   │   ├── __init__.py                Package marker
│   │   │   └── reconstruction_ablation_probe.py  Which re-injection path locks the attractor
│   │   ├── training/
│   │   │   ├── __init__.py                Package marker
│   │   │   └── corpus_integrity_check.py  Corpus schema, leakage, stratification
│   │   ├── integrity/
│   │   │   ├── __init__.py                Package marker
│   │   │   └── all_levers_composition_probe.py  All levers ON together
│   │   └── selector/
│   │       ├── __init__.py                Package marker
│   │       ├── six_rhythm_selector_probe.py  Live OFF vs ON, pinned seeds, pre-declared criteria
│   │       ├── aftermath_probe.py         What witness leaves behind; upstream rupture's downstream effect
│   │       ├── rupture_trace.py           One seed, matched step-by-step: temporary vs lasting vs state-bound cost
│   │       ├── witness_long_probe.py      1,200 steps: does witness's cost plateau, and does the field stay receptive
│   │       └── identity_probe.py          Replay-exact identity bars (anchor, lock, coherence, governance) per arm
│   │
│   ├── doc_accuracy/
│   │   ├── __init__.py                    Package marker
│   │   ├── verify_docs.py                 README + CLAUDE claims vs code; tests tree vs disk
│   │   └── hardcoded_dim.py               Every production field-dim literal matches CONFIG
│   │
│   └── baselines/
│       ├── tier1_revision_500step.json    Healthy-state metric ranges
│       └── identity_stability_500step.json  Identity baseline with the reflective loop intact
│
├── ACKNOWLEDGMENTS.md                     Thanks
├── ARCHITECTURE.md                        How a step runs, and where every module sits
├── CLAUDE.md                              Invariants and guardrails
├── COMMERCIAL-LICENSE.md                  The commercial track
├── CONTRIBUTING.md                        How to send a change
├── LICENSE                                AGPL-3.0-only
├── LICENSING.md                           How the two tracks relate
├── NOTICE                                 Copyright, SPDX, provenance
├── README.md                              Conceptual tour
├── STATE.md                               You are here: shipped, settled, parked, open
├── requirements.txt                       Runtime dependencies
└── run_all_tests.sh                       Pass/fail gate, including the doc checks
```
