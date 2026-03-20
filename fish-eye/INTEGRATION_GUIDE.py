"""
Standalone Fisheye Transformation Module
=========================================

This module provides fisheye lens correction and unwrapping functionality
that can be easily integrated into any Qt or Python application.

Key Components:
--------------
1. FisheyeProcessor (core/processor.py)
   - Main transformation engine
   - Pre-computes remap tables for fast processing
   - Handles fisheye unwrapping with configurable parameters

2. Integration Example (see below)
   - Simple timer-based approach (no threading overhead)
   - Direct camera reading and processing
   - Works seamlessly with Qt event loop

Usage Example:
-------------
```python
import cv2
from PyQt5.QtCore import QTimer
from core.processor import FisheyeProcessor

# Initialize processor
processor = FisheyeProcessor(width=1920, height=1080)

# Configure parameters
processor.update_parameters(
    center_x=960,
    center_y=540,
    radius=599,
    fov_h=90.0,
    fov_v=67.5,
    k1=-0.371,
    k2=0.165,
    zoom=0.5,
    rotation=0.0
)

# Open camera
camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Process frames
def process_frame():
    ret, frame = camera.read()
    if ret:
        unwrapped = processor.process_frame(frame)
        # Display or save unwrapped frame
        
# Use Qt timer (recommended - no threading overhead)
timer = QTimer()
timer.timeout.connect(process_frame)
timer.start(0)  # As fast as possible
```

Performance Notes:
-----------------
- Processing: ~9ms per frame (1920x1080) = 110 FPS theoretical
- Use timer-based approach instead of QThread for best performance
- QThread signal/slot overhead caused significant lag in original implementation
- Direct timer approach achieves 30+ FPS in Qt without lag

Files Needed for Integration:
-----------------------------
- core/processor.py (main transformation logic)
- core/preset_manager.py (optional: preset management)
- utils/config.py (configuration constants)
- presets/ (optional: JSON preset files)

API Reference:
-------------
FisheyeProcessor Methods:
- __init__(width, height): Initialize processor
- update_parameters(**params): Update transformation parameters
- process_frame(frame, fast_mode=False): Transform frame
- draw_circle_overlay(frame): Draw fisheye circle on frame
- auto_detect_parameters(frame): Auto-detect fisheye circle
- get_parameters(): Get current parameters
- compute_remap_tables(): Recompute transformation tables

Parameters:
- center_x, center_y: Circle center coordinates
- radius: Fisheye circle radius in pixels
- fov_h, fov_v: Horizontal/vertical field of view (degrees)
- k1, k2: Radial distortion coefficients
- zoom: Zoom factor (0.1-3.0)
- rotation: Rotation angle (degrees)
- focal_length: Camera focal length
"""
