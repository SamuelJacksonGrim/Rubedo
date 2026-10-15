"""
tests/integration/six_rhythm_selector_invariants.py

Gate for the six-rhythm selector lever (loop/autonomous_cycle.py, opt-in).

  1. Inert means byte-identical: lever off with a reader attached, and lever on
     with no reader, both leave the field exactly where the default cycle leaves it.
  2. Generator.peek_batch is read-only: no usage bump, no new symbol, no step tick.
  3. Selector logic (with a scripted reader, so the test is about the wiring):
     witness skips the reflective loop and records behavior "witness"; rupture
     runs the held-direction push and releases its target afterward; a read under
     the margin changes nothing and records the energy behavior.

Run:
    python -m tests.integration.six_rhythm_selector_invariants
"""

import sys

import numpy as np

from cognition.rhythm_reader import RhythmRead
from tests._common import build_full_stack

TOKS = [['signal', 'pattern', 'hold'], ['field', 'memory', 'trace'], ['open', 'wide', 'drift']]


class ScriptedReader:
    def __init__(self, script):
        self.script = list(script)

    def read(self, generator, tokens):
        return self.script.pop(0) if self.script else RhythmRead(None, 0.0, 0.0)


_ORIG_RNG = np.random.default_rng


def _pin_rngs():
    """The substrate is stochastic by design: chorus, dreamer and the interference
    primitives call np.random.default_rng() with OS entropy. Pin every unseeded
    call to a fixed seed sequence so two runs can be compared bit for bit."""
    import itertools, random
    random.seed(0)
    np.random.seed(0)
    seeds = itertools.count(1000)
    np.random.default_rng = lambda seed=None, *a, **k: _ORIG_RNG(next(seeds) if seed is None else seed, *a, **k)


def run(n, setup=None):
    _pin_rngs()
    try:
        gen, cycle, gov, ve = build_full_stack()
        if setup:
            setup(cycle)
        states = [cycle.step(tokens=TOKS[i % 3], source_id='gate', origin_type='internal') for i in range(n)]
    finally:
        np.random.default_rng = _ORIG_RNG
    return cycle, states


def main():
    print('=' * 72)
    print('  GATE: six-rhythm selector invariants')
    print('=' * 72)

    # 1. inert = byte-identical
    base, _ = run(30)
    again, _ = run(30)
    assert np.array_equal(base.field.field, again.field.field), "baseline itself is not deterministic"

    def off_with_reader(c):
        c.attach_rhythm_reader(ScriptedReader([RhythmRead('witness', 0.9, 0.9)] * 30))
    def on_without_reader(c):
        c.six_rhythm_selector = True
    for name, setup in (('lever off + reader', off_with_reader), ('lever on, no reader', on_without_reader)):
        c, states = run(30, setup)
        assert np.array_equal(base.field.field, c.field.field), f"{name}: field differs from default"
        assert all(not s.extras for s in states), f"{name}: extras populated while inert"
    print('  inert paths byte-identical to default (30 steps)')

    # 2. peek is read-only
    gen, cycle, gov, ve = build_full_stack()
    for t in TOKS:
        cycle.step(tokens=t, source_id='gate', origin_type='internal')
    reg = gen.registry
    usage = {k: (s.usage, s.last_seen_step) for k, s in reg.symbols.items()}
    n_sym, counter = len(reg.symbols), reg.step_counter
    vecs, known = gen.peek_batch([['signal', 'pattern'], ['never', 'seen', 'zzqx']])
    assert known.tolist() == [True, False], f"known mask wrong: {known}"
    assert np.abs(vecs[1]).sum() == 0
    assert len(reg.symbols) == n_sym and reg.step_counter == counter, "peek registered something"
    assert {k: (s.usage, s.last_seen_step) for k, s in reg.symbols.items()} == usage, "peek bumped usage"
    print('  peek_batch registered nothing and bumped no usage')

    # 3. selector logic
    script = [RhythmRead('witness', 0.5, 0.8), RhythmRead('rupture', 0.5, 0.8),
              RhythmRead('reflect', 0.5, 0.8), RhythmRead('witness', 0.01, 0.4)]
    def on(c):
        c.six_rhythm_selector = True
        c.attach_rhythm_reader(ScriptedReader(script))
    gen, cycle, gov, ve = build_full_stack()
    on(cycle)
    s_w = cycle.step(tokens=TOKS[0], source_id='gate', origin_type='internal')
    assert s_w.extras['behavior'] == 'witness' and s_w.extras['rhythm_read'] == 'witness'
    assert s_w.reflection_passes == 0, "witness ran the reflective loop"
    s_r = cycle.step(tokens=TOKS[1], source_id='gate', origin_type='internal')
    assert s_r.extras['behavior'] == 'rupture'
    assert getattr(cycle, '_rupture_target', None) is not None, "rupture did not set a held target"
    fires = getattr(cycle, '_rupture_fires', 0)
    assert fires >= 1, "rupture push did not fire"
    s_e = cycle.step(tokens=TOKS[2], source_id='gate', origin_type='internal')
    assert s_e.extras['behavior'] in ('stabilize', 'dream', 'reflect', 'explore', 'dream (forced)')
    assert cycle._rupture_target is None, "held rupture target not released after the pulse"
    s_low = cycle.step(tokens=TOKS[0], source_id='gate', origin_type='internal')
    assert s_low.extras['behavior'] != 'witness', "a read under the margin still switched to witness"
    print(f'  witness -> {s_w.extras["behavior"]} (0 reflection passes); rupture -> {s_r.extras["behavior"]} '
          f'(held push fired, released next step); under-margin -> {s_low.extras["behavior"]}')
    print('Selector inert when off, read-only peek, modes wired as designed.')


if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print(f'FAIL: {e}')
        sys.exit(1)
