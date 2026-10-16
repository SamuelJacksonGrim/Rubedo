"""
tests/integration/wide_workload.py

The opt-in wide room is a deterministic partition of the corpus holdout:
same four source ids, same weights, every token unchanged by canonicalization.
Building it does not draw from the replay RNGs. The canonical room is still
the object the gates import.

    python -m tests.integration.wide_workload
"""

from __future__ import annotations

import hashlib
import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from substrate import determinism
from tests._common import RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS
from tests.workloads import SOURCE_IDS, describe, load_named, wide_sources
from training.corpus import HOLDOUT_PATH, load_corpus

REPO = Path(__file__).resolve().parents[2]


def _digest(sources) -> str:
    h = hashlib.sha256()
    for sid, seqs in sources.items():
        h.update(sid.encode())
        for seq in seqs:
            h.update(("\0".join(seq) + "\n").encode())
    return h.hexdigest()


def _np_state_equal(a, b) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
            if not np.array_equal(x, y):
                return False
        elif x != y:
            return False
    return True


def _draws(sources, weights, seed, n):
    sids = list(sources)
    w = [weights[s] for s in sids]
    pick = random.Random(seed)
    out = []
    for _ in range(n):
        src = pick.choices(sids, weights=w)[0]
        out.append((src, tuple(pick.choice(sources[src]))))
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--digest"]:
        print(_digest(wide_sources()))
        return 0

    print("=" * 72)
    print("  GATE: wide workload (opt-in room; canonical object untouched)")
    print("=" * 72)

    # Canonical tripwire. The phrases themselves stay the gate's object.
    canon_src, canon_w = load_named("canonical")
    assert canon_src is RESONANCE_FAMILY_SOURCES
    assert canon_w is RESONANCE_FAMILY_WEIGHTS
    assert list(canon_src) == list(SOURCE_IDS)
    assert canon_src["source_samuel"][0] == ["identity", "continuity", "witness"]
    canon_tokens = {t for seqs in canon_src.values() for seq in seqs for t in seq}
    assert len(canon_tokens) == 46, len(canon_tokens)
    canon_hhi = sum(v * v for v in canon_w.values())
    assert abs(canon_hhi - 0.285) < 1e-12, canon_hhi

    wide_sources.cache_clear()
    with determinism.deterministic(7):
        py_before = random.getstate()
        np_before = np.random.get_state()
        sources, weights = load_named("wide")
        assert random.getstate() == py_before, "wide build drew from random"
        assert _np_state_equal(np.random.get_state(), np_before), "wide build drew from numpy"
    assert weights == RESONANCE_FAMILY_WEIGHTS
    assert weights is not RESONANCE_FAMILY_WEIGHTS
    assert abs(sum(v * v for v in weights.values()) - canon_hhi) < 1e-12

    info = describe(sources)
    hold = load_corpus(HOLDOUT_PATH)
    assert info["sequences"] == len(hold), info
    assert info["distinct_tokens"] >= 400, info
    counts = list(info["per_source"].values())
    assert max(counts) - min(counts) <= 2, counts
    assert Counter(tuple(rec["tokens"]) for rec in hold) == Counter(
        tuple(seq) for seqs in sources.values() for seq in seqs
    ), "wide room is not a partition of the holdout"
    print(f"  holdout partition: {info['sequences']} sequences, "
          f"{info['distinct_tokens']} distinct tokens, per source {info['per_source']}")

    wide_sources.cache_clear()
    again, _w = load_named("wide")
    assert _digest(sources) == _digest(again)

    assert _draws(sources, weights, 42, 300) == _draws(again, weights, 42, 300)
    # Canonical draws stay inside the canonical lists (the probe's default path).
    canon_phrases = {tuple(seq) for seqs in canon_src.values() for seq in seqs}
    canon_draw = _draws(canon_src, canon_w, 42, 50)
    assert all(phrase in canon_phrases for _src, phrase in canon_draw)

    # Witness-phrase mix is the probe's, and it has to keep working on this room.
    from tests.diagnostic.integrity.value_fixes_probe import _pick_tokens
    from tests.diagnostic.integrity.witness_composition_gate import WITNESS_PHRASES

    pick = random.Random(0)
    kinds = []
    for _ in range(2000):
        toks, kind = _pick_tokens(pick, "B", SOURCE_IDS[0], sources)
        kinds.append(kind)
        if kind == "witness":
            assert toks in WITNESS_PHRASES
        else:
            assert toks in sources[SOURCE_IDS[0]]
    frac = kinds.count("witness") / len(kinds)
    assert 0.16 <= frac <= 0.24, frac
    pick = random.Random(1)
    for _ in range(200):
        toks, kind = _pick_tokens(pick, "A", SOURCE_IDS[0], sources)
        assert kind == "canonical" and toks in sources[SOURCE_IDS[0]]
    print(f"  witness mix on wide: {frac:.3f} of steps are witness phrases (kind B)")

    env = {**os.environ, "PYTHONUTF8": "1"}
    digests = []
    for seed_env in ("0", "1"):
        env["PYTHONHASHSEED"] = seed_env
        r = subprocess.run(
            [sys.executable, "-m", "tests.integration.wide_workload", "--digest"],
            cwd=REPO, env=env, capture_output=True, text=True, timeout=120,
        )
        assert r.returncode == 0, r.stderr[-800:]
        digests.append(r.stdout.strip().splitlines()[-1])
    assert digests[0] == digests[1] == _digest(sources), digests
    print(f"  cross-process: two hash seeds agree ({digests[0][:16]}...)")
    print("  PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"  FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
