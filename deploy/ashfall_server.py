"""Standalone public ASHFALL server for Railway.

Zero database credentials, no Docker or Django process. Only serves the
player landing page, its public assets and curated public JSON.
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent.parent
PUBLIC_API = os.getenv(
    "ASHFALL_PUBLIC_API_URL",
    "https://nightwell-dev-web-production.up.railway.app/api/public/ashfall/",
)
CACHE_LOCK = threading.Lock()
CACHE = {"until": 0.0, "value": None}


def published_json():
    with CACHE_LOCK:
        now = time.monotonic()
        if CACHE["value"] is not None and now < CACHE["until"]:
            return CACHE["value"]
    try:
        req = Request(PUBLIC_API, headers={"Accept": "application/json", "User-Agent": "ASHFALL-Public-Site/1.0"})
        with urlopen(req, timeout=4) as response:
            if response.status != 200:
                raise ValueError("Unexpected public API status")
            content = response.read(256 * 1024)
        data = json.loads(content)
        if data.get("schema") != 1 or "published" not in data:
            raise ValueError("Unexpected public JSON schema")
        result = json.dumps(data, ensure_ascii=False).encode("utf-8")
    except (OSError, ValueError, json.JSONDecodeError):
        result = (BASE / "ashfall" / "data" / "public.json").read_bytes()
    with CACHE_LOCK:
        CACHE.update(value=result, until=time.monotonic() + 45)
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "ASHFALL/1.0"

    def send(self, code, data, mime, cache):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def handle_path(self):
        path = urlsplit(self.path).path
        if path in ("/", "/index.html", "/ashfall/"):
            return BASE / "ashfall" / "index.html", "text/html; charset=utf-8", "public, max-age=90"
        if path == "/data/public.json" or path == "/ashfall/data/public.json":
            return None, "application/json; charset=utf-8", "public, max-age=45"
        assets = {
            "/static/player/site.css": ("site.css", "text/css; charset=utf-8"),
            "/static/player/site.js": ("site.js", "text/javascript; charset=utf-8"),
            "/static/player/icon.svg": ("icon.svg", "image/svg+xml"),
        }
        if path in assets:
            filename, mime = assets[path]
            return BASE / "static" / "player" / filename, mime, "public, max-age=3600"
        return False, None, None

    def do_GET(self):
        resource, mime, cache = self.handle_path()
        if resource is False:
            self.send(404, b"Not Found", "text/plain; charset=utf-8", "no-store")
            return
        try:
            data = published_json() if resource is None else resource.read_bytes()
            self.send(200, data, mime, cache)
        except OSError:
            self.send(503, b"Unavailable", "text/plain; charset=utf-8", "no-store")

    def do_HEAD(self):
        self.do_GET()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"ASHFALL public website listening on {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
