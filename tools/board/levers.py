"""Which levers the live board may flip, and how.

A writable lever is a flag the step already reads, or an attach/detach the
cycle already exposes. Guards are not levers. Boot-only work (pretrain, the
dream-channel decoder, the rhythm reader's centroids) is shown and refused.

The ⊘ consumer is the writer. The ⊘ read stays unread by this module:
WitnessReaper.read() calls Generator.generate, which registers tokens and
bumps usage. The runner caches the advisory the consumer already asked for.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Names a control file must never apply, even if a client sends them.
GUARDS = (
    "sacred_shield",
    "manipulation",
    "manipulation_ladder",
    "ethical",
    "ethical_gates",
    "system_rights",
    "SystemRights",
)

# Fix 0-B's documented leak when the bool is on. Off is 0.
BINDING_LEAK_ON = 0.10
# The lever table's research ignite. First time λ is attached, not on every reattach.
LAMBDA_IGNITE = 2.0


@dataclass
class Board:
    """Live objects the runner holds. Levers mutate these; nothing else does."""

    generator: object = None
    cycle: object = None
    governance: object = None
    value_engine: object = None
    dream_channel: object = None
    dream_channel_on: bool = False
    dream_cycle_on: bool = False
    reader_ok: bool = False
    config: dict = field(default_factory=dict)
    reaper: object = None
    consumer: object = None
    lambda_ledger: object = None
    # Last advisory the consumer's own read() returned. Not a fresh read.
    advisory: dict = field(default_factory=lambda: {"n": None, "by": {}})
    ddm_config: dict = field(default_factory=dict)


@dataclass
class ApplyResult:
    applied: bool
    before: object
    after: object
    reason: str = ""


def _flag(obj, name, default=False):
    return bool(getattr(obj, name, default))


def _ensure_reaper(board: Board) -> None:
    if board.reaper is not None:
        return
    from cognition.integrity_read import IntegrityDecayConsumer, WitnessReaper

    reaper = WitnessReaper(
        board.value_engine,
        registry=board.generator.registry,
        bond_manager=board.governance.bond_manager,
    )
    cache = board.advisory
    original = reaper.read

    def caching_read():
        advisories = original()
        by_path = {}
        for item in advisories:
            labels = list(item.pathologies or ["unnamed"])
            for label in labels:
                by_path[label] = by_path.get(label, 0) + 1
        cache["n"] = len(advisories)
        cache["by"] = by_path
        return advisories

    reaper.read = caching_read
    board.reaper = reaper
    # named_only stays True. The aggressive mode is documented to collapse.
    board.consumer = IntegrityDecayConsumer(reaper, board.value_engine, named_only=True)
    board.cycle.attach_integrity_read(reaper)


def _set_oslash(board: Board, on: bool) -> None:
    _ensure_reaper(board)
    if on:
        board.cycle.attach_integrity_consumer(board.consumer)
    else:
        board.cycle.attach_integrity_consumer(None)


def _set_lambda(board: Board, on: bool) -> None:
    if on:
        if board.lambda_ledger is None:
            from agents.lambda_ledger import LambdaLedger
            ledger = LambdaLedger()
            ledger.ignite(LAMBDA_IGNITE)
            board.lambda_ledger = ledger
        board.cycle.attach_lambda_ledger(board.lambda_ledger)
    else:
        board.cycle.attach_lambda_ledger(None)


def _set_bond_ddm(board: Board, on: bool) -> None:
    manager = board.governance.bond_manager
    if on:
        if manager._ddm is None:
            from agents.bond_accumulator import BondFormationAccumulator
            manager._ddm = BondFormationAccumulator(**dict(board.ddm_config or {}))
    else:
        # Off drops integrated evidence. On again starts V at 0; the private
        # noise stream restarts at its seed. It does not resume.
        manager._ddm = None


def _set_fix0b(board: Board, on: bool) -> None:
    monitor = board.cycle.expression_metastability
    if on:
        if monitor is None:
            raise RuntimeError("expression monitor is not on this cycle")
        monitor.track_regime_share = True
        board.cycle.diversity_fitness = True
        board.generator.registry.set_diversity_weights()
    else:
        board.cycle.diversity_fitness = False
        # Private profiles are the fitness term. Clearing them is the off
        # position; stored credits stay on the symbols and are unread.
        board.generator.registry._profiles = None


def _set_binding_leak(board: Board, on: bool) -> None:
    board.generator.registry.binding_leak = BINDING_LEAK_ON if on else 0.0


def _oslash_on(board: Board) -> bool:
    return board.cycle.integrity_consumer is not None


def _lambda_on(board: Board) -> bool:
    return board.cycle.lambda_ledger is not None


def _ddm_on(board: Board) -> bool:
    return board.governance.bond_manager._ddm is not None


def _fix0b_on(board: Board) -> bool:
    return bool(board.cycle.diversity_fitness)


def _leak_on(board: Board) -> bool:
    return float(board.generator.registry.binding_leak) > 0.0


def _dream_channel_writable(board: Board) -> bool:
    return board.dream_channel is not None


def _selector_writable(board: Board) -> bool:
    return board.reader_ok and board.cycle.rhythm_reader is not None


# id, label, plain meaning, kind, read(), write() or None, writable predicate
def _specs():
    return (
        ("D", "D · like-for-like coherence",
         "Compare the field before and after on the same squashed scale. Off mixes a raw before with a squashed after, so the delta is not the input's effect.",
         lambda b: _flag(b.cycle.field, "coherence_like_for_like"),
         lambda b, v: _set_both_like(b, v),
         lambda b: True),
        ("F", "F · systemic damp pays full",
         "A damp that cannot name a source still quiets the injection. On, the value engine is paid as if the step were allowed. Named damps are unchanged.",
         lambda b: _flag(b.governance, "systemic_damp_pays_full"),
         lambda b, v: setattr(b.governance, "systemic_damp_pays_full", bool(v)),
         lambda b: True),
        ("C", "C · dream consolidation",
         "A dream crystal is credited to the memories it recombined, and its relation is the cosine with the long anchor. Off, the offer uses a synthetic dream key and relation 0.5.",
         lambda b: _flag(b.cycle, "dream_consolidation"),
         lambda b, v: setattr(b.cycle, "dream_consolidation", bool(v)),
         lambda b: True),
        ("E", "E · alignment value signal",
         "Values learn from how this step's alignment differs from its own recent average, not from the coherence delta. The first step on centers at zero.",
         lambda b: _flag(b.value_engine, "value_alignment_signal"),
         lambda b, v: setattr(b.value_engine, "value_alignment_signal", bool(v)),
         lambda b: True),
        ("G", "G · satisfaction from valence",
         "The value engine's satisfaction reads valence instead of the coherence delta. Joy in the emotion block is still mostly coherence under another name.",
         lambda b: _flag(b.cycle, "satisfaction_from_emotion"),
         lambda b, v: setattr(b.cycle, "satisfaction_from_emotion", bool(v)),
         lambda b: True),
        ("novelty", "Novelty attenuation",
         "Lets a new input loosen the reflective loop, up to the 0.30 ceiling. Off, the loop pulls expression back as hard as ever.",
         lambda b: _flag(b.cycle.reflector, "novelty_attenuation"),
         lambda b, v: setattr(b.cycle.reflector, "novelty_attenuation", bool(v)),
         lambda b: True),
        ("selector", "Six-rhythm selector",
         "The generator's read of the input can choose witness or rupture. Witness receives without acting. Rupture is a held shove. Off, energy alone picks the four bands.",
         lambda b: _flag(b.cycle, "six_rhythm_selector"),
         lambda b, v: setattr(b.cycle, "six_rhythm_selector", bool(v)),
         _selector_writable),
        ("rupture_upstream", "Rupture upstream",
         "How rupture is applied once the read chooses it. On, the held direction is mixed into the generator output and the ordinary path carries it. Off, the reflective loop is forced instead, and the field absorbs it.",
         lambda b: _flag(b.cycle, "rupture_upstream"),
         lambda b, v: setattr(b.cycle, "rupture_upstream", bool(v)),
         lambda b: True),
        ("oslash", "⊘ consumer",
         "Turns the integrity read's advice into a pull on thin, named-pathology values. Sacred values are skipped. Off, the read is not asked, because asking it would bump symbol usage.",
         _oslash_on,
         _set_oslash,
         lambda b: True),
        ("dream_channel", "Dream channel",
         "Whether this step may feed the system's own decoded expression back as source_dream, through the gate. The decoder itself is trained only at boot.",
         lambda b: bool(b.dream_channel_on),
         lambda b, v: _set_dream_channel(b, v),
         _dream_channel_writable),
        ("dream_cycle", "Dream cycle",
         "Whether the runner calls the offline dream cycle on the stabilize cadence. That call writes crystals and the field; it is the existing driver, not a new inject path.",
         lambda b: bool(b.dream_cycle_on),
         lambda b, v: _set_dream_cycle(b, v),
         lambda b: True),
        ("bond_ddm", "Bond formation accumulator",
         "Bond quality integrates evidence to a bound instead of one snapshot. Turning it off drops the accumulated evidence. Turning it on starts the bound at zero.",
         _ddm_on,
         _set_bond_ddm,
         lambda b: True),
        ("fix0b", "Fix 0-B diversity fitness",
         "Symbols that show up in a varied stretch of expression decay a little less. The regime tracker starts when this turns on, so the first window pays nothing. Off stops the term.",
         _fix0b_on,
         _set_fix0b,
         lambda b: b.cycle.expression_metastability is not None),
        ("binding_leak", "Binding leak",
         "Unrefreshed attractor and crystal bindings decay on each reaper pass. On is the measured 0.10. Sacred and protected symbols are exempt.",
         _leak_on,
         _set_binding_leak,
         lambda b: True),
        ("lambda", "λ solvent",
         "Gates whether co-present values reinforce each other. The first on ignites λ at 2. Off detaches the gate and keeps the scalar. On again reattaches the same ledger.",
         _lambda_on,
         _set_lambda,
         lambda b: True),
    )


def _set_both_like(board: Board, value: bool) -> None:
    flag = bool(value)
    board.cycle.field.coherence_like_for_like = flag
    board.cycle.watcher.coherence_like_for_like = flag


def _set_dream_channel(board: Board, value: bool) -> None:
    if board.dream_channel is None:
        raise RuntimeError("dream channel was not built at boot")
    board.dream_channel_on = bool(value)


def _set_dream_cycle(board: Board, value: bool) -> None:
    board.dream_cycle_on = bool(value)


_SPEC_BY_ID = {row[0]: row for row in _specs()}


def known_ids():
    return tuple(_SPEC_BY_ID)


def apply_lever(board: Board, lever_id: str, value) -> ApplyResult:
    """Flip one lever. Refusals leave the board unchanged."""
    if lever_id in GUARDS or lever_id.lower() in {g.lower() for g in GUARDS}:
        return ApplyResult(False, None, None, "guards are not on the panel")
    spec = _SPEC_BY_ID.get(lever_id)
    if spec is None:
        return ApplyResult(False, None, None, f"unknown lever {lever_id}")
    _id, _label, _plain, read, write, writable = spec
    if not writable(board):
        return ApplyResult(False, read(board), read(board), _readonly_reason(board, lever_id))
    if not isinstance(value, bool):
        return ApplyResult(False, read(board), read(board), "panel levers are on/off")
    before = read(board)
    if before == bool(value):
        return ApplyResult(True, before, before, "already set")
    try:
        write(board, bool(value))
    except Exception as exc:
        return ApplyResult(False, before, read(board), str(exc))
    after = read(board)
    return ApplyResult(True, before, after, "")


def _readonly_reason(board: Board, lever_id: str) -> str:
    if lever_id == "dream_channel":
        return "the decoder is trained at boot; this run did not build it"
    if lever_id == "selector":
        return "the rhythm reader was not built; centroids belong to the boot weights"
    if lever_id == "fix0b":
        return "this cycle has no expression monitor to read"
    return "not switchable on this run"


def _readonly_rows(board: Board):
    cfg = board.config or {}
    margin = getattr(board.cycle, "rhythm_read_margin", None)
    alpha = getattr(board.value_engine, "alignment_ema_alpha", None)
    rows = (
        ("pretrain", "Corpus pretrain",
         "Trains the generator before the first step. A live toggle cannot untrain it.",
         bool(cfg.get("pretrain_on_corpus")),
         "boot only"),
        ("eval_mode", "Eval mode",
         "Dropout stays off. This is the operating regime, not a lever.",
         True,
         "unconditional at boot"),
        ("chorus", "Chorus",
         "Six-agent harmonization is wired in the constructor. Flipping it would rebuild the step.",
         bool(cfg.get("use_chorus")),
         "boot only"),
        ("session_persistence", "Session persistence",
         "Saves weights at the end of a run and skips pretrain on the next boot. Not a mid-run flag.",
         bool(cfg.get("session_persistence")),
         "boot and shutdown only"),
        ("stream_recorder", "Stream recorder",
         "An observe-only census. It does not change the loop, so it is not a lever.",
         bool(cfg.get("stream_recorder")),
         "not a lever"),
        ("itg", "Ignition threshold gate",
         "Standing policy: this containment lever stays unwired. It is not waiting on a measurement.",
         False,
         "severed"),
        ("rhythm_margin", "Rhythm read margin",
         "How sure the six-rhythm read must be before witness or rupture runs. A dial, not a switch. The selector toggle is the switch.",
         margin,
         "dial, left at boot"),
        ("alignment_alpha", "Alignment EMA rate",
         "How fast lever E's baseline forgets. Unused while E is off. Not a switch.",
         alpha,
         "dial, left at boot"),
        ("dream_p", "Dream-channel rate",
         "The fraction of steps that may be self-dialogue while the dream channel is on. The switch is the dream channel toggle.",
         cfg.get("dream_channel_p"),
         "dial, left at boot"),
    )
    out = []
    for lid, label, plain, value, note in rows:
        out.append({
            "id": lid,
            "label": label,
            "plain": plain,
            "writable": False,
            "value": value,
            "note": note,
        })
    return out


def panel(board: Board) -> list:
    """Current lever row for status.json and the page."""
    rows = []
    for lever_id, label, plain, read, _write, writable in _specs():
        can = bool(writable(board))
        note = "" if can else _readonly_reason(board, lever_id)
        if lever_id == "selector" and can:
            note = "Witness is not its own switch. The read chooses witness or rupture."
        if lever_id == "oslash" and can:
            note = "Named pathologies only. The aggressive mode is not on this panel."
        try:
            value = read(board)
        except Exception:
            value = None
            can = False
            note = note or "unreadable"
        rows.append({
            "id": lever_id,
            "label": label,
            "plain": plain,
            "writable": can,
            "value": value,
            "note": note,
        })
    rows.extend(_readonly_rows(board))
    return rows


def lever_values(board: Board) -> dict:
    """Bool (and the read-only dials) stored on each metrics row."""
    out = {}
    for row in panel(board):
        value = row["value"]
        if isinstance(value, float):
            out[row["id"]] = round(value, 6)
        else:
            out[row["id"]] = value
    return out
