"""
tests/diagnostic/selector/witness_long_probe.py

Long-run witness (informational). Does witness's small coherence cost level off or
keep falling, and does the field stay receptive while it does? (Coherence alone
can't tell: a field that stops changing can look stable because it stopped
taking anything in.)

Arms per seed, one invocation, same pretrained checkpoint, pinned RNGs, paired
by step (compare within this run only: wall-clock reads make runs vary between
invocations, finding 2026-10-14-witness-aftermath-and-upstream-rupture).

PRE-DECLARED (written before the first run, 2026-10-14):
  plateau       the matched coherence gap (WITNESS - OFF) levels off: mean gap over
                the last third is not more than 0.01 below the middle third.
  receptive     witness retention (field turns toward the witnessed input, d1)
                in the last third is >= 50% of the first third, and still above
                OFF's on the same phrases in the last third.
  accumulated   at the end, the field leans toward what it has witnessed:
                cos(field_end, mean of witnessed input directions) WITNESS > OFF.
  Pass = all three on >= 2 of 3 seeds. Plateau fails -> bound witness strength.
  Receptive fails -> witness is wearing out, not stabilizing.

Run:
    python -m tests.diagnostic.selector.witness_long_probe <checkpoint_dir> [steps] [seeds]
"""

import sys
from pathlib import Path

import numpy as np

from tests.diagnostic.selector.aftermath_probe import run, cos


def main():
    ckpt = Path(sys.argv[1])
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1200
    seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    third = steps // 3
    for seed in range(1, seeds + 1):
        off, _ = run(ckpt, "OFF", seed, steps)
        on, _ = run(ckpt, "WITNESS", seed, steps)
        gap = np.array([b["coh"] - a["coh"] for a, b in zip(off, on)])
        g1, g2, g3 = gap[:third].mean(), gap[third:2 * third].mean(), gap[2 * third:].mean()

        ev = [t for t, x in enumerate(on) if x["behavior"] == "witness" and x["u"] is not None and 1 <= t < steps - 1]
        def ret(rows, ts):
            v = [cos(rows[t + 1]["field"], on[t]["u"]) - cos(rows[t - 1]["field"], on[t]["u"]) for t in ts]
            return float(np.median(v)) if v else float("nan")
        first = [t for t in ev if t < third]
        last = [t for t in ev if t >= 2 * third]
        r_on1, r_on3, r_off3 = ret(on, first), ret(on, last), ret(off, last)
        r_off1 = ret(off, first)   # context (added after the first run): does OFF's retention decay too?

        witnessed = np.mean([on[t]["u"] / (np.linalg.norm(on[t]["u"]) + 1e-8) for t in ev], axis=0)
        acc_on, acc_off = cos(on[-1]["field"], witnessed), cos(off[-1]["field"], witnessed)

        plateau = g3 >= g2 - 0.01
        receptive = (r_on3 >= 0.5 * r_on1) and (r_on3 > r_off3)
        accumulated = acc_on > acc_off
        print(f"\n=== seed {seed} ({steps} steps, {len(ev)} witness steps)")
        print(f"  matched gap by third: {g1:+.4f}  {g2:+.4f}  {g3:+.4f}   plateau {'PASS' if plateau else 'FAIL'}")
        print(f"  gap per 100 steps: " + " ".join(f"{gap[i:i + 100].mean():+.3f}" for i in range(0, steps, 100)))
        print(f"  retention d1: first third {r_on1:+.4f}  last third {r_on3:+.4f} (OFF last third {r_off3:+.4f})"
              f"   receptive {'PASS' if receptive else 'FAIL'}")
        print(f"  context, OFF retention: first third {r_off1:+.4f} -> last third {r_off3:+.4f}"
              f"  (ON keeps {r_on3 / r_on1 if r_on1 else float('nan'):.0%}, OFF keeps "
              f"{r_off3 / r_off1 if r_off1 else float('nan'):.0%})")
        print(f"  accumulated cos(field_end, witnessed): WITNESS {acc_on:+.4f}  OFF {acc_off:+.4f}"
              f"   {'PASS' if accumulated else 'FAIL'}")


if __name__ == "__main__":
    main()
