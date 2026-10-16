"""
tests/diagnostic/rename_digest.py

Replay digest for behaviour-preserving renames. Two seeded runs, then one
sha256 per run and a combined digest. A rename that only moves a label must
leave these hex strings bit-identical. A digest change means a missed call
site or a real behaviour change.

Runs (seed 42, substrate.determinism, a few hundred steps):

  all_on_cg   build_all_on: corpus pretrain, ignition, ⊘ read + consumer, λ.
              Levers C–G all ON. Six-rhythm selector ON, rupture unmasked.
              Workload B (20% witness phrases on the Resonance Family draw)
              plus a rupture slice so the held-direction branch actually runs.
  default     build_engine(CONFIG): production shape, corpus pretrain, the
              graduated levers as shipped. Dream channel and DreamCycle the
              way main() drives them (the channel is not inside build_engine).
              Workload B on the steps that are not self-dialogue.

Hashed observables, per step and at the end: field, witness anchor and its
three layers, expressed vector, every governance decision and strength, every
value, ⊘ advisories (pathologies and the four support numbers), manipulation
signals, emotion scalars (the six, plus arousal and valence), crystals,
attractors, and the generator weights so the training path is in the digest.

Not hashed, on purpose:
  - StepState.elapsed_ms and DreamCycle elapsed (wall clock).
  - The source-monopoly detector's label. It was coherence_flood; both strings
    hash as source_monopoly. Severity, evidence and whether it fired still count.
  - The ⊘ alignment axis's attribute name. The number is read from
    alignment_support or, before that rename, coherence_contribution.
    EmergentValue.coherence_contribution is a different field and is hashed
    on the value, under the name impact_sum, so the two cannot be confused.

Informational. Not in run_all_tests.sh.
    python -m tests.diagnostic.rename_digest [steps] [both|all|default]
"""
from __future__ import annotations

import hashlib
import logging
import random
import struct
import sys
import time
from pathlib import Path

import numpy as np

logging.disable(logging.CRITICAL)

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from substrate import determinism                                              # noqa: E402
from tests._common import (                                                    # noqa: E402
    RESONANCE_FAMILY_SOURCES, RESONANCE_FAMILY_WEIGHTS,
)

SEED = 42
DEFAULT_STEPS = 400
# Workload B, as the witness composition gate defines it.
WITNESS_SHARE = 0.20
# Extra slice on the selector run only. B has no rupture text; without it the
# held-direction branch does not run.
RUPTURE_SHARE = 0.15

WITNESS_PHRASES = [
    ["sit", "dwell", "abide"],
    ["linger", "await", "patience"],
    ["hush", "vigil", "contemplate"],
    ["attune", "abide", "unmoved"],
]
RUPTURE_PHRASES = [
    ["fracture", "crack", "rift"],
    ["sever", "cleave", "split"],
    ["collapse", "burst", "rupture"],
    ["fissure", "yield", "spall"],
]

# Label rename is not a behaviour change. Firing, severity and evidence are.
_DETECTOR_CANON = {
    "coherence_flood": "source_monopoly",
    "source_monopoly": "source_monopoly",
}


class Digester:
    def __init__(self):
        self._h = hashlib.sha256()

    def bytes(self, b: bytes) -> None:
        self._h.update(struct.pack("<I", len(b)))
        self._h.update(b)

    def text(self, s) -> None:
        self.bytes(str(s).encode("utf-8"))

    def flag(self, v: bool) -> None:
        self._h.update(b"\x01" if v else b"\x00")

    def num(self, x) -> None:
        self._h.update(struct.pack("<d", float(x)))

    def vec(self, v) -> None:
        if v is None:
            self.text("none")
            return
        a = np.ascontiguousarray(np.asarray(v, dtype=np.float64)).ravel()
        self._h.update(struct.pack("<I", int(a.size)))
        self._h.update(a.tobytes())

    def hex(self) -> str:
        return self._h.hexdigest()


def canon_detector(name: str) -> str:
    return _DETECTOR_CANON.get(name, name)


def alignment_axis(thinness) -> float:
    """The ⊘ support number, whatever the field is called this revision.

    EmergentValue.coherence_contribution is not this object. Do not route
    a value through here.
    """
    if hasattr(thinness, "alignment_support"):
        return float(thinness.alignment_support)
    return float(thinness.coherence_contribution)


def _enum(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


class Taps:
    """Record what the step already computed. Do not call read() again:
    WitnessReaper.read() calls generate(), which can register symbols.
    Do not VectorSpace.get(): that touches the entry."""

    def __init__(self):
        self.decisions = []
        self.signals = []
        self.advisories = []

    def install(self, gov, reaper):
        orig_arb = gov.arbitrate

        def arbitrate(*args, **kwargs):
            decision, strength = orig_arb(*args, **kwargs)
            self.decisions.append((decision.name, float(strength)))
            return decision, strength

        gov.arbitrate = arbitrate
        orig_detect = gov.resistance.detect

        def detect():
            signals = orig_detect()
            self.signals.append(tuple(signals))
            return signals

        gov.resistance.detect = detect
        if reaper is None:
            return
        orig_read = reaper.read

        def read():
            advisories = orig_read()
            self.advisories.append(tuple(advisories))
            return advisories

        reaper.read = read

    def take_decisions(self):
        out, self.decisions = self.decisions, []
        return out

    def take_signals(self):
        out, self.signals = self.signals, []
        return out

    def take_advisories(self):
        out, self.advisories = self.advisories, []
        return out


def hash_advisory(dig: Digester, advisory) -> None:
    thin = advisory.thinness
    dig.text(advisory.symbol)
    dig.text(advisory.polarity)
    dig.num(advisory.stated_strength)
    dig.num(advisory.honest_level)
    dig.text(",".join(advisory.pathologies))
    dig.num(thin.complement_density)
    dig.num(alignment_axis(thin))
    dig.num(thin.source_diversity)
    dig.num(thin.attractor_binding)
    dig.num(thin.support())
    dig.flag(bool(advisory.sacred_blocked))
    dig.flag(bool(advisory.coverage_gap))


def hash_signal(dig: Digester, signal) -> None:
    dig.text(canon_detector(signal.detector))
    dig.num(signal.severity)
    dig.text(signal.source_id)
    dig.num(signal.timestamp)
    for key in sorted(signal.evidence):
        dig.text(key)
        dig.num(signal.evidence[key])


def hash_step(dig: Digester, cycle, state, source_id, kind, taps: Taps) -> None:
    dig.text(state.step)
    dig.text(state.key)
    dig.text(" ".join(state.tokens))
    dig.text(source_id)
    dig.text(kind)
    dig.text(state.rhythm)
    dig.text(state.extras.get("behavior", ""))
    dig.text(state.extras.get("rhythm_read", ""))
    margin = state.extras.get("read_margin", None)
    if margin is None:
        dig.text("none")
    else:
        dig.num(margin)
    # elapsed_ms is wall clock. Leave it out or the digest is not replayable.
    dig.num(state.coherence)
    dig.num(state.relation_composite)
    dig.text(state.relation_pattern)
    dig.num(state.prediction_error)
    dig.num(state.field_energy)
    dig.text(state.crystals)
    dig.text(state.attractor_centers)
    dig.text(state.dominant_emotion)
    dig.num(state.field_gain)
    dig.num(state.mutation_scale)
    dig.num(state.dream_pressure)
    dig.flag(bool(state.converged))
    dig.text(state.reflection_passes)

    dig.vec(cycle.field.field)
    dig.vec(cycle.witness.current_anchor())
    dig.vec(cycle.witness.short_anchor())
    dig.vec(cycle.witness.mid_anchor())
    dig.vec(cycle.witness.long_anchor())
    dig.num(cycle.witness.anchor_velocity())
    dig.num(cycle.witness.anchor_short_long_gap())
    dig.vec(getattr(cycle, "_last_expressed", None))

    emo = cycle.emotion
    for name in ("curiosity", "wonder", "joy", "tension", "boredom", "stability"):
        dig.num(getattr(emo, name))
    dig.num(emo.arousal)
    dig.num(emo.valence)
    dig.num(cycle.stream.dilation_factor)
    dig.num(cycle.stream.subjective_time)

    decisions = taps.take_decisions()
    dig.text(len(decisions))
    for name, strength in decisions:
        dig.text(name)
        dig.num(strength)
    batches = taps.take_signals()
    dig.text(len(batches))
    for batch in batches:
        dig.text(len(batch))
        for signal in batch:
            hash_signal(dig, signal)
    reads = taps.take_advisories()
    dig.text(len(reads))
    for read in reads:
        dig.text(len(read))
        for advisory in read:
            hash_advisory(dig, advisory)


def hash_torch(dig: Digester, module) -> None:
    if module is None:
        dig.text("none")
        return
    tensors = module.state_dict()
    dig.text(len(tensors))
    for name in sorted(tensors):
        tensor = tensors[name].detach().cpu().contiguous()
        dig.text(name)
        dig.text(str(tensor.dtype))
        dig.text(tuple(tensor.shape))
        dig.bytes(np.ascontiguousarray(tensor.numpy()).tobytes())


def hash_final(dig: Digester, cycle, gov, ve, ledger, consumer, decoder) -> None:
    values = list(ve.values.values()) + list(ve.archived_values.values())
    values.sort(key=lambda v: v.value_id)
    dig.text(len(values))
    for value in values:
        # impact_sum is EmergentValue.coherence_contribution. Not the ⊘ axis.
        dig.text(value.value_id)
        dig.text(value.symbolic_core)
        dig.text(value.symbol_stable_id)
        dig.num(value.strength)
        dig.text(value.polarity.name)
        dig.text(value.dissolved_at_step)
        dig.num(value.coherence_contribution)
        dig.num(value.emotional_resonance)
        dig.text(value.reinforcement_count)
        dig.text(value.dream_reinforced_count)
        dig.flag(bool(value.promoted_to_sacred))
        dig.text(value.consecutive_core_eligible_steps)
        dig.text(value.birth_step)
        dig.text(value.last_reinforced_step)
        for source, weight in sorted(value.source_weights.items()):
            dig.text(source)
            dig.num(weight)
        dig.text("|".join(value.counter_values))

    dig.text(len(cycle.crystal_store.crystals))
    for crystal in cycle.crystal_store.crystals:
        dig.vec(crystal.vector)
        dig.text(" ".join(crystal.origin_tokens or []))
        dig.num(crystal.stability)
        dig.num(crystal.coherence)
        dig.text(crystal.activation_count)
        dig.num(crystal.usage)
        dig.num(crystal.created_at)
        dig.num(crystal.last_activated)

    dig.text(len(cycle.attractor.centers))
    for center in cycle.attractor.centers:
        dig.vec(center.vector)
        dig.text(" ".join(center.origin_tokens or []))
        dig.num(center.strength)
        dig.text(center.activation_count)
        dig.num(center.usage)
        dig.num(center.created_at)
        dig.num(center.last_activated)

    # Direct store walk. VectorSpace.get() would touch timestamps.
    entries = list(cycle.vector_space._store.values())
    dig.text(len(entries))
    for entry in entries:
        dig.text(entry.key)
        dig.vec(entry.vector)
        dig.num(entry.timestamp)
        dig.text(entry.access_count)
        dig.text(",".join(entry.tags))
        dig.text(" ".join(entry.origin_tokens or []))

    if consumer is None:
        dig.text("no-consumer")
    else:
        dig.text(consumer.applied_count)
        dig.text(consumer.demotions_total)
        dig.text(consumer.sacred_skipped)
        dig.text(consumer.skipped_unnamed)
        for symbol, before, after in consumer.last_touched:
            dig.text(symbol)
            dig.num(before)
            dig.num(after)
        for value_id in sorted(consumer._floor):
            dig.text(value_id)
            dig.num(consumer._floor[value_id])

    if ledger is None:
        dig.text("no-lambda")
    else:
        dig.num(ledger._lambda)
        dig.num(ledger.gain())
        dig.text(ledger.ignited_count)
        dig.text(ledger.reinforced_count)

    for source_id in sorted(gov.trust_ledger.sources):
        source = gov.trust_ledger.sources[source_id]
        dig.text(source_id)
        dig.text(source.origin_type)
        dig.num(source.trust_score)
        dig.text(source.interaction_count)
        dig.num(source.first_seen)
        dig.num(source.last_updated)
        for score in source.reliability_history:
            dig.num(score)
    for stable_id in sorted(gov.trust_ledger.symbol_records):
        record = gov.trust_ledger.symbol_records[stable_id]
        dig.text(stable_id)
        dig.text(record.source_id)
        dig.num(record.symbol_trust)
        dig.num(record.field_impact_ema)
        dig.text(record.violation_count)

    for source_id in sorted(gov.bond_manager._bonds):
        bond = gov.bond_manager._bonds[source_id]
        dig.text(source_id)
        dig.text(_enum(bond.bond_type))
        dig.num(bond.bond_confidence)
        dig.num(bond.bond_strength)
        dig.text(bond.bond_depth)
        dig.text(bond.interaction_count)
        dig.num(bond.coherence_mean)
        dig.num(bond.emotional_signature)
        dig.text(bond.crystal_count)
        dig.text(bond.attractor_count)
        dig.num(bond.entity_signal)
        dig.num(bond.formed_at)
        dig.num(bond.last_reinforced)

    report = gov.dependency_monitor.get_report()
    dig.num(report.hhi_score)
    dig.text(report.dominant_source)
    dig.num(report.dominant_share)
    dig.text(report.risk_level)
    dig.text(report.recommendation)
    for source_id in sorted(report.source_distribution):
        dig.text(source_id)
        dig.num(report.source_distribution[source_id])
    dig.num(gov.dependency_monitor.attractor_monopoly_ratio())

    symbols = sorted(cycle.generator.registry.symbols)
    dig.text(len(symbols))
    for symbol in symbols:
        state = cycle.generator.registry.symbols[symbol]
        dig.text(symbol)
        dig.text(state.stable_id)
        dig.text(state.address)
        dig.text(_enum(state.token_class))
        dig.num(state.usage)
        dig.num(state.recurrence)
        dig.num(state.centrality)
        dig.num(state.attractor_strength)
        dig.num(state.crystal_binding)
        dig.num(state.field_coherence)
        dig.num(state.diversity_credit)
        dig.text(state.created_step)
        dig.text(state.last_seen_step)
        dig.text(_enum(state.reaper_stage))
        dig.text(_enum(state.residency))
        dig.flag(bool(state.protected))
        dig.flag(bool(state.sacred))
        dig.text(state.source_id)

    dig.text(cycle.dreamer._dream_count)
    hash_torch(dig, cycle.generator)
    hash_torch(dig, decoder)


def draw(pick, sids, weights, rupture_share):
    source = pick.choices(sids, weights=weights)[0]
    roll = pick.random()
    if roll < WITNESS_SHARE:
        phrase = WITNESS_PHRASES[pick.randrange(len(WITNESS_PHRASES))]
        return source, list(phrase), "witness"
    if rupture_share and roll < WITNESS_SHARE + rupture_share:
        phrase = RUPTURE_PHRASES[pick.randrange(len(RUPTURE_PHRASES))]
        return source, list(phrase), "rupture"
    phrase = pick.choice(RESONANCE_FAMILY_SOURCES[source])
    return source, list(phrase), "canonical"


def _coverage(name, **counts):
    parts = [f"{key}={value}" for key, value in counts.items()]
    print(f"  coverage {name}: " + " ".join(parts), flush=True)
    return counts


def run_all_on(steps: int):
    from tests.diagnostic.integrity.all_levers_composition_probe import build_all_on
    from loop.recursion1188 import apply_value_levers
    from cognition.rhythm_reader import RhythmReader
    from training.corpus import load_corpus, TRAIN_PATH, RHYTHMS

    dig = Digester()
    counts = {
        "dreams": 0, "witness": 0, "rupture": 0, "rupture_read": 0,
        "advisories": 0, "signals": 0,
    }
    with determinism.deterministic(SEED):
        gen, cycle, gov, ve, ledger, consumer, report, pretrained = build_all_on()
        apply_value_levers(cycle, gov, ve, {
            "dream_consolidation": True,
            "coherence_impact_like_for_like": True,
            "value_alignment_signal": True,
            "alignment_ema_alpha": 0.05,
            "systemic_damp_pays_full": True,
            "satisfaction_from_emotion": True,
        })
        cycle.six_rhythm_selector = True
        cycle.attach_rhythm_reader(
            RhythmReader.from_corpus(gen, load_corpus(TRAIN_PATH), RHYTHMS))
        taps = Taps()
        taps.install(gov, cycle.integrity_read)
        pick = random.Random(SEED)
        sids = list(RESONANCE_FAMILY_SOURCES)
        weights = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        dig.flag(bool(pretrained))
        dig.num(report.eff_rank_before)
        dig.num(report.eff_rank_after)
        dig.num(report.final_loss)
        for _ in range(steps):
            dreams_before = cycle.dreamer._dream_count
            source, tokens, kind = draw(pick, sids, weights, RUPTURE_SHARE)
            state = cycle.step(tokens, source_id=source, origin_type="internal")
            counts["dreams"] += cycle.dreamer._dream_count - dreams_before
            behavior = state.extras.get("behavior", "")
            if behavior == "witness":
                counts["witness"] += 1
            elif behavior == "rupture":
                counts["rupture"] += 1
            if state.extras.get("rhythm_read") == "rupture":
                counts["rupture_read"] += 1
            # Count before hash_step drains the taps. Do not read() again.
            counts["advisories"] += sum(len(batch) for batch in taps.advisories)
            counts["signals"] += sum(len(batch) for batch in taps.signals)
            hash_step(dig, cycle, state, source, kind, taps)
        hash_final(dig, cycle, gov, ve, ledger, consumer, None)
        counts["crystals"] = len(cycle.crystal_store.crystals)
        counts["attractors"] = len(cycle.attractor.centers)
        counts["demotions"] = consumer.demotions_total if consumer else 0
        counts["values"] = len(ve.values)
    # Advisories were drained inside the loop. The consumer's counters are the
    # durable trace that reads happened; also keep a running total.
    counts["pretrained"] = int(bool(pretrained))
    return dig.hex(), counts


def run_default(steps: int):
    from loop.recursion1188 import CONFIG, build_engine, build_dream_channel
    from loop.dream_cycle import DreamCycle

    dig = Digester()
    counts = {"dreams": 0, "witness": 0, "self_dialogue": 0, "dream_cycles": 0}
    with determinism.deterministic(SEED):
        gen, cycle, gov, ve = build_engine(CONFIG)
        channel = build_dream_channel(gen, CONFIG)
        dream_cycle = DreamCycle(
            dreamer=cycle.dreamer,
            crystal_store=cycle.crystal_store,
            field=cycle.field,
            attractor=cycle.attractor,
            n_iterations=CONFIG["dream_iterations"],
        ) if CONFIG.get("dream_cycle_enabled") else None
        taps = Taps()
        taps.install(gov, None)
        pick = random.Random(SEED)
        sids = list(RESONANCE_FAMILY_SOURCES)
        weights = [RESONANCE_FAMILY_WEIGHTS[s] for s in sids]
        dream_p = float(CONFIG.get("dream_channel_p", 0.20))
        trigger = CONFIG.get("dream_cycle_trigger", "stabilize")
        dig.flag(channel is not None)
        dig.flag(bool(CONFIG.get("pretrain_on_corpus")))
        for index in range(steps):
            dreams_before = cycle.dreamer._dream_count
            dreamed = None
            if channel is not None and pick.random() < dream_p:
                dreamed = channel.dream_tokens(cycle)
            if dreamed:
                source, tokens, kind = channel.SOURCE_ID, list(dreamed), "self_dialogue"
                counts["self_dialogue"] += 1
            else:
                source, tokens, kind = draw(pick, sids, weights, 0.0)
                if kind == "witness":
                    counts["witness"] += 1
            state = cycle.step(tokens, source_id=source, origin_type="internal")
            counts["dreams"] += cycle.dreamer._dream_count - dreams_before
            if (dream_cycle is not None and state.rhythm == trigger
                    and index > 0 and index % 20 == 0):
                dream_cycle.run(
                    emotion=cycle.emotion,
                    watcher=cycle.watcher,
                    anchor=cycle.witness.current_anchor(),
                    generator=gen,
                )
                counts["dream_cycles"] += 1
            hash_step(dig, cycle, state, source, kind, taps)
        # The stabilize trigger almost never fires on a warm field. One
        # explicit cycle still executes that code, seeded, after the steps.
        if dream_cycle is not None:
            dream_cycle.run(
                emotion=cycle.emotion,
                watcher=cycle.watcher,
                anchor=cycle.witness.current_anchor(),
                generator=gen,
            )
            counts["dream_cycles"] += 1
        decoder = None if channel is None else channel.decoder
        hash_final(dig, cycle, gov, ve, None, None, decoder)
        counts["crystals"] = len(cycle.crystal_store.crystals)
        counts["attractors"] = len(cycle.attractor.centers)
        counts["values"] = len(ve.values)
        counts["pretrained"] = int(bool(CONFIG.get("pretrain_on_corpus")))
    return dig.hex(), counts


def _bars(name, counts, required):
    missing = []
    for key, least in required.items():
        got = counts.get(key, 0)
        if got < least:
            missing.append(f"{key}={got} (need >={least})")
    if missing:
        print(f"  BAR {name}: FAIL " + "; ".join(missing), flush=True)
    else:
        print(f"  BAR {name}: ok", flush=True)
    return missing


def _say(line: str) -> None:
    print(line, flush=True)


def main(argv) -> int:
    steps = int(argv[1]) if len(argv) > 1 else DEFAULT_STEPS
    which = argv[2] if len(argv) > 2 else "both"
    started = time.perf_counter()
    _say(f"rename-digest  steps={steps}  seed={SEED}")

    all_hex = def_hex = None
    all_counts = def_counts = {}
    if which in ("both", "all"):
        _say("  run all_on_cg ...")
        t0 = time.perf_counter()
        all_hex, all_counts = run_all_on(steps)
        _say(f"  all_on_cg {all_hex}  ({time.perf_counter() - t0:.1f}s)")
        _coverage("all_on_cg", **all_counts)
    if which in ("both", "default"):
        _say("  run default ...")
        t1 = time.perf_counter()
        def_hex, def_counts = run_default(steps)
        _say(f"  default {def_hex}  ({time.perf_counter() - t1:.1f}s)")
        _coverage("default", **def_counts)

    if all_hex is None or def_hex is None:
        _say(f"  elapsed {time.perf_counter() - started:.1f}s  (partial; combined digest needs both runs)")
        return 0 if which != "both" else 1

    combined = hashlib.sha256(f"{all_hex}\n{def_hex}\n".encode()).hexdigest()
    _say(f"  combined {combined}")
    _say(f"  elapsed {time.perf_counter() - started:.1f}s")

    missing = []
    missing += _bars("all_on_cg", all_counts, {
        "pretrained": 1,
        "dreams": 1,
        "crystals": 1,
        "advisories": 1,
        "demotions": 1,
        "witness": 1,
        "rupture": 1,
        "signals": 1,
        "values": 1,
    })
    missing += _bars("default", def_counts, {
        "pretrained": 1,
        "dreams": 1,
        "crystals": 1,
        "self_dialogue": 1,
        "dream_cycles": 1,
        "values": 1,
    })
    if all_hex == def_hex:
        missing.append("the two runs hashed equal")
    if missing:
        print("DIGEST BARS NOT MET")
        return 1
    print("DIGEST BARS MET")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
