"""Plain run-folder files. No torch. A torn last line is skipped, not fatal."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path


def to_jsonable(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    module = type(value).__module__
    if module.startswith("numpy"):
        if hasattr(value, "shape"):
            return to_jsonable(value.tolist())
        if hasattr(value, "item"):
            return to_jsonable(value.item())
    return str(value)


def _replace(src: Path, dst: Path) -> None:
    delay = 0.02
    last = None
    for _ in range(12):
        try:
            src.replace(dst)
            return
        except PermissionError as exc:
            last = exc
            time.sleep(delay)
            delay = min(delay * 2, 0.25)
    if last is not None:
        raise last


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(to_jsonable(obj), indent=2, ensure_ascii=False)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    _replace(tmp, path)


def read_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def append_jsonl(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(to_jsonable(obj), ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
        handle.flush()


def read_jsonl(path: Path) -> list:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
