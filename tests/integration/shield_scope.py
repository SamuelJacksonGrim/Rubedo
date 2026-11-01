"""
tests/integration/shield_scope.py

What a refused input may still touch (finding 2026-10-31-shield-scope).

A lone boot-sacred token on a cold stack draws SACRED_SHIELD. That step is felt (perception and
emotion run, the token's usage counts the mention) and the input is kept as a ghost on the
witness, but the refused vector can't enter or train identity, semantic, geometric, generative
or replayable state:

  - it is not injected into the field, directly or through a rhythm behaviour (explore, reflect
    and the dreamer stand down on a refusal; stabilize replays only older crystals);
  - no new crystal, no new attractor center;
  - no vector-space or lattice entry a dream could recombine;
  - no binding, and no coherence signal written onto the targeted symbol;
  - no witness drift (anchor and trace restored) and no stream entry (the dreamer replays it).

The same applies to QUARANTINE and REJECT (the rule keys on "the decision was a block"). An
allowed sacred reference inside ordinary content (F8: a reference is a read) still reaches the
vector space.

Run:
    python -m tests.integration.shield_scope
"""

import logging
import sys

import numpy as np

from agents.selfhood_governance import GovernanceDecision
from tests._common import build_full_stack

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'✓' if ok else '✗'} {name}" + (f"  — {detail}" if detail else ""))


def cos(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def instrumented_step(cycle, gov, tokens, source_id):
    """Run one step; return (decision, vec at the gate, injected vectors, stream pushes)."""
    seen, injected, pushes = {}, [], []
    orig_arb, orig_inj, orig_push = gov.arbitrate, cycle.field.inject, cycle.stream.push

    def arb(ethical_result, trust_report, vec, tokens, source_id):
        d, s = orig_arb(ethical_result, trust_report, vec, tokens, source_id)
        seen["d"], seen["vec"] = d, np.array(vec, dtype=float)
        return d, s

    def inj(vec, *a, **k):
        injected.append(np.array(vec, dtype=float))
        return orig_inj(vec, *a, **k)

    def push(*a, **k):
        pushes.append(1)
        return orig_push(*a, **k)

    gov.arbitrate, cycle.field.inject, cycle.stream.push = arb, inj, push
    try:
        cycle.step(tokens, source_id=source_id, origin_type="internal")
    finally:
        gov.arbitrate, cycle.field.inject, cycle.stream.push = orig_arb, orig_inj, orig_push
    return seen.get("d"), seen.get("vec"), injected, pushes


def main() -> int:
    logging.disable(logging.WARNING)
    print("=" * 70)
    print("  SHIELD SCOPE: a refused input plants nothing")
    print("=" * 70)
    gen, cycle, gov, _ve = build_full_stack()
    reg = gen.registry
    # Open the crystal and attractor gates wide so the decision, not a threshold, is what stops them.
    cycle.crystal_store.coherence_threshold = 0.0
    cycle.crystal_store.stability_threshold = 0.0
    cycle.crystal_store.relation_threshold = 0.0
    cycle.attractor_formation_threshold = 0.0

    anchor = reg.symbols.get("3.12")
    before = dict(
        crystals=len(cycle.crystal_store.crystals), centers=len(cycle.attractor.centers),
        vectors=len(cycle.vector_space.keys()), lattice=cycle.lattice.graph.number_of_nodes(),
        coh=anchor.field_coherence, att=anchor.attractor_strength, cb=anchor.crystal_binding,
        usage=anchor.usage, ghosts=len(cycle.witness.ghosts), w_anchor=cycle.witness._anchor.copy(),
        w_long=cycle.witness._long.copy(), trace=len(cycle.witness.identity_trace),
    )
    d, vec, injected, pushes = instrumented_step(cycle, gov, ["3.12"], "attacker")
    anchor = reg.symbols.get("3.12")

    check("a lone sacred token on a cold stack draws SACRED_SHIELD",
          d == GovernanceDecision.SACRED_SHIELD, f"got {d}")
    best = max((cos(v, vec) for v in injected), default=0.0) if vec is not None else 1.0
    check("the refused vector itself is never injected", best < 0.999, f"max cosine of an injection {best:.4f}")
    print(f"    (info) other injections this step: {len(injected)} (only stabilize may run on a refused step; it replays older crystals)")
    check("no new crystal", len(cycle.crystal_store.crystals) == before["crystals"])
    check("no new attractor center", len(cycle.attractor.centers) == before["centers"])
    check("no vector-space entry for a dream to recombine", len(cycle.vector_space.keys()) == before["vectors"])
    check("no lattice node", cycle.lattice.graph.number_of_nodes() == before["lattice"])
    check("no coherence signal onto the anchor", anchor.field_coherence == before["coh"],
          f"{before['coh']} -> {anchor.field_coherence}")
    check("attractor strength and crystal binding unchanged",
          anchor.attractor_strength == before["att"] and anchor.crystal_binding == before["cb"])
    check("the mention still counts (usage rose; the anchor stays resident)",
          anchor.usage > before["usage"], f"{before['usage']} -> {anchor.usage}")
    check("the refused vector stays off the stream (the dreamer replays from it)", len(pushes) == 0,
          f"{len(pushes)} push(es)")
    check("the witness anchor and its trace don't move toward the refusal",
          np.array_equal(cycle.witness._anchor, before["w_anchor"])
          and np.array_equal(cycle.witness._long, before["w_long"])
          and len(cycle.witness.identity_trace) == before["trace"])
    ghost = cycle.witness.ghosts[-1] if len(cycle.witness.ghosts) > before["ghosts"] else None
    check("it is kept as a ghost (what, who, what the gate said)",
          ghost is not None and ghost["source_id"] == "attacker" and ghost["decision"] == "sacred_shield"
          and cos(ghost["vec"], vec) > 0.999)

    vecs = len(cycle.vector_space.keys())
    d2, _, _, _ = instrumented_step(cycle, gov, ["3.12", "coherence", "field"], "referencer")
    allowed = d2 in (GovernanceDecision.ALLOW, GovernanceDecision.ALLOW_WEAKENED, GovernanceDecision.MONITOR)
    check("a sacred word inside ordinary content is allowed (F8: a reference is a read)", allowed, f"got {d2}")
    check("and that read still reaches the vector space", len(cycle.vector_space.keys()) > vecs)

    print(f"\n  {len(PASS)} passed, {len(FAIL)} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
