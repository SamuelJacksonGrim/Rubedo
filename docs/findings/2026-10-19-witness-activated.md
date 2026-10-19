# Witness activated by architect decision over a HOLD gate

**Date:** 2026-10-19 · **Status:** standing · **Decision:** Samuel (architect), on this record

## Question
With ⊘ Fragmentation fixed (`2026-10-18-fragmentation.md`, `fragmentation_grace` graduated), does the witness stance
pass its pre-declared gate (`tests/diagnostic/integrity/witness_composition_gate.py`, written 2026-10-15 before the
first run), and if not, what exactly fails?

## Control
The gate's own design: per seed, the all-ON stack with witness (WIT) against the same stack without it (REF), same
seed, workload A (canonical) and workload B (canonical + 20% witness phrases), 500 steps. Twelve seeds, all on the
new default (grace on): 42-44 (Grok, 2026-10-18), 45-47 (held-out, 2026-10-18), 48-53 (2026-10-19). OMP/MKL = 1.
Logs: `data/2026-10-18-heldout-witness-grace.log`, `data/2026-10-19-witness-default-48-49-50.log`,
`data/2026-10-19-witness-default-51-52-53.log`; 42-44 are in `2026-10-18-fragmentation.md`.

## Result

| bar (pre-declared) | 12 seeds |
|---|---|
| receptivity: field turns toward the witnessed input, WIT > REF | **12/12**, about 2× (e.g. +0.00478 vs +0.00178) |
| identity, anchor drift ≤ 2×REF + 0.01 | passes every seed; **lower with witness on all 9 measured here** (45: 0.080 vs 0.106 · 46: 0.124 vs 0.135 · 47: 0.077 vs 0.113 · 48: 0.135 vs 0.191 · 49: 0.084 vs 0.123 · 50: 0.068 vs 0.093 · 51: 0.080 vs 0.096 · 52: 0.137 vs 0.142 · 53: 0.105 vs 0.144) |
| identity, field lock ≤ 2×REF + 1e-5 | passes every seed (WIT ~5-7e-6 vs REF ~1-2e-6: the witnessed field moves more, i.e. less locked) |
| identity, matched coherence mean ≥ −0.05 | passes every seed (−0.033 to −0.043) |
| identity, no 10-step coherence mean below −0.10 | **fails 6 of 9** here: −0.1042, −0.1020, −0.1011, −0.1053, −0.1044, −0.1153 (passes at −0.0996, −0.0964, −0.0937). 42-44 passed |
| composition, every health check holds for WIT and nothing REF holds breaks | workload A: witness fires **0** times on every seed, so A's HHI 0.297-0.321 misses are the workload (REF fails them identically). Workload B: the only witness-caused break in 12 seeds is **seed 46, bonds 1 → 0** |
| non-vacuous, witness fires ≥ 50 on B | 12/12 (89-115) |

Gate verdict on every three-seed set: **HOLD** (identity 1/3 on 45-47, 48-50, 51-53; composition short on the sets
with an HHI-on-A seed).

Production path (`tests/diagnostic/integrity/witness_production_check.py`, `build_engine(CONFIG)` with pretraining,
the gate's workload B mix, seed 42, 500 steps): reader attached, witness taken on 78 steps, energy stance on 422,
**rupture 0**.

## What this means
Witness does what it was built for: about twice the receptivity, with the identity anchor steadier, not looser,
and a field that stays less locked. Its cost is short dips in watcher coherence while it takes input in (the
coherence that LEXICON lists as overloaded: the watcher composite, not identity), and one lost bond in twelve runs.
The identity bar fails on exactly one of its four sub-checks, the 10-step coherence dip, by 0.001 to 0.015.

## Decision (architect, 2026-10-19)
Samuel: witness on, citing the table above, with this finding recording that the gate was overridden, not passed.
He had already said (2026-10-16) that a dip is worth 2× retention. The pre-declared bars are unchanged; no bar was
loosened to make witness pass.

Implemented: `CONFIG["six_rhythm_selector"] = True` with `CONFIG["six_rhythm_stances"] = ["witness"]`.
`loop.recursion1188.stance_filtered` returns any rupture read with margin 0, so the selector never takes rupture
(the same wrapper the gate uses); rupture stays OFF. A boot without pretraining can't build the reader's centroids,
so the selector logs a warning and stays inert instead of failing the boot. `tests/integration/production_boot.py`
pins all of it (selector on, stances witness only, rupture neutralised, witness passed through).
Suite 28/28. `tests.diagnostic.rename_digest` (OMP/MKL = 1) moves on purpose: combined
`ae907b9aa94ee4736cd4c4c9c4f40e19fb07c0421c7178263dd7e047e351420d` (was `48f877d8…`); it is the baseline for the next
rename batch.

## Open
- [ ] Option 3 run alongside (Samuel, 2026-10-19: "might find more information"): an amended gate that judges
  identity by anchor drift + field lock, states the coherence dip as a separate cost bar, and judges composition
  only where witness fires, run on all 12 seeds. Labelled post-hoc; it does not replace the pre-declared gate.
- [ ] Seed 46's lost bond: is witness ever the reason a bond doesn't form, or was 46 B marginal?
- [ ] Maturity-triggered witness (BACKLOG): witness may matter most early, before the view saturates (~step 235).
