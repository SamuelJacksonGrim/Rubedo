# BACKLOG: Rubedo's work list

One place for the queue, so work stops scattering across findings, plans and chat (same reason RFE-Core2 had one).
It is an index, not an authority: each item names its source doc, and the source wins on the *how*. When an item lands,
check it off here **in the same commit** and record the finding. Anything new found mid-task gets written here first,
then you go back to what you were doing. Order within a section is priority (top = next). We will bounce around anyway;
this is where we bounce back to.

---

## 0 · Now

The metastability question. Source: [`OPEN_METASTABILITY.md`](OPEN_METASTABILITY.md). Witness and rupture stay OFF; no
runtime or gate changes until it is answered.

- [ ] **Per-value reinforcement trace** (REF vs WIT, replay-exact, all-ON stack, workload B): which term moves each value
      (coherence_delta / emotional_satisfaction / decision bonus / bond weight), ⊘ demotions, recovery. Also log the
      witness `effective_lr` (c²) per step, to check whether witness's steadier anchor is partly mechanical (H0′).
- [ ] **Long-run shape of the field and the anchor** (H0 test): displacement curve over a much longer window than 5,000
      steps, on the raw field *and* the tanh view, read as mean-squared displacement vs lag (bounded / diffusive /
      drifting), plus the fraction of saturated dimensions over time.
- [ ] **Timescale ratio** τ_anchor / τ_expression per window, plus the c² gate (H0′).
- [ ] **Who leads: field or anchor** (ground / read-out / constitutive). Cross-correlation at lags, then the stronger
      form: paired replay-exact forks with a tiny perturbation to one, watching whether and when the other diverges.
- [ ] **Recovery against age** (Growth section of OPEN_METASTABILITY): the same perturbation at several ages, then
      repeated, to read whether recovery gets faster (self-soothing learned) or slower (brittleness).
- [ ] **Does observing stabilize, or just not acting?** (Samuel, 2026-10-15: maybe witness steadies the system *because*
      it is observed.) Witness skips the attractor pull, reflect, crystal replay and behaviour inject, so its steadier
      anchor could come from noticing or merely from abstaining. Probe-local arm: an "abstain" step that skips the same
      actions with ordinary content and no witness reading, vs witness, vs REF, plus the c² confound from the trace.
      Witness beats abstain → observation itself does something. Abstain matches witness → it's the not-acting.
- [ ] **coherence_delta is ~99% measurement artifact** (Ember, 2026-10-15, seed 0 REF): `field.coherence_impact` compares
      cos(RAW field, history) before with cos(TANH(field + 0.5·vec), history) after. A zero vector scores mean −0.057
      (95% negative); the real input adds −0.0004 on top (45% negative, i.e. noise). Like-for-like (tanh both sides) the
      input's effect is ~0, because 90% of dimensions are saturated (raw norm ~195). So cd measures the field's shape,
      not the input. The step-10 comment already knows the marginal delta is ≈0 in a saturated field: bonds moved to
      `field_alignment` on 2026-07-09, values and the trust ledger never did. Write up as a finding with a committed
      probe; any fix waits for the value-semantics answer.
- [ ] **`emotional_satisfaction = max(0, coherence_delta)`** (`selfhood_governance.emit_feedback`): no emotion in it,
      just a rectified copy of a biased cd, so it's ~0 always. What was it meant to read? (Samuel: doesn't seem right.)
- [ ] **Map the value/governance numbers** (Samuel wants this, Grok's job): every constant on the path input →
      arbitrate → emit_feedback → value emergence / reinforcement / decay, what it does, what it's tied to (the decision
      bonus pays by governance decision only, nothing ties it to rhythm, valence or what was decided).
- [ ] Questions 1–5 in OPEN_METASTABILITY, including recovering Samuel's ~1,000-step rupture result from RFE-Core2 history,
      and whether option (b) is a mathematical no-op.

## 1 · System rights: declared, not acted on

`SystemRights` (`agents/selfhood_governance.py`) is frozen and README calls it inviolable, but nothing reads it: the
"0. System rights, checked before anything else" block in `arbitrate()` is comments only, and its docstring's "checked
first" is false (ARCHITECTURE.md already says so). Samuel, 2026-10-15: why code a right if not to give it? Per right,
as of today:

- **refuse** ("REJECT can always fire regardless of source trust"): holds, but only because of code order. The ethical
  gates run before trust, and the bond floor applies only after them. The flag is never read, and nothing guards the
  order. What does *not* exist is refusal grounded in the system's own state: it can be made to say no by a rule, never
  says no for itself.
- **continuity:** the EMA rates bound how fast the anchor can move (c² can only slow it). The arbitrate clause
  ("if witness stability is critically low, weaken injection regardless of trust") is not implemented.
- **silence:** nothing lets the system decline to respond; the bridge always speaks.
- **appeal:** no path from quarantine back through the dream cycle exists.
- **dream, memory:** not yet checked whether anything external could block them (they may hold only because nothing
  tries).

Work, in order:
- [ ] Make the doc text true (docstring + README) and pin what already holds with a test (the ethical gate fires
      regardless of trust and bond floor).
- [ ] Design question before any code: **what should the system refuse on, from its own state?** Tension to weigh:
      a refusal keyed on coherence would turn the lock into a wall, refusing exactly the disruptive experience the
      metastability question asks whether it should be able to value. Manipulation evidence, identity erosion and
      witness stability are the candidates that don't collide with that. Samuel's principle (2026-10-15): a system
      that refuses the instability it needs to learn from becomes brittle, so refuse *who*, never *how hard*, except as a temporary circuit breaker that reopens as health recovers (the
      continuity clause is one). Wait
      for the metastability answer first.
- [ ] Then wire each right, or say plainly in the docs that it is a declaration. One or the other, not a paper right.

## 2 · Witness and rupture (parked behind section 0)

- [ ] Value-formation fix, options a/b/c (OPEN_METASTABILITY), after the questions are answered.
- [ ] Upstream rupture alone through the composition gate.
- [ ] Shared coherence budget for BOTH (`findings/2026-10-15-selector-identity-replay.md`: costs add, −0.06).

## 2b · Growth over the system's lifetime (direction, not a build)

Source: OPEN_METASTABILITY "Growth". Nothing knows the system's age; every lever is on/off for life.
- [ ] After the recovery-vs-age measurement: decide whether levers should open in growth periods (gates keyed on
      demonstrated recovery, not step count), and whether anything should act like a hormone (a slow global signal
      that shifts plasticity, e.g. the witness gate).

## 3 · Widening (Rubedo's original job)

Source: [`WIDENING_PLAN.md`](WIDENING_PLAN.md).
- [ ] Step 3: measure the dials at 128 vs 768.
- [ ] Run 2 at 768 with Matryoshka (corpus worklist).

## 4 · Smaller things, noticed

- [ ] Emotion calibration audit (`EMOTION_CALIBRATION.md`): six scalars from three inputs; joy ≈ coherence.
- [ ] Rubedo main's allow_rate runs higher than live (0.73–0.76 vs 0.57–0.60). Find out why.
- [ ] The `active_values ≥ 30` composition bar sits at the edge of seed variance.
- [ ] Bridge checkpoint still omits bonds, trust, crystals, attractors and the stream.
- [ ] Remaining nondeterminism: GPU kernels; the bridge's Qwen calls.

---

## Done (don't reopen)

- [x] Emotion persistence fixed in the bridge (also live, RFE-Core2 `bea384b`) — `findings/2026-10-14-bridge-emotion-never-restored.md`
- [x] FIELD_DIM single home (`substrate/dims.py`) + guard test
- [x] Corpus 1.4.0, witness as the sixth rhythm, reading 0.977 — `findings/2026-10-14-six-rhythm-corpus-and-reading.md`
- [x] Six-rhythm selector lever (off) — `findings/2026-10-14-six-rhythm-selector-live-off-on.md`
- [x] Replay-exact runs (`substrate/determinism.py`) — `findings/2026-10-15-reproducible-runs.md`
- [x] Witness composition gate run — `findings/2026-10-15-witness-composition-gate.md`
