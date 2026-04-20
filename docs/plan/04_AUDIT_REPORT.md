# Pre-Mortem Audit Report

> **Date**: 2026-04-16
> **Agents**: Technical Auditor (Safety Specialist) + Systems Architect (Optimization Specialist)
> **Protocol**: Elon Musk first-principles — agents propose hypotheses, Project Lead validates against codebase

> **Historical Note**: This is the 2026-04-16 pre-mortem rationale document. Its accepted findings were folded into `01_MASTER_PLAN.md`. Use this file for background and design reasoning, not for current progress status.

> **Superseded Guidance Warning**: Some Phase 1 recommendations in this audit assume the earlier singleton-registration migration path. The current repo direction is `setContextProperty()` for runtime bindings plus conservative `qmldir` type exports, as tracked in `01_MASTER_PLAN.md` and `03_QML_BINDINGS.md`.

> **Implemented Since This Audit**: `0.1-0.4`, `PRE-1`, `1.0`, `1.2`, `POST-1`, `3.1`, `3.8`, `3.9`, partial Phase 2 (`2.0`, `2.1`, `2.2`, `2.4`, `2.5a`), plus partial Phase 3 safety/transport tests (`3.4`, `3.6`), the subsequent test-suite/documentation normalization pass, and the final `input.py` popup-close wiring that removes the last Python-side `findChild()` lookup. **Session 2 additions (2026-04-21)**: `test_control_processor.py` (31 tests — track curve/deadzone/clamping, winch guards/locks/activation-gate, wheel travel accumulation/send), `test_qt_bridge.py` (13 tests — signals, video source selection, null-safe wiring), `fakes.py` 7 new controller fakes + stub drift checks, `conftest.py` platform fix + fixture alias + autouse flush, `winch.py` logger routing fix (4 `move_*` methods). Full suite: **100 tests, all passing**.

---

## Audit Process

1. Two sub-agents deployed in parallel with distinct mandates
2. Verification agent deployed to cross-examine 5 critical claims
3. Project Lead rendered final verdicts on all 19 findings

---

## CONFIRMED & INTEGRATED (Plan changed)

### R1: QML_IMPORT_NAME is Dead Code (LOW → Plan Impact: HIGH)

**Source**: Technical Auditor
**Finding**: The plan instructed adding `QML_IMPORT_NAME = "PaintController"` and `QML_IMPORT_MAJOR_VERSION = 1` to every controller file. These module-level variables are only consumed by the `@QmlElement` decorator pipeline — they do nothing for `qmlRegisterSingletonInstance()`, which takes URI/version as direct arguments.

**Evidence**: PySide6 type stubs confirm `qmlRegisterSingletonInstance(type_obj, uri, version_major, version_minor, qml_name, callback)`.

**Verdict**: VALID. Removed from all Phase 1 task descriptions. Future developers would have been confused by dead variables implying false coupling.

---

### R2: Task 0.3 Breaks C++ Binary (HIGH)

**Source**: Technical Auditor
**Finding**: `src/paint_controller.cpp` L502-503 sets `baseStreamer` and `backend` context properties and loads the same QML files. Removing `baseStreamer` from QML (Task 0.3) breaks the C++ launch path.

**Evidence**: Verified. C++ binary shares `qml/core/MainWindow.qml`. Has its own launch file. But only sets 2 of the 24 runtime objects required by the full UI — already non-functional for normal operation.

**Verdict**: VALID. User decision executed — **C++ path deleted in Phase 1A.** Source files (`src/*.cpp`, `include/paint_controller/*.hpp`) removed entirely.

---

### R3: Task 1.2 Missing input.py findChild (MEDIUM)

**Source**: Technical Auditor
**Finding**: `handlers/input.py` L79 has a `findChild("messagePopup")` call that the plan didn't list. It closes the popup before switching control modes.

**Evidence**: Verified at L79-82 in live code (`UIInputHandler.on_switch_pressed()`), created by the factory and wired into `main()`.

**Verdict**: VALID. Added to Task 1.2 scope. Replace with `qt_bridge.close_popup()` emitting `closePopupRequested` signal.

---

### R4: objectName Keep/Remove List Missing (MEDIUM)

**Source**: Technical Auditor
**Finding**: Plan said "remove objectName declarations used only for findChild" but didn't specify which.

**Evidence**: Audited all `objectName` values in QML. `messagePopup`, `selectBar`, `videoFullscreenOverlay` — ONLY used by Python findChild. `stackView`, `topBar`, `lidarOverlay` — used by QML/JS navigation code.

**Verdict**: VALID. Explicit list added to Task 1.2.

---

### R5: Silent Undefined on Singleton Typos (HIGH)

**Source**: Systems Architect
**Finding**: QML silently returns `undefined` when accessing a misspelled singleton. No crash, no console error. Dangerous for robotic control.

**Verdict**: VALID. Added POST-1 validation task: loop through all expected singleton names and verify `engine.singletonInstance()` returns non-null.

---

### R6: Task 1.7 Too Large (HIGH)

**Source**: Technical Auditor
**Finding**: 10 controller registrations + 20+ QML file changes in one task exceeds reasonable LLM context window.

**Verdict**: VALID. Split into 1.7a (ESP32, Lidar, SSH, Video, BaseTopView) and 1.7b (Recorder, Overlay, Action, Steam).

---

### R7: Task 1.10/1.9 Wrong Order (MEDIUM)

**Source**: Technical Auditor
**Finding**: Versionless imports (1.10) should be done BEFORE qmldir creation (1.9) so qmldir files are written consistently.

**Verdict**: VALID. Reordered in dependency graph.

---

### R8: qmldir Namespace Collision Risk (MEDIUM)

**Source**: Technical Auditor
**Finding**: If `core/qmldir` declares bare `module PaintController`, it collides with the singleton registration URI.

**Verdict**: VALID. Added guard: all qmldir must use dotted names like `PaintController.Core`. Verification: `grep -rn "^module PaintController$"` → 0 hits.

---

### R9: Task 1.11 Dependency Underspecified (MEDIUM)

**Source**: Technical Auditor
**Finding**: Required properties depend on ALL controller migrations (1.0-1.8) AND qmldir (1.9), not just 1.9.

**Verdict**: VALID. Fixed in dependency graph.

---

### R10: Need Machine-Verified QML Mapping (MEDIUM)

**Source**: Technical Auditor
**Finding**: The context property → QML file mapping table is manually compiled. If wrong, a QML file silently breaks.

**Verdict**: VALID. Added PRE-1 task: generate fresh mapping via grep and compare.

---

### R11: Screen.pixelDensity Fails in QtObject Singleton (CRITICAL)

**Source**: Both agents
**Finding**: CommonStyle is `pragma Singleton` + `QtObject` with no parent Window. `Screen` is an attached type that requires being inside a visual hierarchy. `Screen.pixelDensity` will be `undefined` or produce a runtime error.

**Evidence**: CommonStyle has no `Item`, no `Window`, no visual tree parent. `Screen` literally cannot attach.

**Verdict**: CONFIRMED CRITICAL. Task 2.0 rewritten to use Python-side `QGuiApplication.primaryScreen().physicalDotsPerInch()` or MainWindow.qml `Component.onCompleted` injection.

---

### R12: Winch Safety Checks Vague (MEDIUM)

**Source**: Technical Auditor
**Finding**: Task 0.4 said "either re-enable or add a comment." Auditor found the disabled code uses `print()`, while active checks use `logger.warning()`.

**Evidence**: 4 methods with `# if not self._available: print(...)` patterns. Active methods `command_speed_rpm/mmps` DO check availability.

**Verdict**: VALID. Specified: re-enable all 4, replace `print()` with `logger.warning()`, return False.

---

### R13: QtBridge SRP Concern (MEDIUM)

**Source**: Systems Architect
**Finding**: QtBridge handles popups + navigation + video overlay + multi-screen + lidar overlay. Adding 3 more signals worsens SRP violation.

**Verdict**: VALID but DEFERRED. User decision: handle in Phase 4. Document as known debt. Splitting now adds 2-3 tasks to Phase 1 without clear benefit.

---

## DISMISSED FINDINGS (No plan changes)

### D1: Facade Pattern for 26 Singletons (Architect)

**Proposal**: Group into 3-4 facade singletons (`HardwareController`, `UIServices`, `Backend`, `WorkflowEngine`).

**Why dismissed**: Breaks PySide6/QML property binding model. A facade would require re-exposing every Property as a pass-through OR exposing child objects as `QObject*` properties (functionally identical to separate singletons with extra indirection). Signal routing through facades adds complexity, not clarity.

---

### D2: Hybrid @QmlSingleton + qmlRegisterSingletonInstance (Architect)

**Proposal**: Use `@QmlSingleton` for controllers with no constructor args.

**Why dismissed**: Only 3 of ~20 controllers (15%) qualify (WarningHandler, SystemMonitor, ScreenManager). Two registration paradigms in one codebase is worse than one consistent approach. `@QmlSingleton` means the QML engine creates the singleton, losing factory control.

---

### D3: Python→QML Signal Dangling References (Architect)

**Claim**: Replacing findChild with signals creates memory leak risk when QML components are destroyed by Loader.

**Why dismissed**: The plan already uses QML-side `Connections {}` blocks, NOT Python-side `.connect()`. QML `Connections` are child objects of the component — they auto-disconnect when the component is destroyed. Verified in the plan's "Target Signal Pattern" reference code.

---

### D4: Interface Segregation for QML (Architect)

**Claim**: QML components use a small subset of controller properties; should expose narrower interfaces.

**Why dismissed**: PySide6 Property bindings are lazy — unused properties consume nothing. Creating proxy objects would add complexity without benefit. QML's binding model naturally provides interface segregation.

---

### D5: cleanup() Missing warning_handler/action_config (Original plan)

**Claim**: ControllerBundle.cleanup() omits `warning_handler` and `action_config`.

**Why dismissed**: Verified — neither `WarningHandler` nor `ActionConfigPython` has a `cleanup()` method. The `cleanup()` method uses `hasattr(ctrl, 'cleanup')` guard. Omissions are correct.

---

### D6: RobotController External Consumers (Auditor)

**Claim**: RobotController is publicly exported in `__init__.py`; external consumers might break.

**Why dismissed**: Verified — zero references in `launch/`, `tests/`, `scripts/`, or `fish-eye/`. The C++ `RobotController` (in `src/paint_controller.cpp`) is a completely separate class. Safe to delete.

---

## DEFERRED FINDINGS (Future consideration)

### F1: ControllerBundle → Registry Pattern (Architect)

Currently adding a controller requires modifying 4 files (ControllerBundle, cleanup(), create_controllers(), application.py). A registry pattern reduces this to 1 file. Good idea but not blocking Phase 1.

**When**: Consider alongside Phase 1 migration, don't mandate.

---

### F2: ROS2 Abstraction for Testability (Architect)

Controllers hard-couple to `rclpy.Node` — testing requires full ROS2 initialization. Inject pub/sub factories for testability.

**When**: Phase 3 test infrastructure (Task 3.1 / 3.6 / 3.7).

---

### F3: Lazy Controller Initialization (Architect)

Some controllers (LidarController, RosBagRecorder, ScreenRecorder) are rarely used but initialized at startup.

**Why deferred**: ROS2 subscription setup is cheap. Heavy items (BaseTopViewService, VideoStreamHandler) are already conditionally activated. Negligible startup cost.

---

## Risk Matrix (Phase 1)

| Task | Risk | Key Concern |
|------|------|-------------|
| 1.0 StateStore | LOW | 4 QML files, establishes pattern |
| 1.1 SettingsManager | LOW | 3 QML files |
| 1.2 QtBridge + findChild | **HIGH** | Signal replacement + input.py + MainWindow central |
| 1.3 Isolated controllers | MEDIUM | 6 registrations, batch error risk |
| 1.4 wheelController | MEDIUM | 7 QML files |
| 1.5 teensyController | MEDIUM | 7 QML files |
| 1.6 winchController | **HIGH** | 11 QML files, highest spread |
| 1.7a controllers batch A | MEDIUM | 5 registrations |
| 1.7b controllers batch B | MEDIUM | 5 registrations |
| 1.8 Workflow handlers | MEDIUM | 5 QML files |
| 1.10 Versionless imports | LOW | Mechanical sed replace |
| 1.9 qmldir manifests | **HIGH** | ~20 new files, naming critical |
| 1.11a-e Required props | MEDIUM | Breaking change per `required` addition |
