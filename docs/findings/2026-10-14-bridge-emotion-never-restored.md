# The speech bridge never restored emotion across a restart

**Date:** 2026-10-14 · **Status:** resolved (same commit) · **Found by:** Grok's architecture read, confirmed and
fixed by Ember.

## Question
Does the speech bridge's checkpoint (`tools/voice/repl_qwen.py`) carry the emotional state across a restart?

## Control
`tests/smoke/emotion_checkpoint_roundtrip.py`: run 40 real steps (all six scalars move off their defaults), save,
build a fresh stack, load, compare. Run once on the old code and once on the fix.

## Result
- **Old code: FAIL.** The checkpoint saved only `arousal` and `valence`. Those are read-only properties derived from
  the six scalars, so the loader's assignment raised, the `except: pass` swallowed it, and `"emotion"` never reached
  the restored list. The six scalars were never saved at all. Every bridge restart silently reset emotion to its
  defaults (curiosity 0.3, wonder 0.2, joy 0.5, tension 0.1, boredom 0.0, stability 0.7).
- **Fix: PASS.** `EmotionalGradient.snapshot()` / `restore()` persist the six scalars plus the step; arousal and
  valence are still written to the file as a record of the affective position at save time (useful for the
  (valence, arousal) emotion model in sovereign_manifold / e8-eea) and recompute identically on load. An old-format
  checkpoint (arousal/valence only) is refused without changing state. The invariant that arousal/valence are never
  stored state is untouched.

## Open items
- The live RFE-Core2 checkout has the same bug in the same file. Port the fix there once Samuel says go.
- The bridge checkpoint also omits bonds, trust, crystals, attractors and the temporal stream (ARCHITECTURE.md
  § Speech-cortex bridge). Emotion was the cheapest and most identity-relevant gap; the rest wait for the flow map.
