# Findings index — the one-screen map of the ledger

One line per finding: what it established, and whether it is still the
authoritative read. **Read this before grepping the ledger.** Statuses:

- **standing** — still the authoritative result on its question
- **superseded** — a later finding corrects or absorbs it (named)
- **resolved** — its open work landed; kept as the record of how
- **shelved** — result stands, the work it feeds is deliberately parked
- **historical** — a completed arc step; context, not current truth

Inline `→ DONE/DECIDED/…` stamps inside each finding mark which of its Open
items landed (added at resolution time, same-commit — the anti-tail-chasing
rule). Every finding file must appear here (CI-enforced by `verify_docs`).

**Rubedo's ledger starts empty (2026-10-14).** The 256 findings that built this system,
2026-06-06 through 2026-10, are in the parent repo:
[RFE-Core2 `docs/findings/INDEX.md`](https://github.com/SamuelJacksonGrim/RFE-Core2/blob/main/docs/findings/INDEX.md),
and in this repo's own git history before the slim commit. Their standing verdicts still
bind here (`STATE.md` lists the settled ones). New results from the widening onward are
recorded below.

| Finding | One-line verdict | Status |
|---|---|---|
| `2026-10-19-witness-activated` | Witness on by architect decision over a HOLD gate, on 12 seeds with grace: receptivity 12/12 (~2×), identity anchor steadier with witness on every seed measured, field less locked; the identity bar fails only on its 10-step coherence-dip sub-check (−0.101 to −0.115 vs −0.10, 6 of 9); witness never fires on workload A; one witness-caused break in 12 (seed 46 bond). `six_rhythm_selector` on with `six_rhythm_stances` ["witness"]: rupture stays off. Production path: witness 78/500 steps, rupture 0 | **standing** |
| `2026-10-18-fragmentation` | Fragmentation is a youth detector: consumer off, every canonical flag is pre-binding and `frag_strong` stays 0 while strong goes 0 → 46 by step 1,600. `fragmentation_grace` waits for 1,500 crystal/attractor relays; all-ON gate passes (strong 12 vs 12, demotions 90); holds on held-out seeds 45-47 (active 37-54 vs 19-37 off). Graduated default-on 2026-10-18; digest unchanged; suite 28/28 | **standing** |
| `2026-10-16-witness-regate-with-df` | Witness re-gated with D+F on: composition 0/3 → 1/3, identity and receptivity still 3/3 (~2× retention). Values no longer collapse under witness (active 13→2 before; now 34→22, 31→26, 39→37, strong band holds); only the marginal `active_values ≥ 30` bar breaks, and **that dip is entirely the ⊘ consumer**: without it witness costs values nothing (54→54, 51→51, 54→54). Witness stays OFF; ⊘ Fragmentation is the critical path | **standing** |
| `2026-10-16-wide-workload-and-df-graduation` | On an 808-token corpus workload the rattle persists (view locks, explore 7,495/8,000 steps, boredom overrides 233 vs 237, cone ~20° vs ~15°): it is the system's. Values hit the opposite wall (808 words for 64 slots, nothing consolidates). D+F holds on both workloads (witness starvation ~0.6 → ~0.95), E's gain was the 46-word room. **D+F graduated default-on**; the all-ON gate's only failing check is the opt-in ⊘ Fragmentation strong-band trim, passed under the exception Samuel granted. Attack tests pass with D+F on; suite 26/26 | **standing** |
| `2026-10-15-value-fixes-measured` | Two bugs fixed and on (CORE manipulation check reads the step's consumed signals; dream crystals found by identity, only new ones pay). Levers C–G off, measured on 3 seeds: F alone is inert because the coherence_delta artifact nets dream-band reinforcement to ~0 (the decision-bonus attribution was accounting, not cause); D+F is the working pair (witness starvation ~0.6→~0.9, composition = REF, no alarms); E strongest (witness stops starving values); C floods CORE; G indiscriminate. Nothing graduates until a wider workload and the architect's call on the ⊘ strong-band exception | **standing** |
| `2026-10-15-h0-steady-self-rattling-mind` | H0 measured (8,000 steps, forks at four ages): the view saturates into a fixed code by step ~235 and the timescale ratio holds on a shelf (~20–35), no stiffening with age; robust, not antifragile or brittle; field constitutive and clamped. But expression is white jitter in a ~15° cone, and crystals and attractors stop forming early (the value count stopping at 46 is the workload's 46-token vocabulary, corrected same day). A steady self with a mind that rattles, on a narrow workload | **standing** |
| `2026-10-15-dream-consolidation-closed` | The post-dream value boost can never fire: the dreamer hard-codes long_relation 0.5 against the store's 0.80 (half of all dream offers cleared coherence + stability and were refused only by that), dream crystals carry synthetic keys that name no value, and new crystals are found by list length. Crystal store ends runs at 1–4 crystals | **standing** |
| `2026-10-15-why-values-weaken-under-witness` | The drop is the decision bonus (70–90%): witness moves steps into the dream band, whose ordinary G/T split fires systemic `identity_erosion` → ALLOW_WEAKENED → smaller bonus + missed emergence. Not negative reinforcement, no recovery. coherence_delta is mostly a raw-vs-tanh measurement artifact (input's own effect ≈0 at saturation); satisfaction = max(0, coherence_delta). Identity PASS partly the c² write-slowing. Options (a)/(b) aim at the wrong thing; value semantics is the question | **standing** |
| `2026-10-15-witness-composition-gate` | Witness on the all-ON stack: identity 3/3, receptivity 3/3 (~2×), composition FAIL: every value weakens (ACTIVE tier 5→0, 7→0) because value = coherence contribution and witness lowers coherence. Baseline healthy (standing gate passes everywhere). Witness stays OFF; value formation is an architect question | **standing** |
| `2026-10-15-selector-identity-replay` | Replay-exact, pre-declared identity bars: WITNESS PASS 2/3 (anchor drifts less than OFF), RUPTURE-UP PASS 3/3, BOTH FAIL 0/3 (coherence costs add, −0.06). Levers stay OFF; BOTH needs a shared budget | **standing** |
| `2026-10-15-reproducible-runs` | 36 wall-clock reads, 9 unseeded generators, 3 random-key sites routed through `substrate/determinism.py`; seeded runs now replay bit-for-bit in and across processes; production unchanged; guard test | resolved (same commit) |
| `2026-10-14-witness-aftermath-and-upstream-rupture` | Witness: retention 3/3, per-event recovery 3/3, responsiveness 2/3 → the dip is the update, small cost accumulates. Upstream rupture: behavior 3/3 (0.63 vs 0.02), integration 3/3; identity holds 2/3 seeds, fails the pre-declared mean bar (seed 2 −0.12). Follow-ups: seed 2 = steady recoverable cost (~0.02), runs don't replay exactly (wall clock); witness over 1,200 steps plateaus and keeps the field ~2× as receptive as OFF under long-run stiffening. Levers stay OFF | **standing** |
| `2026-10-14-six-rhythm-selector-live-off-on` | Live OFF/ON, 3 seeds: reading precise (1.00, never hijacks stance); split run: witness works (field moves 35–45% less) and owns the coherence drop (−0.06..−0.13); rupture-through-reflect FAILS (integrator absorbs it). Lever stays OFF; rupture + witness cost are architect decisions | **standing** |
| `2026-10-14-six-rhythm-corpus-and-reading` | Corpus 1.4.0 adds witness (integrity clean); six-class pretrain reads rhythm from unseen holdout at 0.977 (witness precision 1.000) | **standing** |
| `2026-10-14-bridge-emotion-never-restored` | Bridge checkpoint saved only derived arousal/valence; emotion reset on every restart. Fixed: six scalars persist | resolved (same commit) |
