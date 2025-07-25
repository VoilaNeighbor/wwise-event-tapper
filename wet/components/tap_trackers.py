import datetime as dt
from collections.abc import Callable
from logging import getLogger
from pathlib import Path

import polars as pl
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_logger = getLogger("wwise-event-tapper")


def _make_meta_control(
    export_callback: Callable[[], None],
    height: int = 23,
    label_align: Qt.AlignmentFlag = (
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    ),
) -> QWidget:
    ret = QWidget()

    export_button = QPushButton("Export")
    bpm_label = QLabel("BPM")
    bpm_spin = QSpinBox()
    bpm_spin.setRange(0, 999)
    offset_label = QLabel("Offset")
    offset_spin = QSpinBox()

    export_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    export_button.setFixedHeight(height)
    export_button.clicked.connect(export_callback)
    bpm_label.setFixedWidth(40)
    bpm_label.setAlignment(label_align)
    bpm_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    bpm_spin.setFixedHeight(height)
    offset_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    offset_label.setFixedWidth(40)
    offset_label.setAlignment(label_align)
    offset_spin.setFixedHeight(height)

    layout = QHBoxLayout(ret)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(export_button)
    layout.addWidget(bpm_label)
    layout.addWidget(bpm_spin)
    layout.addWidget(offset_label)
    layout.addWidget(offset_spin)

    return ret


class TapTracksContainer(QGroupBox):
    def __init__(self) -> None:
        super().__init__()

        self.setTitle("⭐ Tap Tracks")

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(10)

        meta_control = _make_meta_control(self.export_to_csv)
        self._layout.addWidget(meta_control)

        # Qt.Key -> milliseconds
        self._track_taps: dict[Qt.Key, list[tuple[int, int]]] = {
            Qt.Key.Key_J: [],
            Qt.Key.Key_K: [],
            Qt.Key.Key_L: [],
        }

        self._track_count_labels: dict[Qt.Key, QLabel] = {}

        # List tracks with a smaller spacing.
        track_layout = QVBoxLayout()
        for key in self._track_taps:
            layout = QHBoxLayout()
            track_label = QLabel(f"<strong>Track {key.name[4:]}</strong>")
            count_label = QLabel("[count: 0]")
            track_label.setFixedWidth(70)
            layout.addWidget(track_label)
            layout.addWidget(count_label)
            track_layout.addLayout(layout)
            track_layout.addStretch()
            self._track_count_labels[key] = count_label

        self._layout.addLayout(track_layout)
        self._layout.addStretch()

        # Public for use in the calibration pass.
        self.tap_csv_path: Path | None = None

    def tap(self, key: Qt.Key, timestamp: int, is_lift: bool) -> bool:
        """Add a tap if there is a track for the key."""
        if (track := self._track_taps.get(key)) is not None:
            if is_lift:
                track[-1] = track[-1][0], timestamp
            else:
                track.append((timestamp, 0))
            self._track_count_labels[key].setText(f"[count: {len(track)}]")
            return True
        return False

    def export_to_csv(self) -> None:
        now = dt.datetime.now().astimezone()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tap Tracks",
            f"tracks.{now:%Y%m%d_%H%M%S}.csv",
            "CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            _logger.info("No file selected")
            QMessageBox.information(self, "Export Failed", "No file selected")
            return

        if not file_path.endswith(".csv"):
            file_path += ".csv"

        data = [
            (key.name[4:], start_time, end_time)
            for key, track in self._track_taps.items()
            for start_time, end_time in track
        ]

        frame = pl.DataFrame(data, schema=["track", "start", "end"])
        frame.write_csv(file_path)
        self.tap_csv_path = Path(file_path).resolve(strict=True)
