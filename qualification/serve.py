"""Loopback-only synthetic preview harness. Never a production document server."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).with_name("static")
WORK = ROOT / ".qualification"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = self.path.split("?")[0]
        routes = {
            "/": (STATIC / "index.html", "text/html"),
            "/viewer/drawio": (STATIC / "drawio.html", "text/html"),
            "/viewer.js": (WORK / "assets/viewer-static.min.js", "text/javascript"),
            "/stencils.js": (WORK / "assets/stencils.min.js", "text/javascript"),
        }
        if route in routes:
            target, mime = routes[route]
        elif route.removeprefix("/") in {"main.js", "drawio.js", "config.js", "style.css"}:
            target = STATIC / route[1:]
            mime = "text/css" if target.suffix == ".css" else "text/javascript"
        else:
            target = WORK / "preview" / route.removeprefix("/")
            if not target.resolve().is_relative_to((WORK / "preview").resolve()):
                self.send_error(404)
                return
            mime = {".json": "application/json", ".png": "image/png", ".jpeg": "image/jpeg", ".pdf": "application/pdf", ".mjs": "text/javascript"}.get(target.suffix, "application/octet-stream")
        if not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        if route == "/viewer/drawio":
            data = (WORK / "preview/drawio-pages.json").read_text().replace("</", "<\\/")
            body = body.replace(b"__PAGES__", data.encode())
        self.send_response(200)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; frame-src 'self'; font-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(format % args, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8788)
    arguments = parser.parse_args()
    print(f"Synthetic M0 preview: http://127.0.0.1:{arguments.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", arguments.port), Handler).serve_forever()
