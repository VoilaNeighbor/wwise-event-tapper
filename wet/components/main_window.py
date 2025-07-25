from logging import getLogger
from typing import override

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from wet.components.music_player import MusicPlayer
from wet.components.tap_trackers import TapTracksContainer
from wet.components.title_bar import TitleBar

_logger = getLogger("wwise-event-tapper")


class AppMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Wwise Event Tapper")
        self.setMinimumSize(500, 809)

        self._player = MusicPlayer()
        self._tap_tracks = TapTracksContainer()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        title_bar = TitleBar(self)
        layout.addWidget(title_bar)

        layout1 = QVBoxLayout()
        layout1.setContentsMargins(10, 10, 10, 10)
        layout1.addWidget(self._player)
        layout1.addWidget(self._tap_tracks)

        layout.addLayout(layout1)
        layout.addStretch()

        self._drag_start = QPoint()

    @override
    def keyPressEvent(self, event: QKeyEvent, /) -> None:
        key = Qt.Key(event.key())
        if key == Qt.Key.Key_Space:
            self._player.toggle_play()
            event.accept()
        elif self._player.playing:
            self._tap_tracks.tap(key, self._player.position, is_lift=False)
            event.accept()
        else:
            super().keyPressEvent(event)

    @override
    def keyReleaseEvent(self, event: QKeyEvent, /) -> None:
        if self._player.playing:
            key = Qt.Key(event.key())
            self._tap_tracks.tap(key, self._player.position, is_lift=True)
            event.accept()
        else:
            super().keyReleaseEvent(event)
