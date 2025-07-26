from contextlib import suppress
from logging import getLogger
from pathlib import Path

import polars as pl
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
from wet.components.wwise_client import WwiseController
from wet.util import now

_logger = getLogger("wwise-event-tapper")
_ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


class RawTapPathConfigurator(QWidget):
    def __init__(self) -> None:
        super().__init__()

        attr = QLabel("<strong>Raw taps:</strong> ")
        self._value = QLabel("<em>none</em>")
        button = make_button("Select")

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


def _calibrate_taps(frame: pl.DataFrame, bpm: int, offset: int) -> pl.DataFrame:
    """Apply BPM calibration to raw taps."""
    beat_duration = 60000.0 / bpm

    def clamp_column(lazy_frame: pl.LazyFrame, tap_col: str) -> pl.LazyFrame:
        seq = ((pl.col(tap_col) - offset) / beat_duration).round().cast(int)
        ts = seq.mul(beat_duration).add(offset).cast(int)
        return lazy_frame.with_columns(
            seq.alias(f"{tap_col}_sequence"),
            ts.alias(f"{tap_col}_calibrated"),
        )

    result = clamp_column(frame.lazy(), "start")
    result = clamp_column(result, "end")
    return result.sort("start").collect()


class TapCalibrator(QGroupBox):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("🛠️ Calibrator")

        self._wwise = WwiseController()
        self._raw_taps = RawTapPathConfigurator()

        self._bpm_spin = make_spinbox((0, 400))
        self._bpm_spin.setValue(90)
        self._offset_spin = make_spinbox((0, 10000))

        self._segment_combo = QComboBox()
        self._segment_combo.setMinimumWidth(200)

        self._setup_layouts()
        self._refresh_segments()

    def _setup_layouts(self) -> None:
        """Create and arrange UI layouts."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Raw taps section
        main_layout.addWidget(self._raw_taps)

        # Calibration settings section
        calibration_group = QGroupBox("Calibration Settings")
        calibration_layout = QHBoxLayout(calibration_group)
        calibration_layout.setSpacing(15)

        # BPM control
        bpm_layout = QVBoxLayout()
        bpm_layout.addWidget(QLabel("BPM:"))
        bpm_layout.addWidget(self._bpm_spin)

        # Offset control
        offset_layout = QVBoxLayout()
        offset_layout.addWidget(QLabel("Offset (ms):"))
        offset_layout.addWidget(self._offset_spin)

        # Export button
        export_layout = QVBoxLayout()
        export_layout.addWidget(QLabel("Export:"))
        export_button = make_button("Export CSV")
        export_button.clicked.connect(self._export_csv)
        export_layout.addWidget(export_button)

        calibration_layout.addLayout(bpm_layout)
        calibration_layout.addLayout(offset_layout)
        calibration_layout.addStretch()
        calibration_layout.addLayout(export_layout)

        main_layout.addWidget(calibration_group)

        # Wwise section
        wwise_group = QGroupBox("Wwise Integration")
        wwise_layout = QVBoxLayout(wwise_group)
        wwise_layout.setSpacing(10)

        # Target segment row
        segment_layout = QHBoxLayout()
        segment_layout.addWidget(QLabel("Target Segment:"))
        segment_layout.addWidget(self._segment_combo)

        # Action buttons row
        actions_layout = QHBoxLayout()
        self._refresh_button = make_button("Refresh")
        self._refresh_button.clicked.connect(self._refresh_segments)
        self._clear_button = make_button("Clear Custom Cues")
        self._clear_button.clicked.connect(self._clear_cues)
        self._export_wwise_button = make_button("Export to Wwise")
        self._export_wwise_button.clicked.connect(self._export_to_wwise)

        actions_layout.addWidget(self._refresh_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self._clear_button)
        actions_layout.addWidget(self._export_wwise_button)

        wwise_layout.addLayout(segment_layout)
        wwise_layout.addLayout(actions_layout)

        main_layout.addWidget(wwise_group)

    def __del__(self) -> None:
        self._wwise.disconnect()

    def on_tracks_exported(self, path: str) -> None:
        self._raw_taps.load_raw_taps(path)

    def _validate_export_params(self) -> tuple[bool, int, int]:
        """Validate BPM and offset parameters. Returns (valid, bpm, offset)."""
        if self._raw_taps.frame.is_empty():
            QMessageBox.warning(self, "No Data", "Please export raw taps first.")
            return False, 0, 0

        bpm = self._bpm_spin.value()
        offset = self._offset_spin.value()

        if not bpm:
            QMessageBox.warning(self, "BPM Not Set", "Please set a non-zero BPM.")
            return False, 0, 0

        return True, bpm, offset

    def _refresh_segments(self) -> None:
        """Refresh available music segments list."""
        self._segment_combo.clear()
        for segment in self._wwise.get_music_segments():
            name = segment.get("name")  # type: ignore[assignment]
            path = segment.get("path")  # type: ignore[assignment]
            if name and path:
                display_name = f"{name} ({path})"
                self._segment_combo.addItem(display_name, segment.get("id"))  # type: ignore[arg-type]

    def _get_selected_segment(self) -> tuple[str | None, str]:
        """Get selected segment ID and name. Returns (id, name)."""
        segment_id = self._segment_combo.currentData()  # type: ignore[assignment]
        segment_name = self._segment_combo.currentText().split(" (")[0]
        return segment_id, segment_name

    def _clear_cues(self) -> None:
        """Clear custom cues from selected segment."""
        segment_id, segment_name = self._get_selected_segment()
        if not segment_id:
            QMessageBox.warning(self, "No Selection", "Please select a music segment.")
            return

        reply = QMessageBox.question(
            self,
            "Clear Cues",
            f"Delete all custom cues from '{segment_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = self._wwise.clear_custom_cues(segment_id)
            if deleted_count > 0:
                self._wwise.save_project()
                QMessageBox.information(
                    self, "Cues Cleared", f"Deleted {deleted_count} custom cues."
                )
            else:
                QMessageBox.information(self, "No Cues", "No custom cues found.")

    def _export_to_wwise(self) -> None:
        """Export calibrated taps to Wwise as cues."""
        valid, bpm, offset = self._validate_export_params()
        if not valid:
            return

        segment_id, segment_name = self._get_selected_segment()
        if not segment_id:
            QMessageBox.warning(self, "No Selection", "Please select a music segment.")
            return

        calibrated_data = _calibrate_taps(self._raw_taps.frame, bpm, offset)
        success_count = self._create_cues_from_data(calibrated_data, segment_id)
        total_count = len(calibrated_data)

        if success_count > 0:
            self._wwise.save_project()
            QMessageBox.information(
                self,
                "Export Complete",
                f"Created {success_count}/{total_count} cues in '{segment_name}'.",
            )
        else:
            QMessageBox.warning(self, "Export Failed", "Failed to create any cues.")

    def _create_cues_from_data(self, data: pl.DataFrame, segment_id: str) -> int:
        """Create cues from calibrated data. Returns success count."""
        success_count = 0

        for row in data.iter_rows(named=True):
            track = row["track"]
            sequence = row["start_sequence"]
            time_ms = row["start_calibrated"]
            cue_name = f"{track}_{sequence}"
            if self._wwise.create_cue(cue_name, segment_id, time_ms):
                success_count += 1
            else:
                _logger.warning("Failed to create cue: %s", cue_name)

        return success_count

    def _export_csv(self) -> None:
        """Export calibrated taps to CSV file."""
        valid, bpm, offset = self._validate_export_params()
        if not valid:
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

        calibrated_data = _calibrate_taps(self._raw_taps.frame, bpm, offset)
        calibrated_data.write_csv(file_path)

        QMessageBox.information(self, "Export Complete", f"Exported to {file_path}")
