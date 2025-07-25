from logging import getLogger
from typing import override

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
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
        self.setMinimumSize(600, 400)

        self._player = MusicPlayer()
        self._tap_tracks = TapTracksContainer()

        title_bar = TitleBar()
        title_bar.exit_button.clicked.connect(self.close)
        title_bar.select_file_button.clicked.connect(self._player.load_music_file)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title_bar)

        layout1 = QVBoxLayout()
        layout1.setContentsMargins(10, 10, 10, 10)
        layout1.addWidget(self._player)
        layout1.addWidget(self._tap_tracks)

        layout.addLayout(layout1)
        layout.addStretch()

        self._drag_start = QPoint()

    def onGlobalKeyPress(self, key: Qt.Key) -> bool | None:
        if self._player.playing:
            return self._tap_tracks.tap(key, self._player.position)

    @override
    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            global_point = event.globalPosition().toPoint()
            self._drag_start = global_point - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        # Triggered when _only_ the left button is pressed.
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()
        else:
            super().mouseMoveEvent(event)
