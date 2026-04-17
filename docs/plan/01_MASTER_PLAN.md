# Paint Controller PySide6/QML Modernization — Validated Master Plan

> **Created**: 2026-04-16
> **Validated**: 2026-04-16 (survived Technical Auditor + Systems Architect pre-mortem)
> **Status**: IN PROGRESS
> **Branch**: `refactor` (create sub-branches per phase)

---

## ⚠️ INSTRUCTIONS FOR FUTURE LLM SESSIONS

1. **Read `00_README.md`** for file reading order
2. **Read this file** for the task list and progress tracker
3. **Read `KNOWLEDGE.md`** in repo root for Qt/Python gotchas
4. **Use the Current Checkpoint + Dependency Graph**, not row order alone, to choose the next task
5. **After completing a task**: Mark it `[x]`, update "Last Modified", note deviations
6. **If a task fails or scope changes**: Document in Notes column
7. **Always verify** — run the verification steps listed per task
8. **After modifying ANY QML**: Test the affected page/overlay manually
9. **NEVER use `qmlRegisterSingletonInstance()`** in PySide6 — it corrupts the QML type system. Use `setContextProperty()` instead. See KNOWLEDGE.md.

**All Python paths below are relative to**: `python/paint_controller/`
**All QML paths below are relative to**: `python/paint_controller/qml/`

---

## Progress Tracker

Last Modified: 2026-04-17

| Task | Status | Notes |
|------|--------|-------|
| 0.1 Delete RobotController | [x] | RobotController + duplicate HeartbeatStatus removed; RobotConfig/ConfigLoader retained because `main()` still uses config loading |
| 0.2 Type ControllerBundle | [x] | Concrete types added; imports moved to module scope |
| 0.3 Remove aliases + fix bugs | [x] | C++ path formally deprecated; `baseStreamer`/`videoStreamer` removed; overlay slot returns list |
| 0.4 Winch safety + ScreenManager | [x] | Re-enabled 4 winch safety checks; ScreenManager now takes `node` in constructor |
| PRE-1 Machine-verify QML mapping | [x] | Mapping table refreshed to live identifiers; lowercase `stateStore` and aliases removed |
| 1.0 Register StateStore | [x] | `StateStore` exposed via `setContextProperty`. `qmlRegisterSingletonInstance` abandoned (PySide6 bug — see KNOWLEDGE.md) |
| 1.1 Register SettingsManager | [ ] | |
| 1.2 Register QtBridge + kill findChild | [x] | All `findChild` replaced with signals (`showPopupRequested`, `closePopupRequested`, `toggleSidebarRequested`, `toggleVideoOverlayRequested`, `updateVideoSourceRequested`). `input.py` uses `close_popup_fn` callable. `QmlObjectName` enum deleted. `objectName` removed from popup/selectBar/videoOverlay. Only remaining QML object access: `engine.rootObjects()[0]` in `toggle_multiscreen_window()`. |
| 1.3 Register isolated controllers | [ ] | |
| 1.4 Register wheelController | [ ] | 7 QML files |
| 1.5 Register teensyController | [ ] | 7 QML files |
| 1.6 Register winchController | [ ] | 11 QML files — highest spread |
| 1.7a Register controllers batch A | [ ] | ESP32, Lidar, SSH, Video, BaseTopView |
| 1.7b Register controllers batch B | [ ] | Recorder, Overlay, Action, Steam |
| 1.8 Register workflow handlers | [ ] | |
| 1.10 Qt6 versionless imports | [ ] | **DO BEFORE 1.9** |
| 1.9 Add qmldir manifests | [ ] | No bare `module PaintController` |
| 1.11a required props — buttons | [ ] | After ALL 1.0-1.8 AND 1.9 |
| 1.11b required props — inputs | [ ] | |
| 1.11c required props — displays | [ ] | |
| 1.11d required props — panels/popups | [ ] | |
| 1.11e required props — widgets | [ ] | |
| POST-1 Startup context property validation | [x] | Validation loop in `application.py` checks all 25 context properties for `None` after `engine.load()` |
| 2.0 Expand CommonStyle | [x] | Token-based design system with scales, colors, spacing, typography, motion, and fixed shell tokens. `scaleFactor` defaults to 1.0 (runtime DPI removed — caused 2x on Steam Deck). `qmldir` singleton added. |
| 2.1 Design system — core/nav | [x] | `MainWindow`, `TopBar`, `SelectBar` migrated. Shell chrome uses fixed tokens. |
| 2.2 Design system — buttons/inputs | [x] | `ActionButton`, `TouchSwitch`, `NumpadButton`, `NumpadNew`, `KeyboardPopup`, `SettingInputField`, `TrajNumpad` migrated |
| 2.3 Design system — displays | [ ] | |
| 2.4 Design system — panels/popups | [x] | `ControlPanel`, `ConnectionStatusPanel`, `SettingsSection`, `CustomPopup` migrated |
| 2.5a Design system — root overlays | [x] | `OverlayLayer`, `EmergencyOverlay` migrated |
| 2.5b Design system — systemcontrol | [~] | `EditWorkFlowTab`, `WorkFlowTab` migrated (layout-safe weights); `CommandTab` anchor fix. Remaining tabs not yet themed. |
| 2.5c Design system — video overlays | [ ] | |
| 2.6a Design system — pages batch 1 | [~] | `PageHome` — removed duplicate stream start, guarded animation binding. Other pages not yet themed. |
| 2.6b Design system — settings pages | [ ] | |
| 2.6c Design system — status/workflow | [ ] | |
| 2.7 Refactor OverlayLayer dedup | [ ] | |
| 2.8 Fix page naming | [ ] | |
| 3.0 Clean __init__.py imports | [ ] | |
| 3.1 Pytest infrastructure | [x] | Added headless Qt fixture, fake ROS node/publisher/subscription/timer scaffolding, and validation test |
| 3.2 Tests — StateStore/Settings | [ ] | |
| 3.3 Tests — QtBridge/Factory | [ ] | |
| 3.4 Tests — Emergency/ControlProc | [ ] | |
| 3.5 Tests — Input/SteamDeck | [ ] | |
| 3.6 Tests — Wheel/Winch | [ ] | |
| 3.7 Tests — ESP32/Teensy | [ ] | |
| 3.8 CI/CD pipeline | [x] | `.github/workflows/ci.yml`: lint → test → ROS2 build. `pyproject.toml` with ruff/pytest/coverage config. `requirements-dev.txt` updated. |
| 3.9 Fix build system | [x] | `CMakeLists.txt` stripped to pure `ament_cmake` wrapper (C++/Qt5/GStreamer deps removed). `package.xml` cleaned to 0.1.0, C++ deps removed. `requirements.txt` switched to `~=` pins. |

## Current Checkpoint

- Completed on 2026-04-17: Phase 0 (`0.1-0.4`), `PRE-1`, `1.0`, `1.2`, `POST-1`, `3.1`, `3.8`, `3.9`
- Phase 2 in progress: `2.0`, `2.1`, `2.2`, `2.4`, `2.5a` complete; `2.5b` and `2.6a` partially complete
- Startup optimization done: deferred video, idempotent streams, timing instrumentation, cross-thread cleanup fix
- QML warning fixes done: NumpadButton self-contained, layout-safe workflow tabs, PageHome animation guard, lidar unused Connections removed
- Validation gate satisfied: CI + build system both done
- **Next task**: `1.1 Register SettingsManager` (resume Phase 1 controller migrations)

---

## Dependency Graph

```
Phase 0: 0.1 → 0.2 → 0.3    (0.4 parallel with 0.2/0.3)
         ↓
Phase 1: PRE-1 — Machine-verify QML mapping table
         ↓
         1.0 (StateStore — establishes pattern)
         ↓
Validation Gate: 3.1 (pytest infrastructure) + 3.8 (CI pipeline)
         ↓
Phase 1 continued: 1.1, 1.2, 1.3 (can parallel after 1.0)
         ↓
         1.4 → 1.5 → 1.6 → 1.7a → 1.7b → 1.8 (controllers, sequential)
         ↓
         1.10 (versionless imports — BEFORE 1.9)
         ↓
         1.9 (qmldir manifests — after all registrations + versionless)
         ↓
         1.11a-e (required props — after ALL 1.0-1.8 AND 1.9)
         ↓
         POST-1 — Startup context property validation
         ↓
Phase 2: 2.0 (DPI via Python injection) → 2.1-2.6 (sequential by batch)
         2.7, 2.8 (independent, anytime)
         ↓
Phase 3 (remaining): 3.0 → 3.2-3.7 (parallel test writing)
         3.9 (independent, anytime)
```

---

## Risk Map

| Task | Risk | Why |
|------|------|-----|
| 1.0 StateStore | LOW | 4 QML files, establishes pattern |
| 1.1 SettingsManager | LOW | 3 QML files |
| 1.2 QtBridge + findChild | ~~HIGH~~ | ✅ DONE — Signal replacement + input.py scope + MainWindow changes |
| 1.3 Isolated controllers (6) | MEDIUM | 6 registrations, 1-3 files each |
| 1.4 wheelController | MEDIUM | 7 QML files |
| 1.5 teensyController | MEDIUM | 7 QML files |
| 1.6 winchController | **HIGH** | 11 QML files, highest spread |
| 1.7a controllers batch A | MEDIUM | 5 registrations, moderate QML changes |
| 1.7b controllers batch B | MEDIUM | 5 registrations |
| 1.8 Workflow handlers | MEDIUM | 5 QML files |
| 1.10 Versionless imports | LOW | Mechanical sed replace |
| 1.9 qmldir manifests | **HIGH** | ~20 new files, module naming critical |
| 1.11a-e Required props | MEDIUM | Each `required` is breaking if caller misses it |
| 2.0 Expand CommonStyle | ~~MEDIUM~~ | ✅ DONE — DPI approach resolved (fixed scaleFactor at 1.0) |

---

## Reference Patterns

### Context Property Pattern (CURRENT — all 25 objects use this)
```python
# In application.py main(), AFTER engine creation, BEFORE engine.load()
ctx = engine.rootContext()
ctx.setContextProperty("wheelController", bundle.wheel_controller)
# QML accesses as global: wheelController.left_wheel_speed
```

> **⚠️ DO NOT use `qmlRegisterSingletonInstance()`** — broken in PySide6 with implicit directory imports. See KNOWLEDGE.md.

### QML Access Pattern
```qml
// Context property — available globally, lowercase instance name
wheelController.left_wheel_speed
```

### Signal-Based Bridge Pattern (IMPLEMENTED — Task 1.2 ✅)
```python
# In qt_bridge.py — signals (live code)
class QtBridge(QObject):
    showPopupRequested = Signal(str, str, str, int)      # title, message, type, delay
    closePopupRequested = Signal()                        # for input.py
    toggleSidebarRequested = Signal()                     # sidebar toggle
    toggleVideoOverlayRequested = Signal(bool, str)       # active, videoSource
    updateVideoSourceRequested = Signal(str)              # videoSource

    def show_popup(self, title, msg, msg_type="info", delay=0):
        self.showPopupRequested.emit(title, msg, msg_type, delay)

    def close_popup(self):
        self.closePopupRequested.emit()
```
```qml
// In MainWindow.qml — Connections block (live code)
Connections {
    target: backend  // context property
    function onShowPopupRequested(title, message, popupType, delay) { ... }
    function onClosePopupRequested() { messagePopup.close() }
    function onToggleSidebarRequested() { selectBar.toggleSidebar() }
    function onToggleVideoOverlayRequested(active, videoSource) { ... }
    function onUpdateVideoSourceRequested(videoSource) { ... }
}
```

### CommonStyle Current State (IMPLEMENTED — Task 2.0 ✅)
```qml
pragma Singleton
import QtQuick 2.15
QtObject {
    property real scaleFactor: 1.0  // drives scale-dependent tokens

    // Colors (37 tokens): backgrounds, cards, accents, status, text, borders, overlay/input/button
    readonly property color backgroundL0: "#0D1117"
    readonly property color accentPrimary: "#58A6FF"
    // ... (see qml/core/CommonStyle.qml for full list)

    // Spacing (scaled): spacingXs(4) through spacingXxl(32)
    // Typography: fontDisplay(24), fontHeading(20), fontBody(16), fontCaption(13), fontLabel(11)
    // Shell chrome (fixed): shellTopBarHeight, shellSidebarExpandedWidth, etc.
    // Legacy aliases (14): backward-compat mappings to new tokens
}
```
Registered via `qml/core/qmldir`: `singleton CommonStyle 1.0 CommonStyle.qml`

### QML Import Current Style (to be modernized in Task 1.10)
```qml
import QtQuick 2.15        // → import QtQuick
import QtQuick.Controls 2.15  // → import QtQuick.Controls
import QtQuick.Layouts 1.15   // → import QtQuick.Layouts
import "../pages/home"         // → stays or becomes module import after qmldir
```

---

## Runtime Identifier → QML File Mapping

Used for Phase 1 tasks. Shows which QML files must be updated per controller registration.

> **IMPORTANT (Audit R10)**: Before continuing Phase 1, run `for prop in StateStore settingsManager backend overlayController workFlowHandler workFlowRunner warningHandler baseStreamHandler wheelController winchController steamDeckHandler windMonitor teensyController esp32ValveController lidarController actionConfig heartbeatHandler controlProcessor sshHandler systemMonitor screenRecorder rosBagRecorder screenManager baseTopViewController; do echo "==$prop=="; grep -rl "$prop" qml/; done` and compare against this table. Fix any discrepancies.

| Identifier | QML Files That Reference It |
|---|---|
| `backend` | EmergencyOverlay, PageSpray, MainSettingsPage |
| `StateStore` | TopBar, PageWorkFlow, ExecutorPageStatus, PlannerPageStatus |
| `overlayController` | MainWindow, MultiScreenListUI, SystemControlMenu |
| `workFlowHandler` | SequenceList, WorkFlowControl, PageWorkFlow |
| `workFlowRunner` | WorkFlowTab, EditWorkFlowTab, WorkFlowStatusOverlay |
| `warningHandler` | TopBar |
| `baseStreamHandler` | PageWheel, PageHome, VideoFullscreenOverlay, DeviceControlTab, PageWorkFlow |
| `wheelController` | PageWheel, BaseFrontOverlay, WheelsCard, DeviceControlTab, ConnectionStatusPanel, ExecutorPageStatus, PlannerPageStatus, WheelStatus |
| `winchController` | PageWinch, PageStatus, EndEffectorOverlay, VideoOverlayTopBar, WinchCard, ConnectionStatusPanel, DeviceControlTab, CommandTab, MoveLengthButton, PlannerPageStatus, ExecutorPageStatus |
| `steamDeckHandler` | *(no QML refs — Python-only, still register for consistency)* |
| `windMonitor` | PageSensors |
| `teensyController` | PageTuning, EndEffectorOverlay, VideoOverlayTopBar, SettingsTab, TeensyArmCard, IMUCard, MonitorHeader, ConnectionStatusPanel, CommandTab, DeviceControlTab, ExecutorPageStatus, PlannerPageStatus, TeensyStatus |
| `esp32ValveController` | EndEffectorOverlay, ValvesCard |
| `lidarController` | LidarOverlay, Lidar2DView, Lidar3DView, WallDetectionOverlay, PageMonitor |
| `actionConfig` | ActionSequence, ActionItem, PageWorkFlow |
| `heartbeatHandler` | ConnectionStatusPanel, DeviceControlTab, PageHome |
| `controlProcessor` | VideoFullscreenOverlay |
| `sshHandler` | PageHome, PageLauncher, VideoOverlayTopBar |
| `systemMonitor` | VideoOverlayTopBar |
| `screenRecorder` | VideoOverlayTopBar, DeviceControlTab |
| `rosBagRecorder` | DeviceControlTab |
| `settingsManager` | SettingsTab, SettingsSection, SettingInputField |
| `screenManager` | MainWindow |
| `baseTopViewController` | BaseTopViewSettingsPopup, BaseFrontOverlay |

**Hotspot files** (touch many properties — will be edited repeatedly):
- `DeviceControlTab.qml` — 7 properties
- `VideoOverlayTopBar.qml` — 5 properties
- `EndEffectorOverlay.qml` — 4 properties
- `ConnectionStatusPanel.qml` — 3 properties
- `PageHome.qml` — 3 properties

---

## Phase 0: Foundation Cleanup

### Task 0.1: Delete Dead RobotController Class

**Goal**: Remove ~525 lines of dead code from `core/application.py`.

**Implementation note (2026-04-17)**: `RobotConfig` and `ConfigLoader` were retained because `main()` still uses `ConfigLoader.load_config('robot_config.yaml')` during startup.

**Context**: The old `RobotController(Node, QObject)` god class was replaced by `PaintRosNode`, `StateStore`, `QtBridge`, `ControllerFactory` in the previous refactor. The new `main()` function never instantiates it. Confirmed dead code — zero runtime references. Verified: no external references in `launch/`, `tests/`, `scripts/`, or `fish-eye/`.

**Files to modify**:
- `core/application.py` — Delete the `RobotController` class (starts around L221, ends around L746). Also delete the `HeartbeatStatus` enum near L85 (duplicate of the one in `core/ros_node.py`). Also delete `RobotConfig` and `ConfigLoader` classes if they exist and are unused.
- `core/__init__.py` — Remove `RobotController` from imports/exports
- `__init__.py` (package root) — Remove `RobotController`, `RobotConfig`, `ConfigLoader` from the backward-compat re-export layer

**How to find the code**:
```bash
grep -n "class RobotController" core/application.py
grep -n "class HeartbeatStatus" core/application.py
grep -n "RobotController" core/__init__.py __init__.py
```

**Verification**:
- `grep -rn "RobotController" python/paint_controller/ --include="*.py"` → only comments/docstrings, no imports
- `python -c "from paint_controller.core.application import main"` → no error
- App launches: `paint_controller`
- Existing tests pass: `pytest tests/`

---

### Task 0.2: Type ControllerBundle + Clean Factory Imports

**Goal**: Replace all `object` fields in `ControllerBundle` dataclass with concrete types.

**Files to modify**:
- `core/controller_factory.py` — Only file

**What to do**:
1. Move all deferred imports (inside `create_controllers()`, around L84-103) to module-level. These are redundant — no circular import risk.
2. Replace every `field: object` in the `ControllerBundle` dataclass (L13-38) with the concrete type. Example: `wheel_controller: object` → `wheel_controller: WheelController`.
3. `cleanup()` method: Verified OK as-is — `warning_handler` and `action_config` are correctly omitted (neither has a `cleanup()` method).

**Verification**:
- App launches
- `mypy core/controller_factory.py` (if available) — no type errors

---

### Task 0.3: Remove Context Property Aliases + Fix Minor Bugs

**Goal**: Remove 2 redundant `setContextProperty` aliases and fix a slot return type bug.

> **C++ Deprecation Notice (Audit R2)**: The C++ binary (`paint_controller_cpp`) shares the same QML files and sets `baseStreamer`/`backend` context properties. It is formally deprecated. Do NOT update `paint_controller.cpp` during modernization. The C++ path only sets 2 of 26 context properties and is already non-functional for full UI. QML changes will break it; this is acceptable.

**Files to modify**:
- `core/application.py` — Remove these 2 lines from the context property block (~L868-895):
  - `ctx.setContextProperty("baseStreamer", qt_bridge)` (alias of `backend`)
  - `ctx.setContextProperty("videoStreamer", video_stream_handler)` (alias of `baseStreamHandler`)
- `qml/pages/spray/PageSpray.qml` — Find `baseStreamer` references, replace with `backend`
- `qml/overlays/systemcontrol/DeviceControlTab.qml` — Find `videoStreamer` references, replace with `baseStreamHandler`
- `ui/overlay.py` — Find `@Slot(result=tuple)` and change to `@Slot(result=list)` (tuple is not a QML metatype)

**How to find references**:
```bash
grep -rn "baseStreamer" qml/
grep -rn "videoStreamer" qml/
grep -n "result=tuple" ui/overlay.py
```

**Verification**:
- PageSpray loads correctly
- DeviceControlTab loads correctly
- `grep -rn "baseStreamer\|videoStreamer" python/` → zero hits in Python
- `grep -rn "baseStreamer\|videoStreamer" qml/` → zero hits in QML

---

### Task 0.4: Winch Safety Checks + ScreenManager Constructor

**Goal**: Re-enable commented-out safety code and fix a monkey-patched constructor.

**Files to modify**:
- `controllers/winch.py` — Re-enable the 4 commented-out availability checks in `move_increment()`, `move_increment_with_accel()`, `move_absolute()`, `move_absolute_with_accel()` (around L168-L216). Replace `print()` with `self._node.get_logger().warning()`. Return `False` when not available. This matches the pattern already used in `command_speed_rpm()` and `command_speed_mmps()`.
- `services/screen_manager.py` — Add `node` (or `logger`) as an `__init__` parameter instead of it being monkey-patched later.
- `core/application.py` — Find `bundle.screen_manager.node = node` (around L841) and replace with passing `node` to constructor.

**How to find the code**:
```bash
grep -n "# if not self" controllers/winch.py
grep -n "\.node = " core/application.py
```

**Verification**:
- Winch page loads, winch commands work (if hardware available)
- Screen detection works on app startup
- Multi-monitor switching works

---

## Phase 1: QML Module System

### Task PRE-1: Machine-Verify QML Mapping Table

**PREREQUISITE — Do this before ANY Phase 1 task.**

**Goal**: Generate a fresh mapping of runtime identifiers to QML files and compare against the table above. Fix discrepancies.

**Script**:
```bash
cd python/paint_controller
for prop in StateStore settingsManager backend overlayController workFlowHandler workFlowRunner \
  warningHandler baseStreamHandler wheelController winchController steamDeckHandler windMonitor \
  teensyController esp32ValveController lidarController actionConfig heartbeatHandler \
  controlProcessor sshHandler systemMonitor screenRecorder rosBagRecorder screenManager \
  baseTopViewController; do
  echo "==$prop=="
  grep -rl "$prop" qml/ 2>/dev/null | sort
done
```

**Action**: Compare output against the mapping table. If any file appears that's not listed, add it. If a listed file doesn't appear, verify the property name is spelled correctly in QML.

---

### Task 1.0: Register StateStore (COMPLETED)

**Goal**: Expose `StateStore` to QML via `setContextProperty`. This defines the reference implementation.

**Status**: ✅ DONE. Originally attempted with `qmlRegisterSingletonInstance` but that API is broken in PySide6 (corrupts QML type system with implicit directory imports). Reverted to `setContextProperty`.

**Python changes**:
- `core/application.py` — Uses `ctx.setContextProperty("stateStore", state_store)` (already existed, kept as-is)

**QML files** (4 files): Access via `stateStore.xyz` (lowercase, no import needed)
- `navigation/TopBar.qml`
- `pages/workflow/PageWorkFlow.qml`
- `pages/status/components/ExecutorPageStatus.qml`
- `pages/status/components/PlannerPageStatus.qml`

---

### Task 1.1: Register SettingsManager

**Same setContextProperty pattern. Already exposed — verify QML access works.**

**Python**: `core/settings.py` + `core/application.py`
**QML** (3 files): `overlays/systemcontrol/SettingsTab.qml`, `components/panels/SettingsSection.qml`, `components/inputs/SettingInputField.qml`

Access via `settingsManager.xyz` (lowercase, no import needed).

**Verification**: Settings page loads. Changing a setting value persists and is reflected in UI.

---

### Task 1.2: Register QtBridge + Eliminate findChild() (COMPLETED)

**Goal**: Two-part task — register QtBridge as singleton AND replace all findChild() calls with signal-based communication.

**Status**: ✅ DONE. All 5 `findChild` calls replaced with signal-based communication. `QmlObjectName` enum deleted. `objectName` removed from `messagePopup`, `selectBar`, `videoFullscreenOverlay`.

**Signals implemented in `qt_bridge.py`**:
- `showPopupRequested(str, str, str, int)` — title, message, type, delay
- `closePopupRequested()` — for input.py close-before-mode-switch
- `toggleSidebarRequested()` — sidebar toggle
- `toggleVideoOverlayRequested(bool, str)` — active, videoSource
- `updateVideoSourceRequested(str)` — update video source

**QML-side**: `Connections { target: backend }` block in `MainWindow.qml` receives all signals.

**input.py**: Uses `close_popup_fn` callable (injected via `create_controllers()` → `qt_bridge.close_popup`).

**Only remaining QML object access**: `engine.rootObjects()[0]` in `toggle_multiscreen_window()` via `QMetaObject.invokeMethod`.

---

### Task 1.3: Register Isolated Controllers (Batch)

**Goal**: Register 6 controllers that each have ≤3 QML references.

| Python File | Register As | QML Files |
|---|---|---|
| `controllers/wind_monitor.py` | `WindMonitor` | PageSensors |
| `services/screen_manager.py` | `ScreenManager` | MainWindow |
| `handlers/control_processor.py` | `ControlProcessor` | VideoFullscreenOverlay |
| `handlers/warnings.py` | `WarningHandler` | TopBar |
| `handlers/heartbeat.py` | `HeartbeatHandler` | ConnectionStatusPanel, DeviceControlTab, PageHome |
| `controllers/system_monitor.py` | `SystemMonitor` | VideoOverlayTopBar |

**For each**: Register in `application.py`, update QML files to `import PaintController` + PascalCase name.

**Verification**: Each affected page/overlay loads. Remove 6 `setContextProperty` lines.

---

### Task 1.4: Register wheelController (7 QML files)

**Python**: `controllers/wheel.py` → register as `WheelController`
**QML files to update**:
1. `pages/wheel/PageWheel.qml`
2. `overlays/video/components/BaseFrontOverlay.qml`
3. `components/displays/WheelsCard.qml`
4. `overlays/systemcontrol/DeviceControlTab.qml`
5. `components/panels/ConnectionStatusPanel.qml`
6. `pages/status/components/ExecutorPageStatus.qml`
7. `pages/status/components/PlannerPageStatus.qml`

In each: add `import PaintController` (if not already present), change `wheelController.xyz` → `WheelController.xyz`.

---

### Task 1.5: Register teensyController (7 QML files)

**Python**: `controllers/teensy.py` → register as `TeensyController`
**QML files to update**:
1. `pages/tuning/PageTuning.qml`
2. `overlays/video/components/EndEffectorOverlay.qml`
3. `overlays/video/components/VideoOverlayTopBar.qml`
4. `overlays/systemcontrol/SettingsTab.qml`
5. `components/displays/TeensyArmCard.qml`
6. `components/displays/IMUCard.qml`
7. `components/displays/MonitorHeader.qml`

---

### Task 1.6: Register winchController (11 QML files)

**Python**: `controllers/winch.py` → register as `WinchController`
**QML files to update**:
1. `pages/winch/PageWinch.qml`
2. `pages/status/PageStatus.qml`
3. `overlays/video/components/EndEffectorOverlay.qml`
4. `overlays/video/components/VideoOverlayTopBar.qml`
5. `components/displays/WinchCard.qml`
6. `components/panels/ConnectionStatusPanel.qml`
7. `overlays/systemcontrol/DeviceControlTab.qml`
8. `overlays/systemcontrol/CommandTab.qml`
9. `components/buttons/MoveLengthButton.qml`
10. `pages/status/components/PlannerPageStatus.qml`
11. `pages/status/components/ExecutorPageStatus.qml`

**CAUTION**: Highest spread. Some files may already have `import PaintController` from earlier tasks. Only add the import if not already present.

---

### Task 1.7a: Register Controllers Batch A (5 controllers)

| Python File | Register As | QML Files |
|---|---|---|
| `controllers/esp32_valve.py` | `ESP32ValveController` | EndEffectorOverlay, ValvesCard |
| `controllers/lidar.py` | `LidarController` | LidarOverlay, Lidar2DView, Lidar3DView, WallDetectionOverlay, PageMonitor |
| `controllers/ssh.py` | `SSHController` | PageHome, PageLauncher, VideoOverlayTopBar |
| `services/video_stream.py` | `VideoStreamHandler` | PageWheel, PageHome, VideoFullscreenOverlay, PageWorkFlow |
| `services/base_top_view_service.py` | `BaseTopViewService` | BaseTopViewSettingsPopup, BaseFrontOverlay |

---

### Task 1.7b: Register Controllers Batch B (5 controllers)

| Python File | Register As | QML Files |
|---|---|---|
| `services/screen_recorder.py` | `ScreenRecorder` | VideoOverlayTopBar, DeviceControlTab |
| `services/ros_bag_recorder.py` | `RosBagRecorder` | DeviceControlTab |
| `ui/overlay.py` | `OverlayController` | MainWindow, MultiScreenListUI, SystemControlMenu |
| `models/action_config.py` | `ActionConfig` | ActionSequence, ActionItem |
| `handlers/steam_deck.py` | `SteamDeckHandler` | *(no QML refs — register for consistency)* |

---

### Task 1.8: Register Workflow Handlers

**Python files**: `services/workflow/workflow_runner.py`, `services/workflow_legacy.py`
**QML files**: SequenceList, WorkFlowControl, PageWorkFlow, WorkFlowTab, WorkFlowStatusOverlay

---

### Task 1.10: Qt6 Versionless Imports (DO BEFORE 1.9)

**Goal**: Scripted find-and-replace across all ~90 QML files.

**Replacements**:
- `import QtQuick 2.15` → `import QtQuick`
- `import QtQuick.Controls 2.15` → `import QtQuick.Controls`
- `import QtQuick.Layouts 1.15` → `import QtQuick.Layouts`
- `import QtQuick.Window 2.15` → `import QtQuick.Window`
- `import QtMultimedia 5.15` → `import QtMultimedia`
- `import Qt5Compat.GraphicalEffects` → keep as-is (compat module)
- Any other versioned Qt imports → remove version numbers

**How**: `find qml/ -name "*.qml" -exec sed -i 's/import QtQuick [0-9.]*/import QtQuick/' {} +` etc.

**Verification**: App launches. No import errors in console output.

---

### Task 1.9: Add qmldir Manifests (AFTER 1.10)

**Goal**: Create `qmldir` file in every QML directory.

> **IMPORTANT (Audit R8)**: No qmldir file may use bare `module PaintController`. That URI is reserved for Python singleton registration. Always use a dotted name like `PaintController.Core`, `PaintController.Components.Buttons`, etc.

**Directories needing qmldir** (~20):
- `core/` → `module PaintController.Core`
- `navigation/` → `module PaintController.Navigation`
- `components/buttons/` → `module PaintController.Components.Buttons`
- `components/displays/` → `module PaintController.Components.Displays`
- `components/inputs/` → `module PaintController.Components.Inputs`
- `components/panels/` → `module PaintController.Components.Panels`
- `components/popups/` → `module PaintController.Components.Popups`
- `components/specialized/pointcloud/` → `module PaintController.Components.PointCloud`
- `widgets/actions/` → `module PaintController.Widgets.Actions`
- `overlays/` → `module PaintController.Overlays`
- `overlays/lidar/` → `module PaintController.Overlays.Lidar`
- `overlays/systemcontrol/` → `module PaintController.Overlays.SystemControl` (already has one — update)
- `overlays/video/` → `module PaintController.Overlays.Video`
- `overlays/video/components/` → `module PaintController.Overlays.Video.Components`
- `pages/home/`, `pages/misc/`, `pages/spray/`, `pages/tuning/`, `pages/wheel/`, `pages/winch/`, `pages/workflow/`
- `pages/settings/`, `pages/settings/pages/`, `pages/settings/components/`
- `pages/status/`, `pages/status/components/`

**qmldir format example** (for `components/buttons/`):
```
module PaintController.Components.Buttons
ActionButton 1.0 ActionButton.qml
CustomButton 1.0 CustomButton.qml
MoveLengthButton 1.0 MoveLengthButton.qml
NumpadButton 1.0 NumpadButton.qml
TouchSwitch 1.0 TouchSwitch.qml
```

**Verification**:
- `grep -rn "^module PaintController$" qml/` → **ZERO hits** (namespace collision guard)
- `qmllint` (if available). App launches with no import errors.

---

### Task 1.11a-e: Add Required Properties

**Goal**: Audit each reusable component and add `required` to properties that callers must provide.

> **IMPORTANT (Audit R9)**: These tasks depend on ALL of 1.0-1.8 AND 1.9. Cannot add `required property` until that property's controller has been migrated to singleton imports.

**Pattern**:
```qml
// BEFORE:
property string settingKey: ""

// AFTER:
required property string settingKey
```

**Sub-batches**:
- **1.11a**: `components/buttons/` (5 files)
- **1.11b**: `components/inputs/` (5 files)
- **1.11c**: `components/displays/` (19 files) — largest batch
- **1.11d**: `components/panels/` + `components/popups/` (4 files)
- **1.11e**: `widgets/actions/` (3 files)

**For each**: Read the component, identify properties that MUST be set by callers (not internal state), add `required`. Then check all usages to ensure they set the property.

**Verification**: App launches — Qt throws a clear error if a required property is missing.

---

### Task POST-1: Startup Singleton Validation

**Goal**: Add validation that catches singleton registration typos.

> **Audit R5**: QML silently returns `undefined` when a singleton name is wrong — no crash, no console error. This is dangerous for a robotic controller.

**Add to `core/application.py`** after `engine.load()`:
```python
# Verify all singletons are registered correctly
_EXPECTED_SINGLETONS = [
    "StateStore", "SettingsManager", "Backend", "WheelController",
    "WinchController", "TeensyController", "ESP32ValveController",
    "LidarController", "WindMonitor", "SystemMonitor", "ScreenManager",
    "ControlProcessor", "WarningHandler", "HeartbeatHandler",
    "SSHController", "VideoStreamHandler", "BaseTopViewService",
    "ScreenRecorder", "RosBagRecorder", "OverlayController",
    "ActionConfig", "SteamDeckHandler", "WorkFlowHandler", "WorkFlowRunner",
]
for name in _EXPECTED_SINGLETONS:
    obj = engine.singletonInstance("PaintController", name)
    if obj is None:
        logger.error(f"FATAL: Singleton '{name}' not registered under PaintController")
        sys.exit(1)
logger.info(f"All {len(_EXPECTED_SINGLETONS)} singletons verified")
```

---

## Phase 2: Design System & DPI

### Task 2.0: Expand CommonStyle.qml

**Goal**: Build a comprehensive design system. ADDITIVE change — don't break existing consumers.

> **IMPORTANT (Audit R11)**: `Screen.pixelDensity` CANNOT work in a `QtObject` singleton — it has no parent Window. The `Screen` attached type requires being inside a visual hierarchy.

**DPI scaling approach** (choose one):
- **Option A (simplest)**: Set from MainWindow.qml: `Component.onCompleted: CommonStyle.scaleFactor = Screen.pixelDensity / 4.0`
- **Option B (cleanest)**: Register a Python-side `ScreenMetrics` singleton:
  ```python
  primary = QGuiApplication.primaryScreen()
  dpi = primary.physicalDotsPerInch() if primary else 96.0
  CommonStyle needs a writable property scaleFactor, set from Python before engine.load()
  ```

**Add to `qml/core/CommonStyle.qml`**:

**Color palette**:
- Background levels: `backgroundL0` (darkest), `backgroundL1`, `backgroundL2`, `backgroundL3` (lightest)
- Accent: `accentPrimary`, `accentSecondary`
- Status: `statusSuccess`, `statusWarning`, `statusError`, `statusInfo`
- Text: `textPrimary`, `textSecondary`, `textDisabled`
- Border: `borderDefault`, `borderFocused`

**Typography**:
- `fontDisplay` (24px), `fontHeading` (20px), `fontBody` (16px), `fontCaption` (13px), `fontLabel` (11px)

**Spacing scale**:
- `spacingXs: 4`, `spacingSm: 8`, `spacingMd: 12`, `spacingLg: 16`, `spacingXl: 24`, `spacingXxl: 32`

**DPI scaling**:
- `property real scaleFactor: 1.0` — writable, set from MainWindow or Python
- Apply to spacing and font sizes

**Component tokens**:
- `cardBackground`, `cardBorder`, `cardRadius`
- `buttonPrimary`, `buttonSecondary`, `buttonDanger`, `buttonHover`, `buttonPressed`
- `inputBackground`, `inputBorder`, `inputFocusBorder`

**Color mapping** (existing hardcoded → new tokens):
- `#1E1E1E`/`#2D2D30` (pages) → `backgroundL0`/`backgroundL1`
- `#252A36`/`#29303b` (components) → `cardBackground`/`backgroundL1`
- `#2c2c2c`/`#3498db` (overlays) → `backgroundL0`/`accentPrimary`

---

### Tasks 2.1-2.6: Apply Design System

For each batch: replace hardcoded colors (`#XXXXXX`), font sizes, and spacing with `CommonStyle.xyz` tokens.

**How to find hardcoded values**:
```bash
grep -rn '#[0-9a-fA-F]\{6\}' qml/
grep -rn 'font.pixelSize:' qml/
grep -rn 'font.pointSize:' qml/
```

**Batches**:
- **2.1**: `core/`, `navigation/`
- **2.2**: `components/buttons/`, `components/inputs/`
- **2.3**: `components/displays/`
- **2.4**: `components/panels/`, `components/popups/`
- **2.5a**: `overlays/` (root-level: OverlayLayer, EmergencyOverlay, MultiScreenListUI)
- **2.5b**: `overlays/systemcontrol/`
- **2.5c**: `overlays/video/`, `overlays/video/components/`, `overlays/lidar/`
- **2.6a**: `pages/home/`, `pages/spray/`, `pages/wheel/`, `pages/winch/`, `pages/tuning/`, `pages/misc/`
- **2.6b**: `pages/settings/`, `pages/settings/pages/`, `pages/settings/components/`
- **2.6c**: `pages/status/`, `pages/status/components/`, `pages/workflow/`

---

### Task 2.7: Refactor OverlayLayer Duplication

**File**: `qml/overlays/OverlayLayer.qml`

Left and right menu containers (~L19-L228) are near-identical ~100-line blocks. Extract a new `MenuOverlay.qml` component and instantiate twice.

---

### Task 2.8: Fix Page Component Naming

**File**: `qml/core/MainWindow.qml`, `qml/navigation/SelectBar.qml`

Rename `page1Component` → `wheelPageComponent`, `page2Component` → `winchPageComponent`, etc. Update all references in SelectBar's navigation switch-case.

---

## Phase 3: Testing & CI/CD

### Task 3.0: Clean __init__.py Imports

Remove the backward-compat layer from `__init__.py` (root). After Task 0.1 removes `RobotController`, the compat layer has no consumers. Clean all package `__init__.py` files to minimal exports.

### Task 3.1: Pytest Infrastructure

Set up pytest with mocking infrastructure for PySide6/ROS2. Extend the `conftest.py` namespace trick. Create mock factories for ROS2 Node, Publisher, Subscriber that can be injected into controllers.

**Implementation note (2026-04-17)**: Added `tests/fakes.py`, expanded `tests/conftest.py` with headless Qt and fake-node fixtures, pinned `pytest.ini` to PySide6 for pytest-qt, added `requirements-dev.txt`, and validated the scaffolding with `tests/test_test_infrastructure.py` plus a full passing pytest run.

> **Deferred idea (Architect)**: When writing tests for hardware controllers (3.6, 3.7), consider injecting pub/sub factories for testability instead of mocking the entire Node.

### Tasks 3.2-3.7: Test Modules

Each task creates tests for a specific pair of modules. Follow existing test patterns in `tests/test_crc.py` and `tests/test_input_utils.py`.

- **3.2**: StateStore + SettingsManager
- **3.3**: QtBridge + ControllerFactory
- **3.4**: EmergencyHandler + ControlProcessor
- **3.5**: UIInputHandler + SteamDeckHandler
- **3.6**: WheelController + WinchController
- **3.7**: ESP32ValveController + TeensyController

### Task 3.8: CI/CD Pipeline

Create `.github/workflows/ci.yml` with: colcon build → pytest → ruff → mypy → coverage.

### Task 3.9: Fix Build System

- `package.xml`: version `0.1.0`, fix PySide6 dep, remove unused rosidl, add test_depend
- `CMakeLists.txt`: add `ament_python_install_package()`, fix Qt5→Qt6, modernize
- `requirements.txt`: pin with `~=`

---

## Key Decisions (Agreed With User)

1. **Framework stays PySide6 + QML** — debt is in patterns, not tech choice
2. **C++ node deprecated** — Python is primary, C++ path abandoned during modernization (Audit R2)
3. **`setContextProperty` for all runtime objects** — `qmlRegisterSingletonInstance` is broken in PySide6 with implicit directory imports (see KNOWLEDGE.md). All controllers use `setContextProperty` with lowercase instance names.
4. **No `QML_IMPORT_NAME` module variables** — not needed for `setContextProperty`
5. **Aggressive approach** — user confirmed: touch every file for solid foundation
6. **Each phase on its own branch** — merged after verification
7. **Target: Steam Deck + industrial touchscreen PCs** — must be DPI-aware
8. **Test target: 30%→60% coverage** with comprehensive CI/CD
9. **QtBridge SRP deferred to Phase 4** — known concern, adding signals as-is for now (Audit R13)
10. **All objects use `setContextProperty`** — `qmlRegisterSingletonInstance` abandoned due to PySide6 bug. No migration needed for existing context properties.
