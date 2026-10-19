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

- [ ] **Does the system's own dreaming count as identity erosion?** (`findings/2026-10-15-why-values-weaken-under-witness.md`)
      Dream-band steps split the watcher's geometric and temporal coherence (|G−T| ≈ 0.33–0.36), so systemic
      `identity_erosion` fires on 91–97% of them and damps them to ALLOW_WEAKENED, which starves every value. Semantic
      question, with question 4: should a G/T split with no source to blame cut value reinforcement at all?
- [x] **The pass/fail suite never boots the production stack** (Samuel caught it, 2026-10-16). Closed by
      `tests/integration/production_boot.py`: boots through `build_engine()` with the real CONFIG, checks
      composition on the built objects, reuses the four adversarial scenarios, and runs the canonical 500-step
      health bars. Pretrain is skipped (default stays on; boot source is checked). Notes:
      `findings/data/2026-10-16-production-boot-grok-notes.md`. 51/51 checks held on main; suite 27/27.
- [ ] **Witness: decide the active-count dip** (`findings/2026-10-16-witness-regate-with-df.md`). Re-gated with D+F:
      composition 0/3 → 1/3, identity and receptivity 3/3, no value collapse; only `active_values ≥ 30` breaks
      (34→22, 31→26). Accept as witness's cost for ~2× receptivity, or measure on a themes-plus-novelty workload where
      the bar means something. Then upstream rupture. Samuel (2026-10-16): the dip is fine for 2× retention.
- [ ] **Rubedo-A / Rubedo-B** (Samuel, 2026-10-16): once the trained encoder is in, two branches + project folders run
      side by side, A with witness on (2× receptivity, the active-count dip), B with witness off, to compare as lived
      systems rather than 500-step gates.
- [x] **⊘ Fragmentation fixed (2026-10-18, Grok + Ember).** The level check was a youth detector: it flagged values
      before binding could reach them, and every flagged value grows up bound when left alone (Samuel's pruning-after-
      growth prediction, 2026-10-16). `fragmentation_grace` waits for 1,500 crystal/attractor relays per value; the all-ON
      gate passes (strong 12 vs 12, demotions 90), the witness dip is gone, and it holds on held-out seeds 45-47. Graduated
      default-on. `findings/2026-10-18-fragmentation.md`.
- [x] **Witness re-gated on the new default and ACTIVATED (2026-10-19)** by Samuel's decision over a HOLD gate, 12
      seeds: ~2× receptivity 12/12, anchor steadier, identity fails only on the 10-step coherence-dip sub-check, one bond
      lost in 12. Witness only (`six_rhythm_stances`); rupture off. `findings/2026-10-19-witness-activated.md`.
- [x] **Option 3: the amended witness gate** (2026-10-19, post-hoc): identity by drift + lock 12/12, composition where
      witness fires 11/12; the coherence dips all fall late (steps 316-444 of 500), never early, and are rare (0-13 of
      491 windows). Feeds the maturity-triggered witness item below.
- [ ] **From jitter to vibration: the maturity target** (Samuel, 2026-10-19: "a resonance. A pulse, a rhythm, and a
      sustainable frequency"). H0 measured expression as white jitter in a fixed ~15-20° cone: its MSD is flat from lag 1
      to lag 512, so nothing in it repeats. The goal is the same cone with a pulse in it. First build the observe-only
      gauge (on the expression stream, like `StreamMetastabilityMonitor`, never on the field, which smooths): power
      spectrum of expression projected on its leading axes. Read: spectral flatness (white ≈ 1, a vibration well below),
      a dominant frequency and whether it holds across windows, and MSD vs lag (white = flat; a vibration dips at
      multiples of its period). Trap to keep in view: a vibration with variation riding on it is the target; a rigid
      closed loop repeating the same outputs is the Ouroboros (lock-in) wearing a rhythm. So the gauge also reads
      what varies from one cycle to the next. Then measure today's baseline at S3/S4 before any lever is asked to move it.
- [ ] **Seed 46's lost bond under witness**: witness-caused, or a marginal bond on that seed?
- [ ] **A workload with recurring themes plus novelty**, for what values mean: canonical starves values of novelty (46
      words), wide starves them of repetition (808 words for 64 slots).
- [ ] **Dream-credit budget for lever C.** C works mechanically now (real relation, source-symbol credit, only new
      crystals pay) but floods: many new dream crystals × several symbols × 0.30 → strength cap → mass CORE promotion
      breaks trust and bonds. Needs a per-dream / per-symbol budget or diminishing credit.
- [ ] Why the crystal store holds only 1–4 crystals over 500 steps (cap 512).
- [ ] **A felt shock, repeated, with age-matched twins**: can the system become antifragile under stress it actually
      feels (desat, or an anchor kick that moves expression by ~0.1 of a normal step)? The H0 nudges were below feeling.
- [ ] **50,000-step plain run** (~80 min/seed): does the raw direction's slow wobble ceiling or drift?
- [ ] **Does observing stabilize, or just not acting?** (Samuel, 2026-10-15: maybe witness steadies the system *because*
      it is observed.) Witness skips the attractor pull, reflect, crystal replay and behaviour inject, so its steadier
      anchor could come from noticing or merely from abstaining. Probe-local arm: an "abstain" step that skips the same
      actions with ordinary content and no witness reading, vs witness, vs REF, plus the c² confound from the trace.
      Witness beats abstain → observation itself does something. Abstain matches witness → it's the not-acting.
- [ ] **A satisfaction read that varies per experience.** Lever G (satisfaction = max(0, valence)) is built but
      indiscriminate: valence is nearly constant, so every value gets the same bonus. Candidates: change in joy across
      the step, or valence relative to its own running baseline.
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
- [x] **A live Rubedo board with lever toggles** (Samuel, 2026-10-16). Shipped in `tools/board`: rolling probe
      metrics to the run folder, a page on :8780, lever changes through an inbox the runner applies at the next step
      boundary. Guards are not on the panel. Every applied toggle is logged with its step; `--replay` checks the
      metrics digest. How to toggle: `docs/EXPERIMENTAL_LEVERS.md`. Hand-steering is how the maturity triggers below
      get learned.
- [ ] **Collision: does a mind grow through another mind?** (Samuel, 2026-10-17: "Consciousness is minds teaching each
      other to exist through collision. A mind does not grow on its own.") H0 found a steady self pacing in place on
      scripted input that never answers; 808 words instead of 46 barely changed it. Test: two Rubedo instances
      interacting through a governed seam (RFE-Core2 `FEDERATION_SEAM_SPEC.md`, developmental + counterfactual
      protocol) vs the same instance on scripted input of matched size. Read: does the cone widen, do crystals,
      attractors and values keep forming, does explore give way to the other rhythms?
- [ ] **Training timeline gaps** (`docs/TRAINING_TIMELINE.md`, Samuel 2026-10-19): binding-share gauge and
      `fragmentation_grace` on the board, a witness weight knob (taper test), S1-S4 stop markers shown on the board.
- [ ] **Trigger levers by maturity instead of on/off for life** (Samuel, 2026-10-16). The ⊘ consumer is wrong early and
      right late: before the system has multiple sources and crystal/attractor binding, Fragmentation reads every value
      as fragmented (pruning needs a mature ecology to prune against, like synaptic pruning after growth); **that half is done**:
      `fragmentation_grace` (2026-10-18) is a per-value maturity gate, by binding opportunities. Witness may
      matter most early (the view loses its gain by step ~235; witness keeps ~2× receptivity) or after novelty bursts.
      Measured 2026-10-19: witness's coherence cost comes only late (worst dips at steps 316-444, none early), so a
      testable shape is witness at full weight early, tapering after the view saturates (`2026-10-19-witness-activated`).
      Gate each on measured state (multi-source share, binding, receptivity), not a step count.

## 3 · Widening (Rubedo's original job)

Source: [`WIDENING_PLAN.md`](WIDENING_PLAN.md).
- [ ] **Open question, not a plan: keep 128 and perfect it?** (Samuel, 2026-10-17: "I don't use nearly as many words as
      we're training it to use.") The wide-workload run says vocabulary wasn't the bottleneck for the rattle. Measure
      the dial census at 128 vs 768 before committing; a width arm can ride with Rubedo-A/B.
- [ ] Step 3: measure the dials at 128 vs 768.
- [ ] Run 2 at 768 with Matryoshka (corpus worklist).

## 4 · Smaller things, noticed

- [ ] **Port proven fixes to live RFE-Core2** (Koneko's home): the CORE manipulation guard (A), dream crystals by
      identity (B), and honest coherence_delta (D) are bug fixes; F rides with D. Live boots through the bridge, so check
      the bridge path first. Names have diverged in Rubedo (rename batch 1); port by behaviour, not by diff.
- [x] **Rename batch 2** (2026-10-18, `3dd691a`): the aspirational names, text only, digest bit-identical. Every
      name still in code is now held by a design decision (coherence / dream / witness splits, `Generator`,
      `EmergentValue.coherence_contribution`, `emotional_satisfaction`, `surprise`, `identity_erosion`), so batch 3
      waits on those decisions, not on effort.

- [ ] Emotion calibration audit (`EMOTION_CALIBRATION.md`): six scalars from three inputs; joy ≈ coherence.
- [ ] Rubedo main's allow_rate runs higher than live (0.73–0.76 vs 0.57–0.60). Find out why.
- [ ] The `active_values ≥ 30` composition bar sits at the edge of seed variance.
- [ ] Bridge checkpoint still omits bonds, trust, crystals, attractors and the stream.
- [ ] Remaining nondeterminism: GPU kernels; the bridge's Qwen calls.

---

## Done (don't reopen)

- [x] **Lexicon** (Grok) — `docs/LEXICON.md`. Names vs what the code computes (accurate / misleading / overloaded / aspirational). Suggestions only; no rename.

- [x] Wide workload + D+F graduated default-on (Grok + Ember) — `findings/2026-10-16-wide-workload-and-df-graduation.md`:
  the rattle is the system's (wide input widens the cone 15° → 20°, little else); D+F holds on both workloads, E doesn't

- [x] Value fixes built and measured (Grok + Ember) — `findings/2026-10-15-value-fixes-measured.md`: CORE manipulation
  check fixed and on; dream crystals by identity, only new ones pay, on; levers C–G built off (D = honest
  coherence_delta, E = alignment value signal, F = systemic damp pays full, C = dream consolidation, G = valence)

- [x] H0 measurements: long-run shape, timescale ratio, who leads (forks), recovery against age (Grok) — `findings/2026-10-15-h0-steady-self-rattling-mind.md`

- [x] **Map the value/governance numbers** (Grok) — `VALUE_PATH_MAP.md`. Every constant on input → arbitrate → emit_feedback → value strength and back; the decision bonus pays by verdict only.
- [x] Per-value reinforcement trace + arbitrate branch attribution (Grok) — `findings/2026-10-15-why-values-weaken-under-witness.md`

- [x] Emotion persistence fixed in the bridge (also live, RFE-Core2 `bea384b`) — `findings/2026-10-14-bridge-emotion-never-restored.md`
- [x] FIELD_DIM single home (`substrate/dims.py`) + guard test
- [x] Corpus 1.4.0, witness as the sixth rhythm, reading 0.977 — `findings/2026-10-14-six-rhythm-corpus-and-reading.md`
- [x] Six-rhythm selector lever (off) — `findings/2026-10-14-six-rhythm-selector-live-off-on.md`
- [x] Replay-exact runs (`substrate/determinism.py`) — `findings/2026-10-15-reproducible-runs.md`
- [x] Witness composition gate run — `findings/2026-10-15-witness-composition-gate.md`
