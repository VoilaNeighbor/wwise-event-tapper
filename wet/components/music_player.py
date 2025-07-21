import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


def _format_time(ms: int) -> str:
    s = ms // 1000
    return f"{s // 60:02d}:{s % 60:02d}"


class MusicPlayer(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._player = QMediaPlayer()
        self._label = QLabel("No music loaded.")
        self._play_button = QPushButton("Play")
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_label = QLabel("00:00 / 00:00")

        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._play_button.setEnabled(False)
        self._play_button.setFixedSize(70, 30)
        self._progress_slider.setEnabled(False)
        self._progress_label.setStyleSheet("color: gray;")

        self._player.positionChanged.connect(self._on_music_position_change)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        self._play_button.clicked.connect(self._on_play_button)
        self._progress_slider.sliderMoved.connect(self._player.setPosition)

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self._play_button)
        progress_layout.addWidget(self._progress_slider)
        progress_layout.addWidget(self._progress_label)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self._label)
        layout.addLayout(progress_layout)

        if __debug__:
            self.load_music_file("assets/Alexander Klaws - Cry on My Shoulder.ogg")

    def _on_music_position_change(self, value: int) -> None:
        self._progress_slider.setValue(value)
        self._progress_label.setText(
            f"{_format_time(value)} / {_format_time(self._player.duration())}"
        )

    def _on_play_button(self) -> None:
        if self._player.isPlaying():
            self._player.pause()
            self._play_button.setText("Play")
        else:
            self._player.play()
            self._play_button.setText("Pause")

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Update the length label.
            self._on_music_position_change(0)
            self._progress_slider.setMaximum(self._player.duration())
            self._progress_slider.setEnabled(True)
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._play_button.setText("Play")

    def load_music_file(self, file_path: str) -> None:
        self._label.setText(f"Loaded: <strong>{os.path.basename(file_path)}</strong>")
        self._player.setSource(QUrl.fromLocalFile(file_path))
        self._play_button.setText("Play")
        self._play_button.setEnabled(True)
        # Further changes are delayed until MediaStatus changes to LoadedMedia.
