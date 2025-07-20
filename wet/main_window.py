"""Main window for the Wwise Event Tapper application."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeyEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from wet.audio_player import AudioPlayer
from wet.event_recorder import EventRecorder


def format_time(seconds: float) -> str:
    """Format time in seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.audio_player = AudioPlayer()
        self.event_recorder = EventRecorder()
        self.current_file: Path | None = None
        self.auto_save_path: Path | None = None
        self.total_duration: float = 0.0

        # Initialize UI and connect signals
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:  # noqa: PLR0915
        self.setWindowTitle("Wwise Event Tapper")
        self.setMinimumSize(500, 300)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create menu bar
        self._create_menu_bar()

        # File selection section
        file_section = QHBoxLayout()
        self.select_file_btn = QPushButton("Select Music File")
        self.select_file_btn.setAutoDefault(False)  # Prevent space key activation
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("font-style: italic; color: gray;")

        file_section.addWidget(self.select_file_btn)
        file_section.addWidget(self.file_label, 1)
        layout.addLayout(file_section)

        # Audio controls section
        controls_section = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.pause_btn = QPushButton("⏸ Pause")
        self.stop_btn = QPushButton("⏹ Stop")

        # Prevent buttons from being activated by space key
        self.play_btn.setAutoDefault(False)
        self.pause_btn.setAutoDefault(False)
        self.stop_btn.setAutoDefault(False)

        # Initially disable controls until file is loaded
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        controls_section.addWidget(self.play_btn)
        controls_section.addWidget(self.pause_btn)
        controls_section.addWidget(self.stop_btn)
        controls_section.addStretch()
        layout.addLayout(controls_section)

        # Progress bar section
        progress_section = QVBoxLayout()
        progress_label = QLabel("Progress:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1000)  # Use 0-1000 for smooth progress
        self.progress_bar.setValue(0)
        self.time_label = QLabel("00:00 / 00:00")

        progress_section.addWidget(progress_label)
        progress_section.addWidget(self.progress_bar)
        progress_section.addWidget(self.time_label)
        layout.addLayout(progress_section)

        # Recording status section
        recording_section = QVBoxLayout()
        self.recording_status = QLabel("Recording: ○ OFF")
        self.events_count = QLabel("Events Recorded: 0")
        self.save_location = QLabel("Auto-save: Not set")
        self.save_location.setStyleSheet("font-size: 10px; color: gray;")

        recording_section.addWidget(self.recording_status)
        recording_section.addWidget(self.events_count)
        recording_section.addWidget(self.save_location)
        layout.addLayout(recording_section)

        # Instructions
        instructions = QLabel(
            "Instructions:\n"
            "• Press SPACEBAR to record tap events\n"
            "• Events are auto-saved when recording starts",
        )
        instructions.setStyleSheet(
            "margin-top: 20px; padding: 10px; background-color: #f0f0f0;"
        )
        layout.addWidget(instructions)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Timer for updating UI
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(100)  # Update every 100ms

    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Music File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.select_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        export_action = QAction("Export Events...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_events)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _connect_signals(self) -> None:
        # Button connections
        self.select_file_btn.clicked.connect(self.select_file)
        self.play_btn.clicked.connect(self.play_audio)
        self.pause_btn.clicked.connect(self.pause_audio)
        self.stop_btn.clicked.connect(self.stop_audio)

        # Audio player signals
        self.audio_player.playback_started.connect(self._on_playback_started)
        self.audio_player.playback_stopped.connect(self._on_playback_stopped)
        self.audio_player.playback_paused.connect(self._on_playback_paused)
        self.audio_player.playback_resumed.connect(self._on_playback_resumed)
        self.audio_player.duration_changed.connect(self._on_duration_changed)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Space:
            if self.audio_player.is_playing():
                timestamp = self.audio_player.get_position()
                self.event_recorder.record_event(timestamp)
                self._update_events_count()
                self.status_bar.showMessage(f"Event recorded at {timestamp:.2f}s", 1000)

                # Auto-save after each event
                if self.auto_save_path:
                    self._auto_save_events()
            # Always accept space key events to prevent button activation
            event.accept()
        else:
            super().keyPressEvent(event)

    def select_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Music File",
            "",
            "Audio Files (*.mp3 *.wav *.ogg);;All Files (*)",
        )

        if file_path:
            self.current_file = Path(file_path)
            self.file_label.setText(self.current_file.name)
            self.file_label.setStyleSheet("font-style: normal; color: black;")

            # Load the file into audio player
            if self.audio_player.load_file(self.current_file):
                self.play_btn.setEnabled(True)
                self.pause_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                self.status_bar.showMessage(f"Loaded: {self.current_file.name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load audio file")

    def play_audio(self) -> None:
        if self.audio_player.play():
            if self.audio_player.is_paused():
                self.status_bar.showMessage("Resumed")
            else:
                self.status_bar.showMessage("Playing...")
        else:
            QMessageBox.warning(self, "Error", "Failed to start playback")

    def pause_audio(self) -> None:
        if self.audio_player.is_playing():
            self.audio_player.pause()
            self.status_bar.showMessage("Paused")
        elif self.audio_player.is_paused():
            # Resume playback
            self.audio_player.play()

    def stop_audio(self) -> None:
        self.audio_player.stop()
        self.status_bar.showMessage("Stopped")

    def export_events(self) -> None:
        if not self.event_recorder.get_events():
            QMessageBox.information(self, "No Events", "No events recorded to export.")
            return

        # Default to export directory
        export_dir = Path("export")
        export_dir.mkdir(exist_ok=True)
        default_name = "events.json"
        if self.current_file:
            default_name = f"{self.current_file.stem}_events.json"

        default_path = str(export_dir / default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Events",
            default_path,
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            try:
                self.event_recorder.export_events(Path(file_path))
                self.status_bar.showMessage(
                    f"Events exported to {Path(file_path).name}"
                )
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export events: {e!s}"
                )

    def _on_playback_started(self) -> None:
        self.event_recorder.start_recording()
        self.recording_status.setText("Recording: ● ON")
        self.recording_status.setStyleSheet("color: red; font-weight: bold;")

        # Set up auto-save on first recording
        if not self.auto_save_path and self.current_file:
            self._setup_auto_save()

    def _on_playback_stopped(self) -> None:
        self.event_recorder.stop_recording()
        self.recording_status.setText("Recording: ○ OFF")
        self.recording_status.setStyleSheet("color: black; font-weight: normal;")

        # Auto-save on stop if we have events
        if self.auto_save_path and self.event_recorder.get_events():
            self._auto_save_events()

    def _on_playback_paused(self) -> None:
        # Don't stop recording on pause, just update UI
        self.recording_status.setText("Recording: ⏸ PAUSED")
        self.recording_status.setStyleSheet("color: orange; font-weight: bold;")

    def _on_playback_resumed(self) -> None:
        # Resume recording display
        self.recording_status.setText("Recording: ● ON")
        self.recording_status.setStyleSheet("color: red; font-weight: bold;")

    def _on_duration_changed(self, duration: float) -> None:
        self.total_duration = duration
        self._update_time_display()

    def _setup_auto_save(self) -> None:
        """Set up auto-save file path based on current music file."""
        if not self.current_file:
            return

        # Create auto-save in export directory
        export_dir = Path("export")
        export_dir.mkdir(exist_ok=True)

        music_stem = self.current_file.stem
        auto_save_name = f"{music_stem}_events.json"
        self.auto_save_path = export_dir / auto_save_name

        self.save_location.setText(f"Auto-save: {self.auto_save_path}")
        self.save_location.setStyleSheet("font-size: 10px; color: blue;")

    def _auto_save_events(self) -> None:
        """Auto-save events to the designated path."""
        if not self.auto_save_path:
            return

        try:
            self.event_recorder.export_events(self.auto_save_path)
            self.status_bar.showMessage(
                f"Auto-saved to {self.auto_save_path.name}", 2000
            )
        except Exception as e:  # noqa: BLE001
            self.status_bar.showMessage(f"Auto-save failed: {e}", 3000)

    def _update_ui(self) -> None:
        if self.audio_player.is_playing():
            self.play_btn.setText("▶ Playing...")
            self.pause_btn.setText("⏸ Pause")
        elif self.audio_player.is_paused():
            self.play_btn.setText("▶ Play")
            self.pause_btn.setText("▶ Resume")
        else:
            self.play_btn.setText("▶ Play")
            self.pause_btn.setText("⏸ Pause")

        # Update progress bar and time display
        if self.total_duration > 0:
            current_pos = self.audio_player.get_position()
            progress = min(int((current_pos / self.total_duration) * 1000), 1000)
            self.progress_bar.setValue(progress)

            # Update time display
            self._update_time_display()

    def _update_events_count(self) -> None:
        count = len(self.event_recorder.get_events())
        self.events_count.setText(f"Events Recorded: {count}")

    def _update_time_display(self) -> None:
        """Update the time display labels."""
        if self.total_duration > 0:
            current_pos = self.audio_player.get_position()
            current_time = format_time(current_pos)
            total_time = format_time(self.total_duration)
            self.time_label.setText(f"{current_time} / {total_time}")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Wwise Event Tapper",
            "Wwise Event Tapper v0.1.0\n\n"
            "A tool for recording tap events synchronized with music playback.\n"
            "Built with PySide6 and pygame.",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.audio_player.stop()
        event.accept()
