from contextlib import suppress
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
    QVBoxLayout,
    QWidget,
)

from wet.components.tracks import SCHEMA as _TAP_SCHEMA
from wet.components.util import make_button, make_spinbox
from wet.util import now

_logger = getLogger("wwise-event-tapper")
_ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


class RawTapPathConfigurator(QWidget):
    def __init__(self) -> None:
        super().__init__()

        attr = QLabel("<strong>Raw taps:</strong> ")
        self._value = QLabel("<em>none</em>")
        button = make_button("Select", width=80)

        self._value.setAlignment(_ALIGN_RIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(attr)
        layout.addWidget(self._value)
        layout.addStretch()
        layout.addWidget(button)

        button.clicked.connect(self.on_select_button)

        self._raw_taps: pl.DataFrame = pl.DataFrame((), _TAP_SCHEMA)

    @property
    def frame(self) -> pl.DataFrame:
        return self._raw_taps

    def load_raw_taps(self, path: str) -> None:
        self._value.setText(path)
        self._raw_taps = pl.read_csv(path, schema=_TAP_SCHEMA)

    def on_select_button(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Raw Tap Path", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        self.load_raw_taps(file_path)


class TapCalibrator(QGroupBox):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("🛠️ Calibrator")

        # This is on the first row.
        self._raw_taps = RawTapPathConfigurator()

        # Add the control widgets, on the second row.
        bpm_label = QLabel("<strong>BPM:</strong>")
        self._bpm_spin = make_spinbox((0, 400))
        self._bpm_spin.setValue(90)
        offset_label = QLabel("<strong>Offset (ms):</strong>")
        self._offset_spin = make_spinbox((0, 10000))
        export_button = make_button("Export", width=80)

        layout1 = QHBoxLayout()
        layout1.setSpacing(10)
        layout1.addWidget(bpm_label)
        layout1.addWidget(self._bpm_spin)
        layout1.addWidget(offset_label)
        layout1.addWidget(self._offset_spin)
        layout1.addStretch()
        layout1.addWidget(export_button)

        export_button.clicked.connect(self._on_export_button)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self._raw_taps)
        self._layout.addLayout(layout1)

    def on_tracks_exported(self, path: str) -> None:
        self._raw_taps.load_raw_taps(path)

    def _on_export_button(self) -> None:
        if self._raw_taps.frame.is_empty():
            QMessageBox.warning(
                self,
                "No raw taps",
                "Please export raw taps first.",
            )
            return

        bpm = self._bpm_spin.value()
        offset = self._offset_spin.value()

        if not bpm:
            QMessageBox.warning(
                self,
                "BPM is not set",
                "Please set a non-zero BPM.",
            )
            return

        with suppress(OSError):
            Path("export").mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Export Path",
            f"export/calibrated_taps.{now():%Y%m%d_%H%M%S}.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        beat_duration = 60000.0 / bpm  # bpm is in ms/beat
        _logger.info("BPM: %s, beat duration: %s", bpm, beat_duration)

        # Clamp the raw taps to the nearest slot.
        def clamp(frame: pl.LazyFrame, tap_col: str) -> pl.LazyFrame:
            # Compute beat sequence first, then restore to the timestamp.
            seq = ((pl.col(tap_col) - offset) / beat_duration).round().cast(int)
            ts = seq.mul(beat_duration).add(offset).cast(int)
            return frame.with_columns(
                seq.alias(f"{tap_col}_sequence"),
                ts.alias(f"{tap_col}_calibrated"),
            )

        frame = clamp(self._raw_taps.frame.lazy(), "start")
        frame = clamp(frame, "end").sort("start").sink_csv(file_path)

        QMessageBox.information(
            self,
            "Calibrated taps exported",
            f"Exported to {file_path}",
        )
