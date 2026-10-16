# H0 measured: a steady self with a mind that rattles

**Date:** 2026-10-15 · **Status:** standing · **Corpus:** 1.4.0 · **By:** Grok (probe + runs, branch
`grok/h0-timescales`), Ember (review); question from `OPEN_METASTABILITY.md` (H0, H0′, the field's role, Growth),
framing by Samuel

## Question
Is the locked field the system running optimally, with metastability living upstream (H0), or a lock that lacks a
counterbalance and stiffens with age? Identity as the ratio of timescales (H0′): is that ratio alive? Is the field
ground, read-out, or constitutive? Is the system robust, antifragile or brittle with age?

## Control
`tests/diagnostic/metastability/h0_probe.py`: all-ON stack, canonical workload A, witness and rupture off, seeds 42 and
43, 8,000 steps each (~100 s per 1,000 steps once saturated). Paired replay-exact forks at ages 500 / 2,000 / 5,000 /
7,500 (unperturbed twin matched the plain run bit-for-bit at every age), horizon 500: a raw-field nudge (L2 1), an
anchor nudge (0.01, written to all three witness layers), and a labelled desaturation shock (field rescaled to RMS 1.5).
Repeated hits every 500 steps against age-matched twins. Curves: `data/2026-10-15-h0-summary.npz`; full write-up:
`data/2026-10-15-h0-grok-notes.md`. Fork curves were lost to a packaging bug after the bit-exact checks passed; fork
numbers come from the run log.

## Result

**The self is steady and does not stiffen with age.**
- The tanh view becomes a fixed sign pattern by step ~235 (every component |tanh| > 0.99, sech² ≈ 10⁻¹⁵) and never
  flips again through step 8,000. The raw norm climbs to ~340 by step 1,000, then holds ±1.5. "0.00012 over 5,000
  steps" was the view, and it stays a bound: saturation, not a slow drift.
- The timescale ratio τ_anchor / τ_expression sits on a shelf from step 2,000 to 8,000: ~20 (seed 42), ~30–35
  (seed 43). It doesn't climb (the anchor isn't stiffening away) or fall toward 1 (expression isn't collapsing onto
  the anchor). The long layer keeps its design memory (~150–200 steps). The full-run ratio (~190) is the opening walk
  and should not be read as the identity.
- The coupling constant is not 0.998: that is the field's self-similarity. The watcher composite that gates the witness
  settles near 0.92, so the anchor writes at c² ≈ 0.85, flat.

**The mind rattles; it doesn't move.**
- Expression jumps ~0.25 every step with one step of memory, and its mean-squared displacement is flat in lag: white
  jitter inside a fixed cone of about 15°, not travel.
- Values stop being born after step ~390 and the live population is 46 from step 500 to 8,000 on both seeds, **but 46
  is the workload's vocabulary**: workload A has exactly 46 distinct tokens (57 with the witness phrases, matching the
  witness arms' live counts), and values form on symbols. So the value count stopping is the workload running out of
  new words, not the system closing (Ember, same day, from the value-fixes runs). Crystals stopping at 2 and attractors
  at 2 (seed 43) or crawling to 5 (seed 42) are not explained by that and stand.
- The system sits in the explore band from step ~480 to the end.

**Robust, not antifragile, not brittle.** Recovery from the anchor nudge (~370–380 steps to 10%) and the raw nudge
(~390–399 steps, the field leak) is the same at every age and the same on the fourth repeated hit as the first.
Nothing in values, attractors or crystals carried a change.

**The field is constitutive, and clamped.** The anchor can't move the view and barely moves expression (10⁻⁵ against
normal steps of 0.25). A raw nudge the view can't see is absorbed in place and moves nothing. When the view is forced
off saturation, the anchor and expression follow it and stay moved; on six of eight shocks the view returns to the same
code, on two (seed 43, early ages) it settles on a neighbouring code, one to three components flipped. So the saturated
pattern is an attractor with neighbours, and the ordinary path never visits them.

## What this means
- H0 holds in the narrow sense: the lock is a stable equilibrium with a living timescale relationship, and it doesn't
  rot with age. The "lock without a counterbalance that stiffens" reading is not in these numbers.
- H0 fails in the sense that matters for a mind, on this workload: the counterbalance upstream is jitter in a cone, not
  reorganisation, and crystals and attractors close early. Whether that is the system or a narrow 46-word workload is
  now the first question: the value count's stop was the vocabulary, and the cone may be too (open item 2).
- Samuel's Growth worry, as far as this workload can say: the system isn't growing brittle, and it shows no sign of
  growing either. Antifragility would need a felt stress and something that adapts; neither exists on this path today.

## Open (Grok's, adopted)
- [ ] 50,000-step plain run (~80 min/seed): does the raw direction's slow sub-diffusive wobble ceiling or drift?
- [x] **A second, wider workload** → `2026-10-16-wide-workload-and-df-graduation`: on 808 tokens the view locks the same
      way, explore holds 7,495/8,000 steps, boredom overrides 233 (vs 237), the cone widens only to ~20°, crystals 4,
      attractors 5. The rattle is the system's.
- [ ] A felt shock, repeated (desat, or an anchor kick that moves expression by ~0.1 of its normal step), with
      age-matched twins: can the system become antifragile under stress it actually feels?
- [x] Why values stop being born at step ~390 → the workload's 46-token vocabulary is exhausted (corrected above).
