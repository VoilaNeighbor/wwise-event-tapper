import datetime as dt
from logging import getLogger
from pathlib import Path

import polars as pl
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

from wet.components.util import make_button

_logger = getLogger("wwise-event-tapper")


class TapTracksContainer(QGroupBox):
    tracks_exported = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setTitle("⭐ Tap Tracks")

        layout_l = QVBoxLayout()
        layout_l.setSpacing(10)

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

        layout_l.addLayout(track_layout)
        layout_l.addStretch()

        # Put the export button to the right
        export_button = make_button("Export")
        export_button.clicked.connect(self.export_to_csv)
        layout_r = QHBoxLayout()
        layout_r.addStretch()
        layout_r.addWidget(export_button)
        layout_tr = QVBoxLayout()
        layout_tr.addLayout(layout_r)
        layout_tr.addStretch()

        self._layout = QHBoxLayout(self)
        self._layout.addLayout(layout_l)
        self._layout.addLayout(layout_tr)

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
            f"raw_taps.{now:%Y%m%d_%H%M%S}.csv",
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
        self.tracks_exported.emit(file_path)
