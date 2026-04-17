# Development Notes

---

### 2026-04-17 20:05 - Instrument Python Startup Lag And Fix Cross-Thread Cleanup

**Goal**: Identify the remaining post-render lag after the QML warning flood was removed, and stop Qt timer cleanup warnings during shutdown
**Issues**: Video streams were being started both from `application.py` and `PageHome.qml`, which re-ran synchronous GStreamer startup on the UI path; shutdown also spawned a Python cleanup thread that called `QObject`/`QTimer` cleanup from the wrong thread and produced `QObject::killTimer` warnings
**Tried**: Added elapsed-time startup/shutdown logs in `application.py`, deferred video startup with `QTimer.singleShot(200, ...)`, made `VideoStreamHandler.start_all_streams()` idempotent with per-stream timing logs, removed the `PageHome.qml` auto-start hook, and moved controller/service cleanup back onto the main Qt thread
**Result**: ✅ The code now emits concrete timing markers for the next run, avoids duplicate camera startup attempts, and should stop the known cross-thread timer shutdown warnings
**Files**: `core/application.py`, `services/video_stream.py`, `qml/pages/home/PageHome.qml`

### 2026-04-17 18:20 - Theme Token Rollout For Shared QML Surfaces

**Goal**: Start Phase 2 design-system work by replacing shell-level hardcoded styling with reusable QML tokens
**Issues**: `CommonStyle.qml` existed but was too small to be useful, the main shell used several unrelated palettes, and popup/overlay primitives still hardcoded colors, spacing, and typography
**Tried**: Expanded `CommonStyle.qml` into a writable scale-aware token surface, set `scaleFactor` from `MainWindow.qml` using `Screen.pixelDensity`, then migrated shared surfaces first instead of attempting all 90 QML files at once
**Result**: ✅ Main shell, shared overlays/popups, and reusable action/input controls now compile against one theme object; future page cleanup can mostly consume tokens instead of inventing new values
**Files**: `qml/core/CommonStyle.qml`, `qml/core/MainWindow.qml`, `qml/navigation/TopBar.qml`, `qml/navigation/SelectBar.qml`, `qml/overlays/OverlayLayer.qml`, `qml/overlays/EmergencyOverlay.qml`, `qml/components/popups/CustomPopup.qml`, `qml/components/buttons/ActionButton.qml`, `qml/components/buttons/TouchSwitch.qml`, `qml/components/inputs/SettingInputField.qml`, `qml/components/inputs/KeyboardPopup.qml`

### 2026-04-17 19:05 - Restore Steam Deck Shell Baseline After DPI Over-Scaling

**Goal**: Bring the top bar and side bar back to their original proportions after the theme token rollout inflated shell sizing
**Issues**: `Screen.pixelDensity / 4.0` is roughly 2x on the Steam Deck, so binding `CommonStyle.scaleFactor` to it doubled shell widths, heights, spacing, and typography
**Tried**: Removed runtime `scaleFactor` updates from `MainWindow.qml`, then split shell chrome onto fixed `CommonStyle` tokens (`shellTopBarHeight`, `shellSidebarExpandedWidth`, etc.) so the top bar, side bar, exit tile, and sidebar status text keep their original baseline regardless of future theme scaling
**Result**: ✅ Shell chrome now uses the theme system without auto-inflating the original Steam Deck layout, and future scale-factor work can happen without re-breaking the shell
**Files**: `qml/core/CommonStyle.qml`, `qml/core/MainWindow.qml`, `qml/navigation/TopBar.qml`, `qml/navigation/SelectBar.qml`, `qml/components/panels/ConnectionStatusPanel.qml`

### 2026-04-17 19:30 - Reduce Startup Freeze From QML Warning Flood

**Goal**: Remove the first-render QML warning churn that was stalling the UI for several seconds after startup
**Issues**: `NumpadButton.qml` depended on fragile `parent.parent.*` bindings, `EditWorkFlowTab.qml` and `WorkFlowTab.qml` used `parent.width * ...` inside layouts causing recursive rearrange warnings, and `PageHome.qml` had an `undefined` bool binding on the end-effector availability pulse
**Tried**: Made `NumpadButton.qml` self-contained with explicit properties, wrapped `NumpadNew.qml` instances in a styled local component that passes the popup palette/font values, replaced workflow overlay width math with layout-safe preferred-width weights, and guarded the end-effector animation `running` binding in `PageHome.qml`
**Result**: ✅ Removed the known startup warning hot paths most likely to block the UI thread during initial render
**Files**: `qml/components/buttons/NumpadButton.qml`, `qml/components/inputs/NumpadNew.qml`, `qml/pages/home/PageHome.qml`, `qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `qml/overlays/systemcontrol/WorkFlowTab.qml`

### 2026-04-17 17:10 - Fix QML Startup Type System Corruption

**Goal**: Restore UI startup after Phase 0 / singleton changes broke `paint_controller`
**Issues**: `QQmlApplicationEngine` fails with `Cannot assign object of type "QQuickRectangle" to list property "data"; expected "QObject"` — global QML type system corruption
**Tried**:
- ~~ToolTip / hover bubble theory~~ — WRONG. Error is not QML-side at all
- Headless isolation tests: all QML compiles fine WITHOUT `qmlRegisterSingletonInstance`
- Even a minimal `QObject` with a single `Property(str)` + `Signal()` triggers the crash when registered via `qmlRegisterSingletonInstance`
- `setContextProperty` works perfectly as replacement
**Root Cause**: `qmlRegisterSingletonInstance` corrupts PySide6's QML type system when combined with implicit directory imports (no `qmldir`). Known family of bugs: PYSIDE-2173, PYSIDE-2160, PYSIDE-2310. Our specific symptom (QQuickRectangle→data) appears unreported upstream.
**Result**: ✅ Replaced `qmlRegisterSingletonInstance` with `setContextProperty("stateStore", state_store)`. Updated 4 QML files: `StateStore.X` → `stateStore.X`, removed `import PaintController 1.0`.
**Files**: `application.py`, `TopBar.qml`, `PageWorkFlow.qml`, `ExecutorPageStatus.qml`, `PlannerPageStatus.qml`

### 2026-04-17 16:30 - Pytest Infrastructure Validation Gate

**Goal**: Complete Task 3.1 so future singleton and controller work has reusable Qt/ROS test scaffolding
**Issues**: VS Code kept selecting the wrong `.venv`, which hid `PySide6` and `pytest`; future tests also needed shared fake ROS primitives instead of per-test ad hoc stubs
**Tried**: Pinned workspace interpreter to `python/paint_controller/venv`, added `pytest-qt` and `pytest-cov`, built reusable fakes for logger/publisher/subscription/timer/node, and kept the namespace-only import bypass in `conftest.py`
**Result**: ✅ Added headless Qt fixture plus fake ROS test doubles, validated with a new infrastructure test, and full pytest now passes (29 tests)
**Files**: `.vscode/settings.json`, `requirements-dev.txt`, `tests/conftest.py`, `tests/fakes.py`, `tests/test_test_infrastructure.py`, `pytest.ini`, `setup.py`, `docs/plan/01_MASTER_PLAN.md`

### 2026-07-18 - Phase 3: Split RobotController God Class

**Goal**: Split ~970-line `RobotController(Node, QObject)` dual-inheritance class into focused components with explicit DI
**Issues**: Dual-inheritance (Node + QObject) prevented clean testing and separation of concerns. All controllers took `robot: RobotController` and accessed arbitrary attrs.
**Tried**: Strangler pattern — created new classes alongside old, rewired main(), kept old class as dead code for rollback.
**Result**: ✅ Created 4 new core files: `PaintRosNode(Node)`, `StateStore(QObject)`, `QtBridge(QObject)`, `ControllerFactory` with `ControllerBundle` dataclass. Rewrote `main()` to orchestrate. Updated 14 controller/handler/service constructors to take explicit deps. Updated 5 QML files (`backend.X` → `stateStore.X`). Fixed pre-existing dead `moveWinchIncrement()` QML call. +984/-367 lines across 22 files.
**Files**: `core/ros_node.py` (new), `core/state_store.py` (new), `core/qt_bridge.py` (new), `core/controller_factory.py` (new), `core/application.py` (main rewrite), 14 controller files, 5 QML files
**Commit**: `2cd0ae2` on `refactor/phase3-core-split`

---

### 2026-03-20 - B2: Teensy Status TypedDict + User-Field Bug Fix

**Goal**: Add type safety to Teensy status dict and fix data loss bug
**Issues**: `_status_callback()` created a new dict on every ROS message, overwriting user-controlled fields (relay_enabled, stability_enabled, auto_correction_enabled, roller_steering_enabled, swing_damping_enabled, spray_gun_leveling_enabled)
**Tried**: Considered dataclass (QML can't dot-access), custom container class (over-engineered). TypedDict gives IDE autocomplete with zero runtime change.
**Result**: ✅ Added `TeensyStatusDict(TypedDict)` for type hints, `_USER_CONTROLLED_FIELDS` tuple, and field preservation loop in `_status_callback`
**Files**: `controllers/teensy.py`

---

### 2026-07-17 - Phase 2 Refactoring: Thread Safety, Settings Auto-gen, Tests

**Goal**: Complete Phase 2 refactoring — thread safety, settings property boilerplate, test infra, config externalization
**Issues**:
- ESP32 socket could close while `recvfrom()` was active (race condition)
- `settings._values` and `teensy._status` had no thread synchronization
- ~195 lines of repetitive `@Property`/getter/setter boilerplate in settings.py
- Test imports triggered PySide6/ROS2 dependency chain via `__init__.py` re-exports
- ControlProcessor `_on_valve_turn_max_changed` missing scale propagation
**Tried**:
- `threading.Lock` for socket, settings values, teensy status — emit signals OUTSIDE lock
- `_make_setting_pair()` factory to auto-generate (Signal, Property) from schema — 1 line per setting
- Pre-register `paint_controller` as namespace-only module in conftest.py to bypass heavy imports
- MagicMock stubs for PySide6 → failed with `typing.ForwardRef` errors
**Result**: ✅ All completed: A1/A2/A3/B1/B2/B3/C1/C2 done. B2 implemented as TypedDict + user-field preservation bug fix (not dataclass — QML needs dict for `all_status`)
**Files**:
- `controllers/esp32_valve.py` — socket lock, QueuedConnection, JSON config loading
- `controllers/teensy.py` — status lock with atomic swap
- `core/settings.py` — values lock, `_SETTINGS_SCHEMA` at module level, `_make_setting_pair()` auto-gen (829→634 lines)
- `handlers/control_processor.py` — valve_turn scale fix, init extracted to 3 setup methods
- `python/config/esp32_valve.json` — externalized ESP32 MAC/IP/ports
- `tests/` — conftest.py, test_crc.py (8), test_input_utils.py (14), test_settings_schema.py (6) = 28 tests

---

### 2026-02-09 - Migrate Valve Control from Teensy to ESP32

**Goal**: Separate valve control from TeensyStatus, integrate ESP32 UDP valve controller directly into paint_controller
**Issues**: 
- Valve status embedded in TeensyStatus message - couples unrelated hardware
- Teensy topic `teensy/valve/turn/cmd` doesn't match actual ESP32 hardware
- Range confusion: ESP32 feedback is 0-10000 (0.01%), command is 0-1000 (0.1%)
**Tried**: 
- Created ESP32ValveController with UDP client (ports 8888/8889), ARP-based discovery
- Used QThread for non-blocking UDP receive to avoid blocking Qt event loop
- Implemented conditional keepalive (resend only if idle >1s)
**Result**: ✅ Valve control now independent, publishes to `valve/status` at 5Hz, subscribes to `valve/turn/cmd`

**Key Implementation**:
```python
# Command: 0-100% ROS → multiply by 10 → 0-1000 ESP32
position_raw = int(position_pct * 10.0)

# Feedback: 0-10000 ESP32 → divide by 100 → 0-100% ROS  
valve_position = valve_pos / 100.0
```

**Files**: 
- `controllers/esp32_valve.py` (new), `controllers/teensy.py` (removed valve code)
- `core/application.py`, `services/workflow/hardware.py`
- `handlers/control_processor.py`, `services/workflow/workflow_runner.py`
- `qml/components/displays/ValvesCard.qml`, `qml/overlays/video/components/EndEffectorOverlay.qml`

---

### 2026-02-05 17:30 - Fix Position Triggers Not Firing on Loop Iterations

**Goal**: Fix position-triggered actions not firing after first loop iteration
**Issues**: `close_valve` only fired on iteration 1, never on iterations 2+. Position triggers cleared but never rebuilt during loop restart.
**Tried**: Store all_scheduled actions in thread, rebuild _pending_position_triggers on each loop iteration
**Result**: ✅ Position triggers now properly reset and fire on every loop iteration

**Root Cause**: 
- `play()` separated position-triggered actions into `_pending_position_triggers`
- Loop restart cleared `_pending_position_triggers = []` 
- But never rebuilt the list from the original schedule
- Position triggers only worked on first iteration

**Fix**:
1. Store both `scheduled_actions` (time-based) and `all_scheduled` (complete list) in WorkFlowExecutionThread
2. On loop restart, rebuild `_pending_position_triggers` from `all_scheduled` by filtering `is_position_triggered`
3. This ensures position triggers are properly reset for each iteration

**Files**: workflow_executor.py

---

### 2026-02-05 17:00 - Industry-Pattern Workflow Completion (Implicit Dependencies)

**Goal**: Fix premature workflow completion when position triggers fire before reference actions finish
**Issues**: In `spray_cycle`, `close_valve` fires at 4200mm during `ascend` (2084→7542mm), finishes in 500ms, but `ascend` still has 15+ seconds remaining. Workflow incorrectly restarts loop while `ascend` is running.
**Tried**: Implemented industry-standard implicit dependency tracking - reference actions automatically marked as "must complete"
**Result**: ✅ Workflow now waits for all must-complete actions before finishing/looping

**Implementation (Industry Pattern 3)**:
1. **Scheduler**: Added `must_complete_before_workflow_end` flag to `ScheduledAction`
2. **Scheduler**: Automatically marks reference actions when building schedule (via `_mark_must_complete_actions()`)
3. **Executor**: Tracks must-complete actions in `_must_complete_actions` dict during execution
4. **Executor**: Waits for all must-complete actions via `_wait_for_must_complete_actions()` before workflow end
5. **Completion Logic**: Uses position-based completion for winch actions (within 50mm tolerance)

**Benefits**: Matches Kubernetes/Airflow patterns, no YAML changes needed, automatic and safe

**Files**: scheduler.py, workflow_executor.py

---

### 2026-02-05 15:45 - Add Workflow Loop Support

**Goal**: Enable workflows to loop back to first action after completion for continuous operation
**Issues**: None - feature addition
**Tried**: Added `loop: true` flag to YAML schema, implemented restart logic in execution thread
**Result**: ✅ Workflows with `loop: true` now restart automatically after completion

**Implementation**:
1. **Executor**: Added `_loop_enabled` flag and `_loop_iteration` counter
2. **Execution Loop**: Modified `_execute_scheduled_actions()` with outer loop that checks loop flag and restarts
3. **State Reset**: Clear position triggers, winch tracking, must-complete actions, and action index between iterations
4. **QML**: Added loop iteration display in WorkFlowStatusOverlay.qml
5. **Runner**: Exposed `is_loop_enabled` and `loop_iteration` properties to QML

**YAML Example**:
```yaml
name: spray_cycle
loop: true  # Optional flag at root level
actions: [...]
```

**Files**: workflow_executor.py, workflow_runner.py, WorkFlowStatusOverlay.qml, spray_cycle.yaml
4. **QML Exposure**: Added `is_loop_enabled` and `loop_iteration` properties to WorkFlowRunner
5. **UI Display**: WorkFlowStatusOverlay shows gold loop iteration indicator when looping

**Files**: 
- workflow_executor.py (loop logic, state tracking)
- workflow_runner.py (QML properties, loop_iteration_changed signal)
- WorkFlowStatusOverlay.qml (loop iteration display)
- spray_cycle.yaml (example with `loop: true`)

**Usage**: Add `loop: true` at root level of workflow YAML. Iteration count starts at 1, increments each cycle.

---

### 2026-02-05 10:30 - Fix QML Import Paths After Structure Reorganization

**Goal**: Fix broken QML component imports after directory structure reorganization
**Issues**: Components in `pages/status/components/` and `overlays/video/components/` using outdated relative paths that don't resolve correctly; PageWorkFlow importing from wrong location
**Tried**: Updated relative paths to account for additional nesting level in all affected subdirectories
**Result**: ✅ Fixed import paths in status components (TeensyStatus, WheelStatus), video overlay components (EndEffectorOverlay, BirdViewSettingsPopup, VideoOverlayTopBar), and PageWorkFlow

**Root Cause**:
After moving components into subdirectories (`pages/status/` → `pages/status/components/`, `overlays/video/overlays/` → `overlays/video/components/`), files were one level deeper but imports still used `../../` instead of `../../../`. PageWorkFlow was importing `../status` instead of `../status/components/`.

**Solution**:
- Status components: `../../core` → `../../../core`, `../../components/*` → `../../../components/*`
- Video overlay components: `../../components/*` → `../../../components/*`
- PageWorkFlow.qml: `../status` → `../status/components`

**Files**: TeensyStatus.qml, WheelStatus.qml, EndEffectorOverlay.qml, BirdViewSettingsPopup.qml, VideoOverlayTopBar.qml, PageWorkFlow.qml

---

### 2026-02-05 00:45 - QML Structure Reorganization

**Goal**: Reorganize 91 QML files into clearer directory structure with better separation of concerns
**Issues**: Confusing nested directories (overlays/video/overlays/), mixed pages and components in same directories, unclear naming (Page5.qml), complex relative import paths requiring depth awareness
**Tried**: Systematic reorganization with git mv to preserve file history, updated all import paths
**Result**: ✅ Flattened video overlay structure, separated settings/status pages from components, reduced import complexity from `../../../` to `../../` paths

**Changes Made**:
1. **Video overlays**: `overlays/video/overlays/` → `overlays/video/components/` (9 files)
2. **Settings**: Split into `pages/settings/pages/` (5 files) and `pages/settings/components/` (5 files)
3. **Status**: Moved components to `pages/status/components/` (4 files)
4. **Renamed**: `Page5.qml` → `PageSensors.qml` (descriptive name for Wind/Lidar visualization)

**Import Path Updates**:
- Video overlay components: `../../../components/` → `../../components/`
- Settings pages: `import "."` → `import "../components"`
- Settings main: `import "."` → `import "pages"`
- Status main: `import "."` → `import "components"`

**Files**: 24 files moved, 11 import statements updated across VideoFullscreenOverlay.qml, PageSettings.qml, PageStatus.qml, and all moved component files

---

### 2026-02-04 14:45 - Fix Multi-Monitor Crash on A Button Press

**Goal**: Prevent application crash when pressing A button (wheel travel command) in multi-monitor mode
**Issues**: A button triggered emergency shutdown only when secondary display (MultiScreenListUI) was active. App exited via Qt.quit() unexpectedly.
**Tried**: Added extensive debug logging to trace event flow
**Result**: ✅ Keyboard events from main window were triggering EXIT button on secondary display. Fixed by disabling keyboard focus on EXIT button.

**Root Cause**:
Qt Buttons accept keyboard activation (Space/Enter) when focused. In multi-monitor setup, keyboard events from Steam Deck controller leaked across windows, causing the EXIT button in MonitorHeader (secondary display) to be triggered by the A button press.

**Evidence from debug logs**:
```
[DEBUG] EXIT BUTTON CLICKED IN MONITOR HEADER!
[DEBUG] EXIT TIMER TRIGGERED - CALLING Qt.quit()!
```

**Solution**:
1. **MonitorHeader.qml EXIT button**:
   - Added `focusPolicy: Qt.NoFocus` to prevent keyboard focus
   - Added `activeFocusOnTab: false` to prevent Tab navigation
   - Added `Keys.onPressed` handler that rejects all keyboard events
   - Button now only responds to actual mouse clicks

2. **MultiScreenListUI.qml debugging**:
   - Added focused Item to log keyboard events reaching secondary window
   - Helps diagnose future cross-window event issues

**Files**: 
- `qml/components/displays/MonitorHeader.qml` (EXIT button keyboard blocking)
- `qml/overlays/MultiScreenListUI.qml` (keyboard event debugging)

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