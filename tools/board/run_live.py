"""Live Rubedo runner.

Boots through build_engine (production shape; pretrain on unless --skip-pretrain),
draws a workload, and runs until stopped. Every N steps it appends a metrics
row. Lever changes arrive as files in the run's inbox and are applied at the
next step boundary. Nothing here injects a vector.

Digests are thread-count sensitive. This process pins its math threads before
importing numpy or torch, and writes the count into config.json. --replay
refuses a different pin.

    python -m tools.board.run_live --run-dir runs/demo --skip-pretrain --steps 40
    python -m tools.board.run_live --replay runs/demo
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


def _thread_count(argv) -> int:
    if "--threads" in argv:
        return max(1, int(argv[argv.index("--threads") + 1]))
    if "--replay" in argv:
        folder = Path(argv[argv.index("--replay") + 1])
        cfg_path = folder / "config.json"
        if cfg_path.is_file():
            try:
                return max(1, int(json.loads(cfg_path.read_text(encoding="utf-8"))["threads"]))
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                pass
    raw = os.environ.get("RUBEDO_THREADS", "1")
    try:
        return max(1, int(raw))
    except ValueError:
        return 1


def _pin_environ(n: int) -> None:
    # Before numpy/torch. A different pool sums reductions in a different
    # order and moves the low bits of a digest (rename batch 1).
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = str(n)


_PINNED_THREADS = _thread_count(sys.argv)
_pin_environ(_PINNED_THREADS)

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.board.control import take                                          # noqa: E402
from tools.board.jsonio import append_jsonl, read_jsonl, to_jsonable, write_json  # noqa: E402
from tools.board.levers import Board, apply_lever, lever_values, panel         # noqa: E402
from tools.board.metrics import (                                              # noqa: E402
    MACHINE_KEYS, Samples, observe_step, series_schema, window_row,
)
from tools.board.workloads import load_workload                                # noqa: E402


@dataclass
class RunSpec:
    run_dir: Path
    seed: int = 42
    workload: str = "canonical"
    steps: int = 0
    every: int = 20
    window: int = 256
    skip_pretrain: bool = False
    threads: int = 1
    build_reader: bool = True
    dream_channel: bool = True
    step_delay: float = 0.0
    # Test seam. Not a CLI flag. Wall-clock wait; the mind does not see it.
    pause_at: int | None = None
    pause_arrived: object = None
    pause_release: object = None
    scripted: list = field(default_factory=list)


def _canon_line(row: dict) -> str:
    clean = {k: v for k, v in to_jsonable(row).items() if k not in MACHINE_KEYS}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_of(rows) -> str:
    hasher = hashlib.sha256()
    for row in rows:
        hasher.update(_canon_line(row).encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def _pin_torch(n: int) -> None:
    import torch
    torch.set_num_threads(int(n))
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass


class _Tap:
    """Record the decision arbitrate just returned. Does not change it."""

    def __init__(self):
        self.decision = "ALLOW"
        self.damp = "other"

    def install(self, governance) -> None:
        original = governance.arbitrate

        def tapped(*args, **kwargs):
            decision, strength = original(*args, **kwargs)
            systemic = bool(getattr(governance, "_last_systemic_damp", False))
            signals = list(getattr(governance, "_step_signals", []) or [])
            named = any(getattr(signal, "source_id", None) for signal in signals)
            if systemic:
                branch = "systemic"
            elif named and decision.name in ("ALLOW_WEAKENED", "QUARANTINE"):
                branch = "named"
            else:
                branch = "other"
            self.decision = decision.name
            self.damp = branch
            return decision, strength

        governance.arbitrate = tapped


def _scripted_at(scripted, step: int) -> list:
    return [item for item in scripted if int(item["step"]) == step]


def _apply_changes(board: Board, changes, step: int, run_dir: Path) -> None:
    for change in changes:
        result = apply_lever(board, str(change["id"]), change.get("value"))
        append_jsonl(run_dir / "toggles.jsonl", {
            "step": int(step),
            "id": str(change["id"]),
            "value": change.get("value"),
            "before": result.before,
            "after": result.after,
            "applied": bool(result.applied),
            "reason": result.reason,
        })


def _write_status(run_dir: Path, state: str, step: int, spec: RunSpec, board: Board,
                  timing: dict) -> None:
    write_json(run_dir / "status.json", {
        "state": state,
        "step": int(step),
        "seed": spec.seed,
        "workload": spec.workload,
        "threads": spec.threads,
        "every": spec.every,
        "window": spec.window,
        "panel": panel(board) if board.cycle is not None else [],
        "timing": timing,
        "guards": "Sacred shield, the manipulation ladder, ethical gates, and SystemRights are not on this panel.",
    })


def _log_to(run_dir: Path):
    """File log for this run. Closed by _unlog so a temp run folder can be removed."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    target = str((run_dir / "run.log").resolve())
    for handler in root.handlers:
        if getattr(handler, "baseFilename", None) == target:
            return handler
    handle = logging.FileHandler(target, encoding="utf-8")
    handle.setLevel(logging.INFO)
    handle.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root.addHandler(handle)
    return handle


def _unlog(handle) -> None:
    if handle is None:
        return
    root = logging.getLogger()
    root.removeHandler(handle)
    handle.close()


def _demotions(cycle) -> int:
    consumer = cycle.integrity_consumer
    if consumer is None:
        return 0
    return int(getattr(consumer, "demotions_total", 0))


def _core_count(value_engine) -> int:
    return sum(
        1 for value in value_engine.values.values()
        if value.dissolved_at_step < 0 and value.promoted_to_sacred
    )


def run_session(spec: RunSpec, replay_of: Path | None = None) -> dict:
    """Run one session. replay_of uses the scripted toggles and ignores the inbox."""
    spec.run_dir = Path(spec.run_dir)
    spec.run_dir.mkdir(parents=True, exist_ok=True)
    if spec.threads != _PINNED_THREADS:
        raise SystemExit(
            f"process pinned to {_PINNED_THREADS} threads at import; "
            f"this run asked for {spec.threads}. Start a fresh process with --threads {spec.threads}."
        )
    _pin_torch(spec.threads)
    log_handle = _log_to(spec.run_dir)
    try:
        return _run_logged(spec, replay_of)
    finally:
        _unlog(log_handle)


def _run_logged(spec: RunSpec, replay_of: Path | None) -> dict:
    from loop.dream_cycle import DreamCycle
    from loop.recursion1188 import CONFIG, build_dream_channel, build_engine
    from substrate import determinism

    cfg = dict(CONFIG)
    if spec.skip_pretrain:
        cfg["pretrain_on_corpus"] = False
    if not spec.dream_channel:
        cfg["dream_channel_enabled"] = False

    config_doc = {
        "seed": int(spec.seed),
        "workload": spec.workload,
        "threads": int(spec.threads),
        "every": int(spec.every),
        "window": int(spec.window),
        "steps_requested": int(spec.steps),
        "skip_pretrain": bool(spec.skip_pretrain),
        "build_reader": bool(spec.build_reader),
        "dream_channel": bool(spec.dream_channel) and bool(cfg.get("dream_channel_enabled", True)),
        "replay_of": str(replay_of) if replay_of else None,
        "actuator": (
            "tools/board flips lever flags at step boundaries only. "
            "It does not inject into the field."
        ),
    }
    write_json(spec.run_dir / "config.json", config_doc)
    write_json(spec.run_dir / "schema.json", {
        "series": series_schema(),
        "mixes": [
            {"key": "rhythm", "label": "Rhythm mix",
             "plain": "Which energy band the field sat in. Explore is the high-energy band, not curiosity. Witness and rupture are not bands; they show up under behavior."},
            {"key": "behavior", "label": "What ran",
             "plain": "The act, not the band. Witness receives without acting. Rupture is a held shove. A boredom force shows as explore while the band stays what it was."},
            {"key": "decisions", "label": "Governance mix",
             "plain": "What the gate decided. ALLOW injects in full. ALLOW_WEAKENED injects quieter. QUARANTINE, REJECT, and SACRED_SHIELD block."},
            {"key": "damp", "label": "Damp branch",
             "plain": "Of the manipulation responses: systemic means the detector could not name a source; named means it could."},
            {"key": "emotions", "label": "Six emotion scalars",
             "plain": "EMAs of prediction error, coherence, and field energy. Joy tracks coherence. Boredom is low novelty in a loose field. The names are hypotheses."},
            {"key": "oslash_by_pathology", "label": "⊘ by pathology",
             "plain": "Which failure the integrity read named on its last look. Blank while the consumer is off, because the board does not call the read itself."},
        ],
    })

    board = Board(config=cfg, ddm_config=dict(cfg.get("bond_ddm_config") or {}))
    _write_status(spec.run_dir, "booting", 0, spec, board, {})

    sources, weights = load_workload(spec.workload)
    sids = list(sources)
    weight_list = [weights[sid] for sid in sids]

    rows = []
    step_times = []
    observe_times = []
    metric_times = []
    completed = 0
    stopped = "end"

    with determinism.deterministic(spec.seed):
        import random

        generator, cycle, governance, value_engine = build_engine(cfg)
        channel = build_dream_channel(generator, cfg) if cfg.get("dream_channel_enabled") else None
        dream_cycle = DreamCycle(
            dreamer=cycle.dreamer,
            crystal_store=cycle.crystal_store,
            field=cycle.field,
            attractor=cycle.attractor,
            n_iterations=cfg.get("dream_iterations", 6),
        )
        reader_ok = False
        if spec.build_reader:
            try:
                from cognition.rhythm_reader import RhythmReader
                from training.corpus import RHYTHMS, TRAIN_PATH, load_corpus
                cycle.attach_rhythm_reader(
                    RhythmReader.from_corpus(generator, load_corpus(TRAIN_PATH), RHYTHMS))
                reader_ok = True
            except Exception as exc:
                logging.getLogger("tools.board").warning("rhythm reader not built: %s", exc)

        board.generator = generator
        board.cycle = cycle
        board.governance = governance
        board.value_engine = value_engine
        board.dream_channel = channel
        board.dream_channel_on = channel is not None
        board.dream_cycle_on = bool(cfg.get("dream_cycle_enabled", True))
        board.reader_ok = reader_ok

        tap = _Tap()
        tap.install(governance)
        samples = Samples(spec.window)
        pick = random.Random(spec.seed)
        dream_p = float(cfg.get("dream_channel_p", 0.20))
        dream_trigger = cfg.get("dream_cycle_trigger", "stabilize")
        scripted = list(spec.scripted or [])
        timing = {"mean_step_ms": None, "mean_observe_ms": None, "mean_metric_ms": None}

        def _emit(now_step: int) -> None:
            # One row. Called on the every-N boundary and once more at the end
            # when the stop falls between boundaries. Replay ends on
            # steps_completed, so both paths have to close the same way or the
            # digest splits on a hand-stop.
            nonlocal timing
            t_metric = time.perf_counter()
            row = window_row(
                samples, cycle, value_engine, board.advisory,
                cycle.integrity_consumer is not None,
                lever_values(board), now_step, 0.0,
            )
            row["overhead_ms"] = (time.perf_counter() - t_metric) * 1000.0
            row["step_ms_mean"] = (
                float(sum(step_times) / len(step_times)) if step_times else 0.0
            )
            row["observe_ms_mean"] = (
                float(sum(observe_times) / len(observe_times)) if observe_times else 0.0
            )
            metric_times.append(row["overhead_ms"])
            rows.append(row)
            append_jsonl(spec.run_dir / "metrics.jsonl", row)
            timing = {
                "mean_step_ms": row["step_ms_mean"],
                "mean_observe_ms": row["observe_ms_mean"],
                "mean_metric_ms": float(sum(metric_times) / len(metric_times)),
                "metric_every": spec.every,
            }
            _write_status(spec.run_dir, "running", now_step, spec, board, timing)
            cone = row["expr_cone_deg"]
            cone_s = f"{cone:.1f}" if isinstance(cone, (int, float)) else "n/a"
            sat = row["sat"]
            sat_s = f"{sat:.2f}" if isinstance(sat, (int, float)) else "n/a"
            print(
                f"  step {now_step:6d}  step {row['step_ms_mean']:.1f} ms  "
                f"observe {row['observe_ms_mean']:.2f} ms  "
                f"window {row['overhead_ms']:.1f} ms  "
                f"sat {sat_s}  cone {cone_s}",
                flush=True,
            )

        _write_status(spec.run_dir, "running", 0, spec, board, timing)
        print(
            f"live run {spec.run_dir.name}  seed {spec.seed}  {spec.workload}  "
            f"threads {spec.threads}  pretrain {'off' if spec.skip_pretrain else 'on'}  "
            f"dream-channel {'built' if channel is not None else 'not built'}",
            flush=True,
        )

        try:
            while True:
                upcoming = completed + 1
                if spec.pause_at is not None and upcoming == spec.pause_at:
                    if spec.pause_arrived is not None:
                        spec.pause_arrived.set()
                    if spec.pause_release is not None:
                        spec.pause_release.wait()

                if replay_of is None:
                    changes, stop = take(spec.run_dir)
                else:
                    changes, stop = _scripted_at(scripted, upcoming), False
                if changes:
                    _apply_changes(board, changes, upcoming, spec.run_dir)
                    _write_status(spec.run_dir, "running", completed, spec, board, timing)
                if stop or (spec.steps > 0 and completed >= spec.steps):
                    stopped = "stop" if stop else "end"
                    break

                boredom_before = cycle._boredom_overrides
                crystals_before = len(cycle.crystal_store.crystals)
                attractors_before = len(cycle.attractor.centers)
                core_before = _core_count(value_engine)
                demote_before = _demotions(cycle)

                use_dream = False
                tokens = None
                source_id = None
                if (board.dream_channel is not None and board.dream_channel_on
                        and pick.random() < dream_p):
                    dreamed = board.dream_channel.dream_tokens(cycle)
                    if dreamed:
                        use_dream = True
                        source_id = board.dream_channel.SOURCE_ID
                        tokens = dreamed
                if not use_dream:
                    source_id = pick.choices(sids, weights=weight_list)[0]
                    tokens = list(pick.choice(sources[source_id]))

                t_step = time.perf_counter()
                state = cycle.step(tokens, source_id=source_id, origin_type="internal")
                step_ms = (time.perf_counter() - t_step) * 1000.0
                decision, damp = tap.decision, tap.damp

                if (board.dream_cycle_on and dream_cycle is not None
                        and state.rhythm == dream_trigger and completed > 0
                        and completed % 20 == 0):
                    dream_cycle.run(
                        emotion=cycle.emotion,
                        watcher=cycle.watcher,
                        anchor=cycle.witness.current_anchor(),
                        generator=generator,
                    )

                t_obs = time.perf_counter()
                observed = observe_step(
                    cycle, value_engine, state, boredom_before, crystals_before,
                    attractors_before, core_before,
                    _demotions(cycle) - demote_before,
                    decision, damp, step_ms,
                )
                observe_ms = (time.perf_counter() - t_obs) * 1000.0
                samples.push(**{key: observed[key] for key in (
                    "expr", "anchor", "sat", "raw_norm", "field_coh", "watcher",
                    "eff_lr", "boredom", "boredom_hit", "rhythm", "behavior", "decision",
                    "damp", "births", "crystal_d", "attractor_d", "core_d",
                    "demote_d", "step_ms",
                )})
                step_times.append(step_ms)
                observe_times.append(observe_ms)
                completed += 1

                if spec.every > 0 and completed % spec.every == 0:
                    _emit(completed)

                if spec.step_delay > 0 and replay_of is None:
                    time.sleep(spec.step_delay)
        except KeyboardInterrupt:
            stopped = "interrupt"

        # Still inside the seed. A stop between samples has no every-N row at
        # `completed`; replay would otherwise invent one (it is given
        # steps_completed) or skip one. Write it here, after the boundary that
        # stopped the loop, so a toggle applied on the way out is in the row
        # on both paths.
        if completed and (not rows or rows[-1]["step"] != completed):
            _emit(completed)

    config_doc["steps_completed"] = completed
    config_doc["stopped"] = stopped
    write_json(spec.run_dir / "config.json", config_doc)
    digest = digest_of(rows)
    (spec.run_dir / "metrics.sha256").write_text(digest + "\n", encoding="utf-8")
    mean_step = float(sum(step_times) / len(step_times)) if step_times else 0.0
    mean_obs = float(sum(observe_times) / len(observe_times)) if observe_times else 0.0
    mean_metric = float(sum(metric_times) / len(metric_times)) if metric_times else 0.0
    every = max(1, spec.every)
    per_step = mean_obs + mean_metric / every
    share = (per_step / mean_step) if mean_step else 0.0
    timing = {
        "mean_step_ms": mean_step,
        "mean_observe_ms": mean_obs,
        "mean_metric_ms": mean_metric,
        "metric_every": spec.every,
        "overhead_per_step_ms": per_step,
        "overhead_share": share,
    }
    _write_status(spec.run_dir, "stopped", completed, spec, board, timing)
    print(
        f"stopped ({stopped}) at step {completed}  digest {digest[:16]}  "
        f"overhead {per_step:.2f} ms/step ({share:.1%} of the step)",
        flush=True,
    )
    return {
        "run_dir": spec.run_dir,
        "steps": completed,
        "digest": digest,
        "rows": len(rows),
        "timing": timing,
        "toggles": read_jsonl(spec.run_dir / "toggles.jsonl"),
    }


def replay(run_dir: Path) -> dict:
    """Re-apply the logged toggles at the same steps and compare the metrics digest."""
    run_dir = Path(run_dir)
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    if int(cfg["threads"]) != _PINNED_THREADS:
        raise SystemExit(
            f"run was pinned to {cfg['threads']} threads; this process is {_PINNED_THREADS}. "
            f"Re-run with --threads {cfg['threads']}."
        )
    steps = int(cfg.get("steps_completed") or 0)
    if steps <= 0:
        raise SystemExit(f"no completed steps in {run_dir}")
    toggles = read_jsonl(run_dir / "toggles.jsonl")
    # Replay every logged request, including refusals, so a reject stays a reject.
    scripted = [
        {"step": int(item["step"]), "id": item["id"], "value": item["value"]}
        for item in toggles
    ]
    out = run_session(RunSpec(
        run_dir=Path(str(run_dir) + "-replay"),
        seed=int(cfg["seed"]),
        workload=cfg["workload"],
        steps=steps,
        every=int(cfg["every"]),
        window=int(cfg["window"]),
        skip_pretrain=bool(cfg["skip_pretrain"]),
        threads=int(cfg["threads"]),
        build_reader=bool(cfg["build_reader"]),
        dream_channel=bool(cfg["dream_channel"]),
        scripted=scripted,
    ), replay_of=run_dir)
    expected = (run_dir / "metrics.sha256").read_text(encoding="utf-8").strip()
    ok = out["digest"] == expected
    print(f"replay {'MATCH' if ok else 'DIFFER'}  {out['digest']}  expected {expected}", flush=True)
    if not ok:
        raise SystemExit(1)
    return out


def _parse(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Live Rubedo runner")
    parser.add_argument("--replay", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workload", default="canonical")
    parser.add_argument("--steps", type=int, default=0, help="0 runs until stopped")
    parser.add_argument("--every", type=int, default=20)
    parser.add_argument("--window", type=int, default=256)
    parser.add_argument("--threads", type=int, default=_PINNED_THREADS)
    parser.add_argument("--skip-pretrain", action="store_true")
    parser.add_argument("--no-rhythm-reader", action="store_true")
    parser.add_argument("--no-dream-channel", action="store_true")
    parser.add_argument("--step-delay", type=float, default=0.0)
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _parse(sys.argv[1:] if argv is None else argv)
    if args.replay is not None:
        replay(args.replay)
        return
    if args.run_dir is None:
        raise SystemExit("pass --run-dir, or --replay <run>")
    if args.threads != _PINNED_THREADS:
        raise SystemExit(
            f"--threads {args.threads} does not match the pin {_PINNED_THREADS} "
            f"set before import. Re-run the process with that --threads "
            f"(it is read from argv at startup)."
        )
    run_session(RunSpec(
        run_dir=args.run_dir,
        seed=args.seed,
        workload=args.workload,
        steps=args.steps,
        every=args.every,
        window=args.window,
        skip_pretrain=args.skip_pretrain,
        threads=args.threads,
        build_reader=not args.no_rhythm_reader,
        dream_channel=not args.no_dream_channel,
        step_delay=args.step_delay,
    ))


if __name__ == "__main__":
    main()
