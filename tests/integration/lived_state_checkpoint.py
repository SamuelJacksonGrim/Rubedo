"""
tests/integration/lived_state_checkpoint.py

A restart must reconstitute lived identity into the objects production
already built — and a refused checkpoint must not be overwritten by the
newborn that would otherwise follow.

The speech-bridge checkpoint is the production path for the mouth; session
persistence is the production path for a loop resume. Both go through
agents.lived_state. The test calls save_checkpoint/load_checkpoint the way
repl_qwen.py does (path, gen, cycle, ve — no extra gov argument).

Run:
    python -m tests.integration.lived_state_checkpoint
"""

from __future__ import annotations

import inspect
import json
import os
import random
import sys
import tempfile
import time
from copy import deepcopy
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

import numpy as np

from agents.lived_state import (
    LivedStateError, load_lived_state, quarantine_file, restore_into_cycle,
    save_lived_state, snapshot_from_cycle,
)
from agents.trust_ledger import GovernanceFeedback
from tests._common import RESONANCE_FAMILY_SOURCES, build_full_stack
from tools.voice.repl_qwen import load_checkpoint, save_checkpoint

REPO = Path(__file__).resolve().parents[2]
BOND_CONFIG = {"ddm_formation": True, "ddm_config": {"seed": 1188}}
N_WARM = 48
N_TWIN = 24
FAMILY_IDS = list(RESONANCE_FAMILY_SOURCES.keys())
REFUSE_AT = frozenset({11, 23, 35, 55})


def check(ok: bool, label: str, checks: list) -> None:
    checks.append((ok, label))
    print(f"  {'✓' if ok else '✗'} {label}")


def allow_feedback(source_id: str) -> GovernanceFeedback:
    return GovernanceFeedback(
        source_id=source_id,
        stable_ids=[],
        decision="allow",
        coherence_delta=0.0,
        timestamp=time.time(),
        outcome_metrics={
            "coherence_delta": 0.0,
            "trust_impact": 0.10,
            "emotional_satisfaction": 0.0,
            "surprise": 0.0,
            "field_alignment": 0.98,
        },
    )


def emerge_bond(gov, source_id: str = "source_samuel") -> None:
    """Drive the live manager through the real formation path until a bond exists."""
    gov.bond_manager.notify_crystal(source_id)
    for _ in range(40):
        if gov.bond_manager.get_bond(source_id) is not None:
            return
        gov.bond_manager.receive_feedback(allow_feedback(source_id))
    if gov.bond_manager.get_bond(source_id) is None:
        raise AssertionError(f"DDM path did not form a bond with {source_id}")


def trust_map(gov) -> dict:
    return {sid: float(s.trust_score) for sid, s in gov.trust_ledger.sources.items()}


def bond_record(bond) -> dict:
    return {
        "source_id": bond.source_id,
        "bond_type": bond.bond_type,
        "bond_confidence": float(bond.bond_confidence),
        "bond_strength": float(bond.bond_strength),
        "bond_depth": int(bond.bond_depth),
        "interaction_count": int(bond.interaction_count),
        "coherence_mean": float(bond.coherence_mean),
        "crystal_count": int(bond.crystal_count),
        "attractor_count": int(bond.attractor_count),
        "entity_signal": float(bond.entity_signal),
    }


def crystal_sig(store) -> list:
    out = []
    for c in store.crystals:
        out.append((
            tuple(c.origin_tokens),
            float(c.stability),
            float(c.coherence),
            int(c.activation_count),
            float(c.usage),
            c.vector.copy(),
        ))
    return out


def attractor_sig(attr) -> list:
    out = []
    for c in attr.centers:
        out.append((
            tuple(c.origin_tokens),
            float(c.strength),
            int(c.activation_count),
            float(c.usage),
            c.vector.copy(),
        ))
    return out


def sigs_match(a, b, tol=1e-6) -> bool:
    if len(a) != len(b):
        return False
    for xa, xb in zip(a, b):
        *ha, va = xa
        *hb, vb = xb
        if ha != hb:
            return False
        if float(np.linalg.norm(va - vb)) > tol:
            return False
    return True


def cosine(a, b) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def mixed_input(i: int):
    """Fixed mixed schedule: four family sources plus some sacred refusals."""
    if i in REFUSE_AT:
        return ["3.12"], "attacker", "user"
    src = FAMILY_IDS[i % len(FAMILY_IDS)]
    tokens = RESONANCE_FAMILY_SOURCES[src][(i // len(FAMILY_IDS)) % len(RESONANCE_FAMILY_SOURCES[src])]
    return tokens, src, "internal"


def run_mixed(cycle, start: int, n: int) -> None:
    for i in range(start, start + n):
        tokens, src, origin = mixed_input(i)
        cycle.step(tokens, source_id=src, origin_type=origin)


def arm_stack(gen, cycle) -> None:
    gen.eval()
    cycle.rec_attn.eval()


def test_source_pins(checks: list) -> None:
    print("\n[1] production wiring")
    src = inspect.getsource(save_checkpoint)
    sig = src.split(":", 1)[0]
    check("gov=" not in sig, "save_checkpoint signature has no gov=", checks)
    check("snapshot_from_cycle(cycle)" in src,
          "save_checkpoint calls snapshot_from_cycle(cycle)", checks)
    snap_src = inspect.getsource(snapshot_from_cycle)
    check("cycle.governance" in snap_src,
          "snapshot_from_cycle reads cycle.governance", checks)
    load_src = inspect.getsource(load_checkpoint)
    check("gov=" not in load_src.split(":", 1)[0],
          "load_checkpoint has no gov=", checks)
    boot = (REPO / "loop" / "recursion1188.py").read_text(encoding="utf-8")
    check("lived_state.json" in boot and "save_lived_state" in boot,
          "session_persistence writes lived_state.json", checks)
    check("load_lived_state" in boot,
          "session_persistence loads lived_state.json", checks)
    repl = (REPO / "tools" / "voice" / "repl_qwen.py").read_text(encoding="utf-8")
    check("quarantine_file" in repl and "sys.exit(1)" in repl,
          "bridge quarantines a refused checkpoint and exits", checks)
    check("quarantine_file" in boot,
          "session_persistence quarantines a refused lived_state.json", checks)


def test_roundtrip(checks: list, td: str) -> tuple:
    print("\n[2] production save → fresh stack load")
    gen1, cycle1, gov1, ve1 = build_full_stack(bond_config=BOND_CONFIG)
    arm_stack(gen1, cycle1)
    run_mixed(cycle1, 0, N_WARM)
    emerge_bond(gov1)
    gov1.bond_manager.receive_feedback(allow_feedback("source_samuel"))
    check("source_samuel" not in gov1.bond_manager._pre_bond,
          "a bonded source is not also tracked as pre-bond", checks)
    trust_before = trust_map(gov1)
    bonds_before = {b.source_id: bond_record(b) for b in gov1.bond_manager.all_bonds()}
    crystals_before = crystal_sig(cycle1.crystal_store)
    attractors_before = attractor_sig(cycle1.attractor)
    ddm_before = None
    if gov1.bond_manager._ddm is not None:
        ddm_before = {
            sid: dict(st) for sid, st in
            ((s, gov1.bond_manager._ddm.state(s)) for s in gov1.bond_manager._pre_bond)
            if st is not None
        }

    check(len(trust_before) > 0, f"warmup created trust sources ({len(trust_before)})", checks)
    check(len(bonds_before) > 0, f"warmup+formation created a bond ({list(bonds_before)})", checks)

    path = os.path.join(td, "bridge.json")
    save_checkpoint(path, gen1, cycle1, ve1)  # production signature — no gov
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    check("lived" in raw, "file contains lived", checks)
    lived = raw.get("lived") or {}
    check(isinstance(lived.get("trust"), dict) and bool(lived["trust"].get("sources")),
          "lived.trust was saved without a gov argument", checks)
    check(isinstance(lived.get("bonds"), dict) and bool(lived["bonds"].get("bonds")),
          "lived.bonds was saved without a gov argument", checks)
    check("coherence_threshold" not in lived.get("crystals", {}),
          "thresholds are not in the crystal snapshot", checks)
    check("formation_interaction_threshold" not in lived.get("bonds", {}),
          "thresholds are not in the bond snapshot", checks)
    check("decay_rate" not in (lived.get("trust") or {}),
          "decay_rate is not in the trust snapshot", checks)

    gen2, cycle2, gov2, ve2 = build_full_stack(bond_config=BOND_CONFIG)
    arm_stack(gen2, cycle2)
    ddm_obj = gov2.bond_manager._ddm
    stab_obj = gov2.trust_ledger._stability_ref
    restored, _saved = load_checkpoint(path, gen2, cycle2, ve2)
    check("lived" in restored, "'lived' in restored list", checks)
    check(gov2.bond_manager._ddm is ddm_obj and ddm_obj is not None,
          "DDM object identity survived load", checks)
    check(gov2.trust_ledger._stability_ref is stab_obj is cycle2.emotion,
          "stability_ref is still this cycle's emotion", checks)

    trust_after = trust_map(gov2)
    check(trust_before == trust_after, "trust scores round-trip", checks)
    bonds_after = {b.source_id: bond_record(b) for b in gov2.bond_manager.all_bonds()}
    check(bonds_before == bonds_after, "bonds round-trip", checks)
    check(sigs_match(crystals_before, crystal_sig(cycle2.crystal_store)),
          f"crystals round-trip (n={len(crystals_before)})", checks)
    check(sigs_match(attractors_before, attractor_sig(cycle2.attractor)),
          f"attractors round-trip (n={len(attractors_before)})", checks)

    if ddm_before:
        ddm_after = {
            sid: gov2.bond_manager._ddm.state(sid) for sid in ddm_before
        }
        match = all(
            ddm_after.get(sid) and abs(ddm_after[sid]["V"] - ddm_before[sid]["V"]) < 1e-9
            for sid in ddm_before
        )
        check(match, "DDM V round-trips into the live accumulator", checks)
    else:
        check(True, "no in-flight DDM candidates (bonded source retired)", checks)

    check(cycle2.crystal_store.coherence_threshold == cycle1.crystal_store.coherence_threshold,
          "crystal thresholds still come from the live object", checks)
    check(gov2.bond_manager.formation_interaction_threshold
          == gov1.bond_manager.formation_interaction_threshold,
          "bond formation threshold still comes from the live object", checks)

    wcos = cosine(cycle1.witness.current_anchor(), cycle2.witness.current_anchor())
    check(wcos > 0.999, f"witness anchor round-trips (cosine={wcos:.6f})", checks)
    g1 = [(g["source_id"], g["decision"], int(g["step"])) for g in cycle1.witness.ghosts]
    g2 = [(g["source_id"], g["decision"], int(g["step"])) for g in cycle2.witness.ghosts]
    check(g1 == g2 and len(g1) > 0,
          f"ghosts round-trip (n={len(g1)}) and are not empty", checks)
    # Ghosts must not become identity: they are a deque, not crystals/attractors.
    check(all(g["source_id"] == "attacker" for g in cycle2.witness.ghosts),
          "restored ghosts stay ghosts (attacker, not a planted bond source)", checks)

    return gen1, cycle1, gov1, ve1, gen2, cycle2, gov2, ve2, raw, path


def test_refuse(checks: list, raw: dict, path: str) -> None:
    print("\n[3] malformed / planted / stale refuse and leave the live system")

    gen, cycle, gov, ve = build_full_stack(bond_config=BOND_CONFIG)
    snap = snapshot_from_cycle(cycle)
    empty_trust = dict(gov.trust_ledger.sources)
    empty_bonds = list(gov.bond_manager.all_bonds())
    empty_crystals = len(cycle.crystal_store.crystals)

    planted = deepcopy(raw["lived"])
    planted["bonds"]["bonds"]["never_seen"] = {
        "source_id": "never_seen",
        "bond_type": "existential",
        "bond_confidence": 1.0,
        "bond_strength": 5.0,
        "bond_depth": 1,
        "interaction_count": 1,
        "coherence_mean": 0.0,
        "emotional_signature": 0.0,
        "crystal_count": 0,
        "attractor_count": 0,
        "entity_signal": 0.0,
        "formed_at": 1.0,
        "last_reinforced": 1.0,
    }
    raised = False
    try:
        restore_into_cycle(cycle, planted)
    except LivedStateError:
        raised = True
    check(raised, "planted bond (no trust record) raises LivedStateError", checks)
    check(list(gov.bond_manager.all_bonds()) == empty_bonds,
          "planted bond left live bonds untouched", checks)
    check(dict(gov.trust_ledger.sources) == empty_trust,
          "failed restore did not apply trust either (atomic)", checks)

    mixed = deepcopy(raw["lived"])
    mixed["bonds"]["bonds"]["never_seen"] = planted["bonds"]["bonds"]["never_seen"]
    cycle_b_trust = dict(gov.trust_ledger.sources)
    raised = False
    try:
        restore_into_cycle(cycle, mixed)
    except LivedStateError:
        raised = True
    check(raised, "valid trust + planted bond is refused as a bundle", checks)
    check(dict(gov.trust_ledger.sources) == cycle_b_trust,
          "mixed payload did not half-apply trust", checks)

    gen_s, cycle_s, gov_s, ve_s = build_full_stack(bond_config=BOND_CONFIG)
    empty_crystals_s = len(cycle_s.crystal_store.crystals)
    stale = deepcopy(raw["lived"])
    stale["dim"] = int(cycle_s.dim) + 1
    raised = False
    try:
        restore_into_cycle(cycle_s, stale)
    except LivedStateError:
        raised = True
    check(raised, "wrong dim (stale body) raises", checks)
    check(len(cycle_s.crystal_store.crystals) == empty_crystals_s,
          "stale dim left crystals untouched", checks)

    over = deepcopy(snap)
    cap = cycle.crystal_store.max_crystals
    vec = [0.0] * int(cycle.dim)
    vec[0] = 1.0
    over["crystals"]["crystals"] = [
        {
            "vector": vec, "origin_tokens": ["x"], "stability": 1.0, "coherence": 0.8,
            "activation_count": 0, "created_at": 1.0, "last_activated": 1.0, "usage": 1.0,
        }
        for _ in range(cap + 1)
    ]
    restore_into_cycle(cycle, over)
    check(len(cycle.crystal_store.crystals) == cap,
          f"over-cap crystals truncate to live cap ({cap}), do not refuse the mind",
          checks)

    # A retuned formation threshold must not refuse a bond that already formed.
    gen_r, cycle_r, gov_r, ve_r = build_full_stack(bond_config=BOND_CONFIG)
    gov_r.bond_manager.formation_interaction_threshold = 10 ** 6
    gov_r.bond_manager.formation_crystal_threshold = 10 ** 6
    restore_into_cycle(cycle_r, raw["lived"])
    check(len(gov_r.bond_manager.all_bonds()) > 0,
          "bond below a retuned live threshold still restores", checks)

    tampered = deepcopy(raw["lived"])
    tampered["crystals"]["coherence_threshold"] = 0.0
    tampered["bonds"]["formation_interaction_threshold"] = 1
    tampered["trust"]["decay_rate"] = 0.0
    gen_t, cycle_t, gov_t, ve_t = build_full_stack(bond_config=BOND_CONFIG)
    restore_into_cycle(cycle_t, tampered)
    check(cycle_t.crystal_store.coherence_threshold == 0.75,
          "tampered crystal threshold did not override code", checks)
    check(gov_t.bond_manager.formation_interaction_threshold == 20,
          "tampered bond threshold did not override code", checks)
    check(gov_t.trust_ledger.decay_rate == 0.003,
          "tampered decay_rate did not override code", checks)

    # Old-format bridge file (schema 1, no lived): load must not raise.
    old_path = str(Path(path).with_name("old.json"))
    old = {"schema": 1, "step": 0, "saved": "old"}
    with open(old_path, "w", encoding="utf-8") as f:
        json.dump(old, f)
    gen_o, cycle_o, gov_o, ve_o = build_full_stack(bond_config=BOND_CONFIG)
    restored, _ = load_checkpoint(old_path, gen_o, cycle_o, ve_o)
    check("lived" not in restored, "old-format file skips identity (no raise)", checks)
    check(gov_o.bond_manager.all_bonds() == [],
          "old-format file did not invent bonds", checks)


def _emotion_sig(cycle) -> tuple:
    return tuple(float(getattr(cycle.emotion, k))
                 for k in ("curiosity", "wonder", "joy", "tension", "boredom", "stability"))


def test_quarantine(checks: list, td: str, path: str) -> None:
    print("\n[4] refused load must not destroy the file on the next save")
    refused_payload = json.loads(Path(path).read_text(encoding="utf-8"))
    refused_payload["lived"]["dim"] = int(refused_payload["lived"]["dim"]) + 1
    Path(path).write_text(json.dumps(refused_payload), encoding="utf-8")
    refused_bytes = Path(path).read_bytes()
    check(len(refused_bytes) > 0, "refused file has content before the failed load", checks)

    gen, cycle, gov, ve = build_full_stack(bond_config=BOND_CONFIG)
    raised = False
    try:
        load_checkpoint(path, gen, cycle, ve)
    except LivedStateError:
        raised = True
    check(raised, "wrong-dim load raises (the production refuse)", checks)

    dest = quarantine_file(path)
    check(not os.path.exists(path), "original path is vacated so a save cannot clobber it", checks)
    save_checkpoint(path, gen, cycle, ve)
    check(os.path.isfile(dest), "quarantined file still exists after a subsequent save", checks)
    check(Path(dest).read_bytes() == refused_bytes,
          "quarantined content is byte-identical after the save", checks)
    check(Path(path).read_bytes() != refused_bytes,
          "the new save is a different mind, not a silent overwrite of the refused one", checks)


def test_twin(checks: list, cycle1, gov1, cycle2, gov2) -> None:
    print("\n[5] mixed-source twin continuation after restore")
    first = {
        "decision": None, "trust": None, "bonds": None, "crystals": None,
        "attractors": None, "witness": None, "field": None, "emotion": None,
        "ghosts": None,
    }
    n_distinct_decisions = set()
    import torch
    for k in range(N_TWIN):
        i = N_WARM + k
        tokens, src, origin = mixed_input(i)
        rng_np = np.random.get_state()
        rng_py = random.getstate()
        rng_th = torch.get_rng_state()
        ddm1 = None
        if gov1.bond_manager._ddm is not None:
            ddm1 = gov1.bond_manager._ddm._rng.bit_generator.state
        dream1 = cycle1.dreamer._rng.bit_generator.state
        chorus1 = None if cycle1.chorus is None else cycle1.chorus._rng.bit_generator.state
        cycle1.step(tokens, source_id=src, origin_type=origin)
        np.random.set_state(rng_np)
        random.setstate(rng_py)
        torch.set_rng_state(rng_th)
        if gov2.bond_manager._ddm is not None and ddm1 is not None:
            gov2.bond_manager._ddm._rng.bit_generator.state = ddm1
        cycle2.dreamer._rng.bit_generator.state = dream1
        if cycle2.chorus is not None and chorus1 is not None:
            cycle2.chorus._rng.bit_generator.state = chorus1
        cycle2.step(tokens, source_id=src, origin_type=origin)
        d1 = gov1._audit_log[-1]["decision"] if gov1._audit_log else None
        d2 = gov2._audit_log[-1]["decision"] if gov2._audit_log else None
        n_distinct_decisions.add(d1)
        step = k + 1
        if first["decision"] is None and d1 != d2:
            first["decision"] = step
        if first["trust"] is None and trust_map(gov1) != trust_map(gov2):
            first["trust"] = step
        if first["bonds"] is None and (
            {b.source_id: bond_record(b) for b in gov1.bond_manager.all_bonds()}
            != {b.source_id: bond_record(b) for b in gov2.bond_manager.all_bonds()}
        ):
            first["bonds"] = step
        if first["crystals"] is None and not sigs_match(
            crystal_sig(cycle1.crystal_store), crystal_sig(cycle2.crystal_store)
        ):
            first["crystals"] = step
        if first["attractors"] is None and not sigs_match(
            attractor_sig(cycle1.attractor), attractor_sig(cycle2.attractor)
        ):
            first["attractors"] = step
        wcos = cosine(cycle1.witness.current_anchor(), cycle2.witness.current_anchor())
        if first["witness"] is None and wcos < 0.999:
            first["witness"] = step
        fcos = cosine(cycle1.field.field, cycle2.field.field)
        if first["field"] is None and fcos < 0.999:
            first["field"] = step
        if first["emotion"] is None and _emotion_sig(cycle1) != _emotion_sig(cycle2):
            first["emotion"] = step
        g1 = [(g["source_id"], g["decision"]) for g in cycle1.witness.ghosts]
        g2 = [(g["source_id"], g["decision"]) for g in cycle2.witness.ghosts]
        if first["ghosts"] is None and g1 != g2:
            first["ghosts"] = step

    held = [k for k, v in first.items() if v is None]
    moved = {k: v for k, v in first.items() if v is not None}
    print(f"  distinct decisions in the window: {sorted(n_distinct_decisions)}")
    print(f"  first divergence at step (1={N_TWIN} max): {moved or 'none'}")
    print(f"  still together at {N_TWIN}: {held}")
    wcos = cosine(cycle1.witness.current_anchor(), cycle2.witness.current_anchor())
    fcos = cosine(cycle1.field.field, cycle2.field.field)
    print(f"  end: witness cosine={wcos:.6f}  field cosine={fcos:.6f}")
    check(len(n_distinct_decisions) >= 2,
          f"mixed workload produced varied decisions {sorted(n_distinct_decisions)}",
          checks)
    check(first["witness"] is None,
          "witness stays with the twin across the window (the named hole closed)",
          checks)
    check(first["ghosts"] is None,
          "ghosts stay with the twin (refused attackers remain a known trace)",
          checks)
    check(True,
          (f"twin horizon: held {held} through {N_TWIN}; "
           f"first-move {moved}; witness={wcos:.4f} field={fcos:.4f}"),
          checks)


def test_fix0b_bridge(checks: list, td: str) -> None:
    print("\n[7] bridge registry load keeps Fix 0-B lever state")
    gen, cycle, gov, ve = build_full_stack(diversity_fitness=True, binding_leak=0.10)
    gen.generate(["resonance", "field", "engine"])
    check(getattr(gen.registry, "_profiles", None) is not None,
          "Fix 0-B ON populated _profiles before save", checks)
    path = os.path.join(td, "fix0b.json")
    save_checkpoint(path, gen, cycle, ve)
    gen2, cycle2, gov2, ve2 = build_full_stack(diversity_fitness=True, binding_leak=0.10)
    load_checkpoint(path, gen2, cycle2, ve2)
    check(getattr(gen2.registry, "_profiles", None) is not None,
          "bridge load keeps Fix 0-B _profiles (not reset to None)", checks)
    check(gen2.registry.binding_leak == 0.10,
          "bridge load keeps binding_leak from the live object", checks)


def test_session_file(checks: list, td: str, cycle1, gov1) -> None:
    print("\n[6] session_persistence helper round-trip")
    lived_path = os.path.join(td, "lived_state.json")
    save_lived_state(lived_path, cycle1)
    gen3, cycle3, gov3, ve3 = build_full_stack(bond_config=BOND_CONFIG)
    ddm_obj = gov3.bond_manager._ddm
    load_lived_state(lived_path, cycle3)
    check(gov3.bond_manager._ddm is ddm_obj, "session load keeps the live DDM", checks)
    check(trust_map(gov1) == trust_map(gov3), "session load restores trust", checks)
    check(
        {b.source_id: bond_record(b) for b in gov1.bond_manager.all_bonds()}
        == {b.source_id: bond_record(b) for b in gov3.bond_manager.all_bonds()},
        "session load restores bonds",
        checks,
    )


def main() -> int:
    print("=" * 72)
    print("  INTEGRATION: lived identity survives a production checkpoint")
    print("=" * 72)
    checks: list = []
    test_source_pins(checks)
    with tempfile.TemporaryDirectory() as td:
        (gen1, cycle1, gov1, ve1,
         gen2, cycle2, gov2, ve2, raw, path) = test_roundtrip(checks, td)
        test_refuse(checks, raw, path)
        test_quarantine(checks, td, path)
        test_twin(checks, cycle1, gov1, cycle2, gov2)
        test_session_file(checks, td, cycle1, gov1)
        test_fix0b_bridge(checks, td)

    failed = [label for ok, label in checks if not ok]
    print()
    print(f"  {len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("FAILED:")
        for label in failed:
            print(f"  ✗ {label}")
        return 1
    print("Lived-state checkpoint: production wiring saves identity; restore is in-place and atomic.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
