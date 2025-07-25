from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
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


class TapTracksContainer(QGroupBox):
    def __init__(self) -> None:
        super().__init__()

        self.setTitle("⭐ Tap Tracks")

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(_make_bpm_control())

        # Qt.Key -> milliseconds
        self._track_taps: dict[Qt.Key, list[int]] = {
            Qt.Key.Key_J: [],
            Qt.Key.Key_K: [],
            Qt.Key.Key_L: [],
        }

        self._track_count_labels: dict[Qt.Key, QLabel] = {}

        for key in self._track_taps:
            layout = QHBoxLayout()
            track_label = QLabel(f"<strong>Track {key.name[4:]}</strong>")
            count_label = QLabel("[count: 0]")
            track_label.setFixedWidth(70)
            layout.addWidget(track_label)
            layout.addWidget(count_label)
            self._layout.addLayout(layout)
            self._layout.addStretch()
            self._track_count_labels[key] = count_label

    def tap(self, key: Qt.Key, value: int) -> bool | None:
        """Add a tap if there is a track for the key."""
        if track := self._track_taps.get(key):
            track.append(value)
            self._track_count_labels[key].setText(f"[count: {len(track)}]")
            return True
