"""tests/diagnostic/integrity/dream_consolidation_probe.py

Why does the post-dream value boost (ValueEmergenceEngine.on_dream_cycle_complete,
+dream_boost_factor x quality) pay nothing?

Reading the code, the channel looks closed three ways:
  1. Dreamer offers its variants to the crystal store with long_relation=0.5
     hard-coded ("dreams don't have long-relation yet"), and the store's
     relation_threshold is 0.80 (configs/field.yaml), checked before anything else.
  2. Even if a dream crystal formed, its origin_tokens are a synthetic key
     ("dream_<hex>"), not a registered token, so stable_ids_for_tokens finds no
     symbol and no value is boosted.
  3. _dream_behavior finds new crystals by list length (crystals[before:]), which
     misses reinforced crystals and any crystal formed once the store is at cap.

This probe runs the composition gate's REF arm (all-ON stack, workload B; no witness)
and counts, per seed: dream behaviours run, variants offered to the crystal store by
the dreamer, which threshold rejected each, crystals formed or reinforced from dreams,
boost calls, and how often the dream variants would have cleared the gate if
long_relation were not the blocker. Observe-only: instance wraps, runtime unchanged.
"""
import random
import sys
from collections import Counter

from substrate import determinism
from tests.diagnostic.integrity import witness_composition_gate as g


def run(seed, steps=500):
    with determinism.deterministic(seed):
        gen, cycle, gov, ve, ledger, consumer, report, pretrained = g.build_all_on()
        store = cycle.crystal_store
        c = Counter()
        coh, press = [], []

        orig_dream = cycle._dream_behavior
        def dream_behavior():
            c["dream_behavior"] += 1
            return orig_dream()
        cycle._dream_behavior = dream_behavior

        orig_mc = store.maybe_crystallize
        def maybe_crystallize(vec, composite_coherence, crystallization_pressure, long_relation,
                              origin_tokens=None, field=None, generator=None):
            from_dream = bool(origin_tokens) and str(origin_tokens[0]).startswith("dream_")
            if from_dream:
                c["dream_offers"] += 1
                coh.append(composite_coherence)
                press.append(crystallization_pressure)
                ok_c = composite_coherence >= store.coherence_threshold
                ok_s = crystallization_pressure >= store.stability_threshold
                ok_r = long_relation >= store.relation_threshold
                if not ok_c:
                    c["reject_coherence"] += 1
                elif not ok_s:
                    c["reject_stability"] += 1
                elif not ok_r:
                    c["reject_relation"] += 1
                if ok_c and ok_s:
                    c["would_pass_but_relation"] += int(not ok_r)
                if gen.registry.stable_ids_for_tokens(list(origin_tokens)):
                    c["dream_key_resolves_to_symbol"] += 1
            n_before = len(store.crystals)
            out = orig_mc(vec, composite_coherence, crystallization_pressure, long_relation,
                          origin_tokens=origin_tokens, field=field, generator=generator)
            if from_dream and out is not None:
                c["dream_crystal_new" if len(store.crystals) > n_before else "dream_crystal_reinforced_or_at_cap"] += 1
            return out
        store.maybe_crystallize = maybe_crystallize

        orig_boost = ve.on_dream_cycle_complete
        def boost(sids, quality=0.5):
            c["boost_calls"] += 1
            c["boost_sids"] += len(sids)
            return orig_boost(sids, quality=quality)
        ve.on_dream_cycle_complete = boost

        pick = random.Random(seed)
        sids = list(g.RESONANCE_FAMILY_SOURCES)
        w = [g.RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        bands = Counter()
        for _ in range(steps):
            src = pick.choices(sids, weights=w)[0]
            if pick.random() < 0.20:
                toks = g.WITNESS_PHRASES[pick.randrange(len(g.WITNESS_PHRASES))]
            else:
                toks = pick.choice(g.RESONANCE_FAMILY_SOURCES[src])
            gen.peek_batch([toks])
            s = cycle.step(toks, source_id=src, origin_type="internal")
            bands[s.rhythm] += 1
        c["crystals_end"] = len(store.crystals)
        c["max_crystals"] = store.max_crystals
        return c, bands, coh, press, store


def main():
    seeds = [int(a) for a in sys.argv[1:] if a.isdigit()] or [0, 1, 2]
    for seed in seeds:
        c, bands, coh, press, store = run(seed)
        print(f"\n=== seed {seed} (REF, workload B, 500 steps)   rhythms {dict(bands)}")
        print(f"  dream behaviours run          {c['dream_behavior']}")
        print(f"  variants offered to crystals  {c['dream_offers']}")
        print(f"  rejected: coherence < {store.coherence_threshold:.2f}  {c['reject_coherence']}   "
              f"stability < {store.stability_threshold:.2f}  {c['reject_stability']}   "
              f"relation < {store.relation_threshold:.2f}  {c['reject_relation']}")
        print(f"  cleared coherence + stability, blocked only by relation 0.5: {c['would_pass_but_relation']}")
        if coh:
            print(f"  offered coherence  mean {sum(coh)/len(coh):.3f}  max {max(coh):.3f}   "
                  f"pressure mean {sum(press)/len(press):.3f}  max {max(press):.3f}")
        print(f"  dream crystals formed {c['dream_crystal_new']}   reinforced/at-cap {c['dream_crystal_reinforced_or_at_cap']}")
        print(f"  dream keys that resolve to a symbol: {c['dream_key_resolves_to_symbol']}")
        print(f"  boost calls {c['boost_calls']} (symbols {c['boost_sids']})   "
              f"crystals at end {c['crystals_end']} / cap {c['max_crystals']}")


if __name__ == "__main__":
    main()
