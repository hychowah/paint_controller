# Development Notes: Multi-Screen Display Implementation

**Date:** January 19, 2026  
**Feature:** Multi-screen UI support for Steam Deck + external monitor

---

## Summary

Successfully implemented automatic multi-screen display support where:
- **Main UI** displays fullscreen on the **external monitor** (DisplayPort-0)
- **Secondary window** (MultiScreenListUI) displays fullscreen on the **built-in Steam Deck screen** (eDP)
- Automatic switching when monitors are connected/disconnected

---

## Problems Encountered & Solutions

### 1. Screen Detection Working but UI Not Appearing on Second Monitor

**Problem:** The `ScreenManager` Python class correctly detected 2 screens, but the QML UI only appeared on one monitor.

**Root Cause:** The original implementation used `Qt.application.screens` as a static property that wasn't being re-queried properly.

**Solution:** Changed from storing the screens list to using the `screen` attached property directly:
```qml
// Before (broken)
property var screens: Qt.application.screens
screen: screens[primaryScreenIndex]

// After (working)
property int mainScreenIndex: Qt.application.screens.length > 1 ? 1 : 0
screen: Qt.application.screens[mainScreenIndex] || Qt.application.screens[0]
```

---

### 2. TypeError: Cannot read property 'width' of undefined

**Problem:** Console errors when accessing screen geometry properties.

**Root Cause:** Used `screen.geometry.width` but Qt Screen objects expose dimensions directly as `screen.width`.

**Solution:** Changed property access:
```qml
// Before (wrong)
width: screen.geometry.width
height: screen.geometry.height

// After (correct)
width: screen.width
height: screen.height
```

---

### 3. Qt.application.screens Not Updated When Signal Fires

**Problem:** When a monitor was disconnected, the Python `ScreenManager` correctly detected 1 screen, but `Qt.application.screens.length` still showed 2 in QML.

**Root Cause:** Timing issue - the Python signal fires before Qt's internal screen list updates.

**Solution:** Added a 100ms Timer to delay screen repositioning:
```qml
Timer {
    id: screenUpdateTimer
    interval: 100  // Wait for Qt to update screen list
    repeat: false
    onTriggered: {
        var appScreens = Qt.application.screens
        // Now appScreens has the correct count
        ...
    }
}

Connections {
    target: screenManager
    function onScreens_changed() {
        screenUpdateTimer.restart()  // Use timer instead of immediate action
    }
}
```

---

### 4. Secondary Window Not Opening in Fullscreen

**Problem:** When plugging in a second monitor, the secondary window appeared in windowed mode instead of fullscreen.

**Error:** `QML MultiScreenListUI: Conflicting properties 'visible' and 'visibility'`

**Root Cause:** Setting both `visible: false` (initial state) and `visibility: Window.FullScreen` (when opening) causes Qt conflicts.

**Solution:** Removed `visible` property entirely and use only `visibility`. Created helper functions:
```qml
// MultiScreenListUI.qml
Window {
    // NO visible property!
    property bool fullscreenMode: false
    visibility: fullscreenMode ? Window.FullScreen : Window.Hidden
    
    function showWindow() {
        visibility = fullscreenMode ? Window.FullScreen : Window.Windowed
    }
    
    function hideWindow() {
        visibility = Window.Hidden
    }
}
```

---

## Files Modified

| File | Changes |
|------|---------|
| `qml/core/MainWindow.qml` | Screen selection logic, auto-open/close, Timer for screen updates |
| `qml/overlays/MultiScreenListUI.qml` | Fullscreen mode support, visibility management |

---

## Current Behavior

| Condition | Main UI Location | Secondary Window |
|-----------|------------------|------------------|
| 1 monitor (startup) | Built-in (eDP) | Not shown |
| 2 monitors (startup) | External (DisplayPort) | Built-in (eDP), fullscreen |
| Monitor connected | Moves to external | Opens on built-in, fullscreen |
| Monitor disconnected | Moves to built-in | Closes automatically |

---

## Testing Commands

```bash
# Test screen detection standalone
cd ~/ros2_ws/src/paint_controller_ros2/python/paint_controller/scripts
python3 test_multiscreen.py

# Run main application
paint_controller
```

---

## Known Working

- ✅ Screen detection (Python ScreenManager)
- ✅ Real-time monitor connect/disconnect detection
- ✅ Main UI fullscreen on external monitor
- ✅ Secondary window fullscreen on built-in screen
- ✅ Auto-switch when monitor connected
- ✅ Auto-close secondary when monitor disconnected
- ✅ Manual toggle via Settings menu still works

---

## Future Improvements

1. **Secondary window content** - Currently shows MultiScreenListUI (debug info). Replace with actual useful content (video feed, status dashboard, etc.)

2. **Screen preference persistence** - Save user's preferred screen assignments

3. **Handle more than 2 screens** - Current logic assumes max 2 screens

4. **Primary screen detection** - Currently assumes eDP is always index 0 and external is index 1. Could be more robust.

---

## Key Lessons Learned

1. **Qt Screen property access**: Use `screen.width` not `screen.geometry.width`

2. **visible vs visibility conflict**: Never use both on a Window. Use `visibility` exclusively with `Window.Hidden`, `Window.Windowed`, `Window.FullScreen`

3. **Signal timing**: Python signals may fire before Qt's internal state updates. Use a short Timer (100ms) to let Qt catch up.

4. **Qt.application.screens**: This is a dynamic list but may have stale data immediately after screen changes. Re-query after a delay.

---

## Code Review Notes (Jan 19, 2026)

**Status**: ✅ Good quality, minor improvements recommended

**Strengths**:
- Excellent problem-solution documentation
- Proper null checks and error handling
- Clean signal-based architecture
- Working solution to Qt timing issues

**Items to Address**:
- Heavy debug logging (18 console.log) - reduce for production
- Code duplication in screen positioning logic - extract helper function
- Magic numbers (100ms, screen indices) - consider constants
- Hardcoded 2-screen assumption - add validation for edge cases

**Recommendation**: Functional and well-documented. Consider cleanup before production release.
