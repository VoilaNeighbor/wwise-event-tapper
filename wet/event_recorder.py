"""Event recorder module for capturing tap events with timestamps."""

import datetime as dt
import logging
import time
from pathlib import Path
from typing import Any

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
        self._recording_start_counter = 0.0

    def start_recording(self) -> None:
        self._recording = True
        self._recording_start_counter = time.perf_counter()

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

    def clear_events(self) -> None:
        self._events.clear()

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

    def import_events(self, file_path: Path) -> bool:
        try:
            data = orjson.loads(file_path.read_bytes())

            # Clear existing events
            self._events.clear()

            # Load events
            for event_data in data.get("events", []):
                event = TapEvent(
                    timestamp=event_data["timestamp"],
                    absolute_time=event_data["absolute_time"],
                )
                self._events.append(event)

        except (orjson.JSONDecodeError, KeyError, FileNotFoundError):
            _logger.exception("Error importing events")
            return False

        else:
            return True

    def get_event_statistics(self) -> dict[str, Any]:
        if not self._events:
            return {
                "total_events": 0,
                "duration": 0.0,
                "average_interval": 0.0,
                "min_interval": 0.0,
                "max_interval": 0.0,
            }

        timestamps = [event.timestamp for event in self._events]
        intervals: list[float] = []

        for i in range(1, len(timestamps)):
            interval = timestamps[i] - timestamps[i - 1]
            intervals.append(interval)

        return {
            "total_events": len(self._events),
            "duration": max(timestamps) - min(timestamps) if timestamps else 0.0,
            "first_event": min(timestamps) if timestamps else 0.0,
            "last_event": max(timestamps) if timestamps else 0.0,
            "average_interval": sum(intervals) / len(intervals) if intervals else 0.0,
            "min_interval": min(intervals) if intervals else 0.0,
            "max_interval": max(intervals) if intervals else 0.0,
        }

    def is_recording(self) -> bool:
        return self._recording
