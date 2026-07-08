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

DASHBOARD_DIR = Path(__file__).resolve().parent
BUSINESS_DATA_DIR = DASHBOARD_DIR.parent / "data" / "business"


class Utf8StaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def guess_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        return UTF8_CONTENT_TYPES.get(suffix, super().guess_type(path))

    def translate_path(self, path: str) -> str:
        normalized = path.split("?", 1)[0].split("#", 1)[0]
        if normalized.startswith("/business/"):
            relative = normalized[len("/business/"):].lstrip("/")
            if relative and ".." not in Path(relative).parts:
                business_root = BUSINESS_DATA_DIR.resolve()
                candidate = (BUSINESS_DATA_DIR / relative).resolve()
                try:
                    candidate.relative_to(business_root)
                except ValueError:
                    pass
                else:
                    if candidate.is_file():
                        return str(candidate)
        return super().translate_path(path)


def main() -> None:
    os.chdir(DASHBOARD_DIR)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Utf8StaticHandler)
    print("Dashboard UTF-8 server: http://127.0.0.1:8000")
    print(f"Business data: {BUSINESS_DATA_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
