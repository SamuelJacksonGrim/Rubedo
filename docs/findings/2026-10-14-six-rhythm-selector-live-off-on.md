# Six-rhythm selector, live OFF vs ON: the reading works; rupture and coherence do not pass

**Date:** 2026-10-14 · **Status:** standing (lever stays OFF) · **Corpus:** 1.4.0 · **By:** Ember

## Question
With a real pretrained production generator, does the selector lever (commit `eadfa6a`) do what it was designed
to do, without making governance or the field's integration worse?

## Control
`tests/diagnostic/selector/six_rhythm_selector_probe.py 300 3`. One pretrained CONFIG-shape generator (dim 128,
corpus 1.4.0) saved once; both arms resume it through `build_engine`'s guarded session path. Same mixed workload per
seed (60% everyday stance phrases, 20% witness-like, 20% rupture-like), sources rotating over the canonical
four-source Resonance Family weights, RNGs pinned per seed so the arms differ only by the lever. Criteria were
written in the probe's docstring before the first run.

(A first 40-step pass used a single source; governance quarantined 24/40 steps in both arms, which hides
everything. Single-source workloads are not a valid test bed for anything that touches the field.)

## Result (3 seeds × 300 steps)

| pre-declared criterion | result |
|---|---|
| modes fire on their own phrases (>= 70%), rarely on stance (<= 15%) | **PASS**: own-phrase precision 1.00 for both modes on all seeds; stance steps switched 0/175, 0/182, 0/171 |
| witness moves the field less than OFF on the same phrases | **PASS 2/3**: 0.56 vs 0.83, 1.22 vs 0.88 (miss), 0.56 vs 0.80 |
| rupture turns the field more than OFF | **FAIL 3/3**: 6e-6 vs 1.8e-5, 1.2e-5 vs 1.4e-5, 7e-6 vs 1.5e-5 (ON turns it *less*) |
| governance no worse (quarantine/reject within +2 pp) | **PASS**: no QUARANTINE or REJECT in either arm (ALLOW vs ALLOW_WEAKENED swings by seed in both directions) |
| final field coherence ON within 0.02 of OFF | **FAIL 3/3**: −0.058, −0.039, −0.132 |

Live reading margins: witness phrases median 0.43 (min 0.33), rupture median 0.40 (min 0.16), all above the 0.10
gate; every witness and rupture phrase was read as its own rhythm.

## What it means
- **The reading is real and safe to build on.** The generator's read of live input is precise and never hijacks an
  ordinary step. That part of the design is validated.
- **Rupture-through-the-reflective-loop is the wrong actuator.** Grok flagged this from the code before the run
  (FLOW notes): the reflective loop *is* the field's integrator, so routing the held push through it gets the push
  absorbed. Measured: rupture steps turn the field less than doing nothing special.
- **Something lowers field coherence 0.04–0.13.** Candidates: witness injecting the raw, un-pulled input; rupture's
  held novel direction. Not yet separated.

## Split run: which mode does what (`six_rhythm_selector_probe 300 3 witness|rupture`)

| arm | field effect (vs OFF, same phrases) | final coherence vs OFF |
|---|---|---|
| witness only | move **less**, 3/3: 0.48 vs 0.84, 0.58 vs 0.91, 0.51 vs 0.86 | **−0.06, −0.09, −0.13** |
| rupture only | turn **less**, 3/3: 5e-6 vs 1.6e-5, 1.1e-5 vs 1.5e-5, 1.0e-5 vs 1.5e-5 | +0.02, −0.03, +0.01 (noise) |

**Witness owns the coherence drop; rupture owns the actuator failure.** Witness does what it was designed to do (the
field moves 35–45% less on witness steps) and the price is self-coherence: the input enters without the pull toward
the system's own basins or the refinement against its own history, so the field holds something it did not shape.
Whether that is receptivity working as meant (the self making room for what it receives) or a cost to bound (e.g.
witness injecting at reduced strength) is an architect question, not a tuning one. Note the coherence read here is
the watcher composite of the field against the anchor, not the ~0.998 `internal_coherence` pin.

## Open items
1. ~~Separate the coherence drop~~ → DONE (same day): witness causes it, rupture doesn't (table above).
2. **Rupture needs a design decision, not a tweak.** An actuator that actually turns the field has to work against
   the integrator, and the field lock (~0.998) is by design (STATE.md, settled). A rupture that moves the field is in
   direct tension with that. This is the architect's call: what should a rupture do to an identity that is meant to
   hold? Options to put to him: (a) rupture acts upstream only (the expression/generator streams, where
   metastability lives) and leaves the field to integrate it; (b) a bounded, logged, governance-visible push that
   bypasses the loop for one held pulse; (c) rupture as a *perceived* event only (recorded, felt in emotion, no
   field actuator).
3. **Revisit the witness metric.** "Moves the field less" was a proxy. Witness is "perceive without transforming";
   the sharper test is whether the field's change aligns with the input itself rather than with the system's own
   basins. Declare that before the next run.
4. Lever stays OFF until 1–3 land, then the all-ON composition gate.
