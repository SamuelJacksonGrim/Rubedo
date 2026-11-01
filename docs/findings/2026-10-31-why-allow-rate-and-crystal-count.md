# Why the allow rate reads higher here than on live, and why the crystal store stays small

- **Date:** 2026-10-31
- **Substrate:** live code paths, reconstructed. Resonance Family, internal origin, the smoke's strict `allow_rate` (`health_summary`: ALLOW / decisions). CPU, CUDA hidden, 2 threads. Corpus for the pretrain arms is Rubedo's `data/corpus` 1.4.0 (8 epochs on `prod_pretrain`, the CONFIG default). Live RFE-Core2 was read, not run (`c3c5403`; the fork's engine parent is `6f8ea42`).
- **Probe:** `tests/diagnostic/why_allow_crystals_probe.py`
- **Status:** standing
- **Depends on:** `2026-10-15-dream-consolidation-closed` (the 1–4 side observation), `2026-10-15-why-values-weaken-under-witness` (systemic `identity_erosion` is what ALLOW_WEAKENED is)

## Question

BACKLOG §4 says Rubedo main's allow rate runs higher than live, 0.73–0.76 against 0.57–0.60, and asks which difference moves it: a graduated default, a lever on here and off there, the workload, or the measurement. BACKLOG §0 (and the dream-consolidation side observation) says the crystal store holds 1–4 crystals over 500 steps against a cap of 512, and asks whether formation is starved, decay or merge eats them, or this is a young system the way fragmentation was.

## Pre-declared signatures

Written in the probe before the first run. Not edited after the data.

- ALLOW, a lever is the gap: turning the post-fork flags back to live's values (D, F, fragmentation grace, witness, the vibration gauge) moves strict allow_rate from the cited 0.73–0.76 into the cited 0.57–0.60, and the other boots do not.
- ALLOW, the gap is the measurement: those two bands show up under two different boots, and the flag pair does not move the rate.
- ALLOW, confounded: every boot lands in one band, or the seed spread is wider than the gap.
- CRYSTALS, starved: offers that clear coherence 0.75, pressure 0.60 and long relation 0.80 stay rare.
- CRYSTALS, merge: many offers clear all three and almost all reinforce an existing crystal (cosine ≥ 0.92), so the store stays in the single digits.
- CRYSTALS, decay: formations are numerous and `decay_step` removes them back to 1–4 inside 500 steps.
- CRYSTALS, youth: the store is 1–4 at step 500 and still growing at 1,500–3,000.
- CRYSTALS, confounded: two boots disagree on which of those it is.

Phase 1 was the smoke harness, the speech-bridge body (with and without the live 5-rhythm checkpoint, train and eval), and `build_engine` with pretrain off (flags on, flags off, and train mode). The cold production body came back seed-bimodal, not a tight 0.73–0.76, and the flag pair did not move it. A second round was named before it ran, criteria unchanged: the composition-gate body (vocab 4096, dim 128, depth 3) in eval and in train, and `build_engine` with the 8-epoch pretrain `main()` actually runs, flags on and flags off. `wake_p50` was added with that round. Phase-1 rows have no waking medians.

## Result (observed)

Seeds 42, 43, 44. Strict allow_rate. Injection rate (ALLOW + ALLOW_WEAKENED + MONITOR) is 1.000 on every row. Quarantine is 0 on every row. Raw rows are under `docs/findings/data/2026-10-31-why-*.jsonl`.

The backlog line (`a35d214`, 2026-10-15) cites the two bands and names no probe, no seed, and no boot. It predates D+F's graduation, fragmentation grace, witness activation, and the vibration gauge, so those cannot be the cause of the numbers as written. Live was not started. Its `build_engine` also pretrains 8 epochs and calls `generator.eval()`, and it has none of the five post-fork flags. Its speech bridge (`tools/voice/repl_qwen.py`) is a different entry: `build_full_stack(vocab_size=8192, dim=128, depth=4, heads=4)`, the 5-rhythm checkpoint, left in train mode, no `eval()`, novelty attenuation only under `--free`. Rubedo's `build_full_stack` now defaults the observe-only vibration gauge on; live's does not. That is the one construction difference in the bridge arms.

### Allow rate, 500 steps

`prod_fork` matches `prod_cold` on every counter this probe records, including the passer-cosine sum. `prod_pretrain_fork` matches `prod_pretrain` the same way. The flag rows are not a failed apply: seed 42 of `prod_pretrain` has like-for-like, damp-pays-full, six-rhythm, and vibration true, and the rhythm reader attached; the fork twin has all five false and no reader.

| arm | boot | 42 | 43 | 44 | dream share |
|---|---|---:|---:|---:|---|
| harness64 | dim 64, depth 3, vocab 4096, train | 0.528 | 0.528 | 0.648 | 0.49 / 0.48 / 0.39 |
| bridge | 8192 / 128 / 4, train, no checkpoint | 0.544 | 0.534 | 0.524 | 0.47 / 0.48 / 0.48 |
| bridge_ckpt | that body + the live 5-rhythm weights, train | 0.550 | 0.506 | 0.694 | 0.47 / 0.51 / 0.41 |
| bridge_ckpt_eval | those weights, eval | 0.546 | 0.548 | 0.708 | 0.47 / 0.48 / 0.40 |
| bridge_eval | random init, eval | 0.708 | 0.994 | 0.976 | 0.33 / 0.19 / 0.19 |
| prod_cold | `build_engine`, pretrain off, flags on, eval | 0.708 | 0.994 | 0.976 | 0.33 / 0.19 / 0.19 |
| prod_cold_train | same body, `train()` | 0.542 | 0.532 | 0.522 | 0.47 / 0.48 / 0.48 |
| shaped | composition body, 4096 / 128 / 3, eval, no pretrain | 0.794 | 0.882 | 0.594 | 0.30 / 0.24 / 0.42 |
| shaped_train | that body, train | 0.540 | 0.524 | 0.514 | 0.47 / 0.49 / 0.49 |
| prod_pretrain | `build_engine` as `main()` builds it, 8-epoch pretrain, eval, flags on | 0.550 | 0.602 | 0.560 | 0.46 / 0.44 / 0.45 |

`bridge_eval` and `prod_cold` are the same three rates. Against a bare `build_full_stack` of the same shape, `build_engine` also loads the YAML, turns the bond-formation accumulator on, and carries D, F, the selector, and the gauge. None of that moves this number.

Fragmentation grace is the one flag that was not really exercised. `build_engine` does not attach the reaper, and `apply_value_levers` writes the flag only when a reaper is already there. On this boot grace is off in both arms, because there is nothing to attach it to. D, F, the six-rhythm selector, the rhythm reader, and the gauge were actually on in one arm and off in the other.

Every ALLOW_WEAKENED in these runs was systemic `identity_erosion`. Almost all of it is moderate. The exception is harness64 seed 42: 4 high and 232 moderate. A few decisions are MONITOR rather than either, so "every non-ALLOW is erosion" is false: seed 44 carries 2 MONITORs on most arms, and `bridge_eval` / `prod_cold` seed 44 carry 3.

The 500-step window is the opening. The same runs at 3,000 steps, weakened counts unchanged from the first 500:

| arm | allow at 3,000 (42 / 43 / 44) | weakened decisions | dream steps |
|---|---|---|---|
| prod_cold | 0.951 / 0.999 / 0.996 | 146 / 3 / 9 | 167 / 94 / 95, equal to the 500-step dream counts |
| shaped_train | 0.923 / 0.921 / 0.919 | 230 / 238 / 241 | 237 / 244 / 247, equal to the 500-step dream counts |
| prod_pretrain | 0.925 / 0.934 / 0.927 | 225 / 199 / 218, equal to the 500-step counts | 231 / 219 / 227, equal to the 500-step dream counts |

### Crystals

Decay removed 0 crystals on every arm and every snap, including 3,000 steps. Nothing was evicted. Cap 512 was never close. Dream offers formed 0 crystals on every arm (the dreamer still offers `long_relation` 0.5; that hole is the 2026-10-15 finding, and it is not what sizes the store).

Waking medians on `prod_pretrain` at 500 steps sit above the gates. Seed 42: coherence 0.909, pressure 0.762, long relation 0.916. Seeds 43 and 44: coherence 0.893 / 0.894, pressure 0.723 / 0.727, long relation 0.905 / 0.912. The mixed median is not this number. Dream's hard-coded 0.5 pulls it down. Do not read `score_p50` as the waking relation.

What the store did on the boots that match the 1–4 quote, 500 steps. "Passers" are offers that cleared all three gates while the store was already non-empty, so the first crystal is a formation and not a passer. Mean cosine is the passer-cosine sum over passers.

| arm | crystals (42 / 43 / 44) | formed | merged | passers with cosine ≥ 0.92 | waking rejects, seed 42 (coherence / stability / relation) |
|---|---|---|---|---|---|
| prod_pretrain | 2 / 2 / 3 | 2 / 2 / 3 | 264 / 275 / 277 | 264 / 275 / 277 of 265 / 276 / 279 | 55 / 172 / 7 |
| prod_pretrain mean cosine | 0.944 / 0.975 / 0.971 | | | | |
| bridge_ckpt | 1 / 2 / 1 | same as the count | 208 / 234 / 238 | 208 / 234 / 238 of 208 / 235 / 238 | 131 / 107 / 53 |
| shaped_train | 1 / 1 / 1 | 1 / 1 / 1 | 256 / 250 / 220 | all of those passers | 57 / 185 / 1 |
| harness64 | 1 / 2 / 16 | same as the count | 238 / 252 / 307 | 238 / 252 / 307 of 238 / 253 / 322 | 111 / 137 / 13 |

Seed 42 of `prod_pretrain`: 265 waking passers, 264 at cosine ≥ 0.92 and merged, 2 formed. The second crystal is the one passer outside the ball. Seeds 43 and 44 are the same shape (one or two crystals outside the ball, the rest merged).

The cold eval body is a wider cone, and it also stops. `prod_cold` at 500 steps: 12 / 15 / 13 crystals, merged 386 / 450 / 453. `shaped` eval: 12 / 15 / 10. Snaps, crystals / formed / merged:

`prod_pretrain` through 3,000. Seed 42 is 0 at step 100 and 2 from step 250 on (merged 14 → 264 at step 500 → 2,764). Seed 43 is 1 at step 100 and 2 from step 250 on (merged 1 → 275 → 2,775). Seed 44 is 1 at step 100 and 3 from step 250 on (merged 5 → 277 → 2,777). Decay 0 at every snap. From step 500 to step 3,000, merged rises by exactly 2,500 on each seed and formed, the waking rejects, the dream count, and the weakened count do not change. Every step after 500 is a waking merge and a clean ALLOW.

`prod_cold` through 3,000: seed 42 is 10 at step 100 and 12 from step 250 on (merged 34 → 2,886). Seed 43 is 15 from step 100 on (merged 50 → 2,950). Seed 44 is 12 at step 100 and 13 from step 250 on (merged 54 → 2,953).

`shaped_train` through 3,000: one crystal on every seed from the step it appears (250, 250, and 500) through step 3,000. Merged at 3,000: 2,756 / 2,750 / 2,720. The long stretch of clean ALLOWs does not grow the store.

Stability is the main waking reject on the pretrained main. Relation rarely blocks a waking step (7, 8, and 4 on the three seeds). A large minority still fails a gate. The store is small because the ones that pass collapse, not because passing is rare: about 270 of 500 waking steps clear all three gates and then land in 2 or 3 crystals.

## Interpretation

The allow-rate question, as posed, is the wrong question. It asks which post-fork graduation opened a gap of 0.73–0.76 against 0.57–0.60. Measured the same way, on the same workload, with the same counter, there is no such gap.

Rubedo's `main()` boot — `build_engine`, 8-epoch pretrain, eval, the graduated flags on — is 0.550 / 0.602 / 0.560. That is the cited live band. Turning every post-fork flag off, and not attaching the rhythm reader, changes no recorded counter. Grace is the exception that was not a real off: this boot never attaches the reaper, so the flag has nothing to land on either way. D, F, the selector, the reader, and the gauge did land, and they still changed nothing. Witness does not show up on this workload, which is the standing result, and the attached reader is not a hidden difference either. The live speech bridge, reconstructed here with the checkpoint and left in train mode, is 0.550 / 0.506 / 0.694. The center of that is the cited live band. The three-seed spread is wider than the citation.

The 0.73–0.76 figure is not this boot. The nearest thing to it is the mean of the cold composition body in eval (0.794 / 0.882 / 0.594, mean 0.757), and one seed of the cold production boot (0.708) whose other two seeds are 0.994 and 0.976. The pre-declared confound fires on that boot: the seed spread is wider than the gap the backlog quoted. Quoting 0.73–0.76 as Rubedo main's rate is a cold-eval number, and not a stable one, set next to a bridge number.

What actually moves the rate, on this workload:

- Eval versus train, on a random-init body. Train stays near 0.52–0.54 with dream share near half the steps, and those dream-band steps are the ones `identity_erosion` weakens. Eval drops the dream share and the rate jumps, on a seed-by-seed basis, to 0.71 or to about 0.98. `prod_cold` and `bridge_eval` are the same jump. The 5-rhythm checkpoint does not make that jump: eval barely moves it (0.546 / 0.548 / 0.708 against 0.550 / 0.506 / 0.694).
- The 8-epoch pretrain moves today's main the other way. It puts the dream share back near 0.45 and the allow rate back into 0.55–0.60. Pretrain lowers this number. It does not produce the high band.
- The window. By step 3,000 the same stacks read about 0.92–0.99, because every weakening in the run happened in the first 500 steps and the rest are clean ALLOWs. The cited bands are opening-window numbers.

No constant was wrong. Nothing was changed.

How far this reaches (sharpened after an outside review by Copilot): it **falsifies** the backlog's attribution to
post-fork flags, for the flags tested, on this workload. It does not recover where the quoted 0.73–0.76 came from.
The backlog line names no commit, harness, seed, boot, window or counter, so that number is **unreproducible**, and
"a cold-eval boot" is the best available explanation, not an identified cause. Other post-parent code differences
weren't tested, counter equality isn't state equality, and three seeds are too few to characterize the bimodal arms
(the 0.757 mean of a 0.794 / 0.882 / 0.594 arm is a summary of three points, not a band).

The crystal question is the right question. The signature that fired is merge, on every boot, and the boots do not disagree about the mechanism. They disagree about how many directions the cone has.

On the pretrained main, a median waking step already clears all three gates, and about 270 of 500 waking offers do. All but one or two of those passers sit at cosine ≥ 0.92 of a crystal that already exists (mean passer cosine 0.944 / 0.975 / 0.971) and merge. The store at step 500 is 2, 2, and 3, which is the 1–4 the October 15 side observation recorded on `build_all_on` (that stack also pretrains, then evals; this probe did not re-run the reaper or the 3-epoch ignition, and the reaper does not touch the crystal store). Decay removed nothing. It could not have: usage starts at 1.0, a crystal stays until usage falls below 0.01, the rate is 0.9995, and `decay_step` runs every 100 steps. Thirty calls in 3,000 steps leave usage at 0.985. Reaching 0.01 would take about 9,200 decay calls, on the order of 900,000 steps, and only if the crystal is never merged — a merge adds 1.0 back to usage.

It is not youth under continued exposure to this workload (a broader or changing input stream could still form new
crystals later; whether merge chaining compresses a richer offer set is the open question below). Fragmentation's story does not transfer. On the pretrained main the count is 2, 2, and 3 from step 250 through step 3,000. Formed stays at that count. From step 500 on, every step is a merge into one of those crystals and a clean ALLOW. The cold eval cone is wider (12–15) and just as finished: flat from step 100 or 250 through step 3,000 while merges keep arriving. The train-mode composition body forms exactly one crystal and is still one at step 3,000, including across 2,500 steps that are clean ALLOWs. The store is not waiting to grow. The expression cone is inside the merge ball of the first crystals, and how many crystals that is depends on the weights (1–3 with pretrain, train mode, or the 5-rhythm checkpoint; about 12–15 on a random-init body in eval). Seed 44 of the dim-64 harness is the outlier, 16 crystals, and it is also the allow-rate outlier on that arm.

## Threats / confounds

- Runs: 3 seeds on every rate that is compared, including the 3,000-step main boot.
- Live's process was not run. The bridge was reconstructed inside Rubedo and pointed at live's checkpoint files, read-only. Live's commits after `6f8ea42` are the encoder's position balance (off by default), corpus and emotion-checkpoint work, and docs, not these arbitration flags. A live `main()` could still differ if its corpus bytes differ from Rubedo's 1.4.0. That was not diffed. It is not needed to explain the cited gap, because Rubedo's own main already lands in the cited live band.
- `main()`'s waking self-dialogue (`dream_channel_p` 0.20, `source_dream`) is not in this probe. It is on in both repos' `main()` and off in the bridge, so it is not a fork difference. A Qwen conversation was not run either. If the cited 0.57–0.60 was a talk rather than this workload, the bridge arm still lands on that band without one.
- The workload is the 46-token Resonance Family. It is the smoke's workload, not a wide corpus and not a conversation.
- Identity of the flag pairs is equality of this probe's counters, not a byte digest of the field.
- Rubedo's bridge arms carry the vibration gauge. Live's `build_full_stack` does not. The gauge is observe-only, and the production on/off pair matched every counter. The bridge was not re-run with the gauge stripped.
- Grace was not bisected in operation. See above. A stack that attaches the reaper could still be different; this workload's production boot is not that stack.
- harness64 seed 44 (allow 0.648, 16 crystals, dream share 0.39) is a real seed, not a dropped run. The dim-64 harness is not a tight band.

## Open / next

- [ ] `main()`'s p=0.20 dream channel, if the number wanted is the one `main()` prints rather than the smoke workload. Not a fork difference.
- [ ] Why a pretrained cone has 2–3 directions and a cold eval cone has about 12–15. That is the next crystal question. It is not a gate, and 0.92 was not touched.
- [x] Which post-fork default moves allow_rate. None of them. → this file.
- [x] Starved, decayed, or young. None of those. Merged. → this file.
