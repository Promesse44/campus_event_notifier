"""Run the local Campus Event Notifier web application."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from event_notifier.events import EventRepository
from event_notifier.server import make_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Campus Event Notifier locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    parser.add_argument(
        "--data-file",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "events.json",
        help="Path to the JSON file used to store events.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    server = make_server(args.host, args.port, EventRepository(args.data_file))
    print(f"Campus Event Notifier is running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Campus Event Notifier.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
