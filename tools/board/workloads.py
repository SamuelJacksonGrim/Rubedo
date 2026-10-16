"""Rooms the live runner can draw from.

canonical and wide are the probe rooms in tests/workloads.py. They are not
main()'s four-by-three toy list. themes is the hook for a future
themes-plus-novelty room: name it here, do not invent the phrases in the runner.
"""

from __future__ import annotations

from tests.workloads import WORKLOAD_NAMES, load_named

# Reserved. Not a room yet.
THEMES = "themes"


def load_workload(name: str):
    """Return (sources, weights). Raises ValueError on an unknown name."""
    if name == THEMES:
        raise ValueError(
            "themes-plus-novelty is not a room yet. "
            "Add the phrases in tools.board.workloads.load_workload, "
            "then drop the reserved-name guard."
        )
    if name not in WORKLOAD_NAMES:
        known = ", ".join(WORKLOAD_NAMES)
        raise ValueError(f"unknown workload {name!r}; expected {known}, or {THEMES!r} later")
    return load_named(name)
