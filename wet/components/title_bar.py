from typing import override

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton

_title_bar_style = """
    QFrame {
        background-color: #2c3e50;
        border-bottom: 1px solid #34495e;
    }
"""

_exit_button_style = """
    QPushButton {
        background: transparent;
        color: white;
        border: none;
        font-size: 14px;
        font-weight: bold;
        text-align: center;
        padding: 0px;
        margin: 0px;
    }
    QPushButton:hover {
        background-color: #e74c3c;
        border-radius: 2px;
    }
"""


class TitleBar(QFrame):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__()
        self._window = window

        self.setFixedHeight(30)
        self.setStyleSheet(_title_bar_style)

        self._exit_button = QPushButton("×")  # noqa: RUF001
        self._exit_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._exit_button.setFixedSize(24, 24)
        self._exit_button.setStyleSheet(_exit_button_style)
        self._exit_button.clicked.connect(self._window.close)

        title_label = QLabel("Wwise Event Tapper")
        title_label.setStyleSheet("color: white; font-weight: bold")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self._exit_button)

    @override
    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            global_point = event.globalPosition().toPoint()
            self._drag_start = global_point - self._window.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        # Triggered when _only_ the left button is pressed.
        if event.buttons() == Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()
            return
        super().mouseMoveEvent(event)
