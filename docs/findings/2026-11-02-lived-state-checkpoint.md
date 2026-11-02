# Can a restart resume the same identity, or does it re-grow trust, bonds, crystals and attractors?

- **Date:** 2026-11-02
- **Substrate:** `tests._common.build_full_stack` (dim 64, pretrain off, `bond_ddm_formation` on), CPU, `CUDA_VISIBLE_DEVICES=-1`.
- **Probe:** `tests/integration/lived_state_checkpoint.py`
- **Status:** standing
- **Depends on:** `2026-10-14-bridge-emotion-never-restored` (the bridge checkpoint and what it still omitted), `2026-10-31-shield-scope` (a refused input cannot enter identity), `2026-10-31-contract-audit` (bonds emerge; caps)

## Question
A living system's accumulated state — trust ledger, relational bonds, memory crystals, attractors — dies on restart. Can we save and restore it so the next process is the same identity, without turning a checkpoint file into a public bond constructor or a way to override later tuning?

## Pre-declared signatures
- SUCCESS looks like: the production `save_checkpoint(path, gen, cycle, ve)` call (no extra `gov`) writes trust and bonds; a fresh stack load restores them in-place; DDM and `_stability_ref` keep their object identity; thresholds in the file are ignored; a planted or malformed payload raises and leaves live state untouched; the new test fails on the unfixed code.
- FAILURE looks like: the test can pass while production does not save trust/bonds; restore replaces the DDM or drops the emotion stability ref; an old file's constants silently override code.
- CONFOUNDED looks like: "the fields came back" on a helper the bridge never calls.

## Result (observed)

**Before (this worktree, unfixed `save_checkpoint`):**

```
SIG def save_checkpoint(path, gen, cycle, ve)
HAS_GOV_PARAM False
READS_CYCLE_GOV False
KEYS ['emotion', 'field', 'registry', 'saved', 'schema', 'step', 'values']
HAS_LIVED False
```

Hermes's isolated draft (`rubedo-hermes` `1dcef7e`) added `gov=None` and a passing round-trip that passed `gov` into the helper. Production call sites never did, so trust and bonds would not have saved. That draft also rebuilt the manager through `__new__` + `__dict__`: `_ddm = None`, `_stability_ref = None`, thresholds restored from the file, bonds planted from a summary dict.

**After:** `tests.integration.lived_state_checkpoint` 42/42.

| Check | Result |
|---|---|
| Production signature (no `gov=`); `snapshot_from_cycle` reads `cycle.governance`; session persistence writes and loads `lived_state.json` | hold |
| File contains `lived.trust` and `lived.bonds` after `save_checkpoint(path, gen, cycle, ve)` | hold |
| Trust scores, bonds, crystals (n=0 at 40 steps), attractors (n=3) round-trip | hold |
| Live DDM object and `_stability_ref is cycle.emotion` survive load | hold |
| Tampered `coherence_threshold=0`, `formation_interaction_threshold=1`, `decay_rate=0` do not override code (still 0.75 / 20 / 0.003) | hold |
| Planted bond (`interaction_count=1`, `crystal_count=0`, no trust record) raises `LivedStateError`; mixed valid-trust + planted-bond applies neither | hold |
| Wrong dim, over-cap crystals (`max_crystals+1`) raise; live store stays empty | hold |
| Old-format bridge file (schema 1, no `lived`) skips identity, does not invent bonds | hold |

**Twin** (restore at step 40 into a fresh stack, then both take the same 12 `source_samuel` inputs):

| | |
|---|---|
| trust | match |
| decisions | match (12/12 `reject` — flood from repeating one source, both twins) |
| crystals | match (still 0) |
| bonds | diverge (attractor_count / type signals) |
| attractor centers | diverge |
| field cosine | 0.998 |
| witness-anchor cosine | 0.000 |

Witness starts at zero on the restored twin. Field was in the bridge file, so it stays close. Attractors keep moving from an unrestored witness / attention / predictor, and the bond's attractor_count follows. That is the continuation gap, not a round-trip miss.

## Interpretation
Restore is reconstitution of already-lived state into the objects production already built. The four stores, pre-bond counters, and DDM V+RNG are state. Thresholds, learning rates, and the DDM physics constants are not. Bonds go through the one `_make_bond` constructor (`held_contracts` still pins a single `RelationalBond(`), and only after the live formation thresholds and a trust record exist — a checkpoint cannot plant a bond that never earned one.

A checkpoint is an input to identity. Malformed, stale-dim, over-cap, or planted payloads fail loud and leave the live system untouched. Restore is not a write through `arbitrate()`, so the sacred shield does not re-run over `origin_tokens`; a lived crystal that mentions `3.12` is memory, not a new refused input. A writable checkpoint is as trusted as `ecology.json`. Signing is not in this change.

What this does **not** restore: witness (short/mid/long/anchor, ghosts), temporal stream, predictive echo, attention window, vector space, lattice, topology, manipulation windows, dependency window. Session persistence still does not save the field or emotion (the bridge file does). Vector-space and witness-list caps stay a separate contract-audit item; this path refuses over-cap crystals and attractors and does not start restoring those stores.

## Threats / confounds
- Runs: 1 on the gate (42 checks). Fail-before was a direct `save_checkpoint` on the unfixed function, not a full suite replay of Hermes's 500-step helper.
- dim 64, 40 warm steps, one forced DDM bond via `notify_crystal` + allow feedback so the test does not depend on crystals forming. Attractors formed on their own (3). Crystals did not.
- Twin inputs were one source repeating — both twins hit `reject`. That equalizes the decision row and is not a claim about a mixed workload.
- `formed_at` / `last_reinforced` use `determinism.now()` (wall clock outside `deterministic()`). They round-trip as numbers; they are not why the twin's bonds diverged.
- Hermes's draft was read with `git -C` and not merged.

## Open / next
- [ ] Witness, stream, predictor, attention, vector space, lattice, topology on a restart. The twin names the witness hole (cosine 0) as the one that moves attractors.
- [ ] Field and emotion on the session-persistence path (already in the bridge file).
- [ ] A mixed-source twin whose decisions are not a flood of `reject`.
- [ ] Whether a checkpoint should be signed, or whether "who can write `lived_state.json`" is the whole trust boundary.
