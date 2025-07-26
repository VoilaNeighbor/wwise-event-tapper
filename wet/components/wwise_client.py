from logging import getLogger
from typing import Any

from waapi import WaapiClient  # type: ignore[import]

_logger = getLogger("wwise-event-tapper")
_instances: list[WaapiClient] = []


class WwiseController(WaapiClient):
    def __init__(self) -> None:
        super().__init__()  # type: ignore
        _instances.append(self)

    def get_music_segments(self) -> list[dict[str, Any]]:
        """Get all music segments from Wwise."""
        try:
            args = {"waql": "from type MusicSegment"}
            opts = {"return": ["id", "name", "path"]}
            result = self.call("ak.wwise.core.object.get", args, options=opts)  # type: ignore
            if result and isinstance(result, dict):
                return result.get("return", [])  # type: ignore
        except Exception:
            _logger.exception("Failed to get music segments")
        return []

    def create_cue(
        self, name: str, segment_id: str, time_ms: int, cue_type: int = 2
    ) -> bool:
        """Create a cue in the specified segment."""
        args = {
            "name": name,
            "parent": segment_id,
            "type": "MusicCue",
            "list": "Cues",
            "@TimeMs": time_ms,
            "@CueType": cue_type,
        }
        result = self.call("ak.wwise.core.object.create", args)  # type: ignore
        return result is not None

    def save_project(self) -> None:
        self.call("ak.wwise.core.project.save", {})  # type: ignore

    def clear_custom_cues(self, segment_id: str) -> int:
        """Clear custom cues (CueType > 1) from segment. Returns count deleted."""
        deleted_count = 0

        args = {
            "waql": f'from object "{segment_id}" select descendants where type = "MusicCue"'  # noqa: E501
        }
        opts = {"return": ["id", "name", "CueType"]}

        result = self.call("ak.wwise.core.object.get", args, options=opts)  # type: ignore
        if not result:
            return 0

        cues = result.get("return", [])  # type: ignore
        if not cues:
            return 0

        for cue in cues:  # type: ignore
            cue_type = cue.get("CueType", 0)  # type: ignore[assignment]
            cue_id = cue.get("id")  # type: ignore[assignment]
            # Only delete custom cues
            if isinstance(cue_type, int) and cue_type > 1 and cue_id:
                delete_args = {"object": cue_id}  # type: ignore[dict-item]
                self.call("ak.wwise.core.object.delete", delete_args)  # type: ignore
                deleted_count += 1

        return deleted_count


def shutdown_instances() -> None:
    for instance in _instances:
        instance.disconnect()
