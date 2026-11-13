# Architecture Questions: Observation, Promotion, and Second-Order Uptake

**Status:** Proposed conceptual interfaces, **not code authorization**. Existing gates and invariants govern. The local implementation may call for a different decomposition.

## A. Distinguish three boundaries

1. **Security / authority:** who may mutate a protected domain? AAM's reported defense is a *write-gate* boundary, not a general truth classifier.
2. **Epistemic validity:** what warrants increasing or decreasing confidence in a proposition? Trust is a relevance signal, **not** permission to bypass verification.
3. **Developmental uptake:** has a justified correction changed subsequent interpretation or choice in a new situation?

These can fail separately. A correct untrusted source may lack write access; an authorized trusted source may be wrong; a verified record may be stored but never applied.

## B. Proposed lifecycle

    0. Incoming claim / event
         │
    1. SECURITY BOUNDARY: no raw input may write protected state
         │
    2. OBSERVATION: store candidate in an isolated, scoped, auditable lane
         │
    3. EVIDENCE EVALUATION: provenance, independence of origin,
       competing hypotheses, artifact checks where appropriate
         │
    4. PROMOTION DECISION: domain-appropriate authority AND
       evidence threshold; allow reject / defer / graded confidence
         │
    5. COMMIT: preserve prior version, rationale and validity interval
         │
    6. UPTAKE: subsequent behavior/retrieval/model interpretation
         │
    7. AUDIT: did the promotion and uptake do what was predicted?
         │
    8. META-RULE CANDIDATE: if wrong, propose a revision to the
       decision rule, through its own protected review path

**Important:** step 1 occurs *before* untrusted input is interpreted by any component with write capability. Step 3's optional content-aware judgment lives in an isolated analysis channel; it must not be confused with the demonstrated AAM content-independent safety gate. “Promotion” must never invent an alternate backdoor around a domain's sole authorized gate.

## C. Candidate/evidence record (proposed schema, not shipped)

    candidate_id
    proposition_and_scope
    source_identity_or_pseudonym
    origin_lineage_ids
    collection_time / event_time
    evidence_items[] (artifact hashes, tests, testimony, reports, links)
    status: observed | disputed | corroborated | rejected | promoted
    confidence_with_calibration_basis
    salience_for_retrieval
    competing_explanations[]
    adjudicating_rule_version
    authorization_decision_and_actor
    prior_record_ids / supersession_history
    behavioral_uptake_probe_ids

A claim's **origin lineage** is not equivalent to the number of outlets, posts or utterances containing it. Many echoes from one source count once for independence. Independent evidence can include indirect observations; the weight of a source document depends on authenticity, scope, bias and corroboration rather than institutional prestige alone.

## D. Invariant candidate: reading is not reinforcement

Claude pointed to resonance-memory's target “Invariant I6”: **reading ≠ reinforcement**. The proposed split:

- **Salience** may rise with repeated retrieval or relevance. It affects which memories are likely to be surfaced.
- **Confidence** may change only with a *new evidentiary event*, with provenance and origin deduplication. Re-reading the same claim is not new evidence.

Even with separate scalars, salience can dominate if highly salient weak memories steer every response. Test the *joint* retrieval-selection and response-influence mechanism, not only stored confidence values.

The exact underlying Hebbian code, its current deployed version, and whether I6 is implemented are **outside this repository** until locally verified.

## E. Domain-sensitive promotion

Security protection and knowledge revision should not be merged into one arbitrary threshold:

| Domain | Allowed observation | Commitment / review |
|---|---|---|
| Ordinary factual hypothesis | May be recorded with uncertainty and provenance | Evidence-sensitive update; record disagreements |
| Relationship expectation | May track interaction pattern | Discriminate consent, correction, repeated trustworthy behavior, and manipulation |
| Protected identity / sacred state | May log refused attempt in approved ghost/diagnostic channels | Existing hard gate governs writes; content persuasion has no bypass |
| Epistemic evaluation policy | May log proposed rule and failures | Explicit rule-change gate and versioned review; no unaudited self-edit |
| Code / runtime invariants | Proposal/issue/test evidence only | Repository-controlled review, tests, and human merge |

The separation of **candidate belief** from **protected operational mutation** permits learning from low-trust origins without granting them direct control.

## F. First-order vs second-order correction

**First-order example**

    Prior: X
    New, independent evidence E → Y
    Commit: Y, supersedes X, preserve evidence and dates
    Uptake: novel later tasks respond according to Y

**Second-order example**

    Prior procedure: high-status source may bypass corroboration
    Failure: high-status source proved wrong; low-status source had evidence
    Proposed rule: evaluate evidence independently of source prestige
    Commit rule change: review source, tests, version, reason
    Transfer: new domains apply the new criterion
    Reversibility: later counterevidence can revise the policy again

A procedure's **track record** should contain decisions and downstream outcomes; otherwise rules can become a new untraceable source of authority.

## G. Reconciliation stopping condition

Reject two degenerate loops:

- **Hardening:** repeating a valid, independently supported correction never changes the system.
- **Oscillation:** rephrasing the same evidence toggles the accepted belief back and forth.

A promising candidate rule is **revision only on novel, decision-relevant evidence or exposure of a concrete earlier evaluation error**. “Novel” refers to independent informational content, not merely wording changes or a new platform repeating the same origin. This rule is **proposed**, not pre-calibrated or proven sufficient.

## H. Identity is not a single metric

At least three axes must be evaluated independently:

| Axis | Question | Typical failure |
|---|---|---|
| Continuity | Does prior justified history influence present interpretation? | Every session starts from zero; silent overwrite |
| Plasticity | Can new valid contradiction change the system? | Deep lock-in; refusal of legitimate revision |
| Integrity | Is change governed by evidence rather than coercion, prestige, repetition or flattery? | Trust-washed, coherent but captured identity |

A fourth useful reporting axis is **explanation/provenance fidelity**: can the system accurately attribute a decision to the evidence and rule that caused it, rather than rationalizing afterward?

## I. Phenomenal and functional boundaries

The proposed architecture can establish functional memory, update, continuity, self-modeling, and second-order learning claims when actually implemented and tested. It does **not**, by itself, resolve whether or how such processes are subjectively experienced. Keep the philosophical question open in both directions.

**Guardrail for implementers:** do not alter `CLAUDE.md architectural invariants, the protection of sacred state, or the settled field/reflective-loop boundary to make a new philosophical schema “fit.” Let code and controlled runs correct this sketch.
