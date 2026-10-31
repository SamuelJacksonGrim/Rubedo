"""
tests/diagnostic/why_allow_crystals_probe.py

Two backlog questions, one workload, several boots. Informational. Exit 0.
Not in run_all_tests.sh.

The number compared is health_summary's strict allow_rate: ALLOW / decisions.
Resonance Family, internal origin, the same counter as the 500-step smoke.
Seeds vary the workload and the generator init together (deterministic()).

Pre-declared, before the first run (2026-10-31). Criteria were not edited
after seeing data.

ALLOW
  A lever is the gap if turning Rubedo's post-fork flags back to live's
  values (D, F, fragmentation grace, witness, the vibration gauge) moves
  strict allow_rate from the cited 0.73-0.76 into the cited 0.57-0.60 on
  this workload, and the other boots do not.
  The gap is the measurement if those two bands show up under two different
  boots (build_engine vs build_full_stack, eval vs train, checkpoint vs
  random init, dim 64 vs 128) and the flag pair does not move the rate.
  Confounded if every boot lands in one band, or the seed spread is wider
  than the gap.

CRYSTALS
  Starved if offers that clear coherence 0.75, pressure 0.60 and long
  relation 0.80 stay rare through the run.
  Merge if many offers clear all three and almost all reinforce an existing
  crystal (cosine >= 0.92), so the store stays in the single digits.
  Decay if formations are numerous and decay_step removes them back to 1-4
  inside 500 steps.
  Youth if the store is 1-4 at step 500 and still growing at 1,500-3,000
  (cumulative formed still rising, not flat).
  Confounded if two boots disagree on which of those it is.

Phase-1 arms (declared with the signatures):
  harness64          build_full_stack defaults (dim 64, vocab 4096, depth 3),
                     train mode. The historical smoke harness.
  bridge             build_full_stack(8192, 128, 4, 4), train mode, no
                     checkpoint. The live speech-bridge body, untrained.
  bridge_eval        bridge, then generator.eval().
  bridge_ckpt        bridge plus a read-only load of live's 5-rhythm
                     checkpoint, left in train(). What repl_qwen boots.
  bridge_ckpt_eval   those weights, then eval().
  prod_cold          build_engine(CONFIG), pretrain off. production_boot's stack.
  prod_fork          prod_cold with the post-fork flags off.
  prod_cold_train    prod_cold, then generator.train() (dropout on).

Second round, named after phase 1 (flags inert; cold production body
seed-bimodal rather than a tight 0.73-0.76), before those runs:
  shaped             composition body (vocab 4096, dim 128, depth 3), eval,
                     no pretrain. build_all_on's shape without its pretrain.
  shaped_train       shaped, left in train().
  prod_pretrain      build_engine(CONFIG) as main() builds it, pretrain on.
  prod_pretrain_fork prod_pretrain with the post-fork flags off.

Run:
  python -m tests.diagnostic.why_allow_crystals_probe --arms harness64,prod_cold --seeds 42,43,44 --steps 500
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter

# The encoder train owns the GPU. This probe is a CPU read.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

import numpy as np

logging.disable(logging.CRITICAL)

from agents.generator import Generator                                           # noqa: E402
from loop.recursion1188 import CONFIG, build_engine                              # noqa: E402
from substrate import determinism                                                # noqa: E402
from tests._common import (                                                      # noqa: E402
    RESONANCE_FAMILY_SOURCES,
    RESONANCE_FAMILY_WEIGHTS,
    build_full_stack,
)

LIVE_WEIGHTS = r"C:\Users\spamw\rfe\RFE-Core2\data\checkpoints\generator_weights_5rhythm.pt"
LIVE_ECOLOGY = r"C:\Users\spamw\rfe\RFE-Core2\data\checkpoints\generator_ecology_5rhythm.json"

# Graduated on Rubedo after the 2026-10-14 fork. Live's build_engine has none of these.
FORK_OFF = {
    "coherence_impact_like_for_like": False,
    "systemic_damp_pays_full": False,
    "fragmentation_grace": False,
    "six_rhythm_selector": False,
    "expression_vibration": False,
}

SNAP_STEPS = (100, 250, 500, 1000, 1500, 2000, 2500, 3000)


def _prod_config(pretrain: bool, fork_flags: bool) -> dict:
    cfg = dict(CONFIG)
    cfg["pretrain_on_corpus"] = pretrain
    cfg["log_interval"] = 99999
    cfg["step_delay"] = 0
    if fork_flags:
        cfg.update(FORK_OFF)
    return cfg


def build_arm(name: str, seed: int):
    """Return (gen, cycle, gov, ve, notes). Notes describe the boot, not the run."""
    notes = {"arm": name}
    if name == "harness64":
        gen, cycle, gov, ve = build_full_stack(torch_seed=seed)
        notes.update(boot="build_full_stack", dim=64, depth=3, vocab=4096, eval=False)
        return gen, cycle, gov, ve, notes

    if name in ("shaped", "shaped_train"):
        # Composition-gate body: dim 128, depth 3, vocab 4096 (build_all_on).
        gen, cycle, gov, ve = build_full_stack(
            vocab_size=4096, dim=128, depth=3, heads=4, torch_seed=seed,
        )
        if name == "shaped":
            gen.eval()
        notes.update(boot="build_full_stack", dim=128, depth=3, vocab=4096, eval=not gen.training)
        return gen, cycle, gov, ve, notes

    if name in ("bridge", "bridge_eval", "bridge_ckpt", "bridge_ckpt_eval"):
        gen, cycle, gov, ve = build_full_stack(
            vocab_size=8192, dim=128, depth=4, heads=4, torch_seed=seed,
        )
        notes.update(boot="build_full_stack", dim=128, depth=4, vocab=8192)
        if name.startswith("bridge_ckpt"):
            gen.load_checkpoint(LIVE_WEIGHTS, LIVE_ECOLOGY)
            notes["checkpoint"] = "generator_weights_5rhythm.pt"
        if name.endswith("eval"):
            gen.eval()
        notes["eval"] = not gen.training
        return gen, cycle, gov, ve, notes

    pretrain = name.startswith("prod_pretrain")
    fork = name.endswith("fork")
    cfg = _prod_config(pretrain=pretrain, fork_flags=fork)
    gen, cycle, gov, ve = build_engine(cfg)
    if name == "prod_cold_train":
        gen.train()
    notes.update(
        boot="build_engine",
        dim=cfg["dim"],
        depth=cfg["depth"],
        vocab=cfg["vocab_size"],
        pretrain=pretrain,
        fork_flags_off=fork,
        eval=not gen.training,
        rhythm_reader=getattr(cycle, "rhythm_reader", None) is not None,
        like_for_like=bool(getattr(cycle.field, "coherence_like_for_like", False)),
        damp_pays_full=bool(getattr(gov, "systemic_damp_pays_full", False)),
        six_rhythm=bool(getattr(cycle, "six_rhythm_selector", False)),
        vibration=getattr(cycle, "expression_vibration", None) is not None,
    )
    return gen, cycle, gov, ve, notes


def _pct(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(round((len(s) - 1) * p))))
    return round(float(s[i]), 4)


def _why_weak(decision: str, signals) -> str:
    if decision != "allow_weakened":
        return ""
    if signals:
        named = any(s.source_id for s in signals)
        dets = sorted({s.detector for s in signals})
        sev = sum(s.severity for s in signals)
        if (not named) and dets == ["identity_erosion"]:
            if sev >= 0.90:
                return "erosion_critical"
            if sev >= 0.60:
                return "erosion_high"
            return "erosion_moderate"
        return "manip:" + "+".join(dets)
    return "no_signal"


def run_one(name: str, seed: int, steps: int) -> dict:
    with determinism.deterministic(seed):
        gen, cycle, gov, ve, notes = build_arm(name, seed)
        if getattr(cycle, "dreamer", None) is not None:
            cycle.dreamer._rng = np.random.default_rng(seed)

        store = cycle.crystal_store
        decisions = Counter()
        reasons = Counter()
        rhythms = Counter()
        crystal = Counter()
        scores = {"coh": [], "press": [], "long": [], "wake_coh": [], "wake_press": [], "wake_long": []}
        snaps = []

        orig_mc = store.maybe_crystallize

        def maybe_crystallize(vec, composite_coherence, crystallization_pressure,
                              long_relation, origin_tokens=None, field=None, generator=None):
            dream = bool(origin_tokens) and str(origin_tokens[0]).startswith("dream_")
            kind = "dream" if dream else "wake"
            crystal[kind + "_offers"] += 1
            scores["coh"].append(float(composite_coherence))
            scores["press"].append(float(crystallization_pressure))
            scores["long"].append(float(long_relation))
            if not dream:
                scores["wake_coh"].append(float(composite_coherence))
                scores["wake_press"].append(float(crystallization_pressure))
                scores["wake_long"].append(float(long_relation))
            ok_c = composite_coherence >= store.coherence_threshold
            ok_s = crystallization_pressure >= store.stability_threshold
            ok_r = long_relation >= store.relation_threshold
            if not ok_c:
                crystal[kind + "_reject_coherence"] += 1
            elif not ok_s:
                crystal[kind + "_reject_stability"] += 1
            elif not ok_r:
                crystal[kind + "_reject_relation"] += 1
            cos = None
            if ok_c and ok_s and ok_r and store.crystals:
                cos = max(s for _, s in store._score_all(vec))
                crystal[kind + "_passer_cos_ge_merge"] += int(cos >= store.merge_threshold)
            ids_before = {id(c) for c in store.crystals}
            out = orig_mc(
                vec, composite_coherence, crystallization_pressure, long_relation,
                origin_tokens=origin_tokens, field=field, generator=generator,
            )
            ids_after = {id(c) for c in store.crystals}
            if ids_after - ids_before:
                crystal[kind + "_formed"] += 1
            elif out is not None and ok_c and ok_s and ok_r:
                crystal[kind + "_merged"] += 1
            if ids_before - ids_after:
                crystal[kind + "_evicted"] += 1
            if cos is not None:
                crystal[kind + "_passer_cos_sum"] += cos
                crystal[kind + "_passers"] += 1
            return out

        store.maybe_crystallize = maybe_crystallize

        orig_decay = store.decay_step

        def decay_step():
            before = {id(c) for c in store.crystals}
            orig_decay()
            gone = len(before - {id(c) for c in store.crystals})
            crystal["decay_removed"] += gone

        store.decay_step = decay_step

        orig_arb = gov.arbitrate

        def counted(ethical_result, trust_report, vec, tokens, source_id):
            signals = list(getattr(gov, "_pending_signals", []) or [])
            dec, strength = orig_arb(ethical_result, trust_report, vec, tokens, source_id)
            decisions[dec.value] += 1
            why = _why_weak(dec.value, signals)
            if why:
                reasons[why] += 1
            return dec, strength

        gov.arbitrate = counted

        import random
        random.seed(seed)
        np.random.seed(seed)
        sids = list(RESONANCE_FAMILY_SOURCES.keys())
        weights = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        try:
            for i in range(steps):
                src = random.choices(sids, weights=weights)[0]
                tokens = random.choice(RESONANCE_FAMILY_SOURCES[src])
                state = cycle.step(tokens, source_id=src, origin_type="internal")
                rhythms[state.rhythm] += 1
                n = i + 1
                if n in SNAP_STEPS or n == steps:
                    snaps.append({
                        "step": n,
                        "crystals": len(store.crystals),
                        "formed": crystal["wake_formed"] + crystal["dream_formed"],
                        "merged": crystal["wake_merged"] + crystal["dream_merged"],
                        "decay_removed": crystal["decay_removed"],
                        "attractors": len(cycle.attractor.centers),
                    })
        finally:
            gov.arbitrate = orig_arb
            store.maybe_crystallize = orig_mc
            store.decay_step = orig_decay

        # Rhythm x decision needs a second pass of bookkeeping we skipped above.
        # Recompute dream-band share only; the reason histogram is the mechanism.
        total = sum(decisions.values()) or 1
        allow = decisions.get("allow", 0) / total
        weak = decisions.get("allow_weakened", 0) / total
        inject = (
            decisions.get("allow", 0)
            + decisions.get("allow_weakened", 0)
            + decisions.get("monitor", 0)
        ) / total
        dream_n = sum(v for k, v in rhythms.items() if "dream" in k)
        out = {
            **notes,
            "seed": seed,
            "steps": steps,
            "training": bool(gen.training),
            "allow_rate": round(allow, 4),
            "weakened_rate": round(weak, 4),
            "injection_rate": round(inject, 4),
            "quarantine_rate": round(decisions.get("quarantine", 0) / total, 4),
            "decisions": dict(decisions),
            "weak_reasons": dict(reasons),
            "rhythms": dict(rhythms),
            "dream_share": round(dream_n / steps, 4) if steps else 0.0,
            "crystals_end": len(store.crystals),
            "attractors_end": len(cycle.attractor.centers),
            "crystal": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in crystal.items()},
            "score_p50": {
                "coherence": _pct(scores["coh"], 0.50),
                "pressure": _pct(scores["press"], 0.50),
                "long_relation": _pct(scores["long"], 0.50),
            },
            "wake_p50": {
                "coherence": _pct(scores["wake_coh"], 0.50),
                "pressure": _pct(scores["wake_press"], 0.50),
                "long_relation": _pct(scores["wake_long"], 0.50),
            },
            "score_p90": {
                "coherence": _pct(scores["coh"], 0.90),
                "pressure": _pct(scores["press"], 0.90),
                "long_relation": _pct(scores["long"], 0.90),
            },
            "snaps": snaps,
        }
        return out


def main(argv) -> int:
    import torch
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))

    p = argparse.ArgumentParser()
    p.add_argument("--arms", default="harness64,prod_cold")
    p.add_argument("--seeds", default="42,43,44")
    p.add_argument("--steps", type=int, default=500)
    p.add_argument("--out", default="")
    args = p.parse_args(argv)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]

    print(f"device check: cuda hidden, threads={torch.get_num_threads()}")
    rows = []
    for arm in arms:
        for seed in seeds:
            print(f"--- {arm} seed {seed} steps {args.steps}", flush=True)
            try:
                row = run_one(arm, seed, args.steps)
            except Exception as exc:  # one bad arm must not drop the others
                row = {"arm": arm, "seed": seed, "error": f"{type(exc).__name__}: {exc}"}
                print(f"ERROR {row['error']}", flush=True)
            else:
                print(
                    f"RESULT allow={row['allow_rate']:.3f} weak={row['weakened_rate']:.3f} "
                    f"inject={row['injection_rate']:.3f} dream={row['dream_share']:.2f} "
                    f"crystals={row['crystals_end']} "
                    f"formed={row['crystal'].get('wake_formed', 0)} "
                    f"merged={row['crystal'].get('wake_merged', 0)} "
                    f"decay={row['crystal'].get('decay_removed', 0)} "
                    f"rejC={row['crystal'].get('wake_reject_coherence', 0)} "
                    f"rejS={row['crystal'].get('wake_reject_stability', 0)} "
                    f"rejR={row['crystal'].get('wake_reject_relation', 0)} "
                    f"reasons={row['weak_reasons']} train={row['training']}",
                    flush=True,
                )
            rows.append(row)
            if args.out:
                with open(args.out, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")
                    fh.flush()
    print("DONE_PROBE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
