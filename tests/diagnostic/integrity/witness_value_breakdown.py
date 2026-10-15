"""
tests/diagnostic/integrity/witness_value_breakdown.py

Why does witness weaken the value ecology on the witnessing workload (gate B)?
Splits every emergent value by whether its symbol is a witness-phrase token, and
compares REF (all-ON) vs WIT (all-ON + witness) on the same replay-exact run.

Hypothesis (written before the run, 2026-10-15): witness steps inject the raw
input, so their coherence contribution is low or negative; values built on
witness tokens get weak/negative reinforcement and thin out (and the ⊘ consumer
demotes thin values). If true: the loss concentrates in witness-token values and
non-witness values are about unchanged. If false (non-witness values also drop),
witness is degrading the value ecology broadly.

Run:  python -m tests.diagnostic.integrity.witness_value_breakdown [seeds...]
"""
import sys
from collections import Counter

import numpy as np

from tests.diagnostic.integrity.witness_composition_gate import run, WITNESS_PHRASES

WTOK = {t for p in WITNESS_PHRASES for t in p}


def summarize(values, group):
    sel = [v for v in values if (v[0] in WTOK) == group]
    alive = [v for v in sel if v[2] < 0]
    return dict(total=len(sel), active=len(alive),
                mean_strength=float(np.mean([v[1] for v in alive])) if alive else float("nan"),
                coh=float(np.mean([v[3] for v in sel])) if sel else float("nan"),
                polarity=dict(Counter(v[4] for v in alive)))


def main():
    seeds = [int(a) for a in sys.argv[1:]] or [43, 44]
    for seed in seeds:
        h_ref, _ = run(seed, "B", False)
        h_wit, _ = run(seed, "B", True)
        print(f"\n=== seed {seed}  (workload B)")
        for label, group in (("witness-token values", True), ("all other values", False)):
            a, b = summarize(h_ref["values"], group), summarize(h_wit["values"], group)
            print(f"  {label}:")
            print(f"    REF total {a['total']:3d} active {a['active']:3d} mean_strength {a['mean_strength']:.3f} "
                  f"coh_contrib {a['coh']:+.4f} polarity {a['polarity']}")
            print(f"    WIT total {b['total']:3d} active {b['active']:3d} mean_strength {b['mean_strength']:.3f} "
                  f"coh_contrib {b['coh']:+.4f} polarity {b['polarity']}")


if __name__ == "__main__":
    main()
