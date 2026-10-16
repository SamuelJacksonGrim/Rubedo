"""
tests/integration/live_board.py

The live runner writes metrics, applies one lever from the control inbox at a
step boundary, and --replay reproduces the metrics digest. Also: a guard id is
refused without touching the engine, the themes workload stays a hook, and the
page server (no engine import) writes an inbox file.

Boot skips pretrain, the dream-channel decoder, and the rhythm reader. The
dream cycle itself stays as CONFIG left it. A few dozen steps, one thread pin.

    python -m tests.integration.live_board
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

# Pin happens at this import, before numpy. The rest of the file uses that pin.
from tools.board.run_live import RunSpec, _PINNED_THREADS, digest_of, replay, run_session

REPO = Path(__file__).resolve().parents[2]


def _guards_and_hook() -> None:
    from tools.board.levers import Board, apply_lever
    from tools.board.workloads import load_workload

    refused = apply_lever(Board(), "sacred_shield", False)
    assert refused.applied is False
    assert "guards" in refused.reason
    try:
        load_workload("themes")
    except ValueError as exc:
        assert "not a room" in str(exc)
    else:
        raise AssertionError("themes should not be a room yet")
    print("  guards refused; themes is still a hook")


def _page_writes_inbox(root: Path) -> None:
    before = set(sys.modules)
    import tools.board.server as board_server
    imported = set(sys.modules) - before
    assert not any(name == "torch" or name.startswith("torch.") for name in imported), sorted(imported)
    assert not any("h0_probe" in name or name.endswith("run_live") for name in imported), sorted(imported)

    runs = root / "runs"
    run = runs / "http-demo"
    run.mkdir(parents=True)
    (run / "status.json").write_text('{"state":"running","step":0,"panel":[]}\n', encoding="utf-8")
    (run / "schema.json").write_text('{"series":[],"mixes":[]}\n', encoding="utf-8")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), board_server.make_handler(runs))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "Live board" in body
            assert "8770" in body and "8740" in body
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/run/http-demo/control",
            data=json.dumps({"id": "G", "value": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 202
        inbox = sorted((run / "inbox").glob("*.json"))
        assert len(inbox) == 1, inbox
        assert json.loads(inbox[0].read_text(encoding="utf-8")) == {"id": "G", "value": True}
        bad = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/run/http-demo/control",
            data=json.dumps({"id": "not a lever", "value": True}).encode("utf-8"),
            method="POST",
        )
        try:
            urllib.request.urlopen(bad, timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
        else:
            raise AssertionError("a bad lever id should be rejected")
    finally:
        httpd.shutdown()
        httpd.server_close()
    print(f"  page on port {port} wrote the inbox and refused a bad id")


def _session(root: Path) -> dict:
    from tools.board.control import enqueue
    from tools.board.jsonio import read_jsonl

    run = root / "live"
    arrived = threading.Event()
    release = threading.Event()
    spec = RunSpec(
        run_dir=run,
        seed=42,
        workload="canonical",
        steps=30,
        every=12,
        window=24,
        skip_pretrain=True,
        threads=_PINNED_THREADS,
        build_reader=False,
        dream_channel=False,
        pause_at=18,
        pause_arrived=arrived,
        pause_release=release,
    )
    holder = {}

    def _go():
        try:
            holder["result"] = run_session(spec)
        except BaseException as exc:
            holder["error"] = exc

    thread = threading.Thread(target=_go, name="live-board")
    thread.start()
    reached = arrived.wait(180)
    if reached:
        enqueue(run, {"id": "G", "value": True})
    release.set()
    thread.join(240)
    assert not thread.is_alive(), "runner did not finish"
    assert reached, "runner did not reach the step-18 boundary"
    if "error" in holder:
        raise holder["error"]

    result = holder["result"]
    rows = read_jsonl(run / "metrics.jsonl")
    assert [row["step"] for row in rows] == [12, 24, 30], [row["step"] for row in rows]
    assert rows[0]["levers"]["G"] is False
    assert rows[1]["levers"]["G"] is True
    assert rows[2]["levers"]["G"] is True
    assert "witness" in rows[-1]["behavior"]
    assert set(rows[-1]["emotions"]) == {
        "curiosity", "wonder", "joy", "tension", "boredom", "stability",
    }
    toggles = read_jsonl(run / "toggles.jsonl")
    assert len(toggles) == 1, toggles
    assert toggles[0]["step"] == 18 and toggles[0]["applied"] is True
    assert toggles[0]["before"] is False and toggles[0]["after"] is True

    digest = (run / "metrics.sha256").read_text(encoding="utf-8").strip()
    assert digest == digest_of(rows) == result["digest"]
    bumped = dict(rows[0])
    bumped["overhead_ms"] = 99999.0
    bumped["step_ms_mean"] = 99999.0
    bumped["observe_ms_mean"] = 99999.0
    assert digest_of([bumped] + rows[1:]) == digest

    try:
        replay(run)
    except SystemExit as exc:
        raise AssertionError(f"replay exited {exc.code}") from exc
    print(
        f"  {result['steps']} steps  digest {digest[:16]}  "
        f"overhead {result['timing']['overhead_per_step_ms']:.3f} ms/step "
        f"({result['timing']['overhead_share']:.1%} of the step)  "
        f"observe {result['timing']['mean_observe_ms']:.3f} ms  "
        f"window {result['timing']['mean_metric_ms']:.3f} ms"
    )
    return result


def main() -> int:
    print("=" * 72)
    print("  GATE: live board (inbox toggle, replay digest, page writes a file)")
    print("=" * 72)
    _guards_and_hook()
    with tempfile.TemporaryDirectory(prefix="rubedo-board-") as tmp:
        root = Path(tmp)
        _page_writes_inbox(root)
        _session(root)
    print("  PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"  FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
