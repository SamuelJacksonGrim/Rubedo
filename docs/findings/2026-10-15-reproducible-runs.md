# Runs replay exactly: model time and randomness in one place

**Date:** 2026-10-15 · **Status:** resolved (same commit) · **By:** Ember; requirements from GPT/Raphael

## Question
Seeded experiments did not replay (`2026-10-14-witness-aftermath-and-upstream-rupture`, follow-up 1: OFF's end-of-run
coherence moved 0.04 between two runs of the same seed). Can a run be made exactly reproducible without changing
production behavior?

## What was uncontrolled (audit)
- **Wall clock, 36 sites:** 25 direct `time.time()` reads (the `EthicalBoundary` flood window, crystal age, the
  temporal stream's tick, trust/bond/witness/governance timestamps, logs) plus 11 dataclass
  `default_factory=time.time` stamps (crystals, attractors, bonds, bindings, trust records, manipulation signals).
- **Unseeded entropy, 9 sites:** `np.random.default_rng()` in chorus, dreamer, vector space and the interference
  primitives; plus python's global `random` (dreamer sampling) and numpy's global generator (training).
- **Random keys, 3 sites:** `uuid4` step keys (topology, vector space, lattice), dream keys, value ids.

## Change
`substrate/determinism.py`: `now()` (model time), `make_rng()`, `new_key()`, and `deterministic(seed, dt)`.
Production = real clock, fresh entropy, uuid4: **behavior unchanged**. Inside `deterministic(...)`: a SimClock that
advances `dt` per cycle step (`AutonomousCycle.step` calls `on_step()`), generators spawned from one SeedSequence in
call order, seeded keys, and python/numpy/torch global seeds; all restored on exit. All 48 sites routed; 10 now-unused
`import time` lines removed. **Explicit time semantics:** `now()` is the mind's time; `perf_counter` stays real because
it is elapsed-time telemetry (only `StepState.elapsed_ms` / DreamCycle timing read it, and nothing behavioral does).

## Control
`tests/integration/determinism_replay.py` (in `run_all_tests.sh`):
1. Two 60-step four-source runs in `deterministic(11)`: field, emotion, trust, step keys, governance decisions,
   crystal/attractor counts and registry usage **identical**; seed 12 differs.
2. The same run in two fresh interpreters: **identical digests**, equal to the in-process digest (so nothing
   process-dependent, such as str-hash ordering of sets, leaks into behavior).
3. Outside `deterministic`: real clock (within 1 s of `time.time()`), fresh entropy per generator.
4. Sim time drives behavior: 30 user-origin steps 0.05 s apart trip the flood ceiling 18 times; 10 s apart, 0.
5. Guard: no production module reads the wall clock, draws unseeded entropy or mints uuid4 except
   `substrate/determinism.py`.
Also: the selector probes now use replay mode instead of the old `default_rng` monkeypatch (which missed the clock);
`rupture_trace` run twice from the same checkpoint printed identical output.

## Remaining nondeterminism (not covered)
- The pretrained generator: torch is seeded inside `deterministic`, so CPU runs replay; GPU kernels can still be
  nondeterministic unless torch's deterministic algorithms are forced.
- The speech bridge's LLM calls (Qwen over HTTP) are outside the substrate and not replayable.
- Elapsed-time telemetry varies by design.

## Effect on earlier findings
Arms compared **within one invocation** (all of 2026-10-14's selector work) were paired correctly even before this;
comparisons of snapshots **across invocations** were not. Future runs replay exactly: re-run any arm and get the same
numbers.
