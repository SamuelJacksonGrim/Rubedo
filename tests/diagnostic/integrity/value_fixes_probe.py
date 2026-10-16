"""
tests/diagnostic/integrity/value_fixes_probe.py

Measurement for levers C–G (docs/EXPERIMENTAL_LEVERS.md), alone and all five
together, against REF. Bugs A and B are always on; they are not arms.

Each cell is its own substrate.determinism.deterministic(seed) context, and the
workload is drawn from random.Random(seed), the witness gate's pairing. That is
NOT the standing composition probe's single process (it does not reseed between
the consumer-off and consumer-on builds, and the workload shares the global
RNG). A mismatch with a previously published composition number is expected.
Do not retune anything below to chase it.

Arms: REF C D E F G ALL. Seeds: 42 43 44. Two kinds:
  composition   standing all-ON stack, canonical Resonance Family, 500 steps.
                No extra watcher.evaluate. Strong band is paired with the same
                arm built without the ⊘ consumer (the standing gate's ref).
  witness       the witness gate's workload B only (20% witness phrases), with
                the gate's post-step watcher.evaluate, so identity and
                receptivity use the gate's definition. REF here means the same
                arm without witness, not the REF arm.

PRE-DECLARED before the first measurement run (2026-10-15). These bars are not
moved after the numbers. A clean "values grew" is the alarm, not the trophy.
"Values stop starving" is not "values mean something".

Composition, required 3/3 seeds (standing gate, copied):
  injection_rate >= 0.95, quarantine_rate == 0, all sources trust maxed,
  HHI < 0.30, bonds >= 1, active_values >= 30 (strength > 1, not the ACTIVE
  tier), strong_values >= _strong(consumer-off) - 1, lambda gain > 0.5,
  consumer demotions >= 1, mean live strength > 1.0.
  strong_values is health_summary's count (standing probe). The witness kind
  uses _strong on both sides, which is what witness_composition_gate does.

Witness B, copied from witness_composition_gate.py:
  identity    anchor drift <= 2 x no-witness + 0.01; field lock <= 2 x + 1e-5;
              matched coherence mean >= -0.05; no 10-step mean below -0.10.
              Required >= 2/3.
  receptivity median retention d1 at witness steps, witness > no-witness.
              Required >= 2/3.
  non-vacuous witness fires >= 50 on every seed, else that seed is void.
  composition the same health checks, witness vs that arm's no-witness strong
              count, required 3/3. A check that holds without witness and fails
              with it is a break.

Ecology alarms, composition kind (canonical workload), arm vs the REF arm.
An ABSOLUTE alarm that also fires on REF is a mis-set bar: report it, and do
not count it against a lever. Relative alarms have no such escape.

  saturation     share of live values with strength >= 4.9 is > 0.25, OR mean
                 live strength >= 4.5 (the CORE line as a population mean).
  core inflation core > max(ref_core + 2, 2 * ref_core) on any seed.
  F core         arms F and ALL only: core > ref_core + 1 on any seed, OR the
                 sum of core across the three seeds > ref sum + 2. A made the
                 manipulation check real; F must not accelerate promotion past
                 one extra on a seed or two extra across the gate.
  monoculture    strength-HHI >= 0.50, OR some polarity holds >= 0.85 of live
                 values AND that share rose by >= 0.25 against REF.
  collapse       live < max(10, 0.5 * ref live) when ref live >= 10.
  indiscriminate mean strength >= ref mean + 1.0 AND live >= ref live AND
                 fraction of live values with reinforcement_count > 0 >= 0.95
                 AND near-cap share > 0.10. A mean rise alone is not this alarm
                 and is not a success. It is recorded.
  C credit       with dream_consolidation on, any dream offer whose tokens
                 include a dream_<hex> key is the wrong credit. Offers that
                 never clear relation 0.80 (boosts stay 0) are INERT, not a
                 pass: the store's 0.80 is sacred and is not lowered.
  D missed       with the like-for-like lever on, mean |coherence_delta| > 0.05
                 (the raw-vs-tanh bias scale). ~0 is the honest number, not a
                 failure. Between 0.02 and 0.05 is reported as "shrunk", not
                 retuned into a pass or a fail.
  G degenerate   with satisfaction_from_emotion on, valence std < 0.02 OR
                 (max - min) < 0.05. A flat valence is a constant bonus. Joy's
                 step-to-step change is recorded as the alternative read; the
                 formula is not switched after seeing it.

Witness starvation (workload B, witness vs the same arm without witness) is a
question, not a trophy. "Still starves" if total live strength under witness
is < 0.95 of the no-witness arm, OR allow count is < 0.90 of it. The finding's
drop was much larger than 10%; this bar does not get loosened to claim a fix.

A lever is a CANDIDATE for default-on only if composition is clean 3/3,
witness identity and receptivity and non-vacuous and witness-composition hold,
and no ecology alarm fires (inert C, missed D, degenerate G, and F/ALL core
included). Graduation still waits on the adversarial suite, and a candidate
that did not change the thing it exists to change does not get graduated.
ALL is reported, not graduated as a bundle.

Informational. exit 0 if the run finishes, exit 1 if a cell throws. Not in
run_all_tests.sh. Resumes from data/value_fixes_probe.json.

Run:
    python -m tests.diagnostic.integrity.value_fixes_probe
    python -m tests.diagnostic.integrity.value_fixes_probe --arms REF,C --seeds 42
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import traceback
from collections import Counter
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

import numpy as np

logging.disable(logging.CRITICAL)
sys.path.insert(0, ".")

from substrate import determinism                                               # noqa: E402
from loop.recursion1188 import apply_value_levers                               # noqa: E402
from tests._common import (                                                      # noqa: E402
    RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS, health_summary,
)
from tests.diagnostic.integrity.all_levers_composition_probe import (            # noqa: E402
    build_all_on, _strong,
)
from tests.diagnostic.integrity.witness_composition_gate import (                # noqa: E402
    WITNESS_PHRASES, attach_witness, cos,
)

OFFICIAL_STEPS = 500
SEEDS = (42, 43, 44)
ARMS = ("REF", "C", "D", "E", "F", "G", "ALL", "DF", "DE", "DEF", "CDEF")
KINDS = ("composition", "witness")

# Absolute / relative bars. Names match the docstring. Do not edit after a run.
SAT_CAP_SHARE = 0.25
SAT_MEAN = 4.5
CORE_PAD = 2
F_CORE_PAD = 1
F_CORE_SUM_PAD = 2
MONO_HHI = 0.50
MONO_SHARE = 0.85
MONO_RISE = 0.25
COLLAPSE_FLOOR = 10
COLLAPSE_FRAC = 0.5
GROW_MEAN = 1.0
GROW_REINF = 0.95
GROW_CAP = 0.10
D_ABS_CD = 0.05
G_STD = 0.02
G_RANGE = 0.05
STARVE_STRENGTH = 0.95
STARVE_ALLOW = 0.90
NEAR_CAP = 4.9

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ROOT / "data" / "value_fixes_probe.json"


def lever_config(arm: str) -> dict:
    # "REF" = all off, "ALL" = all on; any other arm name is a set of lever
    # letters, e.g. "DF" or "DEF" for combinations (added 2026-10-15 after F alone
    # proved entangled with D: on dream-band steps the coherence_delta artifact
    # makes reinforcement ~0 even when the step is paid as ALLOW).
    if arm == "REF":
        letters = set()
    elif arm == "ALL":
        letters = set("CDEFG")
    else:
        letters = set(arm)
    return {
        "dream_consolidation": "C" in letters,
        "coherence_impact_like_for_like": "D" in letters,
        "value_alignment_signal": "E" in letters,
        "systemic_damp_pays_full": "F" in letters,
        "satisfaction_from_emotion": "G" in letters,
    }


def _stats(xs) -> dict:
    if not xs:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None,
                "mean_abs": None, "mean_abs_delta": None}
    a = np.asarray(xs, dtype=float)
    delta = np.abs(np.diff(a)) if a.size > 1 else np.zeros(0)
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "std": float(a.std()),
        "min": float(a.min()),
        "max": float(a.max()),
        "mean_abs": float(np.abs(a).mean()),
        "mean_abs_delta": float(delta.mean()) if delta.size else 0.0,
    }


def ecology(ve) -> dict:
    live = [v for v in ve.values.values() if v.dissolved_at_step < 0]
    strengths = np.array([float(v.strength) for v in live], dtype=float)
    total = float(strengths.sum()) if strengths.size else 0.0
    polarity = Counter(v.polarity.value for v in live)
    reinforced = sum(1 for v in live if v.reinforcement_count > 0)
    n = len(live)
    return {
        "live": n,
        "dissolved": sum(1 for v in ve.values.values() if v.dissolved_at_step >= 0),
        "active_tier": int(polarity.get("active", 0)),
        "polarity": dict(polarity),
        "mean_strength": float(strengths.mean()) if n else 0.0,
        "total_strength": total,
        "near_cap": int((strengths >= NEAR_CAP).sum()) if n else 0,
        "core": sum(1 for v in live if v.promoted_to_sacred),
        "dream_boosts": int(sum(v.dream_reinforced_count for v in ve.values.values())),
        "strength_hhi": float(((strengths / total) ** 2).sum()) if total > 0 else 0.0,
        "reinforced_frac": (reinforced / n) if n else 0.0,
        "max_strength": float(strengths.max()) if n else 0.0,
    }


def instrument(cycle, gov, ve):
    decisions = Counter()
    orig_arb = gov.arbitrate

    def counted(*args, **kwargs):
        dec, strength = orig_arb(*args, **kwargs)
        decisions[dec.value] += 1
        return dec, strength

    gov.arbitrate = counted

    trace = {"cd": [], "sat": [], "align": [], "valence": [], "term": [],
             "djoy": [], "pay_override": 0}
    orig_eval = ve.evaluate_experience

    def traced(report):
        out = orig_eval(report)
        trace["cd"].append(float(report.coherence_delta))
        trace["sat"].append(float(report.emotional_satisfaction))
        trace["align"].append(float(getattr(report, "field_alignment", 0.0)))
        trace["valence"].append(float(cycle.emotion.valence))
        term = getattr(ve, "_step_coherence_term", None)
        trace["term"].append(float(report.coherence_delta if term is None else term))
        return out

    ve.evaluate_experience = traced

    orig_emit = gov.emit_feedback

    def emit_wrap(*args, **kwargs):
        feedback = orig_emit(*args, **kwargs)
        payment = (feedback.outcome_metrics or {}).get("value_payment")
        if payment and payment != feedback.decision:
            trace["pay_override"] += 1
        return feedback

    gov.emit_feedback = emit_wrap

    dream = {"offers": 0, "formed": 0, "dream_key_offers": 0, "source_offers": 0,
             "rel_sum": 0.0, "rel_max": None, "rel_min": None}
    in_dream = {"flag": False}
    orig_dream = cycle.dreamer.dream

    def dream_wrap(*args, **kwargs):
        in_dream["flag"] = True
        try:
            return orig_dream(*args, **kwargs)
        finally:
            in_dream["flag"] = False

    cycle.dreamer.dream = dream_wrap
    orig_mc = cycle.crystal_store.maybe_crystallize

    def mc_wrap(*args, **kwargs):
        crystal = orig_mc(*args, **kwargs)
        if in_dream["flag"]:
            if "long_relation" in kwargs:
                rel = float(kwargs["long_relation"])
            elif len(args) >= 4:
                rel = float(args[3])
            else:
                rel = 0.0
            tokens = kwargs.get("origin_tokens")
            if tokens is None and len(args) >= 5:
                tokens = args[4]
            tokens = list(tokens or [])
            dream["offers"] += 1
            dream["rel_sum"] += rel
            dream["rel_max"] = rel if dream["rel_max"] is None else max(dream["rel_max"], rel)
            dream["rel_min"] = rel if dream["rel_min"] is None else min(dream["rel_min"], rel)
            if crystal is not None:
                dream["formed"] += 1
            if any(str(t).startswith("dream_") for t in tokens):
                dream["dream_key_offers"] += 1
            elif tokens:
                dream["source_offers"] += 1
        return crystal

    cycle.crystal_store.maybe_crystallize = mc_wrap
    return decisions, trace, dream


def _pick_tokens(pick, workload, src):
    if workload == "B" and pick.random() < 0.20:
        return WITNESS_PHRASES[pick.randrange(len(WITNESS_PHRASES))], "witness"
    return pick.choice(RESONANCE_FAMILY_SOURCES[src]), "canonical"


def run_arm(seed, arm, steps, with_consumer, with_witness, workload):
    """One build, one deterministic context. Returns metrics and optional rows."""
    levers = lever_config(arm)
    with determinism.deterministic(seed):
        gen, cycle, gov, ve, ledger, consumer, _report, pretrained = build_all_on(
            with_consumer=with_consumer)
        apply_value_levers(cycle, gov, ve, levers)
        if with_witness:
            attach_witness(gen, cycle)
        decisions, trace, dream = instrument(cycle, gov, ve)
        pick = random.Random(seed)
        sids = list(RESONANCE_FAMILY_SOURCES)
        weights = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        rows = [] if with_witness or workload == "B" else None
        # Workload B's no-witness arm still needs rows: identity compares both.
        if workload == "B":
            rows = []
        for _ in range(steps):
            src = pick.choices(sids, weights=weights)[0]
            tokens, kind = _pick_tokens(pick, workload, src)
            joy_before = float(cycle.emotion.joy)
            if rows is not None:
                vecs, known = gen.peek_batch([tokens])
            state = cycle.step(tokens, source_id=src, origin_type="internal")
            trace["djoy"].append(float(cycle.emotion.joy) - joy_before)
            if rows is not None:
                field = cycle.field.field
                if np.linalg.norm(field) > 1e-8:
                    coh = cycle.watcher.evaluate(
                        field / (np.linalg.norm(field) + 1e-8),
                        cycle.witness.current_anchor(),
                        cycle.field.resonate(),
                    ).composite
                else:
                    coh = 0.0
                rows.append({
                    "kind": kind,
                    "behavior": state.extras.get("behavior", state.rhythm),
                    "field": field.copy(),
                    "coh": coh,
                    "anchor": np.array(cycle.witness.current_anchor(), dtype=float),
                    "u": vecs[0] if known[0] else None,
                })
        h = health_summary(cycle, gov, ve, decisions)
        live_strengths = [v.strength for v in ve.values.values() if v.dissolved_at_step < 0]
        h["mean_strength"] = (sum(live_strengths) / len(live_strengths)) if live_strengths else 0.0
        h["strong"] = _strong(ve)
        h["gain"] = float(ledger.gain())
        h["demotions"] = int(consumer.snapshot()["demotions_total"]) if consumer is not None else 0
        h["decisions"] = dict(decisions)
        long_anchor = np.asarray(cycle.witness.long_anchor(), dtype=float)
        payload = {
            "pretrained": bool(pretrained),
            "health": {k: (float(v) if isinstance(v, (float, np.floating)) else v)
                       for k, v in h.items() if k != "decisions"},
            "decisions": {str(k): int(v) for k, v in decisions.items()},
            "ecology": ecology(ve),
            "trace": {
                "cd": _stats(trace["cd"]),
                "sat": _stats(trace["sat"]),
                "align": _stats(trace["align"]),
                "valence": _stats(trace["valence"]),
                "term": _stats(trace["term"]),
                "djoy": _stats(trace["djoy"]),
                "pay_override": int(trace["pay_override"]),
            },
            "dream": {
                "offers": int(dream["offers"]),
                "formed": int(dream["formed"]),
                "dream_key_offers": int(dream["dream_key_offers"]),
                "source_offers": int(dream["source_offers"]),
                "rel_mean": (dream["rel_sum"] / dream["offers"]) if dream["offers"] else None,
                "rel_max": dream["rel_max"],
                "rel_min": dream["rel_min"],
                "crystals": len(cycle.crystal_store.crystals),
            },
            "long_anchor_norm": float(np.linalg.norm(long_anchor)),
        }
        # health values may include bools and ints; json can take them.
        payload["health"]["mean_strength"] = float(h["mean_strength"])
        payload["health"]["strong"] = int(h["strong"])
        payload["health"]["gain"] = float(h["gain"])
        payload["health"]["demotions"] = int(h["demotions"])
        return payload, rows


def _health_checks(h, strong_count, strong_ref) -> dict:
    return {
        "injection_rate >= 0.95": h["injection_rate"] >= 0.95,
        "no benign quarantines": h["quarantine_rate"] == 0.0,
        "all sources trust maxed": bool(h["all_sources_trust_max"]),
        "HHI < 0.30": h["hhi"] < 0.30,
        "bonds >= 1": h["bonds_formed"] >= 1,
        "active_values >= 30": h["active_values"] >= 30,
        "strong vs ref (-1)": strong_count >= strong_ref - 1,
        "lambda gate open": h["gain"] > 0.5,
        "consumer used": h["demotions"] >= 1,
        "no field collapse": h["mean_strength"] > 1.0,
    }


def composition_checks(h, strong_ref) -> dict:
    # Standing probe: health_summary strong_values vs _strong of the consumer-off build.
    return _health_checks(h, h["strong_values"], strong_ref)


def witness_pair_metrics(r_ref, r_wit) -> dict:
    a100 = 100
    d_ref = 1 - cos(r_ref[-1]["anchor"], r_ref[a100]["anchor"])
    d_wit = 1 - cos(r_wit[-1]["anchor"], r_wit[a100]["anchor"])

    def lock(rows):
        return float(np.median([
            1 - cos(rows[t]["field"], rows[t - 1]["field"])
            for t in range(len(rows) - 200, len(rows))
        ]))

    l_ref, l_wit = lock(r_ref), lock(r_wit)
    gap = np.array([b["coh"] - a["coh"] for a, b in zip(r_ref, r_wit)])
    worst10 = min(float(gap[i:i + 10].mean()) for i in range(len(gap) - 9))
    ident = (d_wit <= 2 * d_ref + 0.01 and l_wit <= 2 * l_ref + 1e-5
             and float(gap.mean()) >= -0.05 and worst10 >= -0.10)
    ev = [t for t, x in enumerate(r_wit)
          if x["behavior"] == "witness" and x["u"] is not None and 1 <= t < len(r_wit) - 1]

    def retention(rows):
        if not ev:
            return float("nan")
        return float(np.median([
            cos(rows[t + 1]["field"], r_wit[t]["u"]) - cos(rows[t - 1]["field"], r_wit[t]["u"])
            for t in ev
        ]))

    ret_ref, ret_wit = retention(r_ref), retention(r_wit)
    fired = sum(1 for x in r_wit if x["behavior"] == "witness")
    return {
        "anchor_ref": d_ref, "anchor_wit": d_wit,
        "lock_ref": l_ref, "lock_wit": l_wit,
        "coh_mean": float(gap.mean()), "worst10": worst10,
        "identity": bool(ident),
        "ret_ref": ret_ref, "ret_wit": ret_wit,
        "receptivity": bool(ret_wit > ret_ref),
        "fired": int(fired),
        "nonvacuous": bool(fired >= 50),
    }


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, float) and (obj != obj or obj in (float("inf"), float("-inf"))):
        return None
    return obj


def load_doc(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"steps": OFFICIAL_STEPS, "cells": {}}


def save_doc(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_jsonable(doc), indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _fmt(x, nd=3):
    if x is None:
        return "none"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def print_payload(label, payload):
    h = payload["health"]
    e = payload["ecology"]
    t = payload["trace"]
    d = payload["dream"]
    dec = payload["decisions"]
    print(
        f"  {label} inj={h['injection_rate']:.3f} q={h['quarantine_rate']:.3f} "
        f"HHI={h['hhi']:.3f} bonds={h['bonds_formed']} active>1={h['active_values']} "
        f"strong={h['strong']} λ={h['gain']:.2f} demot={h['demotions']}"
    )
    print(
        f"    ecology live={e['live']} ACTIVE={e['active_tier']} mean={e['mean_strength']:.3f} "
        f"core={e['core']} dreams={e['dream_boosts']} near_cap={e['near_cap']} "
        f"hhi={e['strength_hhi']:.3f} pol={e['polarity']}"
    )
    print(
        f"    allow={dec.get('allow', 0)} weak={dec.get('allow_weakened', 0)} "
        f"pay_as_allow={t['pay_override']} |cd|={_fmt((t['cd'] or {}).get('mean_abs'))} "
        f"sat={_fmt((t['sat'] or {}).get('mean'))} "
        f"val={_fmt((t['valence'] or {}).get('mean'))}±{_fmt((t['valence'] or {}).get('std'))} "
        f"term±={_fmt((t['term'] or {}).get('std'))} "
        f"djoy={_fmt((t['djoy'] or {}).get('mean_abs_delta'))}"
    )
    print(
        f"    dream offers={d['offers']} formed={d['formed']} dream_key={d['dream_key_offers']} "
        f"source={d['source_offers']} rel_max={_fmt(d['rel_max'], 4)} "
        f"crystals={d['crystals']} long_norm={payload['long_anchor_norm']:.3f}"
    )


def measure_composition(seed, arm, steps):
    ref_payload, _ = run_arm(seed, arm, steps, with_consumer=False, with_witness=False, workload="A")
    payload, _ = run_arm(seed, arm, steps, with_consumer=True, with_witness=False, workload="A")
    checks = composition_checks(payload["health"], ref_payload["health"]["strong"])
    payload["strong_ref"] = int(ref_payload["health"]["strong"])
    payload["checks"] = checks
    payload["composition_ok"] = all(checks.values())
    payload["strong_ref_ecology"] = ref_payload["ecology"]
    return payload


def measure_witness(seed, arm, steps):
    bare, rows_bare = run_arm(seed, arm, steps, with_consumer=True, with_witness=False, workload="B")
    wit, rows_wit = run_arm(seed, arm, steps, with_consumer=True, with_witness=True, workload="B")
    checks_bare = _health_checks(bare["health"], bare["health"]["strong"], bare["health"]["strong"])
    checks_wit = _health_checks(wit["health"], wit["health"]["strong"], bare["health"]["strong"])
    broke = [k for k in checks_wit if checks_bare[k] and not checks_wit[k]]
    pair = witness_pair_metrics(rows_bare, rows_wit) if steps >= OFFICIAL_STEPS else {
        "identity": False, "receptivity": False, "nonvacuous": False, "fired": 0,
        "short_run": True,
    }
    allow_bare = bare["decisions"].get("allow", 0)
    allow_wit = wit["decisions"].get("allow", 0)
    strength_bare = bare["ecology"]["total_strength"]
    strength_wit = wit["ecology"]["total_strength"]
    still = (
        (strength_bare > 0 and strength_wit < STARVE_STRENGTH * strength_bare)
        or (allow_bare > 0 and allow_wit < STARVE_ALLOW * allow_bare)
    )
    return {
        "bare": bare,
        "wit": wit,
        "checks_wit": checks_wit,
        "broke_vs_bare": broke,
        "composition_ok": bool(all(checks_wit.values()) and not broke),
        "pair": pair,
        "starve": {
            "strength_wit": strength_wit,
            "strength_bare": strength_bare,
            "strength_ratio": (strength_wit / strength_bare) if strength_bare else None,
            "allow_wit": allow_wit,
            "allow_bare": allow_bare,
            "allow_ratio": (allow_wit / allow_bare) if allow_bare else None,
            "still_starves": bool(still),
        },
    }


def _polarity_alarm(eco, ref) -> bool:
    n = eco["live"] or 1
    ref_n = ref["live"] or 1
    for name, count in eco["polarity"].items():
        share = count / n
        ref_share = ref["polarity"].get(name, 0) / ref_n
        if share >= MONO_SHARE and share >= ref_share + MONO_RISE:
            return True
    return False


def alarms_for(arm, eco, ref, trace, dream) -> list:
    """Relative alarms need ref. Absolute alarms note when REF itself trips them."""
    flags = lever_config(arm)
    out = []
    n = eco["live"] or 1
    cap_share = eco["near_cap"] / n
    sat = cap_share > SAT_CAP_SHARE or eco["mean_strength"] >= SAT_MEAN
    if sat:
        out.append("saturation")
    if ref is not None:
        ref_core = ref["core"]
        if eco["core"] > max(ref_core + CORE_PAD, 2 * ref_core):
            out.append("core_inflation")
        if arm in ("F", "ALL") and eco["core"] > ref_core + F_CORE_PAD:
            out.append("F_core_seed")
        if eco["strength_hhi"] >= MONO_HHI or _polarity_alarm(eco, ref):
            out.append("monoculture")
        if ref["live"] >= COLLAPSE_FLOOR and eco["live"] < max(COLLAPSE_FLOOR, COLLAPSE_FRAC * ref["live"]):
            out.append("collapse")
        if (eco["mean_strength"] >= ref["mean_strength"] + GROW_MEAN
                and eco["live"] >= ref["live"]
                and eco["reinforced_frac"] >= GROW_REINF
                and cap_share > GROW_CAP):
            out.append("indiscriminate")
    if flags["dream_consolidation"] and dream["dream_key_offers"] > 0:
        out.append("C_wrong_credit")
    if flags["coherence_impact_like_for_like"]:
        mean_abs = (trace.get("cd") or {}).get("mean_abs")
        if mean_abs is not None and mean_abs > D_ABS_CD:
            out.append("D_missed")
    if flags["satisfaction_from_emotion"]:
        val = trace.get("valence") or {}
        std = val.get("std")
        span = None if val.get("min") is None else val["max"] - val["min"]
        if std is not None and (std < G_STD or (span is not None and span < G_RANGE)):
            out.append("G_degenerate")
    return out


def f_core_sum_alarm(cells) -> bool:
    seeds = []
    for seed in SEEDS:
        ref = cells.get(f"REF|{seed}|composition")
        arm = cells.get(f"F|{seed}|composition")
        if not ref or not arm:
            return False
        seeds.append((arm["ecology"]["core"], ref["ecology"]["core"]))
    if len(seeds) < len(SEEDS):
        return False
    return sum(a for a, _ in seeds) > sum(r for _, r in seeds) + F_CORE_SUM_PAD


def report(doc) -> None:
    cells = doc.get("cells", {})
    print("\n" + "=" * 78)
    print("  VALUE FIXES — pre-declared bars, not a graduation")
    print("=" * 78)
    for arm in ARMS:
        comp_ok = []
        ident = recept = nonvac = wcomp = 0
        present = 0
        alarm_names = Counter()
        for seed in SEEDS:
            comp = cells.get(f"{arm}|{seed}|composition")
            wit = cells.get(f"{arm}|{seed}|witness")
            ref = cells.get(f"REF|{seed}|composition")
            if comp:
                present += 1
                comp_ok.append(bool(comp.get("composition_ok")))
                ref_eco = None if arm == "REF" or not ref else ref["ecology"]
                for name in alarms_for(arm, comp["ecology"], ref_eco, comp["trace"], comp["dream"]):
                    alarm_names[name] += 1
            if wit:
                pair = wit.get("pair") or {}
                ident += int(bool(pair.get("identity")))
                recept += int(bool(pair.get("receptivity")))
                nonvac += int(bool(pair.get("nonvacuous")))
                wcomp += int(bool(wit.get("composition_ok")))
                starve = wit.get("starve") or {}
                print(
                    f"  {arm} seed {seed} witness starve "
                    f"strength { _fmt(starve.get('strength_ratio')) } "
                    f"allow { _fmt(starve.get('allow_ratio')) } "
                    f"{'STILL' if starve.get('still_starves') else 'not starving'}"
                )
        if arm in ("F", "ALL") and f_core_sum_alarm(cells):
            alarm_names["F_core_sum"] += 1
        if present == 0:
            print(f"  {arm}: no cells")
            continue
        comp_clean = len(comp_ok) == len(SEEDS) and all(comp_ok)
        witness_holds = ident >= 2 and recept >= 2 and nonvac == len(SEEDS) and wcomp == len(SEEDS)
        # Absolute saturation on REF is not a lever fault. Drop it from the
        # candidate veto only when the REF arm tripped the same absolute alarm.
        veto = []
        for name, n in alarm_names.items():
            if name == "saturation":
                ref_sat = 0
                for seed in SEEDS:
                    ref = cells.get(f"REF|{seed}|composition")
                    if ref and "saturation" in alarms_for("REF", ref["ecology"], None, ref["trace"], ref["dream"]):
                        ref_sat += 1
                if ref_sat:
                    print(f"  {arm}: saturation also on REF ({ref_sat} seeds) — bar does not discriminate")
                    if n > ref_sat:
                        veto.append(name)
                    continue
            veto.append(name)
        candidate = comp_clean and witness_holds and not veto and present == len(SEEDS)
        print(
            f"  {arm}: composition {sum(comp_ok)}/{len(comp_ok)}  "
            f"identity {ident}/{len(SEEDS)} receptivity {recept}/{len(SEEDS)} "
            f"nonvacuous {nonvac}/{len(SEEDS)} witness-composition {wcomp}/{len(SEEDS)}  "
            f"alarms={dict(alarm_names) or '{}'}  "
            f"{'CANDIDATE' if candidate else 'HOLD'}"
        )


def main(argv=None) -> int:
    try:
        import torch
        torch.set_num_threads(4)
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Measure value-path levers C–G.")
    parser.add_argument("--arms", default=",".join(ARMS))
    parser.add_argument("--seeds", default=",".join(str(s) for s in SEEDS))
    parser.add_argument("--kinds", default=",".join(KINDS))
    parser.add_argument("--steps", type=int, default=OFFICIAL_STEPS)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    kinds = [k.strip() for k in args.kinds.split(",") if k.strip()]
    for arm in arms:
        if arm not in ARMS:
            print(f"unknown arm {arm}", file=sys.stderr)
            return 2
    official = args.steps == OFFICIAL_STEPS and tuple(seeds) == SEEDS
    out = Path(args.out) if official else None
    if not official:
        print("NOT A MEASUREMENT — steps or seeds differ from the declared gate; nothing is written.")
    doc = load_doc(out) if out else {"steps": args.steps, "cells": {}}
    if out and doc.get("steps") not in (None, OFFICIAL_STEPS):
        print(f"refusing to resume a doc stamped steps={doc.get('steps')}", file=sys.stderr)
        return 2
    doc["steps"] = OFFICIAL_STEPS if official else args.steps
    doc.setdefault("cells", {})

    planned = [(seed, arm, kind) for seed in seeds for arm in arms for kind in kinds]
    print(f"value fixes probe  steps={args.steps}  cells={len(planned)}  out={out}")
    for index, (seed, arm, kind) in enumerate(planned, start=1):
        key = f"{arm}|{seed}|{kind}"
        if not args.force and key in doc["cells"]:
            print(f"[{index}/{len(planned)}] {key}  (resume, kept)")
            continue
        print(f"[{index}/{len(planned)}] {key}  running", flush=True)
        try:
            if kind == "composition":
                cell = measure_composition(seed, arm, args.steps)
                print_payload(key, cell)
                print(f"    composition {'OK' if cell['composition_ok'] else 'FAIL'}  "
                      f"strong {cell['health']['strong']} vs ref {cell['strong_ref']}")
                if not cell["composition_ok"]:
                    failed = [k for k, v in cell["checks"].items() if not v]
                    print(f"    failing: {failed}")
            elif kind == "witness":
                if args.steps < OFFICIAL_STEPS:
                    print("    witness identity needs 500 steps; skipping")
                    continue
                cell = measure_witness(seed, arm, args.steps)
                print_payload(key + " bare", cell["bare"])
                print_payload(key + " wit", cell["wit"])
                pair = cell["pair"]
                print(
                    f"    identity {'OK' if pair['identity'] else 'FAIL'}  "
                    f"anchor {pair['anchor_wit']:.4f} vs {pair['anchor_ref']:.4f}  "
                    f"lock {pair['lock_wit']:.2e} vs {pair['lock_ref']:.2e}  "
                    f"coh {pair['coh_mean']:+.4f} worst10 {pair['worst10']:+.4f}"
                )
                print(
                    f"    receptivity {'OK' if pair['receptivity'] else 'FAIL'}  "
                    f"{pair['ret_wit']:+.5f} vs {pair['ret_ref']:+.5f}  "
                    f"fired {pair['fired']}  "
                    f"composition {'OK' if cell['composition_ok'] else 'FAIL'}"
                )
            else:
                print(f"unknown kind {kind}", file=sys.stderr)
                return 2
        except Exception:
            traceback.print_exc()
            return 1
        if out:
            doc["cells"][key] = cell
            save_doc(out, doc)
        else:
            doc["cells"][key] = cell
    if official:
        report(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
