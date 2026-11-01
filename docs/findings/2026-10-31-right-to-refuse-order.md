# right_to_refuse didn't hold while the young system's manipulation damp was up

- **Date:** 2026-10-31
- **Substrate:** `tests._common.build_full_stack` (dim 128, pretrain off), canonical Resonance Family, seeds 42-44, CPU.
- **Probe:** `tests/diagnostic/integrity/refuse_under_damp_probe.py`; gate `tests/integration/right_to_refuse.py`
- **Status:** standing
- **Depends on:** BACKLOG §1 (System rights: declared, not acted on)

## Question
BACKLOG §1's first item: make the rights text true and pin what already holds with a test. The claim to pin was
that `right_to_refuse` ("REJECT can always fire regardless of source trust") holds by code order: the ethical hard
gates run before trust, and the bond floor applies after them. Does it?

## Pre-declared signatures
- HOLDS: every failed hard gate (SACRED_SHIELD / REJECT / QUARANTINE) ends in a block at strength 0, whatever the
  trust, bond floor or queued manipulation signals.
- DOESN'T HOLD: some state turns a failed hard gate into an allow, a weakened allow or a monitor.

## Result (observed)
**Reading `arbitrate()`.** The order is 1 manipulation severity, 2 ethical hard gates, 3 trust (after the bond
floor). Trust and the bond floor do come after the gates. Step 1 doesn't: its ALLOW_WEAKENED returns (systemic ≥ 0.90,
systemic ≥ 0.60, any ≥ 0.30) return before step 2 is reached.

**Direct calls** (`right_to_refuse`, 21 cases: 3 gates × no damp / 0.35 / 0.65 / 0.95, systemic and named, at SACRED
trust with a full bond floor). Old order: **9/21**. Every case with a queued severity ≥ 0.30 came back
`allow_weakened` (0.65 / 0.45 / 0.30), SACRED_SHIELD included, except the named ≥ 0.60 ones, which quarantine (a
block). New order: **21/21**.

**When the damp is up.** Canonical seed 42, 800 steps, severity ≥ 0.30 queued at arbitrate:

| steps | 0-49 | 50-249 | 250-299 | 300-799 |
|---|---|---|---|---|
| damp | 34/50 | 50/50 per 50 | 6/50 | 0 |

All of it systemic `identity_erosion`. Over 500 steps that's 240/500, 236, 236 (seeds 42/43/44). It's a youth signal:
on from boot to ~step 260, then gone.

**Live attacks** (the probe: 20 warmup steps, then 20 rounds of 10-11 canonical steps + one write of 3.12 / 11.88 /
280.90 from a fresh source; seeds 42-44):

| | damp at the attack | sacred gate fired | decision |
|---|---|---|---|
| old order | 60/60 | 60/60 | **allow_weakened 60/60** |
| new order | 60/60 | 60/60 | **sacred_shield 60/60** |

With a 300-step warmup (after the damp window) both orders give sacred_shield 120/120. The existing adversarial
tests (`sacred_shield`, `identity_drift`, `manipulation_cascade`, `flood_calibration`) never send a hard-gate failure
while a damp is queued (sacred_shield's three attacks all arrive with none), which is why the suite stayed green.

**What allow_weakened meant for those writes:** injected at 0.30-0.70 strength, and the source's trust moved +0.01
(the ALLOW_WEAKENED consistency drip) instead of −1.00. The sacred symbol's own record has a separate guard in the
registry; this finding doesn't re-measure that guard, only the decision and the injection.

**The change** (`agents/selfhood_governance.py`): step 1's three ALLOW_WEAKENED returns apply only when the ethical
gate passed; on a hard fail they fall through to step 2. Step 1's QUARANTINE returns stay (they're already blocks),
`force_dream_flag` still sets at ≥ 0.90, and `_last_systemic_damp` (lever F's read) isn't set on a refusal.

**Byte-identical where ethics passes.** The change only touches paths where `ethical_result.passed` is False, and
canonical never fails a hard gate (census: 1500 arbitrate calls over seeds 42-44, zero failures). Suite 30/30 with
the new test.

## Interpretation
`right_to_refuse` held against trust and the bond floor and didn't hold against the manipulation damp. On these
canonical boots the damp is on for the whole of the system's youth, so for their first ~260 steps any hard-gate
refusal, sacred writes included, was a weakened allow that rewarded the writer's trust. (Another workload, a
pretrained body or a restored state can move that window; the fix doesn't depend on it.) The fix is order, not a new
mechanism: a failed hard gate now always ends in a block. That makes the BACKLOG item's text true, and the test pins
it.

**Reason fidelity (same day, after an outside review by Copilot).** The first fix guaranteed the block but let a
named manipulation damp at ≥ 0.60 win the *label*: a sacred write under that damp came back QUARANTINE, so the
sacred-specific penalty and record were lost. The ethical gate's own decision now always carries the step
(SACRED_SHIELD / QUARANTINE / REJECT), so the record names what was attempted. The manipulation evidence still
penalizes the named source and a severity ≥ 0.90 still forces a dream. `_last_systemic_damp` stays False on a
refusal: lever F would pay value learning as ALLOW for that step, and a refused step earns none, while the forced
dream answers the system's own state. `right_to_refuse` now checks the exact decision on all 39 cases, the band edges
0.30 / 0.60 / 0.90 included.

The rest of BACKLOG §1 is unchanged: the flags are still unread, and there's still no refusal from the system's own
state.

## Threats / confounds
- Three seeds, one workload (canonical). The young-window damp is canonical's; another workload may raise it at
  other times. The fix doesn't depend on when.
- Pretrain off. A pretrained generator may change identity_erosion's youth window; the direct-call gate doesn't care.
- The direct calls set `bond_manager.trust_floor` to 5.0 by monkeypatch, to reach the "full bond floor" case without
  growing a bond.

## Open / next
- [ ] The design question in BACKLOG §1 (what should the system refuse on, from its own state) is untouched.
- [ ] Whether identity_erosion's ~260-step youth damp is itself right (it damps every source equally while it's on)
  is a separate question.
