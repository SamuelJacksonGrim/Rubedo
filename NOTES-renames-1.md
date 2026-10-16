# Renames batch 1

Branch `grok/renames-1`. Proof tool: `python -m tests.diagnostic.rename_digest` (400 steps, seed 42). About 7.6 minutes on CPU. Informational; not in `run_all_tests.sh`.

## Pre-rename digest (before any rename)

Recorded from the tool as committed in `98a5458`, code still on the old names. Commit `98a5458` also lists the tool in `docs/PROJECT_STRUCTURE.md`.

| Run | Digest |
|---|---|
| all_on_cg | `ce77a1ffbc921e80f965dfd179e8c3ad5ddf30702ad94b9406369c278023d508` |
| default | `628ef207f77028d387a6552c386d1be430c7d6725fea1448ee3195a53c646527` |
| combined | `5d53e7ad4fea50f3b426f326585672d90cacd72b46e948adf242ab5df88826f9` |

Coverage the bars required, and got: all-ON had dreams 125, witness 45, rupture 66, crystals 7, advisories 21186, demotions 9523, manipulation signals 53, corpus pretrain on. Default had dreams 202, witness phrases 63, self-dialogue 82, one dream-cycle, crystals 3, corpus pretrain on. Elapsed 455.3s.

## Post-rename digest

Same command, after `c1b92c7`, `7bf2428`, and `454e4ef`. Exit 0. Bars met. Bit-identical to the pre-rename digest.

| Run | Digest |
|---|---|
| all_on_cg | `ce77a1ffbc921e80f965dfd179e8c3ad5ddf30702ad94b9406369c278023d508` |
| default | `628ef207f77028d387a6552c386d1be430c7d6725fea1448ee3195a53c646527` |
| combined | `5d53e7ad4fea50f3b426f326585672d90cacd72b46e948adf242ab5df88826f9` |

Coverage unchanged: all-ON dreams 125, witness 45, rupture 66, rupture_read 66, advisories 21186, signals 53, crystals 7, attractors 14, demotions 9523, values 63, pretrained 1. Default dreams 202, witness 63, self-dialogue 82, dream_cycles 1, crystals 3, attractors 2, values 65, pretrained 1. Elapsed 453.2s.

## Suite

`run_all_tests.sh` via Git Bash, Windows Python 3.13 (the WSL `python3` has no torch). Exit 0. 27 passed, 0 failed, about 134s. That includes `tests.doc_accuracy.verify_docs` (19/19) and `tests.doc_accuracy.hardcoded_dim`.

## Files touched

### `coherence_flood` → `source_monopoly` (`c1b92c7`)

- `agents/manipulation_resistance.py` — detector string, `DETECTOR_NAMES`, `_detect_source_monopoly`, module comment. `canonical_detector()` appended at the end of the file so the `__init__` line of `hhi_critical` stayed 160.
- `agents/selfhood_governance.py` — rewrites `signal.detector` through `canonical_detector` before the signal is stored.
- `agents/dependency_monitor.py` — comment that named the detector.
- `loop/autonomous_cycle.py` — comment that named the detector.
- `README.md` — detector table and the attractor-formation step.
- `ARCHITECTURE.md` — dependency-monitor row.
- `docs/FLOW.md` — attractor-monopoly row.
- `docs/VALUE_PATH_MAP.md` — detector table.
- `docs/EXPERIMENTAL_LEVERS.md` — `hhi_critical` row and the severity-math shorthand.
- `docs/LEXICON.md` — item 13 and the detector table row, marked formerly.

`docs/findings/` had no `coherence_flood`. No `configs/*.yaml`, no `tools/`, no `api/`, no `tests/baselines/*.json`, and no test asserted the old string.

### `ThinnessVector.coherence_contribution` → `alignment_support` (`7bf2428`)

- `cognition/integrity_read.py` — the field, `support()`, `as_dict` key, `from_dict`, the constructor alias, and the comments that described the live field. `_COHERENCE_REF` and `_coherence_support` were not renamed. No line was inserted above `_THIN_TAU`, so the `integrity_read.py:39` citations stay true.
- `docs/LEXICON.md` — item 14 and the thinness row, marked formerly.

Not this field, left byte-for-byte: `agents/value_emergence.py` (the impact sum and its checkpoint key), `agents/selfhood_governance.py` (the CORE-promotion request), `README.md` line that cites the old `coherence_contribution ≥ 5.0` gate, `docs/VALUE_PATH_MAP.md`, `docs/EXPERIMENTAL_LEVERS.md` lever E, `docs/OPEN_METASTABILITY.md`, the value-trace finding, and the tests that read `value.coherence_contribution`.

### Dreamer "offline" → live inside the step (`454e4ef`)

- `agents/dreamer.py` — module docstring and class docstring. Text only.
- `docs/LEXICON.md` — item 4 and the `Dreamer` row, so they no longer claim the docstring still says offline.

`DreamCycle`, `DreamSession`, `tools/dream/run_dream.py`, and the other "offline" mentions are different mechanisms and were not edited.

## Aliases

1. **`canonical_detector()`** at the bottom of `agents/manipulation_resistance.py`. Maps `"coherence_flood"` to `"source_monopoly"`. `handle_manipulation_signals` calls it before the signal is appended to `_pending_signals`. A saved signal or an external caller can still carry the old label. Governance does not branch on the string; it branches on severity and `source_id`. `detect()` itself now emits `source_monopoly`, so on a live step the rewrite is a no-op. The digest's own map does the same translation, which is why the hash did not move.

2. **`ThinnessVector` read alias.** The constructor takes keyword `coherence_contribution` only when `alignment_support` is omitted. `from_dict` reads `"alignment_support"`, or else the old key. `as_dict` writes only `"alignment_support"`. No `float()` coercion: the stored number is the number passed, and the four-argument positional call is unchanged. Nothing in the repo reloads an advisory dict today. The alias is there because `as_dict` used to publish the old key, so a saved report or an external caller can still hold it. The alias is on the vector, not on `DemotionAdvisory`. A whole advisory blob would be read by passing its `"support"` dict through `ThinnessVector.from_dict`. `EmergentValue.coherence_contribution` is not accepted here and was not given an alias.

3. **Dreamer.** No alias. Comments only.

## What a plain search would have missed

- `COHERENCE_FLOOD` in comments and the prose name "flood" in the severity-math line were the same detector, not a second symbol. The ethical `flood_ceiling` check in `verify_docs` is unrelated.
- The string `coherence_contribution` is two fields. The value engine's impact sum is serialized under that key in checkpoints (`_value_to_dict` / `_dict_to_value`) and is what the old CORE gate meant. Renaming that key would break a saved value. It was left alone, including every test that reads `v.coherence_contribution` off a value.
- `_COHERENCE_REF = 5.0` is unused except comments (the dead marginal reference). `_coherence_support` is the method that computes the axis. Both contain "coherence" and both stayed.
- The digest taps keep the same signal objects `detect()` returned. `handle_manipulation_signals` then mutates `detector` on those objects, and the digest hashes them after that. The canon map covers both orders.
- No call site reads the thinness `as_dict` key. The read alias had to be added on the constructor and on `from_dict`; a search for readers would have found none and skipped it.
- `docs/findings/` never mentions `coherence_flood`. It does mention the value's `coherence_contribution`, in the value-trace notes, and that file was not edited.
- The Dreamer module still says the class runs on `stabilize`. That sentence was already there and is not the word "offline". `stabilize` does not call `Dreamer`; the dream band and `force_dream_flag` do. Left as it was, because this batch was the offline wording only.
- Local name `cc` inside `WitnessReaper.read` is the alignment number. A comment says so. The variable was not renamed.
- Git rewrites LF to CRLF when it touches a file. That is a warning, not a content change.
