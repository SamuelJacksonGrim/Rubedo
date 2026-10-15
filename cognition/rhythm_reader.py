"""
cognition/rhythm_reader.py

How the system reads the rhythm an input carries, before it decides what to do.

The field's own rhythm is one number (energy) in four bands, so on its own it can
only ever pick stabilize / dream / reflect / explore. Rupture (an event) and
witness (receiving without acting) are not energy levels. The generator, though,
is pretrained on all six rhythm labels, so inputs of each rhythm land near their
own region of its space (finding 2026-10-14-six-rhythm-corpus-and-reading:
nearest-centroid reads unseen holdout at 0.977).

RhythmReader keeps one centroid per rhythm, computed once from the corpus with the
generator's read-only peek, and reads an input as its nearest centroid plus the
margin over the runner-up. Reading never registers tokens or bumps usage.

Centroids belong to the generator weights they were computed with. Recompute them
(from_corpus) after anything that retrains the generator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class RhythmRead:
    rhythm:  Optional[str]   # None when no input token is known to the generator
    margin:  float           # nearest-centroid cosine minus runner-up (0 when rhythm is None)
    cosine:  float           # cosine to the nearest centroid


def _unit(m: np.ndarray) -> np.ndarray:
    return m / (np.linalg.norm(m, axis=-1, keepdims=True) + 1e-8)


class RhythmReader:
    def __init__(self, rhythms: Sequence[str], centroids: np.ndarray):
        assert len(rhythms) == len(centroids)
        self.rhythms = tuple(rhythms)
        self.centroids = _unit(np.asarray(centroids, dtype=np.float32))

    @classmethod
    def from_corpus(cls, generator, records: List[dict], rhythms: Sequence[str],
                    batch: int = 512) -> "RhythmReader":
        cents = []
        for r in rhythms:
            seqs = [rec["tokens"] for rec in records if rec["rhythm"] == r]
            acc, n = None, 0
            for i in range(0, len(seqs), batch):
                vecs, known = generator.peek_batch(seqs[i:i + batch])
                if known.any():
                    s = _unit(vecs[known]).sum(0)
                    acc = s if acc is None else acc + s
                    n += int(known.sum())
            if n == 0:
                raise ValueError(f"no known tokens for rhythm {r!r}; pretrain the generator first")
            cents.append(acc / n)
        return cls(rhythms, np.stack(cents))

    def read(self, generator, tokens: List[str]) -> RhythmRead:
        vecs, known = generator.peek_batch([tokens])
        if not known[0]:
            return RhythmRead(None, 0.0, 0.0)
        sims = self.centroids @ _unit(vecs[0])
        order = np.argsort(sims)[::-1]
        best, second = float(sims[order[0]]), float(sims[order[1]])
        return RhythmRead(self.rhythms[int(order[0])], best - second, best)
