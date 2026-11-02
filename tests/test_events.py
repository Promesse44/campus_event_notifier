from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from event_notifier.events import EventRepository, event_from_payload
from event_notifier.server import make_server


class EventValidationTests(unittest.TestCase):
    def test_builds_event_with_timezone_aware_start_time(self) -> None:
        event = event_from_payload(
            {
                "title": "Tech Meetup",
                "description": "Talks and networking",
                "location": "Main Hall",
                "starts_at": "2030-10-10T18:00:00+03:00",
            }
        )
        self.assertEqual(event.title, "Tech Meetup")
        self.assertEqual(event.starts_at.utcoffset(), timedelta(hours=3))

    def test_rejects_missing_required_field(self) -> None:
        with self.assertRaisesRegex(ValueError, "Title is required"):
            event_from_payload(
                {
                    "title": " ",
                    "description": "",
                    "location": "Main Hall",
                    "starts_at": "2030-10-10T18:00:00Z",
                }
            )

    def test_rejects_start_time_without_timezone(self) -> None:
        with self.assertRaisesRegex(ValueError, "must include a timezone"):
            event_from_payload(
                {
                    "title": "Tech Meetup",
                    "description": "",
                    "location": "Main Hall",
                    "starts_at": "2030-10-10T18:00:00",
                }
            )


class EventRepositoryTests(unittest.TestCase):
    def test_saves_and_sorts_only_upcoming_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = EventRepository(Path(directory) / "nested" / "events.json")
            now = datetime(2030, 1, 1, tzinfo=timezone.utc)
            for title, start in (
                ("Later event", now + timedelta(days=2)),
                ("Past event", now - timedelta(days=1)),
                ("Soon event", now + timedelta(hours=1)),
            ):
                repository.add(
                    event_from_payload(
                        {
                            "title": title,
                            "description": "",
                            "location": "Campus",
                            "starts_at": start.isoformat(),
                        }
                    )
                )

            upcoming = repository.list_upcoming(now)
            self.assertEqual([event.title for event in upcoming], ["Soon event", "Later event"])

            saved = json.loads(repository.path.read_text(encoding="utf-8"))
            self.assertEqual(len(saved), 3)


class EventHttpTests(unittest.TestCase):
    def test_http_api_creates_and_lists_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server = make_server(
                "127.0.0.1", 0, EventRepository(Path(directory) / "events.json")
            )
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                event_data = {
                    "title": "Student Fair",
                    "description": "Meet campus clubs",
                    "location": "Quad",
                    "starts_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
                }
                request = Request(
                    f"{base_url}/api/events",
                    data=json.dumps(event_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request) as response:
                    self.assertEqual(response.status, 201)
                    created = json.load(response)
                self.assertEqual(created["title"], "Student Fair")

                with urlopen(f"{base_url}/api/events") as response:
                    listed = json.load(response)
                self.assertEqual([event["title"] for event in listed], ["Student Fair"])

                with urlopen(f"{base_url}/") as response:
                    self.assertIn(b"Campus Event Notifier", response.read())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_http_api_reports_invalid_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server = make_server(
                "127.0.0.1", 0, EventRepository(Path(directory) / "events.json")
            )
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                request = Request(
                    f"http://127.0.0.1:{server.server_port}/api/events",
                    data=b'{"title": ""}',
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request)
                self.assertEqual(raised.exception.code, 400)
                self.assertIn("Title is required", raised.exception.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
