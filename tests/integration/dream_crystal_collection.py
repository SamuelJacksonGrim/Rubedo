"""
tests/integration/dream_crystal_collection.py

_dream_behavior credits the crystals the dream newly formed, found by
identity (including one the store then evicted), not crystals[before:].
Reinforcing a crystal that already existed pays nothing: crediting
reinforcement re-paid the same symbols every dream and flooded CORE.
With dream_consolidation off, the dreamer still offers long_relation 0.5 and
a synthetic dream key. On, relation is the cosine with the long anchor and
the offered tokens are the sampled memories' tokens.

Run:
    python -m tests.integration.dream_crystal_collection
"""

import sys

import numpy as np

from agents.value_emergence import EmergentValue
from substrate import determinism
from substrate.memory_crystals import MemoryCrystal
from tests._common import build_full_stack


def expect(name, ok):
    print(f"  {'✓' if ok else '✗'} {name}")
    return bool(ok)


def _plant(ve, registry, token, strength=1.0):
    sid = registry.register(token).stable_id
    vid = f"val_{token}"
    ve.values[vid] = EmergentValue(
        value_id=vid, symbol_stable_id=sid, symbolic_core=token, strength=strength,
    )
    ve.symbol_to_value[sid] = vid
    return sid, ve.values[vid]


def main():
    print("=" * 72)
    print("  INTEGRATION: dream crystals are collected by identity")
    print("=" * 72)

    results = []
    gen, cycle, gov, ve = build_full_stack()
    dim = cycle.dim

    # Reinforced crystal: already in the store, so a length slice is empty.
    sid, value = _plant(ve, gen.registry, "resonance")
    existing = MemoryCrystal(
        vector=np.ones(dim, dtype=np.float32),
        origin_tokens=["resonance"],
        stability=1.0,
        coherence=0.9,
    )
    cycle.crystal_store.crystals.append(existing)

    def fake_dream(**kwargs):
        cycle.dreamer.last_dream_crystals = [existing, existing]
        return []

    cycle.dreamer.dream = fake_dream
    before = len(cycle.crystal_store.crystals)
    before_strength = value.strength
    cycle._dream_behavior()
    results.append(expect(
        "reinforcing a crystal that existed before the dream pays nothing",
        len(cycle.crystal_store.crystals) == before
        and value.dream_reinforced_count == 0
        and value.strength == before_strength,
    ))

    # Formed during the dream (absent before it), reported twice: credited once.
    sid, new_value = _plant(ve, gen.registry, "newly_formed")
    fresh = MemoryCrystal(
        vector=np.full(dim, 0.5, dtype=np.float32),
        origin_tokens=["newly_formed"],
        stability=0.9,
        coherence=0.9,
    )

    def fake_fresh(**kwargs):
        cycle.crystal_store.crystals.append(fresh)
        cycle.dreamer.last_dream_crystals = [fresh, fresh]
        return []

    cycle.dreamer.dream = fake_fresh
    cycle._dream_behavior()
    results.append(expect(
        "crystal formed during the dream is credited once",
        new_value.dream_reinforced_count == 1,
    ))

    # Formed at the cap and already evicted: not in the store list at all.
    sid, ghost_value = _plant(ve, gen.registry, "evicted_token")
    ghost = MemoryCrystal(
        vector=np.full(dim, 0.2, dtype=np.float32),
        origin_tokens=["evicted_token"],
        stability=0.8,
        coherence=0.9,
    )

    def fake_ghost(**kwargs):
        cycle.dreamer.last_dream_crystals = [ghost]
        return []

    cycle.dreamer.dream = fake_ghost
    cycle._dream_behavior()
    results.append(expect(
        "crystal absent from the store is still credited",
        all(ghost is not c for c in cycle.crystal_store.crystals)
        and ghost_value.dream_reinforced_count == 1,
    ))

    # The dreamer itself: off keeps 0.5 and dream_<hex>; on uses the long anchor
    # and the tokens stored beside the sampled memories.
    with determinism.deterministic(1):
        gen2, cycle2, gov2, ve2 = build_full_stack()
        space = cycle2.vector_space
        space.put("mem_a", np.ones(cycle2.dim), origin_tokens=["alpha"])
        space.put("mem_b", np.ones(cycle2.dim) * 0.5, origin_tokens=["beta"])
        offers = []

        class Store:
            def maybe_crystallize(self, vec, composite_coherence, crystallization_pressure,
                                  long_relation, origin_tokens=None, field=None, generator=None):
                offers.append((float(long_relation), list(origin_tokens or []), vec.copy()))
                return MemoryCrystal(
                    vector=np.asarray(vec, dtype=np.float32).copy(),
                    origin_tokens=list(origin_tokens or []),
                    stability=1.0,
                    coherence=1.0,
                )

        anchor = cycle2.witness.current_anchor()
        long_anchor = cycle2.witness.long_anchor()
        # The contract is the offer, not whether a cold field clears 0.25.
        cycle2.dreamer.coherence_gate = 0.0
        cycle2.dreamer.dream(
            emotion=cycle2.emotion, watcher=cycle2.watcher, anchor=anchor,
            crystal_store=Store(), generator=gen2, consolidate=False,
        )
        off = list(offers)
        offers.clear()
        cycle2.dreamer.dream(
            emotion=cycle2.emotion, watcher=cycle2.watcher, anchor=anchor,
            crystal_store=Store(), generator=gen2, consolidate=True,
            long_anchor=long_anchor,
        )
        on = list(offers)

    off_ok = bool(off) and all(
        rel == 0.5 and toks and toks[0].startswith("dream_") for rel, toks, _ in off
    )
    def _expected(vec):
        denom = np.linalg.norm(vec) * np.linalg.norm(long_anchor) + 1e-8
        return round(float(np.dot(vec, long_anchor) / denom), 6)

    on_ok = bool(on) and all(
        abs(rel - _expected(vec)) < 1e-9
        and toks
        and set(toks) <= {"alpha", "beta"}
        and not any(t.startswith("dream_") for t in toks)
        for rel, toks, vec in on
    )
    # Returned crystals are recorded, and a repeat of the same object is once.
    recorded = cycle2.dreamer.last_dream_crystals
    results.append(expect("consolidation off offers 0.5 and a dream key", off_ok))
    results.append(expect("consolidation on offers long-anchor cosine and source tokens", on_ok))
    results.append(expect(
        "dreamer records each returned crystal once",
        len(recorded) == len(on) and len(recorded) == len({id(c) for c in recorded}),
    ))

    print()
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"  ALL CHECKS PASS: {passed}/{total}")
        return 0
    print(f"  FAILED: {passed}/{total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
