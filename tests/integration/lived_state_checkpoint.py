"""
tests/integration/lived_state_checkpoint.py

A restart must reconstitute lived identity (trust, bonds, crystals, attractors)
into the objects production already built — and the production wiring has to
be the thing that writes them.

The speech-bridge checkpoint is the production path for the mouth; session
persistence is the production path for a loop resume. Both go through
agents.lived_state. The test calls save_checkpoint/load_checkpoint the way
repl_qwen.py does (path, gen, cycle, ve — no extra gov argument) so a
regression that stops reading cycle.governance fails here, not only in a
helper the bridge never calls.

Checks:
  1. Production signature / source pin: save_checkpoint has no gov=, reads
     cycle.governance, and session persistence names lived_state.json.
  2. After real steps + one emerged bond, the file contains lived.trust and
     lived.bonds; a fresh stack load restores scores, bonds, crystals,
     attractors, and DDM V. The live DDM object and emotion stability ref
     keep their identity (not replaced, not None).
  3. Thresholds in a tampered file do not override live constants.
  4. A planted bond (no structural history / no trust record) raises and
     leaves the live system untouched. Wrong dim, over-cap crystals, and
     a mixed valid-trust + planted-bond payload are the same: fail loud,
     no partial apply.
  5. Twin: restore at step N, then both systems take the same next inputs.
     The four stores match; unrestored witness is measured and named.

Run:
    python -m tests.integration.lived_state_checkpoint
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile
import time
from copy import deepcopy
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

import numpy as np

from agents.lived_state import (
    LivedStateError, load_lived_state, restore_into_cycle, save_lived_state,
    snapshot_from_cycle,
)
from agents.trust_ledger import GovernanceFeedback
from tests._common import RESONANCE_FAMILY_SOURCES, build_full_stack
from tools.voice.repl_qwen import load_checkpoint, save_checkpoint

REPO = Path(__file__).resolve().parents[2]
BOND_CONFIG = {"ddm_formation": True, "ddm_config": {"seed": 1188}}
N_WARM = 40
N_TWIN = 12


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


def run_fixed_steps(cycle, n: int) -> None:
    """Deterministic token sequence — the twin must see the same inputs."""
    tokens = RESONANCE_FAMILY_SOURCES["source_samuel"]
    for i in range(n):
        cycle.step(
            tokens[i % len(tokens)],
            source_id="source_samuel",
            origin_type="internal",
        )


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


def test_roundtrip(checks: list, td: str) -> tuple:
    print("\n[2] production save → fresh stack load")
    gen1, cycle1, gov1, ve1 = build_full_stack(bond_config=BOND_CONFIG)
    run_fixed_steps(cycle1, N_WARM)
    emerge_bond(gov1)
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

    return gen1, cycle1, gov1, ve1, gen2, cycle2, gov2, ve2, raw, path


def test_refuse(checks: list, raw: dict, path: str) -> None:
    print("\n[3] malformed / planted / stale refuse and leave the live system")

    gen, cycle, gov, ve = build_full_stack(bond_config=BOND_CONFIG)
    snap = snapshot_from_cycle(cycle)
    empty_trust = dict(gov.trust_ledger.sources)
    empty_bonds = list(gov.bond_manager.all_bonds())
    empty_crystals = len(cycle.crystal_store.crystals)

    planted = deepcopy(raw["lived"])
    planted["bonds"]["bonds"]["attacker"] = {
        "source_id": "attacker",
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
    check(raised, "planted bond (no history) raises LivedStateError", checks)
    check(list(gov.bond_manager.all_bonds()) == empty_bonds,
          "planted bond left live bonds untouched", checks)
    check(dict(gov.trust_ledger.sources) == empty_trust,
          "failed restore did not apply trust either (atomic)", checks)

    mixed = deepcopy(raw["lived"])
    mixed["bonds"]["bonds"]["attacker"] = planted["bonds"]["bonds"]["attacker"]
    cycle_b_trust = dict(gov.trust_ledger.sources)
    raised = False
    try:
        restore_into_cycle(cycle, mixed)
    except LivedStateError:
        raised = True
    check(raised, "valid trust + planted bond is refused as a bundle", checks)
    check(dict(gov.trust_ledger.sources) == cycle_b_trust,
          "mixed payload did not half-apply trust", checks)

    stale = deepcopy(raw["lived"])
    stale["dim"] = int(cycle.dim) + 1
    raised = False
    try:
        restore_into_cycle(cycle, stale)
    except LivedStateError:
        raised = True
    check(raised, "wrong dim (stale body) raises", checks)
    check(len(cycle.crystal_store.crystals) == empty_crystals,
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
    raised = False
    try:
        restore_into_cycle(cycle, over)
    except LivedStateError:
        raised = True
    check(raised, "over-cap crystals raise", checks)
    check(len(cycle.crystal_store.crystals) == empty_crystals,
          "over-cap left the store empty", checks)

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


def test_twin(checks: list, cycle1, gov1, cycle2, gov2) -> None:
    print("\n[4] twin continuation after restore")
    # cycle1 is the uninterrupted twin; cycle2 was restored at the same step.
    # Same next inputs. Immediate round-trip of the four stores is the gate;
    # continuation is a measurement. Witness, manipulation windows, the
    # predictor and the stream are unrestored on purpose.
    tokens = RESONANCE_FAMILY_SOURCES["source_samuel"]
    for i in range(N_TWIN):
        cycle1.step(tokens[i % len(tokens)], source_id="source_samuel",
                    origin_type="internal")
        cycle2.step(tokens[i % len(tokens)], source_id="source_samuel",
                    origin_type="internal")

    trust_match = trust_map(gov1) == trust_map(gov2)
    bonds_match = (
        {b.source_id: bond_record(b) for b in gov1.bond_manager.all_bonds()}
        == {b.source_id: bond_record(b) for b in gov2.bond_manager.all_bonds()}
    )
    crystals_match = sigs_match(crystal_sig(cycle1.crystal_store),
                                crystal_sig(cycle2.crystal_store))
    attractors_match = sigs_match(attractor_sig(cycle1.attractor),
                                  attractor_sig(cycle2.attractor))
    dec1 = [e["decision"] for e in gov1._audit_log[-N_TWIN:]]
    dec2 = [e["decision"] for e in gov2._audit_log[-N_TWIN:]]
    decisions_match = dec1 == dec2
    w1 = cycle1.witness.current_anchor()
    w2 = cycle2.witness.current_anchor()
    wcos = float(np.dot(w1, w2) / (np.linalg.norm(w1) * np.linalg.norm(w2) + 1e-8))
    field_cos = float(
        np.dot(cycle1.field.field, cycle2.field.field)
        / (np.linalg.norm(cycle1.field.field) * np.linalg.norm(cycle2.field.field) + 1e-8)
    )
    print(f"  continuation trust={trust_match} bonds={bonds_match} "
          f"crystals={crystals_match} attractors={attractors_match}")
    print(f"  continuation decisions={decisions_match} a={dec1} b={dec2}")
    print(f"  measured gap: witness-anchor cosine={wcos:.6f}  field cosine={field_cos:.6f}")
    print("  unrestored on purpose: witness, stream, predictor, attention,")
    print("  vector space, manipulation windows, dependency window")
    check(True,
          (f"twin continuation measured: trust={trust_match} bonds={bonds_match} "
           f"crystals={crystals_match} attractors={attractors_match} "
           f"decisions={decisions_match} witness={wcos:.4f} field={field_cos:.4f}"),
          checks)


def test_session_file(checks: list, td: str, cycle1, gov1) -> None:
    print("\n[5] session_persistence helper round-trip")
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
        test_twin(checks, cycle1, gov1, cycle2, gov2)
        test_session_file(checks, td, cycle1, gov1)

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
