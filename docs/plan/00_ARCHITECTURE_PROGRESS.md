# Architecture Progress

This file is the single live control board for unfinished architecture work.

Use this file for the current execution order, frozen contracts, quarantine rules, and validation gates.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for durable architecture rationale and historical stage context.

## Current Snapshot

- Overall status: in progress
- Active architecture program: QML surface retirement per `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`
- Most recent completed slice: Phase 7 MainWindow.qml shell simplification (`shellRouter`, `MultiScreenHost.qml`, removal of `winchController` context global) on 2026-07-24
- Core purpose: reduce global coupling, clarify ownership, shrink the app-scope QML contract, and make operator-visible behavior easier to trace
- First-principles rule: success means fewer permanent app-scope QML reads and fewer equal-owner concepts, not wrapper proliferation
- Last focused validation: `45 passed` for `tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_startup_smoke.py tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_qml_imports.py tests/test_shell_router.py` on 2026-07-24
- Last full-suite baseline: `300 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q` on 2026-07-24

## Live Board

### Now

- Phase 7 is complete. Deferred until the next phase is chosen or reprioritized.

### Next

- Phase 8 (`AppRuntime` wiring extraction, optional) or a higher-leverage retirement target.

### Later

#### Automation follow-on

- Do not open the downstream automation-contract wave until the app-scope QML contract is materially smaller than it is today.

### Frozen

- Key-first shell route identity owned in `MainWindow.qml`
- `ShellState` as the bounded shell policy owner
- `OverlayHostPolicy` as the bounded overlay host and layer owner
- `shellConnectivityStatus` for shell-facing telemetry
- `launcherAdmin` for Launcher admin actions
- `systemControlServices` for the touched workflow, editor, and command system-control family
- `videoRuntime` for the touched fullscreen control, feed, and top-bar family
- Rule: do not casually reopen these contracts unless a future slice proves a real retirement win that cannot be achieved within the current ownership boundary

## Quarantined Remainder

These files are allowed to keep temporary raw-global reads until their named family is active. They are explicit remainder, not architectural truth.

- `python/paint_controller/qml/pages/wheel/PageWheel.qml` — base preview seam remainder after wheel detail telemetry retirement

## Validation Gates

- Every slice must retire at least one raw app-scope QML read path in the same change.
- Every slice touching `python/paint_controller/core/app_runtime.py` must record the AppRuntime contract delta.
- No new contract may become a controller-shaped mirror, a generic device bag, or a raw `all_status` passthrough.
- If a slice changes a QML-facing contract, add or update startup smoke coverage for that contract.
- If a slice touches timers, worker pools, QThreads, controller cleanup, or QObject lifetime, add teardown-specific regression coverage before closing the slice.
- When a raw QML global loses its last live consumer, remove it from `AppRuntime` in the same slice.
- Startup-smoke fixtures for touched surfaces must stop providing retired globals once a slice lands so smoke coverage cannot silently mask fallback to the old context bag.

## Focused Validation Order

1. `tests/test_app_runtime_runtime.py` and `tests/test_controller_factory_runtime.py` for AppRuntime, shutdown, controller-factory, and retirement assertions
2. The touched startup-smoke surface files for page and feature-root contract parity, including `tests/test_startup_smoke.py`, `tests/test_startup_smoke_shell.py`, `tests/test_startup_smoke_home.py`, and `tests/test_startup_smoke_workflow_editor.py` as applicable
3. `tests/test_qml_imports.py` when the slice changes QML contract shape or feature-root composition
4. Focused handler or model tests for the touched family
5. `tests/test_ssh.py` or another teardown-specific band whenever the slice touches QObject lifetime or background workers

## Recent Validation Hardening

- Fullscreen overlay warning hardening is green at `26 passed` for `tests/test_startup_smoke.py`, `tests/test_qml_imports.py`, and `tests/test_workflow_runner.py`.
- SSH teardown crash coverage is green at `4 passed` for `tests/test_ssh.py`.

## Historical Completion Summary

- Stage 0 through Stage 4.5 are complete for the targeted families.
- Workstream A through Workstream D are complete for the targeted families.
- Workstream E landed the workflow/editor and command contract reduction, bounded video runtime slice, shared winch, teensy, wheel, and recording status slices, the shell/connectivity family through `shellConnectivityStatus` plus `launcherAdmin`, the page-level wheel detail retirement in `PageWheel.qml`, the page/shared-card winch detail retirement through `winchStatus`, the teensy/end-effector detail retirement through extended `teensyStatus` plus bounded `valveStatus`, the lidar/monitor telemetry retirement through bounded `lidarStatus`, and the fullscreen overlay telemetry retirement through existing `wheelStatus` plus `winchStatus`.
- The remaining PageHome preview/frame-refresh remainder is retired behind explicit `videoRuntime` ownership, and the supporting startup-smoke/runtime cleanup wave is in place to keep further large-file work bounded.
- Phase 0 of the QML surface retirement program completed the contract-parity harness, removed the `MainWindow.qml` `visible`/`visibility` conflict, retired the duplicate `core/CommonStyle.qml` singleton, and added teardown regression coverage.
- Phase 1 completed the winch family retirement: `winchActions` now owns winch motion policy; `winchMotionHandler` is removed from the QML context and the codebase.
- Phase 2 completed the wheel family retirement: `wheelActions` now owns wheel enable/reset policy; `wheelController` is removed from the app-scope QML context; wheel-related methods are removed from `DeviceActionHandler`.
- Phase 3 completed the tuning family retirement: `tuningActions` now owns yaw PID tuning policy; `tuningAdminHandler` is removed from the QML context and the codebase; `PageTuning.qml` no longer reads raw `teensyController.all_status`.
- Phase 4 completed the base top-view family retirement: `baseTopViewActions` now owns base-top view calibration policy and `_BaseTopViewStatus` owns the read-only calibration surface; `baseTopViewAdminHandler` and `baseTopViewController` are removed from the QML context; `BaseTopViewSettingsPopup.qml` and `BaseFrontOverlay.qml` use only bounded models; `BaseTopViewService.cleanup()` now disconnects `frameReady` before quitting the worker thread.
- Phase 5 completed the device operations split: `recordingActions` owns EF/base camera, screen, and ROS bag recording toggles; `teensyActions` owns Teensy feature toggles and lidar power; `systemActions` owns `clearErrors`; `winchActions` now also owns load detection; `DeviceOperationsHandler` is removed from the QML context and the codebase; `DeviceControlTab.qml` and `PageWinch.qml` use only the new feature-root models.
- Phase 6 completed the remaining raw controller retirement: `_TeensyStatus` now exposes rails, propellers, and spray-gun details previously read from `teensyController.all_status`; `TeensyStatus.qml` no longer reads `teensyController`; `PageWheel.qml` reads frame signals from `videoRuntime.feeds`; `MainWindow.qml` reads screen changes from `shellState`; the raw globals `teensyController`, `esp32ValveController`, `lidarController`, `controlProcessor`, `systemMonitor`, `screenRecorder`, `rosBagRecorder`, `screenManager`, and `baseStreamHandler` are removed from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and the QML context.
- Phase 7 completed the MainWindow.qml shell simplification: `ShellRouter` now owns the route registry, current route, and navigation slot; `MultiScreenHost.qml` owns the secondary window lifecycle; `MainWindow.qml` uses `shellRouter` for navigation and defers multi-screen window management to `MultiScreenHost`; backend fullscreen-video toggle/update signals are wired directly to `overlayHost` in Python; the unused `winchController` context global is removed.

## Active Risks

- The app-scope QML context contract is still broader than it should be for a professional Qt program.
- Some feature roots now have bounded contracts while leaf components still bypass them, which can create false progress if later slices only rename access.
- The remaining telemetry families must stay family-based and bounded; otherwise the repo can drift from one large context bag into many narrow-but-permanent bags.
- Harness drift remains a real risk, especially where startup smoke still injects raw globals that a landed slice should no longer depend on.

## Next Session Checklist

1. Keep the live board in this file as the only source of truth for unfinished architecture work.
2. Continue the master plan at Phase 7 (`MainWindow.qml` shell simplification, optional) unless a higher-leverage retirement is proven.
3. Preserve frozen shell and launcher contracts.
4. Keep the quarantined remainder explicit by file.
5. Do not open automation follow-on work until the root QML contract is materially smaller.