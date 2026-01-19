# Multi-Screen Display Support

This document describes the multi-screen display capabilities of the Paint Controller Qt application.

## Overview

The Paint Controller now supports adaptive multi-screen display with real-time detection and management. This allows the application to:

- Detect connected displays automatically
- Monitor display changes in real-time (plug/unplug events)
- Dynamically adjust UI based on available screens
- Display content on multiple screens simultaneously

## Architecture

### ScreenManager Class

Located in: `python/paint_controller/services/screen_manager.py`

The `ScreenManager` is a Qt-based service that provides:

**Functionality:**
- Real-time screen detection using Qt's `QGuiApplication.screens()`
- Periodic monitoring (every 1 second) for screen configuration changes
- Signal-based notifications for screen events

**Signals:**
- `screens_changed`: Emitted when screens are added/removed
- `screen_added(int)`: Emitted when a new screen is detected (with index)
- `screen_removed(int)`: Emitted when a screen is disconnected (with index)
- `primary_screen_changed(str)`: Emitted when primary screen changes (with name)

**Methods:**
- `get_screen_count() -> int`: Returns number of detected screens
- `get_screen_list() -> List[Dict]`: Returns detailed info for all screens
- `get_screen_info_string(index) -> str`: Returns formatted info for a specific screen
- `get_primary_screen_name() -> str`: Returns the name of the primary screen
- `get_screen(index) -> QScreen`: Returns QScreen object by index

### ScreenInfo Class

Data class containing screen information:
- `index`: Screen index number
- `name`: Display name
- `manufacturer`: Hardware manufacturer
- `model`: Display model
- `serial_number`: Serial number
- `width`, `height`: Resolution
- `refresh_rate`: Refresh rate in Hz
- `virtual_x`, `virtual_y`: Position in virtual desktop
- `is_primary`: Whether this is the primary display
- `device_pixel_ratio`: Pixel density ratio

## UI Components

### MultiScreenListUI.qml

Located in: `python/paint_controller/qml/overlays/MultiScreenListUI.qml`

A test/demo window that displays:
- Current number of detected screens
- Detailed information for each screen
- Real-time updates when screens are added/removed
- Status indicator showing monitoring is active

**Features:**
- Automatically refreshes when screen configuration changes
- Can be positioned on secondary display
- Provides visual feedback for connected displays
- Includes manual refresh button

### Integration in MainWindow.qml

The main window now includes:
- Dynamic screen property that updates on screen changes
- Function `toggleMultiScreenWindow()` to open/close test UI
- Automatic repositioning of secondary windows when screens change
- Connections to ScreenManager signals for real-time updates

## Usage

### Opening the Multi-Screen Test Window

1. Launch the Paint Controller application
2. Navigate to Settings (gear icon in sidebar)
3. Scroll to "Display Settings" section
4. Click "Multi-Screen Test"
5. A new window will open showing all detected screens

### Testing Multi-Screen Behavior

1. With the application running, connect an external monitor
2. The multi-screen test window will automatically update
3. The main application will detect the new screen
4. If the test window is open and a second screen exists, it will be repositioned to the second screen

### Accessing Screen Information from Python

```python
# Get number of screens
screen_count = controller.screen_manager.get_screen_count()

# Get list of all screens
screens = controller.screen_manager.get_screen_list()

# Get specific screen info
info = controller.screen_manager.get_screen_info_string(0)

# Get primary screen name
primary = controller.screen_manager.get_primary_screen_name()
```

### Accessing Screen Information from QML

```qml
// Get screen count
var count = screenManager.get_screen_count()

// Get screen info string
var info = screenManager.get_screen_info_string(0)

// Connect to screen change signals
Connections {
    target: screenManager
    
    function onScreens_changed() {
        console.log("Screen configuration changed")
    }
    
    function onScreen_added(index) {
        console.log("Screen added at index:", index)
    }
    
    function onScreen_removed(index) {
        console.log("Screen removed at index:", index)
    }
}
```

## Implementation Details

### Screen Detection Strategy

The system uses a hybrid approach:
1. **Qt Signals**: Primary detection using Qt's built-in signals (`screenAdded`, `screenRemoved`)
2. **Periodic Polling**: Backup monitoring every 1 second to catch any missed events

This ensures reliable detection even if Qt signals are delayed or missed.

### Window Positioning

Windows can be positioned on specific screens using:
```qml
Window {
    x: screens[1].virtualX
    y: screens[1].virtualY
    width: screens[1].width
    height: screens[1].height
}
```

The virtual coordinates allow proper positioning in multi-monitor setups with different arrangements.

### Performance Considerations

- Screen monitoring runs every 1 second (minimal CPU impact)
- Screen info is cached and only updated on changes
- QML updates are signal-driven (no polling from QML side)

## Future Enhancements

Potential improvements for the multi-screen system:

1. **Screen Configuration Persistence**
   - Save preferred screen assignments
   - Remember window positions per screen
   - Auto-restore layout on startup

2. **Advanced Window Management**
   - Drag windows between screens
   - Maximize/fullscreen per screen
   - Picture-in-picture mode

3. **Extended Display Modes**
   - Mirror mode (duplicate content on all screens)
   - Extended mode (different content on each screen)
   - Presenter mode (control on one screen, display on another)

4. **Screen-Specific Content**
   - Video output on secondary display
   - Control interface on primary display
   - Data visualization on additional screens

## Troubleshooting

### Screen Not Detected

If an external monitor is not detected:
1. Check physical connection (HDMI/DisplayPort/USB-C)
2. Ensure monitor is powered on
3. Check system display settings (`xrandr` on Linux)
4. Restart the application
5. Click "Refresh" button in the multi-screen test window

### Window Not Appearing on Second Screen

If the test window doesn't appear on the second screen:
1. Verify screen is detected (check count in test window)
2. Close and reopen the test window
3. Check if screens are in extended mode (not mirrored)
4. Verify virtual screen coordinates in system settings

### Real-Time Updates Not Working

If screen changes aren't detected in real-time:
1. Wait up to 1 second (polling interval)
2. Click "Refresh" button manually
3. Check console logs for Qt screen signals
4. Verify ScreenManager is initialized correctly

## Technical Notes

### Steam Deck Considerations

The original design targeted Steam Deck's built-in display:
- Resolution: 1280x800
- Single screen by default
- Can connect to external displays via USB-C dock

With the new multi-screen support:
- Steam Deck display is screen 0 (primary)
- External displays become screen 1, 2, etc.
- UI adapts automatically to available screens

### Qt Platform Compatibility

The implementation uses:
- Qt 5.15+ / PySide6
- Qt Quick 2.15
- Qt Quick Controls 2.15
- X11 backend (required for VTK compatibility)

Note: Wayland support may have limitations due to VTK requirements.

## API Reference

See `screen_manager.py` for full API documentation including:
- All public methods and their signatures
- Signal definitions and parameters
- ScreenInfo data structure
- Error handling and edge cases
