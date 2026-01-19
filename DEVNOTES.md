# Development Notes

---

### 2026-01-19 - Multi-Screen Display Implementation

**Goal**: Automatic multi-screen support — Main UI on external monitor, secondary window on Steam Deck built-in screen

**Issues**:
1. QML UI only appeared on one monitor despite Python detecting 2 screens
2. `TypeError: Cannot read property 'width' of undefined` on screen geometry
3. `Qt.application.screens` showed stale count when disconnect signal fired
4. Secondary window opened windowed instead of fullscreen (visible/visibility conflict)

**Tried**:
1. Storing `Qt.application.screens` as static property → failed; changed to dynamic index lookup
2. `screen.geometry.width` → wrong; Qt uses `screen.width` directly
3. Immediate screen repositioning in signal handler → stale data; added 100ms Timer delay
4. Setting both `visible: false` and `visibility: Window.FullScreen` → conflict; use only `visibility`

**Result**: ✅ All working — auto-detection, real-time connect/disconnect, fullscreen on both screens

**Files**: `qml/core/MainWindow.qml`, `qml/overlays/MultiScreenListUI.qml`

**Behavior**:
| Condition | Main UI | Secondary Window |
|-----------|---------|------------------|
| 1 monitor | Built-in (eDP) | Hidden |
| 2 monitors | External (DisplayPort) | Built-in, fullscreen |
| Monitor connected | Moves to external | Opens on built-in |
| Monitor disconnected | Moves to built-in | Closes |

**Future**: ~~Replace secondary window debug content with useful dashboard~~ ✅ Done (see Industrial Monitor below); persist screen preferences; handle >2 screens

---

### 2026-01-19 - Industrial Monitor UI Implementation

**Goal**: Create a dedicated 1280x720 monitoring interface for secondary screen (Steam Deck built-in) with modular architecture and 7-inch display optimization.

**Approach**:
- Split monolithic 1073-line QML into 7 modular components (115-223 lines each)
- Created reusable cards: MonitorHeader, WheelsCard, ValvesCard, TeensyArmCard, WinchCard, IMUCard
- Increased font sizes 6-25% for 7-inch screen readability (primary values 32-34px, labels 11-14px)
- Implemented 3-column layout: Mobility (30%) | Core Operations (40%) | Sensors (30%)
- Added standalone test script with mock controllers for development without hardware

**Layout Structure**:
1. **Header Bar (80px)**: Telemetry (voltage, temp, loop time) | Status badges (relay, enable) | E-Stop button
2. **Main Body (640px)**: Wheels + Valves | Teensy Arm + Winch | IMU grid with sparklines

**Color Scheme** (Industrial Dark):
- Background: `#1e222b`, Cards: `#29303b` (8px radius)
- Green: `#2ecc71` (nominal), Cyan: `#3498db` (motion), Red: `#e74c3c` (emergency), Amber: `#f39c12` (warnings)

**Files**:
- Main: `qml/pages/status/PageMonitor.qml` (115 lines)
- Components: `qml/components/displays/{MonitorHeader,WheelsCard,ValvesCard,TeensyArmCard,WinchCard,IMUCard}.qml`
- Test: `scripts/test_industrial_monitor.py` (347 lines with mock controllers)
- Integration: `qml/overlays/MultiScreenListUI.qml`

**Data Sources**:
- `teensyController.all_status.*` (voltage, temp, loop time, IMU, arm, valves, spray gun)
- `wheelController.*` (speed, current, motor availability for L/R wheels)
- `winchController.*` (cable length, speed, torque, voltage, temperature)

**Result**: ✅ Modular architecture (90% reduction in main file size), optimized for 7-inch displays, standalone testable

**Issues Fixed**:
- **Layout recursion**: Using `parent.width * 0.30` in RowLayout caused circular dependency. Fixed with weight-based layouts (`Layout.preferredWidth: 3` for 30% of total 10).
- **Test script display**: QQmlApplicationEngine can't display Rectangle roots. Switched to QQuickView with SizeRootObjectToView mode.
- **Font sizes**: Increased throughout for 7-inch screen readability (see KNOWLEDGE.md).

---

### 2026-01-19 18:00 - Monitor UI: Test Script & Layout Fixes

**Goal**: Enable standalone testing of monitor UI without main app

**Issues**:
1. Test script said "loaded successfully" but no window appeared
2. Console flooded with `Qt Quick Layouts: Detected recursive rearrange` errors

**Root Causes**:
1. `QQmlApplicationEngine` requires Window root, not Rectangle
2. Layout children used `parent.width * 0.30` causing circular dependency

**Solution**:
1. Switched to `QQuickView` with `SizeRootObjectToView` mode
2. Replaced percentage-based widths with weight-based layouts: `Layout.preferredWidth: 3` (30% of total 10)
3. Created mock controllers (TeensyController, WheelController, WinchController) with realistic 10Hz data simulation

**Result**: ✅ Window displays correctly, no layout warnings, fully functional standalone test

**Files**: `scripts/test_industrial_monitor.py`, `qml/pages/status/PageMonitor.qml`

---