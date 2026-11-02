"""
tests/integration/held_contracts.py

Pins contracts that hold and had no test of their own. The broken ones are
recorded in docs/findings/2026-10-31-contract-audit.md and are not asserted
here.

  1. The reaper's decision leaves a sacred symbol ACTIVE and in the registry.
     A matched non-sacred symbol is archived.
  2. Reclaiming an address does not reuse the stable_id.
  3. The ⊘ consumer does not change the strength of a sacred advisory or a
     value already marked promoted_to_sacred. An ordinary advisory still moves.
  4. RelationalBond is constructed in one place.
  5. The dream channel and DreamSession do not inject. The loop driver feeds
     source_dream through cycle.step.
  6. dilation_factor and subjective_time are not read by the step except
     tick() and update_dilation().
  7. quarantine_symbol does not archive a sacred symbol, and decay_step does not
     rewrite its usage (both broke until 2026-10-31).
  8. The per-step stores are bounded: TopologicalLog, the witness snapshot and
     candidate lists, the cycle's VectorSpace (grew without a cap until 2026-10-31).

Run:
    python -m tests.integration.held_contracts
"""

from __future__ import annotations

from pathlib import Path

from agents.symbolic_memory import AddressSpace, ReaperDecision, SymbolRegistry
from agents.value_emergence import EmergentValue, ValuePolarity
from cognition.integrity_read import (
    DemotionAdvisory,
    IntegrityDecayConsumer,
    ThinnessVector,
)

REPO = Path(__file__).resolve().parents[2]

PASS = []
FAIL = []


def check(name: str, ok: bool, detail: str = ""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'✓' if ok else '✗'} {name}" + (f"  — {detail}" if detail else ""))


def fresh_registry() -> SymbolRegistry:
    return SymbolRegistry(AddressSpace(vocab_size=256))


def code_lines(path: Path):
    """Yield (lineno, code) with a # comment stripped. Docstrings stay."""
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        yield i, line.split("#", 1)[0]


def test_reaper_leaves_sacred():
    print("\n[1] Reaper decision does not archive a sacred symbol")
    reg = fresh_registry()
    reg.register("holy")
    reg.register("mortal")
    for name in ("holy", "mortal"):
        state = reg.symbols[name]
        state.usage = 0.0
        state.created_step = 0
        state.last_seen_step = 0
    holy = reg.symbols["holy"]
    holy.sacred = True
    holy.usage = 5.0
    decision = reg.reaper.evaluate(holy, 100)
    check("evaluate() returns ACTIVE for a sacred symbol past its lifespan",
          decision == ReaperDecision.ACTIVE, f"got {decision}")
    reg.step_counter = 100
    reg.decay_step()
    kept = reg.symbols.get("holy")
    check("decay_step keeps the sacred symbol in the active set",
          kept is not None and kept.sacred and kept.reaper_stage == ReaperDecision.ACTIVE,
          "missing" if kept is None else f"stage={kept.reaper_stage} usage={kept.usage:.4f}")
    check("decay_step leaves the sacred symbol's usage alone (fixed 2026-10-31)",
          kept is not None and kept.usage == 5.0,
          "missing" if kept is None else f"usage={kept.usage:.4f}")
    check("the matched non-sacred symbol is archived",
          "mortal" not in reg.symbols)


def test_stable_id_not_reused():
    print("\n[2] stable_id is not recycled when its address is reclaimed")
    reg = fresh_registry()
    first = reg.register("alpha")
    sid = first.stable_id
    reg.address_space.reclaim(sid)
    second = reg.register("beta")
    check("a new symbol does not receive the reclaimed stable_id",
          second.stable_id != sid, f"alpha={sid} beta={second.stable_id}")
    check("the original symbol still owns its stable_id",
          reg.symbol_table.sid_for("alpha") == sid)


def test_consumer_skips_sacred():
    print("\n[3] ⊘ consumer does not pull a sacred value")

    class Engine:
        def __init__(self):
            self.values = {}
            self.polarity_writes = 0

        def _update_polarity(self, value):
            self.polarity_writes += 1

    def value(vid, strength, promoted=False):
        return EmergentValue(
            value_id=vid, symbol_stable_id=1, symbolic_core=vid,
            strength=strength, polarity=ValuePolarity.STRONG,
            promoted_to_sacred=promoted,
        )

    def advisory(vid, strength, sacred):
        return DemotionAdvisory(
            value_id=vid, symbol=vid, polarity="strong",
            stated_strength=strength, honest_level=0.0,
            pathologies=["Drift"], thinness=ThinnessVector(0, 0, 0, 0),
            sacred_blocked=sacred, coverage_gap=False,
        )

    engine = Engine()
    engine.values["flagged"] = value("flagged", 4.0, promoted=False)
    engine.values["core"] = value("core", 4.5, promoted=True)
    engine.values["plain"] = value("plain", 4.0, promoted=False)

    class Reaper:
        def read(self):
            return [
                advisory("flagged", 4.0, True),
                advisory("core", 4.5, False),
                advisory("plain", 4.0, False),
            ]

    touched = IntegrityDecayConsumer(Reaper(), engine, rate=1.0).apply()
    check("sacred_blocked advisory does not change strength",
          engine.values["flagged"].strength == 4.0,
          f"strength={engine.values['flagged'].strength}")
    check("promoted_to_sacred value is not pulled even if the advisory forgot the flag",
          engine.values["core"].strength == 4.5,
          f"strength={engine.values['core'].strength}")
    check("an ordinary advisory still moves",
          engine.values["plain"].strength < 4.0 and any(t[0] == "plain" for t in touched),
          f"strength={engine.values['plain'].strength} touched={touched}")


def test_one_bond_constructor():
    print("\n[4] RelationalBond is constructed in one place")
    hits = []
    for root in ("agents", "cognition", "loop", "substrate", "interference", "api"):
        for path in (REPO / root).rglob("*.py"):
            for i, code in code_lines(path):
                if "RelationalBond(" in code:
                    hits.append(path.relative_to(REPO).as_posix() + f":{i}")
    check("exactly one RelationalBond( call, in the bond manager",
          hits == ["agents/relational_bond_manager.py:478"],
          f"hits={hits}")


def test_voices_go_through_the_step():
    print("\n[5] source_dream and DreamSession do not inject on their own")
    channel = (REPO / "cognition" / "dream_channel.py").read_text(encoding="utf-8")
    session = (REPO / "cognition" / "dream_session.py").read_text(encoding="utf-8")
    driver = (REPO / "loop" / "recursion1188.py").read_text(encoding="utf-8")
    check("DreamChannel source does not call field.inject",
          "field.inject" not in channel)
    check("DreamSession source does not call field.inject",
          "field.inject" not in session)
    check("the loop driver names source_dream and steps it",
          "dream_channel.SOURCE_ID" in driver and "cycle.step(" in driver)


def test_dilation_is_a_sink():
    print("\n[6] dilation_factor and subjective_time stay out of the decision")
    allowed = {
        "self.stream.tick()",
        "self.stream.update_dilation(",
    }
    bad = []
    roots = [REPO / "agents", REPO / "loop" / "autonomous_cycle.py",
             REPO / "loop" / "recursion1188.py"]
    files = []
    for root in roots:
        files.extend(root.rglob("*.py") if root.is_dir() else [root])
    for path in files:
        for i, code in code_lines(path):
            if ".dilation_factor" not in code and ".subjective_time" not in code:
                continue
            if any(ok in code for ok in allowed):
                continue
            bad.append(f"{path.relative_to(REPO)}:{i}: {code.strip()}")
    check("no decision read of dilation_factor or subjective_time",
          not bad, "\n".join(bad))


def test_quarantine_spares_sacred():
    print("\n[7] quarantine_symbol does not archive a sacred symbol (fixed 2026-10-31)")
    reg = fresh_registry()
    reg.register("holy")
    reg.register("plain")
    holy = reg.symbols["holy"]
    holy.sacred = True
    reg.quarantine_symbol(holy.stable_id)
    reg.quarantine_symbol(reg.symbols["plain"].stable_id)
    check("a sacred symbol stays in the registry, not cold-archived",
          "holy" in reg.symbols and reg.symbols["holy"].reaper_stage != ReaperDecision.COLD_ARCHIVE)
    check("an ordinary symbol is still quarantined", "plain" not in reg.symbols)


def test_rolling_stores_are_bounded():
    print("\n[8] Per-step stores are bounded (fixed 2026-10-31)")
    from substrate.topological_log import TopologicalLog
    from agents.witness import Witness
    log = TopologicalLog(max_nodes=50)
    prev = None
    for i in range(80):
        log.add(f"n{i}", parent=prev)
        prev = f"n{i}"
    check("TopologicalLog keeps at most max_nodes, dropping the oldest",
          log.graph.number_of_nodes() == 50 and log.graph.has_node("n79") and not log.graph.has_node("n0"),
          f"nodes={log.graph.number_of_nodes()}")
    check("TopologicalLog is bounded by default", TopologicalLog().max_nodes is not None)
    w = Witness(dim=8)
    check("Witness snapshots and crystallization candidates have a maxlen",
          getattr(w.snapshots, "maxlen", None) is not None
          and getattr(w.crystallization_candidates, "maxlen", None) is not None)
    hits = [ln for _, ln in code_lines(REPO / "loop" / "autonomous_cycle.py")
            if "VectorSpace(" in ln and "max_size=" in ln]
    check("the cycle builds its VectorSpace with a max_size", bool(hits))


def main() -> int:
    print("=" * 70)
    print("  HELD CONTRACTS")
    print("=" * 70)
    test_reaper_leaves_sacred()
    test_stable_id_not_reused()
    test_consumer_skips_sacred()
    test_one_bond_constructor()
    test_voices_go_through_the_step()
    test_dilation_is_a_sink()
    test_quarantine_spares_sacred()
    test_rolling_stores_are_bounded()
    print()
    print(f"  {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILED:")
        for name in FAIL:
            print(f"  - {name}")
        return 1
    print("Contracts that were checked here hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
