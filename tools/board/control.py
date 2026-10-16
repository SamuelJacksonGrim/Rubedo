"""Control inbox. The board writes a file; the runner reads it at a step boundary.

No socket into the process. A name appears only after the JSON is complete.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from tools.board.jsonio import read_json, write_json

_lock = threading.Lock()
_seq = 0


def enqueue(run_dir: Path, payload: dict) -> str:
    """Drop one request into the run's inbox. Returns the filename."""
    global _seq
    inbox = Path(run_dir) / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    with _lock:
        _seq += 1
        name = f"{time.time_ns():020d}-{_seq:04d}.json"
    write_json(inbox / name, payload)
    return name


def take(run_dir: Path) -> tuple:
    """Apply-order requests waiting at this boundary. Torn files stay put.

    Returns (changes, stop). changes are {"id", "value"} in filename order.
    Files are removed only after they parse.
    """
    inbox = Path(run_dir) / "inbox"
    if not inbox.is_dir():
        return [], False
    changes = []
    stop = False
    for path in sorted(p for p in inbox.glob("*.json") if p.is_file()):
        data = read_json(path)
        if not isinstance(data, dict):
            continue
        try:
            path.unlink()
        except OSError:
            continue
        if data.get("stop") is True:
            stop = True
            continue
        if "id" in data:
            changes.append({"id": str(data["id"]), "value": data.get("value")})
    return changes, stop
