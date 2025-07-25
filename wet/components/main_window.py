from logging import getLogger
from typing import override

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QSpinBox, QVBoxLayout, QWidget

from wet.components.calibrator import TapCalibrator
from wet.components.music_player import MusicPlayer
from wet.components.title_bar import TitleBar
from wet.components.tracks import TapTracksContainer

_logger = getLogger("wwise-event-tapper")


class AppMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Wwise Event Tapper")
        self.setFixedSize(500, 800)

        self._player = MusicPlayer()
        self._tap_tracks = TapTracksContainer()
        self._calibrator = TapCalibrator()

        self._tap_tracks.tracks_exported.connect(self._calibrator.on_tracks_exported)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        title_bar = TitleBar(self)
        layout.addWidget(title_bar)

        # For contents, add some margin.
        layout1 = QVBoxLayout()
        layout1.setContentsMargins(10, 10, 10, 10)
        layout1.addWidget(self._player)
        layout1.addWidget(self._tap_tracks)
        layout1.addWidget(self._calibrator)

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

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Clear the focus if clicking on another position.
        # -- We emulate this effect by clearing the focus and then re-trigger
        # -- the mouse event.
        focused = QApplication.focusWidget()
        if isinstance(focused, QSpinBox):
            focused.clearFocus()
        super().mousePressEvent(event)
