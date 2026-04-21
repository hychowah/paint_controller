# Paint Controller PySide6/QML Modernization — Validated Master Plan

> **Created**: 2026-04-16
> **Validated**: 2026-04-21 (pre-mortem + post-implementation/test sync)
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

Last Modified: 2026-04-21

| Task | Status | Notes |
|------|--------|-------|
| 0.1 Delete RobotController | [x] | RobotController + duplicate HeartbeatStatus removed; stale `RobotConfig`/`ConfigLoader` were later deleted in `TD-014` after replacing the dead `robot_config.yaml` path with `RuntimeDefaults` |
| 0.2 Type ControllerBundle | [x] | Concrete types added; imports moved to module scope |
| 0.3 Remove aliases + fix bugs | [x] | C++ path formally deprecated; `baseStreamer`/`videoStreamer` removed; overlay slot returns list |
| 0.4 Winch safety + ScreenManager | [x] | Re-enabled 4 winch move-command availability guards with logger warnings; ScreenManager now takes `node` in constructor |
| BF-1 Winch load-detection guard | [x] | `set_load_detection_mode()` now returns early with a logger warning when the winch is unavailable; covered in `tests/test_winch.py` |
| BF-2 SystemMonitor thread affinity | [x] | Worker timer now belongs to the worker object and start/stop are queued through signals; covered in `tests/test_system_monitor.py` |
| BF-3 Wheel error queued handling | [x] | `error_state_changed` now uses `Qt.QueuedConnection` so UI-side reactions stay off the ROS thread |
| BF-4 Winch logger consistency | [x] | Remaining availability guards in `winch.py` now use the node logger instead of `print()` |
| BF-5 MainWindow startup import fix | [x] | Stale `../pages/workflow` import removed from `MainWindow.qml`; validated in `QT_QPA_PLATFORM=offscreen` mode through `MainWindow QML loaded` |
| BF-6 Heartbeat state machine | [x] | `StateStore.controller_heartbeat_state` now drives `/controller/heartbeat`; `UIHeartbeatHandler`, emergency, and wheel-error paths update `IDLE`/`ONTASK`/`WARNING`/`ERROR` coherently |
| BF-7 Safe-state shutdown ordering | [x] | Shutdown now tears down the QML shell before backend cleanup, keeps controller/service cleanup ahead of ROS node destruction, and explicitly cleans up late thread owners including the ESP32 UDP thread |
| BF-8 Emergency hold duration from settings | [x] | `emergency_hold_duration_s` added to `SettingsManager` with default `1.0` and clamp `[0.2, 2.0]`; `EmergencyButtonHandler` updates live from the setting signal |
| BF-9 SafetyCoordinator + comms-loss failsafe | [x] | New `SafetyCoordinator` halts winch, wheel, spray trigger, and ESP32 valve; emergency, heartbeat-loss, and wheel-error now converge through the same halt-all path |
| PRE-1 Machine-verify QML mapping | [x] | Mapping table refreshed to live identifiers; lowercase `stateStore` and aliases removed |
| 1.0 Register StateStore | [x] | `StateStore` exposed via `setContextProperty`. `qmlRegisterSingletonInstance` abandoned (PySide6 bug — see KNOWLEDGE.md) |
| 1.1 Register SettingsManager | [x] | Confirmed done — registered during runtime bootstrap and validated in the post-load context-property loop |
| 1.2 Register QtBridge + kill findChild | [x] | All `findChild` replaced with signals (`showPopupRequested`, `closePopupRequested`, `toggleSidebarRequested`, `toggleVideoOverlayRequested`, `updateVideoSourceRequested`). `input.py` uses `close_popup_fn` callable. `QmlObjectName` enum deleted. `objectName` removed from popup/selectBar/videoOverlay. Only remaining QML object access: `engine.rootObjects()[0]` in `toggle_multiscreen_window()`. |
| 1.3 Register isolated controllers | [x] | CANCELLED — singleton-registration track abandoned; these objects already work via `setContextProperty()` |
| 1.4 Register wheelController | [x] | CANCELLED — `wheelController` already exposed via context property |
| 1.5 Register teensyController | [x] | CANCELLED — `teensyController` already exposed via context property |
| 1.6 Register winchController | [x] | CANCELLED — `winchController` already exposed via context property |
| 1.7a Register controllers batch A | [x] | CANCELLED — runtime stays on context properties; no PySide6 singleton migration |
| 1.7b Register controllers batch B | [x] | CANCELLED — runtime stays on context properties; no PySide6 singleton migration |
| 1.8 Register workflow handlers | [x] | CANCELLED — runtime stays on context properties; `workflow_legacy.py` deleted in Phase 1B |
| 1.10 Qt6 versionless imports | [x] | All QML files now use versionless Qt imports; `PageSpray.qml` uses `Qt5Compat.GraphicalEffects` for the Qt6 compatibility path |
| 1.9 Add qmldir manifests | [x] | Type-export `qmldir` files added across the QML tree; no bare `module PaintController`, and no new `module ...` declarations yet while runtime stays on relative imports |
| 1.11a required props — buttons | [~] | Downgraded to `TD-001`; no longer in the active queue |
| 1.11b required props — inputs | [~] | Downgraded to `TD-001`; no longer in the active queue |
| 1.11c required props — displays | [~] | Downgraded to `TD-001`; no longer in the active queue |
| 1.11d required props — panels/popups | [~] | Downgraded to `TD-001`; no longer in the active queue |
| 1.11e required props — specialized | [~] | Downgraded to `TD-001`; no longer in the active queue |
| POST-1 Startup context property validation | [x] | Post-load validation during runtime bootstrap checks all 22 context properties for `None` after `engine.load()` |
| 2.0 Expand CommonStyle | [x] | Token-based design system with scales, colors, spacing, typography, motion, and fixed shell tokens. `scaleFactor` defaults to 1.0 (runtime DPI removed — caused 2x on Steam Deck). `qmldir` singleton added. |
| 2.1 Design system — core/nav | [x] | `MainWindow`, `TopBar`, `SelectBar` migrated. Shell chrome uses fixed tokens. |
| 2.2 Design system — buttons/inputs | [x] | `ActionButton`, `TouchSwitch`, `NumpadButton`, `NumpadNew`, `KeyboardPopup`, `SettingInputField` migrated; `TrajNumpad.qml` deleted in Phase 1B |
| 2.3 Design system — displays | [x] | Display folder migrated to `CommonStyle` for the shared visual system; a few responsive size/motion literals still remain in specialized visualizers/dials |
| 2.4 Design system — panels/popups | [x] | `ControlPanel`, `ConnectionStatusPanel`, `SettingsSection`, `CustomPopup` migrated |
| 2.5a Design system — root overlays | [x] | `OverlayLayer`, `EmergencyOverlay` migrated |
| 2.5b Design system — systemcontrol | [~] | Deferred by user until safety/test hardening is complete. `EditWorkFlowTab`, `WorkFlowTab` migrated (layout-safe weights); `CommandTab` anchor fix. |
| 2.5c Design system — video overlays | [ ] | Deferred by user until after BF + Phase 3 hardening work |
| 2.6a Design system — pages batch 1 | [~] | Deferred by user until safety/test hardening is complete. `PageHome` already removed duplicate stream start and guarded its animation binding. |
| 2.6b Design system — settings pages | [ ] | Deferred by user until after the active hardening queue |
| 2.6c Design system — status/workflow | [ ] | Deferred by user until after the active hardening queue |
| 2.7 Refactor OverlayLayer dedup | [ ] | Deferred with the rest of the design-system backlog |
| 2.8 Fix page naming | [ ] | |
| 3.0 Clean __init__.py imports | [x] | `core`, `handlers`, and `controllers` package inits are now lightweight and no longer re-export heavy Qt/ROS modules |
| 3.1 Pytest infrastructure | [x] | Added headless Qt fixture, namespace-safe imports, fake ROS node/publisher/subscription/timer scaffolding, shared fake topic bus, and validation tests; normalized existing utility/harness test files to the layered style |
| 3.2 Tests — StateStore/Settings | [x] | Added direct runtime coverage for `StateStore` signals/defaults and `SettingsManager` load/clamp/save/persistence behavior |
| 3.3 Tests — QtBridge/Factory | [x] | `tests/test_qt_bridge.py` — 13 tests (signals, video source selection, null-safe wiring) |
| 3.4 Tests — Emergency/ControlProc | [x] | `tests/test_emergency.py` (EmergencyButtonHandler); `tests/test_control_processor.py` — 31 tests (track curve/deadzone/clamping, winch guards/locks/activation-gate, wheel travel accumulation/send) |
| 3.5 Tests — Input/SteamDeck | [x] | Added pure HID decoder `utils/steam_deck_hid.py`, new `tests/test_steam_deck_hid.py`, and kept `tests/test_steam_deck_handler.py` green after removing unsafe destructor-side cleanup |
| 3.6 Tests — Wheel/Winch | [x] | `tests/test_winch_ros_integration.py` plus `tests/test_winch.py` cover the winch path; `tests/test_wheel.py` now covers unified speed publishing, state updates, error transitions, and timeout availability |
| 3.7 Tests — ESP32/Teensy | [x] | `tests/test_esp32_valve.py` covers command clamping, keepalive gating, raw UDP messages, status publishing, and shutdown cleanup of the UDP receive thread; `tests/test_teensy.py` covers status parsing, user-field preservation, relay publishing, thrust updates, and force publishing |
| 3.8 CI/CD pipeline | [x] | `.github/workflows/ci.yml`: lint gates both pytest and ROS2 build jobs. `pyproject.toml` with ruff/pytest/coverage config. `requirements-dev.txt` updated. |
| 3.9 Fix build system | [x] | `CMakeLists.txt` stripped to pure `ament_cmake` wrapper (C++/Qt5/GStreamer deps removed). `package.xml` cleaned to 0.1.0, C++ deps removed. `requirements.txt` switched to `~=` pins. |
| 3.10 Static typing gate | [~] | Initial `pyright` gate added to CI: strict on `core/controller_factory.py`, basic visibility on selected PySide-heavy core files (`settings.py`, `state_store.py`, `qt_bridge.py`); handler/controller boundary expansion remains next |
| TD-014 main() decomposition | [x] | Bootstrap moved into `core/app_runtime.py`; `core/application.py` is now a thin entry-point wrapper, `RosThread` moved to `core/ros_node.py`, the dead `robot_config.yaml` loader path was deleted in favor of `RuntimeDefaults`, and one registration table now drives both QML context-property registration and validation |
| 4.0 Startup/emergency integration smoke test | [x] | `tests/test_startup_smoke.py` now covers both offscreen startup wiring and shutdown teardown, asserting that `MainWindow.qml` loads cleanly and that teardown introduces no new null-binding warnings |

## Current Checkpoint

- **Test infrastructure stabilized**: Qt fixture conflict resolved: `qt_core_app` is now an alias of `qt_app`; `QT_QPA_PLATFORM` forced to `offscreen`; `_flush_qt_events` autouse fixture added
- FakePublisher hardened with `isinstance` type check; FakeRosBus delivers `copy.copy(msg)` instead of shared reference
- Controller fakes added to `fakes.py`: `FakeWheel`, `FakeWinch`, `FakeTeensy`, `FakeEsp32Valve`, `FakeOverlay`, `FakeHeartbeatHandler`, `FakeStateStore`
- Stub drift-check tests added to `test_test_infrastructure.py`
- `test_control_processor.py` (31 tests) and `test_qt_bridge.py` (13 tests) completed
- BF-1..BF-4 are complete: the winch unavailable guards are fixed, SystemMonitor startup is worker-thread-safe, and wheel error handling is queued off the ROS thread
- `3.0` is complete: package `__init__.py` files no longer re-export the heavy Qt/ROS module graph
- `3.6` is complete: WheelController now has dedicated unit coverage alongside the existing winch tests
- `3.7` is complete: ESP32ValveController and TeensyController now have direct regression coverage, and the spray-gun leveling state now persists across ROS status callbacks
- `3.5` is complete: Steam Deck raw HID parsing now lives in a pure decoder with dedicated tests, and the cleanup regression remains covered without interpreter-exit segfaults
- **Persistence/threads hardening complete**: settings and SSH JSON writes are now atomic, SSH command/availability callbacks marshal back through Qt signals, and `TeensyController` no longer exposes a live shared `_status` dict across ROS and Qt threads
- **Safety integration coverage added**: `tests/test_safety_integration.py` now exercises the real `UIHeartbeatHandler` → `SafetyCoordinator` halt-all path with fake effectors, covering the convergence route that previously existed only across isolated unit tests
- **Typing gate v1 is live**: `pyrightconfig.json` and CI now enforce an initial pyright pass; strict mode currently holds for `core/controller_factory.py` while PySide descriptor-heavy core modules stay in basic mode until the typed wrapper/stub story improves
- **Safety hardening batch complete**: BF-6..BF-9 are implemented and covered by targeted regression tests; shutdown teardown ordering is now hardened across the QML shell, Steam Deck reader thread, and ESP32 UDP thread owner
- **TD-014 is complete**: startup/shutdown orchestration now lives in `core/app_runtime.py`, `core/application.py` is a thin compatibility wrapper, `RosThread` now lives beside `PaintRosNode`, and the stale missing-`robot_config.yaml` warning is gone because that dead loader path was removed
- **Validation update**: full-suite revalidation is green at `145 passed`; pyright is green (`0 errors`), and a serial offscreen launch still reaches `MainWindow QML loaded` before the expected timeout-kill. The known non-blocking Qt Quick 3D/RHI warning in offscreen mode remains.
- Recent targeted validation for the controller hardening batches is green; revalidate any full-suite claim with a fresh local pytest run instead of relying on older fixed test-count snapshots
- Task 1.1 (SettingsManager QML registration): verified done — still registered during runtime bootstrap and validated in POST-1 loop after the `AppRuntime` extraction
- **Approved queue change executed**: `TD-014` is complete, `3.10` remains a phased rollout rather than a one-shot repo-wide mandate, and `2.8` remains the next cosmetic cleanup after typing work
- **Deferred backlog**: `2.5b`, `2.5c`, `2.6a-c`, and `2.7` stay in the plan but are intentionally postponed until the active hardening queue is complete
- **Next tasks** (priority order):
  1. `3.10 Static typing gate expansion`
  2. `2.8 Fix page naming`

---

## Dependency Graph

```
Completed this batch: BF-1..BF-9, 3.0, 3.5, 3.6, 3.7, 4.0, the first `3.10` gate slice, and TD-014
         ↓
Quality gate expansion: 3.10 (handler/controller boundaries beyond the current factory/core slice)
         ↓
Cosmetic cleanup: 2.8 (page naming)

Deferred backlog: 2.5b, 2.5c, 2.6a-c, and 2.7 remain tracked but are intentionally postponed until the active hardening queue is complete; `1.11a-e` is now tracked as `TD-001` rather than an active queue item
```

---

## Risk Map

| Task | Risk | Why |
|------|------|-----|
| 1.0 StateStore | LOW | 4 QML files, establishes pattern |
| 1.1 SettingsManager | LOW | 3 QML files |
| 1.2 QtBridge + findChild | ~~HIGH~~ | ✅ DONE — Signal replacement + input.py scope + MainWindow changes |
| 1.3 Isolated controllers (6) | CANCELLED | Context-property runtime retained; singleton migration abandoned |
| 1.4 wheelController | CANCELLED | Context-property runtime retained |
| 1.5 teensyController | CANCELLED | Context-property runtime retained |
| 1.6 winchController | CANCELLED | Context-property runtime retained |
| 1.7a controllers batch A | CANCELLED | Context-property runtime retained |
| 1.7b controllers batch B | CANCELLED | Context-property runtime retained |
| 1.8 Workflow handlers | CANCELLED | Context-property runtime retained; workflow consolidation is separate work |
| 1.10 Versionless imports | LOW | Mechanical sed replace |
| 1.9 qmldir manifests | **HIGH** | ~20 new files, module naming critical |
| 1.11a-e Required props | MEDIUM | No longer in the active queue; still useful defensive debt, but startup smoke and broader tests now catch the higher-value binding regressions |
| BF-6 Heartbeat state machine | ~~HIGH~~ | ✅ DONE — controller heartbeat now publishes live runtime state from `StateStore` |
| BF-7 Safe-state shutdown ordering | ~~HIGH~~ | ✅ DONE — QML teardown, controller/service cleanup, and late thread-owner cleanup now all complete before final ROS node destruction |
| BF-8 Emergency hold duration from settings | ~~HIGH~~ | ✅ DONE — emergency hold duration is now an explicit clamped setting with a 1.0s default |
| BF-9 SafetyCoordinator + comms-loss failsafe | ~~HIGH~~ | ✅ DONE — all halt-all paths now include the ESP32 valve and share one coordinator |
| BF-1 Winch load-detection guard | HIGH | Safety bug: unavailable winch currently can still publish load-detection commands |
| BF-2 SystemMonitor thread affinity | MEDIUM | Wrong-thread timer startup can block UI and undermines worker-thread isolation |
| BF-3 Wheel error queued handling | MEDIUM | Current direct callback path runs UI-side reactions from the ROS thread |
| BF-4 Winch logger consistency | LOW | Remaining `print()` guards bypass structured ROS logging |
| BF-5 MainWindow startup import fix | ~~HIGH~~ | ✅ DONE — stale `../pages/workflow` import removed and startup validated headlessly through `MainWindow QML loaded` |
| 3.6 WheelController tests | ~~HIGH~~ | ✅ DONE — dedicated WheelController coverage now exists in `tests/test_wheel.py` |
| 3.7 ESP32/Teensy tests | ~~HIGH~~ | ✅ DONE — dedicated ESP32 and Teensy coverage now exists, including ESP32 shutdown cleanup regression coverage |
| 2.0 Expand CommonStyle | ~~MEDIUM~~ | ✅ DONE — DPI approach resolved (fixed scaleFactor at 1.0) |
| 3.10 Static typing gate | MEDIUM | Initial pyright gate now exists, but expansion beyond the current factory/core slice still depends on better typing around PySide descriptor-heavy modules and handler/controller boundaries |
| 4.0 Startup/emergency integration smoke test | ~~MEDIUM~~ | ✅ DONE — `tests/test_startup_smoke.py` now exercises both offscreen shell load and shutdown teardown without new null-binding warnings |

---

## Reference Patterns

### Context Property Pattern (CURRENT — all 22 runtime objects use this)
```python
# In app_runtime.py runtime bootstrap, AFTER engine creation, BEFORE engine.load()
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
import QtQuick
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

### QML Import Current Style (IMPLEMENTED — Task 1.10 ✅)
```qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../pages/home"         // still relative until qmldir rollout
```

---

## Runtime Identifier → QML File Mapping

Used for Phase 1 tasks. Shows which QML files must be updated per controller registration.

> **IMPORTANT (Audit R10)**: Before continuing Phase 1, run `for prop in stateStore settingsManager backend overlayController workFlowRunner warningHandler baseStreamHandler wheelController winchController steamDeckHandler windMonitor teensyController esp32ValveController lidarController heartbeatHandler controlProcessor sshHandler systemMonitor screenRecorder rosBagRecorder screenManager baseTopViewController; do echo "==$prop=="; grep -rl "$prop" qml/; done` and compare against this table. Fix any discrepancies.

| Identifier | QML Files That Reference It |
|---|---|
| `backend` | EmergencyOverlay, PageSpray, MainSettingsPage |
| `stateStore` | TopBar, ExecutorPageStatus, PlannerPageStatus |
| `overlayController` | MainWindow, MultiScreenListUI, SystemControlMenu |
| `workFlowRunner` | WorkFlowTab, EditWorkFlowTab, WorkFlowStatusOverlay |
| `warningHandler` | TopBar |
| `baseStreamHandler` | PageWheel, PageHome, VideoFullscreenOverlay, DeviceControlTab |
| `wheelController` | PageWheel, BaseFrontOverlay, WheelsCard, DeviceControlTab, ConnectionStatusPanel, ExecutorPageStatus, PlannerPageStatus, WheelStatus |
| `winchController` | PageWinch, PageStatus, EndEffectorOverlay, VideoOverlayTopBar, WinchCard, ConnectionStatusPanel, DeviceControlTab, CommandTab, MoveLengthButton, PlannerPageStatus, ExecutorPageStatus |
| `steamDeckHandler` | *(no QML refs — Python-only, still register for consistency)* |
| `windMonitor` | PageSensors |
| `teensyController` | PageTuning, EndEffectorOverlay, VideoOverlayTopBar, SettingsTab, TeensyArmCard, IMUCard, MonitorHeader, ConnectionStatusPanel, CommandTab, DeviceControlTab, ExecutorPageStatus, PlannerPageStatus, TeensyStatus |
| `esp32ValveController` | EndEffectorOverlay, ValvesCard |
| `lidarController` | LidarOverlay, Lidar2DView, Lidar3DView, WallDetectionOverlay, PageMonitor |
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

**Goal**: Remove ~525 lines of dead bootstrap code that previously lived in `core/application.py`.

**Implementation note (2026-04-17, updated 2026-04-21)**: `RobotConfig` and `ConfigLoader` were retained temporarily during Phase 0 because `main()` still referenced them. TD-014 later removed that dead path entirely after confirming `robot_config.yaml` does not exist in the repo and replacing it with `RuntimeDefaults` in `core/config.py`.

**Context**: The old `RobotController(Node, QObject)` god class was replaced by `PaintRosNode`, `StateStore`, `QtBridge`, `ControllerFactory` in the previous refactor. The old bootstrap path never instantiated it. Confirmed dead code — zero runtime references. Verified: no external references in `launch/`, `tests/`, `scripts/`, or `fish-eye/`.

**Files to modify**:
- `core/application.py` — Historical location of the deleted `RobotController` class, duplicate `HeartbeatStatus`, and temporary `RobotConfig` / `ConfigLoader` scaffolding. TD-014 later moved live bootstrap ownership into `core/app_runtime.py`.
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

> **Historical Runtime Note (Audit R2)**: The old C++ UI/runtime path is no longer part of the live tree. Do not plan modernization work around `paint_controller_cpp` or a top-level `src/` UI path; the active runtime is the Python/QML application only.

**Files to modify**:
- `core/application.py` — Historical location of the context property block before TD-014 moved live registration into `core/app_runtime.py`:
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
- `core/application.py` — Historical bootstrap location where `bundle.screen_manager.node = node` was removed before live orchestration later moved into `core/app_runtime.py`.

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

### Task BF-6: Heartbeat State Machine

**Goal**: Replace the hardcoded controller heartbeat with a live state machine that downstream systems can trust.

**Problem**: `PaintRosNode.publish_heartbeat()` currently publishes `IDLE` unconditionally, even during emergency or communication loss. That makes `/controller/heartbeat` a timer tick, not a safety signal.

**Files to modify**:
- `core/state_store.py` — add `controller_heartbeat_state` property + changed signal
- `utils/constants.py` — define `IDLE`, `ONTASK`, `WARNING`, `ERROR` heartbeat constants in one place
- `core/ros_node.py` — inject/read the current heartbeat state instead of hardcoding `IDLE`
- `handlers/emergency.py` — set state to `ERROR` on emergency trigger and back to `IDLE` when manually cleared
- `handlers/heartbeat.py` — set state to `WARNING` on base/EF heartbeat loss and clear it on recovery
- `core/application.py` — historical bootstrap location that originally routed wheel motor error into the same state machine; live routing now lives in `core/app_runtime.py`

**Verification**:
- Targeted tests prove emergency, wheel-error, and heartbeat-loss transitions publish the expected `UInt8` value
- Headless app smoke still reaches `MainWindow QML loaded`

---

### Task BF-7: Safe-State Shutdown Ordering

**Outcome**: Controller cleanup now runs while the shared ROS node is still valid, and the QML shell is torn down before backend QObject cleanup begins.

**Implemented**:
- `RosThread` no longer owns `node.destroy_node()`
- runtime shutdown tears down the QML object tree before controller/service cleanup
- controller/service cleanup completes before `node.cleanup()` / `destroy_node()`
- the remaining app-owned thread owners now participate in normal cleanup, including the Steam Deck reader thread and ESP32 UDP receive thread

**Files changed**:
- `core/application.py` (historical wrapper location before TD-014 moved teardown orchestration into `core/app_runtime.py`)
- `handlers/steam_deck.py`
- `services/screen_manager.py`
- `controllers/esp32_valve.py`

**Verification**:
- live shutdown logs now complete without QML null-binding spam or `QThread: Destroyed while thread is still running`
- targeted shutdown regressions cover QML teardown, Steam Deck cleanup, and ESP32 cleanup

---

### Task BF-8: Emergency Hold Duration From Settings

**Goal**: Remove ambiguity from the emergency hold duration by making it an explicit safety setting.

**Problem**: `EmergencyButtonHandler` currently uses `0.2` seconds while the code comment still says "1 second". That is a safety contract mismatch.

**Files to modify**:
- `core/settings.py` — add `emergency_hold_duration_s` with default `1.0` and clamp range `[0.2, 2.0]`
- `handlers/emergency.py` — read/update the duration from settings instead of a literal
- `tests/test_settings_runtime.py`, `tests/test_emergency.py` — cover clamp + runtime behavior

**Verification**:
- Changing the setting updates the handler behavior without restart
- Tests cover both clamp behavior and hold-to-trigger timing

---

### Task BF-9: SafetyCoordinator + Comms-Loss Failsafe

**Goal**: Centralize "halt all effectors" behavior so emergency, heartbeat-loss, and wheel-error cannot drift apart.

**Problem**: The current emergency path stops winch, spray, and wheel only; the ESP32 valve is still omitted, and heartbeat-loss only updates status without enforcing a stop.

**Files to modify**:
- `handlers/safety_coordinator.py` — new contained extraction with `halt_all_effectors(reason)`
- `handlers/emergency.py` — delegate to `SafetyCoordinator`
- `handlers/heartbeat.py` — call the same halt path on heartbeat-loss transitions
- `core/controller_factory.py` — inject the coordinator into dependent handlers
- `core/application.py` — historical bootstrap location that was later superseded by `core/app_runtime.py` during TD-014

**Verification**:
- Tests assert emergency and heartbeat-loss each stop winch, wheel, spray trigger, and ESP32 valve even if one effector call raises

---

## Phase 1: QML Module System

### Task PRE-1: Machine-Verify QML Mapping Table

**PREREQUISITE — Do this before ANY Phase 1 task.**

**Goal**: Generate a fresh mapping of runtime identifiers to QML files and compare against the table above. Fix discrepancies.

**Script**:
```bash
cd python/paint_controller
for prop in stateStore settingsManager backend overlayController workFlowRunner \
  warningHandler baseStreamHandler wheelController winchController steamDeckHandler windMonitor \
  teensyController esp32ValveController lidarController heartbeatHandler \
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
- `core/app_runtime.py` — Runtime bootstrap uses `ctx.setContextProperty("stateStore", state_store)` via the shared registration table

**QML files** (3 files): Access via `stateStore.xyz` (lowercase, no import needed)
- `navigation/TopBar.qml`
- `pages/status/components/ExecutorPageStatus.qml`
- `pages/status/components/PlannerPageStatus.qml`

---

### Task 1.1: Register SettingsManager

**Same setContextProperty pattern. Already exposed — verify QML access works.**

**Python**: `core/settings.py` + runtime bootstrap (`core/app_runtime.py`; historically `core/application.py` before TD-014)
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

### Tasks 1.3-1.8: Controller Singleton Migration (CANCELLED)

These tasks originally aimed to migrate runtime objects from context properties to PySide6 singleton registration plus PascalCase QML access.

**Status**: CANCELLED.

**Reason**:
- `qmlRegisterSingletonInstance()` is broken in this codebase/PySide6 combination and corrupts the QML type system.
- All runtime objects already work via `engine.rootContext().setContextProperty()`.
- Future effort should go to tests, workflow consolidation, god-object decomposition, design-system completion, and later QML module cleanup.

**Replacement guidance**:
- Keep runtime objects on lowercase context properties.
- Do not add `import PaintController` singleton-based access for controllers/services.
- Treat workflow work as a consolidation/removal task for `workflow_legacy.py`, not a registration task.

---

### Task 1.10: Qt6 Versionless Imports (COMPLETED)

**Goal**: Normalize the full QML tree to versionless Qt6 imports before `qmldir` rollout.

**Replacements**:
- `import QtQuick 2.15` → `import QtQuick`
- `import QtQuick.Controls 2.15` → `import QtQuick.Controls`
- `import QtQuick.Layouts 1.15` → `import QtQuick.Layouts`
- `import QtQuick.Window 2.15` → `import QtQuick.Window`
- `import QtMultimedia 5.15` → `import QtMultimedia`
- `import Qt5Compat.GraphicalEffects` → keep as-is (compat module)
- Any other versioned Qt imports → remove version numbers

**Status**: ✅ DONE. All QML files now use versionless Qt imports. `PageSpray.qml` uses `Qt5Compat.GraphicalEffects` for the Qt6 compatibility path.

**Verification**: `grep -rnE '^import (Qt[^ ]+) [0-9]+\.[0-9]+$' python/paint_controller/qml/` → zero hits. Versionless-import cleanup is complete.

---

### Task 1.9: Add qmldir Manifests (AFTER 1.10)

**Status**: Completed on 2026-04-20 with a runtime-safe interim strategy.

The tree now has `qmldir` manifests for the component/page/overlay directories that were still missing them, but the files intentionally contain only type export lines for now. The app still relies on relative directory imports and `setContextProperty()` bindings, so this task stopped short of introducing URI-module imports or new dotted `module ...` declarations.

**Implemented scope**:
- `navigation/`
- `components/buttons/`, `components/displays/`, `components/inputs/`, `components/panels/`, `components/popups/`, `components/specialized/pointcloud/`
- `overlays/`, `overlays/lidar/`, `overlays/video/`, `overlays/video/components/`
- `pages/home/`, `pages/misc/`, `pages/settings/`, `pages/settings/components/`, `pages/settings/pages/`, `pages/spray/`, `pages/status/`, `pages/status/components/`, `pages/tuning/`, `pages/wheel/`, `pages/winch/`

**qmldir format used** (for `components/buttons/`):
```
ActionButton 1.0 ActionButton.qml
CustomButton 1.0 CustomButton.qml
MoveLengthButton 1.0 MoveLengthButton.qml
NumpadButton 1.0 NumpadButton.qml
TouchSwitch 1.0 TouchSwitch.qml
```

**Verification**:
- No new `qmldir` file uses bare `module PaintController`
- No new `qmldir` file introduces a `module ...` declaration that would conflict with the current relative-import runtime
- `qmllint` (if available). App launches with no import errors.

---

### Task 1.11a-e: Add Required Properties

**Goal**: Audit each reusable component and add `required` to properties that callers must provide.

> **IMPORTANT (Audit R9)**: These tasks depend on stable module/import cleanup. Finish 1.9 first, then add `required property` only after each component's callers are explicit and audited.

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
- **1.11e**: `components/specialized/pointcloud/` (2 files)

**For each**: Read the component, identify properties that MUST be set by callers (not internal state), add `required`. Then check all usages to ensure they set the property.

**Verification**: App launches — Qt throws a clear error if a required property is missing.

---

### Task POST-1: Startup Context Property Validation

**Goal**: Add validation that catches context-property wiring typos.

> **Audit R5**: QML silently returns `undefined` when a runtime object name is wrong — no crash, no console error. This is dangerous for a robotic controller.

**Add to the runtime bootstrap** after `engine.load()`:
```python
# Verify all context properties are wired correctly
_EXPECTED_CONTEXT_PROPERTIES = [
  "stateStore", "backend", "overlayController", "workFlowRunner",
  "warningHandler", "baseStreamHandler", "wheelController",
  "winchController", "steamDeckHandler", "windMonitor",
  "teensyController", "esp32ValveController", "lidarController",
  "heartbeatHandler", "controlProcessor", "sshHandler",
  "systemMonitor", "screenRecorder", "rosBagRecorder",
  "settingsManager", "screenManager", "baseTopViewController",
]
for name in _EXPECTED_CONTEXT_PROPERTIES:
  if ctx.contextProperty(name) is None:
    logger.error(f"Missing QML context property: {name}")
logger.info(f"Validated {len(_EXPECTED_CONTEXT_PROPERTIES)} QML context properties")
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
- **2.3**: `components/displays/` — completed 2026-04-20; shared display styling now runs through `CommonStyle`, with a few responsive literals still remaining in specialized visualizers/dials
- **2.4**: `components/panels/`, `components/popups/`
- **2.5a**: `overlays/` (root-level: OverlayLayer, EmergencyOverlay, MultiScreenListUI)
- **2.5b**: `overlays/systemcontrol/`
- **2.5c**: `overlays/video/`, `overlays/video/components/`, `overlays/lidar/`
- **2.6a**: `pages/home/`, `pages/spray/`, `pages/wheel/`, `pages/winch/`, `pages/tuning/`, `pages/misc/`
- **2.6b**: `pages/settings/`, `pages/settings/pages/`, `pages/settings/components/`
- **2.6c**: `pages/status/`, `pages/status/components/`

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

**Implementation note (2026-04-17, updated 2026-04-21)**: Added `tests/fakes.py`, expanded `tests/conftest.py` with headless Qt and fake-node fixtures, configured pytest in `pyproject.toml` for PySide6/pytest-qt, added `requirements-dev.txt`, and validated the scaffolding with `tests/test_test_infrastructure.py`. Later sessions expanded the suite substantially; the current validated full-suite state is tracked in **Current Checkpoint** rather than older fixed-count snapshots.

> **Deferred idea (Architect)**: When writing tests for hardware controllers (3.6, 3.7), consider injecting pub/sub factories for testability instead of mocking the entire Node.

### Tasks 3.2-3.7: Test Modules

Each task creates tests for a specific pair of modules. Follow the layered patterns already present in `tests/test_crc.py`, `tests/test_input_utils.py`, `tests/test_emergency.py`, `tests/test_winch.py`, and `tests/test_winch_ros_integration.py`.

- **3.2**: StateStore + SettingsManager — completed with direct runtime tests for defaults, signals, load/merge/clamp, save helpers, and section persistence
- **3.3**: QtBridge + ControllerFactory
- **3.4**: EmergencyHandler + ControlProcessor
- **3.5**: UIInputHandler + SteamDeckHandler
- **3.6**: WheelController + WinchController
- **3.7**: ESP32ValveController + TeensyController

### Task 3.8: CI/CD Pipeline

Create `.github/workflows/ci.yml` with the current repo flow: lint first, then pytest and ROS2 build as lint-gated jobs.

### Task 3.9: Fix Build System

- `package.xml`: version `0.1.0`, fix PySide6 dep, remove unused rosidl, add test_depend
- `CMakeLists.txt`: add `ament_python_install_package()`, fix Qt5→Qt6, modernize
- `requirements.txt`: pin with `~=`

### Task 3.10: Static Typing Gate

**Goal**: Add a semantics-aware typing gate after the active safety batch so controller/handler wiring regressions are caught before runtime.

**Scope**:
- Start with `core/`, `controller_factory.py`, and the handler/controller constructor boundaries touched by the safety batch
- Prefer a narrow mypy or pyright configuration over an all-or-nothing repo-wide rollout
- Add the gate to CI after the active safety batch and startup smoke test are green

**Verification**:
- CI fails on newly introduced type regressions in the covered modules

---

## Phase 4: Runtime Safety Verification

### Task 4.0: Startup/Emergency Integration Smoke Test

**Outcome**: The smoke gate now validates both startup integrity and shutdown teardown behavior for the QML shell.

**What it covers now**:
- offscreen `MainWindow.qml` load
- all 22 context properties resolving at startup
- no fatal QML startup warnings
- shutdown teardown producing no new null-binding / undefined-assignment warnings after the teardown helper runs

**Verification**:
- `tests/test_startup_smoke.py` passes in the full suite
- see **Current Checkpoint** for the latest validated full-suite result rather than relying on this older task-local count

---

## Key Decisions (Agreed With User)

1. **Framework stays PySide6 + QML** — debt is in patterns, not tech choice
2. **C++ node deprecated** — Python is primary, C++ path abandoned during modernization (Audit R2)
3. **`setContextProperty` for all runtime objects** — `qmlRegisterSingletonInstance` is broken in PySide6 with implicit directory imports (see KNOWLEDGE.md). All controllers use `setContextProperty` with lowercase instance names.
4. **No `QML_IMPORT_NAME` module variables** — not needed for `setContextProperty`
5. **Aggressive approach** — user confirmed: touch every file for solid foundation
6. **Each phase on its own branch** — merged after verification
7. **Target: Steam Deck + industrial touchscreen PCs** — must be DPI-aware
8. **Test direction: layered suite** — pure logic, harness validation, component behavior, and thin real ROS transport checks
9. **QtBridge SRP deferred to Phase 4** — known concern, adding signals as-is for now (Audit R13)
10. **All objects use `setContextProperty`** — `qmlRegisterSingletonInstance` abandoned due to PySide6 bug. No migration needed for existing context properties.
11. **Safety batch outranked cosmetic cleanup during the April 21 hardening pass** — this was completed; use **Current Checkpoint** for the active queue
12. **Emergency hold duration becomes a real setting** — `emergency_hold_duration_s` defaults to `1.0` and is clamped to `[0.2, 2.0]`
13. **Shutdown ownership stays in the runtime orchestration layer** — `RosThread` stops spinning, and the bootstrap owner (`AppRuntime.shutdown()` after TD-014; historically `main()`) owns final controller cleanup and `node.destroy_node()` ordering
14. **Heartbeat is a state signal, not a metronome** — `/controller/heartbeat` must reflect `IDLE`/`ONTASK`/`WARNING`/`ERROR`
15. **Safety behavior must converge through one halt-all path** — emergency, wheel-error, and heartbeat-loss will share a `SafetyCoordinator`
16. **Static typing gate is added after the active safety batch** — narrow, high-signal coverage first; not a repo-wide mandate on day one
