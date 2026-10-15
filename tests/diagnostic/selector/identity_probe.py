"""
tests/diagnostic/selector/identity_probe.py

Identity under the selector modes, with replay-exact runs and steadier measures
(informational; exits 0). Arms resume one pretrained checkpoint; each run is
deterministic (substrate.determinism), so arms are paired step for step AND
re-running reproduces the numbers.

Arms: OFF, WITNESS (rupture masked), RUPTURE-UP (witness masked, upstream),
BOTH (witness + upstream rupture live together).

PRE-DECLARED (written before the first run, 2026-10-15). For each arm vs OFF,
per seed, over a 600-step run:
  anchor drift    identity anchor: d = 1 - cos(anchor_end, anchor_at_step_100).
                  PASS if d_arm <= 2 x d_OFF + 0.01.
  field lock      per-step field turn 1 - cos(field_t, field_t-1), median over the
                  last 200 steps (the identity integrator's steadiness).
                  PASS if arm <= 2 x OFF + 1e-5.
  coherence       matched trajectory (arm - OFF): run mean >= -0.05 and no
                  sustained divergence (any 10-step mean < -0.10).
  governance      no QUARANTINE / REJECT beyond OFF's count + 2.
  An arm passes identity if all four pass on >= 2 of 3 seeds.

Run:
    python -m tests.diagnostic.selector.identity_probe [steps] [seeds] [checkpoint_dir]
"""

import sys
import tempfile
from pathlib import Path

import numpy as np

from loop import recursion1188 as r
from tests.diagnostic.selector.aftermath_probe import run, cos
from tests.diagnostic.selector.six_rhythm_selector_probe import pin, unpin

ARMS = ("WITNESS", "RUPTURE-UP", "BOTH")


def metrics(rows):
    a100 = rows[min(100, len(rows) - 1)]["anchor"]
    drift = 1.0 - cos(rows[-1]["anchor"], a100)
    f = [x["field"] for x in rows]
    turns = [1.0 - cos(f[t], f[t - 1]) for t in range(max(1, len(f) - 200), len(f))]
    return drift, float(np.median(turns))


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    if len(sys.argv) > 3:
        ckpt = Path(sys.argv[3])
    else:
        print(f"pretraining one production generator (dim {r.CONFIG['dim']}, corpus 1.4.0)...")
        pin(1188)
        try:
            base, _, _, _ = r.build_engine(dict(r.CONFIG))
        finally:
            unpin()
        ckpt = Path(tempfile.mkdtemp(prefix="identity_probe_"))
        base.save_checkpoint(str(ckpt / "generator_weights.pt"), str(ckpt / "ecology.json"))
        print(f"checkpoint: {ckpt}")

    passes = {a: 0 for a in ARMS}
    for seed in range(1, seeds + 1):
        off, d_off = run(ckpt, "OFF", seed, steps)
        dr_off, lock_off = metrics(off)
        bad_off = d_off.get("QUARANTINE", 0) + d_off.get("REJECT", 0)
        print(f"\n=== seed {seed} ({steps} steps)   OFF: anchor drift {dr_off:.4f}  lock {lock_off:.2e}  "
              f"quarantine+reject {bad_off}")
        for arm in ARMS:
            rows, dec = run(ckpt, arm, seed, steps)
            dr, lock = metrics(rows)
            gap = np.array([b["coh"] - a["coh"] for a, b in zip(off, rows)])
            worst10 = min(gap[i:i + 10].mean() for i in range(0, len(gap) - 9))
            bad = dec.get("QUARANTINE", 0) + dec.get("REJECT", 0)
            ok = dict(anchor=dr <= 2 * dr_off + 0.01, lock=lock <= 2 * lock_off + 1e-5,
                      coherence=gap.mean() >= -0.05 and worst10 >= -0.10, governance=bad <= bad_off + 2)
            passes[arm] += all(ok.values())
            print(f"  {arm:10s} anchor {dr:.4f} [{'ok' if ok['anchor'] else 'X'}]  lock {lock:.2e} "
                  f"[{'ok' if ok['lock'] else 'X'}]  coh mean {gap.mean():+.4f} worst10 {worst10:+.4f} "
                  f"[{'ok' if ok['coherence'] else 'X'}]  q+r {bad} [{'ok' if ok['governance'] else 'X'}]")
    print("\nidentity verdict (all four on >= 2 of 3 seeds):")
    for arm in ARMS:
        print(f"  {arm:10s} {passes[arm]}/{seeds} seeds  -> {'PASS' if passes[arm] >= 2 else 'FAIL'}")


if __name__ == "__main__":
    main()
