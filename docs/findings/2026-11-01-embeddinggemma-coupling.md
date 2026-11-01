# Does a pretrained 768 field with EmbeddingGemma perception still meet the F9 constraints, and does it still couple to content?

- **Date:** 2026-11-01
- **Substrate:** July's stack, not `build_engine`. `Generator(dim=N)`, 8-epoch rhythm pretrain, `eval`, `AutonomousCycle` with chorus, governance, and the value engine. `FIELD_DIM` stays 128. The 768 body is an override. After pretrain, `generate` is wrapped so the step's vector is EmbeddingGemma-300M's unit vector (llama.cpp, CPU, `--embedding`, `-ngl 0`, port 8082). The 128 coupling arm is the same stack with the generator's own encode. Thresholds left at 5 / 150 / 300. CPU. No constant edited.
- **Probe:** `tests/diagnostic/widening/embeddinggemma_probe.py --batch`. Job `.detached/egemma-step5`, status `DONE 0` at 2026-11-01T00:47:05. Rules hash `c5c4383e9eee9dc7d16c10585826b754df07a58b12c8c57865da8c021a4936a2`, written to `declaration.json` before the first pretrain and not rewritten.
- **Status:** standing
- **Depends on:** `2026-10-31-settled-half-and-f9-gate` (F9's constraint set, and the open degraded-pin question), `docs/WIDENING_PLAN.md` step 5, `substrate/resonance_field.py` `DEFAULT_THRESHOLDS`

## Question

Widening step 5. Plug EmbeddingGemma into a 768 field whose generator was pretrained at that width. Do the shipped bands still satisfy F9's constraint set on that body (four bands, last 100 of 400, plus a real weakened-injection stabilize pin)? And does the wide field still respond to content the way the 128 field did?

## Pre-declared signatures

Written in the probe before any arm. Not edited to fit the result. `declaration.json` says `declared_before: "any arm"`.

Seeds 42, 43, 44. Source schedule RNG 1188, the same tokens on every seed. Equilibrium is the mean post-step field L2 over the last 100 of 400. Drift is recorded and is not part of the hold.

**Constraints hold** on every seed, not on the mean:

- full-strength stabilize equilibrium > 5
- degraded stabilize equilibrium > 5, and only if the unforced decision was `ALLOW` on at least 0.80 of the steps. Below that the wrap did not weaken a full-strength body, and the constraints are not claimed
- dream equilibrium > 150
- 150 ≤ reflect equilibrium < 300
- explore equilibrium ≤ 303 (300 × 1.01). The 1% is July's published explore pin of 301.1, which the constraint text treats as on the line of 300. It is not a fitted slack

The degraded pin rewrites thresholds to stabilize and returns every non-blocking decision as `ALLOW_WEAKENED` at the live factor 0.40. Boredom stays at 0.50. Its count does not void a pin. The cold-harness ranges are not this gate.

If the constraints do not hold, the F9 integer formula proposes a placement on the seed-mean equilibria and does not apply it. Stabilize stays 5. The dream cut is `round(0.75 × dream equilibrium)`. The explore edge is `ceil(explore equilibrium)`, raised only if that is what keeps reflect inside the band.

**Couples**, per width: every seed's Pearson r of content-change with value-change, rounded to 6 decimal places, is ≥ 0.20; the mean of those is ≥ 0.30; and the mean content-change on the 15 block switches is ≥ 0.02. Content-change is `1 − cos` of the cached perception of the tokens. Value-change is the L2 change in live value strengths. The schedule is July's 12 phrases in 16 blocks of 25, so a repeated text has content-change 0 by construction.

**The way the 128 field did** requires the 128 arm to couple, the 768 arm to couple, the two means to differ by no more than `max(span_128, 0.10)`, and no sign flip on a 128 seed that itself cleared 0.20. Both clauses are the pass. A match between two failures is not a pass.

The free run is a log. Thresholds untouched. It records the energy class and the behavior boredom actually ran. It is not a gate.

## Result

No constant changed. `DEFAULT_THRESHOLDS` is still 5 / 150 / 300. `FIELD_DIM` is still 128. Every arm file records `device: cpu` and `field_dim_constant: 128`.

Pretrain did train. Final rhythm accuracy is 0.988 / 0.987 / 0.989 at dim 128 and 0.981 / 0.983 / 0.984 at dim 768 (seeds 42 / 43 / 44). Loss fell across 8 epochs on every arm. Those weights are not the step's vector on the 768 arms. The wrap replaces `generate` after the checkpoint is saved.

**Constraints: FAIL.** Two failures, both on every seed.

Pinned explore, and this one is a full-strength body. Decisions on the explore pin are ALLOW 397, ALLOW_WEAKENED 1, MONITOR 2, the same on 42, 43, and 44. Boredom overrides 0. Last-100 means:

| Seed | stabilize | dream | reflect | explore |
|---|---:|---:|---:|---:|
| 42 | 25.4 | 184.7 | 295.9 | 307.2 |
| 43 | 35.6 | 183.3 | 296.3 | 307.1 |
| 44 | 24.9 | 182.5 | 294.4 | 311.2 |
| mean | 28.6 | 183.5 | 295.5 | 308.5 |

307, 307, and 311 are all above 303. The seed-mean 308.5 is above it. 300 sits below the pinned explore equilibrium, which is the failure the rule named: explore would be a basin.

The other three inequalities hold on these numbers. Stabilize is above 5. Dream is above 150. Reflect is inside [150, 300). That is not a clean reflect basin. Boredom overrode the reflect pin 284 / 278 / 235 times, so most of that pin ran explore's behavior while the classifier was pinned to reflect. The rule said a boredom count does not void the pin. It also does not make 295 reflect's own equilibrium.

The degraded pin is not the measurement. Unforced ALLOW was 13/400 = 0.0325 on every seed, under the 0.80 floor, so the constraints are not claimed from it. The unwrapped stabilize pin, and the dream pin, have the same mix: ALLOW 13, ALLOW_WEAKENED 385, MONITOR 2. Forcing the remaining 13 full-strength steps down to 0.40 did not open a lower basin. The degraded last-100 means are 31.9 / 42.0 / 31.4, all above the full-strength stabilize means, not below them. The ~13 figure in the constraint text was not reproduced, and this arm cannot be used to place against it.

Every last-100 window is still climbing. Drift (second 50 minus first 50) is positive on every band and every seed, and above 2% of the level on every one of them. Stabilize's drift is about 6–8 on a level of 25–36. Explore's is about 10–12 on a level of 307–311. Reflect's is about 15. The rule recorded drift and did not gate on it. The levels above are not settled equilibria.

**Proposal, not applied.** The formula, given the seed-means including the rejected degraded mean of 35.1, emits stabilize 5, dream 138, reflect 309. `apply` is false. Read as four bands that would be stabilize below 5, dream below 138, reflect below 309, explore at or above 309.

That stabilize 5 is not a degraded measurement. The formula keeps 5 whenever the degraded mean is above 5, and the mean it saw is the pin the allow floor rejected. The dream cut 138 is `round(0.75 × 183.5)` from a dream pin that was already weakened 385/400. The explore edge 309 is `ceil(308.5)` from the full-strength explore pin, one unit above a mean that climbed about 11 in the previous 50 steps. Shipping 309 would draw the line on a window that has not stopped. Nothing was edited.

**Coupling: FAIL.** Content contrast is real, and the absolute bar fails at both widths. The match clause holds. The pass requires both.

Switch `1 − cos` (15 boundaries), within-block content-change is 0 by the cache:

| Dim | Seed | r | switch 1−cos |
|---|---:|---:|---:|
| 128 | 42 | −0.017060 | 0.367 |
| 128 | 43 | −0.022068 | 0.466 |
| 128 | 44 | −0.016477 | 0.359 |
| 768 | 42 | −0.016599 | 0.397 |
| 768 | 43 | −0.016623 | 0.397 |
| 768 | 44 | −0.018977 | 0.397 |

Means −0.018535 (span 0.005591) at 128 and −0.017400 (span 0.002378) at 768. The gap is 0.001, inside the 128 span. No 128 seed cleared 0.20, so the sign rule had nothing to compare. Twelve distinct phrases at both widths. The 768 switch distance is the same on every seed because the embedder is deterministic and the phrases are the same. The 128 distance moves with the seed because each generator encodes the phrases differently. Both clear 0.02.

Value strength barely moves, and it moves less at a switch than inside a block. Mean per-step L2 at the 15 switches is 0.001386 on all six arms. Mean per-step L2 on the other steps is about 0.0017–0.0021. The largest single step is about 0.05. The path length over 399 steps is 0.66–0.83. A correlation near −0.02 is that pattern: the switch steps are slightly quieter than the steps where the text did not change. It is the same pattern at 128 and at 768. The wide field does not track content. The 128 field does not either. This is not a width collapse.

**Free run.** Thresholds 5 / 150 / 300. Last 100, post-step energy class is reflect on all 100 steps, every seed. Mean energy 235.2 / 234.6 / 230.4. Behavior in that window: explore 100 / 100 / 59, and reflect 0 / 0 / 41. Boredom overrides over the whole 400: 148 / 138 / 59, and that count equals the number of steps whose behavior differed from the energy class. Nothing else rewrote the band. The energy class never enters explore. Boredom is what runs explore while the field sits in reflect, under 300, about 70 below the pinned explore equilibrium and about 60 below the boredom-contaminated reflect pin.

## Threats

- Three seeds, one schedule. The decision mix is identical across seeds because the tokens are identical. That is the design. It is not three independent governance histories.
- Drift is not in the hold, and every window failed the 2% description. The explore failure would survive a settled window only if the climb stopped below 303. It was still going up at step 400. A longer pin is a different instrument. It is not a reason to ship 309 off this one.
- The reflect inequality holds on a pin boredom mostly turned into explore. Do not quote 295 as reflect's own equilibrium on this body.
- The degraded arm's higher mean is inside the size of the drift. It is not evidence that weakening raises energy. The allow floor already refuses the arm.
- Coupling's negative sign is small and replicated. It is not a claim that values move against content in any way that clears 0.20. The bar was 0.20 per seed and 0.30 on the mean. Both widths miss it by an order of magnitude.
- July's generator-perception rerun, where dream / reflect / explore barely moved with width and allow on the pin was 1.00, is a different perception. This result does not retract that table. It is the plugged body.
- The formula saw a degraded mean the rule had already rejected. The dream and explore cuts do not read that mean. The stabilize 5 does, and only as a floor check.

## Open

- [ ] RFE's own 768 encoder, same two questions, when that run exists. Not this body.
- [ ] The degraded gate on a full-strength stabilize pin. This body did not provide one: stabilize-band governance was already `ALLOW_WEAKENED` 385/400. The question in `2026-10-31-settled-half-and-f9-gate` stays open.
- [ ] A reflect pin with boredom unable to rewrite the band, if 295 is ever going to be called reflect's equilibrium here. The rule as written did not require it, and it is not a retune.
- [ ] Decode (widening step 6). Not this commit.

Suite **32/32**. `run_all_tests.ps1`, job `.detached/suite-egemma`, `DONE 0` at 2026-11-01T01:01:55. Doc-accuracy 19/19. `hardcoded_dim` PASS. `FIELD_DIM` is still 128.
