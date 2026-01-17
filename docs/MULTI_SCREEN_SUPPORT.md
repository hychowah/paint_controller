# Adaptive Multi-Screen UI Support

## Overview

The Paint Controller application now supports adaptive multi-screen display with real-time monitor detection. This feature allows the application to:

- Detect connected displays automatically
- Respond to monitor plug/unplug events in real-time
- Allow users to select which display to use
- Adapt window geometry to the selected display
- Support extended and duplicate display modes

## Architecture

### Components

#### 1. ScreenManager (Python)
**Location:** `python/paint_controller/core/screen_manager.py`

The `ScreenManager` class is a Qt-based Python component that:
- Monitors Qt's screen management signals (`screenAdded`, `screenRemoved`, `primaryScreenChanged`)
- Maintains a list of connected displays with their properties
- Exposes screen information to QML through Qt properties and slots
- Emits signals when screen configuration changes

**Key Features:**
- Real-time screen detection
- Screen information retrieval (resolution, refresh rate, position)
- Primary screen tracking
- Thread-safe cleanup on shutdown

**Signals:**
- `screen_added(int index, str name)` - Emitted when a display is connected
- `screen_removed(int index, str name)` - Emitted when a display is disconnected
- `screens_changed()` - Emitted when any screen configuration changes
- `primary_screen_changed(str name)` - Emitted when the primary screen changes
- `screen_count_changed(int count)` - Emitted when the number of screens changes

**Properties (QML accessible):**
- `screen_count: int` - Number of connected displays
- `primary_screen_name: str` - Name of the primary display
- `has_multiple_screens: bool` - Whether multiple displays are connected

**Methods (QML callable):**
- `get_screen_count() -> int`
- `get_screen_info(index: int) -> dict`
- `get_all_screens_info() -> list[dict]`
- `get_primary_screen_info() -> dict`
- `is_valid_screen_index(index: int) -> bool`

#### 2. MainWindow.qml (QML)
**Location:** `python/paint_controller/qml/core/MainWindow.qml`

The main window has been updated to:
- Connect to ScreenManager signals
- Dynamically update window geometry when screens change
- Provide helper functions for screen switching
- Log screen events for debugging

**New Functions:**
- `updateWindowGeometry()` - Updates window position and size based on target screen
- `handleScreenAdded(index, name)` - Handles screen addition events
- `handleScreenRemoved(index, name)` - Handles screen removal events
- `switchToScreen(screenIndex)` - Switches the application to a specific screen
- `logScreenInfo()` - Logs information about all connected screens

#### 3. Display Settings Page (QML)
**Location:** `python/paint_controller/qml/pages/settings/DisplaySettingsPage.qml`

A new settings page that provides:
- List of all connected displays
- Visual indication of primary and active screens
- One-click screen switching
- Real-time updates when screens are added/removed
- Information about each display (resolution, refresh rate, position)

## Usage

### For Users

#### Accessing Display Settings

1. Launch the Paint Controller application
2. Navigate to **Settings** from the sidebar
3. Select **Display** (first option in Base Settings)
4. The Display Settings page shows:
   - Number of connected displays
   - List of all displays with their properties
   - Which display is currently active
   - Which display is the primary display

#### Switching Displays

1. In the Display Settings page, tap on any display from the list
2. The application window will immediately move to the selected display
3. The active display is marked with a green "Active" badge

#### Real-Time Display Detection

The application automatically detects when you:
- Connect an external monitor (display is added to the list)
- Disconnect a monitor (display is removed from the list)
- Change the primary display in system settings

No restart is required - changes are reflected immediately.

### For Developers

#### Integration Example

```python
from paint_controller.core.screen_manager import ScreenManager

# Create ScreenManager (after QApplication is initialized)
screen_manager = ScreenManager(parent=your_qobject)

# Access screen information
screen_count = screen_manager.screen_count
print(f"Connected displays: {screen_count}")

# Get all screen information
screens = screen_manager.get_all_screens_info()
for screen in screens:
    print(f"Screen: {screen['name']} - {screen['width']}x{screen['height']}")

# Connect to signals
screen_manager.screen_added.connect(on_screen_added)
screen_manager.screen_removed.connect(on_screen_removed)

# Cleanup when done
screen_manager.cleanup()
```

#### QML Integration

```qml
// Access screenManager from QML
Text {
    text: "Displays: " + screenManager.screen_count
}

// Get screen information
Component.onCompleted: {
    var screens = screenManager.get_all_screens_info()
    for (var i = 0; i < screens.length; i++) {
        console.log(screens[i].name)
    }
}

// React to screen changes
Connections {
    target: screenManager
    
    function onScreens_changed() {
        console.log("Screen configuration changed")
    }
}
```

## Testing

### Manual Testing

1. **Single Display Test:**
   - Launch application on a single-screen system
   - Verify Display Settings shows 1 display
   - Check that screen information is correct

2. **Multi-Display Test:**
   - Connect an external monitor
   - Verify Display Settings updates automatically
   - Try switching between displays
   - Verify window moves correctly

3. **Hot-Plug Test:**
   - With application running, connect/disconnect monitors
   - Verify real-time detection works
   - Check console logs for screen events
   - Verify window stays on a valid display

### Automated Testing

Run the test script:
```bash
cd python/paint_controller
python -m paint_controller.scripts.test_screen_manager
```

This will:
- Test ScreenManager initialization
- Verify property access
- Test all slot methods
- Validate screen information retrieval
- Monitor for real-time screen changes

## Technical Details

### Screen Detection Mechanism

Qt provides native screen management through `QGuiApplication`:
- `QGuiApplication.screens()` - Returns list of all screens
- `QGuiApplication.primaryScreen()` - Returns the primary screen
- `QGuiApplication.screenAdded` signal - Emitted when screen is connected
- `QGuiApplication.screenRemoved` signal - Emitted when screen is disconnected

The ScreenManager wraps these Qt APIs and exposes them to QML in a clean, reactive way.

### Window Positioning

Window geometry is set using:
- `x` and `y` - Position relative to virtual desktop (from `screen.virtualGeometry()`)
- `width` and `height` - Window dimensions (from `screen.size()`)

For multi-monitor setups:
- Each screen has a position in the virtual desktop coordinate system
- The virtual desktop encompasses all screens
- Moving the window is just changing its x/y coordinates

### Coordinate System Example

```
Primary Screen (0,0)          External Monitor (1920,0)
┌─────────────────┐          ┌─────────────────┐
│                 │          │                 │
│  1920x1080      │          │  1920x1080      │
│                 │          │                 │
└─────────────────┘          └─────────────────┘
```

## Compatibility

- **Supported:** X11, Wayland, Windows, macOS
- **Qt Version:** PySide6 (Qt 6.x)
- **Python Version:** 3.10+
- **Display Modes:** Extended, Duplicate, Single

## Troubleshooting

### Display not detected

1. Check if Qt can see the display:
   ```bash
   python -c "from PySide6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); print(len(app.screens()))"
   ```

2. Verify system display settings
3. Check console logs for screen events

### Window doesn't move to selected screen

1. Verify target screen index is valid
2. Check console logs for geometry updates
3. Ensure window is not being forced by window manager

### Real-time detection not working

1. Verify ScreenManager is properly initialized
2. Check that signals are connected
3. Test with the test script to isolate the issue

## Future Enhancements

Potential improvements for future versions:
- [ ] Remember user's screen preference
- [ ] Support for spanning window across multiple screens
- [ ] Per-screen DPI scaling
- [ ] Custom window modes (windowed, borderless, fullscreen per screen)
- [ ] Screen configuration presets
- [ ] Multi-window support (different windows on different screens)

## References

- [Qt QScreen Documentation](https://doc.qt.io/qt-6/qscreen.html)
- [Qt QGuiApplication Documentation](https://doc.qt.io/qt-6/qguiapplication.html)
- [Qt Multi-Screen Development](https://doc.qt.io/qt-6/topics-multi-screen.html)
