"""
tests/integration/value_lever_contracts.py

Levers C–G default off and, off, do not change the quantity they replace.
On, each one pays the thing it claims and does not pay the things it must
not (injection strength, trust impact, a named-source damp, quarantine).

Run:
    python -m tests.integration.value_lever_contracts
"""

import sys

import numpy as np

from agents.manipulation_resistance import ManipulationSignal
from agents.selfhood_governance import GovernanceDecision
from agents.value_emergence import ExperienceReport
from agents.watcher import Watcher
from substrate.resonance_field import ResonanceField
from tests._common import build_full_stack
from tests.integration.governance_decision_flow import clean_ethical_result, trust_report


def expect(name, ok, detail=""):
    print(f"  {'✓' if ok else '✗'} {name}" + (f"  ({detail})" if detail and not ok else ""))
    return bool(ok)


def _like_for_like():
    field = ResonanceField(dim=16)
    rng = np.random.default_rng(1)
    for _ in range(8):
        field.inject(rng.normal(size=16), strength=0.4)
    vec = rng.normal(size=16)
    hist = np.mean(list(field.history)[-32:], axis=0)
    mean_norm = np.linalg.norm(hist)
    probed = np.tanh(field.field + vec * 0.5)
    after = float(np.dot(probed, hist) / (np.linalg.norm(probed) * mean_norm + 1e-8))
    raw_before = float(
        np.dot(field.field, hist) / (np.linalg.norm(field.field) * mean_norm + 1e-8)
    )
    tanh_before_vec = np.tanh(field.field)
    tanh_before = float(
        np.dot(tanh_before_vec, hist) / (np.linalg.norm(tanh_before_vec) * mean_norm + 1e-8)
    )
    off = field.coherence_impact(vec)
    field.coherence_like_for_like = True
    on = field.coherence_impact(vec)
    field_ok = (
        abs(off - float(np.clip(after - raw_before, -1.0, 1.0))) < 1e-9
        and abs(on - float(np.clip(after - tanh_before, -1.0, 1.0))) < 1e-9
        and abs(on - off) > 1e-6
    )

    watcher = Watcher(dim=16, field=field)
    field.coherence_like_for_like = False
    watcher.coherence_like_for_like = False
    w_off = watcher._coherence_delta(vec)
    watcher.coherence_like_for_like = True
    w_on = watcher._coherence_delta(vec)
    # Watcher maps both cosines through (cos+1)/2, so the gap is on a half scale.
    def half(cosine):
        return (cosine + 1.0) / 2.0

    def cos(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    w_off_expected = half(cos(probed, hist)) - half(cos(field.field, hist))
    w_on_expected = half(cos(probed, hist)) - half(cos(tanh_before_vec, hist))
    watch_ok = (
        abs(w_off - w_off_expected) < 1e-9
        and abs(w_on - w_on_expected) < 1e-9
        and abs(w_on - w_off) > 1e-8
    )
    return field_ok, watch_ok


def _arbitrate(gov, signal):
    gov._pending_signals = [signal]
    return gov.arbitrate(
        clean_ethical_result(),
        trust_report(),
        np.zeros(4),
        ["token"],
        "speaker",
    )


def main():
    print("=" * 72)
    print("  INTEGRATION: value-path lever contracts")
    print("=" * 72)
    results = []

    field_ok, watch_ok = _like_for_like()
    results.append(expect("D off is raw-vs-tanh; on is tanh-vs-tanh", field_ok))
    results.append(expect("D drives the watcher copy with the same switch", watch_ok))

    gen, cycle, gov, ve = build_full_stack()
    systemic = ManipulationSignal(
        detector="identity_erosion", severity=0.55, source_id=None, evidence={},
    )
    named = ManipulationSignal(
        detector="trust_wash", severity=0.55, source_id="bad_actor", evidence={},
    )
    quarantining = ManipulationSignal(
        detector="trust_wash", severity=0.75, source_id="bad_actor", evidence={},
    )

    gov.systemic_damp_pays_full = False
    dec_off, strength_off = _arbitrate(gov, systemic)
    paid = []

    def capture(report):
        paid.append((report.decision, report.trust_impact, report.coherence_delta))

    ve.evaluate_experience = capture
    fb_off = gov.emit_feedback(dec_off, "speaker", [], -0.2, field_alignment=0.8)
    results.append(expect(
        "F off: systemic damp stays ALLOW_WEAKENED for the value engine",
        dec_off == GovernanceDecision.ALLOW_WEAKENED
        and "value_payment" not in fb_off.outcome_metrics
        and paid[-1][0] == "allow_weakened"
        and abs(fb_off.outcome_metrics["trust_impact"] - 0.01) < 1e-12
        and abs(fb_off.outcome_metrics["emotional_satisfaction"]) < 1e-12,
    ))

    gov.systemic_damp_pays_full = True
    dec_on, strength_on = _arbitrate(gov, systemic)
    fb_on = gov.emit_feedback(dec_on, "speaker", [], -0.2, field_alignment=0.8)
    results.append(expect(
        "F on: injection verdict stays weakened, value engine is paid ALLOW",
        dec_on == GovernanceDecision.ALLOW_WEAKENED
        and abs(strength_on - strength_off) < 1e-12
        and fb_on.decision == "allow_weakened"
        and fb_on.outcome_metrics.get("value_payment") == "allow"
        and abs(fb_on.outcome_metrics["trust_impact"] - 0.01) < 1e-12
        and paid[-1][0] == "allow",
    ))

    dec_named, strength_named = _arbitrate(gov, named)
    fb_named = gov.emit_feedback(dec_named, "speaker", [], -0.2, field_alignment=0.8)
    results.append(expect(
        "F on does not re-pay a named-source damp",
        dec_named == GovernanceDecision.ALLOW_WEAKENED
        and "value_payment" not in fb_named.outcome_metrics
        and paid[-1][0] == "allow_weakened",
    ))

    dec_q, strength_q = _arbitrate(gov, quarantining)
    fb_q = gov.emit_feedback(dec_q, "speaker", [], -0.2, field_alignment=0.8)
    results.append(expect(
        "F on does not soften a named quarantine",
        dec_q == GovernanceDecision.QUARANTINE
        and strength_q == 0.0
        and "value_payment" not in fb_q.outcome_metrics
        and paid[-1][0] == "quarantine",
    ))

    # G: explicit override, and the cycle only passes it when the flag is on.
    fb_g_off = gov.emit_feedback(
        GovernanceDecision.ALLOW, "speaker", [], -0.2, field_alignment=0.4,
    )
    fb_g_on = gov.emit_feedback(
        GovernanceDecision.ALLOW, "speaker", [], -0.2, field_alignment=0.4,
        satisfaction=0.37,
    )
    seen = []
    orig_emit = gov.emit_feedback

    def spy(*args, **kwargs):
        seen.append(dict(kwargs))
        return orig_emit(*args, **kwargs)

    gov.emit_feedback = spy
    cycle.satisfaction_from_emotion = False
    cycle.step(["hello", "field"], source_id="speaker", origin_type="internal")
    off_kw = seen[-1]
    cycle.satisfaction_from_emotion = True
    cycle.step(["hello", "field"], source_id="speaker", origin_type="internal")
    on_kw = seen[-1]
    # valence was updated by the step before emit, so the kw matches it now.
    results.append(expect(
        "G off is max(0, cd); on reads max(0, valence) from the cycle",
        abs(fb_g_off.outcome_metrics["emotional_satisfaction"]) < 1e-12
        and abs(fb_g_on.outcome_metrics["emotional_satisfaction"] - 0.37) < 1e-12
        and "satisfaction" not in off_kw
        and abs(on_kw.get("satisfaction", -1.0) - max(0.0, cycle.emotion.valence)) < 1e-12,
    ))

    # E: off adds coherence_delta; on adds alignment minus its EMA.
    sid = gen.registry.register("align_token").stable_id

    def report(alignment, cd=-0.1):
        return ExperienceReport(
            source_id="speaker", bond_type=None, bond_confidence=0.0,
            stable_ids=[sid], coherence_delta=cd,
            emotional_satisfaction=0.0, surprise=0.1, trust_impact=0.10,
            decision="allow", field_alignment=alignment,
        )

    ve.evaluate_experience = ve.__class__.evaluate_experience.__get__(ve, ve.__class__)
    ve.value_alignment_signal = False
    ve.evaluate_experience(report(0.90))
    value = ve.get_value_for_symbol(sid)
    off_sum = value.coherence_contribution
    ve.value_alignment_signal = True
    ve.alignment_ema_alpha = 0.05
    ve._alignment_ema = None
    before = value.coherence_contribution
    ve.evaluate_experience(report(0.90))
    first = value.coherence_contribution - before
    before = value.coherence_contribution
    ve.evaluate_experience(report(0.95))
    second = value.coherence_contribution - before
    results.append(expect(
        "E off sums cd; on sums alignment minus the running EMA",
        abs(off_sum - (-0.1)) < 1e-9
        and abs(first) < 1e-12
        and abs(second - 0.05) < 1e-9,
        detail=f"off={off_sum:.4f} first={first:.4f} second={second:.4f}",
    ))

    print()
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"  ALL CHECKS PASS: {passed}/{total}")
        return 0
    print(f"  FAILED: {passed}/{total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
