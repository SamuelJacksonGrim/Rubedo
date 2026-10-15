"""
tests/diagnostic/selector/aftermath_probe.py

What witness and upstream rupture leave behind (informational; exits 0).

Arms per seed, all resuming one pretrained production checkpoint, same workload,
RNGs pinned, so step t sees the same input in every arm (paired comparison):
  OFF               default
  WITNESS           selector on, rupture reads masked (witness only)
  RUPTURE-UP        selector on, witness reads masked, rupture_upstream=True

Per step: field vector, field coherence (watcher composite of the unit field
against the anchor), the expressed vector (cycle._last_expressed), the input's
read-only direction u_t (Generator.peek_batch), and the held rupture target.

PRE-DECLARED (written before the first run, 2026-10-14; GPT/Raphael's three
questions for witness, behavioral bar for rupture):

  WITNESS, at every witness step t, paired with OFF at the same t:
    retention       the field turns toward the witnessed input more than OFF:
                    d_k = cos(field_{t+k}, u_t) - cos(field_{t-1}, u_t);
                    median(d_1) WITNESS > OFF, and still > OFF at k = 5.
    recovery        the coherence deficit (WITNESS - OFF) closes: |deficit| at
                    t+10 smaller than at t+1 (median over witness steps).
    responsiveness  the next expression leans toward what was witnessed:
                    median cos(expr_{t+1}, u_t) WITNESS > OFF.
    If retention and responsiveness hold, the coherence dip is the update
    mechanism (keep it, bounded by what was measured). If they fail, it is
    collateral damage (fix the mechanism).

  RUPTURE-UP, at every rupture step t with held target T:
    behavior        the expression carries the disruption: median
                    cos(expr_t, T) RUPTURE-UP > OFF, and still > OFF at t+1.
    integration     the field takes it in: median cos(field_{t+5}, T) > OFF.
    identity        final field coherence within 0.02 of OFF (mean over seeds),
                    and no QUARANTINE/REJECT increase.
    Pass = all three on >= 2 of 3 seeds. Fail on behavior = absorbed upstream too.

Run:
    python -m tests.diagnostic.selector.aftermath_probe [steps] [seeds]
"""

import random
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from loop import recursion1188 as r
from tests.diagnostic.selector.six_rhythm_selector_probe import pin, workload, _ORIG


def unit(v):
    return v / (np.linalg.norm(v) + 1e-8)


def cos(a, b):
    return float(unit(a) @ unit(b))


def field_coh(cycle):
    f = cycle.field.field
    if np.linalg.norm(f) < 1e-8:
        return 0.0
    return cycle.watcher.evaluate(unit(f), cycle.witness.current_anchor(), cycle.field.resonate()).composite


def run(ckpt, arm, seed, steps):
    pin(seed)
    try:
        cfg = dict(r.CONFIG)
        cfg.update(session_persistence=True, checkpoint_dir=str(ckpt),
                   six_rhythm_selector=(arm != "OFF"), rupture_upstream=(arm == "RUPTURE-UP"))
        gen, cycle, gov, ve = r.build_engine(cfg)
        if arm != "OFF":
            from cognition.rhythm_reader import RhythmRead
            keep = "witness" if arm == "WITNESS" else "rupture"
            real = cycle.rhythm_reader.read
            def masked(g, t):
                rd = real(g, t)
                if rd.rhythm in ("witness", "rupture") and rd.rhythm != keep:
                    return RhythmRead(rd.rhythm, 0.0, rd.cosine)
                return rd
            cycle.rhythm_reader.read = masked
        decisions = Counter()
        gate = cycle._governance_gate
        def counted(*a, **k):
            d, s = gate(*a, **k)
            decisions[d.name] += 1
            return d, s
        cycle._governance_gate = counted
        rows = []
        for kind, toks, src in workload(steps, random.Random(seed)):
            vecs, known = gen.peek_batch([toks])
            s = cycle.step(tokens=toks, source_id=src, origin_type="internal")
            rows.append(dict(kind=kind, behavior=s.extras.get("behavior", s.rhythm),
                             field=cycle.field.field.copy(), coh=field_coh(cycle),
                             expr=np.array(cycle._last_expressed, dtype=float),
                             u=vecs[0] if known[0] else None,
                             target=None if getattr(cycle, "_rupture_target", None) is None
                             else np.array(cycle._rupture_target, dtype=float)))
        return rows, decisions
    finally:
        np.random.default_rng = _ORIG


def med(xs):
    xs = [x for x in xs if x is not None and np.isfinite(x)]
    return float(np.median(xs)) if xs else float("nan")


def witness_report(off, on):
    idx = [t for t, x in enumerate(on) if x["behavior"] == "witness" and x["u"] is not None
           and 1 <= t < len(on) - 10]
    out = {"n": len(idx)}
    for k in (1, 5):
        for name, rows in (("off", off), ("on", on)):
            out[f"ret{k}_{name}"] = med([cos(rows[t + k]["field"], on[t]["u"]) - cos(rows[t - 1]["field"], on[t]["u"])
                                        for t in idx])
    out["deficit1"] = med([abs(on[t + 1]["coh"] - off[t + 1]["coh"]) for t in idx])
    out["deficit10"] = med([abs(on[t + 10]["coh"] - off[t + 10]["coh"]) for t in idx])
    out["resp_off"] = med([cos(off[t + 1]["expr"], on[t]["u"]) for t in idx])
    out["resp_on"] = med([cos(on[t + 1]["expr"], on[t]["u"]) for t in idx])
    return out


def rupture_report(off, on):
    idx = [t for t, x in enumerate(on) if x["behavior"] == "rupture" and x["target"] is not None
           and t < len(on) - 5]
    out = {"n": len(idx)}
    for k in (0, 1):
        out[f"beh{k}_off"] = med([cos(off[t + k]["expr"], on[t]["target"]) for t in idx])
        out[f"beh{k}_on"] = med([cos(on[t + k]["expr"], on[t]["target"]) for t in idx])
    out["int_off"] = med([cos(off[t + 5]["field"], on[t]["target"]) for t in idx])
    out["int_on"] = med([cos(on[t + 5]["field"], on[t]["target"]) for t in idx])
    return out


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    print(f"pretraining one production generator (dim {r.CONFIG['dim']}, corpus 1.4.0)...")
    pin(1188)
    base, _, _, _ = r.build_engine(dict(r.CONFIG))
    np.random.default_rng = _ORIG
    ckpt = Path(tempfile.mkdtemp(prefix="aftermath_probe_"))
    base.save_checkpoint(str(ckpt / "generator_weights.pt"), str(ckpt / "ecology.json"))

    for seed in range(1, seeds + 1):
        off, d_off = run(ckpt, "OFF", seed, steps)
        wit, d_wit = run(ckpt, "WITNESS", seed, steps)
        rup, d_rup = run(ckpt, "RUPTURE-UP", seed, steps)
        w, u = witness_report(off, wit), rupture_report(off, rup)
        print(f"\n=== seed {seed} ({steps} steps)")
        print(f"  WITNESS (n={w['n']})")
        print(f"    retention d1  OFF {w['ret1_off']:+.4f}  ON {w['ret1_on']:+.4f}   d5  OFF {w['ret5_off']:+.4f}  ON {w['ret5_on']:+.4f}")
        print(f"    recovery |coh deficit|  t+1 {w['deficit1']:.4f}  t+10 {w['deficit10']:.4f}")
        print(f"    responsiveness cos(expr_t+1, u_t)  OFF {w['resp_off']:+.4f}  ON {w['resp_on']:+.4f}")
        print(f"    final field coherence OFF {off[-1]['coh']:.4f}  ON {wit[-1]['coh']:.4f}")
        print(f"  RUPTURE-UP (n={u['n']})")
        print(f"    behavior cos(expr, T)  t  OFF {u['beh0_off']:+.4f}  ON {u['beh0_on']:+.4f}   t+1  OFF {u['beh1_off']:+.4f}  ON {u['beh1_on']:+.4f}")
        print(f"    integration cos(field_t+5, T)  OFF {u['int_off']:+.4f}  ON {u['int_on']:+.4f}")
        print(f"    final field coherence OFF {off[-1]['coh']:.4f}  ON {rup[-1]['coh']:.4f}")
        print(f"  governance OFF {dict(d_off)}  WITNESS {dict(d_wit)}  RUPTURE-UP {dict(d_rup)}")


if __name__ == "__main__":
    main()
