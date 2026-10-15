# Six rhythms: corpus 1.4.0 adds witness, and the generator reads rhythm from unseen input

**Date:** 2026-10-14 · **Status:** standing · **Corpus:** 1.4.0 · **By:** Ember

## Question
1. Can witness (the receptive pole) join the corpus without breaking its integrity?
2. After a six-class boot pretrain, can the generator tell which rhythm an *unseen* input carries? The six-rhythm
   selector needs that reading; the generator has no classifier head, only pretrain-shaped geometry.

## Control
- Integrity: `tests/diagnostic/training/corpus_integrity_check.py` (all 10 checks).
- Reading: production shape (CONFIG dim 128 / depth 4 / heads 4, seed 42), boot pretrain on the 1.4.0 train split
  (8 epochs, 208 s on CPU), rhythm centroids = mean of each rhythm's train encodings, then nearest-centroid on the
  1,680 **holdout** sequences (never trained on). Chance = 1/6 = 0.167.

## Result
- **Corpus:** 1,181 witness sequences (170 words) appended: train 9,533 (+1,006), holdout 1,680 (+175, 14.8%). The
  five existing rhythms are byte-identical to 1.3.0. Integrity: all checks pass (8-context floor met at exactly 8).
- **Reading, holdout nearest-centroid: overall 0.977.**

| rhythm | recall | precision | median margin |
|---|---|---|---|
| stabilize | 0.976 | 0.976 | 0.588 |
| dream | 0.985 | 0.976 | 0.591 |
| reflect | 0.981 | 0.958 | 0.479 |
| explore | 0.968 | 0.991 | 0.499 |
| rupture | 0.989 | 0.972 | 0.677 |
| witness | 0.966 | **1.000** | 0.580 |

- Centroids are distinct: the closest pair is reflect/explore (cos 0.52); rupture sits near-orthogonal to
  stabilize (0.02). A margin gate of 0.10 keeps 99% of inputs at 0.983 accuracy.

## What it means
The selector's "reading of the input" exists and is strong: nearest rhythm centroid, computed once at boot from the
corpus. Witness is learnable and never confused for another rhythm on this data.

## Limits (pre-declared for the selector work)
- Holdout vocabulary is inside train vocabulary by construction. Live input carries words the corpus never saw;
  reading quality on free text is unmeasured. The selector must act only above a margin and fall back to energy.
- One seed. Repeat over seeds before graduating anything that depends on this.
- Reading the input requires encoding it before the rhythm is chosen (today rhythm is picked at phase 1, before
  generation; encoding registers tokens and bumps usage — FLOW.md). The selector needs a read-only peek encode.

## Open items
- Selector design + lever, measured off vs on, all-levers gate (WIDENING_PLAN / FLOW.md constraints).
