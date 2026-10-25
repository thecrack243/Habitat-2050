"""Loopback-only API for the independent Habitat 2050 frontend."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(FRONTEND))

from api.dashboard import build_dashboard_payload, build_evidence_export


LOGGER = logging.getLogger("habitat2050.frontend_api")
HOST = "127.0.0.1"
PORT = 8765
MAX_REQUEST_BYTES = 4096


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "Habitat2050LocalAPI/1.0"

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(
            payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        try:
            if self.path == "/api/health":
                self._send_json(200, {"status": "ok"})
                return
            if self.path == "/api/dashboard":
                self._send_json(200, build_dashboard_payload())
                return
            self._send_json(404, {"error": "API route not found."})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:
            LOGGER.exception("GET request failed for %s", self.path)
            if not self.wfile.closed:
                self._send_json(500, {"error": "Unable to build dashboard results."})

    def do_POST(self) -> None:
        if self.path != "/api/export":
            self._send_json(404, {"error": "API route not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid Content-Length header."})
            return
        if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request body is empty or too large."})
            return

        try:
            request = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return
        if not isinstance(request, dict):
            self._send_json(400, {"error": "Request body must be a JSON object."})
            return

        try:
            content = build_evidence_export(request.get("threshold"))
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except Exception:
            LOGGER.exception("Evidence export failed.")
            self._send_json(500, {"error": "Unable to create the evidence export."})
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", 'attachment; filename="habitat-2050-evidence.zip"')
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, message: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), message % args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with ThreadingHTTPServer((HOST, PORT), DashboardHandler) as server:
        LOGGER.info("Habitat 2050 API listening on http://%s:%s", HOST, PORT)
        server.serve_forever()


if __name__ == "__main__":
    main()
