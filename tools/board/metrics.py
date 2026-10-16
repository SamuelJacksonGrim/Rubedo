"""Rolling-window metrics for one live run.

The estimators are the probe ones: timescale and MSD from h0_probe, the value
ecology counts from value_fixes_probe. Saturation, raw norm, and effective_lr
use the same cuts record_step and Witness.update use. The cone angle is the
lag-1 MSD of a unit expression, read as an angle the way the H0 note does
(||a−b||² = 2 − 2 cos).

Importing h0_probe disables logging. This module turns logging back on.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

# Machine time. Kept on the row for the page, dropped from the replay digest.
MACHINE_KEYS = ("overhead_ms", "step_ms_mean", "observe_ms_mean")

DECISIONS = (
    "ALLOW",
    "ALLOW_WEAKENED",
    "MONITOR",
    "QUARANTINE",
    "REJECT",
    "SACRED_SHIELD",
)
RHYTHMS = ("stabilize", "dream", "reflect", "explore")
# What ran, which is not the energy band once the selector or boredom is in play.
BEHAVIORS = (
    "stabilize", "dream", "reflect", "explore",
    "witness", "rupture", "dream_forced",
)
EMOTIONS = ("curiosity", "wonder", "joy", "tension", "boredom", "stability")
DAMP = ("systemic", "named", "other")

# One line each, because the names mislead. The page prints these under the curves.
SERIES = (
    ("sat", "Saturation",
     "Share of the field view stuck near ±1. High means the shape is clamped, not that it is healthy."),
    ("raw_norm", "Raw field size",
     "Size of the field before the squashing. It can grow while the view stays put."),
    ("field_coherence", "Field self-similarity",
     "How much the field matches its own recent average. The ~0.998 pin is this gauge, not the mind's flexibility."),
    ("watcher", "Watcher composite",
     "The score that gates identity writing. It is not the field pin."),
    ("effective_lr", "Anchor write rate",
     "How hard this step writes the identity anchor. It is the watcher score squared."),
    ("timescale_ratio", "Timescale ratio",
     "How much slower the identity anchor moves than expression, over this window. A shelf means the self is steady."),
    ("expr_cone_deg", "Expression cone",
     "How far the mind wanders, in degrees. Flat across a longer lag means jitter in place, not travel."),
    ("expr_msd", "Expression step",
     "How far expression jumps in one step (mean squared distance). Compare with the longer lag."),
    ("expr_msd_far", "Expression at a longer lag",
     "Same distance measured further apart. Close to the one-step number means the cone is not widening."),
    ("expr_mean_cosine", "Expression agreement",
     "How tightly expression points the same way across the window. 1 would be a single direction."),
    ("boredom", "Boredom",
     "The boredom scalar: low novelty in a loose field, not a mood. High can force the explore behavior."),
    ("boredom_overrides", "Boredom overrides",
     "Times in this window that boredom forced the explore behavior."),
    ("values_live", "Living values",
     "Values that have not been dissolved. On a small vocabulary this stops when the words run out."),
    ("values_births", "Value births",
     "New values born inside this window."),
    ("values_mean_strength", "Mean value strength",
     "Average strength of the living values. The cap is 5."),
    ("values_active", "Active band",
     "Values in the active polarity band only (strength from 2 up to 3.5), not every living value."),
    ("values_strong", "Strong values",
     "Living values at strength 3.5 or more. Includes any that were later promoted."),
    ("values_core", "CORE values",
     "Values governance has promoted. Promotion is the only way in."),
    ("values_core_promotions", "CORE promotions",
     "Promotions inside this window."),
    ("crystals", "Crystals",
     "Memory crystals held right now."),
    ("crystal_births", "New crystals",
     "Crystals added inside this window."),
    ("attractors", "Attractors",
     "Attractor centers held right now."),
    ("attractor_births", "New attractors",
     "Attractors added inside this window."),
    ("oslash_advisories", "⊘ advisories",
     "Thin values the integrity read named on its last look. Empty while the consumer is off, because the board does not call the read itself."),
    ("oslash_demotions", "⊘ demotions",
     "Values the consumer actually pulled down inside this window."),
)


def series_schema() -> list:
    return [{"key": key, "label": label, "plain": plain} for key, label, plain in SERIES]


_EST = None


def _estimators():
    global _EST
    if _EST is None:
        import logging
        from tests.diagnostic.integrity.value_fixes_probe import ecology
        from tests.diagnostic.metastability.h0_probe import msd_curve, timescale, unit_rows
        logging.disable(logging.NOTSET)
        _EST = (msd_curve, timescale, unit_rows, ecology)
    return _EST


class Samples:
    """Bounded per-step record. The metric row is computed from this, not from disk."""

    def __init__(self, maxlen: int):
        self.maxlen = int(maxlen)
        self.expr = deque(maxlen=self.maxlen)
        self.anchor = deque(maxlen=self.maxlen)
        self.sat = deque(maxlen=self.maxlen)
        self.raw_norm = deque(maxlen=self.maxlen)
        self.field_coh = deque(maxlen=self.maxlen)
        self.watcher = deque(maxlen=self.maxlen)
        self.eff_lr = deque(maxlen=self.maxlen)
        self.boredom = deque(maxlen=self.maxlen)
        self.boredom_hit = deque(maxlen=self.maxlen)
        self.rhythm = deque(maxlen=self.maxlen)
        self.behavior = deque(maxlen=self.maxlen)
        self.decision = deque(maxlen=self.maxlen)
        self.damp = deque(maxlen=self.maxlen)
        self.births = deque(maxlen=self.maxlen)
        self.crystal_d = deque(maxlen=self.maxlen)
        self.attractor_d = deque(maxlen=self.maxlen)
        self.core_d = deque(maxlen=self.maxlen)
        self.demote_d = deque(maxlen=self.maxlen)
        self.step_ms = deque(maxlen=self.maxlen)

    def push(self, **fields) -> None:
        for name, value in fields.items():
            getattr(self, name).append(value)


def observe_step(cycle, value_engine, state, boredom_before, crystals_before,
                 attractors_before, core_before, demote_delta, decision, damp,
                 step_ms):
    """One step's cheap reads. Vectors are copied so later mutation cannot rewrite them."""
    raw = np.asarray(cycle.field.field, dtype=np.float64)
    view = np.tanh(raw)
    expr = np.asarray(cycle._last_expressed, dtype=np.float64).copy()
    anchor = np.asarray(cycle.witness._anchor, dtype=np.float64).copy()
    # Same cuts as h0_probe.record_step and Witness.update.
    coherence = float(state.coherence)
    live = [v for v in value_engine.values.values() if v.dissolved_at_step < 0]
    births = sum(1 for v in value_engine.values.values() if v.birth_step == value_engine._step)
    core_now = sum(1 for v in live if v.promoted_to_sacred)
    crystals = len(cycle.crystal_store.crystals)
    attractors = len(cycle.attractor.centers)
    boredom_hit = int(cycle._boredom_overrides - boredom_before)
    return {
        "expr": expr,
        "anchor": anchor,
        "sat": float(np.mean(np.abs(view) > 0.95)),
        "raw_norm": float(np.linalg.norm(raw)),
        "field_coh": float(cycle.field.internal_coherence()),
        "watcher": coherence,
        "eff_lr": float(np.clip(coherence ** 2, 0.01, 1.0)),
        "boredom": float(cycle.emotion.boredom),
        "boredom_hit": boredom_hit,
        "rhythm": state.rhythm if state.rhythm in RHYTHMS else "other",
        "behavior": _behavior(state, boredom_hit),
        "decision": decision,
        "damp": damp,
        "births": int(births),
        "crystal_d": int(max(0, crystals - crystals_before)),
        "attractor_d": int(max(0, attractors - attractors_before)),
        "core_d": int(max(0, core_now - core_before)),
        "demote_d": int(max(0, demote_delta)),
        "step_ms": float(step_ms),
        "crystals": crystals,
        "attractors": attractors,
        "core_now": core_now,
    }


def _mean(xs) -> float | None:
    if not xs:
        return None
    return float(np.mean(np.asarray(xs, dtype=np.float64)))


def _finite(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _cone_deg(msd):
    """Lag-1 MSD of unit vectors, as an angle. None when the MSD is not a real distance."""
    number = _finite(msd)
    if number is None or number < 0.0:
        return None
    cosine = float(np.clip(1.0 - 0.5 * number, -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))


def _behavior(state, boredom_hit: int) -> str:
    """The act that ran. The selector records it; boredom is visible either way.

    With the selector off, extras stay empty, so a boredom force is taken from
    the override counter. Witness and rupture only appear once the selector
    writes them. The energy band stays on `rhythm`.
    """
    extras = getattr(state, "extras", None) or {}
    raw = extras.get("behavior") if isinstance(extras, dict) else None
    if raw == "dream (forced)":
        return "dream_forced"
    if raw in BEHAVIORS:
        return raw
    if boredom_hit:
        return "explore"
    if getattr(state, "rhythm", None) in RHYTHMS:
        return state.rhythm
    return "other"


def _counts(items, keys) -> dict:
    out = {key: 0 for key in keys}
    other = 0
    for item in items:
        if item in out:
            out[item] += 1
        else:
            other += 1
    if other:
        out["other"] = other
    return out


def _ratio(anchor_tau, expr_tau):
    """Same cases as h0_probe._ratio, without importing it (it is private)."""
    if anchor_tau == float("inf") and expr_tau == float("inf"):
        return None, "both unresolved"
    if expr_tau == float("inf"):
        return 0.0, "expression unresolved"
    if anchor_tau == float("inf"):
        return None, "anchor slower than window"
    if not expr_tau:
        return None, "expression tau is 0"
    return float(anchor_tau / expr_tau), "measured"


def window_row(samples: Samples, cycle, value_engine, board_advisory, consumer_on,
               levers: dict, step: int, overhead_ms: float) -> dict:
    msd_curve, timescale, unit_rows, ecology = _estimators()
    n = len(samples.sat)
    expr = np.stack(samples.expr) if n else np.zeros((0, 1))
    anchor = np.stack(samples.anchor) if n else np.zeros((0, 1))

    tau_anchor = None
    tau_expr = None
    ratio = None
    bound = "too short"
    if n >= 8:
        max_lag = max(1, min(128, n // 4))
        a = timescale(anchor, max_lag)
        e = timescale(expr, max_lag)
        tau_anchor = _finite(a["tau_e"])
        tau_expr = _finite(e["tau_e"])
        # timescale reports inf as the number, which _finite drops. Recover the case.
        ratio, bound = _ratio(a["tau_e"], e["tau_e"])
        if a["status"] == "frozen" or e["status"] == "frozen":
            bound = "frozen"
            ratio = None

    expr_msd = None
    expr_msd_far = None
    mean_cos = None
    cone = None
    if n >= 2:
        far = 1 if n < 8 else min(32, max(2, n // 4))
        lags = [1] if far == 1 else [1, far]
        curve = msd_curve(expr, lags)
        expr_msd = _finite(curve[0])
        expr_msd_far = expr_msd if far == 1 else _finite(curve[1])
        cone = _cone_deg(expr_msd)
        units = unit_rows(expr)
        center = units.mean(axis=0)
        norm = float(np.linalg.norm(center))
        if norm > 0.0:
            center = center / norm
            mean_cos = float(np.mean(units @ center))

    eco = ecology(value_engine)
    polarity = eco.get("polarity") or {}
    strong = sum(
        1 for v in value_engine.values.values()
        if v.dissolved_at_step < 0 and float(v.strength) >= 3.5
    )
    emotions = {name: float(getattr(cycle.emotion, name)) for name in EMOTIONS}

    by_path = {}
    advisories = None
    if consumer_on:
        advisories = board_advisory.get("n")
        by_path = dict(board_advisory.get("by") or {})

    step_ms = _mean(samples.step_ms)
    row = {
        "step": int(step),
        "window": int(n),
        "sat": _mean(samples.sat),
        "raw_norm": _mean(samples.raw_norm),
        "field_coherence": _mean(samples.field_coh),
        "watcher": _mean(samples.watcher),
        "effective_lr": _mean(samples.eff_lr),
        "tau_anchor": tau_anchor,
        "tau_expr": tau_expr,
        "timescale_ratio": _finite(ratio) if ratio is not None else None,
        "timescale_bound": bound,
        "expr_msd": expr_msd,
        "expr_msd_far": expr_msd_far,
        "expr_mean_cosine": mean_cos,
        "expr_cone_deg": cone,
        "boredom": _mean(samples.boredom),
        "boredom_overrides": int(sum(samples.boredom_hit)),
        "boredom_overrides_total": int(cycle._boredom_overrides),
        "rhythm": _counts(samples.rhythm, RHYTHMS),
        "behavior": _counts(samples.behavior, BEHAVIORS),
        "decisions": _counts(samples.decision, DECISIONS),
        "damp": _counts(samples.damp, DAMP),
        "values_live": int(eco["live"]),
        "values_births": int(sum(samples.births)),
        "values_mean_strength": float(eco["mean_strength"]),
        "values_active": int(polarity.get("active", 0)),
        "values_strong": int(strong),
        "values_core": int(eco["core"]),
        "values_core_promotions": int(sum(samples.core_d)),
        "crystals": int(len(cycle.crystal_store.crystals)),
        "crystal_births": int(sum(samples.crystal_d)),
        "attractors": int(len(cycle.attractor.centers)),
        "attractor_births": int(sum(samples.attractor_d)),
        "oslash_attached": bool(consumer_on),
        "oslash_advisories": advisories,
        "oslash_by_pathology": by_path,
        "oslash_demotions": int(sum(samples.demote_d)),
        "oslash_demotions_total": _demote_total(cycle),
        "emotions": emotions,
        "levers": dict(levers),
        "overhead_ms": float(overhead_ms),
        "step_ms_mean": step_ms,
    }
    return row


def _demote_total(cycle) -> int:
    consumer = cycle.integrity_consumer
    if consumer is None:
        # Detached. The held object may still exist on the board; the row
        # reports the consumer that is actually in the step. Frozen at 0
        # while detached would hide history, so prefer the live attachment.
        return 0
    return int(getattr(consumer, "demotions_total", 0))
