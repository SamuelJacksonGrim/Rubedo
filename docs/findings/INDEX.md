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
