"""
tests/smoke/stream_vibration_smoke.py

Observe-only vibration gauge (cognition/stream_vibration.py) — the maturity
target's read (BACKLOG "From jitter to vibration").

Verifies:
  1. three synthetic controls separate: white / vibration / lock-in
  2. bounded ring + status() surfacing
  3. observe-only: no loop/agents imports; with vs without is byte-identical
     on the loop (field, emotion, trust, keys, decisions, crystals)

The live S3/S4 baseline is tests.diagnostic.metastability.vibration_probe,
not this smoke.

Run:
    python -m tests.smoke.stream_vibration_smoke
"""

from __future__ import annotations

import ast
import hashlib
import logging
from pathlib import Path

logging.disable(logging.CRITICAL)

import numpy as np

from cognition.stream_vibration import (
    StreamVibrationGauge,
    analyze,
    synthetic_stream,
)
from substrate import determinism
from tests._common import (
    RESONANCE_FAMILY_SOURCES,
    RESONANCE_FAMILY_WEIGHTS,
    build_full_stack,
)

REPO = Path(__file__).resolve().parents[2]


def _expect(name, ok, detail=""):
    mark = "✓" if ok else "✗"
    extra = f"  ({detail})" if detail else ""
    print(f"  {mark} {name}{extra}")
    return bool(ok)


def _digest(cycle, gov, keys, decisions):
    h = hashlib.sha256()
    h.update(cycle.field.field.tobytes())
    trust = {s: round(v.trust_score, 12) for s, v in sorted(gov.trust_ledger.sources.items())}
    h.update(repr((
        cycle.emotion.snapshot(), trust, keys, decisions,
        len(cycle.crystal_store.crystals), len(cycle.attractor.centers),
    )).encode())
    return h.hexdigest()


def _run(track_vibration, seed=11, steps=80):
    import random as _r
    with determinism.deterministic(seed):
        gen, cycle, gov, ve = build_full_stack(track_vibration=track_vibration)
        decisions = []
        gate = cycle._governance_gate

        def counted(*a, **k):
            d, s = gate(*a, **k)
            decisions.append(d.name)
            return d, s

        cycle._governance_gate = counted
        pick = _r.Random(seed)
        sids = list(RESONANCE_FAMILY_SOURCES)
        w = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        keys = []
        for _ in range(steps):
            src = pick.choices(sids, weights=w)[0]
            st = cycle.step(
                pick.choice(RESONANCE_FAMILY_SOURCES[src]),
                source_id=src, origin_type="internal",
            )
            keys.append(st.key)
        return cycle, gov, keys, decisions


def test_synthetics():
    print("[1] Synthetic controls (white / vibration / lock-in)")
    rng = np.random.Generator(np.random.PCG64(0))
    results = []
    expected = (("white", "white"), ("vibration", "vibration"), ("lock-in", "lock-in"))
    reports = {}
    for kind, want in expected:
        X = synthetic_stream(kind, n=256, dim=64, rng=rng)
        r = analyze(X)
        reports[kind] = r
        results.append(_expect(
            f"{kind} reads {want}",
            r.label == want,
            f"got {r.label} sf={r.spectral_flatness:.3f} "
            f"period={r.dominant_period} resid={r.residual_frac}",
        ))
    w, v, k = reports["white"], reports["vibration"], reports["lock-in"]
    results.append(_expect(
        "white spectral flatness is high (>= 0.40)",
        w.spectral_flatness >= 0.40, f"sf={w.spectral_flatness:.3f}",
    ))
    results.append(_expect(
        "white has no dominant that holds",
        (not w.has_dominant) and (not w.dominant_holds),
    ))
    results.append(_expect(
        "vibration spectral flatness is well below white",
        v.spectral_flatness < 0.20 and v.spectral_flatness < w.spectral_flatness,
        f"sf={v.spectral_flatness:.3f} vs white {w.spectral_flatness:.3f}",
    ))
    results.append(_expect(
        "vibration period holds and leftover is real",
        v.dominant_holds and v.residual_frac >= 0.06,
        f"period={v.dominant_period} resid={v.residual_frac:.3f}",
    ))
    results.append(_expect(
        "lock-in leftover is gone (rigid loop)",
        k.residual_frac < 0.06 and k.cycle_distance < 1e-9,
        f"resid={k.residual_frac:.3e} cyc={k.cycle_distance:.3e}",
    ))
    return results


def test_ring_and_status():
    print()
    print("[2] Bounded ring + status surfacing")
    results = []
    gen, cycle, gov, ve = build_full_stack()
    results.append(_expect(
        "default stack attaches the gauge",
        cycle.expression_vibration is not None,
    ))
    n = 80
    for i in range(n):
        cycle.step(["warmup", "pulse", "hold"], source_id="source_samuel",
                   origin_type="internal")
    g = cycle.expression_vibration
    snap = g.snapshot()
    results.append(_expect(
        "ring caps at window",
        snap["samples"] == min(n, g.window) and snap["seen"] == n,
        f"samples={snap['samples']} seen={snap['seen']} window={g.window}",
    ))
    st = cycle.status()
    results.append(_expect(
        "status carries expression_vibration",
        "expression_vibration" in st and st["expression_vibration"]["seen"] == n,
    ))
    _gen_off, cycle_off, _, _ = build_full_stack(track_vibration=False)
    cycle_off.step(["warmup", "no", "gauge"], source_id="source_samuel",
                   origin_type="internal")
    results.append(_expect(
        "opt-out: gauge is None and status has no key",
        cycle_off.expression_vibration is None
        and "expression_vibration" not in cycle_off.status(),
    ))
    # force a read on a short synthetic so snapshot is populated
    rng = np.random.Generator(np.random.PCG64(1))
    X = synthetic_stream("white", n=64, dim=8, rng=rng)
    gauge = StreamVibrationGauge(window=64, interval=8, min_samples=32)
    for v in X:
        gauge.observe(v)
    results.append(_expect(
        "lazy recompute has a label after min_samples",
        gauge.report.label in ("white", "vibration", "lock-in", "unknown"),
        f"label={gauge.report.label}",
    ))
    return results


def test_observe_only():
    print()
    print("[3] Observe-only: import firewall + byte-identical loop")
    results = []
    tree = ast.parse((REPO / "cognition" / "stream_vibration.py").read_text(
        encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    bad = [m for m in mods if m.startswith(("loop", "agents"))]
    results.append(_expect(
        "stream_vibration imports nothing from loop/ or agents/",
        not bad, f"imports={sorted(mods)}",
    ))

    src = (REPO / "loop" / "autonomous_cycle.py").read_text(encoding="utf-8")
    # The cycle may construct, observe, and surface the gauge. It must not
    # branch on the report.
    results.append(_expect(
        "cycle never reads report fields (label / flatness / period)",
        "expression_vibration.report" not in src
        and "expression_vibration.compute_now" not in src
        and "spectral_flatness" not in src,
    ))

    on = _run(True)
    off = _run(False)
    d_on = _digest(*on)
    d_off = _digest(*off)
    results.append(_expect(
        "with vs without: field + emotion + trust + keys + decisions match",
        d_on == d_off, f"on={d_on[:16]} off={d_off[:16]}",
    ))
    np.testing.assert_array_equal(on[0].field.field, off[0].field.field)
    results.append(_expect("with vs without: field bytes identical", True))
    return results


def main():
    print("=" * 72)
    print("  SMOKE: expression vibration gauge (observe-only)")
    print("=" * 72)
    print()
    results = []
    results.extend(test_synthetics())
    results.extend(test_ring_and_status())
    results.extend(test_observe_only())
    print()
    if all(results):
        print("SMOKE PASSED — controls separate; gauge is bounded and observe-only.")
        return 0
    print("SMOKE FAILED")
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
