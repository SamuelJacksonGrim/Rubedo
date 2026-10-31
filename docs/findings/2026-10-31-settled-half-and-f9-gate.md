# Which dials still move after step 260, and does the F9 gate still hold?

- **Date:** 2026-10-31
- **Substrate:** `build_engine(CONFIG)` with `dim` overridden per arm. `FIELD_DIM` stays 128. Pretrain off, dream channel not built. D and F on. Bond DDM on. Witness selector on and inert (no rhythm reader). Fragmentation grace's flag is on; `build_engine` does not attach the consumer that reads it, so grace did not act. Rupture off. CPU.
- **Probe:** `tests/diagnostic/widening/dial_census_probe.py` (the step-260 split) and `tests/diagnostic/widening/rhythm_band_probe.py` (the pins). Neither file edits a constant.
- **Status:** standing
- **Depends on:** `2026-10-31-dial-census-widths` (the seven unsplit reads, and the canonical settled energy), `2026-10-31-right-to-refuse-order` (the step-260 cut), `substrate/resonance_field.py` `DEFAULT_THRESHOLDS` (the July F9 constraint set). The July probe this gate is checked against is RFE-Core2 `tests/diagnostic/calibration/rhythm_band_equilibria_probe.py`, finding `2026-07-06-f9-rhythm-band-rescale`. That file is not in this repo.

## Question

Widening step 4. Of the seven decision reads the census could not split in time, which still move once the first 260 steps are cut out? And do today's pinned rhythm equilibria at dim 128 still sit inside the F9 gate the placement rule requires before any band may move?

## Pre-declared signatures

Written in the two probes before these arms. Not edited to fit the result.

**Split.** Same numeric rule as the census, on the late window only. A late read moves at width W when `abs(mean_W − mean_128) > span_128`, after rounding to 6 decimal places. Rates (pattern identity, witness crystal-clear, witness snapshot-clear) are `(count_end − count_at_cut) / 240`. Stocks (lattice edges and nodes, binding total and established, bonds, sacred promotions) are the increment `end − cut`, not the end stock. Metastability regime count is the end snapshot: the monitor window is 128 steps, so on a 500-step arm it sits inside the settled half. Youth-only means the late read does not move. Unresolved means the 128 late span swallows a gap that is still more than 20% of the 128 late level, and the late increment is not near 0. That asks for a longer arm. It is not a retune.

**Pins.** Placement is the F9 constraint set, not a search on occupancy. A pin forces one band and sets the boredom override threshold to 2, so boredom cannot rewrite the band into explore. Canonical workload, seeds 42–44, 400 steps. The equilibrium is mean field energy over steps 301–400. Drift is the mean of steps 351–400 minus the mean of steps 301–350. Absolute drift above 2% of the level means that window is not an equilibrium. The degraded pin forces every non-blocking decision to `ALLOW_WEAKENED` at the live `weakened_strength_factor` (0.40).

The dim-128 gate, seed-mean equilibrium, outside which the pin is the wrong instrument and nothing ships:

| Band | Gate |
|---|---|
| stabilize, full strength | 30–45 |
| stabilize, degraded | 8–20 |
| dream | 160–240 |
| reflect | 270–320 |
| explore | 280–330 |

Dim 64 is reported. It is not a fit point and it does not retune the defaults. If the gate fails, free-run occupancy arms do not run. There is no second placement.

- SUCCESS for the bands would have been a shipped set, then the occupancy signature on the fitting seeds and again on held-out seeds 45 and 46.
- FAILURE looks like: the dim-128 means outside that gate, or a drifted window, or a placement that cannot satisfy the F9 constraints together. Nothing ships.
- The rule does not say which failure it is when the means fall outside. "Wrong instrument" is the stop. It is not a verdict on why.

## Result

No constant changed. `DEFAULT_THRESHOLDS` is still 5 / 150 / 300. `decide()` wrote `placement.json` with `ship: false` and returned exit 2 at 11:02. Reason recorded there: dim-128 pinned equilibria are outside the F9 calibration gate. No free-run arm was started.

Data: `docs/findings/data/2026-10-31-youth-split/` (18 arms, `split-classification.json`) and `docs/findings/data/2026-10-31-rhythm-bands/` (75 pins, `placement.json`). A duplicate driver was refused at 10:58; the relaunch skipped every finished file and ran the 14 pins that were not yet complete. Both batches exited 0.

### Youth split

18 arms. Canonical and wide, widths 128 / 256 / 768, seeds 42 / 43 / 44, 500 steps, counters at step 260. Class is the late read.

| Late read | Canonical 256 | Canonical 768 | Wide 256 | Wide 768 |
|---|---|---|---|---|
| Pattern identity, cutoff 0.7 | youth-only (1, 1, 1) | rule flags; 235/240, 240, 240 | youth-only | rule flags; 232/240, 237, 240 |
| Witness crystal-clear | **moves** 135/240, 171, 192 | **moves** 20/240, 114, 52 | **moves** 84/240, 109, 156 | **moves** 1/240, 22, 19 |
| Witness snapshot-clear | youth-only (240/240) | rule flags; 233/240, 240, 240 | youth-only | rule flags; 232/240, 234, 240 |
| Lattice edges, increment | youth-only (2880, 2880, 2880) | youth-only (2880) | youth-only (2880) | **moves** 2746, 2794, 2852 |
| Lattice nodes, increment | 240, 240, 240 | 240 | 240 | 240 |
| Binding total, increment | 0, 0, 0 | rule flags; 1, 0, 0 | 0 | **moves** 9, 5, 0 |
| Binding established, increment | 0 | 1, 0, 0 | 0 | **moves** 1, 1, 1 |
| Bonds, increment | **moves** 0, 0, 0 → 1, 2, 1 | **moves** → 1, 1, 1 | unresolved (4, 2, 2 → 1, 1, 1; span 2) | unresolved (same) |
| Sacred promotions, increment | **moves** 2, 2, 2 → 1, 2, 1 | **moves** → 0, 0, 0 | 0, 0, 0 | 0 |
| Expression regimes, end window | **moves** 2, 1, 1 → 15, 15, 15 | **moves** → 16, 16, 16 | **moves** 6, 2, 3 → 14, 13, 19 | youth-only (2, 2, 8; span 4) |
| Generator regimes, end window | **moves** 6, 3, 6 → 16, 16, 16 | **moves** → 16 | unresolved (15, 10, 13 → 2, 7, 14; span 5) | **moves** → 2, 2, 8 |

128 late crystal-clear is 240/240 on canonical and 199/240, 231, 233 on wide. 128 late snapshot-clear is 240/240 on both. Where the table says the rule flags a rate, the late span at 128 is 0, so any miss moves. The misses are a handful of steps on one or two seeds. That is the census's span-0 dust, not a cutoff to retune. Binding's canonical 768 flag is one late concept on seed 42.

Lattice nodes add one per step at every width. Nothing to retune.

Canonical lattice edges add 2880 in the late half at every width. The census full-run drop (about 5800 → 5500 → 5330) is entirely before step 260. Wide 768 keeps a settled remainder: 134, 86 and 28 fewer late edges than 2880.

Canonical binding's census jump (established concepts 1/4/2 → 13/14/13 → 17/16/17) is already present at the cut. The settled half adds nothing at 128 or 256, and one concept on one seed at 768. Wide 768 adds a late trickle (9, 5, 0 new; one of them established on each seed), not the full-run explosion.

Canonical bonds: the late half forms none at 128 and one or two at width. The census end-count drop (4 → 1) is the youth bonds 128 keeps. Width's bond is the late one. Wide's late drop (4/2/2 → 1) is smaller than the 128 span, so the rule does not call it a move, and the gap is large enough that the rule calls it unresolved.

Sacred promotions on canonical happen after step 260: two at 128, one or two at 256, none at 768. Wide promotes none in the late half at any width (it already promoted none in the census at 128).

Expression regimes at canonical 128 end locked or cycling (2, 1, 1). At 256 and 768 the settled window is 15 or 16 regimes, states structureless, metastable, or dissolving. That is not the opening. Wide expression moves at 256 and does not at 768 (the 128 span covers 2/2/8 against 6/2/3). Generator regimes go to 16 on canonical at both widths. Wide's 256 generator read is unresolved; at 768 it falls to 2, 2, 8.

### Pinned equilibria

Seed-mean field energy, steps 301–400. Drift in parentheses is the count of seeds whose window failed the 2% cut. Boredom overrides were 0 on all 75 pins.

| Dim | Stabilize | Degraded | Dream | Reflect | Explore |
|---|---|---|---|---|---|
| 64 | 98.7 (3/3) | 80.0 (1/3) | 312.6 (3/3) | 246.4 (3/3) | 282.8 (3/3) |
| 128 | **65.3** (1/3) | **69.1** (1/3) | **273.4** (2/3) | **252.2** (3/3) | 292.1 (3/3) |
| 256 | 25.0 (2/3) | 31.1 (2/3) | 178.4 (3/3) | 257.4 (3/3) | 304.2 (3/3) |
| 512 | 20.7 (1/3) | 26.9 (3/3) | 175.7 (3/3) | 261.0 (3/3) | 310.4 (3/3) |
| 768 | 21.8 (2/3) | 28.4 (3/3) | 175.9 (3/3) | 261.2 (3/3) | 312.9 (3/3) |

Dim 128 per seed, the only row the gate judges:

| Band | Seeds 42 / 43 / 44 | Mean | Gate | Drift |
|---|---|---|---|---|
| Stabilize | 67.3 / 65.4 / 63.2 | 65.3 | 30–45 | +0.7 / +1.5 / +0.8. Seed 43 is 2.3%, just over the cut. The other two are flat. |
| Degraded | 71.6 / 70.2 / 65.6 | 69.1 | 8–20 | +0.8 / +1.7 / +0.4. Same shape, just over on seed 43. |
| Dream | 232.1 / 272.5 / 315.6 | 273.4 | 160–240 | +9.2 / +0.3 / +17.9. Seed 42's mean is inside the gate and still rising. The three seeds do not share a level. |
| Reflect | 250.9 / 253.2 / 252.4 | 252.2 | 270–320 | +9.6 / +10.0 / +9.7, about 3.8% on every seed. Tight. The second 50 steps sit about 10 above the first 50. p90 is 258–261, still under 270. |
| Explore | 291.8 / 292.9 / 291.8 | 292.1 | 280–330 | +11.4 / +12.0 / +11.3, about 3.9%. The mean is inside the gate. The window is not a basin. |

`decide()` stops on the first failed check. The means failed. The drift check did not get to be the reason. It would have failed too: reflect and explore on every seed, dream on two.

Degraded did not open a lower basin. At dim 128 and every wider dim its mean sits about 4 to 7 above the full-strength stabilize pin. On every degraded pin from dim 128 up, all three seeds, the unforced decision was already `ALLOW_WEAKENED` on 384 of 400 steps, 0 were blocking, and the wrapper forced all 400. At dim 64 that already-weakened count is 23 / 226 / 384, and the degraded mean (80) is below stabilize (99), still far above 8–20. Dim 64's stabilize window is not a plateau: seeds 117.5 / 107.8 / 70.8, drift on every seed.

July's published pinned table, one seed, dim 128 then dim 64: stabilize 37.3 / 34.8, dream 197.7 / 209.1, reflect 294.5 / 292.0, explore 301.1 / 294.9. The ~13 degraded figure is not a row that probe printed.

The census free-run settled energy at canonical 128 was 282 / 287 / 290. Those late reflect counts (189 / 178 / 158) are the same numbers as the late boredom overrides, so the behavior that ran was explore. This probe's explore pin, boredom forced off, sits at 292 / 293 / 292. The reflect pin, also boredom off, sits at 251 / 253 / 252. The census energy is the explore pin. It is not a measurement of reflect's own basin.

Widths above 128 were not judged. The table is what the pins did. Placement did not run.

## Interpretation

Two results, kept apart.

The split reorders the census list. Leave the 0.7 pattern cutoff, the snapshot coherence gate, canonical lattice edges, and the binding cosine. Their 500-step moves do not survive the cut, except the dust and the one-seed trickle named above. Wide lattice at 768 still loses some late edges. It is a remainder, not the census drop.

What still moves on a settled field:

1. Witness crystallization clear-rate, both workloads, both widths. The snapshot gate does not. Do not retune 0.92 / 0.90 / 0.75 off a 500-step mean, and do not retune them in front of the bands. The split says the settled half is where they fail.
2. Sacred promotions on canonical. The settled half promotes two values at 128 and none at 768.
3. Metastability regime count on canonical, expression and generator, both widths. The settled window leaves locked/cycling. Wide does not tell the same story at 768.
4. Bond timing on canonical. Not a settled refusal. 128 forms its bonds before the cut; width forms one after it.

The bands did not ship. The dim-128 pin is outside the gate on four of five bands, and the miss is not a scale factor. July had degraded far below full-strength stabilize, then dream, then reflect and explore a few points apart. This pin has degraded beside stabilize, dream's three seeds scattered from 232 to 316, and reflect about 40 below explore.

The data cannot say whether July's table is stale on today's stack or this pin is a different instrument. Both would put these means outside that gate. What the data does decide:

- It is not a width quirk inside this harness. Dim 64 is not near July's 35 either, and it does not agree with dim 128. July reported the two dims agreeing. This run does not reproduce that agreement. It also does not show what July's probe would print on this tree.
- It is not "the field is still climbing into the old stabilize band." Stabilize and degraded at dim 128 are plateaus, 20 and 50 points above the top of their gates.
- It is not "reflect would have entered 270–320 if the window were a little longer" as a fact. The second 50 steps sit about 10 above the first 50, and p90 is still under 261. The probe's own rule says this is not an equilibrium. A longer pin might keep climbing. This file does not show that.
- Witness-as-stance and fragmentation grace cannot be the cause of these pins. They did not run. D and F did run. So did bond DDM, the canonical workload, and a generator with pretrain off. None of those was toggled. The data does not attribute the miss to any one of them.

The harness difference is real, and it is code, not a number from these files. July's probe builds a generator, pretrains it for 8 epochs, and pins by rewriting the thresholds to 0 or 1e9. Boredom stays at 0.50, so a bored step can still run explore's behavior. Its workload is four 3-token sources, RNG 1188, seed 42. It has no degraded pin. The ~13 in the constraint set is the free-run stall under a candidate threshold of 15, described as the weakened-injection equilibrium. This probe uses `build_engine` with pretrain off, pins by replacing `current_rhythm`, forces boredom off, runs the canonical workload on three seeds, and adds an `arbitrate` wrapper for the degraded band. The energy is the same quantity (field L2 norm) and the window is the same (last 100 of 400). The stack around it is not.

## Threats

- Three seeds. Dream at dim 128 already disagrees with itself by 80 energy. A mean outside the gate is solid. A mean inside a band would not have been.
- The 2% drift cut fails on most bands. Treating 252 or 273 as a basin would violate the probe's own rule. The gate refusal does not need them to be basins. The levels are elsewhere.
- 384/400 already weakened, identical across seeds and across every dim from 128 up, is too exact to be three fields happening to match. These files do not record which steps. Do not invent a warmup length from the count.
- The relaunch did not rewrite a finished pin. A pin file counts as finished only when it parses and says `steps == 400`.
- Pretrain off is the census condition and July's opposite. The census finding already says a pretrained generator can move settled energy. That is one of the harness differences, not a third result.
- Span 0 still promotes a few missed steps to "moves." Named above. Not retunes.
- Wide bonds, and wide generator regimes at 256, are unresolved on purpose. A 1200-step arm is the rule's next measurement. It is not required to refuse the band ship. The bands never reached occupancy.

## Open

- [ ] Separate the two explanations before any band moves. Run July's probe file, unchanged, on this tree (it lives in RFE-Core2, not here): 8-epoch pretrain, threshold pin, its four sources, seed 42, dims 64 and 128. If it reprints ~37 / ~198 / ~294 / ~301, this pin is the different instrument and these files do not place bands. If it reprints this pin's dim-128 levels, July's table is stale on this stack. If only some bands match, say which. Either way the drift cut still applies: reflect, dream, and explore were not basins in 400 steps on this pin.
- [ ] The degraded gate is a further question even after that. July's probe never pinned `ALLOW_WEAKENED`. The ~13 is the 15-trap stall. A 0.4× stabilize pin inside that same July harness is what would show whether weakened injection still sinks the field, or whether [8, 20] is guarding a different quantity. This wrapper already shows that forcing 0.4× on this harness does not.
- [ ] Witness crystallization, canonical sacred promotions, and the canonical regime count are settled moves. They wait behind the band question. No constant in this commit.
- [ ] Wide bonds, and wide generator regimes at 256: longer arm, same cut, if those two are going to be classified. Not this commit.
