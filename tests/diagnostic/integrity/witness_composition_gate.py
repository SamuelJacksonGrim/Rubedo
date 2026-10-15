"""
tests/diagnostic/integrity/witness_composition_gate.py

The graduation gate for WITNESS (the six-rhythm selector, witness mode only):
does it hold when every other behavior-bearing lever is ON too? Built on the
standing all-levers gate (all_levers_composition_probe.build_all_on: production
dim, corpus pretrain, eval mode, novelty attenuation, bond DDM, Build A ignition,
Build B λ gate, ⊘ consumer named_only). Rupture is OFF throughout (its reads are
masked): witness is gated alone, per the agreed order.

Per seed, two paired arms, each run deterministic (substrate.determinism) so the
arms see identical inputs: REF = the all-ON stack; WIT = the same stack + witness.

Two workloads per arm:
  A  canonical   the standing gate's 500-step Resonance Family workload, unchanged.
  B  witnessing  the same sources, 20% of steps replaced by witness phrases, so
                 witness actually fires (it rarely reads as witness on A).

PRE-DECLARED (written before the first run, 2026-10-15; GPT/Raphael's three
requirements):
  composition  every health check of the standing gate holds for WIT on A and on B
               (strong band paired against REF, -1 slack), and no check that holds
               for REF fails for WIT. Required on 3 of 3 seeds (hard gate).
  identity     on B: anchor drift <= 2 x REF + 0.01; field lock <= 2 x REF + 1e-5;
               matched coherence mean >= -0.05 and no 10-step mean below -0.10.
               Required on >= 2 of 3 seeds.
  receptivity  on B: median retention d1 at witness steps (field turns toward the
               witnessed input) WIT > REF at the same steps. >= 2 of 3 seeds.
  non-vacuous  on B witness fires >= 50 times per seed, else the gate is void.
  PASS = all four. Passing makes witness a candidate for activation, not an
  automatic default (the activation decision is made separately, on the record).

Informational. exit 0. Not in run_all_tests.sh (minutes per seed).
Run:  python -m tests.diagnostic.integrity.witness_composition_gate [seeds...]
"""
import logging
import random
import sys
from collections import Counter

import numpy as np

logging.disable(logging.CRITICAL)
sys.path.insert(0, ".")

from substrate import determinism                                                # noqa: E402
from tests._common import RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS, health_summary  # noqa: E402
from tests.diagnostic.integrity.all_levers_composition_probe import build_all_on, _strong     # noqa: E402

WITNESS_PHRASES = [["sit", "dwell", "abide"], ["linger", "await", "patience"],
                   ["hush", "vigil", "contemplate"], ["attune", "abide", "unmoved"]]


def unit(v):
    return v / (np.linalg.norm(v) + 1e-8)


def cos(a, b):
    return float(unit(a) @ unit(b))


def attach_witness(gen, cycle):
    from cognition.rhythm_reader import RhythmReader, RhythmRead
    from training.corpus import load_corpus, TRAIN_PATH, RHYTHMS
    reader = RhythmReader.from_corpus(gen, load_corpus(TRAIN_PATH), RHYTHMS)
    real = reader.read
    def witness_only(g, t):
        rd = real(g, t)
        if rd.rhythm == "rupture":          # rupture stays OFF in this gate
            return RhythmRead(rd.rhythm, 0.0, rd.cosine)
        return rd
    reader.read = witness_only
    cycle.six_rhythm_selector = True
    cycle.attach_rhythm_reader(reader)


def run(seed, workload, with_witness):
    with determinism.deterministic(seed):
        gen, cycle, gov, ve, ledger, consumer, report, pretrained = build_all_on()
        if with_witness:
            attach_witness(gen, cycle)
        pick = random.Random(seed)
        sids = list(RESONANCE_FAMILY_SOURCES)
        w = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        decisions = Counter()
        orig = gov.arbitrate
        def counted(*a, **k):
            dec, strength = orig(*a, **k)
            decisions[dec.value] += 1
            return dec, strength
        gov.arbitrate = counted
        rows = []
        for _ in range(500):
            src = pick.choices(sids, weights=w)[0]
            if workload == "B" and pick.random() < 0.20:
                toks, kind = WITNESS_PHRASES[pick.randrange(len(WITNESS_PHRASES))], "witness"
            else:
                toks, kind = pick.choice(RESONANCE_FAMILY_SOURCES[src]), "canonical"
            vecs, known = gen.peek_batch([toks])
            s = cycle.step(toks, source_id=src, origin_type="internal")
            f = cycle.field.field
            coh = (cycle.watcher.evaluate(unit(f), cycle.witness.current_anchor(), cycle.field.resonate()).composite
                   if np.linalg.norm(f) > 1e-8 else 0.0)
            rows.append(dict(kind=kind, behavior=s.extras.get("behavior", s.rhythm), field=f.copy(), coh=coh,
                             anchor=np.array(cycle.witness.current_anchor(), dtype=float),
                             u=vecs[0] if known[0] else None))
        gov.arbitrate = orig
        h = health_summary(cycle, gov, ve, decisions)
        vals = [v.strength for v in ve.values.values() if v.dissolved_at_step < 0]
        h["mean_strength"] = sum(vals) / len(vals) if vals else 0.0
        h["strong"] = _strong(ve)
        h["gain"] = ledger.gain()
        h["demotions"] = consumer.snapshot()["demotions_total"]
        h["values"] = [(v.symbolic_core, v.strength, v.dissolved_at_step, v.coherence_contribution,
                        v.polarity.name) for v in ve.values.values()]
        return h, rows


def health_checks(h, strong_ref):
    return {
        "injection_rate >= 0.95": h["injection_rate"] >= 0.95,
        "no benign quarantines": h["quarantine_rate"] == 0.0,
        "all sources trust maxed": h["all_sources_trust_max"],
        "HHI < 0.30": h["hhi"] < 0.30,
        "bonds >= 1": h["bonds_formed"] >= 1,
        "active_values >= 30": h["active_values"] >= 30,
        "strong vs ref (-1)": h["strong"] >= strong_ref - 1,
        "lambda gate open": h["gain"] > 0.5,
        "consumer used": h["demotions"] >= 1,
        "no field collapse": h["mean_strength"] > 1.0,
    }


def main():
    seeds = [int(a) for a in sys.argv[1:]] or [42, 43, 44]
    tally = Counter()
    for seed in seeds:
        print(f"\n=== seed {seed}")
        comp_ok = True
        for wl in ("A", "B"):
            h_ref, r_ref = run(seed, wl, False)
            h_wit, r_wit = run(seed, wl, True)
            c_ref, c_wit = health_checks(h_ref, h_ref["strong"]), health_checks(h_wit, h_ref["strong"])
            fired = sum(1 for x in r_wit if x["behavior"] == "witness")
            broke = [k for k in c_wit if c_ref[k] and not c_wit[k]]
            ok = all(c_wit.values()) and not broke
            comp_ok &= ok
            print(f"  workload {wl}: witness fired {fired}   composition {'OK' if ok else 'FAIL'}"
                  + (f"  (failing: {[k for k, v in c_wit.items() if not v]}; broke vs REF: {broke})" if not ok else ""))
            print(f"    REF inj {h_ref['injection_rate']:.3f} q {h_ref['quarantine_rate']:.3f} HHI {h_ref['hhi']:.3f} "
                  f"bonds {h_ref['bonds_formed']} active {h_ref['active_values']} strong {h_ref['strong']} "
                  f"λ {h_ref['gain']:.2f} demot {h_ref['demotions']}")
            print(f"    WIT inj {h_wit['injection_rate']:.3f} q {h_wit['quarantine_rate']:.3f} HHI {h_wit['hhi']:.3f} "
                  f"bonds {h_wit['bonds_formed']} active {h_wit['active_values']} strong {h_wit['strong']} "
                  f"λ {h_wit['gain']:.2f} demot {h_wit['demotions']}")
            if wl == "B":
                a100 = 100
                d_ref = 1 - cos(r_ref[-1]["anchor"], r_ref[a100]["anchor"])
                d_wit = 1 - cos(r_wit[-1]["anchor"], r_wit[a100]["anchor"])
                lock = lambda rows: float(np.median([1 - cos(rows[t]["field"], rows[t - 1]["field"])
                                                     for t in range(len(rows) - 200, len(rows))]))
                l_ref, l_wit = lock(r_ref), lock(r_wit)
                gap = np.array([b["coh"] - a["coh"] for a, b in zip(r_ref, r_wit)])
                worst10 = min(gap[i:i + 10].mean() for i in range(len(gap) - 9))
                ident = (d_wit <= 2 * d_ref + 0.01 and l_wit <= 2 * l_ref + 1e-5
                         and gap.mean() >= -0.05 and worst10 >= -0.10)
                ev = [t for t, x in enumerate(r_wit) if x["behavior"] == "witness" and x["u"] is not None
                      and 1 <= t < len(r_wit) - 1]
                ret = lambda rows: float(np.median([cos(rows[t + 1]["field"], r_wit[t]["u"])
                                                    - cos(rows[t - 1]["field"], r_wit[t]["u"]) for t in ev])) if ev else float("nan")
                ret_ref, ret_wit = ret(r_ref), ret(r_wit)
                recept = ret_wit > ret_ref
                tally["identity"] += ident
                tally["receptivity"] += recept
                tally["nonvacuous"] += fired >= 50
                print(f"    identity: anchor {d_wit:.4f} vs {d_ref:.4f}  lock {l_wit:.2e} vs {l_ref:.2e}  "
                      f"coh mean {gap.mean():+.4f} worst10 {worst10:+.4f}  -> {'OK' if ident else 'FAIL'}")
                print(f"    receptivity: retention d1 WIT {ret_wit:+.5f} vs REF {ret_ref:+.5f}  -> {'OK' if recept else 'FAIL'}")
        tally["composition"] += comp_ok
    n = len(seeds)
    print("\nGATE:")
    rows = [("composition (3/3)", "composition", tally["composition"] == n),
            ("identity (>=2/3)", "identity", tally["identity"] >= 2),
            ("receptivity (>=2/3)", "receptivity", tally["receptivity"] >= 2),
            ("non-vacuous (3/3)", "nonvacuous", tally["nonvacuous"] == n)]
    verdict = {label: ok for label, _, ok in rows}
    for label, key, ok in rows:
        print(f"  {label:22s} {tally[key]}/{n}  {'PASS' if ok else 'FAIL'}")
    print("  VERDICT:", "PASS: witness composes; candidate for activation." if all(verdict.values())
          else "HOLD: witness does not pass the gate; see FAILs.")


if __name__ == "__main__":
    main()
