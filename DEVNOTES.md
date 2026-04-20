# Development Notes

---

### 2026-04-21 - Qt Fixture Stabilisation + Safety-Critical Test Coverage

**Goal**: Stop the full test suite from aborting; add first-principles coverage for the two largest untested modules (ControlProcessor, QtBridge)
**Issues**:
- `QT_QPA_PLATFORM=xcb` was already set in the VS Code terminal environment; conftest used `setdefault` so it was never overridden → `QApplication([])` aborted with "could not connect to display"
- `qt_core_app` created an independent `QCoreApplication`; if resolved before `qt_app`, subsequent `QApplication` creation also aborted (mutual exclusion)
- `test_input_handler.py` tests had no explicit `qt_app` fixture dependency — worked only when another file's session fixture happened to run first
- `FakePublisher.publish()` accepted any Python object (no type enforcement)
- `FakeRosBus.publish()` passed the same object reference to all subscribers (real DDS serializes)
**Tried**:
- Changed `os.environ.setdefault(...)` → `os.environ["QT_QPA_PLATFORM"] = "offscreen"` (force override)
- Made `qt_core_app` an alias of `qt_app` to guarantee exactly one application instance
- Added `_flush_qt_events` autouse fixture (calls `app.processEvents()` after each test)
- Added `assert isinstance(message, self.msg_type)` to `FakePublisher.publish()`
- Added `copy.copy(msg)` in `FakeRosBus.publish()` before delivering to subscribers
**Result**: ✅ `python/paint_controller/venv/bin/python -m pytest tests -q` → 99 passed, 1 pre-existing failure (test_winch logger routing). Suite went from aborting at test 9 to 100 collected tests.  Added 31 ControlProcessor tests (track deadzone/nonlinearity/clamping/dispatch, winch guards/locks/activation-gate, wheel travel accumulation/clamping/deferral) and 13 QtBridge tests (signal emission, video source selection, null-safe deferred wiring)
**Files**: `tests/conftest.py`, `tests/fakes.py`, `tests/test_input_handler.py`, `tests/test_test_infrastructure.py`, `tests/test_control_processor.py` (new), `tests/test_qt_bridge.py` (new)

### 2026-04-20 02:05 - Pre-Commit Documentation Sync And LLM Navigation Cleanup

**Goal**: Make the documentation set truthful and easier to navigate before committing the current implementation batch
**Issues**: README and plan docs still mixed an older historical `42 passed` full-suite claim with the current Qt fixture abort, the README test inventory lagged behind the new `StateStore`/`SettingsManager`/`UIInputHandler` coverage, and fresh sessions could still miss the existing `docs/plan/00_README.md` index
**Tried**: Reconciled validation wording across the README and master plan, promoted `docs/plan/00_README.md` as the canonical LLM session-start index instead of adding a second index file, and softened a couple of overstated completion notes to match the real repo state
**Result**: ✅ The active docs now agree on the current validation state, new sessions have a clearer navigation entry point, and the repo can be committed without claiming a fully green local test suite that is not yet true in this terminal
**Files**: `README.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/04_AUDIT_REPORT.md`

### 2026-04-20 01:15 - Finish qmldir Rollout, Core Runtime Tests, and Display Tokenization

**Goal**: Complete Tasks `1.9`, `3.2`, and `2.3` without destabilizing the current relative-import QML runtime or the terminal-safe pytest path
**Issues**: The repo still lacked `qmldir` coverage in most QML directories, had no direct runtime tests for `StateStore` or `SettingsManager`, and `components/displays/` still bypassed `CommonStyle` heavily. A full `tests/` run in this shell still aborts when the `qt_app`/`QApplication` fixture path is exercised
**Tried**: Added type-export `qmldir` files across the missing directories without introducing new `module ...` declarations, added a `paint_controller.core` namespace stub plus `qt_core_app` fixture, wrote direct runtime tests for `StateStore` and `SettingsManager`, and tokenized the full display folder against `CommonStyle`
**Result**: ✅ Task `1.9` is complete with safe `qmldir` coverage, Task `3.2` now has direct runtime coverage, Task `2.3` is functionally complete across the display folder, and targeted venv validation for the new core/settings/input test batch reports `17 passed`
**Files**: `python/paint_controller/qml/**/qmldir`, `python/paint_controller/qml/components/displays/*.qml`, `tests/conftest.py`, `tests/test_state_store.py`, `tests/test_settings_runtime.py`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/03_QML_BINDINGS.md`

### 2026-04-20 00:20 - Align Plan Docs With Remaining Safety Fixes

**Goal**: Eliminate the last Python-side popup `findChild()` lookup, re-enable the remaining winch move-command safety guards, and bring the plan docs back into exact agreement with the live code
**Issues**: The documentation already claimed both fixes were complete, but `handlers/input.py` still closed the popup through `findChild()` and `controllers/winch.py` still had four commented-out availability guards on move commands
**Tried**: Switched `UIInputHandler` to use the already-injected `close_popup_fn`, removed the dead popup/object-name wiring, re-enabled the four winch guards with logger warnings and early `False` returns, then updated the plan docs and task record to reflect the now-true runtime state
**Result**: ✅ Python now has zero `findChild()` calls, winch move commands refuse unavailable hardware again, the active plan files no longer overstate unfinished work, and `UIInputHandler` now has focused regression coverage for popup-close + mode-switch behavior
**Files**: `python/paint_controller/handlers/input.py`, `python/paint_controller/controllers/winch.py`, `tests/test_input_handler.py`, `PLANNING.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/plan/03_QML_BINDINGS.md`, `docs/plan/04_AUDIT_REPORT.md`

### 2026-04-20 00:35 - Normalize QML Imports To Versionless Qt6 Style

**Goal**: Complete Task `1.10` by removing version pins from Qt module imports across the QML tree before starting the broader `qmldir` rollout
**Issues**: The tree still mixed `QtQuick 2.15`, `QtQuick.Controls 2.15`, `QtQuick.Layouts 1.15`, and a leftover `QtGraphicalEffects 1.15` import in `PageSpray.qml`
**Tried**: Applied a mechanical tree-wide import rewrite for the Qt6 modules, then converted the final graphical-effects import to `Qt5Compat.GraphicalEffects` and updated the active plan docs to mark `1.10` complete
**Result**: ✅ The QML tree now uses versionless Qt imports consistently, leaving `qmldir` expansion as the next structural cleanup step rather than import syntax churn
**Files**: `python/paint_controller/qml/**/*.qml`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/03_QML_BINDINGS.md`

### 2026-04-17 23:30 - Synchronize README And Plan Docs To Current Runtime

**Goal**: Bring the root README and `docs/plan/*` back in sync with the implemented runtime, test model, and modernization status
**Issues**: The docs still described older migration intent, stale bridge debt, and outdated test workflow details even though the repo had already shifted to context-property runtime exposure and layered pytest coverage
**Tried**: Rewrote `README.md` around current setup/run/test flow, updated the plan entry docs and master tracker, replaced stale `findChild()`/singleton-migration language with the live bridge state, and documented the layered test suite plus the then-current `42 passed` local result
**Result**: ✅ Documentation reflected the runtime and test direction at that point; later sessions added more coverage and replaced the earlier full-suite pass claim with the current targeted-pass-plus-fixture-blocker status
**Files**: `README.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/plan/03_QML_BINDINGS.md`, `docs/plan/04_AUDIT_REPORT.md`

### 2026-04-17 23:05 - Normalize Existing Test Files By Test Layer

**Goal**: Align the current test suite with the layered testing model before adding new tests
**Issues**: The pure utility and schema files still used older class-wrapper patterns that obscured the real unit boundary, while the newer controller tests already followed a clearer behavior-first style
**Tried**: Flattened pure utility/schema tests into module-level behavior functions, kept the shared harness file explicitly scoped to test primitives, and left the controller plus ROS integration files on their existing component/transport split
**Result**: ✅ Existing tests now read more consistently by boundary: pure logic, harness validation, component behavior, and real ROS transport; the full suite still passed at that point in the repo timeline
**Files**: `tests/test_crc.py`, `tests/test_input_utils.py`, `tests/test_settings_schema.py`, `tests/test_test_infrastructure.py`

### 2026-04-17 22:20 - Add Transport-Level Controller Validation

**Goal**: Make controller tests more meaningful by verifying that a second node subscribed to the same topic actually receives the published command
**Issues**: The existing safety tests only asserted that fake publishers stored messages, which proves controller intent but not pub/sub delivery semantics
**Tried**: Extended `tests/fakes.py` with a shared in-process topic bus, added an infrastructure test proving node-to-node delivery, added a `WinchController` fake-bus transport test, and added a real `rclpy` pub/sub test that spins a subscriber node until it receives the message
**Result**: ✅ The test harness now has both a fast transport layer for routine controller tests and a real ROS pub/sub validation path for command delivery
**Files**: `tests/fakes.py`, `tests/test_test_infrastructure.py`, `tests/test_winch.py`, `tests/test_winch_ros_integration.py`, `PLANNING.md`

### 2026-04-17 22:00 - Add WinchController Safety Tests

**Goal**: Continue the safety-critical test phase with focused coverage for `WinchController`
**Issues**: `WinchController` imports ROS and message modules at import time, so the test interpreter needed lightweight module stubs; the tests also needed to validate both availability guards and the settings-driven speed clamp behavior without a live ROS system
**Tried**: Extended `tests/conftest.py` with a namespace-only `paint_controller.controllers` package plus minimal test stubs for `rclpy.node`, `std_msgs.msg`, and `paint_interfaces.msg`, then added focused tests for command rejection, move-command guards, clamp behavior, enable publishing, and settings updates
**Result**: ✅ Winch safety behavior is now covered by unit tests and can run in the project venv without ROS runtime dependencies
**Files**: `tests/conftest.py`, `tests/test_winch.py`, `docs/plan/01_MASTER_PLAN.md`, `PLANNING.md`

### 2026-04-17 21:40 - Add EmergencyButtonHandler Safety Tests

**Goal**: Start the safety-critical test phase with focused coverage for `EmergencyButtonHandler`
**Issues**: Importing `paint_controller.handlers.emergency` through the package path would execute `handlers/__init__.py` and drag in the full handler stack; during test design it also became clear the emergency trigger stopped the winch and spray trigger but did not stop the wheel controller
**Tried**: Extended `tests/conftest.py` with a namespace-only `paint_controller.handlers` package for direct submodule imports, added focused tests around hold/cancel/trigger/cooldown behavior, and updated `EmergencyButtonHandler` to call the wheel emergency stop path during trigger
**Result**: ✅ Emergency behavior is now covered by unit tests and the handler stops the wheel controller as intended during emergency activation
**Files**: `tests/conftest.py`, `tests/test_emergency.py`, `python/paint_controller/handlers/emergency.py`, `docs/plan/01_MASTER_PLAN.md`, `PLANNING.md`

### 2026-04-17 21:15 - Phase A Cleanup: Remove Dead Launch/Test Config And Archive Prototype

**Goal**: Remove obsolete repository artifacts so the plan and codebase match the current runtime architecture
**Issues**: The repo still contained a dead C++ launch file for a non-built executable, a redundant `pytest.ini` that duplicated `pyproject.toml`, and the archived `fish-eye/` prototype even though its logic had already been ported into `base_top_view_service.py`
**Tried**: Deleted the dead launch file and redundant pytest config, removed the fish-eye prototype contents, cleaned stale singleton-migration guidance from the plan docs, and updated code/comments that still referenced the removed prototype or pytest config
**Result**: ✅ Phase A non-destructive cleanup is complete and the approved destructive cleanup has removed the obsolete files; only empty fish-eye directories may remain because directory removal commands are blocked by the tool policy
**Files**: `launch/paint_controller_cpp.launch.py`, `pytest.ini`, `fish-eye/*`, `python/paint_controller/core/qt_bridge.py`, `python/paint_controller/core/ros_node.py`, `python/paint_controller/handlers/warnings.py`, `python/paint_controller/services/base_top_view_service.py`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/03_QML_BINDINGS.md`, `PLANNING.md`

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
