from __future__ import annotations

import json
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Deque, Dict, Optional
from urllib.parse import parse_qs, urlparse


class TelemetryHttpFeed:
    """Very small HTTP feed for dashboards and robot publisher pages.

    Endpoints:
    - GET /health
    - GET /latest
    - GET /history?limit=100
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, history_limit: int = 1000) -> None:
        self.host = host
        self.port = port
        self._history: Deque[Dict[str, Any]] = deque(maxlen=history_limit)
        self._latest: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def update(self, payload: Dict[str, Any]) -> None:
        with self._lock:
            self._latest = payload
            self._history.append(payload)

    def start(self) -> None:
        if self._server is not None:
            return

        feed = self

        class Handler(BaseHTTPRequestHandler):
            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(204)
                self._cors_headers()
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                path = parsed.path

                if path == "/health":
                    self._respond_json({"ok": True})
                    return

                if path == "/latest":
                    with feed._lock:
                        payload = dict(feed._latest)
                    self._respond_json(payload)
                    return

                if path == "/history":
                    query = parse_qs(parsed.query)
                    try:
                        limit = int(query.get("limit", [100])[0])
                    except ValueError:
                        limit = 100
                    limit = max(1, min(5000, limit))
                    with feed._lock:
                        payload = list(feed._history)[-limit:]
                    self._respond_json(payload)
                    return

                self._respond_json(
                    {
                        "message": "Telemetry feed",
                        "endpoints": ["/health", "/latest", "/history?limit=100"],
                    },
                    status=404,
                )

            def _respond_json(self, payload: Any, status: int = 200) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self._cors_headers()
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _cors_headers(self) -> None:
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
