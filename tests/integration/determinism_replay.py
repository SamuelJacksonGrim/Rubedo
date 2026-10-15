"""
tests/integration/determinism_replay.py

Contract for substrate/determinism.py (model time + randomness in one place).

  1. Exact replay: two runs in deterministic(seed) match bit for bit (field,
     emotion, trust scores, step keys, governance decisions, crystal / attractor
     counts, registry usage), and a different seed differs.
  2. Cross-process replay: the same run in two fresh interpreters gives the same
     digest (catches anything process-dependent, e.g. str-hash ordering of sets).
  3. Production untouched: outside deterministic(), model time is the real clock
     and generators draw fresh entropy.
  4. Simulated time drives behavior: 30 user-origin steps 0.05 s apart trip the
     flood ceiling (12 per 60 s); the same steps 10 s apart never do.
  5. Guard: no production module reads the wall clock, draws unseeded entropy, or
     mints uuid4 keys except substrate/determinism.py.

Run:
    python -m tests.integration.determinism_replay
"""

import hashlib
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

from substrate import determinism
from tests._common import RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS, build_full_stack

REPO = Path(__file__).resolve().parents[2]


def workload_run(seed, steps=60):
    import random as _r
    with determinism.deterministic(seed):
        gen, cycle, gov, ve = build_full_stack()
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
            st = cycle.step(pick.choice(RESONANCE_FAMILY_SOURCES[src]), source_id=src, origin_type="internal")
            keys.append(st.key)
        trust = {s: round(v.trust_score, 12) for s, v in sorted(gov.trust_ledger.sources.items())}
        usage = sorted((k, round(v.usage, 9)) for k, v in gen.registry.symbols.items())
        return dict(field=cycle.field.field.copy(), emotion=cycle.emotion.snapshot(), trust=trust,
                    keys=keys, decisions=decisions, crystals=len(cycle.crystal_store.crystals),
                    attractors=len(cycle.attractor.centers), usage=usage)


def digest(r):
    h = hashlib.sha256()
    h.update(r["field"].tobytes())
    h.update(repr((r["emotion"], r["trust"], r["keys"], r["decisions"], r["crystals"],
                   r["attractors"], r["usage"])).encode())
    return h.hexdigest()


def flood_count(dt, steps=30):
    with determinism.deterministic(5, dt=dt):
        gen, cycle, gov, ve = build_full_stack()
        hits = 0
        orig = gov.ethical_boundary._is_flooding
        def watch(source_id, origin_type="user"):
            nonlocal hits
            f = orig(source_id, origin_type)
            hits += int(f)
            return f
        gov.ethical_boundary._is_flooding = watch
        for _ in range(steps):
            cycle.step(["signal", "pattern", "hold"], source_id="one_user", origin_type="user")
        return hits


def guard():
    bad = []
    pat = re.compile(r"time\.time\b|time\.monotonic\b|datetime\.(now|utcnow)|default_rng\(\s*\)|uuid\.uuid4")
    for d in ("agents", "substrate", "cognition", "interference", "loop"):
        for p in (REPO / d).rglob("*.py"):
            if p.name == "determinism.py":
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                if pat.search(code):
                    bad.append(f"{p.relative_to(REPO)}:{i}: {line.strip()}")
    return bad


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--digest":
        print(digest(workload_run(int(sys.argv[2]))))
        return

    print("=" * 72)
    print("  GATE: determinism (model time + randomness)")
    print("=" * 72)

    a, b, c = workload_run(11), workload_run(11), workload_run(12)
    assert np.array_equal(a["field"], b["field"]), "same seed: field differs"
    for k in ("emotion", "trust", "keys", "decisions", "crystals", "attractors", "usage"):
        assert a[k] == b[k], f"same seed: {k} differs"
    assert not np.array_equal(a["field"], c["field"]), "different seeds produced identical fields"
    print(f"  replay: identical across 60 steps (decisions {dict(Counter(a['decisions']))}); seed 12 differs")

    env = {"PYTHONUTF8": "1"}
    import os
    env = {**os.environ, **env}
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, "-m", "tests.integration.determinism_replay", "--digest", "11"],
                           cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, r.stderr[-800:]
        outs.append(r.stdout.strip().splitlines()[-1])
    assert outs[0] == outs[1], f"cross-process digests differ: {outs}"
    assert outs[0] == digest(a), "subprocess digest differs from in-process digest"
    print(f"  cross-process: two fresh interpreters agree ({outs[0][:16]}...)")

    assert isinstance(determinism.clock(), determinism.RealClock), "production clock is not real"
    assert abs(determinism.now() - time.time()) < 1.0
    x, y = determinism.make_rng().random(4), determinism.make_rng().random(4)
    assert not np.array_equal(x, y), "production generators are not drawing fresh entropy"
    print("  production: real clock, fresh entropy (deterministic() restored both)")

    fast, slow = flood_count(0.05), flood_count(10.0)
    assert fast > 0 and slow == 0, f"flood under sim time: dt=0.05 -> {fast}, dt=10 -> {slow}"
    print(f"  sim time drives behavior: flood hits {fast} at 0.05 s/step, {slow} at 10 s/step")

    bad = guard()
    assert not bad, "direct wall-clock / entropy / uuid4 in production:\n" + "\n".join(bad)
    print("  guard: model time, entropy and keys only via substrate/determinism.py")
    print("Runs replay exactly in deterministic mode; production behavior unchanged.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
