# Master Plan: Shrink the QML Runtime Surface

> **Status**: Phase 8 completed. The core QML surface retirement program (Phases 0–8) is finished.  
> **Branch**: `qml-surface-retirement-phase-0`  
> **Goal**: Retire raw controller/handler context properties and replace them with bounded, feature-root Python models so QML stays declarative and Python owns policy.

This plan is sliced into self-contained sessions. Each phase can be completed, validated, and committed independently. Future sessions should read this file first, then check `docs/plan/00_ARCHITECTURE_PROGRESS.md` for the live execution board.

---

## Guiding principles

1. **Retire before adding.** Every new model must remove at least one raw QML read path in the same slice.
2. **No shallow wrappers.** A new model must own real policy (admin gating, logging, error handling, dispatch). If it only forwards calls, do not create it.
3. **No controller-shaped mirrors.** Do not expose one slot per controller method.
4. **One canonical Python owner per operator-visible behavior.**
5. **Measure surface area, not class count.** Track `_EXPECTED_CONTEXT_PROPERTY_NAMES` and raw controller references in QML.
6. **Follow project validation gates.** Run the focused test band for every touched family; update startup smoke fakes when a contract changes.

---

## Success metrics

- Reduce root-context property count from ~33 to ~12–15.
- Eliminate direct QML reads of `*Controller` objects and handler taxonomies (`deviceActionHandler`, `winchMotionHandler`, etc.).
- All QML actions use feature-root models (`wheelActions`, `winchActions`, `tuningActions`, etc.).
- Startup smoke tests derive their contract from production wiring (automated parity check).

---

## Phase overview

| Phase | Focus | Est. sessions | Risk |
|---|---|---|---|
| 0 | Contract-parity harness + cleanup | 1 | Low |
| 1 | Winch family (`winchActions`) | 1 | Low |
| 2 | Wheel family (`wheelActions`) | 1 | Low |
| 3 | Tuning family (`tuningActions`) | 1 | Low |
| 4 | Base top-view family (`baseTopViewActions`) | 1 | Medium |
| 5 | Device operations split | 1–2 | Medium |
| 6 | Remaining raw status controllers retirement | 1–2 | Medium |
| 7 | `MainWindow.qml` shell simplification (optional) | 2–3 | High |
| 8 | `AppRuntime` wiring extraction (optional) | 1–2 | Medium |

Phases 0–6 are the core refactor. Phases 7–8 are follow-on maintainability work and can be deferred.

---

## Phase 0: Contract-parity harness and cleanup

### Goal

Make the QML contract drift-visible and fix shallow issues before adding new models.

### Files

- `python/paint_controller/core/app_runtime.py`
- `tests/startup_smoke_support.py`
- `tests/test_app_runtime_runtime.py`
- `python/paint_controller/qml/MainWindow.qml`

### Steps

1. Add a harness test that compares `_EXPECTED_CONTEXT_PROPERTY_NAMES` against the keys produced by `startup_smoke_support._context_objects()` and the actual `ControllerBundle` fields. Fail if a property is added/removed without updating the smoke fixture.
2. Fix the `MainWindow.qml` `visible` + `visibility` conflict (use `visibility` only).
3. Remove the duplicate `core/CommonStyle.qml` singleton; point all imports to `theme/CommonStyle`.
4. Add teardown regression tests for `BaseTopViewService`, `OverlayController`, and `SteamDeckHandler` if not present.

### Validation gates

- `python/paint_controller/venv/bin/python -m pytest tests/test_app_runtime_runtime.py tests/test_startup_smoke*.py tests/test_qml_imports.py -q` passes.
- New contract-parity test passes.
- `qmllint` warnings do not increase.

### Completion criteria

- Any future change to `_EXPECTED_CONTEXT_PROPERTY_NAMES` must update `startup_smoke_support.py` or the parity test fails.
- `MainWindow.qml` no longer mixes `visible` and `visibility`.

### Completed

- Branch: `qml-surface-retirement-phase-0`
- Validation: focused band `45 passed`; full suite `276 passed`; `qmllint` clean; pyright clean on touched Python files.
- Notes: `OverlayController.cleanup()` uses a `_cleaned_up` guard rather than explicit signal disconnects to avoid PySide6 `SignalInstance.disconnect()` warnings when multiple slots are connected.

---

## Phase 1: Winch family

### Goal

Create `winchActions` and retire `winchMotionHandler` from the QML context.

### Rationale

Smallest handler, single QML consumer (`PageWinch.qml`), clear feature boundary. Good warm-up slice.

### Files

- New: `python/paint_controller/models/winch_actions.py`
- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `python/paint_controller/qml/pages/winch/PageWinch.qml`
- Modify: `tests/startup_smoke_support.py`
- Modify: `tests/test_app_runtime_runtime.py`

### Steps

1. Create `_WinchActions` (or `WinchActions` in `models/winch_actions.py`) that absorbs the policy currently in `WinchMotionHandler`:
   - `moveIncrement(lengthMm, speedMmS)`
   - `moveAbsolute(lengthMm, speedMmS)`
   - `retractFull()`
   - `extendOneMeter()`
   - `emergencyStop()`
   - Own admin-gate checks, logging, error emission.
2. Keep `WinchMotionHandler` as an internal implementation detail or merge it into the new model. If merged, update `ControllerBundle` and `controller_factory.py`.
3. Add `winchActions` to `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`.
4. Update `PageWinch.qml` to call `winchActions.*` instead of `winchMotionHandler.*`.
5. Remove `winchMotionHandler` from context properties and from `startup_smoke_support.py`.
6. Add/update focused tests for `WinchActions`.

### Validation gates

- `tests/test_startup_smoke*.py` pass.
- `tests/test_app_runtime_runtime.py` passes.
- Winch-focused tests pass.
- `qmllint` passes.

### Completion criteria

- `winchMotionHandler` no longer appears in `_EXPECTED_CONTEXT_PROPERTY_NAMES`.
- `PageWinch.qml` contains no `winchMotionHandler` references.

---

## Phase 2: Wheel family

### Goal

Create `wheelActions` and retire `wheelController` plus wheel-related `deviceActionHandler` calls from QML.

### Files

- New: `python/paint_controller/models/wheel_actions.py`
- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `python/paint_controller/handlers/device_actions.py`
- Modify: `python/paint_controller/qml/pages/wheel/PageWheel.qml`
- Modify: `tests/startup_smoke_support.py`
- Modify: `tests/test_app_runtime_runtime.py`

### Steps

1. Create `_WheelActions` with slots:
   - `setEnabled(enabled)`
   - `resetPosition()`
   - Own admin-gate checks, logging, error emission.
2. Move wheel action policy out of `DeviceActionHandler` (remove `requestWheelEnabled`, `resetWheelPosition`, `toggleWheelEnable`) into `_WheelActions`.
3. Add `wheelActions` to context properties.
4. Update `PageWheel.qml` to use `wheelActions` and `wheelStatus` only; remove `wheelController` and `deviceActionHandler` references.
5. Remove `wheelController` from context properties and smoke fakes.
6. Update `DeviceActionHandler` tests to no longer expect wheel methods.

### Validation gates

- `tests/test_startup_smoke*.py` pass.
- `tests/test_app_runtime_runtime.py` passes.
- Wheel/controller tests pass.
- `qmllint` passes.

### Completion criteria

- `wheelController` and wheel methods of `deviceActionHandler` removed from QML.
- `PageWheel.qml` only uses `wheelStatus` and `wheelActions`.

---

## Phase 3: Tuning family

### Goal

Create `tuningActions` and retire `tuningAdminHandler`. Also retire direct `teensyController.all_status` reads in `PageTuning.qml`.

### Files

- New: `python/paint_controller/models/tuning_actions.py`
- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `python/paint_controller/handlers/tuning_admin.py`
- Modify: `python/paint_controller/qml/pages/tuning/PageTuning.qml`
- Modify: `python/paint_controller/qml/pages/status/components/TeensyStatus.qml` (if it reads `teensyController.all_status`)
- Modify: `tests/startup_smoke_support.py`
- Modify: `tests/test_app_runtime_runtime.py`

### Steps

1. Create `_TuningActions` with slots:
   - `setShortYawPid(p, i, d)`
   - `setLongYawPid(p, i, d)`
2. Extend `_TeensyStatus` (or add `_TuningStatus`) to expose tuning-relevant read-only properties currently read from `teensyController.all_status`: `imuYaw`, `yawCommand`, `yawPidP`, etc.
3. Merge or replace `TuningAdminHandler` with `_TuningActions`.
4. Update `PageTuning.qml` to use `teensyStatus.*` and `tuningActions.*`.
5. Remove `tuningAdminHandler` from context properties and smoke fakes.
6. Add/update tests for `_TuningActions`.

### Validation gates

- Startup smoke tests pass.
- `test_app_runtime_runtime.py` passes.
- Tuning tests pass.
- `qmllint` passes.

### Completion criteria

- `tuningAdminHandler` removed from QML context.
- `PageTuning.qml` contains no `teensyController.all_status` references.

---

## Phase 4: Base top-view family

### Goal

Create `baseTopViewActions` and retire `baseTopViewAdminHandler`. Rationalize `baseTopViewController` and `baseStreamHandler` exposure.

### Files

- New: `python/paint_controller/models/base_top_view_actions.py`
- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `python/paint_controller/handlers/base_top_view_admin.py`
- Modify: `python/paint_controller/qml/overlays/video/components/BaseTopViewSettingsPopup.qml`
- Modify: `python/paint_controller/qml/pages/wheel/PageWheel.qml` (if it uses `baseStreamHandler`)
- Modify: `tests/startup_smoke_support.py`

### Steps

1. Create `_BaseTopViewActions` with slots:
   - `setZoom(value)`
   - `setOffsetX(value)`, `setOffsetY(value)`
   - `setCropEnabled(value)`
   - `setCropWidthRatio(value)`, `setCropCenterX(value)`
   - `setK1(value)` … `setK4(value)`
   - `saveSettings()`, `resetToDefaults()`
2. Consider exposing base-top-view status through `videoRuntime` or a dedicated `baseTopViewStatus` model instead of raw `baseTopViewController`.
3. Update `BaseTopViewSettingsPopup.qml` to use `baseTopViewActions` and the status model.
4. Remove `baseTopViewAdminHandler` and `baseTopViewController` from context properties if their status is fully covered.
5. Fix the `BaseTopViewService` teardown issue: disconnect `stream.frameReady` from `worker.process_frame` before quitting the worker thread.
6. Add/update tests and teardown regression coverage.

### Validation gates

- Startup smoke tests pass.
- `test_app_runtime_runtime.py` passes.
- Base-top-view tests pass.
- `qmllint` passes.

### Completion criteria

- `baseTopViewAdminHandler` removed from QML context.
- `BaseTopViewSettingsPopup.qml` only uses bounded models.

---

## Phase 5: Device operations split

### Goal

Dissolve `deviceOperationsHandler` into feature-root models without creating shallow mirrors.

### Rationale

`DeviceOperationsHandler` mixes several concerns: teensy toggles, winch load detection, recording toggles, lidar power, error clear. This phase requires the most design care.

### Proposed grouping

- `recordingActions`
  - `toggleEndEffectorRecording()`
  - `toggleBaseRecording()`
  - `toggleScreenRecording()`
  - `toggleRosBagRecording()`
- `teensyActions`
  - `toggleStability()`, `toggleYaw()`, `toggleAutoCorrection()`
  - `toggleSprayGunLeveling()`, `toggleRollerSteering()`
  - `toggleSwingDamping()`, `toggleSprayGunLed()`
  - `setLidarPower(enabled)`
- Move winch load detection into `winchActions` from Phase 1.
- Move `clearErrors()` into a small `systemActions` or keep it in `systemControlServices` if appropriate.

### Files

- New: `python/paint_controller/models/recording_actions.py`
- New: `python/paint_controller/models/teensy_actions.py`
- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `python/paint_controller/handlers/device_operations.py`
- Modify: `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`
- Modify: `tests/startup_smoke_support.py`

### Steps

1. Create the two (or three) action models, each owning admin-gate, logging, and dispatch.
2. Remove the corresponding methods from `DeviceOperationsHandler` or retire the handler entirely.
3. Update `DeviceControlTab.qml` to use the new models.
4. Update context properties and smoke fakes.
5. Add/update tests.

### Validation gates

- Startup smoke tests pass.
- `test_app_runtime_runtime.py` passes.
- Device operations tests pass.
- `qmllint` passes.

### Completion criteria

- `deviceOperationsHandler` removed from QML context.
- `DeviceControlTab.qml` uses only feature-root action models.

---

## Phase 6: Remaining raw controller retirement

### Goal

Retire the remaining raw controllers from the QML context: `teensyController`, `esp32ValveController`, `lidarController`, `controlProcessor`, `systemMonitor`, `screenRecorder`, `rosBagRecorder`, `screenManager`, `baseStreamHandler`.

### Files

- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`
- Modify: `tests/startup_smoke_support.py`
- Modify: `tests/test_app_runtime_runtime.py`

### Steps

1. Ensure every direct read has a bounded model:
   - `teensyController.all_status.*` → `teensyStatus` (already mostly done).
   - `esp32ValveController.*` → `valveStatus` (already exists).
   - `lidarController.*` → `lidarStatus` (already exists).
   - `controlProcessor`, `systemMonitor` → these should likely not be exposed to QML at all; check if any QML file uses them.
   - `screenRecorder`, `rosBagRecorder` → `recordingStatus` (already exists).
   - `screenManager` → `shellState` or keep as internal if only used by `MainWindow.qml` for screen geometry.
   - `baseStreamHandler` → `videoRuntime`.
2. Remove each retired name from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`.
3. Update QML consumers and smoke fakes.

### Validation gates

- Full startup smoke suite passes.
- `test_app_runtime_runtime.py` passes.
- Full pytest suite passes.
- `qmllint` passes.

### Completion criteria

- The nine retired names are removed from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`.
- No QML file references `teensyController`, `esp32ValveController`, `lidarController`, `controlProcessor`, `systemMonitor`, `screenRecorder`, `rosBagRecorder`, `screenManager`, or `baseStreamHandler`.

### Completed

- Extended `_TeensyStatus` with rails, propellers, and spray-gun details previously read from `teensyController.all_status`; updated `TeensyStatus.qml` to use `teensyStatus.*`.
- Repointed `PageWheel.qml` to `videoRuntime.feeds` for base frame signals.
- Repointed `MainWindow.qml` to `shellState` for screen-count changes.
- Removed the nine retired globals from the app-scope QML context and startup-smoke fixtures.
- Validation: focused band `48 passed`; full suite `294 passed`; `qmllint` clean.

---

## Phase 7: MainWindow.qml shell simplification (optional)

### Goal

Move routing and multi-screen policy out of `MainWindow.qml` and into Python models.

### Files

- New: `python/paint_controller/models/shell_router.py`
- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `python/paint_controller/qml/MainWindow.qml`

### Steps

1. Create `ShellRouter` Python model with `currentRoute` property and `navigateTo(route)` slot.
2. Move page registry and route order from `MainWindow.qml` into `ShellRouter`.
3. Update `MainWindow.qml` to bind `StackView` to `shellRouter.currentRoute`.
4. Move multi-screen window lifecycle to Python or a dedicated `MultiScreenHost.qml`.
5. Remove the `backend` signal handlers that imperatively toggle fullscreen video; route through `overlayHost`/`videoRuntime`.

### Validation gates

- All startup smoke tests pass.
- Full pytest suite passes.
- Manual smoke: app launches, navigation works, dual-screen mode works.

### Completed

- Created `ShellRouter` in `python/paint_controller/models/shell_router.py` owning the route registry, `currentRoute`, `currentRouteOrder`, `navigateTo()`, and `routeOrder()`.
- Created `python/paint_controller/qml/core/MultiScreenHost.qml` to encapsulate secondary window creation, placement, and destruction.
- Updated `MainWindow.qml` to bind navigation to `shellRouter`, kept a minimal route-to-component map, and removed inline multi-screen lifecycle code.
- Wired `qt_bridge.toggleVideoOverlayRequested` → `overlay_host.toggle_video_fullscreen(source)` and `qt_bridge.updateVideoSourceRequested` → `overlay_host.set_video_fullscreen_source(source)` in `AppRuntime._wire_signals()`, removing the backend `Connections` handlers from QML.
- Removed the unused `winchController` context global from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`.
- Updated `SelectBar.qml` to consume `shellRouter` directly; added `FakeShellRouter`/`FakeShellState` to startup-smoke fixtures and added `tests/test_shell_router.py`.
- Validation: focused band `45 passed`; full suite `300 passed`; `qmllint` clean; `shell_router.py` pyright clean.

---

## Phase 8: AppRuntime wiring extraction (optional)

### Goal

Keep `AppRuntime` as a thin composition root; move context-property building and signal wiring into focused helpers.

### Files

- New: `python/paint_controller/core/qml_context_composer.py`
- New: `python/paint_controller/core/signal_wiring.py`
- Modify: `python/paint_controller/core/app_runtime.py`
- Modify: `tests/test_app_runtime_runtime.py`

### Steps

1. Extract `_EXPECTED_CONTEXT_PROPERTY_NAMES`, `_build_context_properties()`, and status-wrapper creation into `QmlContextComposer`.
2. Extract signal connections (Steam Deck callbacks, status timer, fullscreen video wiring, etc.) into `SignalWiring`.
3. `AppRuntime` orchestrates: create objects → create composer/wiring → run → shutdown.
4. Update tests to exercise the new helpers directly.

### Validation gates

- Full pytest suite passes.
- Startup smoke tests pass.
- `colcon build` passes.

### Completed

- Created `python/paint_controller/core/qml_context_composer.py` owning `_EXPECTED_CONTEXT_PROPERTY_NAMES`, `_SystemControlServices`, all status-wrapper classes (`_VideoRuntime*`, `_RecordingStatus`, `_ShellConnectivityStatus`, `_LauncherAdmin`, `_*Status`), helper functions, and `QmlContextComposer.compose()`.
- Created `python/paint_controller/core/signal_wiring.py` owning `SignalWiring.wire()` (Steam Deck callbacks, emergency/video/fullscreen signal routing, wheel-error handler) and `SignalWiring.start_timers()` (status timer, system monitor, deferred video startup).
- Slimmed `python/paint_controller/core/app_runtime.py` from ~1650 lines to ~470 lines; it now orchestrates creation, composer/wiring invocation, context-property registration, and shutdown.
- Updated `tests/test_app_runtime_runtime.py` to source `_EXPECTED_CONTEXT_PROPERTY_NAMES` from `qml_context_composer` and to exercise `SignalWiring` directly.
- Added `tests/test_qml_context_composer.py` and `tests/test_signal_wiring.py` for focused coverage of the new helpers.
- Added `qml_context_composer.py` and `signal_wiring.py` to `pyrightconfig.json`; pyright clean on included scope.
- Validation: focused band `58 passed`; full suite `313 passed`; `qmllint` clean. `colcon build` still fails pre-existingly because the `resource/` directory is missing from the package root.

---

## Cross-cutting concerns

### pyright

Add new `models/*_actions.py` files to `pyrightconfig.json` and aim for strong typing. Avoid `Any` in new code.

### Tests

For every phase:
- Update `tests/startup_smoke_support.py` fake objects.
- Update `tests/test_app_runtime_runtime.py` property assertions.
- Add focused unit tests for new action models.
- If a phase touches timers/workers, add teardown regression tests following `tests/test_ssh.py`.

### DEVNOTES and tech-debt

After each phase, append a short `DEVNOTES.md` entry summarizing what changed, why, and validation results. Update `docs/tech-debt.md` when an item is resolved.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Shallow wrappers | Require each new model to own admin-gate + logging + dispatch. Reject pure forwarders. |
| Partial retirement | Strict “retire before add” rule per phase. Use grep to confirm no old references remain. |
| Smoke-test drift | Phase 0 contract-parity test prevents silent drift. |
| Hardware regression | Validate with focused tests; keep internal handler logic unchanged unless merging. |
| Large sessions | Each phase is bounded to one feature family. Stop at end of any phase. |

## Rollback

Each phase is self-contained. If a phase breaks validation, revert the files touched in that phase. The context-property list is additive during a phase (new model added, old one removed in same commit), so a single git revert restores the previous contract.

---

## Next-session checklist

When resuming this plan:

1. Read `docs/plan/00_ARCHITECTURE_PROGRESS.md` for the live board.
2. Confirm which phase is next.
3. Run the focused test band for the phase before changing anything.
4. Update this master plan file if the plan itself needs correction.
