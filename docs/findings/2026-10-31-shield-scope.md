# A refused input is experienced but plants nothing

- **Date:** 2026-10-31
- **Substrate:** `tests._common.build_full_stack` (its defaults: dim 64, pretrain off), cold stack, CPU.
- **Probe:** gate `tests/integration/shield_scope.py`
- **Status:** standing
- **Depends on:** `2026-10-31-contract-audit` (its open items: what a shielded write may touch; `rupture_on_lock`)

## Question
The contract audit found that a write SACRED_SHIELD blocks still leaves things behind: the refused vector could seed an
attractor center, form a crystal (whose activation injects into the field), be stored in the vector space and lattice,
bind a concept, and signal its coherence onto the sacred symbol. Which of those may a refused input still do?

## The call (Samuel and Claude, with a second opinion from a fresh Grok session)
The line is "a refused vector shapes nothing", keyed on the decision.

- **Blocked on a refusal:** field injection (already), crystal formation, attractor seeding, the vector-space and
  lattice entries (the dreamer samples the vector space and injects recombinations, so storing a refused vector is a
  delayed inject), concept binding, and the coherence signal onto the targeted symbols.
- **Kept:** perception before the gate (watcher, witness, emotion, echo), the stream push and topology record (the
  step was experienced), and the usage bump in `generate()`. Usage only decides embedding residency (hot / warm /
  cold) and eviction order; sacred symbols are never reaped. Being named, even in an attack, keeping the anchor
  resident moves nothing, and undoing it would mean rolling back counters set before the gate. Grok argued for
  rolling it back too (the 2026-07-03 ruling counts lifecycle as part of a write); we judged residency-only
  bookkeeping on the side of "noticing".
- **Scope: every refusal, not only SACRED_SHIELD.** Writing the test showed a QUARANTINE planting the same geometry.
  The principle doesn't depend on which gate refused, so the rule covers QUARANTINE, REJECT and SACRED_SHIELD.
- **F8 holds.** The rule keys on the decision, not on "contains a sacred token": an allowed reference inside ordinary
  content is still a read, still counts, and still reaches memory.

## Result (observed)
`shield_scope`, one cold step of `['3.12']` from a fresh source, crystal and attractor gates opened to 0 so the
decision is the only thing that can stop them:

| check | before the change | after |
|---|---|---|
| decision | SACRED_SHIELD | SACRED_SHIELD |
| the refused vector injected | **yes, cosine 1.000** (crystal activation) | no |
| new crystal / new attractor center | yes / yes | no / no |
| vector-space / lattice entry | yes / yes | no / no |
| coherence signal onto `3.12` | 0.0 → 0.64 | unchanged |
| attractor strength, crystal binding | changed | unchanged |
| usage (residency) | 1 → 2 | 1 → 2 |
| stream push (experienced) | 1 | 1 |
| `['3.12', 'coherence', 'field']` | ALLOW, reaches memory | ALLOW, reaches memory |

Old code 5/12, new 12/12. The rhythm behaviours' own injections (chorus, explore mutation, the dreamer) are the open
architect question in CLAUDE.md; the test reports them and does not assert on them. On this step there were none.
Canonical runs have no refusals (census: 1,500 arbitrate calls over seeds 42-44, zero blocks), so they're unchanged.

## `rupture_on_lock`
Kept, and named in CLAUDE.md as the second sanctioned monitor read beside `diversity_credit`. It is not dead code:
the 2026-08-04 rupture investigation built it, and the 2026-09-23 dim-256 lock gate used it as the rupture arm
(`reflect()` on ~2,135 of ~2,150 steps). It reads stage A's `regime_state`, blends a held direction, and the result
still goes through `arbitrate()`. Off by default; no third read without naming it.

## Threats / confounds
- One cold step at the test stack's dim 64; the rule keys on the decision, so it doesn't depend on step number or width.
- Usage kept rising for the targeted symbol; with decay no longer recomputing sacred usage (`84db64e`), repeated
  naming ratchets residency only.

## Open / next
- [ ] The rhythm behaviours' direct injections on a refused step (explore's mutation is of the step's vector): still
  the architect question; this finding doesn't settle it.
