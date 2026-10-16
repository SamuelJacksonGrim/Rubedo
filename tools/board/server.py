"""Live board page. Binds 127.0.0.1 only.

Reads a run folder and writes control files. Does not import the engine, the
probe stack, or the runner: importing those pulls torch and, for the H0 probe,
disables logging. The runner is what applies a file, at the next step boundary.

    python -m tools.board.server --port 8780 --runs tools/board/runs
"""

from __future__ import annotations

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.board.control import enqueue  # noqa: E402
from tools.board.jsonio import read_json, read_jsonl  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
HOST = "127.0.0.1"
DEFAULT_PORT = 8780
SAFE_ID = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
LEVER_ID = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
BODY_MAX = 8192

PAGES = {
    "/": (STATIC / "index.html", "text/html; charset=utf-8"),
    "/index.html": (STATIC / "index.html", "text/html; charset=utf-8"),
    "/app.css": (STATIC / "app.css", "text/css; charset=utf-8"),
    "/app.js": (STATIC / "app.js", "text/javascript; charset=utf-8"),
}


def _safe_run(text: str) -> str | None:
    if not text or text in {".", ".."} or any(ch not in SAFE_ID for ch in text):
        return None
    return text


def _lever_id(text: str) -> str | None:
    if not text or len(text) > 64 or any(ch not in LEVER_ID for ch in text):
        return None
    return text


def _run_dir(runs_dir: Path, run_id: str) -> Path | None:
    safe = _safe_run(run_id)
    if safe is None:
        return None
    folder = (runs_dir / safe).resolve()
    if folder.parent != runs_dir.resolve() or not folder.is_dir():
        return None
    return folder


def _list_runs(runs_dir: Path) -> list:
    if not runs_dir.is_dir():
        return []
    found = []
    for folder in runs_dir.iterdir():
        if not folder.is_dir() or _safe_run(folder.name) is None:
            continue
        status = read_json(folder / "status.json") or {}
        config = read_json(folder / "config.json") or {}
        try:
            mtime = folder.stat().st_mtime
        except OSError:
            mtime = 0
        found.append({
            "run_id": folder.name,
            "state": status.get("state") or "unknown",
            "step": status.get("step"),
            "seed": config.get("seed"),
            "workload": config.get("workload"),
            "threads": config.get("threads"),
            "mtime": mtime,
        })
    found.sort(key=lambda row: (row["mtime"], row["run_id"]), reverse=True)
    return found


def _metrics(folder: Path, after, limit: int) -> list:
    rows = read_jsonl(folder / "metrics.jsonl")
    if after is None:
        return rows[-limit:]
    try:
        cutoff = int(after)
    except (TypeError, ValueError):
        return rows[-limit:]
    return [row for row in rows if int(row.get("step") or 0) > cutoff]


def make_handler(runs_dir: Path):
    """Handler class bound to one runs directory. Tests use port 0."""
    root = Path(runs_dir)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            return

        def do_GET(self):
            try:
                self._get()
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                return

        def do_POST(self):
            try:
                self._post()
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                return

        def _get(self):
            parsed = urllib.parse.urlparse(self.path)
            page = PAGES.get(parsed.path)
            if page is not None:
                self._file(*page)
                return
            parts = [part for part in parsed.path.split("/") if part]
            if parts == ["api", "runs"]:
                self._json(200, _list_runs(root))
                return
            if len(parts) == 4 and parts[0] == "api" and parts[1] == "run":
                folder = _run_dir(root, parts[2])
                if folder is None:
                    self._json(404, {"error": "no such run"})
                    return
                kind = parts[3]
                if kind == "status":
                    self._json(200, read_json(folder / "status.json") or {})
                    return
                if kind == "schema":
                    self._json(200, read_json(folder / "schema.json") or {"series": [], "mixes": []})
                    return
                if kind == "config":
                    self._json(200, read_json(folder / "config.json") or {})
                    return
                if kind == "toggles":
                    self._json(200, read_jsonl(folder / "toggles.jsonl"))
                    return
                if kind == "metrics":
                    qs = urllib.parse.parse_qs(parsed.query)
                    after = (qs.get("after") or [None])[0]
                    limit = 400
                    if "limit" in qs:
                        try:
                            limit = max(1, min(5000, int(qs["limit"][0])))
                        except ValueError:
                            limit = 400
                    self._json(200, _metrics(folder, after, limit))
                    return
            self._json(404, {"error": "not found"})

        def _post(self):
            parsed = urllib.parse.urlparse(self.path)
            parts = [part for part in parsed.path.split("/") if part]
            if not (len(parts) == 4 and parts[0] == "api" and parts[1] == "run" and parts[3] == "control"):
                self._json(404, {"error": "not found"})
                return
            folder = _run_dir(root, parts[2])
            if folder is None:
                self._json(404, {"error": "no such run"})
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > BODY_MAX:
                self._json(400, {"error": "body must be a small JSON object"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._json(400, {"error": "body is not JSON"})
                return
            if not isinstance(payload, dict):
                self._json(400, {"error": "body must be an object"})
                return
            if payload.get("stop") is True and "id" not in payload:
                name = enqueue(folder, {"stop": True})
                self._json(202, {"queued": name, "stop": True})
                return
            lever = _lever_id(str(payload.get("id") or ""))
            if lever is None or not isinstance(payload.get("value"), bool):
                self._json(400, {"error": "expected {id, value:true|false} or {stop:true}"})
                return
            # Charset only. The runner accepts or refuses, and logs which.
            name = enqueue(folder, {"id": lever, "value": payload["value"]})
            self._json(202, {"queued": name, "id": lever, "value": payload["value"]})

        def _file(self, path: Path, content_type: str):
            if not path.is_file():
                self._json(404, {"error": "missing page"})
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _json(self, code: int, obj):
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

    return Handler


def main(argv=None) -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Live Rubedo board")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--runs", type=Path, required=True)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    runs = Path(args.runs)
    runs.mkdir(parents=True, exist_ok=True)
    try:
        httpd = ThreadingHTTPServer((HOST, int(args.port)), make_handler(runs))
    except OSError as exc:
        raise SystemExit(f"127.0.0.1:{args.port} is not free ({exc})")
    print(f"live board  http://{HOST}:{httpd.server_address[1]}/  runs {runs}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("board stopped", flush=True)
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
