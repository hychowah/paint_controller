# Development Notes

---

### 2026-02-03 21:30 - Extract Reusable SettingInputField Component

**Goal**: Eliminate 800+ lines of repeated code in SettingsTab.qml
**Issues**: Each setting (winch speed, track speed, arm position, etc.) used identical 60-70 line pattern for label + input + save button
**Tried**: Created reusable SettingInputField.qml component with configurable properties
**Result**: ✅ Reduced SettingsTab.qml from 1048 → 412 lines (~60% reduction). Component is reusable across all settings.

**Pattern Identified**:
Every setting repeated:
- ColumnLayout container
- Label Text with range description  
- RowLayout with input Rectangle + TextInput + Save button
- Identical focus handling, hover states, save logic

**Solution**:
Created `components/inputs/SettingInputField.qml` (109 lines) with properties:
- `label`: Display text + range
- `settingKey`: Python property name (e.g., "winch_max_speed_mmps")
- `decimalPlaces`: 0 for integers, 1-2 for floats
- `unitSuffix`: For confirmation messages (e.g., " mm/s", " RPM")
- `numberPadTarget`: Reference to NumpadNew popup
- `confirmationPopup`: Reference to CustomPopup

**Key Design Choice**:
Uses global `settingsManager` context property (exposed from Python) instead of passing as prop. This matches Qt's pattern for context-injected objects.

**Exceptions**:
Kept 2 settings inline due to special logic:
- `thrust_force`: Updates `teensyController` immediately
- `thrust_ramp_rate`: Clamps value to 0.1-10.0 range

**Files**: 
- `qml/components/inputs/SettingInputField.qml` (NEW - reusable component)
- `qml/overlays/systemcontrol/SettingsTab.qml` (refactored to use component 8x)

---

### 2026-02-03 19:15 - Stop Bird View Processing When Not Visible

**Goal**: Prevent bird view transformation from running in background when not needed
**Issues**: Continuous frame processing wastes CPU even when bird view widget not visible
**Approach**: Add enabled property controlled by Python based on control mode and overlay state

**Implementation**:
1. **BirdViewService changes** (`services/bird_view_service.py`):
   - Added `enabled` Property (bool) with `enabledChanged` signal
   - Store `_base_front_stream` reference without immediately connecting
   - `enabled` setter connects/disconnects `frameReady` signal dynamically
   - Start with `_enabled = False` by default to save resources

2. **Application.py integration** (`core/application.py`):
   - `toggle_fullscreen()`: Enable bird view only when `control_mode == "base"` and overlay active
   - Disable bird view when overlay closes
   - `update_fullscreen_video_source()`: Update bird view enabled state when switching control modes
   - Bird view automatically disabled when switching to End Effector view

**Result**: ✅ Bird view transformation only runs when viewing base_front camera in fullscreen. Automatically pauses when switching to end effector or closing video overlay.
**Files**: 
- `services/bird_view_service.py` (enabled property + signal connection control)
- `core/application.py` (toggle_fullscreen + update_fullscreen_video_source)
- `qml/overlays/video/overlays/BaseFrontOverlay.qml` (removed lifecycle hooks)

---

### 2026-02-03 19:00 - Persist Bird View Settings to settings.json

**Goal**: Save/load bird view transformation parameters across app restarts using SettingsManager
**Issues**: All 9 parameters (zoom, pan, crop, distortion, source points) reset to defaults on restart
**Approach**: Extend SettingsManager with bool/list types, add schema entries, connect BirdViewService

**Implementation**:
1. **SettingsManager extensions** (`core/settings.py`):
   - Added "bool" and "list" type support to `_validate_and_convert()` method
   - Added 9 bird view schema entries with proper min/max/defaults
   - Added 9 Qt Property definitions with getters/setters
   - Added 9 signal definitions for property changes
   - Updated `_emit_setting_signal()` to handle bird view signals

2. **BirdViewService modifications** (`services/bird_view_service.py`):
   - Constructor now accepts `settings_manager` parameter
   - Loads all 9 settings after worker thread initialization using `settings_manager.get()`
   - `resetToDefaults()` updated to include `src_points_normalized` and persist all defaults via `settings_manager.save()`

3. **QML Save Button** (`qml/overlays/video/overlays/BirdViewSettingsPopup.qml`):
   - Added "Save Settings" button with blue styling before Reset button
   - Copies all bird view properties from birdViewController to settingsManager
   - Calls `saveSetting()` for each parameter individually
   - Shows CustomPopup with "Saved" or "Failed to save settings" message
   - Added CustomPopup import and component

4. **Application integration** (`core/application.py`):
   - Passed `settings_manager` to BirdViewService constructor during initialization

**Settings Persisted** (9 parameters):
- `bird_view_zoom` (float, 0.606, 0.1-2.0)
- `bird_view_offset_x` (float, 0.026, -1.0-1.0)
- `bird_view_offset_y` (float, 0.474, -1.0-1.0)
- `bird_view_crop_enabled` (bool, True)
- `bird_view_crop_width_ratio` (float, 0.9, 0.1-1.0)
- `bird_view_crop_center_x` (float, 0.5, 0.0-1.0)
- `bird_view_k1` (float, 0.32, 0.0-1.0)
- `bird_view_k2` (float, 0.272, 0.0-1.0)
- `bird_view_src_points` (list, [[0.012,1.0], [0.988,1.0], [0.837,0.727], [0.372,0.727]])

**Result**: ✅ Bird view settings persist across restarts. Manual save button consistent with existing UI patterns (SettingsTab.qml). Settings auto-load on BirdViewService init.
**Files**: 
- `core/settings.py` (schema + properties + signals + validation)
- `services/bird_view_service.py` (load settings + save on reset)
- `qml/overlays/video/overlays/BirdViewSettingsPopup.qml` (save button + popup)
- `core/application.py` (pass settings_manager to BirdViewService)

---

### 2026-02-03 18:30 - Add Click-and-Drag Point Editor for Perspective Tuning

**Goal**: Add visual point editor with drag-and-drop for the four trapezoid source points
**Issues**: Sliders inadequate for tuning perspective coordinates—need visual feedback
**Approach**: Overlay with Canvas trapezoid + draggable corner handles

**Implementation**:
1. **BirdViewService additions**:
   - `sourcePoints` Property exposing src_points_normalized array
   - `updateSourcePoint(index, x, y)` Slot updates individual points
   - `editMode` Property toggles point editor visibility
   - Points stored as normalized coords (0.0-1.0), auto-scaled to pixels when initialized
   - Increased crop_width_ratio default from 0.656 → 0.9 (270px vs 197px wide output)

2. **PointEditorOverlay.qml**: Interactive visual editor
   - Canvas draws trapezoid connecting 4 points with dashed lines
   - 4 draggable circular handles (20px) with labels (BL/BR/TR/TL)
   - Real-time coordinate display next to each point
   - Active point highlighted in red vs green
   - Constrained dragging within bounds
   - ESC or "Done Editing" button exits mode
   - Semi-transparent dark overlay for contrast

3. **BirdViewSettingsPopup**: Added "Edit Source Points" button
   - Opens point editor and closes settings popup
   - Prominent placement at top with pencil icon

4. **BaseFrontOverlay layout changes**:
   - PointEditorOverlay inside birdViewWidget
   - MouseArea disabled during edit mode
   - Moved widget from bottom-center to right-middle (anchored to right edge, verticalCenter)
   - z-index 200 keeps editor above video

**Result**: ✅ Can visually adjust perspective by dragging trapezoid corners, see effect immediately. Wider output for better usability.
**Files**: 
- `services/bird_view_service.py` (sourcePoints property + updateSourcePoint slot + wider crop)
- `qml/overlays/video/overlays/PointEditorOverlay.qml` (new)
- `qml/overlays/video/overlays/BirdViewSettingsPopup.qml` (edit button)
- `qml/overlays/video/overlays/BaseFrontOverlay.qml` (integrated editor + repositioned)

---

### 2026-02-03 18:00 - Add Bird View Transformation Parameter UI

**Goal**: Add popup interface to adjust bird view transformation parameters in real-time
**Approach**:
- Expose all BirdViewTransformer parameters as Qt Properties
- Create settings popup with sliders for real-time adjustment
- Open popup by tapping bird view widget

**Implementation**:
1. **BirdViewService Properties**: Added Qt Properties with signal emission:
   - zoom, offsetX, offsetY (pan control)
   - cropEnabled, cropWidthRatio, cropCenterX
   - k1, k2 (fisheye distortion coefficients)
   - `resetToDefaults()` Slot restores default values
   - Property setters trigger `_calculate_destination_points()` for immediate effect
   - Distortion changes reinitialize undistortion maps

2. **BirdViewSettingsPopup.qml**: Created popup with 8 sliders + toggle
   - Custom `SettingSlider` component for consistency
   - Real-time binding to `birdViewController` properties
   - Reset and Close buttons in bottom bar
   - 500x650px modal popup

3. **Tap handler**: Added MouseArea to birdViewWidget
   - Opens popup on click
   - Cursor changes to pointing hand for discoverability

**Result**: ✅ Can adjust bird view transformation live while viewing camera
**Files**: 
- `services/bird_view_service.py` (Qt Properties added)
- `qml/overlays/video/overlays/BirdViewSettingsPopup.qml` (new)
- `qml/overlays/video/overlays/BaseFrontOverlay.qml` (MouseArea + popup)

---

### 2026-02-03 15:30 - Bird View Integration with QThread

**Goal**: Integrate bird_view transform feature from /bird_view into main GUI with minimal CPU overhead
**Approach**: 
- Created `BirdViewService` following `VideoStreamHandler` pattern
- Reuses BASE_FRONT camera stream (no duplicate ROS2 subscription)
- QThread worker pattern prevents UI blocking
- Downscales 640x480→320x240 before transformation to reduce CPU load
- Frame skipping when processing exceeds 33ms to stay realtime

**Implementation**:
1. **BirdViewTransformer**: Extracted core logic from bird_view_transform.py
   - Fisheye undistortion with cached maps (k1=0.32, k2=0.272)
   - Perspective transform with default parameters (zoom=0.606, pan=0.026/0.474)
   - Vertical crop enabled (ratio=0.656)
   - Source points scaled for 320x240 input
   - Output: 200x267px for GUI display

2. **BirdViewWorker**: QThread worker for async processing
   - Converts QImage→numpy→cv2 processing→QImage
   - Downscales before transformation (2x reduction)
   - `_processing` flag skips frames if previous transform still running
   - Thread-safe image provider updates with QMutex

3. **Integration**:
   - Service connects to `video_handler.camera_streams[BASE_FRONT].frameReady` signal
   - ImageProvider registered as "bird_view" in QML engine
   - Display in BaseFrontOverlay.qml bottom center (above wheel panels)
   - Connections block refreshes on frameReady signal

**Result**: ✅ Bird view displays in overlay without blocking UI, minimal CPU impact
**Files**: 
- `services/bird_view_service.py` (new)
- `core/application.py` (registration)
- `qml/overlays/video/overlays/BaseFrontOverlay.qml` (UI display)

---

### 2026-01-29 16:30 - Fix Mode Switch Crash from Popup Collision

**Goal**: Fix crash when switching control modes immediately after sending wheel travel command
**Issues**: 
- Crash occurred when pressing A (wheel travel) then immediately switching modes (base ↔ EF)
- Error: "QObject::killTimer: Timers cannot be stopped from another thread" followed by emergency shutdown
- Root cause: Popup tried to render while video overlay Loader was destroying/creating components

**Investigation**:
1. Initial hypothesis: Threading issue with timers in cleanup
   - Multiple QTimers created in main thread, stopped from ROS thread during emergency cleanup
   - Found 8+ components with problematic timer management
2. Realized popup overlap alone doesn't crash (L5→R5 rapid press works fine)
3. **Real root cause**: QML scene graph conflict during mode switch:
   - Mode switch triggers `update_fullscreen_video_source()`
   - Video overlay Loader destroys old component (BaseFrontOverlay) and creates new (EndEffectorOverlay)
   - `show_popup()` called during this transition
   - Popup rendering conflicts with Loader's component destruction/creation
   - Qt scene graph becomes unstable → crash → emergency shutdown

**Solution**:
1. Close any existing popup BEFORE mode switch to clear rendering state
2. Defer new popup by 150ms using `QTimer.singleShot()` to let Loader stabilize
3. Added try/except around popup closing for safety

**Result**: ✅ No crash when rapidly switching modes after commands. Popup appears with imperceptible 150ms delay.

**Files**: `handlers/input.py` (on_switch_pressed method)

---

### 2026-01-28 14:30 - Wheel Travel Settings & Accumulation Fix

**Goal**: Fix wheel travel accumulation logic and add configurable settings

**Issues**:
- Accumulation was wrong: directly set value instead of `new_value = past_value + (joystick * scale)`
- Hardcoded constants (max=500mm, rate=20, rpm=300) not configurable
- Single "Wheel Travel" mode couldn't control left/right wheels independently
- `inputHandler` typo caused AttributeError on A button press

**Implementation**:
1. Added settings to `settings.py`:
   - `wheel_travel_max`: default 500mm, range 100-1000mm
   - `wheel_travel_rate`: default 100mm/sec, range 10-500mm/sec (NEW - controls adjustment speed)
   - `wheel_travel_rpm`: default 300, range 50-600 RPM
2. Added UI controls in SettingsTab.qml (Track Control section)
3. Fixed accumulation in `_process_wheel_travel()`:
   - Changed from `value = joystick * scale` to `value += joystick * scale`
   - Clamps total (not delta) to ±wheel_travel_max
   - Scale computed dynamically: `(rate * update_interval) / 32768`
4. Split "Wheel Travel" into "Wheel Travel Left" and "Wheel Travel Right":
   - Mode name determines which wheel to control (not joystick side)
   - Both joysticks can control same wheel if both set to same mode
5. Fixed `inputHandler` → `input_handler` typo in application.py
6. Updated all mode checks in input.py, application.py, control_processor.py

**Result**: ✅ Proper accumulation, configurable settings, independent left/right control

**Files**: `core/settings.py`, `handlers/control_processor.py`, `handlers/input.py`, `core/application.py`, `ui/overlay.py`, `qml/overlays/systemcontrol/SettingsTab.qml`

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