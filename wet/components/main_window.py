from logging import getLogger

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from wet.components.music_player import MusicPlayer
from wet.components.title_bar import TitleBar

_logger = getLogger("wwise-event-tapper")


class AppMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Wwise Event Tapper")
        self.setMinimumSize(600, 400)

        self._player = MusicPlayer()

        title_bar = TitleBar()
        title_bar.exit_button.clicked.connect(self.close)
        title_bar.select_file_button.clicked.connect(self._on_select_file)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title_bar)
        layout.addWidget(self._player)
        layout.addStretch()
        self.setCentralWidget(widget)

        self._drag_start = QPoint()

    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            global_point = event.globalPosition().toPoint()
            self._drag_start = global_point - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        # Triggered when _only_ the left button is pressed.
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def _on_select_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            caption="Select Audio File",
            dir="",
            filter="Audio Files (*.mp3 *.wav *.ogg);;All Files (*)",
        )
        if file_path:
            self._player.load_music_file(file_path)
        else:
            QMessageBox.warning(self, "Error", f"Failed to load music at {file_path}")
