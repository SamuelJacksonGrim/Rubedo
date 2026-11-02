"""
tests/integration/lived_state_sweep.py

A checkpoint is an input to identity, and Python's json accepts NaN and Infinity,
so a file can carry them. Field-by-field checks only find the fields someone
thought of. This walks EVERY path in a real warmed snapshot and corrupts it, one
at a time: NaN, inf, -inf, 1e30, -1, the wrong type, and the key removed.

Each variant goes through JSON as a real file does, then decode and apply on a
live stack. It must end one of two ways:
  refused: LivedStateError, live state byte-identical to before; or
  accepted: every float finite, every vector within VECTOR_MAX_ABS, and the
            system steps without an exception.
Anything else fails: a foreign exception, non-finite values in live state, an
exception during apply (a half-restored mind), a step that crashes.

Paths are reduced to templates (list indices become [*]); the LAST element of a
list is the one corrupted, because restore keeps the tail of a capped window.

Run:
    python -m tests.integration.lived_state_sweep
"""

from __future__ import annotations

import json
import math
import os
import sys
from copy import deepcopy

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

from agents.lived_state import (
    LivedStateError, VECTOR_MAX_ABS, apply_staged, decode_from_cycle,
    restore_into_cycle, snapshot_from_cycle,
)
from agents.manipulation_resistance import ManipulationSignal
from tests._common import build_full_stack
from tests.integration.lived_state_checkpoint import (
    BOND_CONFIG, N_WARM, allow_feedback, arm_stack, emerge_bond, mixed_input, run_mixed,
)

NAN, INF = float("nan"), float("inf")
VARIANTS = [
    ("nan", NAN), ("inf", INF), ("-inf", -INF), ("1e30", 1e30), ("-1", -1),
    ("str", "x"), ("null", None), ("bool", True), ("list", [1, [2]]), ("dict", {"a": 1}),
]
REMOVED = object()
# The sections a warmed stack must have populated, or the sweep isn't covering them.
MUST_COVER = (
    "trust.sources.source_samuel.trust_score", "bonds.bonds.source_samuel.bond_strength",
    "bonds.ddm.rng.state.state", "crystals.crystals[*].vector[*]", "attractors.centers[*].vector[*]",
    "witness.anchor[*]", "witness.ghosts[*].vec[*]", "emotion.joy", "emotion.step", "field.field[*]",
    "field.history[*][*]", "attention.history[*][*]", "echo.weights[*]", "watcher.history[*][*]",
    "manipulation.velocities[*]", "dependency.window[*]", "pending.pending_signals[*].severity",
    "pending.pending_signals[*].evidence.x", "dreamer_rng.state.state", "chorus_rng.state.inc",
)


def templates(node, path=(), label=""):
    """Yield (template, concrete path) once per template, for containers and leaves alike."""
    seen = set()

    def walk(n, p, t):
        if p and t not in seen:
            seen.add(t)
            yield t, p
        if isinstance(n, dict):
            for k, v in n.items():
                yield from walk(v, p + (k,), f"{t}.{k}" if t else str(k))
        elif isinstance(n, list) and n:
            yield from walk(n[-1], p + (len(n) - 1,), f"{t}[*]")

    yield from walk(node, path, label)


def mutated(clean, path, value):
    d = deepcopy(clean)
    cur = d
    for p in path[:-1]:
        cur = cur[p]
    if value is REMOVED:
        if isinstance(cur, list):
            del cur[path[-1]]
        else:
            del cur[path[-1]]
    else:
        cur[path[-1]] = value
    return d


def bad_numbers(node, dim, path="") -> str:
    """The first non-finite float or oversized vector in live state, or ''."""
    if isinstance(node, dict):
        for k, v in node.items():
            r = bad_numbers(v, dim, f"{path}.{k}")
            if r:
                return r
    elif isinstance(node, list):
        if len(node) == dim and node and all(isinstance(x, float) for x in node):
            if any(abs(x) > VECTOR_MAX_ABS for x in node if math.isfinite(x)):
                return f"oversized vector at {path}"
        for i, v in enumerate(node):
            r = bad_numbers(v, dim, f"{path}[{i}]")
            if r:
                return r
    elif isinstance(node, float) and not math.isfinite(node):
        return f"non-finite at {path}"
    return ""


def warmed_snapshot(cycle, gov):
    """A real snapshot with every section populated. Crystals rarely form this early and pending signals are
    consumed by the next arbitrate, so one of each is added through the real restore path."""
    run_mixed(cycle, 0, N_WARM)
    emerge_bond(gov)
    gov.bond_manager.receive_feedback(allow_feedback("source_samuel"))
    gov._pending_signals.append(ManipulationSignal(
        detector=gov._pending_signals[0].detector if gov._pending_signals else "velocity_spike",
        severity=0.5, source_id="source_samuel", evidence={"x": 1.0}, timestamp=1.0,
    ))
    snap = json.loads(json.dumps(snapshot_from_cycle(cycle)))
    if not snap["crystals"]["crystals"]:
        center = snap["attractors"]["centers"][0]
        snap["crystals"]["crystals"].append({
            "vector": center["vector"], "origin_tokens": center["origin_tokens"], "stability": 1.0,
            "coherence": 0.9, "activation_count": 1, "created_at": 1.0, "last_activated": 1.0, "usage": 1.0,
        })
    restore_into_cycle(cycle, snap)
    return json.loads(json.dumps(snapshot_from_cycle(cycle)))


def main() -> int:
    gen, cycle, gov, _ve = build_full_stack(bond_config=BOND_CONFIG)
    arm_stack(gen, cycle)
    clean = warmed_snapshot(cycle, gov)
    dim = int(cycle.dim)
    paths = list(templates(clean))
    names = {t for t, _ in paths}
    missing = [m for m in MUST_COVER if m not in names]

    tokens, src, origin = mixed_input(0)
    failures, refused, accepted = [], 0, 0
    baseline = json.dumps(clean, sort_keys=True)
    for template, path in paths:
        for label, value in VARIANTS + [("removed", REMOVED)]:
            payload = json.loads(json.dumps(mutated(clean, path, value)))
            try:
                staged = decode_from_cycle(cycle, payload)
            except LivedStateError:
                refused += 1
                if json.dumps(json.loads(json.dumps(snapshot_from_cycle(cycle))), sort_keys=True) != baseline:
                    failures.append(f"{template} {label}: refused but live state changed")
                    restore_into_cycle(cycle, clean)
                continue
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{template} {label}: foreign {type(exc).__name__} at decode: {str(exc)[:60]}")
                continue
            accepted += 1
            try:
                apply_staged(staged)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{template} {label}: {type(exc).__name__} DURING APPLY: {str(exc)[:60]}")
                restore_into_cycle(cycle, clean)
                continue
            try:
                bad = bad_numbers(json.loads(json.dumps(snapshot_from_cycle(cycle))), dim)
                if bad:
                    failures.append(f"{template} {label}: accepted, {bad}")
                else:
                    cycle.step(tokens, source_id=src, origin_type=origin)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{template} {label}: accepted, then {type(exc).__name__}: {str(exc)[:60]}")
            restore_into_cycle(cycle, clean)
            baseline = json.dumps(json.loads(json.dumps(snapshot_from_cycle(cycle))), sort_keys=True)

    total = refused + accepted
    print(f"swept {len(paths)} paths, {total} variants: {refused} refused, {accepted} accepted harmlessly-or-not")
    if missing:
        print(f"  ✗ not covered (section empty in the warmed snapshot): {missing}")
    print(f"  {'✓' if not failures else '✗'} {len(failures)} failures")
    for line in failures[:40]:
        print(f"      {line}")
    if len(failures) > 40:
        print(f"      ... {len(failures) - 40} more")
    if failures or missing:
        return 1
    print("Lived-state sweep: every corrupted path was refused cleanly or left the system finite and stepping.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
