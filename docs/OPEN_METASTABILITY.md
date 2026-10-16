# OPEN: metastability, change, and what values are built from

**RESUME HERE** (marker set 2026-10-15, before a context compaction). Samuel paused the value-formation fix to ask a
deeper question first. Nothing below is decided. **Witness and rupture stay OFF. Don't change the runtime or weaken
any gate until this is answered.**

## Where we are
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

## The work, in order
0. **Finish the step-by-step reinforcement trace** (planned before the pause): one replay-exact pair (REF vs WIT, all-ON
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
