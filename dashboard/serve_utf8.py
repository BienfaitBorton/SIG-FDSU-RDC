from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


UTF8_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}

DASHBOARD_DIR = Path(__file__).resolve().parent
BUSINESS_DATA_DIR = DASHBOARD_DIR.parent / "data" / "business"
PROGRAMS_DATA_DIR = DASHBOARD_DIR.parent / "data" / "programs"
HEALTH_PATH = "/healthz"


class DashboardServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class Utf8StaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def guess_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        return UTF8_CONTENT_TYPES.get(suffix, super().guess_type(path))

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == HEALTH_PATH:
            payload = json.dumps(
                {"status": "ok", "service": "sig-fdsu-dashboard"},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        if getattr(self.server, "verbose", False):
            super().log_message(format, *args)

    def translate_path(self, path: str) -> str:
        normalized = path.split("?", 1)[0].split("#", 1)[0]
        for prefix, root_dir in (
            ("/business/", BUSINESS_DATA_DIR),
            ("/programs/", PROGRAMS_DATA_DIR),
        ):
            if normalized.startswith(prefix):
                relative = normalized[len(prefix):].lstrip("/")
                if relative and ".." not in Path(relative).parts:
                    data_root = root_dir.resolve()
                    candidate = (root_dir / relative).resolve()
                    try:
                        candidate.relative_to(data_root)
                    except ValueError:
                        pass
                    else:
                        if candidate.is_file():
                            return str(candidate)
        return super().translate_path(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serveur local UTF-8 du dashboard SIG-FDSU RDC")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.chdir(DASHBOARD_DIR)
    try:
        server = DashboardServer((args.host, args.port), Utf8StaticHandler)
    except OSError as exc:
        print(f"Dashboard indisponible sur {args.host}:{args.port}: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1) from exc

    server.verbose = args.verbose

    def stop_server(_signum: int, _frame: object) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, stop_server)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_server)

    print(f"Dashboard UTF-8 prêt: http://{args.host}:{args.port}{HEALTH_PATH}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
