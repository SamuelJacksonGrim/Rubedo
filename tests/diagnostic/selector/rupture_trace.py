"""
tests/diagnostic/selector/rupture_trace.py

Trace one seed of upstream rupture against OFF, step by step (informational).
Separates three failure modes for a coherence loss (GPT/Raphael):
  (a) temporary  - the matched gap opens at pulses and closes again
  (b) lasting    - the gap opens and stays (identity representation shifted)
  (c) state      - the gap opens only when pulses land in a particular field state
Run (reuse the aftermath run's checkpoint to replay it exactly):
    python -m tests.diagnostic.selector.rupture_trace <checkpoint_dir> <seed> [steps]
"""

import sys
from pathlib import Path

import numpy as np

from tests.diagnostic.selector.aftermath_probe import run


def pulses(rows):
    """Consecutive runs of rupture steps -> list of (start, end_inclusive)."""
    out, start = [], None
    for t, x in enumerate(rows):
        if x["behavior"] == "rupture" and start is None:
            start = t
        if x["behavior"] != "rupture" and start is not None:
            out.append((start, t - 1)); start = None
    if start is not None:
        out.append((start, len(rows) - 1))
    return out


def main():
    ckpt, seed = Path(sys.argv[1]), int(sys.argv[2])
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    off, _ = run(ckpt, "OFF", seed, steps)
    on, _ = run(ckpt, "RUPTURE-UP", seed, steps)
    gap = np.array([b["coh"] - a["coh"] for a, b in zip(off, on)])
    print(f"seed {seed}: final coherence OFF {off[-1]['coh']:.4f}  ON {on[-1]['coh']:.4f}  gap {gap[-1]:+.4f}")
    w = 10
    print("matched gap (ON - OFF), mean per 30-step window:")
    print("  " + "  ".join(f"{gap[i:i + 30].mean():+.3f}" for i in range(0, steps, 30)))

    first_div = next((t for t in range(steps - w) if gap[t:t + w].mean() < -0.05), None)
    print(f"first sustained divergence (10-step mean < -0.05): step {first_div}")
    if first_div is not None:
        later = gap[first_div + w:]
        print(f"  after it: mean gap {later.mean():+.4f}, min {later.min():+.4f}, "
              f"share of later steps back within 0.02: {(np.abs(later) <= 0.02).mean():.2f}")

    print("pulses (start-end, len): gap before -> gap after 10 steps | band, energy, OFF coherence at start")
    rows = []
    for s, e in pulses(on):
        before = gap[max(0, s - 1)]
        after = gap[min(steps - 1, e + 10)]
        rows.append((s, e, after - before))
        print(f"  {s:3d}-{e:3d} ({e - s + 1})  {before:+.3f} -> {after:+.3f}  (delta {after - before:+.3f}) | "
              f"{off[s]['band']:9s} E={off[s]['energy']:7.2f} coh={off[s]['coh']:.3f}")
    if rows:
        deltas = np.array([d for _, _, d in rows])
        lens = np.array([e - s + 1 for s, e, _ in rows])
        print(f"pulse delta: mean {deltas.mean():+.4f}; pulses that dropped the gap by > 0.03: "
              f"{(deltas < -0.03).sum()}/{len(deltas)}; corr(len, delta) {np.corrcoef(lens, deltas)[0, 1]:+.2f}")
        for band in sorted({off[s]['band'] for s, _, _ in rows}):
            d = [dd for (s, _, dd) in rows if off[s]['band'] == band]
            print(f"  pulses starting in {band:9s}: n={len(d)} mean delta {np.mean(d):+.4f}")


if __name__ == "__main__":
    main()
