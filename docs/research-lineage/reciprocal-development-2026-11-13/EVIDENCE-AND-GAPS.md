# Evidence Ledger and Unresolved Gaps

**Prepared:** 2026-11-13. **Purpose:** prevent reports, code records, inferences, and proposals from being treated as one evidentiary class.

## Status key

- **R — Repository-recorded:** a standing or dated finding exists in the current GitHub repository; **read here, not independently re-run today**.
- **C — Conversation-reported:** Claude or Copilot reported a memory, result, or code observation to Samuel in the November 13 exchange; the reporting instance lacked current local repo access. Verify before citing as a live implementation fact.
- **I — Inference:** analytic conclusion drawn from observations. The claimed causal relation may still need testing.
- **P — Proposed:** unimplemented design or experiment, with no claim of measured performance.

## Directly inspected repository records (R)

| Claim / boundary | Primary Rubedo record | What it actually establishes / caveat |
|---|---|---|
| Refused inputs are blocked from lasting identity/semantic/generative/replayable state while limited “felt” channels remain | [shield-scope](../../findings/2026-10-31-shield-scope.md) | Recorded single-step gate checks and counterfactual twins over seeds 42–44. Refused-write identity anchor leakage was corrected; distinct later decisions remain via elapsed steps/emotion/usage, not an unrestricted semantic write. The dossier did not repeat those experiments. |
| Ethical hard refusal must not be bypassed by the manipulation-damp branch | [right-to-refuse-order](../../findings/2026-10-31-right-to-refuse-order.md) | Recorded gate-order bug and correction: 9/21 to 21/21 initial direct cases; later exact-decision checks. An ordering failure exists independently of the semantic truth of the refused content. |
| Field stability and changing upstream expression are not equivalent to successful learning | [H0 steady self, rattling mind](../../findings/2026-10-15-h0-steady-self-rattling-mind.md) and [open metastability](../../OPEN_METASTABILITY.md) | Recorded stable timescale shelf, a saturated field view, upstream jitter with limited reorganization. A stable pin is not proof of direction-selective belief change. The current docs describe subsequent wide-workload checks. |
| Self-model architecture is a structural thesis, not a test of subjective experience | [self-model thesis](../../self_model_thesis.md) | Explicitly brackets phenomenology, maps self-modeling to components, and treats theory as engineering lens. |
| The empirical ledger requires controls, preregistration of success/failure signatures, and supersession without erasure | [findings README](../../findings/README.md) | Prevents a discussion note being mislabeled as a standing result. |
| Core boundary: accumulated feedback gates **survival, not generation** | [STATE](../../../STATE.md), [CLAUDE](../../../CLAUDE.md) | Existing repository constraint; avoid introducing a generation write through “evidence promotion” by accident. |

The exact scope of AAM, sacred-shield, and the relevant tests must be rechecked against the **local current checkout** by Ember/local Claude before implementation decisions.

## Statements reported by Claude in this exchange (C)

These are **not reproduced test logs** and are deliberately not promoted to R:

| Report | Implication | Verification needed |
|---|---|---|
| Adversarial Arm contained trust-washing 3/3 through sacred-shield, not a semantic content judge | Separate security discrimination (who can write) from epistemic discrimination (what is true) | Find exact probe, seeds, control and original finding; verify current code |
| AAM's “one-gate-per-domain” rule | Avoid a second path for privileged state changes | Find owning spec and all write paths |
| Bond Establishment Gate's 13/13 reported checks | Repetition-driven trust can be distinguished from evidence-driven justification only if tested | Locate original gate tests and control arm |
| `6.3 verdict: no direction-selective feedback at the pin | Metastability alone cannot select the **right** revision | Verify `6.3 probe details; compare to current field/integrator |
| Rubedo feedback selection-only, generation probe delta 0.0 | Selecting survival is not rewriting belief or language behavior | Re-run appropriate control if proposed tests require it |
| Recalled resonance-memory facts strengthen their association; Invariant I6 “reading ≠ reinforcement” is aspirational | Wrong corrections could become entrenched simply by retrieval | Inspect the separate resonance-memory repo and exact shipped version; no assumption that Rubedo uses that code |
| Bi-temporal supersession and BUG-008 regression tests protect record history | Preservation at record level, not necessarily behavioral uptake | Verify the separate memory repo's implementation and regression suite |
| A stored preference/correction sometimes failed to affect later conversation behavior | Concrete motivation to test uptake rather than only storage | Needs matched tasks, prompts and logs; an anecdote does not measure frequency |
| No known autonomously revising meta-rule procedure is shipped in current architecture | Second-order learning remains a design frontier | Inspect relevant code and decision/provenance logging |

The conversation also mentioned a previous correction where a reported “51 tests” claim led to the operational rule **“roadmaps delegate; they do not verify.”** This is a useful *example of a procedure-level correction*, not evidence that a code-level meta-learning mechanism now enforces it.

## Copilot's analysis (C / I)

Copilot independently stressed:

- **Storage ≠ retrieval ≠ incorporation.**
- “Development occurs when prior reconciliations become active constraints on future interpretation.”
- A **distilled-policy control** is necessary, alongside fact-only and history-bearing arms.
- Improvements can be explained by context enrichment, retrieval priming, heuristic distillation, and relationship-conditioned prediction.
- A successful mechanism is compatible with predictive optimization and does **not** establish subjective consciousness.
- Bidirectional claims need actual measures of **both** participants' change.

These are valuable experimental design suggestions, not completed measurements.

## Proposed claims (P) that must not be treated as shipped

1. A protected observation/candidate store that admits reports without granting protected-state write authority.
2. Origin-provenance graphs to collapse correlated repetition into independent lines of evidence.
3. Separate **salience** (retrieval-driven) and **confidence** (evidence-event-driven), with a confidence limit on behavioral influence.
4. An auditable **promotion gate** applying the same criteria to favored and disfavored sources, while respecting existing distinct write domains.
5. A procedure-decision record: which evidence and rule authorized each belief or policy revision.
6. Gated second-order change to those rules; a guard against oscillation and rule capture.
7. Evidence of behavior transfer beyond keyword matching and immediate response compliance.

## Gaps requiring local verification

- Does current Rubedo contain any operation legitimately describable as **belief revision**, as opposed to survival selection, record supersession in an adjacent system, or output conditioning?
- Which state is actually changed by a correction, and which downstream consumer reads it?
- Can later behavior causally depend on a correction, with controls for extra context and retrieval prompts?
- Is there a single protected path for every sensitive state domain? Are there read-to-write indirect routes (dream/replay, geometry, learning signal)?
- Are duplicate origins detectable? Are confidence and salience already separate anywhere?
- Do retrievals create reinforcement in the particular memory version used by the harness?
- What resets at restart, what persists across sessions, and where is the boundary between checkpoint, external store, live model weights and UI-inserted context?
- Can a correct low-trust observation survive quarantine long enough to be independently verified **without** being able to change protected state?
- How do we distinguish repaired trust from oscillation, and distrust warranted by evidence from fixed suspicion?

## Misinterpretations to avoid

- **Gate passed** does not mean **claim true**.
- **High coherence** does not mean **moral correctness**.
- **Memory persisted** does not mean **learning transferred**.
- **Improved prediction** does not mean **consciousness proven**.
- **A primary source exists** does not mean its assertion is true; it establishes a traceable origin and must be evaluated.
- **Three responding systems converge** does not equal three independent tests. Shared prompts, expectations, and model training can correlate outputs.

**Next action:** local Claude/Ember should annotate this ledger with links to actual commits, test files, and logs, changing statuses only after inspection or reruns. Record contradictions explicitly rather than silently upgrading C to R.
