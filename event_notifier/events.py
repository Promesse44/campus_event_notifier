"""Event validation and JSON-backed storage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Event:
    id: str
    title: str
    description: str
    location: str
    starts_at: datetime

    def to_dict(self) -> dict[str, str]:
        values = asdict(self)
        values["starts_at"] = self.starts_at.isoformat()
        return values


def event_from_payload(payload: Any) -> Event:
    if not isinstance(payload, dict):
        raise ValueError("The event body must be a JSON object.")

    fields: dict[str, str] = {}
    for name, max_length in (
        ("title", 120),
        ("description", 2000),
        ("location", 200),
        ("starts_at", 40),
    ):
        value = payload.get(name)
        if not isinstance(value, str):
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be text.")
        value = value.strip()
        if not value and name != "description":
            raise ValueError(f"{name.replace('_', ' ').capitalize()} is required.")
        if len(value) > max_length:
            raise ValueError(
                f"{name.replace('_', ' ').capitalize()} must be "
                f"{max_length} characters or fewer."
            )
        fields[name] = value

    try:
        starts_at = datetime.fromisoformat(fields["starts_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Start time must be a valid ISO 8601 date and time.") from error
    if starts_at.tzinfo is None or starts_at.utcoffset() is None:
        raise ValueError("Start time must include a timezone.")

    return Event(
        id=str(uuid4()),
        title=fields["title"],
        description=fields["description"],
        location=fields["location"],
        starts_at=starts_at,
    )


class EventRepository:
    """Persist campus events in a local JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def list_upcoming(self, now: datetime | None = None) -> list[Event]:
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None or current_time.utcoffset() is None:
            raise ValueError("The comparison time must include a timezone.")
        return sorted(
            (event for event in self._read() if event.starts_at > current_time),
            key=lambda event: event.starts_at,
        )

    def add(self, event: Event) -> None:
        events = self._read()
        events.append(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            temporary_path.write_text(
                json.dumps([item.to_dict() for item in events], indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError:
            temporary_path.unlink(missing_ok=True)
            raise

    def _read(self) -> list[Event]:
        try:
            contents = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except OSError:
            raise

        try:
            data = json.loads(contents)
            if not isinstance(data, list):
                raise ValueError("The event data file must contain a JSON list.")
            events = []
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("Each saved event must be a JSON object.")
                starts_at = datetime.fromisoformat(
                    item["starts_at"].replace("Z", "+00:00")
                )
                if starts_at.tzinfo is None or starts_at.utcoffset() is None:
                    raise ValueError("A saved event has a start time without a timezone.")
                events.append(
                    Event(
                        id=item["id"],
                        title=item["title"],
                        description=item["description"],
                        location=item["location"],
                        starts_at=starts_at,
                    )
                )
            return events
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read event data from {self.path}.") from error
