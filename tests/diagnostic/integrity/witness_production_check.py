"""
tests/diagnostic/integrity/witness_production_check.py

Does the witness stance actually run on the production path (build_engine with
CONFIG, pretraining on), not just in witness_composition_gate's hand-built stack?
Witness was activated 2026-10-19 (six_rhythm_selector on, six_rhythm_stances
["witness"]); this boots the real engine, steps it on the gate's workload B
token mix, and counts the stances the selector took. Rupture must never appear.

Informational, exit 0 when witness fired and rupture didn't. Minutes (pretrain).
Run:  python -m tests.diagnostic.integrity.witness_production_check [steps]
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from substrate.determinism import deterministic            # noqa: E402
from loop.recursion1188 import CONFIG, build_engine        # noqa: E402


def main():
    import random
    from tests._common import RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS
    from tests.diagnostic.integrity.witness_composition_gate import WITNESS_PHRASES
    steps = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 500
    with deterministic(42):
        gen, cycle, gov, ve = build_engine(dict(CONFIG))
        attached = cycle.rhythm_reader is not None
        modes = Counter()
        real_select = cycle._select_mode

        def counted(toks):
            mode, read = real_select(toks)
            modes[mode or "energy"] += 1
            return mode, read

        cycle._select_mode = counted
        # The gate's workload B: the resonance family's canonical mix with 20%
        # witness phrases.
        pick = random.Random(42)
        sids = list(RESONANCE_FAMILY_SOURCES)
        w = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        for _ in range(steps):
            src = pick.choices(sids, weights=w)[0]
            if pick.random() < 0.20:
                toks = WITNESS_PHRASES[pick.randrange(len(WITNESS_PHRASES))]
            else:
                toks = pick.choice(RESONANCE_FAMILY_SOURCES[src])
            cycle.step(toks, source_id=src, origin_type="internal")
    print(f"reader attached: {attached}   steps: {steps}   stances: {dict(modes)}")
    ok = attached and modes.get("witness", 0) > 0 and modes.get("rupture", 0) == 0
    print("PASS: witness runs on the production path, rupture never" if ok
          else "FAIL: witness did not fire, or rupture did")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
