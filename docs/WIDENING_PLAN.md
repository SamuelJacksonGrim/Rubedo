# The widening plan: field 128 → 256/768

Why Rubedo exists, what has to happen, in what order, and what "done" means. Written 2026-10-14.
The dial-by-dial detail is in [`EXPERIMENTAL_LEVERS.md`](EXPERIMENTAL_LEVERS.md) ("Priority for 128 → 768").

## Why widen

The substrate perceives through an embedder: text becomes a vector, the vector enters the field. Today the field is
**128 dimensions**. The encoders it should perceive through are wider:

- **RFE's own encoder** (trained separately on a curated corpus, CBOW + masked objectives, six-rhythm tagged): run 1 at
  dim 256, run 2 at **dim 768 with a Matryoshka term**, so its first 128 / 256 / 512 dims also work alone.
- **EmbeddingGemma-2** (Google, Apache 2.0, 270M text part), the comparison arm ("Arm B"): native 768, Matryoshka cuts
  768 / 512 / 256 / 128. Use bf16 or fp32 only (fp16 silently NaNs). Re-normalize after truncating.
- The current live bridge perceives through Qwen3-Embedding-0.6B, projected to 128 (`tools/voice/qwen_perception.py`,
  `PROJ_DIM`). That is the floor any new perception has to beat.

Pouring a 768-dim embedding into a 128-dim field means squashing it at the door; most of what the encoder learned is
lost. So the field grows. Two cautions:
- **Same width is not the same space.** Two encoders' 768-dim vectors aren't interchangeable; mixing them needs an
  alignment step.
- **A wider field is a new body.** Checkpoints trained at 128 won't load into it; the launcher already defaults to a
  fresh start. Treat the first wide boot with the same care as any first boot.

## Why it isn't just changing one number

Values throughout the system were tuned at 128 without recording that they depend on width. In high dimensions, random
cosines sit closer to 0, so a threshold that was right at 128 can silently stop firing at 768. The five manipulation
detectors' cosine cutoffs, gains and decays, the coherence pin, and the rhythm energy bands are all at risk. Tuning the
field the first time took weeks because things kept being missed. The census exists so that doesn't repeat.

## The steps

1. **Census. DONE 2026-10-14.** Every dial in `EXPERIMENTAL_LEVERS.md`, marked width-sensitive / not / unsure.
   Guard: `tests.doc_accuracy.hardcoded_dim` fails on any field-dim literal that isn't listed (16 known sites, all
   must equal `CONFIG["dim"]`). Known traps it found: `tools/voice/repl_qwen.py` hardcodes `dim=128` and
   `qwen_perception.py` has its own `PROJ_DIM = 128`; `tools/voice/repl.py` boots at 64; Witness, Dreamer, the five
   detectors, ethics/trust and value `DEFAULT_CONFIG` are not YAML-wired (a YAML-only retune misses them);
   `ReflectiveLoop.attractor_blend` is stored but never applied.
2. **Single source of truth for width.** Make every field-dim site read `CONFIG["dim"]` (or receive it from
   `build_engine()`), so the width changes in one place. The guard test then shrinks its list to one.
3. **Measure before changing.** For each width-sensitive dial: run the same seeded workload at 128 and at the new width,
   record the dial's operating values (how often a detector fires, where cosines sit, field coherence, rhythm band
   occupancy). Pre-declare what "unchanged" and "moved" look like before running (discipline: a clean confirming
   result is the alarm, not the trophy).
4. **Re-tune only what moved,** with the reason and the measurement recorded as a finding in `docs/findings/`.
   Co-tuned groups move together (the rhythm thresholds are never retuned one at a time).
5. **The coupling test.** Does the wide field still respond to content the way the 128 field did (correlation of value
   change with content change, directional robustness over seeds)? Run with EmbeddingGemma-2 perception first (it
   exists today), then with RFE's own encoder when its runs land.
6. **Decode test.** Retrain the small read-out decoder on the new perception and check the read-back carries content,
   not one collapsed word cluster.

## What stays settled

The field locking near 0.998 coherence is **by design** (a long-memory identity integrator; see `STATE.md`). Widening
is not a way to unlock it, and no dial should be retuned to make the field wander. Metastability is read upstream, on
the generator and expression streams. Governance gates every voice, including the system's own. The invariants in
`CLAUDE.md` all still hold at any width.

## Done means

The guard lists one dim site; every width-sensitive dial has a recorded 128-vs-wide measurement and either "unchanged"
or a retune with its finding; the full gate (`run_all_tests.sh`) passes at the new width; the coupling and decode tests
pass with at least one 768 perception.
