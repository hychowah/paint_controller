# Architecture Progress

This file is the single live control board for unfinished architecture work.

Use this file for the current execution order, frozen contracts, quarantine rules, and validation gates.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for durable architecture rationale and historical stage context.

## Current Snapshot

- Overall status: in progress
- Active architecture program: none — **TD-054** and **TD-056** closed; **TD-055** residual only. QML surface retirement closed (TD-032).
- Most recent completed slice: **TD-056** RosTelemetryBridge + wheel/winch main-thread apply (2026-07-29)
- Debt tracker: TD-055 residual optional 4′/5′; opportunistic TD-052/053; heartbeat telemetry residual — see `docs/tech-debt.md`
- Core purpose: reduce global coupling, clarify ownership, shrink ambient QML *usage* (injection depth), and make composition/ports closer to a professional Qt program — without reopening TD-032 name-retirement.
- First-principles rule: success means fewer ambient leaf reads, thinner composition export, real CI/type control planes, and **deeper modules with less change amplification** — not wrapper proliferation, mega-Backend, or empty layer folders
- Last full-suite baseline: `484 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q` on 2026-07-29 (halt-stop + Teensy bridge residual)

## Live Board

### Now

- Phase 8 is complete. **QML surface retirement program closed** (TD-032, 2026-07-28).
- **Problem 2 Wave 1+2 landed** (2026-07-29): dual HAL collapse; ContinuousTeleopEngine; Actions invoke family; factory subsystem builders; workflow port dialect; Teensy formatting off-device. Phase 4′/5′ **deferred** (no empty rehome theater).

### Next

- Opportunistic TD-052/053. TD-055 4′/5′ only if a real status/rehome win appears. Optional: heartbeat ROS→main marshal residual.
- **TD-054 / TD-056 resolved** (2026-07-29): command bus + continuous latch; telemetry bridge for wheel/winch. Do not reintroduce raw multi-thread command publish or unlocked ROS-thread property mutation on Property-bag devices.
- **TD-048 / TD-050 / TD-049 / hygiene band resolved** (2026-07-29): inject-first; finalize ports; shared Teensy ports; docs/cleanup/StateStore/smoke dual-source hygiene.
- Root context contract remains frozen at `_EXPECTED_CONTEXT_PROPERTY_NAMES` (~26 names). Prefer **inject then retire last consumer**; do not open a new boundary-retirement mega-program.
- Industrial HMI / operator-UX product work is **out of scope** for this architecture track unless explicitly reprioritized.

### Later

#### Automation follow-on

- Do not open the downstream automation-contract wave until the app-scope QML contract is materially smaller than it is today.

### Frozen

- Key-first shell **route identity owned by `ShellRouter`** (Python); `MainWindow.qml` is a declarative consumer
- `ShellState` as the bounded shell policy owner
- `OverlayHostPolicy` as the bounded overlay host and layer owner
- `shellConnectivityStatus` for shell-facing telemetry
- `launcherAdmin` for Launcher admin actions
- `systemControlServices` for the touched workflow, editor, and command system-control family
- `videoRuntime` for the touched fullscreen control, feed, and top-bar family
- Rule: do not casually reopen these contracts unless a future slice proves a real retirement win that cannot be achieved within the current ownership boundary

## Quarantined Remainder

These files are allowed to keep temporary raw-global reads until their named family is active. They are explicit remainder, not architectural truth.

- *(none)*

## Validation Gates

- Prefer inject-first; retire raw app-scope QML reads when a family is touched (do not reopen TD-032 name-retirement mega-program).
- Every slice touching `python/paint_controller/core/app_runtime.py` must record the AppRuntime contract delta.
- No new contract may become a controller-shaped mirror, a generic device bag, or a raw `all_status` passthrough.
- If a slice changes a QML-facing contract, add or update startup smoke coverage for that contract.
- If a slice touches timers, worker pools, QThreads, controller cleanup, or QObject lifetime, add teardown-specific regression coverage before closing the slice.
- When a raw QML global loses its last live consumer, remove it from the context composer expected-name set in the same slice.
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
- Phase 8 completed the AppRuntime wiring extraction: `QmlContextComposer` now owns `_EXPECTED_CONTEXT_PROPERTY_NAMES`, all status-wrapper classes, and context-property dict construction; `SignalWiring` now owns Steam Deck callbacks, status-timer startup, and all runtime signal connections; `AppRuntime` is reduced to a thin composition root that orchestrates creation, wiring, and shutdown; new focused tests cover the composer and wiring helpers directly.

## Active Risks

- The app-scope QML context contract is still broader than ideal (~26 frozen names); shrink only with last-consumer proof, not vanity rename programs.
- Harness drift remains a risk where smoke fixtures re-implement production contracts by hand (TD-042 hygiene).
- In-flight workflow action may still oneshot-publish before cooperative stop is seen.
- Operator UI workflow `stop()` may still use local `_emergency_shutdown` (not the global halt matrix).
- Do not reintroduce raw multi-thread ROS **command** `publish` outside `RosCommandBus.pump`, or unlocked ROS-thread QObject mutation on property-bag / status devices.

## Next Session Checklist

1. Keep this file as the live unfinished-work board; durable Qt rationale stays in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`.
2. Concurrency integrity track closed (TD-054/056). TD-055 residual only in `docs/tech-debt.md`.
3. Preserve frozen shell and launcher contracts.
4. Keep quarantined remainder explicit by file (currently none).
5. Do not open automation follow-on until there is a clear product need separate from ambient QML cleanup.
6. Reject shallow “architecture” PRs: no empty layer packages, no pass-through-only types, no second HAL, no new popup/peer deps on controllers.