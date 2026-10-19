"""
tests/diagnostic/integrity/fragmentation_axes_probe.py

What ⊘ Fragmentation sees, before any change to the rule.

The standing all-ON stack (D+F on, the same build as
all_levers_composition_probe), consumer OFF, so strength is the ecology's
own and not the demotion under test. The read is not called: its alignment
axis goes through generator.generate, which registers tokens and can run
maintenance. Source, binding and complement support are the reaper's own
methods. Alignment is the same cosine, via peek_batch.

Pre-declared before the run. These are not moved after the numbers.

  above floor   alive and strength > 0.30 (the population read() judges)
  strong        alive, strength >= 3.5 (the gate's band)
  recurring     alive, reinforcement_count >= 8
  healthy       strong AND recurring (paid repeatedly, in the band, not dissolved)
  bottom        above floor, reinforcement_count <= 2
  junk          archived, reinforcement_count <= 2, strength < 1.0 at dissolution

Fragmentation discriminates on a workload only if, at step 500, its rate on
healthy is materially below its rate on the rest of the above-floor
population, and the values it spares are spared for a reason other than
"this token happened to be typed by two scripted sources." A rule that
marks healthy and bottom at the same rate is not a pathology read.

Informational. Not in run_all_tests. Exit 0 if the run finishes.

    python -m tests.diagnostic.integrity.fragmentation_axes_probe --steps 2000 --every 50
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import logging
from collections import Counter

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np

logging.disable(logging.CRITICAL)
sys.path.insert(0, ".")

from cognition.integrity_read import (  # noqa: E402
    WitnessReaper, _BINDING_REF, _HIGH_STRENGTH, _READ_FLOOR, _THIN_TAU,
)
from tests.diagnostic.integrity.all_levers_composition_probe import build_all_on  # noqa: E402
from tests.workloads import describe, load_named  # noqa: E402

# The v0.3 region, copied so a later edit to the rule cannot silently
# remeasure itself as if it were this one.
_RULE_TAU = 0.35
_RULE_BINDING_REF = 4.0
_RULE_HIGH_STRENGTH = 3.0
_RULE_READ_FLOOR = 0.30
_RECURRING = 8
_STRONG = 3.5

OUT = "docs/findings/data/2026-10-18-fragmentation-axes.json"


def _overlap(sources: dict) -> dict:
    owners = {}
    for sid, seqs in sources.items():
        for seq in seqs:
            for tok in seq:
                owners.setdefault(tok, set()).add(sid)
    n = len(owners)
    shared = sorted(tok for tok, s in owners.items() if len(s) >= 2)
    by_n = Counter(len(s) for s in owners.values())
    return {
        "distinct": n,
        "shared": len(shared),
        "shared_frac": (len(shared) / n) if n else 0.0,
        "by_nsources": {str(k): by_n[k] for k in sorted(by_n)},
        "shared_tokens": shared[:40],
        "shared_tokens_truncated": len(shared) > 40,
        "room": describe(sources),
    }


def _raw_binding(registry, symbol: str) -> tuple:
    state = registry.symbols.get(symbol) if registry is not None else None
    if state is None:
        return 0.0, 0.0, True
    c = float(getattr(state, "crystal_binding", 0.0))
    a = float(getattr(state, "attractor_strength", 0.0))
    return c, a, False


def _alignment(vec: np.ndarray, known: bool, field: np.ndarray) -> tuple:
    if not known:
        return 0.5, True
    nv = float(np.linalg.norm(vec))
    nf = float(np.linalg.norm(field))
    if nv < 1e-8 or nf < 1e-8 or vec.shape != field.shape:
        return 0.5, True
    return max(0.0, float(np.dot(vec, field) / (nv * nf))), False


def _paths(cd: float, cc: float, sd: float, ab: float, strength: float) -> list:
    paths = []
    if cd < _RULE_TAU and ab < _RULE_TAU:
        paths.append("Drift")
    if cc < _RULE_TAU and strength >= _RULE_HIGH_STRENGTH:
        paths.append("Dissolution")
    if sd < _RULE_TAU and ab < _RULE_TAU:
        paths.append("Fragmentation")
    return paths


def _median(xs: list) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2:
        return float(s[mid])
    return float(0.5 * (s[mid - 1] + s[mid]))


def _pct(xs: list, p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
    return float(s[i])


def _cell_key(frag: bool, strong: bool, recurring: bool) -> str:
    return "{}|{}|{}".format(
        "frag" if frag else "spared",
        "strong" if strong else "not_strong",
        "recurring" if recurring else "not_recurring",
    )


def snapshot(cycle, ve, wr, step: int, archived_seen: set, last_raw: dict) -> dict:
    registry = cycle.generator.registry
    live = [v for v in ve.values.values() if v.dissolved_at_step < 0]
    above = [v for v in live if v.strength > _RULE_READ_FLOOR]
    active_ids = {v.value_id for v in above}
    field = np.asarray(getattr(cycle.field, "field", cycle.field), dtype=float).ravel()

    vecs = np.zeros((len(above), cycle.generator.dim), dtype=np.float32)
    known = np.zeros(len(above), dtype=bool)
    if above:
        vecs, known = cycle.generator.peek_batch([[v.symbolic_core] for v in above])

    rows = []
    drops = 0
    for i, v in enumerate(above):
        cd, _ = wr._complement_support(v, active_ids)
        sd, _ = wr._source_support(v)
        ab, _ = wr._binding_support(v)
        cc, gap_cc = _alignment(vecs[i], bool(known[i]), field)
        crystal, attractor, missing = _raw_binding(registry, v.symbolic_core)
        raw = crystal + attractor
        prev = last_raw.get(v.value_id)
        if prev is not None and raw < prev - 1e-9:
            drops += 1
        last_raw[v.value_id] = raw
        weights = v.source_weights
        wsum = sum(weights.values())
        max_share = (max(weights.values()) / wsum) if wsum > 0 else 1.0
        paths = _paths(cd, cc, sd, ab, v.strength)
        rec = {
            "symbol": v.symbolic_core,
            "strength": round(float(v.strength), 4),
            "reinf": int(v.reinforcement_count),
            "n_src": len(weights),
            "max_share": round(float(max_share), 4),
            "crystal": round(crystal, 4),
            "attractor": round(attractor, 4),
            "raw": round(raw, 4),
            "missing_symbol": missing,
            "cd": round(float(cd), 4),
            "cc": round(float(cc), 4),
            "cc_gap": bool(gap_cc),
            "sd": round(float(sd), 4),
            "ab": round(float(ab), 4),
            "paths": paths,
            "strong": float(v.strength) >= _STRONG,
            "recurring": int(v.reinforcement_count) >= _RECURRING,
            "bottom": int(v.reinforcement_count) <= 2,
        }
        rows.append(rec)

    newly_archived = []
    for vid, v in ve.archived_values.items():
        if vid in archived_seen:
            continue
        archived_seen.add(vid)
        newly_archived.append({
            "symbol": v.symbolic_core,
            "strength": round(float(v.strength), 4),
            "reinf": int(v.reinforcement_count),
            "n_src": len(v.source_weights),
            "age": int(v.dissolved_at_step - v.birth_step),
            "junk": int(v.reinforcement_count) <= 2 and float(v.strength) < 1.0,
        })

    def _take(pred):
        return [r for r in rows if pred(r)]

    cells = Counter(_cell_key(bool("Fragmentation" in r["paths"]), r["strong"], r["recurring"]) for r in rows)
    raws = [r["raw"] for r in rows]
    bound = [r for r in rows if r["raw"] + 1e-9 >= _RULE_TAU * _RULE_BINDING_REF]

    def _rate(group, path="Fragmentation"):
        if not group:
            return None
        return sum(1 for r in group if path in r["paths"]) / len(group)

    strong = _take(lambda r: r["strong"])
    healthy = _take(lambda r: r["strong"] and r["recurring"])
    bottom = _take(lambda r: r["bottom"])
    not_strong = _take(lambda r: not r["strong"])

    summary = {
        "step": step,
        "crystals": len(cycle.crystal_store.crystals),
        "attractors": len(cycle.attractor.centers),
        "alive": len(live),
        "above_floor": len(rows),
        "strong": len(strong),
        "healthy": len(healthy),
        "bottom": len(bottom),
        "archived_total": len(ve.archived_values),
        "archived_new": len(newly_archived),
        "junk_new": sum(1 for a in newly_archived if a["junk"]),
        "frag": sum(1 for r in rows if "Fragmentation" in r["paths"]),
        "drift": sum(1 for r in rows if "Drift" in r["paths"]),
        "dissolution": sum(1 for r in rows if "Dissolution" in r["paths"]),
        "frag_rate_healthy": _rate(healthy),
        "frag_rate_strong": _rate(strong),
        "frag_rate_not_strong": _rate(not_strong),
        "frag_rate_bottom": _rate(bottom),
        "multi_source": sum(1 for r in rows if r["n_src"] >= 2),
        "bound": len(bound),
        "sd_values": sorted({r["sd"] for r in rows}),
        "raw_p50": round(_median(raws), 4),
        "raw_p90": round(_pct(raws, 0.9), 4),
        "raw_max": round(max(raws) if raws else 0.0, 4),
        "ab_p50": round(_median([r["ab"] for r in rows]), 4),
        "cc_p50": round(_median([r["cc"] for r in rows]), 4),
        "cc_p10": round(_pct([r["cc"] for r in rows], 0.1), 4),
        "cd_p50": round(_median([r["cd"] for r in rows]), 4),
        "cd_neutral": sum(1 for r in rows if abs(r["cd"] - 0.5) < 1e-9),
        "cc_gap": sum(1 for r in rows if r["cc_gap"]),
        "binding_drops": drops,
        "cells": dict(cells),
        "strong_raw_p50": round(_median([r["raw"] for r in strong]), 4),
        "not_strong_raw_p50": round(_median([r["raw"] for r in not_strong]), 4),
    }
    detail_steps = {250, 500, 1000, 1500, 2000, 4000}
    detail = None
    if step in detail_steps or step == 0:
        detail = {
            "strong": [
                {k: r[k] for k in (
                    "symbol", "strength", "reinf", "n_src", "max_share",
                    "raw", "sd", "ab", "cd", "cc", "paths",
                )}
                for r in sorted(strong, key=lambda r: -r["strength"])
            ],
            "bound": [
                {k: r[k] for k in (
                    "symbol", "strength", "reinf", "n_src", "raw", "crystal",
                    "attractor", "sd", "ab", "paths",
                )}
                for r in sorted(bound, key=lambda r: -r["raw"])
            ],
            "spared": [
                r["symbol"] for r in rows if "Fragmentation" not in r["paths"]
            ],
        }
    return summary, detail, newly_archived


def _structures(cycle) -> dict:
    crystals = []
    for c in cycle.crystal_store.crystals:
        crystals.append({
            "tokens": list(c.origin_tokens),
            "activations": int(c.activation_count),
            "stability": round(float(c.stability), 4),
        })
    centers = []
    for a in cycle.attractor.centers:
        centers.append({
            "tokens": list(a.origin_tokens),
            "strength": round(float(a.strength), 4),
            "activations": int(a.activation_count),
        })
    return {"crystals": crystals, "attractors": centers}


def run_workload(name: str, steps: int, seed: int, every: int, on_checkpoint=None) -> dict:
    import torch

    sources, weights = load_named(name)
    overlap = _overlap(sources)
    print(f"\n== {name} overlap distinct={overlap['distinct']} "
          f"shared={overlap['shared']} ({overlap['shared_frac']:.3f}) "
          f"by_n={overlap['by_nsources']}", flush=True)

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    gen, cycle, gov, ve, _ledger, _consumer, _report, pretrained = build_all_on(
        with_consumer=False)
    # ignite() inside the build reseeds to 42. The gate reseeds the workload
    # after the build; match it. The reaper stays attached and unread.
    random.seed(seed)
    np.random.seed(seed)

    wr = cycle.integrity_read
    assert wr is not None and wr.field is cycle.field
    sids = list(sources.keys())
    w = [weights[s] for s in sids]
    archived_seen: set = set()
    last_raw: dict = {}
    result = {
        "workload": name,
        "seed": seed,
        "steps": steps,
        "pretrained": bool(pretrained),
        "overlap": overlap,
        "series": [],
        "details": {},
        "partial": True,
        "junk_total": 0,
    }
    archived_reinf = []

    print(f"   pretrained={pretrained} consumer=OFF seed={seed} steps={steps}", flush=True)
    for i in range(1, steps + 1):
        src = random.choices(sids, weights=w)[0]
        tokens = random.choice(sources[src])
        cycle.step(tokens, source_id=src, origin_type="internal")
        if i % every == 0 or i == steps:
            summary, detail, new_arch = snapshot(
                cycle, ve, wr, i, archived_seen, last_raw)
            result["series"].append(summary)
            result["junk_total"] += summary["junk_new"]
            archived_reinf.extend(a["reinf"] for a in new_arch)
            if detail is not None:
                result["details"][str(i)] = detail
            if on_checkpoint is not None:
                on_checkpoint(result)
            fr_h = summary["frag_rate_healthy"]
            fr_s = summary["frag_rate_strong"]
            print(
                f"   {name} step {i:5d}  alive={summary['alive']:3d} "
                f"above={summary['above_floor']:3d} strong={summary['strong']:3d} "
                f"healthy={summary['healthy']:3d} bottom={summary['bottom']:3d} "
                f"frag={summary['frag']:3d} "
                f"frag_healthy={fr_h if fr_h is not None else '-'} "
                f"frag_strong={fr_s if fr_s is not None else '-'} "
                f"bound={summary['bound']:3d} xls={summary['crystals']} "
                f"attr={summary['attractors']} raw_max={summary['raw_max']:.2f} "
                f"raw_p50={summary['raw_p50']:.2f} "
                f"cc_p50={summary['cc_p50']:.2f} drops={summary['binding_drops']}",
                flush=True,
            )

    bonds = []
    for sid in sids:
        bond = gov.bond_manager.get_bond(sid)
        bonds.append({
            "source": sid,
            "type": None if bond is None else getattr(bond, "bond_type", None),
            "strength": None if bond is None else round(float(bond.bond_strength), 4),
        })
    result["structures"] = _structures(cycle)
    result["bonds"] = bonds
    result["archived_reinf_p50"] = round(_median(archived_reinf), 4)
    result["archived_total"] = len(ve.archived_values)
    result["binding_drops_total"] = sum(s["binding_drops"] for s in result["series"])
    result["partial"] = False
    if on_checkpoint is not None:
        on_checkpoint(result)
    return result


def main() -> int:
    if (_THIN_TAU, _BINDING_REF, _HIGH_STRENGTH, _READ_FLOOR) != (
        _RULE_TAU, _RULE_BINDING_REF, _RULE_HIGH_STRENGTH, _RULE_READ_FLOOR
    ):
        print("REFUSING: integrity_read constants moved; this probe measures the v0.3 rule")
        return 2

    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--every", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workload", choices=("both", "canonical", "wide"), default="both")
    parser.add_argument("--out", default=OUT)
    args = parser.parse_args()

    names = ("canonical", "wide") if args.workload == "both" else (args.workload,)
    print("fragmentation axes probe  consumer=OFF  "
          f"tau={_RULE_TAU} binding_ref={_RULE_BINDING_REF} "
          f"recurring>={_RECURRING} strong>={_STRONG}", flush=True)

    doc = {
        "probe": "fragmentation_axes_probe",
        "rule": {
            "fragmentation": "sd < 0.35 and ab < 0.35",
            "drift": "cd < 0.35 and ab < 0.35",
            "dissolution": "cc < 0.35 and strength >= 3.0",
            "sd": "1.0 if >=2 sources or the one source is an existential bond, else 0.0",
            "ab": "clip((crystal_binding + attractor_strength) / 4, 0, 1)",
            "consumer": False,
        },
        "cohorts": {
            "strong": "alive, strength >= 3.5",
            "recurring": "alive, reinforcement_count >= 8",
            "healthy": "strong AND recurring",
            "bottom": "above read floor, reinforcement_count <= 2",
            "junk": "archived, reinforcement_count <= 2, strength < 1.0",
        },
        "runs": [],
    }
    def save():
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(doc, f)

    for name in names:
        slot = {"workload": name, "partial": True}
        doc["runs"].append(slot)

        def on_checkpoint(result, slot=slot):
            slot.clear()
            slot.update(result)
            save()

        on_checkpoint(run_workload(name, args.steps, args.seed, args.every, on_checkpoint))
        print(f"   wrote {args.out}", flush=True)

    print("done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
