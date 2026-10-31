"""
tests/diagnostic/metastability/vibration_probe.py

Today's baseline on the vibration gauge: synthetic controls first (the
instrument has to tell white / vibration / lock-in apart), then the
canonical Resonance Family workload at Rubedo's S3 (~500, formation closed)
and first S4 (1000) points.

Stack: build_engine() with the production CONFIG, pretrain skipped (CPU;
the GPU is on the encoder). Witness selector is ON in CONFIG but inert
without pretrain (same as production_boot). Seed 42 under
substrate.determinism. Window 512, trailing-256 also reported at S3 so the
opening walk is not silently inside the read.

    python -m tests.diagnostic.metastability.vibration_probe
    python -m tests.diagnostic.metastability.vibration_probe --steps 500
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path

import numpy as np

logging.disable(logging.CRITICAL)

from cognition.stream_vibration import analyze, synthetic_stream  # noqa: E402
from loop.recursion1188 import CONFIG, build_engine  # noqa: E402
from substrate import determinism  # noqa: E402
from tests._common import (  # noqa: E402
    RESONANCE_FAMILY_SOURCES,
    RESONANCE_FAMILY_WEIGHTS,
)

REPO = Path(__file__).resolve().parents[3]


def _fmt(r):
    def n(x, p=3):
        if x is None:
            return "nan"
        try:
            x = float(x)
        except (TypeError, ValueError):
            return str(x)
        if not np.isfinite(x):
            return "nan"
        return f"{x:.{p}f}"

    return (
        f"label={r.label}  sf={n(r.spectral_flatness)}  "
        f"period={n(r.dominant_period, 2)}  holds={r.dominant_holds}  "
        f"resid={n(r.residual_frac)}  cyc={n(r.cycle_distance)}  "
        f"msd1={n(r.msd_lag1)}  msdP={n(r.msd_at_period)}  "
        f"ratio={n(r.msd_period_ratio)}  cone={n(r.cone_deg, 1)}deg  "
        f"expl={n(r.explained_var)}  n={r.samples}"
    )


def _msd_line(r):
    parts = []
    for lag, val in zip(r.msd_lags, r.msd):
        if np.isfinite(val):
            parts.append(f"{lag}:{val:.3f}")
    return "  ".join(parts)


def run_synthetics(dim=64, n=256, seed=0):
    print("Synthetic controls")
    rng = np.random.Generator(np.random.PCG64(seed))
    out = {}
    for kind in ("white", "vibration", "lock-in"):
        X = synthetic_stream(kind, n=n, dim=dim, rng=rng)
        r = analyze(X)
        out[kind] = r
        print(f"  {kind:10s}  {_fmt(r)}")
        print(f"             msd  {_msd_line(r)}")
    return out


def run_live(steps, s3, s4, seed):
    cfg = dict(CONFIG)
    cfg["pretrain_on_corpus"] = False
    print()
    print(f"Live canonical workload  steps={steps}  seed={seed}  "
          f"dim={cfg['dim']}  pretrain skipped  window=512")
    t0 = time.perf_counter()
    with determinism.deterministic(seed):
        _gen, cycle, _gov, _ve = build_engine(cfg)
        pick = random.Random(seed)
        sids = list(RESONANCE_FAMILY_SOURCES)
        w = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        marks = {}
        for i in range(1, steps + 1):
            src = pick.choices(sids, weights=w)[0]
            cycle.step(
                pick.choice(RESONANCE_FAMILY_SOURCES[src]),
                source_id=src, origin_type="internal",
            )
            if i in (s3, s4) or i == steps:
                g = cycle.expression_vibration
                r = g.compute_now()
                marks[i] = {
                    "report": r,
                    "trailing256": None,
                    "rhythm": cycle.status()["rhythm"],
                    "crystals": len(cycle.crystal_store.crystals),
                    "attractors": len(cycle.attractor.centers),
                    "values": (
                        cycle.value_engine.summary() if cycle.value_engine else {}
                    ),
                }
                if len(g._vecs) >= 256:
                    marks[i]["trailing256"] = analyze(
                        list(g._vecs)[-256:], n_axes=3,
                        window=256, seen=g._seen,
                    )
    elapsed = time.perf_counter() - t0
    print(f"  wall {elapsed:.1f}s  ({elapsed / max(steps, 1) * 1000:.1f} ms/step)")
    return marks


def _print_mark(step, name, mark):
    print()
    print(f"{name}  (step {step}, rhythm={mark['rhythm']}, "
          f"crystals={mark['crystals']}, attractors={mark['attractors']})")
    print(f"  window   {_fmt(mark['report'])}")
    print(f"           msd  {_msd_line(mark['report'])}")
    if mark["trailing256"] is not None:
        print(f"  trail256 {_fmt(mark['trailing256'])}")
        print(f"           msd  {_msd_line(mark['trailing256'])}")
    vs = mark.get("values") or {}
    if vs:
        print(f"  values total={vs.get('total_values', '?')}  "
              f"active={vs.get('active', '?')}  core={vs.get('core', '?')}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=1000)
    p.add_argument("--s3", type=int, default=500)
    p.add_argument("--s4", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--synthetics-only", action="store_true")
    p.add_argument("--save", type=str, default="")
    args = p.parse_args()

    print("=" * 72)
    print("  PROBE: expression vibration gauge — controls + S3/S4 baseline")
    print("=" * 72)
    print()
    syn = run_synthetics()
    if args.synthetics_only:
        return 0

    s4 = args.s4 if args.s4 <= args.steps else args.steps
    s3 = args.s3 if args.s3 <= args.steps else None
    marks = run_live(args.steps, s3, s4, args.seed)
    if s3 in marks:
        _print_mark(s3, "S3 · formation closed (canonical, nearest honest)", marks[s3])
    if s4 in marks and s4 != s3:
        _print_mark(s4, "S4 · first steady-state check", marks[s4])

    if args.save:
        path = Path(args.save)
        blob = {}
        for step, mark in marks.items():
            blob[str(step)] = {
                "report": mark["report"].as_dict(),
                "trailing256": (
                    mark["trailing256"].as_dict() if mark["trailing256"] else None
                ),
                "rhythm": mark["rhythm"],
                "crystals": mark["crystals"],
                "attractors": mark["attractors"],
            }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(blob, indent=2), encoding="utf-8")
        print(f"\n  wrote {path}")

    print()
    print("Controls are the instrument's proof. The live numbers are today's")
    print("baseline, not a lever change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
