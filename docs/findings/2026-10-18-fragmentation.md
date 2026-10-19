# Fragmentation is a youth detector

**Date:** 2026-10-18 · **Status:** standing (flag stays off) · **By:** Grok

## Question
⊘ Fragmentation (`source_diversity < 0.35` and `attractor_binding < 0.35`) is the shared cause of the witness active-count dip and the all-ON strong-band failure (12 → 2). Samuel on 2026-10-16: pruning needs a mature ecology. Is the rule firing on values before binding has had time to arrive, and does a wait — Drift and Dissolution untouched, default off — keep the strong band without silencing the consumer?

## Control
Consumer off, D+F on, seed 42, 2,000 steps, snapshot every 50: `tests/diagnostic/integrity/fragmentation_axes_probe.py`. Logs: `docs/findings/data/2026-10-18-fragmentation-axes-{canonical,wide}.{json,log}`. Per-value follow-up, consumer off, no `read()`: `2026-10-18-fragmentation-fate.json` and `-43`/`-44`.

The fix is `CONFIG["fragmentation_grace"]` (default **False**). On: Fragmentation cannot name a value until `_FRAGMENTATION_GRACE_SIGNALS` (1500) crystal/attractor token-relays have happened since that value was first read. Off: the historical level check, and `signal_crystal` / `signal_attractor` are not wrapped. Not on the live board. Not graduated.

## Result
Consumer off, canonical, the flag falls as binding arrives and never marks a strong value. `frag_strong` is 0.0 from the first step any value is strong (step 300) through step 2,000. Binding never drops (`drops=0`).

| step | frag | bound | strong |
|---|---|---|---|
| 50 | 38/43 | 3 | 0 |
| 300 | 12 | 34 | 2 |
| 450 | 0 | 46 | 5 |
| 500 | 0 | 46 | 12 |
| 1,000 | 0 | 46 | 28 |
| 1,600 and 2,000 | 0 | 46 | 46 |

Wide is the same shape without a strong band (the 808-word workload does not repeat enough): frag 62/64 at step 50, 16 at 700, 6 at 1,000, 0 at 1,600, and 1 at 2,000 — the one value still unbound (`bound=63`, `raw_max` 19.5, `drops=0`). No value is flagged after binding. Left alone, the canonical values the rule flagged at step 50 are bound by step 450 and strong by step 1,600.

A step-age wait cannot serve both gates. On the composition probe's consumer-on trajectory (reference arm first), mutation is still readable and unbound at age 293. On witness seed 44 workload A, governance is still readable and unbound at age 306. Any age that still demotes the composition tail nicks seed 44's strong band. Relay count separates them: the latest strong value still readable and unbound had seen 1,407 relays (seed 44 A, both arms); the composition tail (mutation / bifurcation / chaos) was still readable at 1,836. 1,500 sits between.

All-ON composition gate, seed 42, 500 steps, `--fragmentation-grace` (every existing bar, none loosened):

| check | result |
|---|---|
| ⊘ preserves strong | 12 vs ref 12 |
| ⊘ consumer used | demotions 90 (a 300-step age wait had demoted 0) |
| active ≥ 30 | 43 |
| mean strength > 1 | 2.468 |
| HHI < 0.30 | 0.290 |
| the rest | injection 1.000, no quarantines, bonds 2, λ open, sacred skipped 238 |

Witness re-gate, same command as `2026-10-16-witness-regate-with-df`, plus `--fragmentation-grace`. The active-count dip is gone. Witness does not pass the gate.

| seed | workload | active REF → WIT | strong | was (consumer on, no grace) |
|---|---|---|---|---|
| 42 | B | 43 → 51 | 5 → 5 | 34 → 22 |
| 43 | B | 45 → 45 | 7 → 7 | 31 → 26 |
| 44 | B | 54 → 51 | 9 → 9 | 39 → 37 |

Workload A is flat (43→43, 32→32, 40→40). Identity 3/3, receptivity 3/3 (retention d1 WIT/REF 0.00307/0.00075, 0.00419/0.00262, 0.00518/0.00270), non-vacuous 78/88/96. Composition **2/3**: seed 43 workload B has HHI 0.307 on both arms, so WIT fails the absolute bar and breaks nothing REF passes. Witness stays OFF.

Flag off, `python -m tests.diagnostic.rename_digest` (OMP/MKL=1): combined `48f877d8a76c90b087600a65c349210b471bdebb87d25096012500f29d64cd9f`, bars met. `run_all_tests.ps1`: 28/28.

## What this means
Fragmentation, as a level check, reads "binding has not arrived yet." With the consumer on, those values are pulled down before the relays that would have bound them. Waiting for 1,500 relays lets the step-500 strong band bind and still pulls a tail that is single-source and unbound after that many opportunities (90 demotions, not zero). Drift and Dissolution are the same checks they were.

## Held-out seeds and graduation (Ember, 2026-10-18)

`_FRAGMENTATION_GRACE_SIGNALS = 1500` was chosen between two ages measured on seeds 42-44, so before graduating it
was checked on seeds it never saw: `witness_composition_gate 45 46 47`, with grace and without, same build, OMP/MKL=1
(logs `data/2026-10-18-heldout-witness-{grace,nograce}.log`).

| seed / workload | demotions, off → on | active values (bar 30), off → on | strong (REF), off → on | witness dip in active, off → on |
|---|---|---|---|---|
| 45 A | 5069 → 361 | 31 → 40 | 6 → 14 | (witness did not fire) |
| 45 B | 5614 → 594 | 29 → 48 | 2 → 8 | 29→26 → 48→42 |
| 46 A | 6968 → 474 | 29 → 40 | 2 → 12 | (witness did not fire) |
| 46 B | 6648 → 36 | 37 → 54 | 1 → 2 | 37→19 → 54→52 |
| 47 A | 5905 → 621 | 29 → 37 | 6 → 12 | (witness did not fire) |
| 47 B | 6178 → 700 | 29 → 43 | 6 → 6 | 29→26 → 43→43 |

The grace generalises: off, the active-values bar fails on five of six runs; on, it passes on all six, and the
witness dip is gone or small. What still fails is identical in both arms, so it is not the grace: HHI 0.319 / 0.321
on workload A for seeds 45 and 46 (REF fails it the same), bonds 1 → 0 under witness on 46 B, and the witness identity
check (same numbers off and on). Counting binding opportunities instead of steps is what lets the constant travel.

**Decision:** `fragmentation_grace` graduates default-on. It passes the all-ON composition gate (the graduation rule)
and holds on held-out seeds; it acts only when the opt-in consumer is attached; `False` restores the historical
level check. The witness lever is separate and stays off: its own gate is still HOLD (identity 1/3 on 45-47).
The all-ON probe and the witness gate now run grace by default; `--fragmentation-grace-off` is the control.

## Open
- [x] Graduate `fragmentation_grace` by a separate call: done, above.
- [ ] Witness composition is 2/3 on 42-44 and identity 1/3 on 45-47; witness stays off until its own gate passes or Samuel decides.
- [ ] Seed 43 workload B HHI 0.307 is both arms. Not a witness-versus-reference dip, and not fixed by loosening the bar.
