"""HTTP interface for the Campus Event Notifier."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from event_notifier.events import EventRepository, event_from_payload

LOGGER = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 16_384


def make_server(
    host: str, port: int, repository: EventRepository
) -> ThreadingHTTPServer:
    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._send_html()
            elif self.path == "/api/events":
                try:
                    events = repository.list_upcoming()
                    self._send_json(200, [event.to_dict() for event in events])
                except (OSError, ValueError):
                    LOGGER.exception("Unable to load upcoming events")
                    self._send_json(500, {"error": "Unable to load events."})
            else:
                self._send_json(404, {"error": "Not found."})

        def do_POST(self) -> None:
            if self.path != "/api/events":
                self._send_json(404, {"error": "Not found."})
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(400, {"error": "Invalid Content-Length header."})
                return
            if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
                self._send_json(400, {"error": "Request body must be between 1 and 16384 bytes."})
                return

            try:
                payload: Any = json.loads(self.rfile.read(content_length))
                event = event_from_payload(payload)
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                self._send_json(400, {"error": str(error)})
                return
            try:
                repository.add(event)
            except (OSError, ValueError):
                LOGGER.exception("Unable to save event")
                self._send_json(500, {"error": "Unable to save the event."})
                return

            self._send_json(201, event.to_dict())

        def _send_html(self) -> None:
            try:
                page = Path(__file__).with_name("index.html").read_bytes()
            except OSError:
                LOGGER.exception("Unable to load application page")
                self._send_json(500, {"error": "Unable to load the application page."})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(page)

        def _send_json(self, status: int, value: Any) -> None:
            body = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format_string: str, *args: object) -> None:
            LOGGER.info("%s - %s", self.address_string(), format_string % args)

    return ThreadingHTTPServer((host, port), RequestHandler)
