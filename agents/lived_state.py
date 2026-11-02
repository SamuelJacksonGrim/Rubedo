"""
Lived identity state for a restart: trust, bonds (and DDM), crystals, attractors.

A checkpoint is an input to identity. Restore is reconstitution of already-lived
state into objects production already built — not a public constructor, and not
a path that lets a file override thresholds or learning rates. Malformed or
stale payloads raise LivedStateError and leave the live objects untouched.

Callers: the speech-bridge checkpoint and session_persistence. Constants stay
in code; only accumulated state is in the file.
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

SCHEMA = 1
ORIGIN_TOKEN_LIMIT = 256
ORIGIN_TOKEN_CHARS = 256


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
    vec = np.asarray(value, dtype=np.float32)
    if vec.shape != (dim,) or not np.all(np.isfinite(vec)):
        raise LivedStateError(f"{name} is not a finite vector of dim {dim}")
    return vec


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
    }


def decode_from_cycle(cycle, data: Any) -> dict:
    """Validate the whole bundle. Returns staging; does not mutate cycle."""
    data = require_dict(data, "lived")
    require_keys(data, ("schema", "dim", "crystals", "attractors"), "lived")
    schema = as_int(data["schema"], 1, SCHEMA, "lived.schema")
    if schema != SCHEMA:
        raise LivedStateError(f"unknown lived-state schema {schema}")
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
    }

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
