# Wwise Event Tapper - Development Plan

## Phase 1: Basic GUI App

### Overview
Create a rudimentary GUI application that allows users to:
1. Select a music file
2. Play the selected music
3. Record tap events (spacebar) with timestamps

### Technical Stack

#### GUI Framework: PySide6
- Cross-platform (Windows, macOS, Linux)
- Modern Qt6 bindings for Python
- Rich widget ecosystem

#### Audio Playback: pygame
- Simple audio playback capabilities
- Cross-platform audio support
- Easy integration with Python
- Alternative: `python-vlc` or `pyglet` for more advanced audio features

#### Key Dependencies to Add
```toml
dependencies = [
    "PySide6>=6.6.0",
    "pygame>=2.5.0",
]
```

### Application Architecture

```
WwiseEventTapper/
├── main_window.py      # Main application window
├── audio_player.py     # Audio playback management
├── event_recorder.py   # Tap event recording
└── file_dialog.py      # File selection utilities
```

### Core Components

#### 1. Main Window (`main_window.py`)
- **Layout**: Vertical layout with sections for:
  - File selection (button + label showing selected file)
  - Audio controls (play/pause/stop buttons)
  - Recording status indicator
  - Event list display (optional for Phase 1)
- **Key Features**:
  - Menu bar with File menu
  - Status bar for feedback
  - Keyboard event handling for spacebar

#### 2. Audio Player (`audio_player.py`)
- **Responsibilities**:
  - Load audio files (MP3, WAV, OGG)
  - Play/pause/stop functionality
  - Track current playback position
  - Emit signals for playback events
- **Implementation Notes**:
  - Use pygame.mixer for basic audio playback
  - Thread-safe playback position tracking
  - Support common audio formats

#### 3. Event Recorder (`event_recorder.py`)
- **Responsibilities**:
  - Record timestamp when spacebar is pressed
  - Calculate offset from music start time
  - Store events in memory (list of timestamps)
  - Export events to JSON/CSV format
- **Data Structure**:
  ```python
  TapEvent = {
      "timestamp": float,  # seconds from music start
      "absolute_time": datetime,  # when tap occurred
  }
  ```

#### 4. File Dialog Utilities (`file_dialog.py`)
- **Responsibilities**:
  - Open file dialog for music selection
  - Validate file format
  - Handle file path management

### Implementation Steps

#### Step 1: Project Setup
1. Update `pyproject.toml` with new dependencies
2. Create main application entry point
3. Set up basic window with PySide6

#### Step 2: File Selection
1. Implement file dialog for music selection
2. Add file path display in UI
3. Basic file format validation

#### Step 3: Audio Playback
1. Integrate pygame for audio playback
2. Add play/pause/stop controls
3. Implement playback position tracking

#### Step 4: Event Recording
1. Implement spacebar key detection
2. Record timestamps relative to music start
3. Display recorded events in UI

#### Step 5: Data Export
1. Save recorded events to JSON file
2. Basic event data validation

### UI Layout Plan

```
┌─────────────────────────────────────────┐
│ File   Help                             │
├─────────────────────────────────────────┤
│                                         │
│ [Select Music File]  📁                 │
│ Selected: /path/to/music.mp3            │
│                                         │
│ ⏯️ Play   ⏸️ Pause   ⏹️ Stop           │
│                                         │
│ Recording: ● ON / ○ OFF                 │
│ Events Recorded: 42                     │
│                                         │
│ Instructions:                           │
│ • Press SPACEBAR to record tap events  │
│ • Events are saved automatically        │
│                                         │
├─────────────────────────────────────────┤
│ Ready                                   │
└─────────────────────────────────────────┘
```

### Challenges & Considerations

#### Audio Playback Timing
- **Challenge**: Accurate timestamp recording relative to audio playback
- **Solution**: Use high-resolution timer (time.perf_counter) and track audio start time

#### Cross-Platform Compatibility
- **Challenge**: Different audio backends on different OS
- **Solution**: pygame provides good cross-platform abstraction

#### Key Event Handling
- **Challenge**: Global key detection vs. window focus
- **Solution**: Start with window-focused detection, consider global hotkeys later

#### Audio Format Support
- **Challenge**: Supporting various audio formats
- **Solution**: pygame supports MP3, OGG, WAV out of the box

### Future Enhancements (Not in Phase 1)
- Global hotkey support (record even when app not focused)
- Audio waveform visualization
- Event editing/deletion
- Multiple hotkey support
- BPM detection and grid alignment
- Wwise project integration
- Real-time audio analysis

### Testing Strategy
- Test with different audio formats
- Test on different operating systems
- Verify timing accuracy with metronome
- Test keyboard responsiveness during playback

This plan provides a solid foundation for building the basic event tapper functionality while keeping the scope manageable for the first iteration.
