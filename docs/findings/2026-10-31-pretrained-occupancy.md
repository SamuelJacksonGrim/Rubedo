# Does pretrained occupancy hold at 256 and 768 against the declared 128 target?

- **Date:** 2026-10-31
- **Substrate:** `build_engine(CONFIG)` with `dim` overridden per arm. `FIELD_DIM` stays 128. Production path: 8-epoch corpus pretrain, `generator.eval()`, dream channel not built. D and F on. Bond DDM on. Witness selector on; the rhythm reader attaches (unlike the census, where it was inert). Fragmentation grace's flag is on; `build_engine` does not attach the consumer. Rupture off. Thresholds left at 5 / 150 / 300. CPU.
- **Probe:** `tests/diagnostic/widening/rhythm_band_probe.py --batch-pretrained-free`. Neither this file nor the probe edits a constant. Job `.detached/pretrained-occupancy`, status `DONE 0` at 15:12.
- **Status:** standing
- **Depends on:** `2026-10-31-settled-half-and-f9-gate` (the occupancy rule, written before any pretrained free-run arm), `2026-10-31-dial-census-widths` (the pretrain-off band verdict this check was asked to confirm or invert)

## Question

Widening step 4's remaining question. Under 8-epoch pretrain, does settled-half occupancy at 256 and at 768 hold against a 128 target declared from the 128 fit arms *before* those widths are read? If it holds on the fitting seeds and again on held-out seeds 45 and 46, step 4 is no band retune. If it does not, say which band and which width. There is no second placement.

## Pre-declared signatures

Written in `rhythm_band_probe.py` before any pretrained free-run arm, and before any 256/768 occupancy is read. Not edited to fit the result.

Canonical only. Settled half steps 261–500, energy-classified rhythm. Boredom's override does not count as explore. Seeds 42–44 fit; 45 and 46 held out. Widths 128 / 256 / 768.

The 128 target is the pretrained 128 fit arms, not the census youth replay. After those three arms finish, `declaration.json` records per-band mean and span of the late fractions (6 d.p.), plus:

- `explore_positive`: every fit seed's late explore count is > 0
- `dream_max_allowed = max(2, max late dream)`
- `stabilize_max_allowed = max late stabilize`
- `reflect_gt_explore`: every fit seed's late reflect > late explore

SUCCESS at width W, on the fitting seeds and again on the held-out seeds:

- for every band, `abs(mean_W − mean_128) <= span_128` (span 0 means any remaining difference fails)
- if `explore_positive`: every seed's late explore > 0; else every seed's late explore is 0
- every seed's late dream <= `dream_max_allowed`
- every seed's late stabilize <= `stabilize_max_allowed`
- if `reflect_gt_explore`: every seed's late reflect > late explore

The 128 held-out seeds must pass the same bars. If they miss, the 128 target is not stable and 256 / 768 are not judged as a retune. If occupancy holds at 256 and at 768 on both seed sets, the answer to step 4 is no band retune. If it does not, say which band and which width. There is no second placement. Do not walk the thresholds toward the free-run mean.

## Result

No constant changed. `DEFAULT_THRESHOLDS` is still 5 / 150 / 300. 15 canonical arms, all `pretrain=True`, `witness_reader=True`, `delta_below_hard` 0, reject 0, quarantine 0. Data: `docs/findings/data/2026-10-31-pretrained-occupancy/`. `declaration.json` was written from seeds 42–44 at dim 128 and was not rewritten from later arms (`declared_before: "256/768 occupancy"`).

Driver exit after scoring: **PRETRAINED OCCUPANCY FAIL (16)**. The probe printed `128 held-out missed the declared target; 256/768 are not a retune`. It did not print `step 4 answer: no band retune` (that line is the PASS path).

### Declaration (128 fit, seeds 42 / 43 / 44)

Late counts out of 240:

| Seed | stabilize | dream | reflect | explore |
|---|---:|---:|---:|---:|
| 42 | 0 | 0 | 240 | 0 |
| 43 | 0 | 0 | 233 | 7 |
| 44 | 0 | 0 | 240 | 0 |

Declared: explore mean **0.009722**, span **0.029167**; reflect mean 0.990278, span 0.029167; dream 0 span 0; stabilize 0 span 0. `explore_positive` **false**. `dream_max_allowed` 2. `stabilize_max_allowed` 0. `reflect_gt_explore` true.

### Late occupancy against that target

| Group | explore mean | reflect mean | mean/span | structural `explore==0` |
|---|---:|---:|---|---|
| 128 fit (target) | 0.009722 | 0.990278 | tautology | seed 43 has 7 |
| 128 held-out | **0.047917** | 0.952084 | **MISS** explore Δ 0.038195, reflect Δ 0.038194 | s45: 15, s46: 8 |
| 256 fit | 0.036111 | 0.963889 | holds (explore Δ 0.026389 ≤ 0.029167) | s43: 26 |
| 256 held-out | 0.027083 | 0.972916 | holds | s45: 1, s46: 12 |
| 768 fit | **0.058333** | 0.941667 | **MISS** explore Δ 0.048611 | s42: 4, s43: 21, s44: 17 |
| 768 held-out | **0.120833** | 0.879166 | **MISS** explore Δ 0.111111 | s45: 0, s46: 58 |

Dream 0 and stabilize 0 on every arm. Reflect > explore on every arm. The 16 FAILs are the ten structural `explore grew to N; 128 fit had none` lines (including 128 fit seed 43) and the six mean misses above (128 held-out reflect+explore, 768 fit reflect+explore, 768 held-out reflect+explore). 256's means hold on both seed sets.

Per-seed late explore, the number the user already has from the log tail: 128 fit 0.010, 768 fit **0.058**, 768 held-out **0.121**. Canonical 768 explores *more* than 128 pretrained, not less.

### Late energy (not a decision read; the quantity the 300 edge sits on)

Mean field energy, steps 261–500:

| Width | Fit 42 / 43 / 44 | Held 45 / 46 |
|---|---|---|
| 128 | 247.7 / 252.3 / 248.0 | 259.2 / 243.7 |
| 256 | 236.3 / 257.6 / 236.5 | 250.6 / 254.0 |
| 768 | 248.3 / 255.3 / 248.4 | 244.5 / 268.9 |

Every pretrained late mean sits under 300. Census pretrain-off canonical 128 was 282 / 287 / 290, on the edge, with late explore 0.21 / 0.26 / 0.34. That is the occupancy pretrain itself removed. Width then moves a smaller remainder, and at 768 the remainder is *up*.

### What else these arms show (not scored)

All 15 arms end metastable, 4 or 5 regimes (expression and generator). Pretrain-off canonical 128 in the youth split ended locked/cycling (2 / 1 / 1). Late sacred promotions are 1 or 2 at every width, 768 included (census 768 late was 0 / 0 / 0). Witness crystallization still fires in the settled half at every width (late crystal-clear 51–170 of 240). `emb_over_pe` at 768 is still over 1 (0.33–1.42). None of that is a band retune, and none of it was this probe's bar.

## Interpretation

Occupancy does not hold. Step 4 is still **no band retune**, for the stop the rule named, not because the PASS line fired.

The 128 held-out seeds miss the declared target (explore 0.048 vs 0.010, span 0.029). That is the pre-declared stop: the 128 target is not stable, and 256 / 768 are not judged as a retune. There is no second placement. Walking 5 / 150 / 300 toward a 768 free-run mean is the thing the rule forbids.

If the 128-unstable stop is set aside and the mean/span rule is still read as a width comparison: 256 holds on both seed sets; 768 does not. The miss is explore (and the complementary reflect). Direction is the opposite of the census. Census pretrain-off: settled energy fell *off* the 300 explore edge as width grew (late explore 0.21–0.34 at 128, ~0 at 256/768), so the surviving retune was "lower the edge." Under 8-epoch pretrain, 128 is already a reflect home (late explore 0.010, late energy ~248), and 768 explores *more* (fit 0.058, held-out 0.121). Lowering 300 would walk the wrong way. The large occupancy change is pretrain itself, not width.

`explore_positive` is all-or-nothing. The 128 fit was mixed (0, 7, 0), so the flag is false, and the structural bar then requires every seed's late explore to be 0 — which fails the fit seed that had 7, and prints `128 fit had none` about a declaration that recorded 7. That bar cannot represent mixed occupancy. It is on the score sheet. The mean/span rule is the one that actually compares widths. Both were pre-declared. Neither is re-declared to make 768 pass.

The plug-in body (EmbeddingGemma-2, or RFE's own encoder) is still not this generator after 8 epochs of rhythm contrastive pretrain. Pretrain-off remains the honest first-boot of that body; that is why the census and the youth split stay on the ledger. Pretrain-on is F9's condition and the production 128-style boot. Occupancy was the production/F9 question. It does not license a band retune, and it does not license retuning witness crystallization, sacred promotions, or the cluster tolerance off the pretrain-off youth split either.

These 15 arms never fail a hard gate. The shield-scope change on `origin/main` (`86d5351`) plants nothing on refused steps; canonical occupancy has none. Rebase does not rewrite these files.

## Threats / confounds

- Three fit seeds plus two held-out. 768 held-out explore 0.121 is seed 46's 58 late explore against seed 45's 0. A two-seed held-out mean is noisy. It is still a miss against span 0.029, and seed 46 alone is already past the bar.
- Occupancy is energy-classified (`state.rhythm`). Boredom overrides still fire (128 fit 239 / 232 / 240 for the full run) and do not count as explore. That is the same convention as the census.
- `explore_positive=false` on mixed 128 occupancy is a rule limitation, recorded above. It inflates the FAIL count. It is not why 768's means miss.
- Wide was not in this batch. The census band retune was canonical.
- CPU, two workers. 128 arms ~150 s; 768 arms ~25 min. Not a GPU result.
- Declaration is write-once. Scoring re-read it; it was not rebuilt from 256/768.

## Open / next

- [ ] The degraded gate is still the further question the F9 finding named. July's probe never pinned `ALLOW_WEAKENED`. Occupancy does not answer it. The EmbeddingGemma 0.4× pin did not either (`2026-11-01-embeddinggemma-coupling`): unforced ALLOW on that stabilize pin was 13/400.
- [ ] Witness crystallization, canonical sacred promotions, and the canonical regime count still move after step 260 on a *cold* generator. These 15 pretrained arms do not reproduce that locked/cycling 128 or the 768 sacred-zero. They are not a retune of those constants. A pretrained youth split would be, if those dials are going to be classified under production boot.
- [ ] Wide occupancy, same rule, if a wide band claim is going to be made. Not this commit.
- [ ] Embedding init against ~0.55 at 256 and 768 (shifted; census priority 2). Still open. 768 `emb_over_pe` still crosses 1 on these arms.

Suite **32/32**. Doc-accuracy **19/19**. `rhythm_band_probe --check` PASS. `--score-pretrained` exit 2, FAIL (16), same numbers as the 15:12 job.
