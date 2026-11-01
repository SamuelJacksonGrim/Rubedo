# A refused input is felt, but can't enter or train the system's lasting state

- **Date:** 2026-10-31 (revised the same night after an outside review by Copilot)
- **Substrate:** `tests._common.build_full_stack` (its defaults: dim 64, pretrain off), CPU.
- **Probes:** gate `tests/integration/shield_scope.py`; counterfactual twin
  `tests/diagnostic/integrity/refused_twin_probe.py`
- **Status:** standing
- **Depends on:** `2026-10-31-contract-audit` (its open items: what a shielded write may touch; `rupture_on_lock`),
  `2026-10-31-refused-rhythm-leak` (the rhythm behaviours on a refused step)

## Question
The contract audit found that a write SACRED_SHIELD blocks still leaves things behind: the refused vector could seed an
attractor center, form a crystal (whose activation injects into the field), be stored in the vector space and lattice,
bind a concept, and signal its coherence onto the sacred symbol. Which of those may a refused input still do?

## The contract
The first version of this finding said "a refused input plants nothing". The outside review showed that was false as
written: everything before the gate (watcher, witness, emotion, echo, stream, usage) still takes the vector, and some of
that is adaptive state. The contract is drawn by causal role instead:

**A refused input (QUARANTINE / REJECT / SACRED_SHIELD) is felt, but it can't enter or train identity, semantic,
geometric, generative or replayable state.**

| state | on a refused step | why |
|---|---|---|
| field injection | no | the gate's job |
| crystal, attractor center, binding, coherence signal | no | geometry and semantic state later steps fall into |
| vector space, lattice, **stream** | no | replayable: the dreamer samples the vector space and replays the stream |
| **witness anchor and trace** | restored to the step's checkpoint | identity: see the twin below |
| rhythm behaviours | only stabilize runs | explore rotated the anchor the refused vector landed on (0.996 copy), reflect re-encoded the refused tokens, the dreamer blended the refusal back in (`2026-10-31-refused-rhythm-leak`); stabilize replays crystals that existed before |
| **ghost** on the witness | kept: vector, source, decision, coherence, step | Samuel: an attack the system never registers is one it can't recognize. Bounded (256); nothing reads it yet |
| emotion, predictive echo | kept | feeling an attack and learning to anticipate it are the defensive side of experience; they don't inject |
| usage | kept (+1) | decides embedding residency and eviction order only. Grok argued for rolling it back; we judged it noticing. The review's point stands that for a non-sacred refused symbol this keeps it hot a little longer; a cache tier, not a semantic write |
| topology log | kept | nothing reads it (contract audit) |

Keyed on the decision, not on "contains a sacred token", so an allowed reference inside ordinary content is still a read
(F8). Every refusal, not only SACRED_SHIELD: writing the first test showed a QUARANTINE planting the same geometry.

## Result (observed)
**Single step** (`shield_scope`, one cold step of `['3.12']` from a fresh source, crystal and attractor gates opened to 0
so the decision is the only thing that can stop them):

| check | before | after |
|---|---|---|
| decision | SACRED_SHIELD | SACRED_SHIELD |
| the refused vector injected | **yes, cosine 1.000** (crystal activation) | no |
| new crystal / attractor center | yes / yes | no / no |
| vector-space / lattice entry | yes / yes | no / no |
| coherence signal onto `3.12` | 0.0 → 0.64 | unchanged |
| attractor strength, crystal binding | changed | unchanged |
| stream push | 1 | 0 |
| witness anchor, long trace, identity trace length | moved | unchanged |
| ghost kept | — | yes (source, decision, cosine 1.0 to the vector) |
| usage (residency) | 1 → 2 | 1 → 2 |
| `['3.12', 'coherence', 'field']` | ALLOW, reaches memory | ALLOW, reaches memory |

Old code 5/12 of the first version's checks; now 14/14.

**Counterfactual twin** (`refused_twin_probe`, seeds 42-44, warm-up 120): twin A sees 200 refused sacred writes, B sees
nothing, C sees 200 allowed reads of the same token inside ordinary content; then all three are reseeded identically and
run the same 150 canonical steps.

| A vs B, after 200 refused writes | before (witness took them) | after (witness restores, keeps ghosts) |
|---|---|---|
| witness anchor cosine | 0.753 / 0.751 / 0.748 | 1.0000 / 0.9999 / 1.0000 |
| anchor shift toward the attack vector | +0.71 / +0.72 / +0.71 | +0.08 / +0.10 / −0.17 (noise on a near-zero shift) |
| ghosts kept | 0 | 200 |
| max emotion difference | 0.11-0.13 | 0.21-0.22 |
| final field cosine after the probe | 0.988 / 0.986 / 0.983 | 0.997 / 0.994 / 0.995 |
| later decisions that differ (of 150) | 22 / 22 / 28 | 37 / 44 / 46 |

For scale, C (allowed reads) moves the anchor to 0.88-0.91 and changes 129-138 of the 150 later decisions.

The identity channel was real and is closed: 200 refused writes had dragged the identity anchor a quarter of the way
toward the attacker (more than the allowed reads did, because the attack is one pure repeated vector), and now leave it
exactly where it was, with every attack kept as a ghost.

The decision row went the other way, and it is not content leaking (the anchor shift toward the attack is ~0 and the
field ends closer to B). Twin A now lives 200 steps that the gate fully refuses, rhythm motion included: its field only
decays, and it feels every attack (the emotion gap doubled). Its later decisions differ because it was bombarded and
starved for a while, which is the "attacks should change you, through what's felt" line Samuel drew. This probe can't yet
separate elapsed time from emotion; that needs an idle twin (below).

Canonical runs have no refusals (census: 1,500 arbitrate calls over seeds 42-44, zero blocks), so they're unchanged.

## `rupture_on_lock`
Kept, and named in CLAUDE.md as the second sanctioned monitor read beside `diversity_credit`. It is not dead code: the
2026-08-04 rupture investigation built it, and the 2026-09-23 dim-256 lock gate used it as the rupture arm (`reflect()` on
~2,135 of ~2,150 steps). It reads stage A's `regime_state`, blends a held direction, and the result still goes through
`arbitrate()`. Off by default; no third read without naming it.

## Threats / confounds
- dim 64 test stacks, pretrain off, three seeds, one attack shape (a lone sacred token). The rule keys on the decision, so
  it doesn't depend on width; the twin's magnitudes might.
- Only SACRED_SHIELD was driven in the twin; QUARANTINE / REJECT take the same code path.
- The probe phase reseeds both twins, so differences are state, not RNG; but A has 200 more steps of elapsed time.

## Open / next
- [x] The rhythm behaviours' direct injections on a refused step. → DECIDED 2026-10-31 (Samuel + Claude, on Grok's
  measurement in `2026-10-31-refused-rhythm-leak`): explore, reflect and the dreamer stand down on a refusal;
  stabilize runs.
- [x] An idle twin (same 200 steps of elapsed time with no input) to split the remaining decision difference into time
  vs feeling. → DONE 2026-10-31 another way (Rubedo has no input-free step): a second refused twin D attacking `11.88`
  instead of `3.12`. Seeds 42-44: A vs B 38 / 45 / 47 decisions differ, D vs B 28 / 37 / 36, **A vs D 10 / 8 / 11**
  (field cosine 0.9998, emotion gap 0.05-0.06). About three quarters of the after-effect is the shared experience of
  a refused barrage (elapsed time plus feeling); the ~10-decision content-specific remainder runs through the channels
  kept on purpose (emotion, the predictive echo, usage), not through geometry, memory or identity.
- [ ] What reads the ghosts. First candidate: a "familiar attack" signal for manipulation resistance (cosine to the ghost
  centroid). It changes behaviour, so it gets measured before it's on, like any lever; hardening vs susceptibility is
  then something to measure, not a side effect.
- [ ] Repeated attacks of varied vectors (a moving attack, not one token) through the twin.
