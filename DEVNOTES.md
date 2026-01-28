# Development Notes

---

### 2026-01-28 05:30 - Wheel Travel Position Control Mode

**Goal**: Add joystick control mode for position-based wheel movement with button trigger

**Requirements**:
- Joystick adjusts travel distance (±500mm) without immediate command send
- Fixed speed of 300 RPM for movement
- A button triggers the actual position command

**Implementation**:
1. Added "Wheel Travel" to control options in `overlay.py`
2. Added ControlConfig in `control_processor.py`:
   - Scale: 500mm / 32768 (joystick max) = ~0.0153
   - Bidirectional with ±500mm range
   - Created `_process_wheel_travel()` handler to accumulate values
   - Added `send_wheel_travel_command()` method for button trigger
3. Modified A button handler in `application.py`:
   - Checks if Wheel Travel mode active on either joystick
   - Sends position command if active, else toggles LiDAR overlay
4. Display formatting shows travel distance in mm

**Pattern**: Similar to Winch Speed bidirectional control, but stores value without immediate publish

**Result**: ✅ Joystick accumulates travel distance, A button sends command via existing position publisher

**Files**: `ui/overlay.py`, `handlers/control_processor.py`, `handlers/input.py`, `core/application.py`

---

### 2026-01-22 03:00 - Winch Speed Deadzone Timeout

**Goal**: Stop sending winch speed commands when joystick remains in deadzone (speed = 0) for >1 second

**Implementation**:
1. Added deadzone tracking variables: `winch_speed_in_deadzone`, `winch_speed_deadzone_start_time`, `winch_speed_should_send`
2. Added constants: `WINCH_SPEED_DEADZONE = 0.05`, `WINCH_SPEED_DEADZONE_TIMEOUT = 1.0`
3. Created dedicated `_process_winch_speed()` handler with timeout logic
4. Added "Winch Speed" to `_control_handlers` dispatch table
5. Removed winch-specific handling from `_process_standard_control()`

**Pattern**: Follows existing `_process_valve_turn()` implementation for consistency

**Result**: ✅ Commands stop after 1s in deadzone, resume immediately when joystick exits deadzone

**Files**: `handlers/control_processor.py`

---

### 2026-01-21 04:30 - Mode-Specific Joystick Control Memory

**Goal**: Remember joystick control selections separately for each control mode (base/ef)

**Issues**: 
- Original implementation had joystick controls reset to hardcoded defaults on mode switch
- User's modification removed default fallback causing UnboundLocalError on first switch

**Implementation**:
1. Added `_base_mode_joystick_controls` and `_ef_mode_joystick_controls` state in UIInputHandler
2. Modified `on_switch_pressed()` to save/restore mode-specific controls
3. Added `get_current_joystick_controls()` in OverlayController
4. Refactored control_processor.py with dispatch table pattern (reduced 20+ lines)

**Result**: ✅ Mode switching preserves user's joystick preferences; dispatch table improves maintainability

**Files**: `handlers/input.py`, `ui/overlay.py`, `handlers/control_processor.py`

---

### 2026-01-21 01:20 - Thrust Force Ramp Up/Down Control

**Goal**: Add configurable ramp up/down control for L1 button thrust force to prevent rapid/instant force application

**Implementation**:
1. Added `thrust_ramp_rate` setting to SettingsManager (default: 1.0, range: 0.1-10.0 thrust/s)
2. Modified TeensyController to use QTimer at 10Hz for smooth ramping
3. Created two methods:
   - `set_thrust_force_enabled()` - Uses ramping (L1 button uses this)
   - `set_thrust_force_instant()` - Instant thrust (preserved for future use)
4. Added UI controls in SettingsTab.qml for ramp rate configuration

**Technical Details**:
- Timer runs at 10Hz (100ms intervals) - matches max command rate requirement
- Ramp rate = thrust/second (1.0 = 0 to 1 in 1 second)
- State tracking: `_current_thrust_force`, `_target_thrust_force`, `_thrust_ramp_rate`
- Graceful ramp up when enabled, ramp down when disabled

**Result**: ✅ Smooth thrust force application with configurable rate

**Files**: `core/settings.py`, `controllers/teensy.py`, `qml/overlays/systemcontrol/SettingsTab.qml`

---

### 2026-01-20 04:00 - SystemControlMenu Dual-Monitor Support

**Goal**: Move SystemControlMenu to touchscreen display when in dual-monitor mode

**Context**: Main UI moves to external (non-touchscreen) monitor when detected. SystemControlMenu relies on touch interaction, so it should appear on built-in touchscreen (showing PageMonitor) instead of main UI in dual-monitor mode.

**Solution**:
1. Added SystemControlMenu to MultiScreenListUI.qml (secondary screen window)
2. Made SystemControlMenu in MainWindow.qml conditional: `visible: screenCount <= 1`
3. SystemControlMenu now appears on touchscreen when 2 monitors detected

**Result**: ✅ SystemControlMenu appears on correct screen based on monitor configuration

**Files**: `qml/core/MainWindow.qml`, `qml/overlays/MultiScreenListUI.qml`

**Behavior**:
| Condition | SystemControlMenu Location |
|-----------|---------------------------|
| 1 monitor | Main UI (built-in) |
| 2 monitors | Secondary window (built-in touchscreen) |

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