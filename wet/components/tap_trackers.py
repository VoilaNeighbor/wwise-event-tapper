from collections import defaultdict

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


def _make_bpm_control() -> QWidget:
    ret = QWidget()
    bpm_label = QLabel("BPM")
    bpm_spin = QSpinBox()
    bpm_spin.setFixedHeight(25)
    bpm_spin.setRange(0, 999)
    offset_label = QLabel("Offset")
    offset_spin = QSpinBox()
    offset_spin.setFixedHeight(25)
    layout = QHBoxLayout(ret)
    layout.setSpacing(10)
    layout.addWidget(bpm_label)
    layout.addWidget(bpm_spin)
    layout.addWidget(offset_label)
    layout.addWidget(offset_spin)
    layout.addStretch()
    return ret


def _make_track(key: str) -> QWidget:
    ret = QWidget()
    label = QLabel(f"Track {key}")
    label.setFixedWidth(60)
    button = QPushButton("Tap")
    button.setFixedSize(50, 30)
    layout = QHBoxLayout(ret)
    layout.setSpacing(10)
    layout.addWidget(label)
    layout.addWidget(button)
    layout.addStretch()
    return ret


class TapTracksContainer(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(_make_bpm_control())

        # QtKey -> milliseconds
        self._taps: defaultdict[int, list[int]] = defaultdict(list)

        keys = ["J", "K", "L"]
        for key in keys:
            widget = _make_track(key)
            self._layout.addWidget(widget)
