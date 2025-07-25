import polars as pl
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from wet.components.util import make_button, make_spinbox
from wet.util import now

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

        self._raw_taps: pl.DataFrame | None = None

    def load_raw_taps(self, path: str) -> None:
        self._value.setText(path)
        self._raw_taps = pl.read_csv(path)

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
        bpm_spin = make_spinbox((0, 400))
        offset_label = QLabel("<strong>Offset (ms):</strong>")
        offset_spin = make_spinbox((0, 10000))
        export_button = make_button("Export", width=80)

        layout1 = QHBoxLayout()
        layout1.setSpacing(10)
        layout1.addWidget(bpm_label)
        layout1.addWidget(bpm_spin)
        layout1.addWidget(offset_label)
        layout1.addWidget(offset_spin)
        layout1.addStretch()
        layout1.addWidget(export_button)

        export_button.clicked.connect(self._on_export)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self._raw_taps)
        self._layout.addLayout(layout1)

    def on_tracks_exported(self, path: str) -> None:
        self._raw_taps.load_raw_taps(path)

    def _on_export(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Export Path",
            f"calibrated_taps.{now():%Y%m%d_%H%M%S}.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return
