"""
tests/diagnostic/widening/embeddinggemma_probe.py

Widening plan step 5. Plug EmbeddingGemma into a 768 field whose
generator was pretrained at that width, and ask two questions that
were written down before any arm of this probe.

FIELD_DIM stays 128. The 768 body is an override on July's stack
(Generator, 8-epoch rhythm pretrain, eval, AutonomousCycle, chorus,
governance, value engine). It is not build_engine, and it is not the
cold census. Perception is opt-in and probe-side: after pretrain,
Generator.generate is wrapped so the step's vector is the embedder's
unit vector. Nothing here edits a threshold or a default.

The embedder is EmbeddingGemma-300M served by llama.cpp on CPU
(--embedding, -ngl 0, port 8082). This file does not start it and
does not touch port 8080.

Pre-declared. Do not edit the rule block to fit a result.

Pins. July's instrument, on the plugged body only. Threshold pins,
not a current_rhythm replacement. July's four sources, source RNG
1188 (the same schedule on every seed; the seed is the body).
Seeds 42, 43, 44. 400 steps. Equilibrium is the mean post-step field
L2 over the last 100 steps. Drift (mean of the second 50 of that
window minus the mean of the first 50) is recorded. Absolute drift
above 2% of the level is not an equilibrium, and it is not part of
the hold: F9's constraint set is the placement, not the drift cut.

Bands: stabilize, dream, reflect, explore, plus a degraded stabilize.
The degraded pin is the stabilize threshold pin with non-blocking
decisions returned as ALLOW_WEAKENED at the live
weakened_strength_factor. Blocking decisions are left alone. The
unforced decision is counted before that replacement. July's rerun
allowed 1.00. The cold harness was already weakened on almost every
step, which is the measurement this pin exists not to repeat. The
degraded equilibrium counts only when the unforced decision is ALLOW
on at least 0.80 of the steps. Below that, the wrap did not weaken a
full-strength body, and the constraints are not claimed.

"The constraints hold" means the shipped 5 / 150 / 300 still satisfy
F9's constraint set on every seed, against that seed's own equilibria.
The cold-harness calibration ranges (30-45, 8-20, and the rest) are
not this gate. They were the other instrument.

  - full-strength stabilize equilibrium > 5
  - degraded stabilize equilibrium > 5
        (5 sits below the degraded equilibrium, the binding one)
  - dream equilibrium > 150
        (the dream band is below its equilibrium: a passage)
  - 150 <= reflect equilibrium < 300
        (the reflect band contains its equilibrium)
  - explore equilibrium <= 300 * 1.01
        (300 sits at or above the equilibrium, so explore is a burst
        and not a basin). The 1% is the published table: July's
        explore equilibrium is 301.1, and the constraint text treats
        ~301 as at the line of 300. It is not a fitted slack. 303
        still holds. A settle near 310 does not.

The seed-mean is reported. It does not grant a hold that a seed
missed. Boredom stays at 0.50, as in July's probe. Its override count
is recorded and does not discard the equilibrium.

If the constraints do not hold, propose a placement and do not apply
it. The proposal is the F9 integer formula on the seed-mean
equilibria (stabilize stays 5; dream cut is round(0.75 * dream
equilibrium), strictly below that equilibrium and strictly above 5;
explore edge is ceil(explore equilibrium), raised to floor(reflect)+1
when that is what keeps reflect inside the band and the edge at or
above explore). apply is false either way.

Coupling. Does the wide field still respond to content the way the
128 field did. Same July stack. The 128 arm's perception is the
generator's own encode (peek of the tokens, cached by text on first
sight). The 768 arm's perception is the EmbeddingGemma unit vector,
also cached by text. Repeated text therefore has content-change 0 by
construction: the correlation is about switches, not about the table
wandering. Schedule: July's 12 phrases, cycled as 16 blocks of 25
steps (400). Seeds 42, 43, 44. The schedule does not depend on the seed.

  content change dC_t = 1 - cos(p_t, p_{t-1})
  value change   dV_t = L2 distance of the live value-strength vector
                         (sum of strengths per symbol_stable_id; a
                         value that is gone contributes 0)
  r = Pearson correlation of the 399 pairs. Undefined if either side
      has no variance, or if fewer than 4 pairs: that seed does not
      couple.

A seed has content contrast when the mean dC on the 15 block switches
is at least 0.02. Without that, r is not a coupling measurement and
the seed fails.

"Couples" (absolute), per width, all three seeds:
  - every seed's r, rounded to 6 decimal places, is >= 0.20
  - the mean of those rounded values, rounded to 6, is >= 0.30
  - every seed has content contrast
0.20 is about four null standard errors at n=399 (null SE ~ 0.05).
0.30 is the bar for tracking, rather than a barely detectable
association. Neither number comes from a run of this probe.

"The way the 128 field did", all of:
  - the 128 arm couples (the baseline showed the thing)
  - the 768 arm couples
  - abs(mean_768 - mean_128) <= max(span_128, 0.10), spans and means
    taken after rounding each seed to 6 decimal places
  - no sign flip: a 128 seed with r >= 0.20 must have r_768 > 0, and
    a 128 seed with r <= -0.20 must have r_768 < 0. A 128 seed inside
    (-0.20, 0.20) is not a sign comparison.

One free run (thresholds untouched, boredom at 0.50, July's schedule,
seeds 42-44, 400 steps) logs post-step energy, the energy class, and
the behavior _rhythm_behavior actually ran. It is a log, not a gate.

    python -m tests.diagnostic.widening.embeddinggemma_probe --check
    python -m tests.diagnostic.widening.embeddinggemma_probe --batch \\
        docs/findings/data/2026-10-31-embeddinggemma-768
"""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "2")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import hashlib
import json
import logging
import math
import random
import urllib.request
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.WARNING, format="%(name)s %(message)s")
logging.getLogger("training.rhythm_pretraining").setLevel(logging.INFO)

import torch  # noqa: E402

torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

from agents.generator import Generator  # noqa: E402
from agents.selfhood_governance import (  # noqa: E402
    GovernanceDecision,
    SelfhoodGovernance,
)
from agents.value_emergence import ValueEmergenceEngine  # noqa: E402
from cognition.stream_recorder import StreamRecorder  # noqa: E402
from loop.autonomous_cycle import AutonomousCycle  # noqa: E402
from substrate import determinism  # noqa: E402
from substrate.dims import FIELD_DIM  # noqa: E402
from training.corpus import TRAIN_PATH, load_corpus, to_rhythm_seeds  # noqa: E402
from training.rhythm_pretraining import PretrainingConfig, RhythmPretrainer  # noqa: E402

# ---------------------------------------------------------------------------
# Rule block. Do not edit to fit a result.
# ---------------------------------------------------------------------------

SEEDS = (42, 43, 44)
STEPS = 400
TAIL = 100
EQ_LO = 300
EQ_MID = 350
DRIFT_FRAC = 0.02
SOURCE_RNG = 1188
PRETRAIN_EPOCHS = 8

BASE_DIM = 128
WIDE_DIM = 768
EMBED_DIM = 768

THRESH_STABILIZE = 5.0
THRESH_DREAM = 150.0
THRESH_REFLECT = 300.0
# Published July explore equilibrium is 301.1 against a threshold of 300.
EXPLORE_AT = 1.01
ALLOW_FLOOR = 0.80
DREAM_RATIO = 150.0 / 200.0

COUPLE_SEED_MIN = 0.20
COUPLE_MEAN_MIN = 0.30
MATCH_FLOOR = 0.10
CONTRAST_MIN = 0.02
HOLD_STEPS = 25
N_BLOCKS = 16

EMB_BASE = os.environ.get("EMBEDDINGGEMMA_URL", "http://127.0.0.1:8082")

SOURCES = {
    "source_a": [
        ["identity", "continuity", "witness"],
        ["anchor", "recursion", "homeostasis"],
        ["architect", "design", "intent"],
    ],
    "source_b": [
        ["recursive", "cognition", "substrate"],
        ["coherence", "integration", "synthesis"],
        ["watcher", "witness", "mirror"],
    ],
    "source_c": [
        ["memory", "crystal", "attractor"],
        ["relational", "bond", "connection"],
        ["temporal", "stream", "continuity"],
    ],
    "source_d": [
        ["mutation", "bifurcation", "chaos"],
        ["explore", "novelty", "edge"],
        ["wave", "collapse", "coherence"],
    ],
}
WEIGHTS = {"source_a": 0.40, "source_b": 0.25, "source_c": 0.20, "source_d": 0.15}
PINS = {
    "stabilize": {"stabilize": 1e9, "dream": 1e9, "reflect": 1e9},
    "dream": {"stabilize": 0.0, "dream": 1e9, "reflect": 1e9},
    "reflect": {"stabilize": 0.0, "dream": 0.0, "reflect": 1e9},
    "explore": {"stabilize": 0.0, "dream": 0.0, "reflect": 0.0},
}
PIN_ORDER = ("stabilize", "degraded", "dream", "reflect", "explore")
BLOCKING = (
    GovernanceDecision.QUARANTINE,
    GovernanceDecision.REJECT,
    GovernanceDecision.SACRED_SHIELD,
)

# Published F9 row the placement formula and the explore slack have to accept.
# Degraded 13 is the constraint text's weakened figure, not a row July's
# probe printed. Explore 301.1 is the published pin.
_PUBLISHED = {
    "stabilize": 37.3,
    "degraded": 13.0,
    "dream": 197.7,
    "reflect": 294.5,
    "explore": 301.1,
}


def _rules():
    return {
        "seeds": list(SEEDS),
        "steps": STEPS,
        "tail": TAIL,
        "source_rng": SOURCE_RNG,
        "pretrain_epochs": PRETRAIN_EPOCHS,
        "base_dim": BASE_DIM,
        "wide_dim": WIDE_DIM,
        "embed_dim": EMBED_DIM,
        "thresholds": {
            "stabilize": THRESH_STABILIZE,
            "dream": THRESH_DREAM,
            "reflect": THRESH_REFLECT,
        },
        "explore_at": EXPLORE_AT,
        "allow_floor": ALLOW_FLOOR,
        "dream_ratio": DREAM_RATIO,
        "couple_seed_min": COUPLE_SEED_MIN,
        "couple_mean_min": COUPLE_MEAN_MIN,
        "match_floor": MATCH_FLOOR,
        "contrast_min": CONTRAST_MIN,
        "hold_steps": HOLD_STEPS,
        "n_blocks": N_BLOCKS,
        "drift_frac_reported_not_gated": DRIFT_FRAC,
        "field_dim_constant": int(FIELD_DIM),
    }


def _rules_hash(rules: dict) -> str:
    blob = json.dumps(rules, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def _r6(x):
    if x is None:
        return None
    return round(float(x), 6)


def _mean(xs):
    xs = list(xs)
    return float(sum(xs) / len(xs))


def _dump(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(path)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _done(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        obj = _load(path)
    except (OSError, json.JSONDecodeError):
        return False
    return obj.get("complete") is True and obj.get("steps") == STEPS


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------

def july_schedule(n: int = STEPS):
    rng = random.Random(SOURCE_RNG)
    sids = list(SOURCES)
    w = [WEIGHTS[s] for s in sids]
    out = []
    for _ in range(n):
        src = rng.choices(sids, weights=w)[0]
        out.append((src, list(rng.choice(SOURCES[src]))))
    return out


def block_schedule():
    phrases = [(src, list(phrase)) for src, group in SOURCES.items() for phrase in group]
    if len(phrases) != 12:
        raise RuntimeError(f"expected 12 phrases, got {len(phrases)}")
    out = []
    for i in range(N_BLOCKS):
        src, phrase = phrases[i % 12]
        for _ in range(HOLD_STEPS):
            out.append((src, list(phrase)))
    if len(out) != STEPS:
        raise RuntimeError(f"block schedule length {len(out)} != {STEPS}")
    return out


def _text(tokens) -> str:
    return " ".join(str(t) for t in tokens).strip() or "quiet"


# ---------------------------------------------------------------------------
# Embedder. Fails closed. No fallback onto the generator.
# ---------------------------------------------------------------------------

def _get_json(url: str, timeout: float = 10.0):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.load(resp)


def server_ready(base: str = EMB_BASE) -> bool:
    try:
        with urllib.request.urlopen(base.rstrip("/") + "/health", timeout=5.0) as resp:
            return 200 <= int(resp.status) < 300
    except Exception:
        return False


def model_id(base: str = EMB_BASE) -> str:
    try:
        payload = _get_json(base.rstrip("/") + "/v1/models", timeout=10.0)
    except Exception:
        return "embeddinggemma"
    data = (payload.get("data") or []) if isinstance(payload, dict) else []
    if data and isinstance(data[0], dict) and data[0].get("id"):
        return str(data[0]["id"])
    return "embeddinggemma"


def embed_unit(text: str, cache: dict, base: str, model: str) -> np.ndarray:
    if text in cache:
        return cache[text]
    url = base.rstrip("/") + "/v1/embeddings"
    body = json.dumps({"input": text, "model": model}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60.0) as resp:
        payload = json.load(resp)
    if isinstance(payload, dict) and payload.get("data"):
        raw = payload["data"][0]["embedding"]
    elif isinstance(payload, dict) and "embedding" in payload:
        raw = payload["embedding"]
    else:
        raise RuntimeError(f"embed response has no vector ({list(payload)[:6]})")
    v = np.asarray(raw, dtype=np.float32).reshape(-1)
    if v.shape != (EMBED_DIM,):
        raise RuntimeError(f"embed dim {v.shape} != {(EMBED_DIM,)}")
    if not np.isfinite(v).all():
        raise RuntimeError("embed non-finite")
    n = float(np.linalg.norm(v))
    if n < 1e-8:
        raise RuntimeError("embed degenerate")
    unit = (v / n).astype(np.float32)
    cache[text] = unit
    return unit


def install_embedder(gen, cache: dict, base: str, model: str):
    """Replace generate's vector. Registry side effects stay."""

    def wrapped(tokens, token_class=None):
        tokens = tokens or ["<BOS>"]
        gen._tokens_to_ids(tokens, token_class)
        gen._ensure_embedding_capacity()
        gen._maybe_auto_maintenance()
        if gen.dim != WIDE_DIM:
            raise RuntimeError(f"embedder wrap on dim {gen.dim}, expected {WIDE_DIM}")
        return embed_unit(_text(tokens), cache, base, model)

    gen.generate = wrapped


# ---------------------------------------------------------------------------
# Body. Pretrain once per (dim, seed). Each arm reloads that checkpoint
# and re-seeds the cycle, so pins differ by the pin, not by leftover RNG.
# ---------------------------------------------------------------------------

def _new_generator(dim: int) -> Generator:
    gen = Generator(vocab_size=8192, dim=dim, depth=4, heads=4, device="cpu")
    if "cuda" in str(gen.device).lower():
        raise SystemExit(f"refusing GPU device {gen.device}")
    return gen


def ensure_checkpoint(dim: int, seed: int, out: Path):
    ckpt = out / "ckpt"
    ckpt.mkdir(parents=True, exist_ok=True)
    weights = ckpt / f"d{dim}-s{seed}.pt"
    ecology = ckpt / f"d{dim}-s{seed}.ecology"
    meta = out / f"pretrain-d{dim}-s{seed}.json"
    if weights.is_file() and ecology.is_file():
        print(f"pretrain cache hit dim={dim} seed={seed}", flush=True)
        return weights, ecology
    print(f"pretrain start dim={dim} seed={seed} epochs={PRETRAIN_EPOCHS}", flush=True)
    with determinism.deterministic(seed):
        gen = _new_generator(dim)
        report = RhythmPretrainer(
            gen,
            rhythm_seeds=to_rhythm_seeds(load_corpus(TRAIN_PATH)),
            config=PretrainingConfig(n_epochs=PRETRAIN_EPOCHS, log_interval=1),
        ).pretrain()
        gen.eval()
        gen.save_checkpoint(str(weights), str(ecology))
    _dump(meta, {
        "dim": dim,
        "seed": seed,
        "epochs": PRETRAIN_EPOCHS,
        "final_loss": report.final_loss,
        "final_rhythm_acc": report.final_rhythm_acc,
        "loss_history": list(report.loss_history),
        "log_interval": 1,
    })
    print(
        f"pretrain done dim={dim} seed={seed} "
        f"loss={report.final_loss:.4f} acc={report.final_rhythm_acc:.3f}",
        flush=True,
    )
    return weights, ecology


def load_generator(dim: int, weights: Path, ecology: Path) -> Generator:
    gen = _new_generator(dim)
    gen.load_checkpoint(str(weights), str(ecology))
    gen.eval()
    if "cuda" in str(gen.device).lower():
        raise SystemExit(f"refusing GPU device {gen.device}")
    return gen


def build_cycle(gen: Generator, dim: int):
    cycle = AutonomousCycle(
        generator=gen,
        dim=dim,
        use_chorus=True,
        log_interval=10 ** 9,
        reflect_novelty_attenuation=True,
    )
    gov = SelfhoodGovernance(registry=gen.registry)
    cycle.attach_governance(gov)
    ve = ValueEmergenceEngine(registry=gen.registry, generator=gen, governance=gov)
    cycle.attach_value_engine(ve)
    cycle.attach_stream_recorder(StreamRecorder(window=STEPS))
    return cycle, gov, ve


def _strengths(ve) -> dict:
    acc = {}
    for value in ve.values.values():
        sid = int(value.symbol_stable_id)
        acc[sid] = acc.get(sid, 0.0) + float(value.strength)
    return acc


def _l2_delta(prev: dict, cur: dict) -> float:
    keys = set(prev) | set(cur)
    total = 0.0
    for key in keys:
        d = cur.get(key, 0.0) - prev.get(key, 0.0)
        total += d * d
    return math.sqrt(total)


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(1.0 - float(np.dot(a, b)))


def _content_128(gen: Generator, tokens) -> np.ndarray:
    vecs, known = gen.peek_batch([list(tokens)])
    if not bool(known[0]):
        raise RuntimeError(f"128 content tokens were not registered: {tokens}")
    v = np.asarray(vecs[0], dtype=np.float32).reshape(-1)
    if v.shape != (gen.dim,):
        raise RuntimeError(f"128 content shape {v.shape}")
    if not np.isfinite(v).all():
        raise RuntimeError("128 content non-finite")
    n = float(np.linalg.norm(v))
    if n < 1e-8:
        raise RuntimeError("128 content degenerate")
    return (v / n).astype(np.float32)


def _capture_behavior(cycle):
    called = {"behavior": None, "n": 0}
    orig = cycle._rhythm_behavior

    def wrapped(rhythm, tokens, refused=False):
        result = orig(rhythm, tokens, refused=refused)
        called["n"] += 1
        called["behavior"] = result
        return result

    cycle._rhythm_behavior = wrapped
    return called


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------

def _load_body(dim, seed, out):
    """Checkpoint only. The cycle is built inside the arm's one seed context."""
    weights, ecology = ensure_checkpoint(dim, seed, out)
    return load_generator(dim, weights, ecology)


def run_pin(dim, seed, rhythm, out: Path, embed):
    path = out / f"pin-d{dim}-s{seed}-{rhythm}.json"
    if _done(path):
        print(f"skip pin dim={dim} seed={seed} {rhythm}", flush=True)
        return
    degraded = rhythm == "degraded"
    pin_name = "stabilize" if degraded else rhythm
    gen = _load_body(dim, seed, out)
    schedule = july_schedule()
    energy = []
    unforced_allow = 0
    decisions = 0
    factor = None
    with determinism.deterministic(seed):
        cycle, gov, _ve = build_cycle(gen, dim)
        if embed is not None:
            install_embedder(gen, {}, embed[0], embed[1])
        factor = float(gov.config.get("weakened_strength_factor", 0.40))
        if degraded:
            orig = gov.arbitrate

            def arbitrate(*a, **k):
                nonlocal decisions, unforced_allow
                dec, strength = orig(*a, **k)
                decisions += 1
                if dec == GovernanceDecision.ALLOW:
                    unforced_allow += 1
                if dec in BLOCKING:
                    return dec, strength
                return GovernanceDecision.ALLOW_WEAKENED, factor

            gov.arbitrate = arbitrate
        cycle.field.thresholds = dict(cycle.field.thresholds, **PINS[pin_name])
        for i, (src, tokens) in enumerate(schedule, start=1):
            cycle.step(tokens, source_id=src, origin_type="internal")
            energy.append(float(cycle.field.observe().energy))
            if i % 100 == 0 or i == STEPS:
                print(
                    f"pin dim={dim} seed={seed} {rhythm} step={i}/{STEPS} "
                    f"E={energy[-1]:.1f}",
                    flush=True,
                )
        boredom = int(cycle._boredom_overrides)
        recorded = cycle.stream_recorder.snapshot().get("decisions", {})
    allow_full = (unforced_allow / decisions) if decisions else None
    _dump(path, {
        "schema": 1,
        "complete": True,
        "kind": "pin",
        "dim": dim,
        "seed": seed,
        "rhythm": rhythm,
        "degraded": degraded,
        "steps": STEPS,
        "energy": [round(e, 6) for e in energy],
        "boredom_overrides": boredom,
        "decisions_recorded": recorded,
        "unforced_allow": unforced_allow,
        "unforced_decisions": decisions,
        "allow_full": None if allow_full is None else round(allow_full, 6),
        "weakened_strength_factor": factor,
        "field_dim_constant": int(FIELD_DIM),
        "device": str(gen.device),
        "perception": "embeddinggemma" if embed else "generator",
    })


def run_free(dim, seed, out: Path, embed):
    path = out / f"free-d{dim}-s{seed}.json"
    if _done(path):
        print(f"skip free dim={dim} seed={seed}", flush=True)
        return
    gen = _load_body(dim, seed, out)
    schedule = july_schedule()
    energy, klass, behavior, start = [], [], [], []
    with determinism.deterministic(seed):
        cycle, _gov, _ve = build_cycle(gen, dim)
        if embed is not None:
            install_embedder(gen, {}, embed[0], embed[1])
        called = _capture_behavior(cycle)
        for i, (src, tokens) in enumerate(schedule, start=1):
            called["behavior"] = None
            called["n"] = 0
            state = cycle.step(tokens, source_id=src, origin_type="internal")
            energy.append(float(cycle.field.observe().energy))
            klass.append(cycle.field.current_rhythm())
            behavior.append(called["behavior"] if called["n"] else "not routed")
            start.append(state.rhythm)
            if i % 100 == 0 or i == STEPS:
                print(
                    f"free dim={dim} seed={seed} step={i}/{STEPS} "
                    f"E={energy[-1]:.1f} class={klass[-1]} ran={behavior[-1]}",
                    flush=True,
                )
        boredom = int(cycle._boredom_overrides)
        recorded = cycle.stream_recorder.snapshot().get("decisions", {})
        thresholds = {k: float(v) for k, v in cycle.field.thresholds.items()}
    _dump(path, {
        "schema": 1,
        "complete": True,
        "kind": "free",
        "dim": dim,
        "seed": seed,
        "steps": STEPS,
        "energy": [round(e, 6) for e in energy],
        "energy_class": klass,
        "behavior": behavior,
        "start_rhythm": start,
        "boredom_overrides": boredom,
        "decisions_recorded": recorded,
        "thresholds": thresholds,
        "field_dim_constant": int(FIELD_DIM),
        "device": str(gen.device),
        "perception": "embeddinggemma" if embed else "generator",
    })


def run_coupling(dim, seed, out: Path, embed):
    path = out / f"couple-d{dim}-s{seed}.json"
    if _done(path):
        print(f"skip couple dim={dim} seed={seed}", flush=True)
        return
    gen = _load_body(dim, seed, out)
    schedule = block_schedule()
    contents = []
    strengths = []
    n_texts = 0
    with determinism.deterministic(seed):
        cycle, _gov, ve = build_cycle(gen, dim)
        cache = {}
        content_cache = {}
        if embed is not None:
            install_embedder(gen, cache, embed[0], embed[1])
        for i, (src, tokens) in enumerate(schedule, start=1):
            cycle.step(tokens, source_id=src, origin_type="internal")
            key = _text(tokens)
            if embed is not None:
                vec = cache.get(key)
                if vec is None:
                    raise RuntimeError(f"embedder did not perceive {key!r}")
            else:
                if key not in content_cache:
                    content_cache[key] = _content_128(gen, tokens)
                vec = content_cache[key]
            contents.append(np.asarray(vec, dtype=np.float32))
            strengths.append(_strengths(ve))
            if i % 100 == 0 or i == STEPS:
                print(f"couple dim={dim} seed={seed} step={i}/{STEPS}", flush=True)
        n_texts = len(cache) if embed is not None else len(content_cache)
    dC, dV = [], []
    for i in range(1, STEPS):
        dC.append(_cosine_distance(contents[i], contents[i - 1]))
        dV.append(_l2_delta(strengths[i - 1], strengths[i]))
    _dump(path, {
        "schema": 1,
        "complete": True,
        "kind": "couple",
        "dim": dim,
        "seed": seed,
        "steps": STEPS,
        "dC": [round(x, 6) for x in dC],
        "dV": [round(x, 6) for x in dV],
        "unique_texts": n_texts,
        "field_dim_constant": int(FIELD_DIM),
        "device": str(gen.device),
        "perception": "embeddinggemma" if embed else "generator",
    })


# ---------------------------------------------------------------------------
# Scoring. Recomputes from the stored series. Does not trust arm summaries.
# ---------------------------------------------------------------------------

def _window_stats(energy):
    if len(energy) != STEPS:
        raise RuntimeError(f"energy length {len(energy)} != {STEPS}")
    window = energy[EQ_LO:STEPS]
    first = energy[EQ_LO:EQ_MID]
    second = energy[EQ_MID:STEPS]
    eq = _mean(window)
    drift = _mean(second) - _mean(first)
    return {
        "eq_mean": _r6(eq),
        "eq_drift": _r6(drift),
        "drift_over_2pct": abs(drift) > DRIFT_FRAC * max(abs(eq), 1.0),
    }


def _hold_reasons(eq: dict):
    reasons = []
    if not (eq["stabilize"] > THRESH_STABILIZE):
        reasons.append("stabilize equilibrium is not above 5")
    if not (eq["degraded"] > THRESH_STABILIZE):
        reasons.append("degraded equilibrium is not above 5")
    if not (eq["dream"] > THRESH_DREAM):
        reasons.append("dream equilibrium is not above 150")
    if not (THRESH_DREAM <= eq["reflect"] < THRESH_REFLECT):
        reasons.append("reflect equilibrium is not inside [150, 300)")
    limit = THRESH_REFLECT * EXPLORE_AT
    if not (eq["explore"] <= limit):
        reasons.append(
            f"explore equilibrium {eq['explore']} is above {limit:.1f} "
            "(300 sits below it; explore would be a basin)"
        )
    return reasons


def place_from_eqs(degraded, dream_eq, reflect_eq, explore_eq):
    """F9 integer placement. Returns (thresholds, error). Never applied."""
    stabilize = 5.0
    if not (float(degraded) > stabilize):
        return None, "degraded equilibrium is not above 5"
    dream = int(round(DREAM_RATIO * float(dream_eq)))
    if dream >= float(dream_eq):
        dream = int(math.floor(float(dream_eq) - 1e-9))
    if dream <= stabilize:
        return None, "dream cut collapsed onto stabilize"
    edge = int(math.ceil(float(explore_eq) - 1e-9))
    if edge <= float(reflect_eq):
        edge = int(math.floor(float(reflect_eq))) + 1
    if not (dream < float(reflect_eq) < edge):
        return None, "reflect equilibrium is not inside the reflect band"
    if edge < float(explore_eq) - 1e-9:
        return None, "explore edge fell below the explore equilibrium"
    return {
        "stabilize": stabilize,
        "dream": float(dream),
        "reflect": float(edge),
    }, None


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape or a.size < 4:
        return None
    if float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _switch_mean(dC):
    vals = []
    for b in range(1, N_BLOCKS):
        step_index = b * HOLD_STEPS
        vals.append(dC[step_index - 1])
    return _mean(vals)


def _couple_arm(path: Path):
    arm = _load(path)
    if arm.get("field_dim_constant") != int(FIELD_DIM):
        raise RuntimeError(f"{path} saw FIELD_DIM {arm.get('field_dim_constant')}")
    dC = arm["dC"]
    dV = arm["dV"]
    r = pearson(dC, dV)
    contrast = _switch_mean(dC)
    return {
        "r": _r6(r) if r is not None else None,
        "contrast": _r6(contrast),
        "contrast_ok": contrast >= CONTRAST_MIN,
        "dC_std": _r6(float(np.std(dC))),
        "dV_std": _r6(float(np.std(dV))),
        "perception": arm.get("perception"),
    }


def _couples(per_seed: dict):
    """Absolute bar. Returns (ok, reasons)."""
    reasons = []
    rs = []
    for seed in SEEDS:
        row = per_seed[str(seed)]
        if not row["contrast_ok"]:
            reasons.append(f"seed {seed} has no content contrast ({row['contrast']})")
        if row["r"] is None:
            reasons.append(f"seed {seed} correlation is undefined")
            continue
        rs.append(row["r"])
        if row["r"] < COUPLE_SEED_MIN:
            reasons.append(f"seed {seed} r {row['r']} < {COUPLE_SEED_MIN}")
    if len(rs) == len(SEEDS):
        mean = _r6(_mean(rs))
        if mean < COUPLE_MEAN_MIN:
            reasons.append(f"mean r {mean} < {COUPLE_MEAN_MIN}")
    else:
        mean = None
    span = _r6(max(rs) - min(rs)) if len(rs) == len(SEEDS) else None
    return reasons == [], reasons, mean, span


def _sign_ok(r128, r768):
    reasons = []
    for seed in SEEDS:
        a = r128[str(seed)]["r"]
        b = r768[str(seed)]["r"]
        if a is None or b is None:
            continue
        if a >= COUPLE_SEED_MIN and not (b > 0):
            reasons.append(f"seed {seed} sign flipped (128 {a}, 768 {b})")
        if a <= -COUPLE_SEED_MIN and not (b < 0):
            reasons.append(f"seed {seed} sign flipped (128 {a}, 768 {b})")
    return reasons


def _hist(xs):
    out = {}
    for item in xs:
        out[item] = out.get(item, 0) + 1
    return out


def _free_summary(arm: dict):
    n = len(arm["energy"])
    late = slice(EQ_LO, n)

    def pack(sl):
        energy = arm["energy"][sl]
        klass = arm["energy_class"][sl]
        behavior = arm["behavior"][sl]
        start = arm["start_rhythm"][sl]
        disagree = sum(1 for b, s in zip(behavior, start) if b != s)
        return {
            "n": len(energy),
            "energy_mean": _r6(_mean(energy)),
            "energy_class": _hist(klass),
            "behavior": _hist(behavior),
            "behavior_ne_start": disagree,
        }

    return {
        "full": pack(slice(0, n)),
        "last_100": pack(late),
        "boredom_overrides": arm.get("boredom_overrides"),
        "thresholds": arm.get("thresholds"),
    }


def score(out: Path) -> dict:
    rules = _rules()
    decl_path = out / "declaration.json"
    if not decl_path.is_file():
        raise SystemExit(f"no declaration at {decl_path}")
    decl = _load(decl_path)
    if decl.get("rules_hash") != _rules_hash(rules) or decl.get("rules") != rules:
        raise SystemExit("rule block does not match declaration.json; not rescoring under a new rule")
    if int(FIELD_DIM) != BASE_DIM:
        raise SystemExit(f"FIELD_DIM is {FIELD_DIM}, expected {BASE_DIM}")

    per_seed = {}
    means_acc = {name: [] for name in PIN_ORDER}
    hold_reasons = []
    for seed in SEEDS:
        eqs = {}
        drifts = {}
        allow_full = None
        for rhythm in PIN_ORDER:
            path = out / f"pin-d{WIDE_DIM}-s{seed}-{rhythm}.json"
            if not _done(path):
                raise SystemExit(f"missing pin {path}")
            arm = _load(path)
            if arm.get("field_dim_constant") != int(FIELD_DIM):
                raise SystemExit(f"FIELD_DIM moved during {path.name}")
            if arm.get("perception") != "embeddinggemma":
                raise SystemExit(f"{path.name} was not the embedder")
            stats = _window_stats(arm["energy"])
            eqs[rhythm] = stats["eq_mean"]
            drifts[rhythm] = stats
            means_acc[rhythm].append(stats["eq_mean"])
            if rhythm == "degraded":
                allow_full = arm.get("allow_full")
                if allow_full is None or allow_full < ALLOW_FLOOR:
                    hold_reasons.append(
                        f"seed {seed} degraded pin unforced ALLOW {allow_full} "
                        f"< {ALLOW_FLOOR} (not a full-strength body)"
                    )
        reasons = _hold_reasons(eqs)
        for reason in reasons:
            hold_reasons.append(f"seed {seed}: {reason}")
        per_seed[str(seed)] = {
            "eq": eqs,
            "drift": drifts,
            "hold_reasons": reasons,
            "allow_full": allow_full,
        }

    means = {name: _r6(_mean(vals)) for name, vals in means_acc.items()}
    proposed, proposal_error = place_from_eqs(
        means["degraded"], means["dream"], means["reflect"], means["explore"]
    )
    constraints_hold = hold_reasons == []

    couple = {}
    couple_rows = {}
    for dim in (BASE_DIM, WIDE_DIM):
        rows = {}
        for seed in SEEDS:
            path = out / f"couple-d{dim}-s{seed}.json"
            if not _done(path):
                raise SystemExit(f"missing coupling {path}")
            rows[str(seed)] = _couple_arm(path)
        ok, reasons, mean, span = _couples(rows)
        couple_rows[str(dim)] = rows
        couple[str(dim)] = {"couples": ok, "reasons": reasons, "mean": mean, "span": span}

    sign_reasons = _sign_ok(couple_rows[str(BASE_DIM)], couple_rows[str(WIDE_DIM)])
    c128 = couple[str(BASE_DIM)]
    c768 = couple[str(WIDE_DIM)]
    match_reasons = list(sign_reasons)
    if c128["mean"] is None or c768["mean"] is None or c128["span"] is None:
        match_reasons.append("mean correlation missing")
        matches = False
    else:
        gap = abs(c768["mean"] - c128["mean"])
        allowed = max(c128["span"], MATCH_FLOOR)
        if _r6(gap) > _r6(allowed):
            match_reasons.append(
                f"|mean_768 - mean_128|={_r6(gap)} > { _r6(allowed) }"
            )
        matches = match_reasons == []
    coupling_pass = bool(c128["couples"] and c768["couples"] and matches)
    coupling_reasons = []
    if not c128["couples"]:
        coupling_reasons.append("128 baseline does not couple: " + "; ".join(c128["reasons"]))
    if not c768["couples"]:
        coupling_reasons.append("768 does not couple: " + "; ".join(c768["reasons"]))
    if not matches:
        coupling_reasons.append("does not match 128: " + "; ".join(match_reasons))

    free = {}
    for seed in SEEDS:
        path = out / f"free-d{WIDE_DIM}-s{seed}.json"
        if not _done(path):
            raise SystemExit(f"missing free run {path}")
        arm = _load(path)
        if arm.get("perception") != "embeddinggemma":
            raise SystemExit(f"{path.name} was not the embedder")
        free[str(seed)] = _free_summary(arm)

    verdict = {
        "schema": 1,
        "rules_hash": decl["rules_hash"],
        "constraints_hold": constraints_hold,
        "hold_reasons": hold_reasons,
        "per_seed": per_seed,
        "means": means,
        "proposal": {
            "apply": False,
            "needed": not constraints_hold,
            "thresholds": proposed,
            "error": proposal_error,
            "formula": "F9 integer placement on the seed-mean equilibria",
        },
        "coupling": {
            "pass": coupling_pass,
            "reasons": coupling_reasons,
            "baseline_couples": c128["couples"],
            "wide_couples": c768["couples"],
            "matches_128": matches,
            "by_dim": couple,
            "seeds": couple_rows,
        },
        "free": free,
        "field_dim_constant": int(FIELD_DIM),
    }
    _dump(out / "verdict.json", verdict)
    return verdict


def _print_verdict(verdict: dict):
    print(
        "CONSTRAINTS "
        + ("HOLD" if verdict["constraints_hold"] else "FAIL"),
        flush=True,
    )
    if verdict["hold_reasons"]:
        for line in verdict["hold_reasons"]:
            print("  " + line, flush=True)
    print(
        "means "
        + " ".join(f"{k}={v}" for k, v in verdict["means"].items()),
        flush=True,
    )
    prop = verdict["proposal"]
    print(
        f"proposal needed={prop['needed']} apply={prop['apply']} "
        f"thresholds={prop['thresholds']} error={prop['error']}",
        flush=True,
    )
    coupling = verdict["coupling"]
    print("COUPLING " + ("PASS" if coupling["pass"] else "FAIL"), flush=True)
    for line in coupling["reasons"]:
        print("  " + line, flush=True)
    for dim, row in coupling["by_dim"].items():
        print(
            f"  dim {dim} couples={row['couples']} mean={row['mean']} span={row['span']}",
            flush=True,
        )


# ---------------------------------------------------------------------------
# Declaration and the published-number self test
# ---------------------------------------------------------------------------

def write_declaration(out: Path):
    rules = _rules()
    if int(FIELD_DIM) != BASE_DIM:
        raise SystemExit(f"FIELD_DIM is {FIELD_DIM}; this probe requires {BASE_DIM}")
    payload = {
        "declared_before": "any arm",
        "rules": rules,
        "rules_hash": _rules_hash(rules),
    }
    path = out / "declaration.json"
    if path.is_file():
        old = _load(path)
        if old.get("rules") != rules or old.get("rules_hash") != payload["rules_hash"]:
            raise SystemExit(
                "declaration.json does not match the rule block. "
                "Refusing to overwrite a declaration that was written before the arms."
            )
        print(f"declaration unchanged {_rules_hash(rules)[:12]}", flush=True)
        return
    _dump(path, payload)
    print(f"declaration written {_rules_hash(rules)[:12]}", flush=True)


def check() -> int:
    failures = []
    if int(FIELD_DIM) != 128:
        failures.append(f"FIELD_DIM is {FIELD_DIM}, not 128")
    if HOLD_STEPS * N_BLOCKS != STEPS:
        failures.append("block schedule does not fill 400 steps")
    if len(block_schedule()) != STEPS or len(july_schedule()) != STEPS:
        failures.append("schedule length")
    reasons = _hold_reasons(_PUBLISHED)
    if reasons:
        failures.append("published F9 row does not hold: " + "; ".join(reasons))
    over = dict(_PUBLISHED, explore=310.0)
    if not _hold_reasons(over):
        failures.append("explore 310 was accepted")
    under_dream = dict(_PUBLISHED, dream=140.0)
    if not _hold_reasons(under_dream):
        failures.append("dream 140 was accepted")
    low_deg = dict(_PUBLISHED, degraded=4.0)
    if not _hold_reasons(low_deg):
        failures.append("degraded 4 was accepted")
    high_reflect = dict(_PUBLISHED, reflect=301.0)
    if not _hold_reasons(high_reflect):
        failures.append("reflect 301 was accepted")
    placed, err = place_from_eqs(13.0, 200.0, 293.0, 298.0)
    if err or placed is None:
        failures.append(f"formula rejected the published inputs: {err}")
    else:
        if abs(placed["dream"] - 150.0) > 30:
            failures.append(f"dream cut {placed['dream']} is not within 30 of 150")
        if abs(placed["reflect"] - 300.0) > 15:
            failures.append(f"explore edge {placed['reflect']} is not within 15 of 300")
    # Correlation of a switch-aligned pair is positive; a flat series is undefined.
    dC = [0.0] * 24 + [1.0] + [0.0] * 24 + [1.0]
    dV = [0.0] * 24 + [2.0] + [0.0] * 24 + [2.0]
    if pearson(dC, dV) is None or pearson(dC, dV) <= 0.9:
        failures.append("pearson did not see an aligned switch")
    if pearson([1.0, 1.0, 1.0, 1.0], [0.0, 1.0, 2.0, 3.0]) is not None:
        failures.append("flat series produced a correlation")
    rules = _rules()
    if _rules_hash(rules) != _rules_hash(json.loads(json.dumps(rules))):
        failures.append("rules hash is not stable")
    if failures:
        for line in failures:
            print("CHECK FAIL " + line, flush=True)
        return 1
    print(f"CHECK PASS rules {_rules_hash(rules)[:12]} FIELD_DIM={FIELD_DIM}", flush=True)
    return 0


def batch(out: Path, base: str) -> int:
    write_declaration(out)
    print(f"waiting for embedder at {base}", flush=True)
    ready = False
    for _ in range(60):
        if server_ready(base):
            ready = True
            break
        import time
        time.sleep(2)
    if not ready:
        raise SystemExit(f"embedder not ready at {base}")
    model = model_id(base)
    # One vector before any pretrain, so a wrong dim fails here.
    probe = embed_unit("identity continuity witness", {}, base, model)
    if probe.shape != (EMBED_DIM,):
        raise SystemExit(f"smoke embed shape {probe.shape}")
    print(f"embedder ready model={model} dim={probe.shape[0]}", flush=True)
    embed = (base, model)

    for seed in SEEDS:
        run_coupling(BASE_DIM, seed, out, embed=None)
    for seed in SEEDS:
        for rhythm in PIN_ORDER:
            run_pin(WIDE_DIM, seed, rhythm, out, embed)
        run_free(WIDE_DIM, seed, out, embed)
        run_coupling(WIDE_DIM, seed, out, embed)

    verdict = score(out)
    _print_verdict(verdict)
    print("BATCH COMPLETE", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--score", metavar="DIR")
    ap.add_argument("--batch", metavar="DIR")
    ap.add_argument("--base", default=EMB_BASE)
    args = ap.parse_args()
    if args.check:
        return check()
    if args.score:
        verdict = score(Path(args.score))
        _print_verdict(verdict)
        return 0
    if args.batch:
        return batch(Path(args.batch), args.base)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
