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
| `2026-10-15-selector-identity-replay` | Replay-exact, pre-declared identity bars: WITNESS PASS 2/3 (anchor drifts less than OFF), RUPTURE-UP PASS 3/3, BOTH FAIL 0/3 (coherence costs add, −0.06). Levers stay OFF; BOTH needs a shared budget | **standing** |
| `2026-10-15-reproducible-runs` | 36 wall-clock reads, 9 unseeded generators, 3 random-key sites routed through `substrate/determinism.py`; seeded runs now replay bit-for-bit in and across processes; production unchanged; guard test | resolved (same commit) |
| `2026-10-14-witness-aftermath-and-upstream-rupture` | Witness: retention 3/3, per-event recovery 3/3, responsiveness 2/3 → the dip is the update, small cost accumulates. Upstream rupture: behavior 3/3 (0.63 vs 0.02), integration 3/3; identity holds 2/3 seeds, fails the pre-declared mean bar (seed 2 −0.12). Follow-ups: seed 2 = steady recoverable cost (~0.02), runs don't replay exactly (wall clock); witness over 1,200 steps plateaus and keeps the field ~2× as receptive as OFF under long-run stiffening. Levers stay OFF | **standing** |
| `2026-10-14-six-rhythm-selector-live-off-on` | Live OFF/ON, 3 seeds: reading precise (1.00, never hijacks stance); split run: witness works (field moves 35–45% less) and owns the coherence drop (−0.06..−0.13); rupture-through-reflect FAILS (integrator absorbs it). Lever stays OFF; rupture + witness cost are architect decisions | **standing** |
| `2026-10-14-six-rhythm-corpus-and-reading` | Corpus 1.4.0 adds witness (integrity clean); six-class pretrain reads rhythm from unseen holdout at 0.977 (witness precision 1.000) | **standing** |
| `2026-10-14-bridge-emotion-never-restored` | Bridge checkpoint saved only derived arousal/valence; emotion reset on every restart. Fixed: six scalars persist | resolved (same commit) |
