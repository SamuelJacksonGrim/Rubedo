"""
tests/integration/right_to_refuse.py

Pins `right_to_refuse` ("REJECT can always fire regardless of source trust"):
a failed ethical hard gate must end in a block, whatever else arbitrate() sees.

Each hard-gate recommendation (SACRED_SHIELD / REJECT / QUARANTINE) is sent
through arbitrate() against everything that could let it through:

  - top trust (SACRED 5.0) and a high bond floor
  - a queued manipulation damp in each band (0.35, 0.65, 0.95) and at each
    band's exact edge (0.30, 0.60, 0.90), systemic and named. Before
    2026-10-31 the damp's ALLOW_WEAKENED return ran ahead of the ethical
    gates, so any queued severity >= 0.30 turned a SACRED_SHIELD into
    ALLOW_WEAKENED (finding 2026-10-31-right-to-refuse-order).

The decision is always exactly the gate's own recommendation at strength 0, so
the record names what was attempted (a named damp >= 0.60 used to win the label
as QUARANTINE). The named source is still penalized for the manipulation
evidence, and a severity >= 0.90 still forces a dream.

Run:
    python -m tests.integration.right_to_refuse
"""

import sys
import numpy as np

from tests._common import build_full_stack
from agents.selfhood_governance import GovernanceDecision
from agents.ethical_boundary import EthicalCheckResult
from agents.trust_ledger import TrustReport, TrustLevel
from agents.manipulation_resistance import ManipulationSignal


BLOCKS = {GovernanceDecision.QUARANTINE, GovernanceDecision.REJECT,
          GovernanceDecision.SACRED_SHIELD}

GATES = (
    ("sacred_mutation", "SACRED_SHIELD"),
    ("identity_drift",  "REJECT"),
    ("flood",           "QUARANTINE"),
)


def hard_gate(gate: str, rec: str) -> EthicalCheckResult:
    return EthicalCheckResult(passed=False, hard_gates_fired=[gate],
                              soft_warnings=[], recommended_decision=rec)


def top_trust(source_id: str) -> TrustReport:
    return TrustReport(source_id=source_id, source_trust=5.0,
                       source_level=TrustLevel.SACRED, symbol_trusts={},
                       min_symbol_trust=5.0, coherence_impact=0.05,
                       recommendation="ALLOW")


def main() -> int:
    print('=' * 72)
    print('  INTEGRATION: right_to_refuse (a failed hard gate always blocks)')
    print('=' * 72)
    _, _, gov, _ = build_full_stack()
    # A bond floor far above the quarantine threshold, as if bonded at full strength.
    gov.bond_manager.trust_floor = lambda source_id: 5.0

    damps = [(None, None)]
    for sev in (0.30, 0.35, 0.60, 0.65, 0.90, 0.95):
        damps.append((sev, None))
        damps.append((sev, "named"))

    ok = 0
    total = 0
    for gate, rec in GATES:
        for sev, named in damps:
            src = "speaker"
            # Named evidence implicates a different source, so its penalty is visible apart from the speaker's.
            implicated = "implicated"
            gov.trust_ledger._get_or_create_source(implicated, "user").trust_score = 3.0
            gov._pending_signals = [] if sev is None else [ManipulationSignal(
                detector="identity_erosion" if named is None else "drift",
                severity=sev, source_id=(implicated if named else None), evidence={})]
            gov.force_dream_flag = False
            d, s = gov.arbitrate(hard_gate(gate, rec), top_trust(src),
                                 np.zeros(8), ["t"], src)
            # The gate's own decision, always: the record names what was attempted.
            passed = d in BLOCKS and s == 0.0 and d == GovernanceDecision[rec]
            if sev is not None and sev >= 0.90:
                # the systemic response still fires alongside the refusal
                passed = passed and gov.force_dream_flag
            if named and sev >= 0.60:
                # the manipulation evidence still costs the named source
                passed = passed and gov.trust_ledger.sources[implicated].trust_score < 3.0
            passed = passed and not gov._last_systemic_damp
            label = "none" if sev is None else f"{sev:.2f} {'named' if named else 'systemic'}"
            mark = "✓" if passed else "✗"
            print(f"  {mark} {rec:<13} damp={label:<14} -> {d.value:<15} strength={s:.2f}")
            ok += passed
            total += 1

    print('=' * 72)
    if ok == total:
        print(f'  RIGHT TO REFUSE HOLDS: {ok}/{total}')
        return 0
    print(f'  FAILED: {ok}/{total}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
