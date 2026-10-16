"""
tests/integration/core_promotion_handshake.py

Verifies SelfhoodGovernance.review_core_promotion() correctly applies
all five verification checks:

  1. Symbol still exists in registry
  2. Symbol is not already sacred
  3. Field-alignment ≥ CORE_ALIGNMENT_MIN (v0.3 — replaces the dead marginal
     coherence_contribution ≥ 5.0 gate)
  4. Multi-source OR dream-reinforced
  5. No active manipulation implicating contributing sources

The five rejection paths must all fire; the "all-pass" case must approve.
This is the regression guard for the value emergence → governance
handshake — Tier 4 will modify the feedback signal that drives value
strength, and we must be sure the promotion contract still holds.

Run:
    python -m tests.integration.core_promotion_handshake
"""

import sys

import numpy as np

from tests._common import build_full_stack
from agents.value_emergence import CorePromotionRequest
from agents.manipulation_resistance import ManipulationSignal
from tests.integration.governance_decision_flow import clean_ethical_result, trust_report


def make_request(
    value_id:                   str   = "test_value",
    symbol_stable_id:           int   = None,    # filled in per test
    symbolic_core:              str   = "test_symbol",
    strength:                   float = 4.6,
    coherence_contribution:     float = 6.0,
    field_alignment:            float = 0.8,    # passing by default (>= CORE_ALIGNMENT_MIN)
    reinforcement_count:        int   = 20,
    dream_reinforced_count:     int   = 0,
    consecutive_eligible_steps: int   = 10,
    contributing_sources:       dict  = None,
) -> CorePromotionRequest:
    """Construct a CorePromotionRequest with sensible defaults."""
    if contributing_sources is None:
        contributing_sources = {"source_a": 0.5, "source_b": 0.5}
    return CorePromotionRequest(
        value_id                   = value_id,
        symbol_stable_id           = symbol_stable_id,
        symbolic_core              = symbolic_core,
        strength                   = strength,
        coherence_contribution     = coherence_contribution,
        field_alignment            = field_alignment,
        reinforcement_count        = reinforcement_count,
        dream_reinforced_count     = dream_reinforced_count,
        consecutive_eligible_steps = consecutive_eligible_steps,
        contributing_sources       = contributing_sources,
    )


def expect(case_name: str, result: bool, expected: bool) -> bool:
    passed = result == expected
    mark = "✓" if passed else "✗"
    outcome = "APPROVED" if result else "REJECTED"
    expected_outcome = "APPROVE" if expected else "REJECT"
    print(f'  {mark} {case_name:<52} → {outcome:<10} (expected {expected_outcome})')
    return passed


def main():
    print('=' * 72)
    print('  INTEGRATION: CORE promotion handshake')
    print('=' * 72)
    print()

    generator, cycle, governance, value_engine = build_full_stack()
    registry = generator.registry
    results = []

    # ──────────────────────────────────────────────────────────────────
    # Case 1: REJECT — symbol does not exist in registry
    # ──────────────────────────────────────────────────────────────────
    governance._pending_signals = []
    req = make_request(
        symbol_stable_id = 999999,    # never registered
        symbolic_core    = "nonexistent_symbol",
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Symbol vanished from registry", result, False))

    # ──────────────────────────────────────────────────────────────────
    # Case 2: REJECT — symbol is already sacred
    # ──────────────────────────────────────────────────────────────────
    # Use one of the three philosophical constants — already sacred at boot
    sacred_id = next(iter(governance.constants.sacred_ids))
    state = registry.get_by_stable_id(sacred_id)
    governance._pending_signals = []
    req = make_request(
        symbol_stable_id = sacred_id,
        symbolic_core    = state.symbol,
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Symbol already sacred", result, False))

    # ──────────────────────────────────────────────────────────────────
    # Case 3: REJECT — field-alignment below threshold (v0.3 gate)
    # ──────────────────────────────────────────────────────────────────
    sid = registry.register("misaligned_value").stable_id
    governance._pending_signals = []
    req = make_request(
        symbol_stable_id = sid,
        symbolic_core    = "misaligned_value",
        field_alignment  = 0.3,    # below CORE_ALIGNMENT_MIN (0.5)
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Field-alignment below CORE_ALIGNMENT_MIN", result, False))

    # ──────────────────────────────────────────────────────────────────
    # Case 4: REJECT — single source, no dream reinforcement
    # ──────────────────────────────────────────────────────────────────
    sid = registry.register("single_source_value").stable_id
    governance._pending_signals = []
    req = make_request(
        symbol_stable_id       = sid,
        symbolic_core          = "single_source_value",
        contributing_sources   = {"only_source": 1.0},   # single source
        dream_reinforced_count = 0,                      # no dreams
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Single source, no dream reinforcement", result, False))

    # ──────────────────────────────────────────────────────────────────
    # Case 5: REJECT — manipulation signal implicates contributor
    # ──────────────────────────────────────────────────────────────────
    sid = registry.register("contaminated_value").stable_id
    governance._pending_signals = [
        ManipulationSignal(
            detector="trust_wash", severity=0.5,
            source_id="bad_actor", evidence={},
        )
    ]
    req = make_request(
        symbol_stable_id     = sid,
        symbolic_core        = "contaminated_value",
        contributing_sources = {"bad_actor": 0.6, "good_source": 0.4},
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Manipulation signal from contributing source",
                          result, False))

    # ──────────────────────────────────────────────────────────────────
    # Case 6: APPROVE — multi-source, no dreams, all gates pass
    # ──────────────────────────────────────────────────────────────────
    sid = registry.register("clean_multi_source_value").stable_id
    governance._pending_signals = []
    req = make_request(
        symbol_stable_id       = sid,
        symbolic_core          = "clean_multi_source_value",
        contributing_sources   = {"source_a": 0.4, "source_b": 0.4, "source_c": 0.2},
        dream_reinforced_count = 0,
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Clean multi-source promotion", result, True))

    # Verify it actually became sacred
    state_after = registry.get_by_stable_id(sid)
    sacred_after = state_after is not None and state_after.sacred
    mark = "✓" if sacred_after else "✗"
    print(f'  {mark} {"Symbol marked sacred after approval":<52} → '
          f'{"sacred=True" if sacred_after else "sacred=False"}')
    results.append(sacred_after)

    # ──────────────────────────────────────────────────────────────────
    # Case 7: APPROVE — single source + dream-reinforced
    # ──────────────────────────────────────────────────────────────────
    sid = registry.register("dream_reinforced_value").stable_id
    governance._pending_signals = []
    req = make_request(
        symbol_stable_id       = sid,
        symbolic_core          = "dream_reinforced_value",
        contributing_sources   = {"only_source": 1.0},   # single source
        dream_reinforced_count = 5,                      # but dream-reinforced
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Single-source value with dream reinforcement",
                          result, True))

    # ──────────────────────────────────────────────────────────────────
    # Case 8: REJECT — contributor named in a signal arbitrate already ate
    # ──────────────────────────────────────────────────────────────────
    sid = registry.register("consumed_signal_value").stable_id
    governance._pending_signals = [
        ManipulationSignal(
            detector="trust_wash", severity=0.5,
            source_id="bad_actor", evidence={},
        )
    ]
    governance.arbitrate(
        clean_ethical_result(),
        trust_report(source_id="speaker"),
        np.zeros(4),
        ["consumed_signal_value"],
        "speaker",
    )
    pending_empty = governance._pending_signals == []
    consumed = any(s.source_id == "bad_actor" for s in governance._step_signals)
    mark = "✓" if pending_empty and consumed else "✗"
    print(f'  {mark} {"Arbitrate consumed the signal into _step_signals":<52} → '
          f'pending_empty={pending_empty} consumed={consumed}')
    results.append(pending_empty and consumed)
    req = make_request(
        symbol_stable_id     = sid,
        symbolic_core        = "consumed_signal_value",
        contributing_sources = {"bad_actor": 0.6, "good_source": 0.4},
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Consumed signal from a contributor blocks promotion",
                          result, False))

    # ──────────────────────────────────────────────────────────────────
    # Case 9: APPROVE — a consumed systemic signal names nobody
    # ──────────────────────────────────────────────────────────────────
    sid = registry.register("systemic_signal_value").stable_id
    governance._pending_signals = [
        ManipulationSignal(
            detector="identity_erosion", severity=0.55,
            source_id=None, evidence={},
        )
    ]
    governance.arbitrate(
        clean_ethical_result(),
        trust_report(source_id="speaker"),
        np.zeros(4),
        ["systemic_signal_value"],
        "speaker",
    )
    req = make_request(
        symbol_stable_id     = sid,
        symbolic_core        = "systemic_signal_value",
        contributing_sources = {"source_a": 0.5, "source_b": 0.5},
    )
    result = governance.review_core_promotion(req)
    results.append(expect("Consumed systemic signal does not block promotion",
                          result, True))

    print()
    print('=' * 72)
    passed = sum(1 for r in results if r)
    total  = len(results)
    if passed == total:
        print(f'  ALL CHECKS PASS: {passed}/{total} handshake gates verified.')
        return 0
    else:
        print(f'  FAILED: {passed}/{total} checks correct.')
        return 1


if __name__ == '__main__':
    sys.exit(main())
