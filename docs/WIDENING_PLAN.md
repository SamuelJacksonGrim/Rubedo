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
   It found 16 duplicated field-dim literals. Known traps it found: `tools/voice/repl_qwen.py` hardcodes `dim=128` and
   `qwen_perception.py` has its own `PROJ_DIM = 128`; `tools/voice/repl.py` boots at 64; Witness, Dreamer, the five
   detectors, ethics/trust and value `DEFAULT_CONFIG` are not YAML-wired (a YAML-only retune misses them);
   `ReflectiveLoop.attractor_blend` is stored but never applied.
2. **Single source of truth for width. DONE 2026-10-14.** `FIELD_DIM` in `substrate/dims.py`; `CONFIG["dim"]`,
   every constructor default, `PROJ_DIM` and both voice REPLs read it; the inert YAML `dim:` keys are gone. Guard:
   `tests.doc_accuracy.hardcoded_dim` fails on any field-dim literal elsewhere (verified by reintroducing one).
   Full gate green at 128, so behavior is unchanged. Side fix: `tools/voice/repl.py` used to boot at 64.
3. **Measure before changing. DONE 2026-10-31.** Same seeded workloads at 128, 256 and 768, rule pre-declared,
   no constant changed. Record: [`findings/2026-10-31-dial-census-widths.md`](findings/2026-10-31-dial-census-widths.md).
   The 500-step rule flags many cosine gates. A step-260 cut (the identity-erosion youth window) puts those misses
   in the first half; the settled half still clears them. On these pretrain-off arms the retune that survives the
   cut is the rhythm bands on canonical, where settled energy falls off the 300 explore edge. Embedding init
   missed its ~0.55 target (shifted, not a decision read). Step 4 measured that list; it did not retune it.
4. **Re-tune only what moved. DONE 2026-10-31: no band retune.** Records:
   [`findings/2026-10-31-settled-half-and-f9-gate.md`](findings/2026-10-31-settled-half-and-f9-gate.md),
   [`findings/2026-10-31-pretrained-occupancy.md`](findings/2026-10-31-pretrained-occupancy.md).
   The step-260 split of the seven reads the census left unsplit is done (pretrain-off). Witness
   crystallization still fails in the settled half, canonical sacred promotions thin out after
   step 260, and the canonical metastability count leaves locked/cycling on the settled window.
   Lattice, binding, and the 0.7 pattern cutoff do not: those 500-step drops were youth. The
   not-ship of the bands stands as a record of this pin (cold boot, production `build_engine`,
   canonical workload). July's own probe, run unchanged, reprints dream/reflect/explore within
   ~3% of the 2026-07-06 table; stabilize rose because today's pin allows 1.00 where July
   allowed 0.39. July's table is not stale, and under that instrument the equilibria barely
   move with width, so 5 / 150 / 300 still satisfies the F9 constraint set at 256 and 768.
   Pretrained occupancy (8 epochs, eval, 128 / 256 / 768, seeds 42–44 plus held-out 45/46,
   128 target declared from the 128 fit arms before 256/768 was read) is FAIL (16). The 128
   held-out seeds miss (explore 0.048 vs 0.010, span 0.029), so 256 / 768 are not judged as a
   retune. Independently, 768 explores *more* than 128 pretrained (fit 0.058, held-out 0.121),
   the opposite of the census. 5 / 150 / 300 stays. Co-tuned groups still move together.
   Nothing in this step edits a constant.
5. **The coupling test.** Does the wide field still respond to content the way the 128 field did (correlation of value
   change with content change, directional robustness over seeds)? EmbeddingGemma-300M first, native 768, on July's
   stack whose generator was pretrained 8 epochs at that width (`2026-11-01-embeddinggemma-coupling`). Seeds 42–44.
   Constraints FAIL. Pinned explore, full strength (ALLOW 397/400, boredom 0), settles at 307 / 307 / 311, above the
   pre-declared 303. Dream (~184) stays above 150 and the reflect numbers (~296) stay inside [150, 300), on a pin
   boredom mostly rewrote into explore (235–284 overrides) and on tails that are still climbing. The 0.4× stabilize
   pin is not a degraded measurement: unforced ALLOW was 13/400, the same mix as the unwrapped stabilize pin.
   Coupling FAIL at both widths (r ≈ −0.018). Content switches are real; value strength barely moves, and it moves
   less at a switch than inside a block. The two widths match each other, so this is not a width collapse. The free
   run's last 100 is reflect on every seed; boredom is what runs explore. The formula's proposal, not applied, is
   5 / 138 / 309. 5 / 150 / 300 stays. This does not retract the generator-perception rerun in step 4. RFE's own
   encoder is still its own pass. Nothing in this step edits a constant.
6. **Decode test.** Retrain the small read-out decoder on the new perception and check the read-back carries content,
   not one collapsed word cluster.

## What stays settled

The field locking near 0.998 coherence is **by design** (a long-memory identity integrator; see `STATE.md`). Widening
is not a way to unlock it, and no dial should be retuned to make the field wander. Metastability is read upstream, on
the generator and expression streams. Governance gates every voice, including the system's own. The invariants in
`CLAUDE.md` all still hold at any width.

## Done means

Width lives only in `FIELD_DIM` (done); every width-sensitive dial has a recorded 128-vs-wide measurement and either "unchanged"
or a retune with its finding; the full gate (`run_all_tests.sh`) passes at the new width; the coupling and decode tests
pass with at least one 768 perception.
