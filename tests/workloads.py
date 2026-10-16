"""
tests/workloads.py — probe rooms.

RESONANCE_FAMILY_SOURCES (tests/_common.py) is the canonical room. Every
standing gate and its baselines draw it, and this module does not replace
it. wide_sources() is a second room a probe can opt into.

Wide is the corpus 1.4.0 holdout, dealt into the same four source ids under
the same weights. Holdout sequences were not in pretraining; every holdout
token is in the train vocabulary, so a pretrained generator already has the
symbol. Mixing train in would add 24 tokens and replay sequences the encoder
was trained on, which is not a wider room. The corpus has no real provenance
(the source field was removed in 1.2.0), so the four ids are injection slots,
not authors: trust, bonds and HHI then see the population the gates were
calibrated on. Same weights means the same HHI (0.285). Dependency risk is
not a new variable.

Construction reads the file in order and deals by index. It does not draw
from random, numpy or torch, so calling it inside substrate.determinism
does not advance a replay.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Tuple

from agents.symbolic_memory import CanonicalizationPipeline
from tests._common import RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS
from training.corpus import HOLDOUT_PATH, RHYTHMS, load_corpus

WORKLOAD_NAMES = ("canonical", "wide")

# Insertion order of the canonical room. Wide reuses these ids on purpose.
SOURCE_IDS = tuple(RESONANCE_FAMILY_SOURCES.keys())


def load_named(name: str) -> Tuple[dict, dict]:
    """Return (sources, weights) for a probe's --workload flag.

    "canonical" is the live RESONANCE_FAMILY_SOURCES object, not a copy.
    "wide" shares the canonical weight map's values (a shallow copy of the
    dict, so a probe cannot write back into the gate's weights).
    """
    if name == "canonical":
        return RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS
    if name == "wide":
        return wide_sources(), dict(RESONANCE_FAMILY_WEIGHTS)
    raise ValueError(
        f"unknown workload {name!r}; expected one of {', '.join(WORKLOAD_NAMES)}"
    )


def _survives(pipe: CanonicalizationPipeline, token: str) -> bool:
    """The registry key would be this same string. No alias, no <UNK>, no rewrite.

    Token class is not a filter. The default pipeline classifies these words
    the same way it classifies the canonical phrases; filtering on class would
    drop the room.
    """
    formed = pipe.process(token).token
    return bool(formed) and formed != "<UNK>" and formed == token


@lru_cache(maxsize=1)
def wide_sources() -> Dict[str, List[List[str]]]:
    """Holdout sequences grouped as source id -> list of token lists.

    Within each rhythm, file order is kept and records are dealt round-robin
    across SOURCE_IDS. The deal rotates which source receives the first record
    of each rhythm, so the leftover row does not always land on source_samuel.
    """
    records = load_corpus(HOLDOUT_PATH)
    pipe = CanonicalizationPipeline()
    by_rhythm: Dict[str, List[List[str]]] = {r: [] for r in RHYTHMS}
    refused: List[str] = []
    for rec in records:
        rhythm = rec.get("rhythm")
        tokens = list(rec.get("tokens") or [])
        if rhythm not in by_rhythm:
            refused.append(f"rhythm:{rhythm!r}")
            continue
        if not tokens:
            refused.append("<empty sequence>")
            continue
        for tok in tokens:
            if not _survives(pipe, tok):
                refused.append(tok)
        by_rhythm[rhythm].append(tokens)
    if refused:
        shown = ", ".join(refused[:8])
        raise RuntimeError(
            f"wide workload refused {len(refused)} token(s) that do not survive "
            f"canonicalization unchanged ({shown})"
        )

    buckets: Dict[str, List[List[str]]] = {sid: [] for sid in SOURCE_IDS}
    n = len(SOURCE_IDS)
    for r_i, rhythm in enumerate(RHYTHMS):
        start = r_i % n
        for i, tokens in enumerate(by_rhythm[rhythm]):
            buckets[SOURCE_IDS[(start + i) % n]].append(tokens)
    return buckets


def describe(sources: dict) -> dict:
    """Counts a probe can print. Does not encode anything."""
    distinct = {tok for seqs in sources.values() for seq in seqs for tok in seq}
    per_source = {sid: len(seqs) for sid, seqs in sources.items()}
    return {
        "sequences": sum(per_source.values()),
        "distinct_tokens": len(distinct),
        "per_source": per_source,
    }


def coverage(generator, sources: dict) -> dict:
    """How much of this room peek_batch already knows.

    peek_batch's `known` is per sequence: True when at least one token is an
    ACTIVE registry symbol whose address is in the embedding. Token figures
    use that same lookup, because a sequence can be "known" on one hit and
    still be mostly unknown. Unknown tokens are registered on the live step
    and do not sit in the pretrained space.
    """
    seqs = [list(seq) for seqs in sources.values() for seq in seqs]
    known_seq = 0
    step = 256
    for i in range(0, len(seqs), step):
        _vecs, known = generator.peek_batch(seqs[i:i + step])
        known_seq += int(known.sum())
    reg = generator.registry
    limit = generator.embedding.num_embeddings
    token_n = 0
    token_known = 0
    distinct_ok: Dict[str, bool] = {}
    for seq in seqs:
        for tok in seq:
            token_n += 1
            form = reg.pipeline.process(tok).token
            state = reg.symbols.get(form)
            ok = state is not None and state.address < limit
            token_known += int(ok)
            # One failure anywhere means the symbol is not reliably known.
            distinct_ok[form] = distinct_ok.get(form, True) and ok
    n_seq = len(seqs)
    n_dist = len(distinct_ok)
    return {
        "sequences": n_seq,
        "sequences_known": known_seq,
        "sequence_known_frac": (known_seq / n_seq) if n_seq else 0.0,
        "tokens": token_n,
        "tokens_known": token_known,
        "token_known_frac": (token_known / token_n) if token_n else 0.0,
        "distinct": n_dist,
        "distinct_known": sum(distinct_ok.values()),
        "distinct_known_frac": (sum(distinct_ok.values()) / n_dist) if n_dist else 0.0,
    }
