"""A dependency-free HTTP demo, intentionally small enough for a workshop.

The standard library HTTP server is for teaching, not production hosting.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from importlib.resources import files
from urllib.parse import parse_qs, urlsplit

from cicd_demo.shipping import shipping_quote


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        request = urlsplit(self.path)
        if request.path == "/":
            # This file must be inside the wheel, not just present in the checkout.
            body = files("cicd_demo").joinpath("resources/index.html").read_bytes()
            self.respond(200, body, "text/html; charset=utf-8")
        elif request.path == "/health":
            self.respond_json(200, {"status": "ok", "version": version("cicd-demo")})
        elif request.path == "/api/quote":
            try:
                values = parse_qs(request.query, keep_blank_values=True).get("subtotal_cents", [])
                if len(values) != 1 or not values[0].isascii() or not values[0].isdecimal():
                    raise ValueError("provide subtotal_cents once as a non-negative integer")
                quote = shipping_quote(int(values[0]))
            except ValueError as error:
                self.respond_json(400, {"error": str(error)})
            else:
                self.respond_json(200, quote)
        else:
            self.respond_json(404, {"error": "not found"})

    def respond_json(self, status: int, payload: dict) -> None:
        self.respond(status, json.dumps(payload).encode(), "application/json")

    def respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CI/CD demo API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer((args.host, args.port), DemoHandler) as server:
        # The smoke test uses the OS-selected port when --port=0.
        print(json.dumps({"host": args.host, "port": server.server_port}), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
