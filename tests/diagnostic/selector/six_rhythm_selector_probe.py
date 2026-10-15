"""
tests/diagnostic/selector/six_rhythm_selector_probe.py

Live OFF vs ON measurement for the six-rhythm selector (informational; exits 0).

One pretrained production generator (CONFIG shape, corpus 1.4.0) is copied into
two arms per seed: OFF (default) and ON (selector + reader). Both run the same
mixed workload: everyday stance phrases, witness-like phrases, rupture-like
phrases. RNGs are pinned per seed so the arms differ only by the lever.

PRE-DECLARED (written before the first run, 2026-10-14):
  works    - ON fires witness mostly on witness phrases and rupture mostly on
             rupture phrases (>= 70% of each mode's firings on its own phrase
             type), and rarely on stance phrases (<= 15% of stance steps).
           - witness steps move the field less than the same phrases do OFF
             (median |field change| ON-witness < OFF same phrases).
           - rupture steps change the field's direction more than OFF does on
             the same phrases (median 1 - cos(field_before, field_after)).
  safe     - governance outcomes don't get worse: quarantine/reject share ON
             within +2 percentage points of OFF; no new sacred-shield events.
           - the field lock is not broken: final field coherence ON within 0.02 of OFF.
  fails    - any of the above misses on 2 of 3 seeds, or the reader is so unsure on
             live text that neither mode fires (then the margin or the reader is wrong).

Run:
    python -m tests.diagnostic.selector.six_rhythm_selector_probe [steps] [seeds]
"""

import itertools
import random
import sys
from collections import Counter

import numpy as np

from loop import recursion1188 as r

STANCE = [["resonance", "field", "engine"], ["memory", "crystal", "attractor"],
          ["recursive", "cognition", "substrate"], ["curiosity", "wonder", "exploration"],
          ["consider", "pattern", "analyze"], ["imagine", "latent", "synthesis"]]
WITNESS = [["sit", "dwell", "abide"], ["linger", "await", "patience"],
           ["hush", "vigil", "contemplate"], ["attune", "abide", "unmoved"]]
RUPTURE = [["fracture", "crack", "rift"], ["sever", "cleave", "split"],
           ["collapse", "burst", "rupture"], ["fissure", "yield", "spall"]]


def workload(n, rng):
    """(kind, tokens, source). Sources rotate over the canonical four-source
    Resonance Family weights: a single-source run trips the concentration
    detectors and quarantines most steps, which hides what the selector does."""
    from tests._common import RESONANCE_FAMILY_WEIGHTS
    sids = list(RESONANCE_FAMILY_WEIGHTS)
    sw = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
    out = []
    for _ in range(n):
        k = rng.choices(["stance", "witness", "rupture"], weights=[6, 2, 2])[0]
        pool = {"stance": STANCE, "witness": WITNESS, "rupture": RUPTURE}[k]
        out.append((k, pool[rng.randrange(len(pool))], rng.choices(sids, weights=sw)[0]))
    return out


_ORIG = np.random.default_rng


_CTX = []


def pin(seed):
    """Enter substrate.determinism's replay mode (SimClock + seeded generators).
    Replaced the old default_rng monkeypatch, which missed the wall clock."""
    from substrate import determinism
    unpin()
    cm = determinism.deterministic(seed)
    cm.__enter__()
    _CTX.append(cm)


def unpin():
    while _CTX:
        _CTX.pop().__exit__(None, None, None)


ONLY = None   # set from argv: "witness" / "rupture" to allow only that selector mode


def run_arm(ckpt_dir, selector, seed, steps):
    """Both arms resume the same pretrained checkpoint through build_engine's
    guarded session-resume path, so they start from identical weights + ecology."""
    pin(seed)
    try:
        cfg = dict(r.CONFIG)
        cfg.update(session_persistence=True, checkpoint_dir=str(ckpt_dir),
                   six_rhythm_selector=selector)
        gen, cycle, gov, ve = r.build_engine(cfg)
        decisions = Counter()
        gate = cycle._governance_gate
        def counted(*a, **k):
            d, s = gate(*a, **k)
            decisions[d.name] += 1
            return d, s
        cycle._governance_gate = counted
        if selector and ONLY and cycle.rhythm_reader is not None:
            from cognition.rhythm_reader import RhythmRead
            real_read = cycle.rhythm_reader.read
            def masked(g, t):
                rd = real_read(g, t)
                if rd.rhythm in ("witness", "rupture") and rd.rhythm != ONLY:
                    return RhythmRead(rd.rhythm, 0.0, rd.cosine)   # below margin: mode suppressed
                return rd
            cycle.rhythm_reader.read = masked
        rows = []
        for kind, toks, src in workload(steps, random.Random(seed)):
            before = cycle.field.field.copy()
            s = cycle.step(tokens=toks, source_id=src, origin_type="internal")
            after = cycle.field.field
            nb, na = np.linalg.norm(before), np.linalg.norm(after)
            turn = 1.0 - float(before @ after / (nb * na + 1e-8)) if nb > 1e-8 else 0.0
            rows.append(dict(kind=kind, behavior=s.extras.get("behavior", s.rhythm),
                             move=float(np.linalg.norm(after - before)), turn=turn,
                             coherence=s.coherence, read=s.extras.get("rhythm_read"),
                             margin=s.extras.get("read_margin")))
        return rows, decisions, cycle
    finally:
        unpin()


def main():
    global ONLY
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    ONLY = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in ("witness", "rupture") else None
    if ONLY:
        print(f"selector restricted to {ONLY} only")
    import tempfile
    from pathlib import Path
    cfg = dict(r.CONFIG)
    print(f"pretraining one production generator (dim {cfg['dim']}, corpus 1.4.0)...")
    pin(1188)
    base_gen, _, _, _ = r.build_engine(cfg)
    unpin()
    ckpt = Path(tempfile.mkdtemp(prefix="selector_probe_"))
    base_gen.save_checkpoint(str(ckpt / "generator_weights.pt"), str(ckpt / "ecology.json"))

    for seed in range(1, seeds + 1):
        off, dec_off, c_off = run_arm(ckpt, False, seed, steps)
        on, dec_on, c_on = run_arm(ckpt, True, seed, steps)
        print(f"\n=== seed {seed} ({steps} steps)")
        fired = Counter((x["behavior"], x["kind"]) for x in on if x["behavior"] in ("witness", "rupture"))
        for mode in ("witness", "rupture"):
            tot = sum(v for (b, k), v in fired.items() if b == mode)
            own = fired.get((mode, mode), 0)
            print(f"  {mode:8s} fired {tot:4d}  on own phrases {own / tot if tot else float('nan'):.2f}  "
                  f"by kind {dict((k, v) for (b, k), v in fired.items() if b == mode)}")
        stance_n = sum(1 for x in on if x["kind"] == "stance")
        stance_hit = sum(1 for x in on if x["kind"] == "stance" and x["behavior"] in ("witness", "rupture"))
        print(f"  stance steps switched to a selector mode: {stance_hit}/{stance_n}")
        for kind in ("witness", "rupture"):
            rs = [x for x in on if x["kind"] == kind]
            reads = Counter(x["read"] for x in rs)
            ms = [x["margin"] for x in rs if x["read"] == kind and x["margin"] is not None]
            print(f"  {kind} phrases read as {dict(reads)}; own-read margins median "
                  f"{np.median(ms) if ms else float('nan'):.3f} min {min(ms) if ms else float('nan'):.3f}")

        def med(rows, kind, key, beh=None):
            v = [x[key] for x in rows if x["kind"] == kind and (beh is None or x["behavior"] == beh)]
            return float(np.median(v)) if v else float("nan")
        print(f"  witness phrases |field move|  OFF {med(off, 'witness', 'move'):.4f}  "
              f"ON(witness steps) {med(on, 'witness', 'move', 'witness'):.4f}")
        print(f"  rupture phrases field turn    OFF {med(off, 'rupture', 'turn'):.6f}  "
              f"ON(rupture steps) {med(on, 'rupture', 'turn', 'rupture'):.6f}")
        print(f"  final field coherence OFF {c_off.watcher.evaluate(c_off.field.field / (np.linalg.norm(c_off.field.field) + 1e-8), c_off.witness.current_anchor(), c_off.field.resonate()).composite:.4f}  "
              f"ON {c_on.watcher.evaluate(c_on.field.field / (np.linalg.norm(c_on.field.field) + 1e-8), c_on.witness.current_anchor(), c_on.field.resonate()).composite:.4f}")
        print(f"  governance OFF {dict(dec_off)}")
        print(f"  governance ON  {dict(dec_on)}")
        print(f"  behavior mix ON {dict(Counter(x['behavior'] for x in on))}")


if __name__ == "__main__":
    main()
