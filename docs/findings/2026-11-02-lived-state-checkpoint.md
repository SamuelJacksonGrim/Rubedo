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
| Planted bond (source with no trust record) raises `LivedStateError`; mixed valid-trust + planted-bond applies neither | hold |
| Wrong dim raises; live store untouched | hold |
| Over-cap crystals truncate to the live cap (a retune must not refuse the mind) | hold |
| A bond below a retuned live formation threshold still restores | hold |
| Old-format bridge file (no `lived`) skips identity, does not invent bonds | hold |
| Refused load + subsequent save: original bytes survive at `*.refused-<timestamp>` | hold |
| Bridge registry load keeps Fix 0-B `_profiles` and `binding_leak` | hold |
| A bonded source is not also tracked as pre-bond | hold |

**Twin, first version** (one source, 12 steps): witness cosine 0.000, field 0.998, all 12 decisions `reject` (flood). Named the witness hole. Superseded by the mixed twin below.

**Twin, mixed** (48 warm steps across four family sources + 3 sacred refusals, restore, then 24 more mixed steps with RNG locked per step). Decisions in the window: `allow_weakened` and `sacred_shield`.

| | first divergence (step of 24) | end |
|---|---|---|
| decisions | held | held 24/24 |
| witness-anchor cosine | held | 0.99998 |
| field cosine | held | 0.99987 |
| ghosts | held | held |
| trust / bonds / emotion / attractors | 1 | drifted |
| crystals | 2 | drifted |

Witness was the named hole and it closed. Queued `_pending_signals` was the next: without it, decisions split at step 1 even with restored windows. With it, the gate stays with the twin for the whole window.

## Hostile values (`tests/integration/lived_state_sweep.py`)

Python's `json` accepts NaN and Infinity, so a file can carry them. A hand-written attack on a real checkpoint found
what the checks above missed: emotion scalars at NaN accepted into live state (`restore` clips, and `np.clip` passes NaN
through); a NaN `emotion.step` and any malformed generator state raising foreign exceptions, the generator ones during
apply, so a half-restored mind; a witness anchor of 1e30 accepted (finite, and still not a mind); non-numeric
`echo.weights` raising the wrong type; whole sections (`witness`, the DDM state) deletable with no complaint.

So the gate is a sweep rather than more field checks: every path in a real warmed snapshot (705 paths, ~7,750 variants),
each corrupted one at a time and sent through JSON. Before the fixes, 282 failures. After, 0: each variant is refused
with live state unchanged, or accepted with everything finite and the system still stepping.

The rules that came out of it: generator states are proven on a scratch generator at decode, so apply cannot fail on
them; `as_array` refuses a coordinate over `VECTOR_MAX_ABS` (1e3, a sanity wall: the field reached ~46 over 300 warm
steps at dim 64, the rest stay near unit scale; revisit if a wider field accumulates further); every section a live
component needs is required, not optional.

What the sweep still accepts, on purpose, and why that isn't a hole: in-range numbers of the wrong value, and removing a
real entry (a bond, a crystal, a ghost). Those are well-formed forgeries. Validation can't tell them from a lived file,
which is the signature question under Open. `emotion.arousal` and `valence` are ignored because they're derived.

## Interpretation
Restore is reconstitution of already-lived state into the objects production already built. Formation thresholds are live code: a retune must not refuse a bond that already formed. Planted bonds are caught by the trust-record check and well-formedness, not by re-applying the formation gate. Caps that can be retuned truncate to the live bound (deque semantics / weakest eviction) instead of refusing the mind.

A refused checkpoint is an identity, not trash. The bridge quarantines it (`*.refused-<timestamp>`) and exits; it does not start a newborn that would overwrite the file on autosave. Session persistence does the same to `lived_state.json`, and a later boot that sees refused siblings without a current lived file refuses to resume ecology as if it were that mind.

Ghosts round-trip as a deque. Nothing reads them into crystals, attractors, or the field. They stay a known trace of refused attackers.

What this still does **not** restore, and what the mixed twin says about them:

| unrestored | measured effect on this twin |
|---|---|
| stream, vector space, lattice, topology | not isolated; candidates for the step-1 trust/emotion/attractor drift |
| field `_phase_history`, `_step` | dilation only (a documented sink); left |
| ethical flood log | wall-clock 60s window; a restart hours later would expire it anyway; left |
| witness snapshots, crystallization candidates, identity_trace | unread in production; left |

Exact equality of trust/bonds/emotion/attractors after restore is not claimed. Decisions, witness, field, and ghosts are.

## Threats / confounds
- Runs: gate at 60 checks. Fail-before for the overwrite hole: unfixed `load_checkpoint` raise → catch → `save_checkpoint` on the same path replaced the bytes.
- dim 64, 48 mixed warm steps, one forced DDM bond, 3 sacred refusals (ghosts n=3, crystals n=5, attractors n=8).
- Twin steps A then B with numpy/python/torch/DDM/dreamer/chorus RNG cloned per step. Without that clone the twins were drawing different noise and the decision row was meaningless.
- `rec_attn.eval()` in the test; production may leave attention in train mode (dropout).
- Hermes's draft was read with `git -C` and not merged.

## Open / next
- [x] Witness + ghosts. → DONE 2026-11-02, mixed twin witness cosine 0.99998
- [x] Mixed-source twin with varied decisions. → DONE, `allow_weakened` / `sacred_shield`, decisions hold 24/24
- [x] Field and emotion on the session-persistence path. → DONE, they ride in `lived`
- [x] Refused load must not destroy the file. → DONE, quarantine + exit
- [ ] Stream, vector space, lattice, topology — candidates for the remaining step-1 trust/emotion/attractor drift. Not restored: not shown to move the gate.
- [ ] Whether a checkpoint should be signed, or whether "who can write `lived_state.json`" is the whole trust boundary.
