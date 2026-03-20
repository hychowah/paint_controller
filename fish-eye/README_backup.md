# Fisheye Unwrapper - Real-Time

Real-time fisheye camera unwrapper for Windows with live preview and interactive parameter adjustment.

## Features

- **Real-time unwrapping**: 30+ FPS performance with 1080p cameras
- **Circular fisheye support**: Handles 180° FOV fisheye lenses where image appears as circle in frame
- **Interactive controls**: Adjust FOV, center, distortion, zoom, rotation in real-time
- **Auto-detection**: Automatic circle detection for fisheye boundary
- **Dual view display**: Side-by-side original and unwrapped video
- **Recording**: Save both original and unwrapped video streams
- **Snapshots**: Capture individual frames
- **Presets**: Save and load parameter configurations

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

1. **Select Camera**: Choose your USB fisheye camera from the list
2. **Choose Resolution**: Select camera resolution (1920x1080 recommended)
3. **Adjust Parameters**:
   - **Fisheye Circle**: Center X/Y, Radius - defines the circular fisheye region
   - **Auto Detect**: Automatically detect circle parameters
   - **Field of View**: Horizontal/Vertical FOV for output view
   - **Distortion**: K1, K2 coefficients for fisheye correction
   - **View**: Zoom, Rotation, Focal Length
4. **Recording**:
   - **Snapshot**: Save current frame as PNG
   - **Record**: Save video stream as MP4
5. **Presets**: Save/load parameter configurations for quick switching

## Controls

- Adjust sliders to change parameters in real-time
- Changes are debounced (200ms) for smooth preview
- Toggle "Show Circle Overlay" to visualize fisheye boundary
- Use presets for common viewing modes:
  - Front View 90°: Standard rectilinear view
  - Wide View 180°: Full fisheye coverage
  - Panoramic 360°: Ultra-wide panorama

## Project Structure

```
fish-eye/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── gui/                    # GUI components
│   ├── camera_dialog.py    # Camera selection dialog
│   ├── main_window.py      # Main application window
│   └── controls_panel.py   # Parameter controls
├── core/                   # Core processing
│   ├── camera_thread.py    # Threaded video capture
│   ├── processor.py        # Fisheye unwrapping
│   ├── preset_manager.py   # Preset save/load
│   └── video_recorder.py   # Video recording
├── utils/                  # Utilities
│   └── config.py           # Configuration and defaults
├── presets/                # Saved presets
└── recordings/             # Recorded videos and snapshots
```

## Circular Fisheye Support

This application is designed for circular fisheye lenses where the 180° FOV image appears as a circle within the rectangular camera frame (common in many USB fisheye cameras).

The **Auto Detect** feature will attempt to find the circle automatically, or you can manually adjust:
- **Center X/Y**: Position of circle center
- **Radius**: Size of fisheye circle

## Performance

Expected frame rates (CPU-only):
- 640x480: 60+ FPS
- 1280x720: 30-45 FPS  
- 1920x1080: 30+ FPS

## Troubleshooting

**No cameras detected**: Make sure your USB fisheye camera is connected and not in use by another application.

**Low FPS**: Try reducing resolution or adjusting distortion parameters less frequently.

**Circle not detected**: Use manual controls to adjust center and radius parameters.

## License

MIT License
