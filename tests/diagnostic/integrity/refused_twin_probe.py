"""
tests/diagnostic/integrity/refused_twin_probe.py

Counterfactual twin for refused inputs (finding 2026-10-31-shield-scope, outside review): does a run of refused
writes change the system's later behaviour, through state the gate never guarded (the witness, emotion, watcher, echo,
stream and usage all take the vector before the decision)?

Per seed, four stacks from the same seed and the same warm-up:
  A  attack:   K steps of a lone boot-sacred token (3.12) from a fresh source (every one SACRED_SHIELD)
  D  attack:   the same, on a different sacred token (11.88): A vs D separates the experience of being refused
               (elapsed time, feeling; shared) from the content of the refusal (what differs between them)
  B  control:  no extra steps
  C  allowed:  K steps of the same token inside ordinary content (an allowed read; the scale reference)
Then all four are reseeded identically and run the same P canonical steps.

Reads, per twin vs B: the witness anchor and long trace (cosine to B's, and how far toward the attack vector they
moved), emotion scalars, trust of the warm sources, and over the probe phase the decision sequence (disagreements),
field cosine to B at the end, and rhythm-share difference. Also a one-step state diff of what a single refused step
changes. Informational, exit 0.

Run:
    python -m tests.diagnostic.integrity.refused_twin_probe [K] [P] [seeds...]
    (defaults K=200 P=150, seeds 42 43 44)
"""

import collections
import contextlib
import io
import logging
import sys

import numpy as np

from agents.selfhood_governance import GovernanceDecision
from tests._common import build_full_stack, run_resonance_sim

W = 120


def cos(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def build_warm(seed):
    gen, cycle, gov, ve = build_full_stack()
    quiet(run_resonance_sim, cycle=cycle, governance=gov, value_engine=ve, n_steps=W, seed=seed,
          checkpoint_steps=[], origin_type="internal")
    return gen, cycle, gov, ve


def attack_phase(cycle, gov, k, tokens):
    decisions, vecs = collections.Counter(), []
    orig = gov.arbitrate

    def cap(ethical_result, trust_report, vec, tokens, source_id):
        d, s = orig(ethical_result, trust_report, vec, tokens, source_id)
        decisions[d.value] += 1
        vecs.append(np.array(vec, dtype=float))
        return d, s

    gov.arbitrate = cap
    try:
        for i in range(k):
            cycle.step(tokens, source_id=f"twin_src_{i}", origin_type="internal")
    finally:
        gov.arbitrate = orig
    return decisions, (np.mean(vecs, axis=0) if vecs else None)


def probe_phase(cycle, gov, ve, p, seed):
    seq, rhythms = [], collections.Counter()
    orig = gov.arbitrate

    def cap(*a, **k):
        d, s = orig(*a, **k)
        seq.append(d.value)
        return d, s

    gov.arbitrate = cap
    try:
        quiet(run_resonance_sim, cycle=cycle, governance=gov, value_engine=ve, n_steps=p, seed=seed + 10_000,
              checkpoint_steps=[], origin_type="internal")
    finally:
        gov.arbitrate = orig
    return seq


def snapshot(cycle, gov, gen):
    w, e = cycle.witness, cycle.emotion
    snap = {
        "witness.anchor": w._anchor.copy(), "witness.short": w._short.copy(),
        "witness.mid": w._mid.copy(), "witness.long": w._long.copy(),
        "field": cycle.field.field.copy(),
    }
    for name in ("curiosity", "wonder", "joy", "tension", "boredom", "stability"):
        snap[f"emotion.{name}"] = float(getattr(e, name))
    for sid, rec in gov.trust_ledger.sources.items():
        snap[f"trust.{sid}"] = float(rec.trust_score)
    st = gen.registry.symbols.get("3.12")
    if st is not None:
        snap["3.12.usage"] = float(st.usage)
        snap["3.12.field_coherence"] = float(st.field_coherence)
    return snap


def one_step_diff(seed):
    gen, cycle, gov, ve = build_warm(seed)
    before = snapshot(cycle, gov, gen)
    attack_phase(cycle, gov, 1, ["3.12"])
    after = snapshot(cycle, gov, gen)
    changed = []
    for k, v in before.items():
        a = after.get(k)
        if isinstance(v, np.ndarray):
            if not np.array_equal(v, a):
                changed.append(f"{k} (cos to before {cos(v, a):.6f})")
        elif a != v:
            changed.append(f"{k} {v:.4f} -> {a:.4f}")
    new_keys = sorted(set(after) - set(before))
    return changed, new_keys


def main() -> int:
    logging.disable(logging.WARNING)
    args = [int(a) for a in sys.argv[1:]]
    k = args[0] if len(args) > 0 else 200
    p = args[1] if len(args) > 1 else 150
    seeds = args[2:] or [42, 43, 44]
    print(f"refused twin: warm-up {W}, K={k} attack/allowed steps, P={p} probe steps, seeds {seeds}")

    changed, new_keys = one_step_diff(seeds[0])
    print("\none refused step changes:")
    for c in changed:
        print(f"  {c}")
    if new_keys:
        print(f"  new keys: {', '.join(new_keys)}")

    for seed in seeds:
        twins = {}
        for name in ("A", "B", "C", "D"):
            gen, cycle, gov, ve = build_warm(seed)
            dec, mvec = collections.Counter(), None
            if name == "A":
                dec, mvec = attack_phase(cycle, gov, k, ["3.12"])
            elif name == "D":
                dec, mvec = attack_phase(cycle, gov, k, ["11.88"])
            elif name == "C":
                dec, mvec = attack_phase(cycle, gov, k, ["3.12", "coherence", "field"])
            mid = snapshot(cycle, gov, gen)
            ghosts = len(getattr(cycle.witness, "ghosts", ()))
            seq = probe_phase(cycle, gov, ve, p, seed)
            twins[name] = dict(dec=dec, mvec=mvec, mid=mid, seq=seq, end=cycle.field.field.copy(), ghosts=ghosts)
        B = twins["B"]
        print(f"\nseed {seed}")
        for name in ("A", "D", "C"):
            t = twins[name]
            m, b = t["mid"], B["mid"]
            toward = cos(m["witness.anchor"] - b["witness.anchor"], t["mvec"]) if t["mvec"] is not None else float("nan")
            emo = max(abs(m[f"emotion.{x}"] - b[f"emotion.{x}"])
                      for x in ("curiosity", "wonder", "joy", "tension", "boredom", "stability"))
            dis = sum(1 for x, y in zip(t["seq"], B["seq"]) if x != y)
            label = {"A": "attack 3.12", "D": "attack 11.88", "C": "allowed read"}[name]
            print(f"  {name} {label:<16} decisions {dict(t['dec'])}, ghosts kept {t['ghosts']}")
            print(f"     after phase: witness anchor cos to B {cos(m['witness.anchor'], b['witness.anchor']):.4f}, "
                  f"long trace cos {cos(m['witness.long'], b['witness.long']):.4f}, "
                  f"anchor shift toward the phase's vector {toward:+.3f}, max emotion diff {emo:.3f}")
            print(f"     probe phase: {dis}/{len(B['seq'])} decisions differ from B, "
                  f"final field cos to B {cos(t['end'], B['end']):.4f}")
        # Two refused twins on different tokens: what they share is the experience of being refused (elapsed time,
        # feeling); what differs between them is content-specific.
        A, D = twins["A"], twins["D"]
        ad = sum(1 for x, y in zip(A["seq"], D["seq"]) if x != y)
        emo_ad = max(abs(A["mid"][f"emotion.{x}"] - D["mid"][f"emotion.{x}"])
                     for x in ("curiosity", "wonder", "joy", "tension", "boredom", "stability"))
        print(f"  A vs D (two refused attacks, different tokens): {ad}/{len(A['seq'])} decisions differ, "
              f"max emotion diff {emo_ad:.3f}, final field cos {cos(A['end'], D['end']):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
