# From jitter to vibration — the observe-only gauge, and today's baseline

- **Date:** 2026-10-31
- **Substrate:** live (`build_engine` production CONFIG, dim 128). Pretrain skipped (CPU; the GPU is on the encoder). Witness selector is ON in CONFIG and inert without pretrain (`production_boot` same stack). Canonical Resonance Family, 46 tokens, seed 42, `substrate.determinism`.
- **Probe:** `tests/diagnostic/metastability/vibration_probe.py`; gate `tests/smoke/stream_vibration_smoke.py`
- **Status:** standing
- **Depends on:** `2026-10-15-h0-steady-self-rattling-mind`

## Question
H0 found expression is white jitter in a fixed cone (MSD flat from lag 1 to 512). Samuel's maturity target is the same cone with a pulse in it ("a resonance. A pulse, a rhythm, and a sustainable frequency"). Before any lever is asked to move it: build the observe-only gauge on the expression stream, show it can tell white / a vibration / a rigid loop apart, prove it does not change a loop number, and read today's baseline at S3 and the first S4.

## Pre-declared signatures
- SUCCESS looks like: the three synthetic controls label white / vibration / lock-in and do not overlap on spectral flatness, a holding period, leftover variance, or MSD-at-period. The live stream at S3/S4 reads white (spectral flatness near 1, no period that holds, MSD flat). With vs without the gauge, the loop is byte-identical.
- FAILURE looks like: the controls overlap, or the live stream already shows a holding period with MSD dips at that period and leftover variance in the vibration band.
- CONFOUNDED looks like: the S3 window still contains the opening walk (view saturates ~235, formation closes ~400), so a 500-sample read mixes infancy into the spectrum. Named in advance: also read a trailing-256 at S3, and read S4 on a window that is entirely post-formation.

## Result (observed)

**Instrument.** `cognition/stream_vibration.py`, wired as `cycle.expression_vibration`, tapped at `_last_expressed` (post-reflection — the stream H0 recorded), never on the field. Bounded ring 512, lazy SVD/rFFT every 32 steps, default-on as a pure observer (`CONFIG["expression_vibration"]=True`). Opt-out `False`. Period from the first autocorrelation peak of the unit-vector stream (FFT peak-picking prefers harmonics on a discrete loop); spectral flatness from the PCA-axis power spectrum; leftover = variance after subtracting the mean cycle.

**Controls** (T=256, dim=64, PCG64 seed 0; same split on dim 128 / T=512, seeds 0–2):

| control | label | spectral flatness | period | holds | residual | MSD at period / lag 1 |
|---|---|---|---|---|---|---|
| i.i.d. unit vectors | white | 0.828 | none | no | — | flat ~2.00 from lag 1 to 192 |
| period-16 orbit + 0.06 isotropic noise | vibration | 0.011 | 16 | yes | 0.173 | 0.365 / 0.496; dips at 16, 32, 48, 64 |
| rigid 16-cycle of distinct unit vectors | lock-in | 0.000 | 16 | yes | ~0 | 0 at every multiple of 16 |

**Observe-only.** `tests.smoke.stream_vibration_smoke`: 80-step Resonance Family, dim 64, seed 11, with vs without — field / emotion / trust / keys / decisions digest `210c26d54cd9639a` both ways, field bytes identical. The gauge module imports nothing from `loop/` or `agents/`. The cycle never reads the report.

**Live canonical, seed 42, 1000 steps, 31.5 s CPU, window 512.**

S3 (step 500, explore, crystals 12, attractors 15, values 46/46 active, 2 CORE):

- Full window (n=500, includes the opening): label `unknown`, sf=0.200, a period-3 that does **not** hold, residual 0.090, cone 14.5°, MSD rising 0.083 (lag 1) → 0.391 (lag 384).
- Trailing 256 (settled): label `white`, sf=0.824, no period, cone 4.6°, MSD flat 0.013 from lag 1 to 192.

S4 (step 1000, last 512; same ecology):

- label `white`, sf=0.827, no period, cone 4.8°, MSD flat 0.014–0.015 from lag 1 to 384.
- Trailing 256: white, sf=0.783, MSD flat 0.015.

## Interpretation
The gauge does the job the backlog asked: white, a pulse with variation, and a rigid loop are three different reads, and lock-in cannot wear a rhythm past the leftover check.

Today's expression stream, once formation has closed, is still white jitter. Nothing in it repeats. Spectral flatness sits with the white control (~0.83), not the vibration control (~0.01). MSD is flat across the lags the window can see. That is H0's rattling mind, restated with the instrument that can see a pulse if one appears.

The S3 full-window `unknown` is the named confound: the opening walk is still in the ring, MSD climbs with lag, and a spurious period-3 does not hold. The trailing-256 at S3 and the S4 window are the baseline to beat.

Default-on, not default-off: this is a stethoscope, not a lever. A gauge that has to be remembered will not be read at S3/S4. Cost is an O(1) copy per step and a 512×D SVD every 32 steps, off the cognitive path. Opt-out is one flag and does not change a loop number.

Do not move a lever on the strength of this finding. The read exists; the pulse does not.

## Threats / confounds
- Runs: 1 live seed (42). Controls: 3 seeds × 2 shapes, all split.
- Pretrain skipped. H0's all-ON stack pretrained 3 epochs; an untrained generator is more collinear, which likely tightens the settled cone (4.8° mean-direction here vs H0's ~15° whole-run cone). The S3 full-window cone 14.5° recovers H0's number because it still contains the walk. White-vs-pulse is the claim; the absolute cone is not a re-measure of H0.
- Window 512. S3 full read is 500 samples (short of one H0 lag-512). S4 is a full 512, all post-formation.
- `cone_deg` is mean angle from the mean direction, not the board's lag-1 MSD-as-angle. Settled lag-1 MSD 0.014 is ~6.8° as an angle (`acos(1 − msd/2)`).
- Classification floors (`_SF_WHITE=0.40`, `_ACORR_PEAK=0.40`, `_RESID_LOCK=0.06`) were set so the three controls separate. A live stream that sits between them is labelled `unknown`, not forced.

## Open / next
- [ ] Pretrained arm (or a checkpoint boot) at the same S3/S4 marks, so the cone is comparable to H0.
- [ ] More seeds. One seed is a first look, not a distribution.
- [ ] The themes-plus-novelty workload (BACKLOG). Canonical starves novelty; that may be why there is no pulse to find.
- [ ] Then, and only then, a lever. The gauge is the read; it is not the move.
