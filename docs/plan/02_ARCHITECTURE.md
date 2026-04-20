# Paint Controller Architecture Reference

> **Source**: Codebase review (2026-04). Updated 2026-04-17 with audit findings, implementation progress, and test/documentation sync.
> **Canonical location**: `docs/plan/02_ARCHITECTURE.md`
> **Related**: [01_MASTER_PLAN.md](01_MASTER_PLAN.md) | [03_QML_BINDINGS.md](03_QML_BINDINGS.md) | [04_AUDIT_REPORT.md](04_AUDIT_REPORT.md)

---

## Project Overview

Steam Deck-based robotic paint controller with ROS2 backend and PySide6/QML UI. Hybrid Python + C++ codebase for controlling a multi-DOF painting robot with cameras, winch, wheels, propellers, Lidar, and spray systems.

**Tech Stack**: ROS2 (Humble/Jazzy), Python 3.10+, PySide6 (Qt 6), QML, C++, OpenCV, GStreamer, VTK, UDP

---

## Architecture Layer Overview

### 1. Core Application Layer (`python/paint_controller/core/`)

**Current orchestration is split across focused core units**

**`main()` in `core/application.py`**
- Owns boot order and runtime wiring
- Creates the Qt app, ROS node, settings/state objects, Steam Deck handler, video services, QML engine, bridge, and controller bundle
- Exposes all runtime objects through `setContextProperty()` (NOT `qmlRegisterSingletonInstance` — broken in PySide6, see KNOWLEDGE.md)
- 22 context properties registered before `engine.load()`
- Post-load validation loop checks all 22 properties for `None`
- Starts timers, ROS thread, system monitor, and shutdown cleanup
- Video streams deferred via `QTimer.singleShot(200, ...)` to avoid blocking first render
- Startup instrumented with `time.perf_counter()` markers (`[startup +NNN.N ms] stage`)
- Cleanup runs on main Qt thread (not background thread) to avoid cross-thread `QTimer` warnings

**`PaintRosNode(Node)`**
- Pure ROS2 node with no Qt inheritance
- Owns the controller heartbeat publisher and ROS cleanup hook
- Keeps ROS lifecycle separate from QML/UI concerns

**`StateStore(QObject)`**
- Thread-safe shared UI/controller state
- Holds display message, control mode, and joystick control info for QML binding
- Exposed via `setContextProperty("stateStore", ...)`

**`QtBridge(QObject)`**
- Signal-based UI bridge for popups, sidebar/fullscreen toggles, multiscreen window, and fullscreen source updates
- **All popup/sidebar/video `findChild()` calls eliminated** — replaced with Qt signals consumed by QML `Connections` block; `UIInputHandler` closes popups through an injected `close_popup_fn`
- Signals: `showPopupRequested(str,str,str,int)`, `closePopupRequested()`, `toggleSidebarRequested()`, `toggleVideoOverlayRequested(bool,str)`, `updateVideoSourceRequested(str)`
- Only remaining QML object access: `engine.rootObjects()[0]` in `toggle_multiscreen_window()` via `QMetaObject.invokeMethod`
- Reads `StateStore` rather than owning application state itself
- Deferred wiring: `set_base_top_view_service()`, `set_input_handler()`

**`ControllerBundle` + `create_controllers()`**
- Factory-built dependency graph for controllers, handlers, and services
- `ControllerBundle` is a lifecycle container with reverse-order cleanup
- This is the real runtime composition layer now that the Python `RobotController` class is gone

**ROS2 Thread**: `RosThread(QThread)`
- Isolated event loop (non-blocking `spin_once`)
- Network error recovery with exponential backoff
- Watchdog timeout detection (5s)
- Graceful cleanup on shutdown

**Settings Management**: `SettingsManager(QObject)` - ~500 lines
- Centralized config persistence (JSON: `~/ros2_ws/src/paint_controller_ros2/python/config/settings.json`)
- ~25 settings: winch speed, track limits, arm positions, video calibration
- Qt signal/property pattern for QML binding
- Validation with min/max/type metadata
- Backward compatibility with defaults

**Runtime registration state**
- All 22 live runtime objects are exposed via `setContextProperty()`
- The singleton-registration track was cancelled because `qmlRegisterSingletonInstance()` is broken in this PySide6 setup
- Remaining Phase 1 work is import/qmldir/property cleanup, not controller singleton migration
- The C++ source files (`src/*.cpp`, `include/paint_controller/*.hpp`) were deleted in Phase 1A

---

### 2. Input/Control Handlers Layer (`python/paint_controller/handlers/`)

#### **Steam Deck Input Handler** - `SteamDeckHandler(QObject)` ~400 lines
- **HID Device Layer**: Valve USB interface (`0x28DE:0x1205`)
- Multi-threaded: `SteamDeckReaderThread(QThread)` for non-blocking USB reads
- State tracking:
  - **Joysticks**: Left/right with smoothing + dead-zone (configurable 0.1 default)
  - **Buttons**: 20 buttons with debounce timing, hold callbacks
  - **Triggers**: Analog values 0-32768
  - **IMU**: Pitch/roll/yaw from internal accelerometer
- Button pressure tracking for double-press detection
- Signals: `input_state_changed`, `button_held`, `button_hold_progress`

**Known Quirks**:
- 100Hz polling sufficient (reduced from 1kHz per KNOWLEDGE.md)
- Port-specific button event delivery is critical

#### **Input Processor** - `UIInputHandler(QObject)` ~100 lines
- Maps Steam Deck buttons → robot actions
- Double-press detection with 1s timeout (arm extend/retract)
- Mode switching: base (track control) ↔ EF (end-effector)
- Menu navigation (up/down/left/right)
- Settings integration for arm presets
- Popup close uses `close_popup_fn` callable (injected via constructor), no `findChild`

#### **Control Processor** - `ControlProcessor(QObject)` ~400 lines
- **Complex joystick-to-command mapping**:
  - Track control: Non-linear curve for friction compensation (dead-zone 5%, threshold 60%)
  - Winch speed: Bidirectional with lock-out when at limits
  - Wheel travel: Continuous accumulation until button press
  - EF controls: 10+ different joystick mappings (arm, rail, trigger, pitch, yaw, etc.)
- Display update at 5Hz (200ms throttle)
- Per-command interval throttling: 10Hz typical
- Valve turn deadzone: 2s timeout to reset
- Settings-driven: Scale factors, min/max bounds dynamically loaded

#### **Emergency Handler** - `EmergencyButtonHandler(QObject)` ~150 lines
- Steam button hold-to-trigger (200ms default)
- Progressive overlay feedback (duration/target_duration)
- Cooldown: 1s between activations
- Actions: Winch/wheel stop, spray trigger disable, error popup
- State machine: idle → holding → triggered → cooldown

#### **Heartbeat Monitor** - `UIHeartbeatHandler(QObject)` ~200 lines
- Monitors 3 subsystems: controller, base robot, end-effector
- Timeout-based disconnection detection (1s timeout)
- Status polling every 200ms
- Enum: IDLE(0x00), ONTASK(0x01), WARNING(0x02), ERROR(0x03)
- Topics: `/controller/heartbeat`, `/base/heartbeat`, `/ef/heartbeat`

#### **Warning Handler** - Minimal (~50 lines)
- Simple warning queue with dedup
- QML-bindable property
- Starts empty at runtime; no placeholder warning rows
- **NOTE (Audit D5)**: No `cleanup()` method — intentionally omitted from `ControllerBundle.cleanup()`

---

### 3. Hardware Controllers Layer (`python/paint_controller/controllers/`)

#### **Wheel Controller** - `WheelController(QObject)` ~250 lines
- ROS2 publisher: `MoveVehicleSpd`, `MoveVehiclePos`
- ROS2 subscriber: `VehicleStatus`
- Motor state tracking: left/right speed, current, position
- Motor availability: Per-track error state + online status
- Error signal: Triggers emergency overlay on motor failure
- Connection timeout: 1s before considered offline
- Unified speed command (both tracks via single message)

#### **Winch Controller** - `WinchController(QObject)` ~200 lines
- ROS2 publisher: speed (RPM/mm·s), enable, move commands
- ROS2 subscriber: `WinchStatus`
- Cable tracking: length, velocity, torque, motor temp
- Load detection mode
- Move commands: Increment, absolute, with acceleration control
- Settings integration: max_speed_mmps loaded from SettingsManager
- Availability guards are re-enabled on the speed and move-command paths; the winch test suite covers the speed-path behavior and transport validation; move-command guard coverage (method-level availability check in `WinchController.move_*`) is tested via `test_control_processor.py` at the ControlProcessor dispatch layer

#### **Teensy Controller** - `TeensyController(QObject)` ~300 lines
- ROS2 publisher: 20+ topics for sprayer, gimbal, props, relay, LED
- ROS2 subscriber: `TeensyStatus` (comprehensive ARM/EF sensor fusion)
- Sensor fusion: IMU (accel/pitch/roll/yaw), gimbal angles, motor temps
- Thrust force ramping: 100ms update (configurable rate from settings)
- Spray trigger: 0-2000 range (1000 = neutral)
- Gimbal control: Pitch speed + angle, roll motors (PWM)
- Prop control: Left/right joint + PWM independent
- Status cache update throttle: 100ms

#### **ESP32 Valve Controller** - `ESP32ValveController(QObject)` ~300 lines
- UDP-based (ports 8888/8889)
- ARP-based IP discovery with fallback (hardcoded 192.168.101.102)
- `UDPReceiveThread(QThread)` for non-blocking recv
- Valve position: 0-100% command → 0-1000 ESP32 (×10 multiplier)
- Feedback: 0-10000 ESP32 → 0-100% ROS (÷100)
- Keep-alive: Only resend if idle >1s
- CRC validation (polynomial 0x07, init 0xFF)

#### **Lidar Controller** - Simple (~100 lines)
- ROS2 subscriber: `/ef/lidar/wall_detection/distance` + `filtered_angle`
- Qt properties: `distance`, `angle` with changed signals

#### **Wind Monitor** - Minimal (~50 lines)
- ROS2 subscriber: `/wind/speed`, `/wind/direction` (Float32)
- Qt properties for QML binding

#### **System Monitor** - `SystemMonitor(QObject) + SystemMonitorWorker(QThread)` ~150 lines
- Battery level/remaining time via `acpi -b`
- CPU temperature from sysfs `/sys/class/thermal/`
- Worker thread: 1s polling interval
- Fallback methods for systems without acpi

#### **SSH Controller** - `UISSHController(QObject)` ~200 lines
- SSH launcher via paramiko (key or password auth)
- Ping-based device availability (0.5s timeout)
- QThreadPool for non-blocking network checks
- Device manager: Up to 10 remote systems

---

### 4. Services Layer (`python/paint_controller/services/`)

#### **Video Stream Handler** - `VideoStreamHandler(QObject)` ~300 lines
- **GStreamer Pipeline**: UDP RTP H264 → AVDec → RGB
- Multi-camera: End-effector, base-front, base-rear, base-top
- Thread-safe: `QMutex` per image provider
- `ImageProvider(QQuickImageProvider)`: Provides images to QML
- Ports: 5000 (EF), 5001 (base-front), 5002 (base-rear), 5003 (base-top)
- Copy-on-read to prevent external modification
- `start_all_streams()` is idempotent (`_streams_started` flag) with per-stream timing logs
- Startup deferred 200ms after QML load to avoid blocking first render

#### **Base Top View Service** - ~400 lines
- Fisheye correction for base camera (1920×1080 @ calibration)
- Parameters: k1=-0.389, k2=0.142 (distortion coefficients)
- Circle boundary: Center (966,540), radius 599 (2048×1080 basis)
- Output: Square 500×500 (dynamic scaling)
- Zoom/pan/rotation: Settings-driven
- Resolution scaling: Automatic if input differs from calibration

#### **Screen Manager** - `ScreenManager(QObject)` ~150 lines
- Real-time multi-display detection
- Qt signal integration: `screens_changed`, `screen_added`, `screen_removed`
- Polling: 1s interval for dynamic changes
- Properties per screen: Name, resolution, DPI, refresh rate, primary flag

#### **Screen Recorder** - ~100 lines
- Desktop capture via ffmpeg
- Configurable output path + codec

#### **ROS Bag Recorder** - ~50 lines
- Topic recording via rosbag2

#### **Workflow Runner** - New pattern
- Replaces legacy handler with improved error handling
- Explicit state tracking + QML-exposed properties

---

### 5. Models & UI Controllers (`python/paint_controller/models/`, `ui/`)

#### **OverlayController** - ~300 lines
- Dual joystick menu system (left/right/system)
- Index tracking for selection
- Auto-disable conflicting options (track controls can coexist)
- Temporary vs. committed selection states
- Yaw angle offset management

---

### 6. QML UI Layer (`python/paint_controller/qml/`) - 90 files

**Directory Structure**:
```
qml/
  core/               → ApplicationWindow, themes, styling
  navigation/         → SelectBar, TopBar (sidebars, headers)
  pages/              → Main content pages
    status/components → TeensyStatus, WheelStatus, etc.
    settings/pages    → Tab implementations
    settings/components → Reusable SettingInputField
  components/         → Core UI building blocks
    buttons/          → Various button styles
    inputs/           → Text inputs, sliders, spinboxes
    displays/         → Cards, gauges, monitors
    panels/           → Grouped UI sections
    specialized/      → VTK pointcloud container, video components
    popups/           → Message popups
  overlays/           → Fullscreen/modal dialogs
    systemcontrol/    → Settings, workflow, system menu (L4/R4 buttons)
    video/            → Video fullscreen + end-effector overlay with live stats
    video/components/ → Nested video controls, settings, topbar
    lidar/            → 3D lidar 2D/3D views
    EmergencyOverlay  → Hold-to-activate visual
    OverlayLayer      → Master coordinator
  widgets/
```

**Key QML Patterns** (from KNOWLEDGE.md):
- **Loader Timing**: Close popups 150ms before Loader source changes (scene graph conflicts)
- **Screen Access**: Use `screen.width`, not `screen.geometry.width`
- **Layout Children**: Never use `parent.width * 0.30` in ColumnLayout/RowLayout (use Layout.fillWidth + weight)
- **Button Keyboard**: Secondary windows get keyboard events leak → use `focusPolicy: Qt.ClickFocus` + `Keys.onPressed` reject
- **Signal-Based Bridge**: `MainWindow.qml` has `Connections { target: backend }` block receiving `showPopupRequested`, `closePopupRequested`, `toggleSidebarRequested`, `toggleVideoOverlayRequested`, `updateVideoSourceRequested`
- **NumpadButton**: Self-contained with explicit properties (no fragile `parent.parent.*` bindings)
- **Workflow Overlays**: Use `Layout.preferredWidth` weights instead of `parent.width * 0.X`

**CRITICAL Audit Finding (R11) — RESOLVED**: `CommonStyle.qml` is a `pragma Singleton` + `QtObject`. `Screen.pixelDensity` cannot work because `QtObject` has no parent Window. **Resolution**: `scaleFactor` defaults to `1.0` (runtime DPI injection was removed because `Screen.pixelDensity / 4.0` ≈ 2x on Steam Deck, doubling all shell sizes). Shell chrome uses fixed tokens (`shellTopBarHeight`, `shellSidebarExpandedWidth`, etc.) that are NOT scaled. Registered as singleton via `qmldir` in `qml/core/`.

**CommonStyle Token System** (~120 lines, `qml/core/CommonStyle.qml`):
- `scaleFactor` (writable, default 1.0) — drives all scale-dependent tokens
- **Colors**: 9 backgrounds, 3 cards, 3 accents, 4 status, 5 text, 2 borders, 10 overlay/input/button
- **Typography**: `fontSans`/`fontMono` families, 5 font sizes (display→label)
- **Spacing**: 6 levels (xs→xxl), all `Math.round(N * scaleFactor)`
- **Radii/Borders**: 3 radii, 2 border widths
- **Controls**: height/layout constants, motion durations
- **Shell Chrome**: 11 fixed tokens (not scaled) preserving Steam Deck baseline
- **Legacy Aliases**: 14 backward-compatible mappings to new tokens
- **Singleton registration**: `qml/core/qmldir` → `singleton CommonStyle 1.0 CommonStyle.qml`

**Multi-Monitor Architecture**:
- Main app: Secondary display (index 1 if available, otherwise primary)
- Industrial monitor: Always on primary (index 0) - shows LiDAR/status fullscreen
- Dynamic detection: ScreenManager polls every 1s

---

### 7. C++ Path (DELETED — Phase 1A)

- Source files deleted in Phase 1A: `src/*.cpp` (paint_controller, steam_deck_handler, steam_deck_test), `include/paint_controller/*.hpp`
- `CMakeLists.txt` is a pure `ament_cmake` wrapper for the Python package; had no C++ build targets when deleted
- `package.xml` does not list C++ dependencies (rclcpp, Qt5, GStreamer, HID)

---

### 8. Threading & Concurrency Model

**Main Qt Thread**:
- QML rendering, UI updates
- Signal/slot delivery
- Steam Deck button callbacks (debounced)
- Timer-based polling (200ms heartbeat, 100ms thrust ramp, etc.)

**ROS2 Thread** (`RosThread`):
- `rclpy.spin_once()` with 50ms timeout
- Decoupled from Qt event loop
- Detects network disconnections, recovers gracefully

**Worker Threads**:
- `SteamDeckReaderThread`: USB HID reads (10ms sleep per iteration)
- `UDPReceiveThread`: UDP valve status (socket timeout 100ms)
- `SystemMonitorWorker`: Battery/CPU polling (configurable interval, e.g., 1s)
- Workflow execution: `ActionWorker(QThread)` for service calls

**Thread Safety**:
- `QMutex` for image provider access (video frames)
- `threading.RLock()` for camera stream pipeline state
- ROS2 client/service calls: Direct (library handles thread safety)

---

## Data Flow & Signal Routing

### Input Loop (Steam Deck → Command)
```
SteamDeckHandler (USB HID) 
  ↓ [100Hz input_state_changed]
UIInputHandler (maps buttons to actions)
  ↓ [slots: on_up_pressed, on_switch_pressed, etc.]
StateStore / QtBridge / main() wiring
  ↓
ControlProcessor (processes joystick state)
  ↓ [publishes to ROS2 topics]
Teensy/Wheel/Winch controllers (command motors)
  ↓ [Status messages back]
Status callbacks update Qt properties
  ↓
QML display binding updates UI
```

### Video Stream Loop (RTP → QML Image)
```
GStreamer UDP pipeline (ports 5000-5003)
  ↓ [New sample]
ImageProvider (updates internal QImage, signals frameReady)
  ↓
QML Image (refreshes from image provider)
  ↓
BaseTopViewTransformer (CPU processing)
  ↓ [Settings/parameters from SettingsManager]
Output image
```

### Settings Change Loop
```
SettingsManager.setting_changed signal
  ↓
Subscribing handlers: Teensy, Wheel, Winch, ControlProcessor
  ↓ [e.g., winch_max_speed_mmps_changed signal]
Values update dynamically
  ↓
QML reflects new limits/values
```

---

## Critical Coupling Points

1. **`main()` + ControllerFactory → Everything**
  - Runtime composition is explicit now, but `application.py` still performs the final orchestration step
  - `create_controllers()` centralizes most constructor dependency wiring
  - This is a major improvement over the old god class, but it remains the main coordination hotspot

2. **SettingsManager → Hardware Controllers**
   - All controllers subscribe to setting_changed signals
   - Creates runtime parameter binding
   - Good separation (settings → dependent value)

3. **ControlProcessor ↔ OverlayController**
   - Joystick control modes selected in overlay
   - Control processor executes them
   - Tight but intentional coupling

4. **Steam Deck Handler ↔ Input Handler**
   - Button events → action handlers
   - Direct callback registration (loose coupling)

5. **QtBridge ↔ Main window root object**
  - Popup/sidebar/fullscreen operations are signal-based now and handled by QML `Connections {}`
  - The only remaining imperative access is `engine.rootObjects()[0]` for the multiscreen window path
  - This is narrower debt than the old `findChild()` bridge, but still worth keeping isolated

---

## Test Architecture

The repo now uses a layered test model instead of one generic mocking style for everything.

**Pure logic tests**
- `tests/test_crc.py`
- `tests/test_input_utils.py`
- `tests/test_settings_schema.py`

**Harness validation**
- `tests/test_test_infrastructure.py` validates the shared fake ROS/Qt primitives themselves

**Component and handler behavior**
- `tests/test_emergency.py` exercises `EmergencyButtonHandler` with explicit fake collaborators
- `tests/test_winch.py` exercises `WinchController` behavior with `FakeNode` and the shared fake topic bus

**Real ROS transport**
- `tests/test_winch_ros_integration.py` proves the published command reaches a real `rclpy` subscriber callback

**Local validation status**
- Current documented local result: targeted venv validation for the new core batch is green, while a full `python/paint_controller/venv/bin/python -m pytest tests -q` run still aborts in this terminal on the Qt application fixture path

---

## Performance Characteristics

**Display Update Rate**: 
- Heartbeat: 0.5s (2Hz)
- Control display: 200ms throttle (5Hz)
- Status UI: 100ms throttle (10Hz)
- Thrust ramp: 100ms timer (10Hz update)

**USB Input Polling**: 
- Steam Deck HID: 10ms sleep between reads (100Hz effective)
- Note: Reduced from 1ms per testing (100Hz + smoothing sufficient)

**ROS2 Spin**: 
- 50ms timeout per `spin_once()` call
- Watchdog: 5s timeout for network detection

**GStreamer Pipeline**:
- Real-time H264 decoding
- Thread-safe via mutex (tight coupling to QImage provider)

**Video Transforms**:
- Fisheye undistortion: Cached remap tables (computed once per resolution)
- Perspective transform: Per-frame computation (lightweight)
- Cropping/resizing: CPU-based, real-time

---

## Deployment

**Build & Run**:
```bash
cd ~/ros2_ws && colcon build --packages-select paint_interfaces paint_controller_ros2
paint_controller  # Entry point (__main__.py)
```

**Configuration Files**:
- `python/config/settings.json` (runtime)
- `python/config/base_top_view_camera.json` (fisheye calibration)
- `python/paint_controller/config/ssh_config.json` (remote device list)
- `python/paint_controller/config/bash_config.json` (launch scripts)

**ROS2 Topics** (Key):
- `/controller/heartbeat` (UInt8)
- `/base/heartbeat`, `/ef/heartbeat`
- `/vehicle/speed/cmd` (MoveVehicleSpd)
- `/winch/move/speed/mmps/cmd` (Float64)
- `/teensy/*` (20+ topics)
- `/valve/turn/cmd` (Float32)
- `valve/status` (ValveStatus)
