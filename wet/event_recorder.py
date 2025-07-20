"""Event recorder module for capturing tap events with timestamps."""

import datetime as dt
import logging
import time
from pathlib import Path

import orjson
from attrs import asdict, define

_logger = logging.getLogger("wwise-event-tapper")


@define
class TapEvent:
    """A single tap event."""

    timestamp: float  # seconds from music start
    absolute_time: float  # seconds since epoch


class EventRecorder:
    def __init__(self) -> None:
        self._events: list[TapEvent] = []
        self._recording = False

    def start_recording(self) -> None:
        self._recording = True

    def stop_recording(self) -> None:
        self._recording = False

    def record_event(self, music_offset: float) -> None:
        """Record a tap event at the given music offset (seconds)."""
        event = TapEvent(
            timestamp=music_offset,
            absolute_time=time.time(),
        )

        self._events.append(event)

    def get_events(self) -> list[TapEvent]:
        return self._events.copy()

    def export_events(self, file_path: Path) -> None:
        events_data = {
            "metadata": {
                "export_time": dt.datetime.now(dt.UTC).isoformat(),
                "total_events": len(self._events),
                "version": "1.0",
            },
            "events": [asdict(event) for event in self._events],
        }

        file_path.write_bytes(orjson.dumps(events_data))

    def is_recording(self) -> bool:
        return self._recording
