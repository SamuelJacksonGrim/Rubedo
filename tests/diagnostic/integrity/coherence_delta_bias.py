"""tests/diagnostic/integrity/coherence_delta_bias.py

Is coherence_delta's negative lean a measurement artifact?

coherence_impact compares cos(RAW field, history_mean) "before" with
cos(TANH(field + 0.5 vec), history_mean) "after". With vec = 0 nothing is
injected, so any nonzero result is pure bias from the raw-vs-tanh mismatch.
Run the gate's REF arm (seed 0, workload B) and log, per step, the bias
(impact of a zero vector), the real impact of the step's input, and the
like-for-like version (tanh before vs tanh after).
"""
import random
import numpy as np

from substrate import determinism
from tests.diagnostic.integrity import witness_composition_gate as g


def like_for_like(field, vec):
    hist = list(field.history)[-32:]
    if not hist:
        return 0.0
    hm = np.mean(hist, axis=0)
    def c(a):
        return float(np.dot(a, hm) / (np.linalg.norm(a) * np.linalg.norm(hm) + 1e-8))
    return c(np.tanh(field.field + vec * 0.5)) - c(np.tanh(field.field))


def main(seed=0, steps=500):
    bias, real, fair, fnorm, sat = [], [], [], [], []
    with determinism.deterministic(seed):
        gen, cycle, gov, ve, ledger, consumer, report, pretrained = g.build_all_on()
        pick = random.Random(seed)
        sids = list(g.RESONANCE_FAMILY_SOURCES)
        w = [g.RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        for _ in range(steps):
            src = pick.choices(sids, weights=w)[0]
            if pick.random() < 0.20:
                toks = g.WITNESS_PHRASES[pick.randrange(len(g.WITNESS_PHRASES))]
            else:
                toks = pick.choice(g.RESONANCE_FAMILY_SOURCES[src])
            vecs, known = gen.peek_batch([toks])
            f = cycle.field
            if known[0] and len(f.history):
                v = g.unit(vecs[0])
                bias.append(f.coherence_impact(np.zeros_like(v)))
                real.append(f.coherence_impact(v))
                fair.append(like_for_like(f, v))
                fnorm.append(float(np.linalg.norm(f.field)))
                sat.append(float(np.mean(np.abs(np.tanh(f.field)) > 0.95)))
            cycle.step(toks, source_id=src, origin_type="internal")
    a = lambda x: np.array(x)
    bias, real, fair = a(bias), a(real), a(fair)
    print(f"steps measured: {len(bias)}")
    print(f"bias (zero vector)     mean {bias.mean():+.4f}  median {np.median(bias):+.4f}  share<0 {np.mean(bias < 0):.2f}")
    print(f"real coherence_impact  mean {real.mean():+.4f}  median {np.median(real):+.4f}  share<0 {np.mean(real < 0):.2f}")
    print(f"real minus bias        mean {(real - bias).mean():+.4f}  share<0 {np.mean(real - bias < 0):.2f}")
    print(f"like-for-like (tanh)   mean {fair.mean():+.4f}  median {np.median(fair):+.4f}  share<0 {np.mean(fair < 0):.2f}")
    print(f"raw field norm         mean {np.mean(fnorm):.2f}   saturated dims (|tanh|>0.95) {np.mean(sat):.2f}")
    for lo, hi in [(0, 50), (50, 150), (150, 300), (300, 500)]:
        s = slice(lo, min(hi, len(bias)))
        print(f"  steps {lo:3d}-{hi:3d}: bias {bias[s].mean():+.4f}  real {real[s].mean():+.4f}  fair {fair[s].mean():+.4f}")


if __name__ == "__main__":
    import sys
    for s in [int(a) for a in sys.argv[1:] if a.isdigit()] or [0, 1, 2]:
        print(f"\n=== seed {s} (REF, workload B)")
        main(seed=s)
