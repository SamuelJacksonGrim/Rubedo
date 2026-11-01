# Which written contracts the step actually enforces

- **Date:** 2026-10-31
- **Substrate:** `tests._common.build_full_stack` (dim 64, pretrain off) for the live steps; direct calls for the bond, the named-damp arbitrate, the reaper, and `Witness(dim=8)`. CPU, two threads.
- **Probe:** throwaway, not kept. The holds are pinned by `tests/integration/held_contracts.py`.
- **Status:** standing
- **Depends on:** `2026-10-31-right-to-refuse-order` (the shape: a green suite, and no test that combined the two conditions)

## Question

CLAUDE.md states a set of contracts with "never / only / always / cannot / must". `right_to_refuse` was one of them: the text was true about trust and the bond floor, the suite was green, and nothing combined a failed hard gate with a queued manipulation damp. How many more of that shape are there?

Looked at, in the order asked: the sacred shield on every write path; bonds only emerging; the observe-only instruments; `source_dream` and the other voices; determinism; unbounded per-step structures; early returns that skip a later guard. The rhythm behaviours that inject after the gate are the open architect question already written into CLAUDE.md. They are listed. They are not re-opened.

## Pre-declared signatures

- HOLDS: the code enforces the sentence on every path that can reach it, and a test in the pass/fail suite fails if that path regresses.
- DOESN'T HOLD: some reachable condition breaks the sentence, whether or not a nearby test is green.

## Result

| Contract | Verdict | Condition | Reproduced | Severity | Pinned today |
|---|---|---|---|---|---|
| Sacred symbols cannot be modified, and the reaper cannot touch them | **Breaks** on the write paths below. The reaper's *decision* does not archive them | A shielded write, a flooded reference, a maintenance pass | Yes | High (archive, attractor); low (usage decay) | Decision label only (`sacred_shield`, `right_to_refuse`). Stage pin added |
| Bonds emerge only at interaction ≥ 20 AND coherence_mean ≥ 0.10 AND crystal ≥ 1 | **Breaks** on the classic path. No public constructor. DDM path holds | DDM off, allow_rate ≥ 0.80, coherence 0 | Yes | Medium | DDM path (`bond_ddm_invariants`). Constructor pin added |
| Metastability monitors, vibration gauge, `dilation_factor`, stream recorder are observe-only | **Breaks** for the monitor when `rupture_on_lock` is on. The other three hold | Lever on and the monitor reads `locked` | Yes for the lever; the others by source read | Medium, off by default | Vibration and recorder smokes. Dilation pin added. The lever is the break, so it is not pinned as a hold |
| `source_dream` goes through `arbitrate()`; instruments do not inject | **Holds.** Direct field writes are listed below | — | Source read, plus the crystal inject in the sacred row | — | Pin added |
| Model time, unseeded draws, and `uuid4` only in `substrate/determinism.py` | **Holds** under `deterministic()`. `dreamer.py:278` `random.sample` is outside the guard regex and uses the module RNG that context seeds | 30 unseeded draws, 30 distinct key tuples | Yes, as production entropy, not as a replay break | — | `determinism_replay` |
| No unbounded per-step structures | **Breaks** for the vector space, the topology log, and two witness lists | Every step, or coherence ≥ 0.80 | Yes | Medium | No (pinning a break would freeze it) |
| A failed hard gate is not skipped by an earlier return | **Block holds.** Named severity ≥ 0.60 still returns `quarantine` before the sacred label. The step does not return at all, so the writers above still run | Named signal 0.70 and a sacred fail | Yes | Low for the label. The writers are the high row | `right_to_refuse` pins the block, not the label |
| CORE promotion only through `review_core_promotion` | Holds | — | Source read | — | `core_promotion_handshake` |
| ⊘ consumer never changes a sacred value | Holds | — | Direct call | — | Pin added |
| `stable_id` is never reused | Holds | Address reclaimed | Direct call | — | Pin added |

## Sacred writes

The shield's own check is narrow and it does fire. `ethical_boundary.py:177` appends `sacred_mutation` only when every stable id in the write is sacred. `arbitrate` then returns `sacred_shield` at strength 0, and `autonomous_cycle.py:627` is the only place that consults that decision before `field.inject`. `tests/adversarial/sacred_shield.py` pins that decision. It does not look at the symbol afterwards.

One cold step, tokens `['3.12']`, source `pure_sacred`. Audit decision `sacred_shield`. `field.inject` was not called. The symbol still moved:

| field | before | after |
|---|---|---|
| usage | 1.0 | 2.0 |
| recurrence | 0.0 | 0.01 |
| lifespan | 0 | 1 |
| field_coherence | 0.0 | 0.64 |
| attractor_strength | 0.0 | 0.5 |
| attractor centers | 0 | 1 |

`generate` calls `registry.register` (`generator.py:627`) before the gate. On an existing symbol `register` (`symbolic_memory.py:1274`) bumps usage, recurrence, and lifespan. After the block, step 18 still calls `signal_coherence` (`autonomous_cycle.py:727`), and `update_field_coherence` (`symbolic_memory.py:1466`) has no sacred check. Step 12 still calls `attractor.add` when `rel_profile.composite >= 0.88` (`autonomous_cycle.py:666`). That predicate held on this first step. `attractor.py:153` then calls `signal_attractor(..., delta=0.5)`, and `update_attractor_strength` (`symbolic_memory.py:1454`) has no sacred check either. The refused vector is now a center. Later steps pull toward it.

Crystals did not form at the default thresholds on that step (0 → 0). The call is unconditional (`autonomous_cycle.py:647`) and does not read the decision. Opening the three crystal thresholds and the attractor threshold, same shielded token, rhythm still `stabilize`: crystals 0 → 1, and `field.inject` ran twice at strength 0.3. That strength is `CrystalStore.field_injection_strength`. One call is `_activate_crystal` (`memory_crystals.py:247`), inside `maybe_crystallize`. The other is `_stabilize_behavior` → `activate_nearest` (`autonomous_cycle.py:1051`), which is the rhythm path already on the open list. `crystal_binding` on `3.12` went to 0.6. `update_crystal_binding` (`symbolic_memory.py:1460`) has no sacred check.

`quarantine_symbol` (`symbolic_memory.py:1520`) has no sacred check. `arbitrate` calls it for every id in `trust_report.symbol_trusts` when the ethical recommendation is `QUARANTINE` (`selfhood_governance.py:372`). That recommendation is the flood gate, and only when the write is not all-sacred (a pure sacred write that also floods stays `sacred_shield`; reproduced, the symbol stayed active). A mixed reference is the case the F8 ruling lets through the sacred gate. With the user flood ceiling set to 0, tokens `['3.12', 'ordinary_word']`: audit decision `quarantine`, and `3.12` was gone from `registry.symbols` and present in the cold archive. The next encode of `3.12` resurrected it through `register`'s archive path, again without asking the shield. So a flooded mention of the anchor both exiles it and, if anyone says it again, pays the cold-resurrection cost and brings it back.

`decay_step` is the smaller one. `evaluate` returns `ACTIVE` for `state.sacred` before it looks at usage (`symbolic_memory.py:879`), and a sacred symbol stayed in the active set while a matched non-sacred symbol was archived. Before that return, `decay_step` has already assigned `state.usage = profile.compute(...)` (`symbolic_memory.py:1356`). One pass, usage 5.0, step 100: usage became 4.9493, stage stayed `ACTIVE`. The reaper does not archive a sacred symbol. The maintenance pass does rewrite its usage.

`fix0b_diversity_fitness` is off. When it is on, `update_diversity_credit` (`symbolic_memory.py:1440`) also has no sacred check, and the cycle calls it at step 4, before the gate (`autonomous_cycle.py:476`). Not run.

The ⊘ consumer does not do this. `IntegrityDecayConsumer.apply` skips `sacred_blocked` and `promoted_to_sacred` (`integrity_read.py:456`). A direct call left those strengths at 4.0 and 4.5 and pulled an ordinary value 4.0 → 0.0. CORE still goes through `review_core_promotion` and then `promote_to_sacred`. Boot sanctification of the three constants is `build_governance_constants`, which is the factory, not a second promotion path.

## Bonds

`RelationalBond(` appears once in the production tree, at `relational_bond_manager.py:448`, inside `_form_bond`. Nothing else constructs one.

`_form_bond` has two callers. The DDM caller (`_ddm_step`, `:438`) commits only on an ACCEPT crossing and only if interaction ≥ 20 and crystal ≥ 1. That is the production boot (`bond_ddm_formation: True`) and it is what `bond_ddm_invariants` pins.

The classic caller is the class default and what `build_full_stack` builds, because that helper does not pass `ddm_formation`. `_maybe_form_bond` (`:414`) takes the structural pair and then `coherence_mean >= threshold OR allow_rate >= 0.80`. CLAUDE.md states the three thresholds as an AND. README already describes the opt-out as "coherence / allow_rate ≥ 0.80", so this is a stale sentence in CLAUDE, not an undocumented side door. It is still not what that sentence says.

Reproduced with `RelationalBondManager()` (DDM off, adaptive on): one `notify_crystal`, twenty `allow` feedbacks at coherence 0. A bond exists. strength 1.0, coherence_mean 0.0, interaction_count 20, crystal_count 1. The adaptive floor had dropped the coherence bar to 0.01 by then; the mean was 0, so allow_rate is what qualified, not the lowered bar.

## Observe-only

`expression_vibration` is observed and copied into `status()`. The cycle never reads `expression_vibration.report`. Pinned by `stream_vibration_smoke`.

`stream_recorder` is the same shape. Pinned by `stream_recorder_smoke`.

`dilation_factor` and `subjective_time` are written in `TemporalStream` and advanced by `tick()`. Nothing under `agents/` or in `autonomous_cycle.py` / `recursion1188.py` reads `.dilation_factor` or `.subjective_time`. Pin added.

`StreamMetastabilityMonitor` is not observe-only on one path. `autonomous_cycle.py:504`:

```python
rupture_now = (
    self.config.get("rupture_on_lock", False)
    and report.stable
    and self.generator_metastability is not None
    and self.generator_metastability.report.regime_state == "locked"
) or (mode == "rupture" and not self.rupture_upstream)
```

`rupture_on_lock` is off unless something sets it. CONFIG does not. With the flag set, the watcher forced `stable`, and the monitor's report forced to `locked` after each observe: `_rupture_fires` went 0 → 1 on the next step. That read changes the vector (the held-direction blend) before the governance gate. `diversity_credit()` is the one read CLAUDE.md carves out, and its lever is off. This is a second read, and it is not carved out.

`tools/ignition/gate.py` also reads `expression_metastability`. That is outside the loop, on the λ path that is supposed to stay outside the gate. Not counted as a loop read.

## Voices

`DreamChannel` never calls `field.inject`. `main` sets `source_id` from `dream_channel.SOURCE_ID` (`"source_dream"`) and calls `cycle.step` (`recursion1188.py:585`). `DreamSession` does not call `field.inject`. Pin added.

`field.inject` inside the running system, other than the gated candidate:

| Call | Strength | When |
|---|---|---|
| `memory_crystals.py:248` `_activate_crystal` | 0.3 | a crystal forms or is activated, decision not consulted |
| `autonomous_cycle.py:1051` stabilize `activate_nearest` | 0.3 | rhythm `stabilize` |
| `dreamer.py:194` | emotional | rhythm `dream`, or `force_dream_flag` |
| `autonomous_cycle.py:1110` reflect chorus | 0.3 | rhythm `reflect` and a chorus is attached |
| `autonomous_cycle.py:1121` explore mutation | 0.5 | rhythm `explore` |
| `autonomous_cycle.py:1163` `_rupture_behavior` | 0.7 | not in the dispatch. The comment at `:1154` says callable only directly |

The last four, and the dreamer, are the internal-motion question CLAUDE.md already leaves open. The crystal store's own inject is not that question. It is the sacred-write row above. The shielded step with the thresholds opened did hit it.

## Determinism

`determinism_replay` already scans `agents`, `substrate`, `cognition`, `interference`, and `loop` for `time.time`, `time.monotonic`, `datetime.now` / `utcnow`, `default_rng()`, and `uuid.uuid4`. That scan is clean, and the replay half of the contract is what the test runs.

`agents/dreamer.py:278` is `random.sample(keys, n)`. The regex does not see it. It draws the `random` module, which `deterministic()` seeds, so a run inside the context does not have a second entropy source. Outside it, thirty calls gave thirty distinct key tuples. That is the production side the existing test asks for (fresh entropy), not a replay hole. `resonance_field.py` builds `default_rng(seed=self._step)`, which the regex also skips because the call is seeded. Same step, same draw.

## Unbounded

Every `step` does `vector_space.put` on a new key (`autonomous_cycle.py:707`) into a `VectorSpace` built with `max_size=None` (`:230`, `vector_space.py:66`). The same step does `topology.add` (`:682`) into a `TopologicalLog` with no cap (`topological_log.py:46`). Four steps: vectors 0 → 4, topology nodes 0 → 4.

`Witness` keeps `identity_trace` at `maxlen=256`. `snapshots` and `crystallization_candidates` are plain lists (`witness.py:437`, `:455`). Six updates of one unit vector at coherence 0.95: snapshots 0 → 12, candidates 0 → 6, no maxlen. High coherence emits a snapshot at ≥ 0.80; crystallization emits another snapshot and a candidate. A steady vector clears both.

Capped, and not the finding: crystals 512, attractor centers 64, lattice `max_nodes` 2048, step history 1000, audit log, the flood deque (pruned by the time window), metastability centroids (`_max_centroids`).

## Early return

The refuse fix left step 1's `QUARANTINE` returns in place, because they are blocks. Direct call: ethical result `passed=False`, gates `['sacred_mutation']`, recommendation `SACRED_SHIELD`; one named `drift` signal at severity 0.70. `arbitrate` returned `quarantine` at strength 0. The injection is blocked. The sacred label and the magnitude-1.0 penalty do not run; the named branch penalizes 0.4 (`selfhood_governance.py:332`) and returns at `:334`. That is the residual of the order fix, not a second allow.

The step itself has the other shape. Nothing returns after a block. Crystal evaluation, attractor formation, the vector-space put, the topology node, `signal_coherence`, and the rhythm behaviour all run for a `sacred_shield` step. That is the sacred table, not a separate hole.

## What this pass did not change

No contract that failed was patched. `held_contracts.py` pins the ones that held and had no test: reaper stage, stable id, the ⊘ consumer, the single bond constructor, `source_dream` / `DreamSession` not injecting, and the dilation sink. `sacred_shield` still does not look past the decision.

## Threats / confounds

- The live steps are dim 64, one cold stack, not the 128-d canonical run. The attractor on step 1 is the witness composite clearing 0.88 against an anchor that was just born from that same vector. A later step whose relation sits under 0.88 would not add a center. The missing check does not depend on the step number.
- Crystal injection was reproduced by opening the thresholds, not by waiting for a natural crystal. At the defaults the shielded step formed no crystal.
- The flood ceiling was set to 0 so the first mixed step flooded. The production ceiling is 12 per 60 seconds. The branch it enters is the same branch.
- `build_full_stack` leaves the bond accumulator off. `build_engine` turns it on. The allow_rate bond is the classic path, which is the class default and the documented opt-out, not this morning's production boot.
- `rupture_on_lock` was forced, and so was `regime_state`. The flag is not in CONFIG.

## Open / next

- [ ] Whether a shielded write should be allowed to register, to become an attractor, to crystallize, or to be `signal_*`'d. The refuse fix was an ordering change. This one is which writers are inside the shield.
- [x] `quarantine_symbol` on a sacred id. A flooded reference cold-archives `3.12`. → DONE 2026-10-31: refused for a sacred id (logged), pinned in `held_contracts` [7].
- [x] CLAUDE.md's bond sentence still says AND coherence_mean ≥ 0.10. The classic path has said OR allow_rate since the Tier 1 revision. Decide which text is the contract. → DONE 2026-10-31: the code is the contract (README already said so); CLAUDE.md now states coherence OR allow rate.
- [ ] `rupture_on_lock` reads the monitor and changes the vector. Off. CLAUDE.md allows one read (`diversity_credit`) and not this one.
- [x] Vector space, topology, and the two witness lists grow without a cap. → DONE 2026-10-31: VectorSpace max_size 16384 (its existing eviction), TopologicalLog max_nodes 4096 (oldest dropped), witness lists deque(maxlen=1024); all above any run in the suite, so nothing changes until a run passes them. Pinned in `held_contracts` [8].
- [x] `decay_step` rewrites sacred usage before the reaper returns ACTIVE. → DONE 2026-10-31: usage is not recomputed for a sacred symbol; pinned in `held_contracts` [1].
