"""
tests/diagnostic/integrity/value_reinforcement_trace.py

OPEN_METASTABILITY work item 0: a step-by-step reinforcement trace of why
every value weakens under witness. Replay-exact REF vs WIT pair, same setup as
witness_composition_gate.run (all-ON stack, workload B, attach_witness).

Instrumentation lives on the probe: wrap _birth_or_strengthen / evaluate_experience
/ _update_all_values / _evaluate_tensions / _dissolve_value / on_dream_cycle_complete
/ IntegrityDecayConsumer.apply / Witness.update on the instance. Runtime and gates
are not touched; lever defaults stay off.

Per step, per value, records:
  - reinforcement and each term (coherence_delta, emotional_satisfaction, bond_weight,
    decision_bonus) plus where emotional_satisfaction itself comes from
  - the decision, rhythm/mode, whether witness fired
  - strength changes that did not come through reinforcement (decay, productive
    tension, ⊘ consumer, dream boost, dissolution)
  - witness effective_lr = clip(coherence^2, 0.01, 1) (agents/witness.py update)

Then, per seed, REF vs WIT:
  1. For values that end weaker under WIT, decompose the total strength difference
     into those terms (must add up, or report the residual).
  2. Temporal shape: trickle vs few large hits vs concentrated after witness steps;
     recovery after witness stops (bin by steps-since-last-witness).
  3. Less reinforcement vs active demotion vs later recovery.
  4. Mean effective_lr REF vs WIT, and in windows right after witness steps.

Raw per-step / per-event rows go to a scratch directory (printed, not committed).
Summary to stdout.

Run:  python -m tests.diagnostic.integrity.value_reinforcement_trace [seeds...]
Default seeds: 0 1 2. Informational. exit 0. Not in run_all_tests.sh.
"""
from __future__ import annotations

import json
import logging
import math
import random
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

logging.disable(logging.CRITICAL)
sys.path.insert(0, ".")

from agents.value_emergence import BOND_WEIGHTS                                          # noqa: E402
from substrate import determinism                                                        # noqa: E402
from tests._common import (                                                              # noqa: E402
    RESONANCE_FAMILY_SOURCES,
    RESONANCE_FAMILY_WEIGHTS,
    health_summary,
)
from tests.diagnostic.integrity.all_levers_composition_probe import (                    # noqa: E402
    build_all_on,
    _strong,
)
from tests.diagnostic.integrity.witness_composition_gate import (                        # noqa: E402
    WITNESS_PHRASES,
    attach_witness,
    run as gate_run,
    unit,
)

N_STEPS = 500
EPS = 1e-12


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _bond_weight(report):
    bw = BOND_WEIGHTS.get(report.bond_type, 1.0)
    if report.bond_type is not None:
        bw *= 0.5 + 0.5 * report.bond_confidence
    return float(bw)


def _decision_bonus(ve, decision):
    return {
        "allow":          ve.config["decision_bonus_allow"],
        "allow_weakened": ve.config["decision_bonus_weakened"],
        "monitor":        ve.config["decision_bonus_monitor"],
    }.get(decision, 0.0)


def _emergence_score(ve, report, bw, db):
    return (
        report.coherence_delta        * 0.40 +
        report.emotional_satisfaction * 0.35 +
        report.surprise               * 0.15 +
        max(0.0, report.trust_impact) * 0.10
    ) * bw + db


def _core_of(ve, value_id):
    v = ve.values.get(value_id) or ve.archived_values.get(value_id)
    return v.symbolic_core if v is not None else None


def _live_by_core(ve):
    out = {}
    for v in ve.values.values():
        if v.dissolved_at_step < 0:
            out[v.symbolic_core] = v
    return out


class Tracer:
    """Instance-level wraps. Records only; orig is always called with the same args."""

    def __init__(self, arm: str):
        self.arm = arm
        self.events = []
        self.steps = []
        self.cycle_step = -1
        self.mode = None
        self.read_rhythm = None
        self.effective_lr = None
        self.watcher_coherence = None
        self.last_witness_step = None
        self.last_decision = None
        self.last_dec_strength = None
        self.last_report = None
        self.last_candidates = []
        self.in_update_all = False
        self.in_cap = False
        self.ve = None
        self.cycle = None
        self.joy_at_feedback = None

    def since_witness(self):
        if self.last_witness_step is None:
            return None
        return self.cycle_step - self.last_witness_step

    def emit(self, **kw):
        row = {
            "arm": self.arm,
            "cycle_step": self.cycle_step,
            "ve_step": None if self.ve is None else self.ve._step,
            "mode": self.mode,
            "read_rhythm": self.read_rhythm,
            "decision": self.last_decision,
            "effective_lr": self.effective_lr,
            "watcher_coherence": self.watcher_coherence,
            "since_witness": self.since_witness(),
            "witness_fired": self.mode == "witness",
        }
        row.update(kw)
        self.events.append(row)

    def install(self, ve, cycle, gov, consumer):
        self.ve = ve
        self.cycle = cycle
        tr = self

        orig_select = cycle._select_mode

        def wrapped_select(tokens):
            mode, read = orig_select(tokens)
            tr.mode = mode
            tr.read_rhythm = None if read is None else read.rhythm
            # Set this before governance feedback (step 10) so per-value events
            # on a witness-fire step have since_witness == 0.
            if mode == "witness":
                tr.last_witness_step = tr.cycle_step
            return mode, read

        cycle._select_mode = wrapped_select

        orig_wit = cycle.witness.update

        def wrapped_wit(*args, **kwargs):
            if args and len(args) >= 2:
                coherence = args[1]
            else:
                coherence = kwargs.get("coherence", 0.0)
            c = _f(coherence)
            tr.watcher_coherence = c
            tr.effective_lr = float(np.clip(c * c, 0.01, 1.0))
            return orig_wit(*args, **kwargs)

        cycle.witness.update = wrapped_wit

        orig_arb = gov.arbitrate

        def wrapped_arb(*args, **kwargs):
            dec, strength = orig_arb(*args, **kwargs)
            tr.last_decision = dec.value
            tr.last_dec_strength = _f(strength)
            return dec, strength

        gov.arbitrate = wrapped_arb

        orig_eval = ve.evaluate_experience

        def wrapped_eval(report):
            tr.last_report = report
            emo = getattr(cycle, "emotion", None)
            tr.joy_at_feedback = None if emo is None else _f(getattr(emo, "joy", None))
            orig_eval(report)

        ve.evaluate_experience = wrapped_eval

        orig_detect = ve._detect_candidates

        def wrapped_detect(report):
            cands = orig_detect(report)
            tr.last_candidates = list(cands)
            return cands

        ve._detect_candidates = wrapped_detect

        orig_birth = ve._birth_or_strengthen

        def wrapped_birth(stable_id, report):
            is_new = stable_id not in ve.symbol_to_value
            s_before = None
            if not is_new:
                vid = ve.symbol_to_value[stable_id]
                s_before = _f(ve.values[vid].strength)
            orig_birth(stable_id, report)
            if stable_id not in ve.symbol_to_value:
                return
            vid = ve.symbol_to_value[stable_id]
            value = ve.values[vid]
            core = value.symbolic_core
            if is_new:
                tr.emit(
                    source="birth",
                    value_id=vid,
                    symbolic_core=core,
                    stable_id=int(stable_id),
                    applied=0.50,
                    live_applied=0.50,
                    strength_after=_f(value.strength),
                )
                s_before = 0.50
            lr = _f(ve.config["reinforcement_lr"])
            bw = _bond_weight(report)
            db = _decision_bonus(ve, report.decision)
            cd = _f(report.coherence_delta)
            es = _f(report.emotional_satisfaction)
            requested = ((cd * 0.6 + es * 0.4) * bw + db) * lr
            applied = _f(value.strength) - _f(s_before)
            if abs(requested) > EPS:
                scale = applied / requested
            else:
                scale = 0.0
            term_cd = (cd * 0.6 * lr) * scale
            term_es = (es * 0.4 * lr) * scale
            term_bw = ((cd * 0.6 + es * 0.4) * (bw - 1.0) * lr) * scale
            term_db = (db * lr) * scale
            tr.emit(
                source="reinforcement",
                value_id=vid,
                symbolic_core=core,
                stable_id=int(stable_id),
                applied=applied,
                live_applied=applied,
                requested=requested,
                clip_loss=requested - applied,
                coherence_delta=cd,
                emotional_satisfaction=es,
                es_formula="max(0, coherence_delta)",
                es_from_cd_relu=max(0.0, cd),
                joy_at_feedback=tr.joy_at_feedback,
                bond_type=report.bond_type,
                bond_confidence=_f(report.bond_confidence),
                bond_weight=bw,
                decision_bonus=db,
                reinforcement_lr=lr,
                term_coherence_delta=term_cd,
                term_emotional_satisfaction=term_es,
                term_bond_weight=term_bw,
                term_decision_bonus=term_db,
                source_id=report.source_id,
                surprise=_f(report.surprise),
                trust_impact=_f(report.trust_impact),
                n_stable_ids=len(report.stable_ids),
                strength_before=_f(s_before),
                strength_after=_f(value.strength),
            )

        ve._birth_or_strengthen = wrapped_birth

        orig_tension = ve._evaluate_tensions

        def wrapped_tension(value):
            before = {vid: _f(v.strength) for vid, v in ve.values.items()}
            orig_tension(value)
            for vid, v in ve.values.items():
                d = _f(v.strength) - before.get(vid, _f(v.strength))
                if abs(d) > EPS:
                    tr.emit(
                        source="tension",
                        value_id=vid,
                        symbolic_core=v.symbolic_core,
                        applied=d,
                        live_applied=d,
                        trigger_value_id=value.value_id,
                        trigger_core=value.symbolic_core,
                        strength_after=_f(v.strength),
                    )

        ve._evaluate_tensions = wrapped_tension

        orig_dissolve = ve._dissolve_value

        def wrapped_dissolve(value_id):
            value = ve.values.get(value_id)
            if value is None:
                return orig_dissolve(value_id)
            core = value.symbolic_core
            s = _f(value.strength)
            reason = "cap" if tr.in_cap else ("update_all" if tr.in_update_all else "other")
            orig_dissolve(value_id)
            tr.emit(
                source="dissolve",
                value_id=value_id,
                symbolic_core=core,
                applied=0.0,
                live_applied=-s,
                dissolve_reason=reason,
                strength_at_dissolve=s,
            )

        ve._dissolve_value = wrapped_dissolve

        orig_update = ve._update_all_values

        def wrapped_update():
            before = {vid: _f(v.strength) for vid, v in ve.values.items()}
            cores = {vid: v.symbolic_core for vid, v in ve.values.items()}
            mark = len(tr.events)
            tr.in_update_all = True
            orig_update()
            tr.in_update_all = False
            tension = defaultdict(float)
            dissolved = {}
            for e in tr.events[mark:]:
                if e.get("source") == "tension":
                    tension[e["value_id"]] += _f(e.get("applied"))
                elif e.get("source") == "dissolve":
                    dissolved[e["value_id"]] = e
            for vid, s0 in before.items():
                t = tension.get(vid, 0.0)
                if vid in dissolved:
                    s1 = _f(dissolved[vid].get("strength_at_dissolve"))
                elif vid in ve.values:
                    s1 = _f(ve.values[vid].strength)
                else:
                    continue
                decay = s1 - s0 - t
                if abs(decay) > EPS:
                    tr.emit(
                        source="decay",
                        value_id=vid,
                        symbolic_core=cores[vid],
                        applied=decay,
                        live_applied=decay,
                        strength_before=s0,
                        strength_after=s1,
                    )

        ve._update_all_values = wrapped_update

        orig_cap = ve._enforce_value_cap

        def wrapped_cap():
            tr.in_cap = True
            orig_cap()
            tr.in_cap = False

        ve._enforce_value_cap = wrapped_cap

        orig_dream = ve.on_dream_cycle_complete

        def wrapped_dream(crystallized_stable_ids, quality=0.5):
            before = {vid: _f(v.strength) for vid, v in ve.values.items()}
            orig_dream(crystallized_stable_ids, quality=quality)
            for vid, v in ve.values.items():
                d = _f(v.strength) - before.get(vid, _f(v.strength))
                if abs(d) > EPS:
                    tr.emit(
                        source="dream",
                        value_id=vid,
                        symbolic_core=v.symbolic_core,
                        applied=d,
                        live_applied=d,
                        quality=_f(quality),
                        strength_after=_f(v.strength),
                    )

        ve.on_dream_cycle_complete = wrapped_dream

        if consumer is not None:
            orig_apply = consumer.apply

            def wrapped_apply(*args, **kwargs):
                before = {vid: _f(v.strength) for vid, v in ve.values.items()}
                touched = orig_apply(*args, **kwargs)
                for vid, v in ve.values.items():
                    d = _f(v.strength) - before.get(vid, _f(v.strength))
                    if abs(d) > EPS:
                        tr.emit(
                            source="integrity",
                            value_id=vid,
                            symbolic_core=v.symbolic_core,
                            applied=d,
                            live_applied=d,
                            strength_before=before[vid],
                            strength_after=_f(v.strength),
                        )
                return touched

            consumer.apply = wrapped_apply
            ve.set_integrity_consumer(wrapped_apply)

        orig_step = cycle.step

        def wrapped_step(tokens, source_id="user", origin_type="user"):
            tr.cycle_step = cycle._step
            tr.mode = None
            tr.read_rhythm = None
            tr.effective_lr = None
            tr.watcher_coherence = None
            tr.last_decision = None
            tr.last_report = None
            tr.last_candidates = []
            tr.joy_at_feedback = None
            mark = len(tr.events)
            state = orig_step(tokens, source_id, origin_type)
            behavior = state.extras.get("behavior", state.rhythm)
            if behavior == "witness":
                tr.last_witness_step = tr.cycle_step
            report = tr.last_report
            bw = db = score = None
            cd = es = surprise = trust = None
            es_relu = None
            if report is not None:
                bw = _bond_weight(report)
                db = _decision_bonus(ve, report.decision)
                score = _emergence_score(ve, report, bw, db)
                cd = _f(report.coherence_delta)
                es = _f(report.emotional_satisfaction)
                es_relu = max(0.0, cd)
                surprise = _f(report.surprise)
                trust = _f(report.trust_impact)
            live = _live_by_core(ve)
            step_events = tr.events[mark:]
            src_sum = Counter()
            for e in step_events:
                src_sum[e.get("source")] += 1
            tr.steps.append({
                "arm": tr.arm,
                "cycle_step": tr.cycle_step,
                "tokens": list(tokens),
                "source_id": source_id,
                "rhythm": state.rhythm,
                "behavior": behavior,
                "mode": tr.mode,
                "read_rhythm": tr.read_rhythm,
                "witness_fired": behavior == "witness",
                "decision": tr.last_decision,
                "dec_strength": tr.last_dec_strength,
                "effective_lr": tr.effective_lr,
                "watcher_coherence": tr.watcher_coherence,
                "joy_at_feedback": tr.joy_at_feedback,
                "coherence_delta": cd,
                "emotional_satisfaction": es,
                "es_formula": "max(0, coherence_delta)",
                "es_from_cd_relu": es_relu,
                "es_equals_relu": None if es is None else abs(es - es_relu) < 1e-12,
                "surprise": surprise,
                "trust_impact": trust,
                "bond_type": None if report is None else report.bond_type,
                "bond_weight": bw,
                "decision_bonus": db,
                "emergence_score": score,
                "emergence_threshold": _f(ve.config["min_emergence_threshold"]),
                "emergence_passed": bool(tr.last_candidates),
                "n_candidates": len(tr.last_candidates),
                "n_stable_ids": 0 if report is None else len(report.stable_ids),
                "since_witness": tr.since_witness(),
                "n_live": len(live),
                "sum_live": sum(_f(v.strength) for v in live.values()),
                "mean_live": (sum(_f(v.strength) for v in live.values()) / len(live)
                              if live else 0.0),
                "n_active": sum(1 for v in live.values() if v.strength > 1.0),
                "n_strong": sum(1 for v in live.values() if v.strength >= 3.5),
                "event_counts": dict(src_sum),
                "live": {c: _f(v.strength) for c, v in live.items()},
            })
            return state

        cycle.step = wrapped_step


def traced_run(seed, with_witness):
    """Same setup as witness_composition_gate.run(seed, 'B', with_witness), plus wraps."""
    tracer = Tracer("WIT" if with_witness else "REF")
    with determinism.deterministic(seed):
        gen, cycle, gov, ve, ledger, consumer, report, pretrained = build_all_on()
        if with_witness:
            attach_witness(gen, cycle)
        tracer.install(ve, cycle, gov, consumer)
        pick = random.Random(seed)
        sids = list(RESONANCE_FAMILY_SOURCES)
        w = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        decisions = Counter()
        # Same counted-arbitrate wrap as the gate; layered on the tracer wrap.
        inner_arb = gov.arbitrate

        def counted(*a, **k):
            dec, strength = inner_arb(*a, **k)
            decisions[dec.value] += 1
            return dec, strength

        gov.arbitrate = counted
        # Byte-identical to witness_composition_gate.run(..., workload="B"):
        # peek_batch is observe-only, but the extra watcher.evaluate AFTER the
        # step writes Watcher temporal history (_update_history) and is
        # load-bearing for the gate's REF numbers.
        for _ in range(N_STEPS):
            src = pick.choices(sids, weights=w)[0]
            if pick.random() < 0.20:
                toks, kind = WITNESS_PHRASES[pick.randrange(len(WITNESS_PHRASES))], "witness"
            else:
                toks, kind = pick.choice(RESONANCE_FAMILY_SOURCES[src]), "canonical"
            vecs, known = gen.peek_batch([toks])
            s = cycle.step(toks, source_id=src, origin_type="internal")
            f = cycle.field.field
            coh = (cycle.watcher.evaluate(unit(f), cycle.witness.current_anchor(), cycle.field.resonate()).composite
                   if np.linalg.norm(f) > 1e-8 else 0.0)
            # Same extra copies the gate takes for its rows (read-only; call order kept).
            _ = (kind, s.extras.get("behavior", s.rhythm), f.copy(), coh,
                 np.array(cycle.witness.current_anchor(), dtype=float),
                 vecs[0] if known[0] else None)
        gov.arbitrate = inner_arb
        h = health_summary(cycle, gov, ve, decisions)
        vals = [v.strength for v in ve.values.values() if v.dissolved_at_step < 0]
        h["mean_strength"] = sum(vals) / len(vals) if vals else 0.0
        h["strong"] = _strong(ve)
        h["gain"] = ledger.gain()
        h["demotions"] = consumer.snapshot()["demotions_total"] if consumer else 0
        h["values"] = [(v.symbolic_core, v.strength, v.dissolved_at_step,
                        v.coherence_contribution, v.polarity.name)
                       for v in ve.values.values()]
        h["archived"] = [(v.symbolic_core, v.strength, v.dissolved_at_step,
                          v.coherence_contribution, v.polarity.name)
                         for v in ve.archived_values.values()]
        h["live_ids"] = {v.symbolic_core: v.value_id
                         for v in ve.values.values() if v.dissolved_at_step < 0}
        h["object_strength"] = {
            v.value_id: (v.symbolic_core, _f(v.strength), v.dissolved_at_step < 0)
            for v in list(ve.values.values()) + list(ve.archived_values.values())
        }
        h["pretrained"] = pretrained
        h["n_live"] = len(vals)
        h["sum_live"] = float(sum(vals)) if vals else 0.0
        h["decisions"] = dict(decisions)
        return h, tracer


def _health_fingerprint(h):
    return {
        "injection_rate": round(h["injection_rate"], 10),
        "quarantine_rate": round(h["quarantine_rate"], 10),
        "hhi": round(h["hhi"], 10),
        "bonds_formed": h["bonds_formed"],
        "active_values": h["active_values"],
        "strong": h["strong"],
        "mean_strength": round(h["mean_strength"], 10),
        "demotions": h["demotions"],
        "values": sorted((c, round(s, 10), d, round(cc, 10), p)
                         for c, s, d, cc, p in h["values"]),
    }


TERM_KEYS = (
    "birth",
    "coherence_delta",
    "emotional_satisfaction",
    "bond_weight",
    "decision_bonus",
    "decay",
    "tension",
    "integrity",
    "dream",
    "dissolve_remove",
)


def _event_terms(e):
    """Map one event onto the additive live-ecology budget."""
    src = e.get("source")
    out = {k: 0.0 for k in TERM_KEYS}
    if src == "birth":
        out["birth"] = _f(e.get("live_applied"))
    elif src == "reinforcement":
        out["coherence_delta"] = _f(e.get("term_coherence_delta"))
        out["emotional_satisfaction"] = _f(e.get("term_emotional_satisfaction"))
        out["bond_weight"] = _f(e.get("term_bond_weight"))
        out["decision_bonus"] = _f(e.get("term_decision_bonus"))
    elif src == "decay":
        out["decay"] = _f(e.get("live_applied"))
    elif src == "tension":
        out["tension"] = _f(e.get("live_applied"))
    elif src == "integrity":
        out["integrity"] = _f(e.get("live_applied"))
    elif src == "dream":
        out["dream"] = _f(e.get("live_applied"))
    elif src == "dissolve":
        out["dissolve_remove"] = _f(e.get("live_applied"))
    return out


def _sum_terms(events):
    acc = {k: 0.0 for k in TERM_KEYS}
    for e in events:
        t = _event_terms(e)
        for k in TERM_KEYS:
            acc[k] += t[k]
    acc["total"] = sum(acc[k] for k in TERM_KEYS)
    return acc


def _by_core(events):
    groups = defaultdict(list)
    for e in events:
        c = e.get("symbolic_core")
        if c is not None:
            groups[c].append(e)
    return groups


def _by_vid(events):
    groups = defaultdict(list)
    for e in events:
        vid = e.get("value_id")
        if vid is not None:
            groups[vid].append(e)
    return groups


def _end_live(h):
    return {c: s for c, s, d, cc, p in h["values"] if d < 0}


def _polarity_counts(h):
    return Counter(p for c, s, d, cc, p in h["values"] if d < 0)


def _reconstruct_object(events_for_core):
    """Object strength (dissolve does not change the stored float)."""
    s = 0.0
    for e in events_for_core:
        if e.get("source") == "dissolve":
            continue
        s += _f(e.get("applied"))
    return s


def _max_residual(h, events):
    """Per-value-id object-strength reconstruction (one generation, not a core's churn)."""
    objects = h.get("object_strength") or {}
    groups = _by_vid(events)
    worst = 0.0
    worst_id = None
    n_checked = 0
    for vid, evs in groups.items():
        rec = _reconstruct_object(evs)
        meta = objects.get(vid)
        if meta is None:
            continue
        actual = _f(meta[1])
        r = abs(rec - actual)
        n_checked += 1
        if r > worst:
            worst, worst_id = r, (vid, meta[0])
    return worst, worst_id, n_checked


def _bin_since(n):
    if n is None:
        return "never"
    if n == 0:
        return "0 (fire)"
    if n <= 2:
        return "1-2"
    if n <= 5:
        return "3-5"
    if n <= 10:
        return "6-10"
    if n <= 20:
        return "11-20"
    return "21+"


BIN_ORDER = ["0 (fire)", "1-2", "3-5", "6-10", "11-20", "21+", "never"]


def _mean(xs):
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return float(sum(xs) / len(xs)) if xs else float("nan")


def _fmt(x, digits=4):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "  n/a "
    return f"{x:+.{digits}f}"


def _fmt_u(x, digits=4):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "  n/a "
    return f"{x:.{digits}f}"


def summarize_seed(seed, h_ref, tr_ref, h_wit, tr_wit):
    live_r, live_w = _end_live(h_ref), _end_live(h_wit)
    cores = sorted(set(live_r) | set(live_w))
    ids_r = h_ref.get("live_ids") or {}
    ids_w = h_wit.get("live_ids") or {}
    ev_r = _by_vid(tr_ref.events)
    ev_w = _by_vid(tr_wit.events)

    weaker, stronger, equal, ref_only, wit_only = [], [], [], [], []
    decomps = []
    for c in cores:
        s_r, s_w = live_r.get(c, 0.0), live_w.get(c, 0.0)
        delta = s_w - s_r
        # Current generation only: the live value_id, or empty if the core is not live.
        t_r = _sum_terms(ev_r.get(ids_r[c], []) if c in ids_r else [])
        t_w = _sum_terms(ev_w.get(ids_w[c], []) if c in ids_w else [])
        dterms = {k: t_w[k] - t_r[k] for k in TERM_KEYS}
        dterms["total"] = t_w["total"] - t_r["total"]
        unexplained = delta - dterms["total"]
        rec = {
            "core": c,
            "ref": s_r,
            "wit": s_w,
            "delta": delta,
            "in_ref": c in live_r,
            "in_wit": c in live_w,
            "terms": dterms,
            "unexplained": unexplained,
            "ref_terms": t_r,
            "wit_terms": t_w,
        }
        decomps.append(rec)
        if c in live_r and c not in live_w:
            ref_only.append(rec)
            weaker.append(rec)
        elif c in live_w and c not in live_r:
            wit_only.append(rec)
            if delta < -1e-9:
                weaker.append(rec)
            elif delta > 1e-9:
                stronger.append(rec)
            else:
                equal.append(rec)
        elif delta < -1e-9:
            weaker.append(rec)
        elif delta > 1e-9:
            stronger.append(rec)
        else:
            equal.append(rec)

    def _stack(rows):
        acc = {k: 0.0 for k in TERM_KEYS}
        acc["delta"] = 0.0
        acc["unexplained"] = 0.0
        for r in rows:
            acc["delta"] += r["delta"]
            acc["unexplained"] += r["unexplained"]
            for k in TERM_KEYS:
                acc[k] += r["terms"][k]
        return acc

    weak_stack = _stack(weaker)
    all_stack = _stack(decomps)

    # Less reinforcement vs negative reinforcement vs demotion
    def _reinf_sign(events, sign):
        tot = 0.0
        n = 0
        for e in events:
            if e.get("source") != "reinforcement":
                continue
            a = _f(e.get("applied"))
            if sign == "+" and a > EPS:
                tot += a
                n += 1
            elif sign == "-" and a < -EPS:
                tot += a
                n += 1
        return tot, n

    pos_r, npos_r = _reinf_sign(tr_ref.events, "+")
    pos_w, npos_w = _reinf_sign(tr_wit.events, "+")
    neg_r, nneg_r = _reinf_sign(tr_ref.events, "-")
    neg_w, nneg_w = _reinf_sign(tr_wit.events, "-")

    def _src_sum(events, src):
        return sum(_f(e.get("live_applied")) for e in events if e.get("source") == src)

    # Emergence-gate misses: steps where the report had symbols but score failed
    def _emerge_stats(steps, witness_only=None):
        rows = steps
        if witness_only is True:
            rows = [s for s in steps if s["witness_fired"]]
        elif witness_only is False:
            rows = [s for s in steps if not s["witness_fired"]]
        n = len(rows)
        failed = [s for s in rows if not s["emergence_passed"]]
        scores = [_f(s["emergence_score"]) for s in rows if s["emergence_score"] is not None]
        cds = [_f(s["coherence_delta"]) for s in rows if s["coherence_delta"] is not None]
        return {
            "n": n,
            "failed": len(failed),
            "fail_rate": len(failed) / n if n else float("nan"),
            "mean_score": _mean(scores),
            "mean_cd": _mean(cds),
        }

    # Temporal: per-step d(sum_live), gap vs REF
    sum_r = [s["sum_live"] for s in tr_ref.steps]
    sum_w = [s["sum_live"] for s in tr_wit.steps]
    n = min(len(sum_r), len(sum_w))
    gap = [sum_w[t] - sum_r[t] for t in range(n)]
    d_gap = [gap[t] - gap[t - 1] for t in range(1, n)]
    d_w = [sum_w[t] - sum_w[t - 1] for t in range(1, n)]
    d_r = [sum_r[t] - sum_r[t - 1] for t in range(1, n)]

    wit_idx = [s["cycle_step"] for s in tr_wit.steps if s["witness_fired"]]
    d_at_wit, d_not_wit = [], []
    for t in range(1, n):
        if tr_wit.steps[t]["witness_fired"]:
            d_at_wit.append(d_gap[t - 1])
        else:
            d_not_wit.append(d_gap[t - 1])

    abs_dg = [abs(x) for x in d_gap]
    abs_dg_sorted = sorted(abs_dg)
    p90 = abs_dg_sorted[int(0.9 * (len(abs_dg_sorted) - 1))] if abs_dg_sorted else float("nan")
    large = sum(1 for x in abs_dg if abs(x) >= 0.10)
    # trickle: most of the end-gap is the sum of many small same-sign steps
    end_gap = gap[-1] if gap else 0.0
    trickle_share = (sum(x for x in d_gap if (x < 0) == (end_gap < 0) and abs(x) < 0.05)
                     / end_gap) if abs(end_gap) > EPS else float("nan")

    bins = {b: {"d_gap": [], "d_wit": [], "elr": [], "cd": []} for b in BIN_ORDER}
    for t in range(n):
        b = _bin_since(tr_wit.steps[t]["since_witness"])
        if t > 0:
            bins[b]["d_gap"].append(d_gap[t - 1])
            bins[b]["d_wit"].append(d_w[t - 1])
        elr = tr_wit.steps[t]["effective_lr"]
        if elr is not None:
            bins[b]["elr"].append(_f(elr))
        cd = tr_wit.steps[t]["coherence_delta"]
        if cd is not None:
            bins[b]["cd"].append(_f(cd))

    def _elr_stats(steps, pred=None):
        xs = [_f(s["effective_lr"]) for s in steps
              if s["effective_lr"] is not None and (pred is None or pred(s))]
        return _mean(xs), len(xs)

    elr_ref, n_elr_ref = _elr_stats(tr_ref.steps)
    elr_wit, n_elr_wit = _elr_stats(tr_wit.steps)
    elr_fire, n_elr_fire = _elr_stats(tr_wit.steps, lambda s: s["witness_fired"])
    elr_1, n_elr_1 = _elr_stats(tr_wit.steps, lambda s: s["since_witness"] == 1)
    elr_2, n_elr_2 = _elr_stats(tr_wit.steps, lambda s: s["since_witness"] == 2)
    elr_3, n_elr_3 = _elr_stats(tr_wit.steps, lambda s: s["since_witness"] == 3)
    elr_late, n_elr_late = _elr_stats(
        tr_wit.steps,
        lambda s: s["since_witness"] is not None and s["since_witness"] >= 10,
    )

    # Recovery: after a witness fire, does sum_live climb back toward REF
    # over the following stretch with no further witness?
    recoveries = []
    fire_steps = [s["cycle_step"] for s in tr_wit.steps if s["witness_fired"]]
    for i, t0 in enumerate(fire_steps):
        t1 = fire_steps[i + 1] if i + 1 < len(fire_steps) else n
        if t1 - t0 < 3:
            continue
        g0 = gap[t0]
        g1 = gap[t1 - 1]
        recoveries.append(g1 - g0)  # >0 means the gap shrank (WIT caught up if gap is negative)

    pol_r, pol_w = _polarity_counts(h_ref), _polarity_counts(h_wit)
    res_r = _max_residual(h_ref, tr_ref.events)
    res_w = _max_residual(h_wit, tr_wit.events)

    dec_r = Counter(h_ref.get("decisions") or {})
    dec_w = Counter(h_wit.get("decisions") or {})

    # emotional_satisfaction vs joy vs relu(cd)
    def _es_audit(steps):
        n = 0
        n_eq = 0
        joy, es, relu, cd, coh = [], [], [], [], []
        for s in steps:
            if s["emotional_satisfaction"] is None:
                continue
            n += 1
            if s.get("es_equals_relu"):
                n_eq += 1
            if s["joy_at_feedback"] is not None:
                joy.append(_f(s["joy_at_feedback"]))
            es.append(_f(s["emotional_satisfaction"]))
            relu.append(_f(s["es_from_cd_relu"]))
            if s["coherence_delta"] is not None:
                cd.append(_f(s["coherence_delta"]))
            if s["watcher_coherence"] is not None:
                coh.append(_f(s["watcher_coherence"]))
        return {
            "n": n,
            "eq_relu": n_eq,
            "mean_es": _mean(es),
            "mean_relu": _mean(relu),
            "mean_joy": _mean(joy),
            "mean_cd": _mean(cd),
            "mean_coh": _mean(coh),
        }

    es_r, es_w = _es_audit(tr_ref.steps), _es_audit(tr_wit.steps)

    fired = sum(1 for s in tr_wit.steps if s["witness_fired"])

    print(f"\n=== seed {seed}  workload B  (REF vs WIT, {N_STEPS} steps)")
    print(f"  witness fired {fired}")
    print(f"  REF  inj {h_ref['injection_rate']:.3f}  active {h_ref['active_values']}  "
          f"strong {h_ref['strong']}  mean_str {h_ref['mean_strength']:.3f}  "
          f"n_live {h_ref['n_live']}  sum_live {h_ref['sum_live']:.3f}  "
          f"demot {h_ref['demotions']}  λ {h_ref['gain']:.2f}")
    print(f"  WIT  inj {h_wit['injection_rate']:.3f}  active {h_wit['active_values']}  "
          f"strong {h_wit['strong']}  mean_str {h_wit['mean_strength']:.3f}  "
          f"n_live {h_wit['n_live']}  sum_live {h_wit['sum_live']:.3f}  "
          f"demot {h_wit['demotions']}  λ {h_wit['gain']:.2f}")
    print(f"  polarity REF {dict(pol_r)}  WIT {dict(pol_w)}")
    print(f"  decisions REF {dict(dec_r)}  WIT {dict(dec_w)}")
    print(f"  accounting residual (max |reconstructed-actual| object strength): "
          f"REF {res_r[0]:.2e} n={res_r[2]}  WIT {res_w[0]:.2e} n={res_w[2]}")

    print(f"\n  values: shared {len(cores) - len(ref_only) - len(wit_only)}  "
          f"weaker-under-WIT {len(weaker)}  stronger {len(stronger)}  equal {len(equal)}  "
          f"REF-only {len(ref_only)}  WIT-only {len(wit_only)}")

    def _print_stack(title, st, n_vals):
        print(f"\n  {title}  (n={n_vals})  observed Δsum_live {st['delta']:+.4f}")
        explained = sum(st[k] for k in TERM_KEYS)
        print(f"    {'term':<24s} {'WIT-REF':>10s}")
        for k in TERM_KEYS:
            print(f"    {k:<24s} {_fmt(st[k], 4):>10s}")
        print(f"    {'sum of terms':<24s} {_fmt(explained, 4):>10s}")
        print(f"    {'unexplained':<24s} {_fmt(st['unexplained'], 4):>10s}")

    _print_stack("decomposition: values weaker under WIT", weak_stack, len(weaker))
    _print_stack("decomposition: all live cores (union)", all_stack, len(decomps))

    weaker_sorted = sorted(weaker, key=lambda r: r["delta"])
    print("\n  weaker values (most negative Δ first, up to 12):")
    print(f"    {'core':<16s} {'REF':>7s} {'WIT':>7s} {'Δ':>8s} "
          f"{'Δcd':>8s} {'Δes':>8s} {'Δbw':>8s} {'Δdb':>8s} "
          f"{'Δdec':>8s} {'Δ⊘':>8s} {'Δdis':>8s} {'unexp':>8s}")
    for r in weaker_sorted[:12]:
        t = r["terms"]
        print(f"    {r['core']:<16s} {r['ref']:7.3f} {r['wit']:7.3f} {r['delta']:+8.3f} "
              f"{t['coherence_delta']:+8.3f} {t['emotional_satisfaction']:+8.3f} "
              f"{t['bond_weight']:+8.3f} {t['decision_bonus']:+8.3f} "
              f"{t['decay']:+8.3f} {t['integrity']:+8.3f} {t['dissolve_remove']:+8.3f} "
              f"{r['unexplained']:+8.3f}")

    print("\n  reinforcement sign (applied strength, all values):")
    print(f"    positive  REF {pos_r:+.4f} (n={npos_r})  WIT {pos_w:+.4f} (n={npos_w})  "
          f"Δ {pos_w - pos_r:+.4f}")
    print(f"    negative  REF {neg_r:+.4f} (n={nneg_r})  WIT {neg_w:+.4f} (n={nneg_w})  "
          f"Δ {neg_w - neg_r:+.4f}")
    print(f"    decay     REF {_src_sum(tr_ref.events, 'decay'):+.4f}  "
          f"WIT {_src_sum(tr_wit.events, 'decay'):+.4f}")
    print(f"    integrity REF {_src_sum(tr_ref.events, 'integrity'):+.4f}  "
          f"WIT {_src_sum(tr_wit.events, 'integrity'):+.4f}")
    print(f"    tension   REF {_src_sum(tr_ref.events, 'tension'):+.4f}  "
          f"WIT {_src_sum(tr_wit.events, 'tension'):+.4f}")
    print(f"    dream     REF {_src_sum(tr_ref.events, 'dream'):+.4f}  "
          f"WIT {_src_sum(tr_wit.events, 'dream'):+.4f}")
    print(f"    dissolve  REF {_src_sum(tr_ref.events, 'dissolve'):+.4f}  "
          f"WIT {_src_sum(tr_wit.events, 'dissolve'):+.4f}")

    print("\n  emergence gate:")
    for label, stats in (
        ("REF all", _emerge_stats(tr_ref.steps)),
        ("WIT all", _emerge_stats(tr_wit.steps)),
        ("WIT fire", _emerge_stats(tr_wit.steps, True)),
        ("WIT other", _emerge_stats(tr_wit.steps, False)),
    ):
        print(f"    {label:<10s} n={stats['n']:3d}  fail {stats['failed']:3d} "
              f"({stats['fail_rate']:.2%})  mean_score {stats['mean_score']:+.4f}  "
              f"mean_cd {stats['mean_cd']:+.4f}")

    print("\n  emotional_satisfaction audit (code: emit_feedback sets "
          "es = max(0, coherence_delta); NOT emotion.joy):")
    for label, a in (("REF", es_r), ("WIT", es_w)):
        print(f"    {label}  es==relu(cd) {a['eq_relu']}/{a['n']}  "
              f"mean es {a['mean_es']:+.4f}  relu(cd) {a['mean_relu']:+.4f}  "
              f"joy {a['mean_joy']:.4f}  cd {a['mean_cd']:+.4f}  "
              f"watcher_coh {a['mean_coh']:.4f}")

    print("\n  temporal shape of gap = sum_live(WIT) - sum_live(REF):")
    print(f"    end gap {end_gap:+.4f}  mean d(gap)/step {_mean(d_gap):+.5f}  "
          f"p90 |d(gap)| {_fmt_u(p90, 4)}  steps with |d(gap)|>=0.10: {large}/{len(d_gap)}")
    print(f"    share of end-gap from small same-sign steps (|d|<0.05): {_fmt(trickle_share, 3)}")
    print(f"    mean d(gap) on witness-fire steps {_mean(d_at_wit):+.5f} (n={len(d_at_wit)})  "
          f"on other steps {_mean(d_not_wit):+.5f} (n={len(d_not_wit)})")
    print("    binned by steps-since-last-witness (WIT arm):")
    print(f"      {'bin':<12s} {'n':>4s} {'mean d(gap)':>12s} {'mean d(WIT)':>12s} "
          f"{'mean elr':>10s} {'mean cd':>10s}")
    for b in BIN_ORDER:
        row = bins[b]
        if not row["d_gap"] and not row["elr"]:
            continue
        print(f"      {b:<12s} {len(row['d_gap']):4d} {_fmt(_mean(row['d_gap']), 5):>12s} "
              f"{_fmt(_mean(row['d_wit']), 5):>12s} {_fmt_u(_mean(row['elr']), 4):>10s} "
              f"{_fmt(_mean(row['cd']), 4):>10s}")
    rec_mean = _mean(recoveries)
    rec_pos = sum(1 for x in recoveries if x > 0)
    print(f"    recovery stretches (gap change from a fire to next fire / end, "
          f"min 3 steps): n={len(recoveries)}  mean {rec_mean:+.4f}  "
          f"gap-shrunk {rec_pos}/{len(recoveries)}")
    print("    (negative mean recovery = WIT does not catch up; the gap widens or holds "
          "after the fire.)")

    print("\n  effective_lr = clip(watcher_composite^2, 0.01, 1):")
    print(f"    REF mean {elr_ref:.4f} (n={n_elr_ref})  WIT mean {elr_wit:.4f} (n={n_elr_wit})  "
          f"Δ {elr_wit - elr_ref:+.4f}")
    print(f"    WIT fire steps     {elr_fire:.4f} (n={n_elr_fire})")
    print(f"    WIT 1 after fire   {elr_1:.4f} (n={n_elr_1})")
    print(f"    WIT 2 after fire   {elr_2:.4f} (n={n_elr_2})")
    print(f"    WIT 3 after fire   {elr_3:.4f} (n={n_elr_3})")
    print(f"    WIT 10+ after fire {elr_late:.4f} (n={n_elr_late})")

    return {
        "seed": seed,
        "fired": fired,
        "ref": {k: h_ref[k] for k in
                ("injection_rate", "active_values", "strong", "mean_strength",
                 "n_live", "sum_live", "demotions", "gain") if k in h_ref},
        "wit": {k: h_wit[k] for k in
                ("injection_rate", "active_values", "strong", "mean_strength",
                 "n_live", "sum_live", "demotions", "gain") if k in h_wit},
        "polarity": {"REF": dict(pol_r), "WIT": dict(pol_w)},
        "decisions": {"REF": dict(dec_r), "WIT": dict(dec_w)},
        "residual": {"REF": res_r[0], "WIT": res_w[0]},
        "n_weaker": len(weaker),
        "n_stronger": len(stronger),
        "n_equal": len(equal),
        "n_ref_only": len(ref_only),
        "n_wit_only": len(wit_only),
        "weak_stack": weak_stack,
        "all_stack": all_stack,
        "weaker": [{k: r[k] for k in
                    ("core", "ref", "wit", "delta", "unexplained", "in_ref", "in_wit")}
                   | {"terms": r["terms"]}
                   for r in weaker_sorted],
        "reinf_sign": {
            "pos_ref": pos_r, "pos_wit": pos_w, "neg_ref": neg_r, "neg_wit": neg_w,
            "npos_ref": npos_r, "npos_wit": npos_w, "nneg_ref": nneg_r, "nneg_wit": nneg_w,
        },
        "non_reinf": {
            "decay": {"REF": _src_sum(tr_ref.events, "decay"),
                      "WIT": _src_sum(tr_wit.events, "decay")},
            "integrity": {"REF": _src_sum(tr_ref.events, "integrity"),
                          "WIT": _src_sum(tr_wit.events, "integrity")},
            "tension": {"REF": _src_sum(tr_ref.events, "tension"),
                        "WIT": _src_sum(tr_wit.events, "tension")},
            "dream": {"REF": _src_sum(tr_ref.events, "dream"),
                      "WIT": _src_sum(tr_wit.events, "dream")},
            "dissolve": {"REF": _src_sum(tr_ref.events, "dissolve"),
                         "WIT": _src_sum(tr_wit.events, "dissolve")},
        },
        "emergence": {
            "REF": _emerge_stats(tr_ref.steps),
            "WIT": _emerge_stats(tr_wit.steps),
            "WIT_fire": _emerge_stats(tr_wit.steps, True),
            "WIT_other": _emerge_stats(tr_wit.steps, False),
        },
        "es_audit": {"REF": es_r, "WIT": es_w},
        "temporal": {
            "end_gap": end_gap,
            "mean_d_gap": _mean(d_gap),
            "p90_abs_d_gap": p90,
            "n_large": large,
            "trickle_share": trickle_share,
            "d_gap_at_fire": _mean(d_at_wit),
            "d_gap_other": _mean(d_not_wit),
            "bins": {b: {"n": len(bins[b]["d_gap"]),
                         "mean_d_gap": _mean(bins[b]["d_gap"]),
                         "mean_d_wit": _mean(bins[b]["d_wit"]),
                         "mean_elr": _mean(bins[b]["elr"]),
                         "mean_cd": _mean(bins[b]["cd"])}
                     for b in BIN_ORDER},
            "recovery_mean": rec_mean,
            "recovery_n": len(recoveries),
            "recovery_shrunk": rec_pos,
        },
        "effective_lr": {
            "REF": elr_ref, "WIT": elr_wit, "delta": elr_wit - elr_ref,
            "fire": elr_fire, "after1": elr_1, "after2": elr_2, "after3": elr_3,
            "after10": elr_late,
        },
    }


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=_json_default, ensure_ascii=False) + "\n")


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def _strip_live(steps):
    """Drop the per-step live-strength map from the JSONL (it is large); keep scalars."""
    out = []
    for s in steps:
        d = dict(s)
        d.pop("live", None)
        out.append(d)
    return out


def main():
    seeds = [int(a) for a in sys.argv[1:] if a.lstrip("-").isdigit()] or [0, 1, 2]
    scratch = Path(tempfile.mkdtemp(prefix="value_reinforcement_trace_"))
    print(f"scratch: {scratch}")
    print("instrumentation is probe-only; runtime/gates/lever defaults unchanged.")

    summaries = []
    for i, seed in enumerate(seeds):
        if i == 0:
            print(f"\n-- replay check: gate.run({seed}, B, REF) vs traced REF --")
            h_gate, _ = gate_run(seed, "B", False)
            h_tr, tr_probe = traced_run(seed, False)
            fp_g, fp_t = _health_fingerprint(h_gate), _health_fingerprint(h_tr)
            match = fp_g == fp_t
            print(f"  REF vs gate.run: {'MATCH' if match else 'MISMATCH'}")
            if not match:
                for k in fp_g:
                    if fp_g[k] != fp_t[k]:
                        print(f"    {k}: gate={fp_g[k]!r}\n         traced={fp_t[k]!r}")
            h_ref, tr_ref = h_tr, tr_probe
        else:
            h_ref, tr_ref = traced_run(seed, False)
        h_wit, tr_wit = traced_run(seed, True)

        seed_dir = scratch / f"seed_{seed}"
        seed_dir.mkdir()
        _write_jsonl(seed_dir / "events_REF.jsonl", tr_ref.events)
        _write_jsonl(seed_dir / "events_WIT.jsonl", tr_wit.events)
        _write_jsonl(seed_dir / "steps_REF.jsonl", _strip_live(tr_ref.steps))
        _write_jsonl(seed_dir / "steps_WIT.jsonl", _strip_live(tr_wit.steps))
        # keep the per-step live maps (needed for recovery plots) as a sidecar
        _write_jsonl(seed_dir / "live_REF.jsonl",
                     [{"cycle_step": s["cycle_step"], "live": s["live"]} for s in tr_ref.steps])
        _write_jsonl(seed_dir / "live_WIT.jsonl",
                     [{"cycle_step": s["cycle_step"], "live": s["live"]} for s in tr_wit.steps])

        summary = summarize_seed(seed, h_ref, tr_ref, h_wit, tr_wit)
        if i == 0:
            summary["replay_match"] = match
        (seed_dir / "summary.json").write_text(
            json.dumps(summary, default=_json_default, indent=2), encoding="utf-8")
        summaries.append(summary)

    print("\n======== across seeds ========")
    print(f"  {'seed':>4s} {'fired':>5s} {'act R/W':>10s} {'str R/W':>10s} "
          f"{'mean R/W':>16s} {'Δsum':>8s} {'Δcd':>8s} {'Δes':>8s} {'Δdb':>8s} "
          f"{'Δdec':>8s} {'Δ⊘':>8s} {'unexp':>8s} {'elr R/W':>16s}")
    for s in summaries:
        st = s["weak_stack"]
        print(f"  {s['seed']:4d} {s['fired']:5d} "
              f"{s['ref']['active_values']:3d}/{s['wit']['active_values']:<6d} "
              f"{s['ref']['strong']:3d}/{s['wit']['strong']:<6d} "
              f"{s['ref']['mean_strength']:5.3f}/{s['wit']['mean_strength']:<8.3f} "
              f"{st['delta']:+8.3f} {st['coherence_delta']:+8.3f} "
              f"{st['emotional_satisfaction']:+8.3f} {st['decision_bonus']:+8.3f} "
              f"{st['decay']:+8.3f} {st['integrity']:+8.3f} {st['unexplained']:+8.3f} "
              f"{s['effective_lr']['REF']:.3f}/{s['effective_lr']['WIT']:.3f}")
    print(f"\nscratch: {scratch}")
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
