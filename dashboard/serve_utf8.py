from __future__ import annotations

import os
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


class Utf8StaticHandler(SimpleHTTPRequestHandler):
    def guess_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        return UTF8_CONTENT_TYPES.get(suffix, super().guess_type(path))


def main() -> None:
    os.chdir(Path(__file__).resolve().parent)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Utf8StaticHandler)
    print("Dashboard UTF-8 server: http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
