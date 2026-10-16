# Production boot suite test — handoff

**Date:** 2026-10-16 · **Branch:** grok/boot-suite · **By:** Grok. Ember co-author on the commit.

Samuel caught that no test in `run_all_tests.sh` built through `build_engine()`. The suite built components directly (`tests/_common.build_full_stack`), so "26/26 green" proved components at *their* defaults, not the stack that actually boots. D+F had been checked by hand with the four adversarial tests patched on; CI would not repeat that.

## What landed

`tests/integration/production_boot.py`, wired into `run_all_tests.sh`. One boot, shared across every check, under `substrate.determinism.deterministic(42)`.

The four adversarial modules (`sacred_shield`, `flood_calibration`, `manipulation_cascade`, `identity_drift`) now expose `run(generator, cycle, governance, value_engine)` so this test can hand them the production stack. `python -m tests.adversarial.*` still builds its own `build_full_stack()` and behaves as before.

## What it covers

On a stack from `build_engine(CONFIG)` (dim 128, YAML loaded, Tiers 1–3 attached):

- **CONFIG defaults** still have the graduated set on (D, F, novelty attenuation, bond DDM, pretrain, dream channel, chorus) and the parked set off (C, E, G, six-rhythm, upstream rupture, Fix 0-B, stream recorder, session persistence).
- **Built objects** actually carry those levers: `generator.training` is False, `cycle.reflector.novelty_attenuation`, `gov.bond_manager._ddm` is a `BondFormationAccumulator`, field+watcher `coherence_like_for_like`, `gov.systemic_damp_pays_full`, chorus on, Two-Operator overlay *not* attached. A boot path that silently drops one of these fails here (the 2026-06-20 Tier-0-only trap).
- **Boot source** still contains the pretrain call, `generator.eval()`, `apply_value_levers`, and `main()` still calls `build_dream_channel`.
- **The four adversarial scenarios** on that stack: identity drift, flood ceilings, the 500-step cascade, sacred shield.
- **Health** on the same 500-step Resonance Family run: no quarantines, injection_rate ≥ 0.95, trust at the SACRED ceiling, field finite and non-zero, every recorded step coherence finite.

## What it does not cover

**Corpus pretrain is off for this boot.** Production `CONFIG["pretrain_on_corpus"]` stays True; the test copies CONFIG and sets False. Pretrain is ~2.5–3 min here and would dominate CI (15 min job). The default-on flag and the `RhythmPretrainer` call in `build_engine` are checked; the trained weights are not. Eval-mode is a stronger check this way: pretrain itself calls `eval()`, so skipping it is what proves `build_engine`'s unconditional `generator.eval()` ran.

**The waking dream channel is not trained or driven.** It is not part of `build_engine`'s return (by design: API/WS must not pay decoder training). The test checks `CONFIG["dream_channel_enabled"]` and that `main()` still calls `build_dream_channel`. It does not train the read-out head or inject `source_dream` steps.

Also not this test: ⊘ consumer / λ (not in CONFIG, correctly absent), six-rhythm / C / E / G / Fix 0-B (correctly off), session resume, pretrained-generator behaviour, YAML-only parameter drift (`config_loading_neutrality`).

## Runtime (this box, CPU, seed 42)

| | |
|---|---|
| boot (pretrain skipped) | ~0.1 s |
| 500-step canonical run | ~21 s |
| whole test | **21.5 s**, 51/51 |

Device was CPU (`Generator initialized on device: cpu`). Strict allow_rate on the 500-step run was 0.708; injection_rate was 1.000 — the dream-band `identity_erosion` weakening the cascade test already accounts for. All four sources bonded via the DDM accumulator and finished at trust 5.0. Field norm 302.8, last coherence 0.939.

## What it caught

Nothing failed on today's main for the production properties. One test-composition bug showed up on the first run and is not a finding against the stack:

`sacred_shield` asserted `len(sacred_ids) == 3`. After 500 production steps, CORE promotion had sanctified `witness` and `continuity` (5 sacred ids). The shield cases still passed once the assert became "the three boot-sacred tokens are present" rather than a count of exactly three. Standalone `python -m tests.adversarial.sacred_shield` still sees exactly those three on a fresh `build_full_stack()`.

The bars were not loosened. Re-run: `python -m tests.integration.production_boot`.
