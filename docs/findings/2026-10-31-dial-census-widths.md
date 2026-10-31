# Which dials move from field width 128 to 256 and 768

- **Date:** 2026-10-31
- **Substrate:** `build_engine(CONFIG)` with `dim` overridden per arm. `FIELD_DIM` stays 128. Pretrain off, dream channel not built, witness selector on and inert (no rhythm reader). D and F on. Rupture off. CPU.
- **Probe:** `tests/diagnostic/widening/dial_census_probe.py`
- **Status:** standing
- **Depends on:** `docs/WIDENING_PLAN.md` step 3, the dial census in `docs/EXPERIMENTAL_LEVERS.md`, `2026-10-31-right-to-refuse-order` (the youth window), `2026-10-31-vibration-gauge-baseline` (the trailing-256 read)

## Question

Widening plan step 3: before any constant changes, which dials actually move between field width 128, 256 and 768 on the same seeded workloads?

## Pre-declared rule

Written before any arm ran (it is the probe's docstring):

A numeric read moves at width W when `abs(mean_W − mean_128) > span_128`, mean and span (max − min) taken across the seeds of that workload, after rounding each seed's read to 6 decimal places. A span of 0 means any remaining difference moves. A read that is null on every seed is untested, not invariant. Fewer than 2 finite seeds is insufficient, not a retune.

A dial **needs retuning** at W when one of its decision reads moves (a gate-clear fraction, a fire count, an occupancy, a label). A dial is **shifted** when only a level read moves. Shifted is not width-invariant. It is a lower-priority look, not a new constant by itself. The field's internal-coherence pin is reported and never listed for retune.

Census marks are hypotheses. This rule decides, including a dial the census marked "no" if this workload reads it.

The step-260 cut below was **not** part of that rule. It is a follow-up from `2026-10-31-right-to-refuse-order`: on canonical, systemic `identity_erosion` keeps a damp (≥ 0.30) queued from boot to ~step 260, so a 500-step arm is half youth. The cut asks whether a move lives only in that window. It does not reclassify the 500-step rule. It changes the order in which a later retune should touch the constants.

## Control

18 arms. Canonical Resonance Family and the corpus-holdout wide workload, `origin_type` internal, seeds 42/43/44, 500 steps, widths 128/256/768. Data: `docs/findings/data/2026-10-31-dial-census/`. Machine reduce (`--reduce`): `classification.json.gz`.

Not on this workload, so neither invariant nor a retune: Qwen/Nomic beat-lock floors, encoder training temperatures and cosine margins, rupture's gaussian scale (rupture is off), the dream-channel decoder width, the voice REPL speak-gate.

Arms ran on `6b24f97`, before the vibration gauge was in the step and before `arbitrate()` yielded to a failed hard gate. The gauge is observe-only. These arms never fail a hard gate (`delta_below_hard` is 0.0 on all 18, quarantine 0, reject 0), which is the condition under which that reorder is byte-identical. They were not re-run after the rebase.

Vibration numbers in the arm files were computed by the probe's copy of `analyze()` from `5349028`. Canonical seed 42 matches `2026-10-31-vibration-gauge-baseline` to the published digits (trailing 256: white, sf 0.824, cone 4.6°, MSD lag-1 0.013; full window: unknown, sf 0.200, cone 14.5°, a period-3 that does not hold). The probe now calls `cognition.stream_vibration.analyze`. Floors were not retuned. The move test is the trailing 256, which is the settled window. The full window still holds the opening walk and is reported, not classified.

## What the 500-step rule says

Class at 256 / 768. "Dust" is a span of 0 and a difference under 0.01.

| Dial | Canonical 256 | Canonical 768 | Wide 256 | Wide 768 |
|---|---|---|---|---|
| Rhythm bands (5 / 150 / 300) | retune | retune | retune | retune |
| Watcher composite (0.40) | shifted | shifted | shifted | shifted |
| Coherence pin | pin, moved | pin, moved | pin, moved | pin, moved |
| FFT layout | shifted | shifted | shifted | shifted |
| Crystal 0.75 / 0.60 / 0.80 | retune | retune | shifted | retune |
| Witness crystallization | retune | retune | retune | retune |
| Attractor 0.88 / pull 0.75 | retune | retune | retune | retune |
| Lattice edge 0.75 | retune | retune | retune | retune |
| Binding 0.82 | retune | retune | retune | retune |
| Value counts | invariant | invariant | invariant | invariant |
| Core alignment | retune | retune | shifted | retune (dust on the ≥ 0.5 gate) |
| Bonds | retune | retune | retune | retune |
| Allow / weakened | retune | retune | invariant | retune |
| Identity erosion 0.30 | retune | retune | retune | retune |
| Drift 0.15 / 0.30 | shifted | retune | shifted | retune |
| Gaslighting −0.20 | shifted | shifted | shifted | shifted |
| Ethical floors −0.05 / −0.30 | shifted | shifted | shifted | shifted |
| Predictive echo 2.5 | shifted | shifted | shifted | shifted |
| Reflective loop | retune | retune | retune | retune |
| Metastability | retune | retune | retune | retune |
| Vibration gauge (trailing 256) | shifted | shifted | shifted | shifted |
| Embedding init | shifted | shifted | shifted | shifted |
| Field gain | shifted | shifted | shifted | shifted |
| Pattern cutoff 0.7 | retune | retune | retune | retune |
| Boredom override (census: no) | retune | retune | retune | retune |

Stabilize occupancy also trips the rule (span 0, the rate moves by less than 0.002). That is not a retune of the 5.0 band. Wide `alignment_over_0_5` at 768 moves 0.998 → 0.997 on one seed. Same treatment.

The pin, reported and not for retune: field coherence, canonical seeds, mean 0.9944 → 0.9915 → 0.9887. Wide 0.9935 → 0.9904 → 0.9853. Still the lock.

Value counts do not move. Canonical active values are 46 on every seed at every width, and strong is 5 / 6 / 12 on seeds 42 / 43 / 44 at every width. Wide stays at the cap-churn the wide-workload finding already recorded (active 0–1).

## Ranked retune list

Order a later change should follow. The 500-step class is the rule. The rank uses the step-260 cut where the cut exists, so a constant the settled field still clears does not get rewritten off a youth average.

**1. Rhythm bands, as a group. This is the settled-regime retune.**

Canonical field energy in steps 261–500: seeds 282 / 287 / 290 at 128, 247 / 253 / 246 at 256, 231 / 251 / 236 at 768. The reflect/explore edge is 300. The settled 128 field sits on it (explore in that half 0.21 / 0.26 / 0.34). The settled 256 and 768 fields sit under it (explore 0 / 0.01 / 0 and 0 / 0.08 / 0). Reflect in that half goes from about 0.7 to about 1.0 because explore is gone, not because dream took it: dream in the late half is 0 at every width.

Wide does not ask for the same edit. Its settled half is already reflect at 128 (explore 0 / 0 / 0.04, energy 251 / 260 / 267) and stays reflect while energy falls further (about 241, then about 226). The full-run dream-up / reflect-down on both workloads is youth: early dream occupancy goes from ~0.4 to ~0.9, and the late half is dream 0 everywhere.

Do not move one band. The census already says the three thresholds are one calibration. Re-measure after, including this cut.

Reflective-loop `reflect_rate` is this same fact (canonical full-run 0.77 → 0.53 → 0.49). `reflect_converged_rate` stays 1.0 at every width. Convergence 0.995 and `attenuation_max` 0.30 are not what moved.

**Leave these constants. The rule says retune; the late half still clears.**

**2. Identity erosion, threshold 0.30, and the allow/weakened split.**

`|G−T| ≥ 0.30` and the erosion fires stop at step 260 at every width, both workloads, except a 768 trickle (canonical seed 42: 7 of the last 240 steps over the gap; wide 768 weakened in that half 0.06 / 0.05 / 0.03). The window does not get longer. It gets fuller. Canonical early fraction over 0.30: 0.30 / 0.21 / 0.15 at 128, 0.80 / 0.78 / 0.80 at 256, 0.94 / 0.84 / 0.86 at 768. Late fraction: 0, aside from that trickle. Weakened decisions match the fires, not a long tail.

This is not the refuse-order finding's queue dwell. That finding counted steps with severity ≥ 0.30 still queued (canonical 128, about 240 of the first 500). This probe counts steps where `|G−T|` is over 0.30 and steps the detector fires. At canonical 128 seed 42 those are 79 and 84, all inside the first 260, against 84 `allow_weakened` for the whole run. The queue can outlast the fire. The fires themselves end where that finding said the damp ends, at 128 and at 768.

Full-run allow/weakened (canonical means 0.92 → 0.56 → 0.51 allow) is that youth mix. The settled half is allow.

**3. Attractor formation 0.88 and pull 0.75.**

Late-half formation-clear and pull-above are 1.0 at 128 and at 256 on both workloads. At 768 the late half is still mostly clearing: canonical pull-above 0.96 / 1.0 / 0.96, wide 0.88 / 0.95 / 0.92. The 500-step collapse (canonical pull-above 1.0 → 0.63 → 0.52, attractors at end 15/14/12 → 2/4/3 → 3/3/3; wide attractors 54 → 2) is the early half, where pull-above falls from 1.0 to ~0.3 to ~0.1. End counts are the youth miss persisting. The settled gate is not the thing that failed.

**4. Crystal thresholds 0.75 / 0.60 / 0.80.**

Same shape. Late-half all-clear is 1.0 at 128 and 256. At 768 it is 0.97 / 1.0 / 0.94 canonical and 0.87 / 0.98 / 0.87 wide. Births on canonical are all in the first 260 at 128 (15 / 17 / 13, then 0) and almost none at width (1–2, one of them late on seed 42 at 768). The store ending at 1 crystal is that missed youth burst, not the settled cosine gate refusing the field. Witness crystallization (full-run clear 0.63 → 0.33 → 0.12 canonical) was not in the cut. It reads the same coherence family. Do not retune it off the 500-step mean until it is split; it is listed with the unsplit reads below rather than assumed clear.

**5. Boredom override, threshold 0.50.** The census marked this dial no. The rule flags the count (canonical 291/302/292 → 240/197/237 → 200/218/212). On canonical the drop is youth: the late half still overrides 189/178/158 at 128 and 240/197/237, 200/218/212 at width, and the early half goes from ~100 overrides to 0. Wide 768's late half is lower (155/148/139 against 240/240/231 at 128). Not an independent retune ahead of the bands. The count fires when boredom exceeds 0.50 and the band is not already explore.

**Rule says retune. The cut did not cover the read, so these stay on the list until they are split.**

**6. Lattice edge cosine 0.75.** Nodes stay 500 (one per step) everywhere. Edges, canonical seeds: 5802/5792/5806 → 5496/5508/5586 → 5328/5338/5322. Wide: 5859±40 at 128, then 4790/5156/5556, then 2808/2988/3010. The wide-768 drop is the large one. Cumulative, so it may be youth, the settled half, or both.

**7. Binding cosine 0.82.** Below 0.82 a new concept is seeded instead of merged. Canonical established concepts (activation count ≥ 5): 1/4/2 → 13/14/13 → 17/16/17. Wide total concepts explode (mean 11 → 129 → 237) while established stays about 2 → 2 → 1. More new concepts, not fewer. Consistent with 0.82 getting harder to clear. Not split in time.

**8. Witness relational "high" cutoff 0.7.** Identity-pattern fraction, canonical: 0.996/1.0/1.0 → 0.838/0.886/0.906 → 0.522/0.718/0.540. Wide: 0.958/0.996/0.994 → 0.652/0.716/0.822 → 0.466/0.546/0.486. Not split.

**9. Witness crystallization 0.92 / 0.90 / 0.75, and the snapshot coherence gate (live value 0.80).** Full-run crystal-clear mean 0.633 → 0.332 → 0.124 canonical, 0.447 → 0.233 → 0.028 wide. Not split. See crystal item 4.

**10. Bonds.** End count, canonical 4/4/4 → 1/2/1 → 1/1/1, wide 4/3/4 → 1/1/1. The step's field-alignment ≥ 0.5 gate does not move (0.998 on 17 of 18 arms). The level does (canonical mean 0.961 → 0.908 → 0.862). Not split.

**11. Sacred promotions (`values_core`).** Canonical 2/2/2 → 1/2/1 → 0/0/0. Wide is 0 at 128 already, so it does not move. This is promotions, not the ≥ 0.5 gate in item 10. Not split.

**12. Metastability cluster tolerance 0.15.** Canonical expression regimes 2/1/1 → 15/15/15 → 16/16/16, and the state leaves locked/cycling. The monitor sees the whole run, youth included. The trailing-256 cone does open in the settled window (item under shifted), so at least some of the spread is not youth. Regime count is a decision read. Whether 0.15 is the wrong constant, or the cloud really is wider, is not settled by the label change alone.

**13. Drift gap 0.30, at 768 only.** `gap_over` leaves 0: canonical 0/0/0.038, wide 0.096/0/0.164. `velocity_over` stays 0. `manip_drift` stays 0. The short/long gap nicks the threshold; the detector does not fire. At 256 only the level moved (canonical anchor gap mean 0.051 → 0.090 → 0.122).

## Shifted, not a retune

A level moved and the decision read did not. First looks, not new constants from this rule:

1. **Embedding init.** The census's own priority 2. Row std stays ~0.035. Output pairwise cosine, same on both workloads because it is init: seeds 0.585/0.647/0.657 at 128, 0.410/0.463/0.447 at 256, 0.280/0.333/0.305 at 768, against the ~0.55 target. Embedding norm over PE norm: 0.56 → 0.79 → 1.37. At 768 the token table outgrows the sinusoid, which is the word-order failure mode inside this generator. No decision read was attached, so the rule says shifted.
2. **Vibration, trailing 256.** Label stays `white` on all 18 arms. Canonical cone 4.6/4.3/4.1° → 7.4/7.0/6.2° → 14.5/8.9/12.0°, MSD lag-1 0.013/0.011/0.010 → 0.034/0.029/0.023 → 0.135/0.042/0.083. Wide 768 cone 16.7/14.6/14.0°, spectral flatness 0.407/0.449/0.453, against the white floor 0.40. The settled stream is a wider jitter. It is not a pulse. Full-window label stays `unknown` (the opening walk).
3. **Predictive echo.** Error mean, canonical 0.299 → 0.534 → 0.656. Surprise rate does not move (the 2.5 gate still classifies the same share).
4. **Watcher composite.** The parts fall (canonical composite mean 0.917 → 0.860 → 0.830) and `stable_rate` stays 1.0. Still over 0.40.
5. **Phase coherence.** Canonical mean 0.949 → 0.894 → 0.858. Harmonic ratio does not clear its own seed span at 128 (one seed is an outlier). No gate was attached.
6. **Field gain.** Canonical mean 1.245 → 1.317 → 1.345. `gain_at_ceiling` stays 0.
7. **Gaslighting cosine.** The crystal-centroid cosine goes up, not down (canonical mean 0.890 → 0.951 → 0.965). The −0.20 gate fires on 0 steps. High-d concentration toward 0 is not what this pair does; both vectors sit in the lock.
8. **Ethical `coherence_delta`.** More negative by about 1e-4 (canonical mean −0.000165 → −0.000258 → −0.000290). Neither the soft floor nor the hard floor fires on any arm.

## Step-260 cut

Replay of the same 18 arms with the same probe, counters snapshotted at step 260 (260 steps, then 240). `youth-windows.json`. Decision reads matched the census files. On seven arms `energy_mean` differed by at most 4e-5, the last digit of the 6-decimal rounding, from running both workloads at once. Not a different trajectory.

| | Canonical late half | Wide late half |
|---|---|---|
| `\|G−T\| ≥ 0.30` | 0 at 128 and 256; 0.03/0/0 at 768 | 0 at 128 and 256; 0.03/0.03/0 at 768 |
| Erosion fires after 260 | 0, except canonical 768 seed 42 (13) and wide 768 (14/12/5) | same |
| Dream occupancy | 0 at every width | 0 at every width |
| Explore occupancy | 0.21/0.26/0.34 → ~0 → ~0 | ~0 at 128 already |
| Crystal all-clear | 1.0 → 1.0 → 0.97/1.0/0.94 | 1.0 → 1.0 → 0.87/0.98/0.87 |
| Pull above 0.75 | 1.0 → 1.0 → 0.96/1.0/0.96 | 1.0/0.99/0.98 → 1.0 → 0.88/0.95/0.92 |

Early-half `|G−T|` over 0.30, canonical: 0.30/0.21/0.15 → 0.80/0.78/0.80 → 0.94/0.84/0.86. The young field spends more of its first 260 steps over the threshold as width grows. It does not keep the gap over the threshold once that window ends.

## Threats

- Three seeds, 500 steps, pretrain off, dream channel off. A pretrained generator can change the youth length and the settled energy. H0's cone was measured with pretrain; the vibration baseline already flagged that.
- The step-260 boundary is the refuse-order finding's canonical dwell, applied here as a cut. It was not pre-declared before these arms. Wide was not where that dwell was measured. On these arms the fire counts do end there anyway.
- Span 0 promotes dust to "moved". Two of those are named above and left off the retune list on purpose.
- Lattice, binding, the pattern cutoff, witness crystallization, bonds, sacred promotions and the metastability regime count are 500-step facts without a youth split. Ranking them under the settled bands is "not yet shown to be settled", not "shown to be youth".
- `manip_erosion` is not queued-severity dwell. See item 2.

## Open

- [ ] Retune the rhythm thresholds as one group off the canonical settled energy, then re-measure with this cut. Not in this commit.
- [ ] Split lattice, binding, the 0.7 pattern cutoff, witness crystallization, bonds, sacred promotions and metastability at step 260 before treating them as settled-regime retunes.
- [ ] Embedding init against the ~0.55 target at 256 and 768 (shifted; at 768 `emb_over_pe` crosses 1). Census priority 2. No constant changed here.
- [ ] A pretrained arm. Pretrain was off on all 18.
