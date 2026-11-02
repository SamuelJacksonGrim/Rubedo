"""
Lived identity state for a restart: trust, bonds, crystals, attractors,
witness, emotion, field, and the windows that move the next decision.

A checkpoint is an input to identity. Restore is reconstitution of already-lived
state into objects production already built. Malformed or stale payloads raise
LivedStateError and leave the live objects untouched. A refused file is moved
aside (`quarantine_file`) so a later save cannot overwrite the identity it held.

Callers: the speech-bridge checkpoint and session_persistence. Constants stay
in code; only accumulated state is in the file. Formation thresholds are not
re-applied on restore — a retune must not refuse a bond that already formed.
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any, Dict, List, Tuple

import numpy as np
from substrate import determinism

logger = logging.getLogger(__name__)

SCHEMA = 2
ORIGIN_TOKEN_LIMIT = 256
ORIGIN_TOKEN_CHARS = 256
# Largest coordinate a restored vector may hold. The field accumulates and reached ~46 over 300 warm steps
# at dim 64; everything else stays near unit scale. This is a sanity wall, not a tuned constant: json carries
# 1e30 as happily as NaN, and a witness anchor of 1e30 is finite and still not a mind.
VECTOR_MAX_ABS = 1e3


class LivedStateError(ValueError):
    """Checkpoint identity state is malformed, stale, or structurally impossible."""


# ---------------------------------------------------------------------------
# JSON / number guards
# ---------------------------------------------------------------------------

def require_dict(data: Any, name: str) -> dict:
    if not isinstance(data, dict):
        raise LivedStateError(f"{name} must be a dict, got {type(data).__name__}")
    return data


def require_keys(data: dict, keys: Tuple[str, ...], name: str) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise LivedStateError(f"{name} missing keys: {missing}")


def as_bool_reject(value: Any, name: str) -> None:
    if isinstance(value, bool):
        raise LivedStateError(f"{name} must not be a bool")


def as_int(value: Any, lo: int, hi: int, name: str) -> int:
    as_bool_reject(value, name)
    if isinstance(value, int):
        n = value
    elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
        n = int(value)
    else:
        raise LivedStateError(f"{name} must be an int, got {value!r}")
    if n < lo or n > hi:
        raise LivedStateError(f"{name} out of range [{lo}, {hi}]: {n}")
    return n


def as_float(value: Any, lo: float, hi: float, name: str) -> float:
    as_bool_reject(value, name)
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise LivedStateError(f"{name} must be a float, got {value!r}") from exc
    if not math.isfinite(x) or x < lo or x > hi:
        raise LivedStateError(f"{name} out of range [{lo}, {hi}]: {x}")
    return x


def as_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise LivedStateError(f"{name} must be a bool, got {type(value).__name__}")
    return value


def as_str(value: Any, name: str, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value:
        raise LivedStateError(f"{name} must be a non-empty string")
    if len(value) > max_len:
        raise LivedStateError(f"{name} exceeds {max_len} chars")
    return value


def as_str_list(value: Any, name: str) -> List[str]:
    if not isinstance(value, list):
        raise LivedStateError(f"{name} must be a list of strings")
    if len(value) > ORIGIN_TOKEN_LIMIT:
        raise LivedStateError(f"{name} has {len(value)} tokens; cap is {ORIGIN_TOKEN_LIMIT}")
    out = []
    for i, tok in enumerate(value):
        if not isinstance(tok, str):
            raise LivedStateError(f"{name}[{i}] must be a string")
        if len(tok) > ORIGIN_TOKEN_CHARS:
            raise LivedStateError(f"{name}[{i}] exceeds {ORIGIN_TOKEN_CHARS} chars")
        out.append(tok)
    return out


def as_vector(value: Any, dim: int, name: str) -> np.ndarray:
    if not isinstance(value, list) or len(value) != dim:
        raise LivedStateError(f"{name} must be a list of length {dim}")
    return as_array(value, (dim,), name, np.float32)


def as_array(value: Any, shape: tuple, name: str, dtype=np.float64) -> np.ndarray:
    """A finite numeric array of exactly this shape, within VECTOR_MAX_ABS. Anything else refuses."""
    try:
        arr = np.asarray(value, dtype=dtype)
    except (TypeError, ValueError, OverflowError) as exc:
        raise LivedStateError(f"{name} is not numeric") from exc
    if arr.shape != tuple(shape):
        raise LivedStateError(f"{name} shape {arr.shape} != {tuple(shape)}")
    if not np.all(np.isfinite(arr)):
        raise LivedStateError(f"{name} is not finite")
    if arr.size and float(np.max(np.abs(arr))) > VECTOR_MAX_ABS:
        raise LivedStateError(f"{name} exceeds {VECTOR_MAX_ABS} in magnitude")
    return arr


def as_rng_state(bit_generator: Any, value: Any, name: str) -> dict:
    """Prove a generator state loads on a scratch generator of the live type, at decode time.

    Setting a malformed state raises deep inside numpy with assorted types, and doing that during apply would
    leave a half-restored mind. Returns the state numpy normalized, so apply cannot fail on it.
    """
    value = require_dict(value, name)
    scratch = type(bit_generator)()
    try:
        scratch.state = value
        return scratch.state
    except Exception as exc:  # noqa: BLE001 - numpy raises Value/Type/Key/Overflow by field
        raise LivedStateError(f"{name} is not a valid generator state: {exc}") from exc


def jsonify(obj: Any) -> Any:
    """Numpy-safe JSON conversion for RNG state and similar nested dicts."""
    if isinstance(obj, dict):
        return {str(k): jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonify(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, (str, bool)) or obj is None:
        return obj
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise LivedStateError("non-finite float in snapshot")
        return float(obj)
    raise LivedStateError(f"cannot snapshot type {type(obj).__name__}")


# ---------------------------------------------------------------------------
# Cycle-level bundle
# ---------------------------------------------------------------------------

def quarantine_file(path: str) -> str:
    """Move `path` aside so a later save cannot overwrite the refused identity.

    Returns the quarantine path. Never deletes. If the destination exists,
    a counter is appended. This is an operator-facing filename, not model time.
    """
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(abs_path)
    stamp = f"{determinism.now():.0f}"
    dest = abs_path + f".refused-{stamp}"
    n = 0
    candidate = dest
    while os.path.exists(candidate):
        n += 1
        candidate = f"{dest}-{n}"
    os.replace(abs_path, candidate)
    logger.warning("Refused checkpoint preserved at %s", candidate)
    return candidate


def snapshot_from_cycle(cycle) -> dict:
    """State-only bundle. Thresholds, learning rates, and object identity stay live."""
    gov = cycle.governance
    return {
        "schema": SCHEMA,
        "dim": int(cycle.dim),
        "trust": None if gov is None else gov.trust_ledger.snapshot(),
        "bonds": None if gov is None else gov.bond_manager.snapshot(),
        "crystals": cycle.crystal_store.snapshot(),
        "attractors": cycle.attractor.snapshot(),
        "witness": cycle.witness.snapshot(),
        "emotion": cycle.emotion.snapshot(),
        "field": {
            "field": cycle.field.field.tolist(),
            "history": [h.tolist() for h in cycle.field.history],
        },
        "attention": cycle.rec_attn.snapshot(),
        "echo": cycle.predictor.snapshot(),
        "watcher": cycle.watcher.snapshot(),
        "manipulation": None if gov is None else gov.resistance.snapshot(),
        "dependency": None if gov is None else gov.dependency_monitor.snapshot(),
        "pending": None if gov is None else gov.snapshot_pending(),
        "dreamer_rng": jsonify(cycle.dreamer._rng.bit_generator.state),
        "chorus_rng": None if cycle.chorus is None else jsonify(cycle.chorus._rng.bit_generator.state),
    }


def decode_from_cycle(cycle, data: Any) -> dict:
    """Validate the whole bundle. Returns staging; does not mutate cycle."""
    data = require_dict(data, "lived")
    require_keys(data, ("schema", "dim", "crystals", "attractors", "witness", "emotion", "field", "attention",
                        "echo", "watcher", "dreamer_rng"), "lived")
    as_int(data["schema"], SCHEMA, SCHEMA, "lived.schema")
    if cycle.governance is not None:
        require_keys(data, ("trust", "bonds", "manipulation", "dependency", "pending"), "lived")
    if cycle.chorus is not None:
        require_keys(data, ("chorus_rng",), "lived")
    for section in ("witness", "emotion", "field", "attention", "echo", "watcher", "dreamer_rng") + (
            ("trust", "bonds", "manipulation", "dependency", "pending") if cycle.governance is not None else ()) + (
            ("chorus_rng",) if cycle.chorus is not None else ()):
        if data[section] is None:
            raise LivedStateError(f"lived section {section!r} is empty")
    dim = as_int(data["dim"], 1, 1_000_000, "lived.dim")
    live_dim = int(cycle.dim)
    if dim != live_dim:
        raise LivedStateError(
            f"stale checkpoint: dim {dim} vs live {live_dim}"
        )

    gov = cycle.governance
    staged: Dict[str, Any] = {
        "crystal_store": cycle.crystal_store,
        "crystals": cycle.crystal_store._decode_lived(data["crystals"], live_dim),
        "attractor": cycle.attractor,
        "attractors": cycle.attractor._decode_lived(data["attractors"], live_dim),
        "trust_ledger": None,
        "trust": None,
        "bond_manager": None,
        "bonds": None,
        "witness": cycle.witness,
        "witness_state": None,
        "emotion": cycle.emotion,
        "emotion_state": None,
        "field_obj": cycle.field,
        "field_state": None,
    }
    if data.get("witness") is not None:
        staged["witness_state"] = cycle.witness._decode_lived(
            data["witness"], live_dim
        )
    if data.get("emotion") is not None:
        em = require_dict(data["emotion"], "emotion")
        # EmotionalGradient.restore is a no-op (False) on old arousal/valence
        # only dicts. That must fail loud here, not skip.
        scalars = ("curiosity", "wonder", "joy", "tension", "boredom", "stability")
        if not all(k in em for k in scalars):
            raise LivedStateError("emotion snapshot missing the six scalars")
        require_keys(em, ("step",), "emotion")
        # Validated here, not in restore(): restore clips, and np.clip passes NaN straight through.
        # arousal/valence are derived and restore ignores them, so they are not carried.
        staged["emotion_state"] = {k: as_float(em[k], 0.0, 1.0, f"emotion.{k}") for k in scalars}
        staged["emotion_state"]["step"] = as_int(em["step"], 0, 10**9, "emotion.step")
    if data.get("field") is not None:
        fld = require_dict(data["field"], "field")
        require_keys(fld, ("field", "history"), "field")
        vec = as_vector(fld["field"], live_dim, "field.field").astype(float)
        hist_in = fld["history"]
        if not isinstance(hist_in, list):
            raise LivedStateError("field.history must be a list")
        maxlen = cycle.field.history.maxlen
        hist = [
            as_vector(h, live_dim, f"field.history[{i}]").astype(float)
            for i, h in enumerate(hist_in[-(maxlen or len(hist_in)):])
        ]
        from collections import deque
        staged["field_state"] = {
            "field": vec,
            "history": deque(hist, maxlen=maxlen),
        }
    staged["attention"] = cycle.rec_attn
    staged["attention_state"] = None
    staged["echo"] = cycle.predictor
    staged["echo_state"] = None
    if data.get("attention") is not None:
        staged["attention_state"] = cycle.rec_attn._decode_lived(
            data["attention"], live_dim
        )
    if data.get("echo") is not None:
        staged["echo_state"] = cycle.predictor._decode_lived(
            data["echo"], live_dim
        )
    staged["watcher"] = cycle.watcher
    staged["watcher_state"] = None
    staged["resistance"] = None
    staged["resistance_state"] = None
    staged["dependency"] = None
    staged["dependency_state"] = None
    if data.get("watcher") is not None:
        staged["watcher_state"] = cycle.watcher._decode_lived(
            data["watcher"], live_dim
        )
    if gov is not None:
        if data.get("manipulation") is not None:
            staged["resistance"] = gov.resistance
            staged["resistance_state"] = gov.resistance._decode_lived(data["manipulation"])
        if data.get("dependency") is not None:
            staged["dependency"] = gov.dependency_monitor
            staged["dependency_state"] = gov.dependency_monitor._decode_lived(data["dependency"])
    staged["governance"] = gov
    staged["pending_state"] = None
    if gov is not None and data.get("pending") is not None:
        staged["pending_state"] = gov._decode_lived_pending(data["pending"])
    staged["dreamer"] = cycle.dreamer
    staged["dreamer_rng"] = as_rng_state(cycle.dreamer._rng.bit_generator, data["dreamer_rng"], "dreamer_rng")
    staged["chorus"] = cycle.chorus
    staged["chorus_rng"] = None
    if cycle.chorus is not None:
        staged["chorus_rng"] = as_rng_state(cycle.chorus._rng.bit_generator, data["chorus_rng"], "chorus_rng")

    trust_payload = data.get("trust", None)
    bonds_payload = data.get("bonds", None)
    if trust_payload is not None or bonds_payload is not None:
        if gov is None:
            raise LivedStateError(
                "checkpoint has trust/bonds but the cycle has no governance"
            )

    known_sources = None
    if trust_payload is not None:
        staged["trust_ledger"] = gov.trust_ledger
        staged["trust"] = gov.trust_ledger._decode_lived(trust_payload)
        known_sources = set(staged["trust"]["sources"])
    if bonds_payload is not None:
        staged["bond_manager"] = gov.bond_manager
        staged["bonds"] = gov.bond_manager._decode_lived(
            bonds_payload, known_sources=known_sources
        )
    return staged


def apply_staged(staged: dict) -> None:
    if staged["trust"] is not None:
        staged["trust_ledger"]._apply_lived(staged["trust"])
    if staged["bonds"] is not None:
        staged["bond_manager"]._apply_lived(staged["bonds"])
    staged["crystal_store"]._apply_lived(staged["crystals"])
    staged["attractor"]._apply_lived(staged["attractors"])
    if staged.get("witness_state") is not None:
        staged["witness"]._apply_lived(staged["witness_state"])
    if staged.get("emotion_state") is not None:
        if not staged["emotion"].restore(staged["emotion_state"]):
            raise LivedStateError("emotion restore refused the snapshot")
    if staged.get("field_state") is not None:
        staged["field_obj"].field = staged["field_state"]["field"]
        staged["field_obj"].history = staged["field_state"]["history"]
    if staged.get("attention_state") is not None:
        staged["attention"]._apply_lived(staged["attention_state"])
    if staged.get("echo_state") is not None:
        staged["echo"]._apply_lived(staged["echo_state"])
    if staged.get("watcher_state") is not None:
        staged["watcher"]._apply_lived(staged["watcher_state"])
    if staged.get("resistance_state") is not None:
        staged["resistance"]._apply_lived(staged["resistance_state"])
    if staged.get("dependency_state") is not None:
        staged["dependency"]._apply_lived(staged["dependency_state"])
    if staged.get("pending_state") is not None:
        staged["governance"]._apply_lived_pending(staged["pending_state"])
    if staged.get("dreamer_rng") is not None:
        staged["dreamer"]._rng.bit_generator.state = staged["dreamer_rng"]
    if staged.get("chorus_rng") is not None and staged.get("chorus") is not None:
        staged["chorus"]._rng.bit_generator.state = staged["chorus_rng"]


def restore_into_cycle(cycle, data: Any) -> None:
    """Validate the whole bundle, then apply. On error the live system is untouched."""
    staged = decode_from_cycle(cycle, data)
    apply_staged(staged)


def save_lived_state(path: str, cycle) -> dict:
    data = snapshot_from_cycle(cycle)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)
    return data


def load_lived_state(path: str, cycle) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    restore_into_cycle(cycle, data)
    logger.info("Lived identity state restored from %s", path)
