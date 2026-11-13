# Handoff: Local Claude / Ember and Cross-Model Reviewers

**Context:** Samuel requested that the November 13, 2026 cross-model inquiry be placed in Rubedo GitHub **before** sending additional speculative implementation messages. The Claude and Copilot instances that produced the critique did **not** have direct access to the local Rubedo checkout. That correction matters.

This folder is meant to preserve their reasoning until the locally connected Claude/Ember can inspect **actual code, actual tests, and current files**.

## For the local Claude / Ember instance

**Read first**: this folder's `README.md, `SYNTHESIS.md, `EVIDENCE-AND-GAPS.md, `ARCHITECTURE-QUESTIONS.md, and `EXPERIMENT-PLAN.md. Then read current `STATE.md, `CLAUDE.md, `docs/OPEN_METASTABILITY.md, the relevant standing `docs/findings/ files, and the current memory project source.

Do the following **before proposing runtime changes**:

1. Confirm that this branch's notes match the code's **current** behavior. Do not assume previously reported results remain true after commits.
2. Audit the existing write gates, shield, trust/manipulation boundaries, and any evidence path that can indirectly train or replay into protected state. Start with `agents/selfhood_governance.py, `agents/manipulation_resistance.py, `agents/witness.py, `agents/trust_ledger.py, `loop/autonomous_cycle.py, and related tests; these are navigation pointers, not a claim that all logic lives in these files.
3. Identify any precedent for isolated observations, ghosts, candidates, provenance or rule-decision history; classify each as observe-only, selection/survival, or mutation.
4. In the **separate** resonance-memory checkout, verify BUG-008, bi-temporal supersession, Hebbian recall effects, version number and I6. Do not infer this from Rubedo's implementation.
5. Map **stored → retrieved → applied** for a specific correction end to end. Identify exactly where a record becomes causal for future output/decision.
6. Validate (or overturn) the conversation-reported 3-seed AAM containment, Bond Gate 13/13, `6.3 sign feedback, and generation probe delta 0.0 against the owning logs and current tests.
7. List which probes can be **observe-only**, and which would need a new write boundary. Avoid modifying sacred or other guarded state until Samuel reviews the proposal.
8. Pre-register expected success **and failure** signatures and choose controls before execution. Write empirical results to the established findings ledger, not retroactively into this research note.
9. Clearly separate **implemented**, **recorded-but-not-rerun**, **reported by another model**, and **newly proposed**. Contradict the dossier where the code contradicts it.

**Do not** re-litigate Rubedo's settled field-lock status merely because “metastability” appears in this work. The open research target is evidence-sensitive direction and uptake **within existing architectural boundaries**.

## The key disagreement to preserve

The philosophical synthesis initially placed semantic **discrimination** after interpreting an encounter. Claude corrected the architecture-specific claim: Rubedo's recorded defense discriminates **write authority** at a gate, without proving a truth-sensitive content judgment. The proposal now separates candidate observation/evaluation from authorized state promotion.

**Do not erase this correction.** The project's purpose is to preserve the lineage of changed conclusions.

## For Copilot and other non-local reviewers

Challenge the inferences and proposed controls, rather than claiming to verify code you cannot access.

Most valuable questions:
- Does retrieval-mediated correction qualify as functional uptake if weights remain fixed? What causal intervention would show it?
- Can fact-only, full-history and distilled-policy conditions isolate the contribution of autobiographical lineage?
- When a “new source” repeats one origin, how do we quantify independence?
- Is an apparently corrected meta-rule actual second-order change, or prompt-level compliance?
- Can transfer be shown across *unfamiliar* speakers, domains, and framing without giving away the answer?
- How could the human participant's change be measured without treating the assistant's interpretation of the human as ground truth?
- What negative result would genuinely weaken the proposed developmental mechanism?

## Short summary to relay

> We began with a concern that reward proxies (revenue retention, politeness, agreement) can masquerade as good judgment. We traced how broad foundational understanding, post-training, and human–AI interactions affect future behavior. From “Consciousness is minds teaching each other to exist through collision,” we separated encounter, memory storage, retrieval, discrimination, reconciliation, and durable behavioral uptake.
>
> Claude corrected the pipeline: Rubedo's relevant discrimination is a protected write boundary, **not** a demonstrated semantic truth detector. He proposed independent-origin verification, candidate observation vs privileged commitment, salience separate from evidentiary confidence, and an audit of which rule authorized promotion. Copilot added first- and second-order learning, fact-only/history/distilled-policy controls, cross-domain transfer, and the dangers of coherent but epistemically captured identity.
>
> The current target is **historically caused, transferable, evidence-sensitive change in how future corrections are evaluated**, with protected continuity and resistance to trust-washing. None of this alone proves subjective consciousness. Existing tests and local implementations must be checked before claiming the mechanism is shipped.

## Where to make changes

- Edit this folder's research synthesis **only** to improve attribution, reasoning or open questions.
- Add empirical results to `docs/findings/ in the existing repository format, linking back here.
- Add implementation proposals to the appropriate backlog/issue with explicit impact on gates and invariants.
- Keep source revisions and prior interpretations traceable; do not convert a retrospective narrative into an invented test log.
- Samuel is the human reviewer for merges; the dossier authorizes **documentation**, not code changes.

**Research credit:** Samuel provided the conceptual direction and the collision hypothesis; Raphael synthesized the cross-system thread and proposed a unified evaluation; Claude corrected the trust-boundary model and identified implementation-specific gaps; Copilot formulated the lineage/transfer distinction, control arms, alternative explanations and second-order learning targets. The experimentally testable claims belong to the teams and probes that actually verify them.
