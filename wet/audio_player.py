"""Audio player module with proper pause support using pygame and position tracking."""

import logging
import time
import wave
from contextlib import suppress
from pathlib import Path

import pygame
from mutagen import File as MutagenFile  # type: ignore
from PySide6.QtCore import QObject, QTimer, Signal

_logger = logging.getLogger("wwise-event-tapper")


def _estimate_duration(file_path: Path) -> float:
    """Estimate duration for non-WAV files."""
    try:
        # Try mutagen if available for better duration detection
        audio_file = MutagenFile(str(file_path))
        if audio_file and (info := getattr(audio_file, "info", None)):
            return float(info.length)

        # Fallback based on file size (rough estimate)
        file_size = file_path.stat().st_size
        # Rough estimate: 1MB ≈ 8-10 seconds for typical music
        estimated_duration = file_size / (128 * 1024)  # Assuming 128 kbps
        return max(30.0, min(estimated_duration, 600.0))  # Between 30s and 10min

    except Exception:
        _logger.exception("Failed to estimate duration for %s", file_path)
        return 180.0  # Default 3 minutes


class AudioPlayer(QObject):
    playback_started = Signal()
    playback_stopped = Signal()
    playback_paused = Signal()
    playback_resumed = Signal()
    duration_changed = Signal(float)  # Emit duration in seconds

    def __init__(self) -> None:
        super().__init__()

        # Instance variables
        self._current_file: Path | None = None
        self._is_playing = False
        self._is_paused = False
        self._duration: float = 0.0

        # Position tracking for proper pause/resume
        self._start_time: float | None = None
        self._pause_position: float = 0.0  # Position where we paused

        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        # Timer for position tracking
        self._position_timer = QTimer()
        self._position_timer.timeout.connect(self._update_position)
        self._position_timer.start(10)  # Update every 10ms

    def load_file(self, file_path: Path) -> bool:
        """Load an audio file for playback.

        Args:
            file_path: Path to the audio file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            self.stop()  # Stop any current playback

            # Load the file
            pygame.mixer.music.load(str(file_path))
            self._current_file = file_path

            # Try to get duration
            try:
                with wave.open(str(file_path), "rb") as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    self._duration = frames / float(rate)
            except Exception:
                _logger.exception("Failed to get duration for %s", file_path)
                # For non-WAV files, estimate duration
                self._duration = _estimate_duration(file_path)

            self.duration_changed.emit(self._duration)

        except pygame.error:
            return False

        return True

    def play(self) -> bool:
        """Start or resume playback.

        Returns:
            True if playback started successfully, False otherwise
        """
        if not self._current_file:
            return False

        try:
            if self._is_paused:
                # Resume from pause position
                # We can't seek with pygame.mixer.music, so we restart and fast-forward
                # For small pause positions, this is acceptable
                pygame.mixer.music.play(start=self._pause_position)
                self._start_time = time.perf_counter() - self._pause_position
                self._is_paused = False
                self._is_playing = True
                self.playback_resumed.emit()
            else:
                # Start from beginning
                pygame.mixer.music.play()
                self._start_time = time.perf_counter()
                self._pause_position = 0.0
                self._is_playing = True
                self._is_paused = False
                self.playback_started.emit()

        except pygame.error:
            return False

        return True

    def pause(self) -> None:
        """Pause playback by storing current position."""
        if self._is_playing and not self._is_paused:
            # Store current position
            self._pause_position = self.get_position()

            # Stop the music
            pygame.mixer.music.stop()

            self._is_paused = True
            # Keep _is_playing as True since we're just paused
            self.playback_paused.emit()

    def stop(self) -> None:
        """Stop playback."""
        pygame.mixer.music.stop()
        self._is_playing = False
        self._is_paused = False
        self._start_time = None
        self._pause_position = 0.0
        self.playback_stopped.emit()

    def is_playing(self) -> bool:
        """Check if audio is currently playing (not paused).

        Returns:
            True if playing, False if stopped or paused
        """
        return (
            self._is_playing and not self._is_paused and pygame.mixer.music.get_busy()
        )

    def is_paused(self) -> bool:
        """Check if audio is paused.

        Returns:
            True if paused, False otherwise
        """
        return self._is_paused

    def get_position(self) -> float:
        """Get current playback position in seconds.

        Returns:
            Current position in seconds from the start of the track
        """
        if self._is_paused:
            return self._pause_position

        if not self._start_time or not self._is_playing:
            return 0.0

        current_time = time.perf_counter()
        position = current_time - self._start_time

        # Clamp to duration
        return min(position, self._duration)

    def get_current_file(self) -> Path | None:
        """Get the currently loaded file.

        Returns:
            Path to current file or None if no file loaded
        """
        return self._current_file

    def get_duration(self) -> float:
        """Get the total duration of the loaded file in seconds."""
        return self._duration

    def _update_position(self) -> None:
        """Update position and check if playback has ended."""
        if self._is_playing and not self._is_paused:  # noqa: SIM102
            if not pygame.mixer.music.get_busy():  # noqa: SIM102
                # Music has ended
                if self.get_position() >= self._duration * 0.99:  # Allow small margin
                    self.stop()

    def __del__(self) -> None:
        """Cleanup on destruction."""
        with suppress(Exception):
            pygame.mixer.quit()
