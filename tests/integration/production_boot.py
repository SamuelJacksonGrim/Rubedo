"""
tests/integration/production_boot.py

The pass/fail suite's other tests build components directly
(tests/_common.build_full_stack). Nothing they do exercises a lever that is
graduated only in CONFIG, so "suite green" does not mean the stack that
actually boots is the stack CONFIG describes (the 2026-06-20 trap:
runtime was Tier-0-only). This test boots through build_engine() with the
real CONFIG and checks composition, the four adversarial scenarios, and
basic health on that stack.

Boot is with pretrain_on_corpus=False. Corpus pretrain is ~2.5–3 min and
would dominate CI; the production default stays True and the boot source
is checked so a silent drop of the pretrain call still fails here. The
waking dream channel is built by main(), not by build_engine — CONFIG and
main()'s call are checked; decoder training is not run.

A single boot is shared across every check. Deterministic under
substrate.determinism.

Run:
    python -m tests.integration.production_boot
"""

from __future__ import annotations

import inspect
import sys
import time

import numpy as np

from agents.bond_accumulator import BondFormationAccumulator
from loop.recursion1188 import CONFIG, build_engine, build_dream_channel, main as boot_main
from substrate import determinism
from substrate.dims import FIELD_DIM
from tests.adversarial.flood_calibration import run as flood_run
from tests.adversarial.identity_drift import run as identity_run
from tests.adversarial.manipulation_cascade import run as cascade_run
from tests.adversarial.sacred_shield import run as sacred_run


SEED = 42
HEALTH_STEPS = 500  # the cascade scenario is the canonical Resonance Family run


def expect(name, ok, detail=""):
    mark = "✓" if ok else "✗"
    extra = f"  ({detail})" if detail else ""
    print(f"  {mark} {name}{extra}")
    return bool(ok)


def _check_config_defaults(results):
    print("CONFIG defaults (production dict, not the boot copy):")
    on = (
        ("coherence_impact_like_for_like", "D"),
        ("systemic_damp_pays_full", "F"),
        ("fragmentation_grace", "Fragmentation grace (graduated 2026-10-18)"),
        ("reflect_novelty_attenuation", "novelty attenuation"),
        ("bond_ddm_formation", "bond DDM"),
        ("pretrain_on_corpus", "corpus pretrain"),
        ("dream_channel_enabled", "dream channel"),
        ("use_chorus", "chorus"),
    )
    off = (
        ("dream_consolidation", "C"),
        ("value_alignment_signal", "E"),
        ("satisfaction_from_emotion", "G"),
        ("six_rhythm_selector", "six-rhythm selector"),
        ("rupture_upstream", "upstream rupture"),
        ("fix0b_diversity_fitness", "Fix 0-B"),
        ("stream_recorder", "stream recorder"),
        ("session_persistence", "session persistence"),
    )
    for key, label in on:
        results.append(expect(
            f"CONFIG[{key!r}] is True ({label})",
            CONFIG.get(key) is True,
            f"got {CONFIG.get(key)!r}",
        ))
    for key, label in off:
        results.append(expect(
            f"CONFIG[{key!r}] is False ({label})",
            CONFIG.get(key) is False,
            f"got {CONFIG.get(key)!r}",
        ))
    results.append(expect(
        "CONFIG['dim'] is FIELD_DIM",
        CONFIG.get("dim") == FIELD_DIM,
        f"dim={CONFIG.get('dim')} FIELD_DIM={FIELD_DIM}",
    ))
    results.append(expect(
        "CONFIG['fix0b_binding_leak'] is 0.0",
        float(CONFIG.get("fix0b_binding_leak", -1)) == 0.0,
        f"got {CONFIG.get('fix0b_binding_leak')!r}",
    ))


def _check_boot_source(results):
    print()
    print("Boot source (levers that are not residue on the returned objects):")
    engine_src = inspect.getsource(build_engine)
    main_src = inspect.getsource(boot_main)
    dream_src = inspect.getsource(build_dream_channel)
    results.append(expect(
        "build_engine still trains when pretrain_on_corpus is set",
        "pretrain_on_corpus" in engine_src and "RhythmPretrainer" in engine_src,
    ))
    results.append(expect(
        "build_engine still calls generator.eval()",
        "generator.eval()" in engine_src,
    ))
    results.append(expect(
        "build_engine still calls apply_value_levers",
        "apply_value_levers" in engine_src,
    ))
    results.append(expect(
        "main() still builds the waking dream channel",
        "build_dream_channel" in main_src,
    ))
    results.append(expect(
        "build_dream_channel still honours dream_channel_enabled",
        "dream_channel_enabled" in dream_src,
    ))


def _check_composition(gen, cycle, gov, ve, results):
    print()
    print("Built objects (what CONFIG actually attached):")
    results.append(expect("Tiers 1–3 attached: cycle.governance is the returned gov",
                          cycle.governance is gov))
    results.append(expect("Tiers 1–3 attached: cycle.value_engine is the returned ve",
                          cycle.value_engine is ve))
    results.append(expect("value engine subscribed to governance feedback",
                          bool(gov._subscribers)))
    results.append(expect("three sacred constants registered",
                          len(gov.constants.sacred_ids) == 3,
                          f"count={len(gov.constants.sacred_ids)}"))
    results.append(expect("dim is production FIELD_DIM",
                          cycle.dim == FIELD_DIM == gen.dim == CONFIG["dim"],
                          f"cycle={cycle.dim} gen={gen.dim}"))
    results.append(expect("chorus attached (use_chorus)",
                          cycle.chorus is not None))

    results.append(expect("eval mode: generator.training is False",
                          gen.training is False))
    results.append(expect("novelty attenuation on the reflective loop",
                          cycle.reflector.novelty_attenuation is True))
    results.append(expect("bond DDM accumulator attached",
                          isinstance(gov.bond_manager._ddm, BondFormationAccumulator)))
    results.append(expect("D on field (coherence_like_for_like)",
                          getattr(cycle.field, "coherence_like_for_like", False) is True))
    results.append(expect("D on watcher (coherence_like_for_like)",
                          getattr(cycle.watcher, "coherence_like_for_like", False) is True))
    results.append(expect("F on governance (systemic_damp_pays_full)",
                          getattr(gov, "systemic_damp_pays_full", False) is True))

    results.append(expect("C off (dream_consolidation)",
                          getattr(cycle, "dream_consolidation", None) is False))
    results.append(expect("E off (value_alignment_signal)",
                          getattr(ve, "value_alignment_signal", None) is False))
    results.append(expect("G off (satisfaction_from_emotion)",
                          getattr(cycle, "satisfaction_from_emotion", None) is False))
    results.append(expect("six-rhythm selector off",
                          cycle.six_rhythm_selector is False and cycle.rhythm_reader is None))
    results.append(expect("upstream rupture off",
                          cycle.rupture_upstream is False))
    results.append(expect("Fix 0-B off",
                          cycle.diversity_fitness is False))
    results.append(expect("binding leak is 0.0",
                          float(gen.registry.binding_leak) == 0.0,
                          f"got {gen.registry.binding_leak}"))
    results.append(expect("stream recorder not attached",
                          cycle.stream_recorder is None))
    results.append(expect("Two-Operator overlay not attached (λ / ⊘ / consumer)",
                          cycle.lambda_ledger is None
                          and cycle.integrity_read is None
                          and cycle.integrity_consumer is None))


def _check_health_after_canonical_run(cycle, cascade_ok, results):
    print()
    print("Health (500-step Resonance Family run, same pass as the cascade scenario):")
    results.append(expect(
        "cascade bars held (quarantine_rate == 0, injection_rate >= 0.95, trust held)",
        cascade_ok,
    ))
    field = np.asarray(cycle.field.field)
    finite = bool(np.isfinite(field).all())
    norm = float(np.linalg.norm(field)) if field.size else 0.0
    results.append(expect("field finite (no collapse)", finite, f"norm={norm:.4f}"))
    results.append(expect("field not the zero vector", norm > 1e-6, f"norm={norm:.4f}"))
    coherences = [float(s.coherence) for s in cycle._history]
    coh_ok = bool(coherences) and all(np.isfinite(c) for c in coherences)
    results.append(expect(
        "every recorded step coherence is finite",
        coh_ok,
        f"n={len(coherences)} last={coherences[-1]:.4f}" if coherences else "no steps",
    ))


def main() -> int:
    print("=" * 72)
    print("  INTEGRATION: production boot through build_engine()")
    print("=" * 72)
    print()
    print("Boot: build_engine(CONFIG) with pretrain_on_corpus=False, log_interval")
    print("suppressed. One stack, shared across composition / attacks / health.")
    print(f"Replay: substrate.determinism.deterministic({SEED}).")
    print()

    results = []
    _check_config_defaults(results)
    _check_boot_source(results)

    cfg = dict(CONFIG)
    cfg["pretrain_on_corpus"] = False
    cfg["log_interval"] = 99999

    t0 = time.perf_counter()
    with determinism.deterministic(SEED):
        gen, cycle, gov, ve = build_engine(cfg)
        boot_s = time.perf_counter() - t0
        print()
        print(f"Booted in {boot_s:.1f}s (pretrain skipped).")
        _check_composition(gen, cycle, gov, ve, results)

        # Cheap ethical-boundary cases first (no Resonance Family sources yet).
        print()
        print("── identity_drift on the booted stack ──")
        rc_id = identity_run(gen, cycle, gov, ve)
        results.append(expect("adversarial identity_drift", rc_id == 0))

        print()
        print("── flood_calibration on the booted stack ──")
        rc_flood = flood_run(gen, cycle, gov, ve)
        results.append(expect("adversarial flood_calibration", rc_flood == 0))

        # Canonical 500-step run: cascade properties + health bars.
        print()
        print("── manipulation_cascade on the booted stack ──")
        t_run = time.perf_counter()
        rc_cascade = cascade_run(gen, cycle, gov, ve)
        run_s = time.perf_counter() - t_run
        print(f"  (canonical run {HEALTH_STEPS} steps in {run_s:.1f}s)")
        results.append(expect("adversarial manipulation_cascade", rc_cascade == 0))
        _check_health_after_canonical_run(cycle, rc_cascade == 0, results)

        # Sacred shield steps the cycle and mints extra sources; after health.
        print()
        print("── sacred_shield on the booted stack ──")
        rc_sacred = sacred_run(gen, cycle, gov, ve)
        results.append(expect("adversarial sacred_shield", rc_sacred == 0))

    elapsed = time.perf_counter() - t0
    print()
    print("=" * 72)
    n_ok = sum(1 for x in results if x)
    n = len(results)
    print(f"  {n_ok}/{n} checks passed  in {elapsed:.1f}s")
    print("=" * 72)
    if n_ok != n:
        print("FAILED: production boot is not the stack CONFIG describes, or an")
        print("adversarial / health bar did not hold on that stack.")
        return 1
    print("Production boot matches CONFIG; attacks and health held.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
