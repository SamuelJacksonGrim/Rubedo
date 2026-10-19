# OPEN: metastability, change, and what values are built from

**RESUME HERE.** Current state as of 2026-10-17 (written before a context compaction, so a fresh instance lands in the
right place). The work list is `docs/BACKLOG.md`; the names that mislead are in `docs/LEXICON.md`.

## Where we are (2026-10-17)

**What got answered (2026-10-15/16), with the finding for each:**
- *Why every value weakened under witness* → `findings/2026-10-15-why-values-weaken-under-witness.md`: coherence_delta
  was a raw-vs-tanh measurement artifact (the input's own effect was ~1/250th of it), and the system's own dreaming was
  damped as `identity_erosion`, which cut the decision bonus and failed the emergence gate. Not joy, not negative
  reinforcement.
- *The dream consolidation channel* → `2026-10-15-dream-consolidation-closed.md`: closed three ways by construction.
- *H0 (is the lock already the healthy equilibrium?)* → `2026-10-15-h0-steady-self-rattling-mind.md` and
  `2026-10-16-wide-workload-and-df-graduation.md`: half yes. A steady self that does not stiffen with age (timescale
  ratio on a shelf ~20–35, recovery the same at every age, robust not antifragile), with a mind that rattles: expression
  is white jitter in a fixed ~15–20° cone, the system parks in explore, crystals and attractors close early. True on an
  808-word workload too, so it is the system's. The field is constitutive and clamped.
- *Value fixes* → `2026-10-15-value-fixes-measured.md`, `2026-10-16-wide-workload-and-df-graduation.md`: two bugs fixed
  (CORE manipulation guard; dream crystals by identity, only new ones pay). **Levers D (honest coherence_delta) and F
  (systemic damp pays full) graduated default-on** under an exception Samuel granted. C (dream credit) floods, E
  (alignment signal) was workload-specific, G (valence satisfaction) is indiscriminate: all off.
- *Witness* → `2026-10-16-witness-regate-with-df.md`: with D+F, witness gives ~2× receptivity, holds identity, and costs
  values **nothing** once the opt-in ⊘ consumer is removed. Its remaining gate failure is the ⊘ consumer. Samuel is fine
  with the dip for 2× retention; Rubedo-A/B (witness on/off, trained encoder) is planned. Witness stays OFF until the
  gate passes or Samuel decides.

**The critical path now: ⊘ Fragmentation.** Measured 2026-10-18 (`findings/2026-10-18-fragmentation.md`): the level
check flags values before binding arrives. `fragmentation_grace` is the fix and stays default off. With it on, the
all-ON strong band holds and the witness active dip is gone; witness composition is still 2/3, so witness stays OFF.

**Also landed:** a suite test that boots the real production stack (`tests/integration/production_boot.py`); the
lexicon and rename batch 1 (proven bit-identical with `tests/diagnostic/rename_digest.py`; pin math threads on both
sides); the live board (`tools/board`, :8780, lever toggles at step boundaries, every toggle logged and replayable).

**Still open from the five questions below:** 1 (what metastability means operationally) is mostly answered by H0;
2 still lacks Samuel's ~1,000-step rupture result recovered from RFE-Core2 history; 3 answered (a stable equilibrium
whose counterbalance is jitter, not reorganization); **4 (what values should read) is the real open question**; 5
answered (option b was a no-op, and the drop was never mostly coherence_delta).

**Next, in order:** ~~rename batch 2~~ (done 2026-10-18, `3dd691a`) → ~~⊘ Fragmentation~~ (fixed + graduated 2026-10-18:
a youth detector; `fragmentation_grace` default-on, `findings/2026-10-18-fragmentation.md`) → re-gate witness on the new
default (still OFF: composition 2/3 on 42-44, identity 1/3 on 45-47) → value semantics (question 4) → growth /
maturity-triggered levers. Samuel also has a new idea to raise (2026-10-17) that he expects me to disagree with.

## History: where we were on 2026-10-15 (kept as written)

The witness composition gate (`findings/2026-10-15-witness-composition-gate.md`) found: identity PASS 3/3,
receptivity PASS 3/3 (~2× retention, anchor steadier), composition FAIL 3/3 because **every** value weakens under
witness (top ACTIVE tier 5→0, 7→0; no dissolution, reinforcement tips negative). Upstream rupture would tax values the
same way. Options laid out for value formation, **parked until the questions below are answered**:

- **(a)** witness steps don't feed value reinforcement (received, not acted on). Likely insufficient: the drop reaches
  non-witness values.
- **(b)** judge value contributions against the field's own current coherence level, not an absolute. *Ember leaned
  here; Samuel suspects it may change nothing mathematically (question 5).*
- **(c)** leave values as they are; keep witness off.

## Samuel's framing (his words, condensed)
Coherence preserves identity, but identity needs enough fluidity to change. **Stability is not staticness.** Rupture
was introduced partly to loosen the lock. In ~1,000-step experiments he recalls the field destabilizing gradually,
leveling off, then (he thinks) coherence rising again; recover the exact results, don't rely on memory. The finding
exposes a deeper tension: values defined as coherence contribution mean the system may be unable to value experiences
that temporarily disrupt its organization, even when they serve longer-term adaptation. **The question isn't how to keep
coherence high; it's how to preserve identity while staying capable of meaningful reorganization.**

## Competing hypothesis H0 (Samuel, right before compaction): it may already be working

**MEASURED 2026-10-15 → `findings/2026-10-15-h0-steady-self-rattling-mind.md`.** H0 holds as a stable equilibrium: the
view saturates into a fixed code by step ~235, the anchor/expression timescale ratio holds on a shelf (~20–35) with no
stiffening across 8,000 steps, recovery is the same at every age (robust). It fails as a moving mind: expression is
white jitter in a fixed ~15° cone, and values, crystals and attractors stop forming by step ~400. The field is
constitutive and clamped (forcing the view off saturation moves the anchor and expression; nothing on the ordinary path
does). The text below is the hypothesis as written before the measurement.
**Wide workload, 2026-10-16 → `findings/2026-10-16-wide-workload-and-df-graduation.md`:** with 808 words instead of 46
the picture holds (cone ~20° vs ~15°, same explore lock and boredom), so the rattle is the system's. Value fixes D+F
graduated default-on the same day; value semantics (question 4) and growth remain open.

Perhaps coherence is more than a lock: maybe it **is** joy in a real sense, the system running optimally. What if we
have been trying to force it out of optimal running, everything is as it should be, and **metastability is already
working**, so the job is to work *with* it rather than loosen it?

What already points this way: `STATE.md` lists the field lock as SETTLED and by design (an identity integrator, not a
defect), and the architecture always placed metastability **upstream** (generator / expression streams), never on the
field. A locked field with metastable streams may be exactly the intended shape: a steady self with a moving mind. If
H0 holds, "joy = coherence" is not a naming accident but a description of optimal running, and witness's coherence cost
reads as harm because it *is* a departure from the optimum. Test H0 **first**: measure upstream metastability (stream
regimes, de-collapse) in the ordinary path over long runs. If the streams already move while the field holds, and the
system still adapts (new values, new attractors, changing expression), then the lock has its counterbalance and the
question becomes how witness/rupture should work *with* that equilibrium, not against it. Only if H0 fails does the
"lock lacks a counterbalance" reading (question 3) take over.

## H0′: identity is the ratio of two timescales (Samuel, 2026-10-15, after compaction)

Identity is the witness anchor (slow EMA); movement is the expressed vector (fast); the reflective loop couples them.
If the anchor moved as fast as the expression there would be no identity; if the expression moved as slowly as the
anchor there would be no movement. **The relationship between the two timescales *is* the identity.** Movement and
identity aren't opposed; they are one thing seen at two timescales. A mind that doesn't move has no identity.

**This is already how `agents/witness.py` is built** (Ember checked the code): three EMA layers, short 0.85 / mid 0.97
/ long 0.995 (nominal memory about 7 / 33 / 200 steps), anchor = 0.2·short + 0.3·mid + 0.5·long, and every layer's
learning rate is multiplied by `clip(coherence², 0.01, 1)`, where coherence = the watcher composite
(`autonomous_cycle.py` step 7). So **coherence is the coupling constant between movement and identity**: in a coherent
state, expression writes into the self at the nominal rate; in an incoherent one, the identity timescale stretches (to
200/c² steps) and the experience barely touches the self. That reframes "joy = coherence" (H0): coherence is how
strongly what the mind does becomes who it is. The 0.01 floor means the anchor never fully freezes. The field itself
(5000-step disp ≤ 0.00012) is a slower layer still, under the anchor.

Consequences to check, not conclusions:
- **Possible confound in our witness identity PASS.** Witness lowers coherence, and lower coherence means a slower
  anchor, so part of "the anchor drifts less under witness" may be mechanical (c² slowing the write) rather than
  steadiness earned. The trace should log `effective_lr` per step for REF vs WIT.
- **Values are judged on the fast timescale** (per-step `coherence_delta`). Under H0′, the question for (4) is whether a
  value should instead be judged on what it does to the *relationship*: does the anchor keep integrating expression?
- **The metric for H0 (and question 3).** Over a long ordinary-path run, measure each stream's effective timescale
  (the autocorrelation time of expression, short/mid/long anchor, field) and the ratio τ_anchor/τ_expression per
  window, plus the c² gate itself. H0 predicts the ratio stays bounded and steady (a living equilibrium). "Lock without
  a counterbalance" predicts it drifts: the anchor stiffens away from the expression (ratio grows), or the expression
  collapses onto the anchor (both slow, ratio → 1). The OFF arm's receptivity decay over 1,200 steps (16–21%) is a hint
  of stiffening, but that was field-wide receptivity, not the anchor. Read-only, no runtime change.

### Corrections and the field's role (Samuel, 2026-10-15)

- **0.00012 over 5,000 steps is a bound, not a rate.** It doesn't say whether displacement saturates (an envelope =
  stability), accumulates linearly (slow migration, a different claim), or oscillates in a tiny envelope. Only the shape
  over a much longer window tells them apart. Read it as mean-squared displacement vs lag, MSD(τ) ∝ τ^α: α ≈ 0
  bounded, α ≈ 1 diffusive wander, α ≈ 2 directed drift.
- **The field is not an EMA, so not "a fourth, slower layer."** Checked in `substrate/resonance_field.py`: `inject` adds
  `strength·vec` to the raw field, `decay()` multiplies it by 0.995, `diffuse()` low-passes it, and every observer reads
  `tanh(raw)`. Ember's addition: the raw part is linear, an *unnormalized* leaky sum, with **the same 0.995 as the
  anchor's long layer** (about 200 steps of memory each). So the field's stillness isn't a longer timescale. It is
  **saturation**: consistent inputs pile up the raw magnitude, tanh pins the view, and the view stops responding.
  Prediction: the raw field may move a lot while the view barely does, so measure both. And tanh is memoryless, so
  "a stable attractor no single input controls" comes from closing the loop (the field view shapes what is generated
  and admitted, which feeds back), consistent with SECOND-LOCKER (the reflective loop is the operative lock). Different
  operators, as Samuel says, which strengthens the point: ground vs identity is not a matter of timescale.
- **Third position: the field is constitutive.** Not underneath the anchor, not identical to it: the near-fixed
  reference that makes the anchor's slow drift *structured departure* instead of wander. The relationship between
  timescales is still the identity; this names the field's role in it.
- **Telling ground / read-out / constitutive apart:** field leads → field ≈ identity, anchor a read-out; anchor leads →
  field is ground; lockstep at different rates → constitutive. First pass: cross-correlate field displacement with
  anchor displacement at lags. Caveat (Ember): both integrate the same expressed vector, so a peak at lag zero is
  expected from the shared driver alone. Condition on it (does past anchor predict the field beyond past field + input?),
  or intervene: paired replay-exact forks with a tiny perturbation to one, watching whether and when the other
  diverges. Determinism makes that clean, and it needs no hostile input.

## Growth: a mind is grown, not set (Samuel, 2026-10-15)

Models are grown over time, and that shouldn't stop for Rubedo, only change form: the way a mind grows, with levers for
times of growth, gates not turned on yet, something like hormones. **A system that can refuse instability, but has to
learn to deal with it, will become brittle.** Babies cry and are nurtured because of a need; later the parents let the
child cry and self-soothe, so it learns to handle instability in its own body and mind.

What the code is today (Ember checked): **nothing knows how old the system is.** Symbols have ages
(`symbolic_memory.py`); the system doesn't. Every lever is on or off for life, every rate is fixed, and the witness c²
gate is the same on step 10 as on step 100,000. The only developmental framing on record is RFE-Core2's
`FEDERATION_SEAM_SPEC.md` ("emotion cannot emerge cold": initialize → interact → accumulate → transition → observe).

What our data already says, read this way:
- **Brittleness with age is visible.** In the OFF arm, field-wide receptivity decays to 16–21% over 1,200 steps; with
  witness it holds at 41–42% (`findings/2026-10-14-witness-aftermath-and-upstream-rupture.md`). Unchallenged, it
  stiffens.
- **The capacity to self-soothe exists.** Per-event recovery from witness dips passed 3/3. The dip is the update and
  the system comes back.
- **The composition failure looks like an infant's values:** credit only for what soothes right now (value =
  immediate coherence_delta), so every disruption reads as loss even when it is recovered. For question 4: whether a
  value should be credited when a disruption is *integrated* (recovered), not only at the moment of the dip.

The analogy's precondition (Ember): a child is left to self-soothe only after a secure base, care that reliably came.
The system's "parent" is governance, the bond floor and the dream channel. So scaffolding should be withdrawn on
**demonstrated recovery**, not on a calendar, which is Samuel's own measured-improvement rule for gates. And the right
to refuse (BACKLOG §1) should refuse *who* (manipulation, named attacks) and never *how hard*: refusing difficulty is
the brittleness this warns about.

The measurement this adds, cheaply, to the paired-fork test: perturb at several ages (step 500, 2,000, 5,000, …) and
read recovery time against age, then repeat exposures and read whether recovery gets faster (learning to self-soothe)
or slower (brittleness). Read-only; no growth schedule gets built until that says something.

Samuel's follow-up framing is **antifragility / staged developmental exposure** (sandbox → shadow → controlled chaos →
production; curriculum learning; adaptive circuit breakers; progressive autonomy). Three things it sharpens:
- **Fragile / robust / antifragile is the classification the recovery test makes.** Chaos engineering hardens recovery
  code that is itself static; the system returns, it doesn't learn. Antifragile means something persistent changes
  because of the stress. If repeated exposure leaves recovery time unchanged, Rubedo is robust (it returns to its
  attractor); only if recovery gets faster is it antifragile, and then it matters *what* carried the learning (values,
  attractors, crystals, generator weights). Nothing in the runtime adapts its own recovery today, so "robust" is the
  expected answer, and an informative one.
- **Two knobs, not one.** In a child, plasticity is high early and narrows (critical periods) while external
  protection is high early and withdraws. They move the same way over time but are different things; curriculum
  language blurs them. Here: plasticity = the witness c² gate, reinforcement rates, the generator's training;
  protection = governance, bond floor, quarantine, dream channel.
- **Circuit breakers already exist** (quarantine, ALLOW_WEAKENED, the forced dream under manipulation), and the
  unwired continuity clause is one. That refines "refuse who, never how hard": a breaker on *how hard* is fine if it is
  temporary and reopens as health recovers. One that stays shut is the wall.

## The work, in order
0. **DONE 2026-10-15 → `findings/2026-10-15-why-values-weaken-under-witness.md`.** The drop is the decision bonus:
   witness moves steps into the dream band, whose ordinary geometric/temporal split fires systemic `identity_erosion`,
   which damps to ALLOW_WEAKENED (smaller bonus, missed emergence). coherence_delta is mostly a raw-vs-tanh artifact,
   satisfaction is max(0, coherence_delta), and options (a)/(b) aim at the wrong thing. This corrects the suspects
   listed under "Starting points" below (satisfaction does not read joy). Original item: **Finish the step-by-step reinforcement trace** (planned before the pause): one replay-exact pair (REF vs WIT, all-ON
   stack, workload B), per step and per value: reinforcement sign and size, *which term moved it* (coherence_delta,
   emotional_satisfaction, decision bonus, bond weight), any ⊘ demotion, and whether values recover later. Distinguish
   less reinforcement / active demotion / later recovery (GPT/Raphael).
1. **What metastability was supposed to mean operationally** here, not as an aspiration.
2. **How coherence, identity stability, receptivity and capacity to change evolve over time**, including the rupture
   experiments (recover Samuel's ~1,000-step result exactly).
3. **Is the lock an identity-preservation mechanism missing its counterbalance, or already the intended equilibrium?**
4. **What value formation is meant to measure:** immediate coherence contribution, longer-term contribution to the
   field, or something else. Establish intended semantics before touching the implementation.
5. **Does (b) correct the mechanism mathematically?** Identify the exact calculation and the smallest experiment that
   distinguishes the possibilities.

## Starting points already found (2026-10-15)
- **The value calculation** (`agents/value_emergence.py::_birth_or_strengthen`, ~line 423):
  `reinforcement = (coherence_delta × 0.6 + emotional_satisfaction × 0.4) × bond_weight + decision_bonus`, then
  `strength += reinforcement × reinforcement_lr` (clip 0..5); `coherence_contribution += coherence_delta`. Emergence
  gate (~line 371): `(coherence_delta×0.40 + emotional_satisfaction×0.35 + surprise×0.15 + max(0, trust_impact)×0.10)
  × bond_weight + decision_bonus ≥ min_emergence_threshold`.
- **`coherence_delta` is already a marginal delta:** `loop/autonomous_cycle.py` step 10 measures
  `actual_delta = field.coherence_impact(vec)` *before* injection and passes it via `governance.emit_feedback`. So (b)
  as phrased may be a no-op. Check before proposing it.
- **Two other suspects for the broad drop:** `emotional_satisfaction` (find where `_on_feedback` builds it, ~line 297;
  if it reads the emotion state, "joy" is literally coherence, `docs/EMOTION_CALIBRATION.md`, so a slightly less
  coherent field lowers satisfaction for every value at once), and the decision bonus (ALLOW vs ALLOW_WEAKENED pay
  differently; witness shifts that mix).
- **History to mine (parent repo RFE-Core2, `docs/findings/INDEX.md`):** the lock-in arc (2026-06-06 coherence-is-not-
  plasticity, frame-correction, expression-decollapse, attractor-migration; the SECOND-LOCKER result), the rupture
  findings (2026-08-04 rupture-and-the-lock-is-a-landscape-problem, rupture_impulse_probe), the 5000-step lock run
  (max disp ≤ 0.00012), `docs/self_model_thesis.md` ("smithing the attractor"), `docs/alchemical_correspondence.md`,
  `docs/north_star.md`, `STATE.md` SETTLED list, Fix 0-B / 0-C (diversity fitness, leaky ratchet), the dim256 finding.
  Metastability today is read upstream (`cognition/stream_metastability.py`, stages A/C), never on the field.
- **Our own long runs (this repo):** `findings/2026-10-14-witness-aftermath-and-upstream-rupture.md` (witness over
  1,200 steps: cost plateaus; field-wide receptivity decays to 16–21% without witness, 41–42% with);
  `findings/2026-10-15-selector-identity-replay.md`.
- Runs are replay-exact now (`substrate/determinism.py`); use `deterministic(seed)` for every arm.
