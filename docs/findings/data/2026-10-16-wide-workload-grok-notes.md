# Wide workload — handoff

**Date:** 2026-10-15 · **Branch:** grok/wide-workload · **Corpus:** 1.4.0 · **By:** Grok (room, probe flag, smoke). Ember co-author on the commit.

The long cells were not run. Build and a few dozen steps only, then these commands.

## What was built

`tests/workloads.py`. A probe opts in with `--workload wide`. The default is `canonical`, which is the same `RESONANCE_FAMILY_SOURCES` object the gates already import. Nothing in `run_resonance_sim` or the standing gates was retargeted.

Wide is the corpus holdout (`training/corpus.py`, `rhythm_holdout.jsonl`), shaped as source id → list of token lists.

| | canonical | wide |
|---|---|---|
| sequences | 16 | 1,680 |
| distinct tokens | 46 | 808 |
| sources | 4, four phrases each | same four ids |
| weights | 0.40 / 0.25 / 0.20 / 0.15 | the same numbers |
| HHI | 0.285 | 0.285 |
| known to a pretrained generator | (not remeasured) | 1.000 |

Per source, in deal order: samuel 420, claude 421, gemini 420, grok 419.

**Holdout only, not mixed with train.** Holdout is 1,680 sequences and 808 distinct tokens, and every one of those tokens already occurs in train (0 unseen). Train would add 24 tokens and would replay sequences the encoder was pretrained on. That is not a wider room. The 46-word problem was the vocabulary ceiling; 808 is the ceiling this room moves.

**Same ids, same weights.** The corpus has no real provenance — the source field was removed in 1.2.0 because the labels were synthetic. The four ids are injection slots, not authors, so trust, bonds and HHI see the population the gates were calibrated on. A new weight mix would have made dependency risk the story. HHI stays 0.40² + 0.25² + 0.20² + 0.15² = 0.285.

**Split.** File order, stratified by rhythm. Within each rhythm, round-robin across the four ids, rotating which source receives the first record of that rhythm so the leftover row does not always land on samuel. No RNG. Building the room does not advance `random`, numpy or torch, including inside `substrate.determinism.deterministic`. Draws in the probes are still `random.Random(seed)`, the same private stream as before.

**Canonicalization.** All 808 holdout tokens survive unchanged: the pipeline's canonical form is the raw string, none become `<UNK>`, none are aliased. `peek_batch` on the all-ON stack after the probe's own 3-epoch pretrain (both probes, seed 42): **4,144/4,144 token occurrences known, 1,680/1,680 sequences known, 808/808 distinct symbols known.** Unknown tokens are not a factor in this room. The peek runs once, in eval, before the first cell's steps, and does not register anything.

The default pipeline classifies these ordinary words as GLYPH and halts there. That is the pipeline's current behavior for the corpus vocabulary, not something this room introduced, and the string is unchanged so the registry key matches. Filtering on class would have dropped the room. Not changed.

**Overlap with the canonical 46.** 45 of the 46 canonical tokens occur in the holdout. `feral` does not. This room is that vocabulary minus one word, plus 763 others — not a disjoint lexicon, and not the same 46 repeated.

**Witness phrases.** The witness kind still replaces 20% of steps with `WITNESS_PHRASES`, on whichever room is selected. Checked on the wide lists: 0.184 of 2,000 draws (seed 0). Kind A never does. About 175/1,680 holdout sequences are rhythm-labeled witness. They were left in. The selector is off on both probes, so that label is not applied; only the embeddings differ. Stripping them would shrink the vocabulary the cone question is about. The gate's contrast is still the 20% phrase swap plus `watcher.evaluate` on the witness arm.

## Flags that are not the measurement

- `value_fixes_probe --workload wide` refuses the canonical default `--out` (`data/value_fixes_probe.json`). A file with no workload stamp is treated as canonical, so a wide run cannot resume it and a canonical run cannot resume a wide file.
- `h0_probe --summary auto` on wide is refused. That name is the canonical npz.
- `h0_probe --forks` defaults to `field,anchor,desat`, which is what an existing invocation already ran. `none` is the plain trace only. `--repeat-hits 0` was already the way to skip repeated hits.

The pre-declared bars in `value_fixes_probe` were not moved. A wide run asks those questions. It is not a new gate and not a graduation.

## Smoke (not the measurement)

- `tests.integration.wide_workload` — partition of the holdout, HHI, cross-process digest under two `PYTHONHASHSEED`s, witness mix, canonical object still the original.
- `tests.integration.determinism_replay` — passed (replay, cross-process, production clock, flood, guard).
- `tests.doc_accuracy.verify_docs` — 19/19.
- `h0_probe time --steps 40 --seed 42` canonical and wide: bit-exact unperturbed fork OK. Wide printed distinct 808.
- `value_fixes_probe --arms REF --seeds 42 --steps 40 --kinds composition` canonical and wide: both finished. Composition checks fail at 40 steps on both; those bars are for 500. Nothing was written.

## Commands to run

From the worktree root. One process per arm so the JSON files are not written by two processes at once. Steps stay at the default 500 and the seeds stay `42,43,44`, or the probe will refuse to write. Both kinds (composition and witness) are the default; do not pass `--kinds` unless you mean to drop witness.

A build on this box was about 2.5 minutes (CPU torch). Each value arm is 12 builds: 3 seeds × a consumer-off/on pair × a bare/witness pair. The steps on top of that are the part that saturated at ~100 s per 1,000 in the H0 run. Four arms at once will share the CPU.

```
python -m tests.diagnostic.integrity.value_fixes_probe --arms REF --seeds 42,43,44 --workload wide --out data/value_fixes_wide_REF.json
python -m tests.diagnostic.integrity.value_fixes_probe --arms DF --seeds 42,43,44 --workload wide --out data/value_fixes_wide_DF.json
python -m tests.diagnostic.integrity.value_fixes_probe --arms DEF --seeds 42,43,44 --workload wide --out data/value_fixes_wide_DEF.json
python -m tests.diagnostic.integrity.value_fixes_probe --arms E --seeds 42,43,44 --workload wide --out data/value_fixes_wide_E.json
```

H0, one seed, 8,000 steps. The cone, whether values / crystals / attractors keep forming, and boredom are on the plain trace (expression MSD, `live` / `births`, `attractors`, `crystals`, `boredom`). The anchor fork is the check that expression still ignores the anchor. Field nudge, desaturation and repeated hits do not answer those, so they are off. The unperturbed verify still runs at each age; that is the bit-exact twin, not a second experiment. Ages and horizon match the published H0 run. Age 7,500 plus horizon 500 lands on step 8,000 and is kept.

```
python -m tests.diagnostic.metastability.h0_probe run --steps 8000 --seeds 42 --workload wide --ages 500,2000,5000,7500 --horizon 500 --forks anchor --repeat-hits 0 --scratch scratch/h0-wide --summary docs/findings/data/2026-10-15-h0-wide-summary.npz
```

`scratch/` is gitignored. The JSON and the npz are not. They are results, not part of this commit.
