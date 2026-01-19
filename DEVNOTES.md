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

**Goal**: Create a dedicated 1280x720 industrial-style monitoring interface for the secondary screen (Steam Deck built-in) with dark theme, clear visual hierarchy separating passive monitoring from active controls.

**Approach**:
- Replaced `MultiScreenListUI` test interface with `PageIndustrialMonitor`
- Created 4 reusable components: `IndustrialCard`, `MonospaceDataLabel`, `ProgressBarIndicator`, `Sparkline`
- Implemented 3-column layout: Mobility (30%) | Core Operations (40%) | Sensors (30%)
- Used monospace fonts for all numerical values to prevent layout shift

**Layout Structure**:
1. **Header Bar (80px)**: Telemetry (voltage, temp, loop time) | Status badges (relay, enable) | E-Stop button
2. **Main Body (640px)**: Wheels + Valves | Teensy Arm + Winch | IMU grid with sparklines

**Color Scheme** (Industrial Dark):
- Background: `#1e222b`
- Cards: `#29303b` (8px radius)
- Green: `#2ecc71` (nominal/enabled)
- Cyan: `#3498db` (fluid/motion)
- Red: `#e74c3c` (emergency only)
- Amber: `#f39c12` (warnings)

**Files**:
- `qml/pages/status/PageIndustrialMonitor.qml` (main page, 1000+ lines)
- `qml/components/displays/IndustrialCard.qml`
- `qml/components/displays/MonospaceDataLabel.qml`
- `qml/components/displays/ProgressBarIndicator.qml`
- `qml/components/displays/Sparkline.qml`
- `qml/overlays/MultiScreenListUI.qml` (updated to load industrial monitor)

**Data Sources**:
- `teensyController.all_status.*` (voltage, temp, loop time, IMU, arm, valves, spray gun)
- `wheelController.*` (speed, current for L/R wheels)
- `winchController.*` (cable length, speed, torque, voltage)

**Result**: ✅ All QML files pass syntax checks. Ready for hardware testing.

---

### 2026-01-19 16:00 - Code Review Notes

**Status**: ✅ Good quality, minor cleanup needed

**Items to address**:
- Reduce debug logging (18 `console.log` statements)
- Extract screen positioning logic to helper function
- Replace magic numbers (100ms, screen indices) with constants
- Add validation for >2 screen edge cases
