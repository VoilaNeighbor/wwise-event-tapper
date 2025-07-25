from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSpinBox


def make_button(text: str, height: int = 23, width: int = 0) -> QPushButton:
    button = QPushButton(text)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setFixedHeight(height)
    if width:
        button.setFixedWidth(width)
    return button


def make_spinbox(minmax: tuple[int, int], height: int = 23) -> QSpinBox:
    spinbox = QSpinBox()
    spinbox.setRange(*minmax)
    spinbox.setFixedHeight(height)
    return spinbox
