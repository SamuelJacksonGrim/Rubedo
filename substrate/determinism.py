"""
substrate/determinism.py

Model time and randomness, in one place, so a run can be replayed exactly.

Time semantics:
  now()           MODEL time: every timestamp and time window the system reasons
                  with (flood window, crystal/attractor/binding age, bond and
                  trust timestamps, the temporal stream's tick, logs). Production
                  = the real wall clock.
  perf_counter    is NOT routed here: elapsed-time telemetry (StepState.elapsed_ms,
                  DreamCycle timing) measures the machine, not the mind, and stays
                  real in every mode.

Randomness:
  make_rng()      a numpy Generator. Production = fresh OS entropy each call (the
                  substrate is stochastic by design). Seeded mode = children of one
                  SeedSequence, handed out in call order.

Production behavior is unchanged unless a caller enters `deterministic(...)`.
Inside it, a SimClock advances a fixed `dt` per cycle step (AutonomousCycle.step
calls on_step()), and python's `random`, numpy's global generator and torch are
seeded too. tests/integration/determinism_replay.py holds the contract.
"""

from __future__ import annotations

import random as _random
import time as _time
from contextlib import contextmanager

import numpy as _np


class RealClock:
    def now(self) -> float:
        return _time.time()

    def on_step(self) -> None:
        pass


class SimClock:
    """Simulated model time: starts at `start`, advances `dt` per cycle step."""

    def __init__(self, start: float = 1_700_000_000.0, dt: float = 0.05):
        self.t = float(start)
        self.dt = float(dt)

    def now(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += float(seconds)

    def on_step(self) -> None:
        self.t += self.dt


_clock = RealClock()
_seq = None   # numpy SeedSequence in seeded mode, else None
_keys = None  # dedicated Generator for step keys in seeded mode


def now() -> float:
    return _clock.now()


def on_step() -> None:
    _clock.on_step()


def make_rng() -> _np.random.Generator:
    if _seq is None:
        return _np.random.default_rng()
    return _np.random.default_rng(_seq.spawn(1)[0])


def new_key(n: int = 8) -> str:
    """Step/node key: uuid4 in production, a seeded hex string in replay mode."""
    if _keys is None:
        import uuid
        return uuid.uuid4().hex[:n]
    return _keys.bytes((n + 1) // 2).hex()[:n]


def clock():
    return _clock


@contextmanager
def deterministic(seed: int, dt: float = 0.05, start: float = 1_700_000_000.0):
    """Replayable mode: SimClock + seeded generators. Restores everything on exit."""
    global _clock, _seq, _keys
    saved = (_clock, _seq, _keys, _random.getstate(), _np.random.get_state())
    try:
        import torch
        torch_state = torch.random.get_rng_state()
    except Exception:   # torch absent
        torch = None
        torch_state = None
    _clock = SimClock(start=start, dt=dt)
    _seq = _np.random.SeedSequence(seed)
    _keys = _np.random.default_rng(_np.random.SeedSequence([seed, 0x6B6579]))
    _random.seed(seed)
    _np.random.seed(seed % (2 ** 32))
    if torch is not None:
        torch.manual_seed(seed)
    try:
        yield _clock
    finally:
        _clock, _seq, _keys, rstate, npstate = saved
        _random.setstate(rstate)
        _np.random.set_state(npstate)
        if torch is not None and torch_state is not None:
            torch.random.set_rng_state(torch_state)
