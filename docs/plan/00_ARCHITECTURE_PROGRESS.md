# Architecture Progress

Status board for the active architecture roadmap in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`.

Use this file for current stage status and next-slice tracking.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for the architecture rationale and staged roadmap.

## Current State

- Overall status: in progress
- Most recent completed slice: Workstream E1 Launcher SSH-admin contract reduction
- Last completed implementation slice: Workstream E1 Launcher SSH-admin contract reduction
- Core refactor purpose: turn the app into a more professional Qt program by reducing global coupling, clarifying ownership, shrinking the app-scope QML contract, and making the codebase easier to maintain, scale, and understand
- Active execution framework: completed stages remain historical record; unfinished work now executes as a family-by-family boundary retirement program inside Workstream E, with explicit family states, touched-slice retirement ledgers, and downstream gates
- North-star rule: each operator-visible behavior should have one canonical Python owner and one declarative QML consumer, with no equal second read path left behind after a checkpoint lands
- First-principles convergence rule: success is reduction of permanent app-scope QML exposure and durable architecture concept count, not namespacing alone
- Current active retirement family: device/status explicit telemetry remainder is now the active lead after the tracked shell/connectivity family was completed for shell/home/launcher surfaces, while the shared video subtree remains partially retired behind `videoRuntime`, the shared winch seam is behind `winchStatus`, the shared teensy seams are behind `teensyStatus`, the shared wheel summary/control seam is behind `wheelStatus`, and the shared recording seam is behind `recordingStatus`
- Next retirement family after that: revisit video/runtime or opportunistic settings cleanup only if a touched slice proves higher leverage than the downstream explicit domain telemetry remainder wave
- Recent validation hardening: fullscreen overlay warning coverage is green at `26 passed` for `tests/test_startup_smoke.py`, `tests/test_qml_imports.py`, and `tests/test_workflow_runner.py`, and the direct SSH teardown regression slice is green at `4 passed` for `tests/test_ssh.py`
- Most recent post-slice focused validation: `28 passed` for `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py` (Launcher SSH-admin contract reduction, 2026-04-27 22:58)
- Latest full validation: `252 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q` — **predates 6 subsequent slices; rerun before treating as current baseline**

## Historical Stage Board

| Stage | Status | Notes |
|---|---|---|
| Stage 0 | completed | Durable authority map is now published in this tracker |
| Stage 1 | completed | Command, device, and workflow boundary freezes are implemented and validated; the former Settings quick-apply exception was carried forward explicitly and is now closed by Stage 4 |
| Stage 2 | completed | The live cycle is removed, joystick selection ownership lives in a dedicated model, per-mode preset memory is selection-owned, direct overlay compatibility regressions exist, and the dead overlay compatibility wrappers are trimmed |
| Stage 3 | completed | Stage 3A shell policy, Stage 3B1 route normalization, and the deferred Stage 3B2 route formalization checkpoint are complete without widening ShellState or reopening overlay ownership |
| Stage 4 | completed | The Settings route is now truthful for schema-backed mixed-admin settings, camera remains explicit summary-only, and `CapabilityCatalog` publishes executable settings/admin metadata for later route and overlay slices |
| Stage 4.5 | completed | Status, wheel, winch, tuning, and base-top calibration surfaces now route through Python-owned admin boundaries, and a thin `AdminActionGate` makes default gating explicit for later legality work |

Unfinished work is no longer tracked here as a simple future stage ladder. It now executes through the active workstream board below.

## Active Workstream Board

| Workstream | Status | Current checkpoint | Next checkpoint after that | Blocking rule |
|---|---|---|---|---|
| Workstream A — Workflow runtime/editor stabilization | completed | A1-A3 landed | Workstream B complete | Keep the editor surface transitional and do not reopen a second workflow read path |
| Workstream B — Overlay contract/operator legality | completed | B1 overlay host and layer matrix landed; B2 legality seam landed | Workstream C complete | Keep legality narrow and shared; do not sprawl per-surface gate logic back into QML |
| Workstream C — Shell/route formalization | completed | C0 route-contract tests plus key-first shell route contract landed | Workstream D dedicated contract reduction | Keep `pageKey` canonical and do not reopen duplicate int-based shell route lookup |
| Workstream D — QML contract reduction | completed | Settings-family raw property-bag semantics retired; unused `capabilityCatalog`, `steamDeckHandler`, and `windMonitor` QML context exposure removed | Workstream E1 next | Keep future slices from re-growing the app-scope QML context bag |
| Workstream E — Contract-first infrastructure and downstream automation | active in progress | E1 slices 1-2 retired the workflow/editor and system-control command globals behind `systemControlServices`; the shared video slice partially retired the touched fullscreen-video root behind `videoRuntime`; the first device/status sub-slice moved the shared winch summary and power/load seam behind `winchStatus`; the second moved the shared teensy power/header seam behind `teensyStatus`; the third moved the shared wheel summary/control seam behind `wheelStatus`; the fourth moved the shared recording seam behind `recordingStatus`; the fifth moved the shared system-control teensy feature-toggle seam behind bounded `teensyStatus` fields; the sixth started the shell/connectivity family by moving the shared `ConnectionStatusPanel.qml` shell chrome behind bounded `shellConnectivityStatus`; the seventh retired the touched PageHome header/footer availability and heartbeat seam behind that same shell contract while removing `heartbeatHandler` from the root QML context surface; the eighth retired the touched PageLauncher LED reachability seam behind that same shell contract without widening Launcher SSH-admin behavior; and the ninth moved the remaining Launcher SSH-admin calls behind bounded `launcherAdmin` while removing raw `sshHandler` from the root QML context surface | Resume the downstream explicit domain telemetry remainder wave before opportunistic settings cleanup, while keeping PageHome video preview and remaining fullscreen/device telemetry explicit remainder unless a touched slice deliberately picks them up | Keep `AppRuntime` as the composition root, but any touched slice must retire at least one app-scope QML read path, must publish a before/after retirement ledger, must not widen `ShellState`, `OverlayHostPolicy`, or the global context bag, and must not count namespacing alone as convergence |

## Active Retirement Family Board

| Family | Status | Current ambient globals | Primary surfaces | Replacement contract goal | Focused validation | Exit criteria |
|---|---|---|---|---|---|---|
| Video/runtime | partial retirement | `baseStreamHandler`, `controlProcessor`, plus the remaining direct fullscreen-overlay telemetry reads that still bypass `videoRuntime` in the video component subtree | `python/paint_controller/qml/features/video/VideoFullscreenWorkspace.qml`, `python/paint_controller/qml/overlays/video/components/VideoOverlayTopBar.qml`, `python/paint_controller/qml/overlays/video/components/BaseFrontOverlay.qml`, `python/paint_controller/qml/overlays/video/components/EndEffectorOverlay.qml` | Keep `videoRuntime` bounded to the touched control, frame-refresh, and top-bar seams while naming the remaining fullscreen telemetry files as explicit quarantined remainder instead of widening it into a generic video/device bag | `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `tests/test_qml_imports.py` | Complete only when the declared video/runtime surfaces either consume `videoRuntime` directly or the remaining fullscreen telemetry files are explicitly quarantined by file and sequence |
| Device/status | active bounded remainder | Mixed controller/service reads and handler intent seams still spread across page, status, system-control, and shell-status device surfaces, but the shared winch summary/power-load seam is now behind `winchStatus`, the shared teensy power/header plus shared feature-toggle seams are now behind `teensyStatus`, the shared wheel summary/control seam is now behind `wheelStatus`, and the shared recording seam is now behind `recordingStatus` | `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/pages/status/PageStatus.qml`, `python/paint_controller/qml/pages/status/PageMonitor.qml`, `python/paint_controller/qml/navigation/ConnectionStatusPanel.qml`, adjacent status surfaces | Keep retiring bounded status or intent-facing seams without turning controller internals into another large global bag; with the shell/connectivity family completed for the tracked shell surfaces, downstream explicit domain telemetry remainder should now proceed by wheel, winch, teensy, then lidar/monitor unless a touched slice proves a different order is higher leverage | `tests/test_device_actions.py`, `tests/test_startup_smoke.py`, `tests/test_qml_imports.py`, focused status-model or handler tests | Each landed sub-slice reduces one real mixed read-plus-intent seam and keeps the blast radius bounded; the family does not complete until the declared shared summary/control surfaces stop reading raw device globals directly or the remainder is explicitly quarantined |
| Shell/connectivity telemetry | completed for tracked shell surfaces | No raw shell/connectivity controller globals remain in the touched shell/home/launcher surfaces; `launcherAdmin` is now the bounded Launcher admin contract, and `baseStreamHandler` remains explicit PageHome video-preview remainder outside this family | `python/paint_controller/qml/navigation/ConnectionStatusPanel.qml`, `python/paint_controller/qml/pages/home/PageHome.qml`, `python/paint_controller/qml/pages/home/PageLauncher.qml`, adjacent shell chrome | Keep the landed `shellConnectivityStatus` and `launcherAdmin` contracts stable for shell-facing QML without reopening raw service/controller globals | `tests/test_startup_smoke.py`, `tests/test_controller_factory_runtime.py`, targeted shell/home smoke coverage | Satisfied: the shared shell panel, touched PageHome shell telemetry, Launcher LEDs, and Launcher SSH-admin calls now consume bounded contracts instead of raw shell/connectivity globals |
| Settings cleanup | follow-on cleanup | Residual ambient settings use remains lower leverage because the typed owner API and route truthfulness work are already in place | `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/pages/settings/`, any touched settings widgets | Retire remaining ambient settings reads only where that still produces a real ownership or surface-area win | `tests/test_settings_runtime.py`, `tests/test_startup_smoke.py`, `tests/test_qml_imports.py` | Cleanup lands only when it materially reduces ambient exposure; it should not displace the bounded device/status wave or the named shell/connectivity telemetry family |

## Workstream E Proof Rules

- Every Workstream E slice must publish a retirement ledger: touched surfaces, ambient globals before, ambient globals after, canonical Python owner introduced or extended, and any remaining files explicitly quarantined.
- Any slice touching `python/paint_controller/core/app_runtime.py` must record an AppRuntime contract delta so shrinking the root context bag is treated as success rather than accidental churn.
- When a raw QML global loses its last live consumer in a landed slice, remove that global from `AppRuntime` in the same slice instead of deferring the cleanup.
- No new contract may become a controller-shaped mirror, a generic device bag, or a raw `all_status` passthrough.
- If a slice changes feature-contract shape, add or update runtime-parity smoke coverage for that contract.
- If a slice touches timers, worker pools, QThreads, controller cleanup, or QObject lifetime, add teardown-specific regression coverage before closing the slice.

## Recent Validation Hardening

### 2026-04-27 - Fullscreen Overlay Warning Hardening

- Repaired the tracked fullscreen overlay warning classes by making `workflow_runtime` notify-backed, guarding startup-time controller/status reads, replacing invalid anchored children inside `Row`, and extending the `CommonStyle.qml` compatibility shim with the video helper aliases the touched overlays already depended on.
- Aligned the fullscreen smoke harness with the real runtime contracts by adding the missing base-top-view and lidar fakes, explicit image-provider registration, and source-specific warning assertions.
- Revalidated the focused fullscreen warning slice to `26 passed` for `tests/test_startup_smoke.py`, `tests/test_qml_imports.py`, and `tests/test_workflow_runner.py`.

### 2026-04-27 - SSH Teardown Crash Fix

- Hardened `UISSHController` teardown with a dedicated `QThreadPool`, weakref-based callbacks, defensive timer disconnects, and idempotent cleanup so controller-owned timers and workers quiesce before QObject destruction.
- Added explicit direct-test cleanup discipline plus a cleanup-order regression test in `tests/test_ssh.py` so the late full-suite shutdown path stays covered.
- Revalidated `tests/test_ssh.py` to `4 passed` and restored the full suite to `252 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`.

## Baseline Authority Map

| Area | Current primary owner | Adjacent / duplicate owners | Notes |
|---|---|---|---|
| Shell window composition | `python/paint_controller/qml/core/MainWindow.qml` | `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `python/paint_controller/models/shell_state.py` | QML still composes the windows, but screen-role and secondary-surface policy now flow from `ShellState` instead of being invented locally |
| Screen facts vs product policy | `python/paint_controller/services/screen_manager.py` for screen facts | `python/paint_controller/models/shell_state.py`, `python/paint_controller/core/qt_bridge.py` | Screen discovery remains fact-only in Python, and product shell policy now lives in `ShellState` rather than root QML |
| Route identity and selection | `python/paint_controller/qml/core/MainWindow.qml` | `python/paint_controller/qml/navigation/SelectBar.qml` as presenter/requester | `MainWindow.qml` now owns the shared route manifest and selected-route writes; `SelectBar.qml` renders from that manifest and emits navigation requests without owning route state |
| Overlay visibility and active-menu policy | `python/paint_controller/ui/overlay.py` | `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `MainWindow.qml`, `MultiScreenListUI.qml` | Overlay/menu presentation is now a stable Python-owned facade consumed by multiple QML surfaces; the next shell work is about host-surface policy, not unresolved Stage 2 menu ownership |
| Control selection vs command execution | `python/paint_controller/models/joystick_selection.py` for selection state | `python/paint_controller/ui/overlay.py`, `python/paint_controller/handlers/control_processor.py` | Selection ownership is explicit, `OverlayController` is now a presentation facade, and `UIInputHandler` no longer stores long-term preset state |
| Settings authority | `python/paint_controller/core/settings.py` | `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/pages/settings/PageSettings.qml` | Python is authoritative; shared settings widgets and route summaries now consume typed `SettingsManager` helpers instead of raw setting lookup/mutation logic, and the Settings route exposes schema-backed mixed-admin settings where a truthful contract exists |
| Workflow runtime | `python/paint_controller/services/workflow/workflow_runner.py` | `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`, `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml` | Runtime control and status stay on `workFlowRunner`, which now publishes a cached declarative read model, canonical workflow-order current-action identity, and notify-driven runtime/progress state |
| Workflow persistence | `python/paint_controller/services/workflow/workflow_editor.py` | `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml` | Editor persistence is split away from runtime execution, shares catalog ownership through `workflow_catalog.py`, writes atomically, normalizes workflow documents, and follows explicit runtime collision rules |
| Machine-affecting QML actions | `python/paint_controller/handlers/manual_commands.py`, `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/handlers/device_operations.py`, `python/paint_controller/handlers/winch_motion.py`, `python/paint_controller/handlers/tuning_admin.py`, `python/paint_controller/handlers/base_top_view_admin.py`, `python/paint_controller/services/workflow/workflow_runner.py` | `WorkFlowTab.qml`, `EditWorkFlowTab.qml` | The remaining direct admin/calibration page and popup mutators now route through narrow Python-owned boundaries. The next legality work is about consuming these seams explicitly, not removing raw QML controller writes that are already gone |

## Completed Slices

### 2026-04-27 - Workstream E1 Launcher SSH-Admin Contract Reduction

- Added a bounded `launcherAdmin` contract in `AppRuntime`, threaded it into `PageLauncher.qml` from `MainWindow.qml`, and retired the remaining raw Launcher config load/save plus command-dispatch calls from `sshHandler`.
- Removed `sshHandler` from the root QML context contract because the landed Launcher admin slice retired its last live QML consumer.
- Revalidated the focused runtime/startup/import band to `28 passed` for `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`.

### 2026-04-27 - Workstream E1 PageLauncher Read-Side Shell Status Reduction

- Reused the existing `shellConnectivityStatus` reachability fields, threaded that contract into `PageLauncher.qml` from `MainWindow.qml`, and retired only the touched BASE and END_EFFECTOR LED bindings from raw `sshHandler.deviceAvailability`.
- Left Launcher SSH config load/save and command dispatch intentionally on `sshHandler` so the slice stays read-side only instead of introducing a premature Launcher admin model.
- Added direct Launcher startup smoke coverage and revalidated the touched QML band to `21 passed` for `tests/test_startup_smoke.py` plus `tests/test_qml_imports.py`.

### 2026-04-27 - Workstream E1 PageHome Shell Telemetry Contract Reduction

- Extended `shellConnectivityStatus` with bounded SSH reachability fields, threaded that contract into `PageHome.qml` from `MainWindow.qml`, and retired the touched PageHome status-header and bottom-status-bar availability/heartbeat reads without touching PageHome video preview.
- Removed `heartbeatHandler` from the root QML context contract because the landed PageHome slice retired its last live QML consumer.
- Revalidated the focused runtime/startup band to `26 passed` for `tests/test_controller_factory_runtime.py` plus `tests/test_startup_smoke.py`, then reran `tests/test_qml_imports.py` to `1 passed`.

### 2026-04-27 - Workstream E1 Shell/Connectivity Panel Contract Reduction

- Added a bounded `shellConnectivityStatus` contract in `AppRuntime` so the shared shell `ConnectionStatusPanel.qml` path can consume explicit winch, wheel, end-effector availability, heartbeat, and IP-address state without continuing to read raw `heartbeatHandler`, `winchController`, `teensyController`, or ghost `uiData` fields from the app-scope context bag.
- Rewired `ConnectionStatusPanel.qml`, `SelectBar.qml`, and `MainWindow.qml` so the touched shell chrome consumes that explicit contract while leaving `PageHome.qml` video preview and `PageLauncher.qml` command/config surfaces explicitly out of scope for a later shell/connectivity follow-up.
- Revalidated the focused runtime and shell startup band to `6 passed` for `tests/test_controller_factory_runtime.py` plus touched `tests/test_startup_smoke.py` paths, and confirmed the shared `ConnectionStatusPanel.qml` surface no longer reads raw `winchController`, `teensyController`, `heartbeatHandler`, `wheelStatus`, or `uiData` values directly.

### 2026-04-27 - Workstream E1 Teensy Feature-Toggle Status Contract Reduction

- Extended the bounded `teensyStatus` contract in `AppRuntime` with only the shared stabilization, yaw, auto-correction, leveling, roller-steering, swing-damping, and spray-gun LED fields needed by the touched system-control surface instead of exposing a generic teensy bag or raw `all_status` passthrough.
- Rewired the shared teensy toggle block in `DeviceControlTab.qml` to consume those bounded `teensyStatus` fields while keeping the existing `deviceOperationsHandler` write path unchanged.
- Revalidated the focused runtime and startup smoke band to `5 passed` for `tests/test_controller_factory_runtime.py` plus the touched `tests/test_startup_smoke.py` paths, and confirmed the shared `DeviceControlTab.qml` teensy toggle surface no longer reads raw `teensyController` toggle fields directly.

### 2026-04-27 - Workstream E1 Device/Status Winch Contract Reduction

- Added a bounded `winchStatus` contract in `AppRuntime` so the first device/status sub-slice can consume explicit winch summary and power/load state without continuing to read raw `winchController` state from the app-scope context bag.
- Rewired `PageWinch.qml`, `PageStatus.qml`, `DeviceControlTab.qml`, `SystemControlWorkspace.qml`, `MainWindow.qml`, and `MultiScreenListUI.qml` so the touched winch summary and power/load consumers use that explicit contract while the existing handler-owned write paths remain unchanged.
- Revalidated the focused device/status winch slice to `27 passed` for `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`.

### 2026-04-27 - Workstream E1 Device/Status Teensy Power/Header Contract Reduction

- Added a bounded `teensyStatus` contract in `AppRuntime` so the shared teensy power/header seam can consume explicit enable, relay, and board-summary telemetry without continuing to read raw `teensyController.all_status` state from the app-scope context bag.
- Rewired `DeviceControlTab.qml`, `TeensyStatus.qml`, `MonitorHeader.qml`, `PageStatus.qml`, `PageMonitor.qml`, `SystemControlWorkspace.qml`, `SystemControlMenu.qml`, `MainWindow.qml`, and `MultiScreenListUI.qml` so the touched teensy power/header consumers use that explicit contract while the existing handler-owned write paths remain unchanged.
- Revalidated the focused device/status teensy slice to `27 passed` for `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`.

### 2026-04-27 - Workstream E1 Video Runtime Contract Reduction

- Added a bounded `videoRuntime` contract in `AppRuntime` with narrow `controls`, `feeds`, and `topBar` leaves instead of continuing direct shared-video reads from the app-scope context bag.
- Rewired `VideoFullscreenWorkspace.qml`, the compatibility wrapper, the main and secondary fullscreen hosts, and the shared video top bar callers to consume that explicit contract while keeping `workflowServices.workflowRunner` stable.
- Treated the remaining direct fullscreen telemetry reads in `BaseFrontOverlay.qml` and `EndEffectorOverlay.qml` as explicit later-family remainder rather than widening `videoRuntime` into a generic video/device mirror.
- Revalidated the focused video/runtime slice to `25 passed` for `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`.

### 2026-04-25 - Stage 0 Authority Map Publication

- Published the durable ownership map for shell state, overlay visibility, control selection, settings, workflow runtime, workflow persistence, and direct machine-affecting QML paths.
- Locked the next code slice to Stage 1B hard device actions instead of the previously-stated settings-outlier path.
- Replaced the old shell-coordinator idea with the narrower `ScreenManager` facts + `ShellState` policy + `QtBridge` intents split in the active roadmap.

### 2026-04-25 - Stage 1A Manual Command Boundary Freeze

- Added Python-owned `ManualCommandHandler` and rewired `CommandTab.qml` to use it.
- Moved command validation, coercion, and dispatch out of QML.
- Kept unsupported commands visible but explicitly unavailable instead of silent no-ops.
- Fixed the Demo parameter mismatch by making Python consume the existing QML gimbal parameter names.

### 2026-04-26 - Stage 1B Through 1E Boundary Freeze

- Added `DeviceActionHandler` and `DeviceOperationsHandler`, then rewired `DeviceControlTab.qml` so hard device actions and operational side effects route through Python-owned boundaries.
- Split workflow editor persistence into `workflow_catalog.py` and `workflow_editor.py`, and rewired `EditWorkFlowTab.qml` to the new editor-facing boundary.
- Hardened `WorkFlowRunner` so runtime execution keeps the existing contract but rejects loading a new workflow while execution is active.
- Expanded direct handler/runtime/factory/startup coverage and reran the full suite to `190 passed`.
- The remaining Settings quick-apply truthfulness gap is now tracked explicitly in the roadmap instead of being implicitly treated as closed Stage 1 work.

### 2026-04-26 - Stage 2 Initial Control-Selection Cycle Break

- Moved `EF Yaw Angle` selection-time offset seeding into `ControlProcessor` so the processor now owns its own yaw target transition behavior.
- Removed `OverlayController`'s `ControlProcessor` back-reference and deleted the deferred cycle wiring from `controller_factory.py`.
- Added focused control-processor transition tests and reran the Stage 2 regression slice plus the full suite to `193 passed`.

### 2026-04-26 - Stage 2 Selection Model Extraction

- Added `JoystickSelectionModel` as the dedicated owner of committed and temporary joystick selection state.
- Rewired `OverlayController` into a presentation/compatibility facade over that model and made `ControlProcessor` read the model directly.
- Added direct selection-model tests and reran the focused Stage 2 slices plus the full suite to `196 passed`.

### 2026-04-26 - Stage 2 Overlay/Input Ownership Freeze

- Added direct `OverlayController` compatibility regressions for menu visibility, temporary-vs-committed selection behavior, and yaw-reset handling.
- Moved base/EF preset memory into `JoystickSelectionModel`, removed the redundant input-side active-menu assignment, centralized overlay toggle behavior, and trimmed the dead overlay compatibility wrappers that no longer had live callers.
- Revalidated the focused overlay/input/startup slices and reran the full suite to `202 passed`.

### 2026-04-26 - Stage 3A Shell Policy Split

- Added a narrow `ShellState` owner for screen-role policy, secondary-surface presence, system-control host-surface policy, and fullscreen host policy.
- Registered `shellState` into the QML context and rewired `MainWindow.qml` plus `MultiScreenListUI.qml` to consume shell policy declaratively instead of turning raw screen count into product behavior locally.
- Added direct `ShellState` tests and reran the focused shell/startup/runtime slices to `26 passed`.

### 2026-04-26 - Stage 3B1 Route Normalization

- Moved top-level route metadata into one shared manifest on `MainWindow.qml` and made `MainWindow.qml` the canonical selected-route owner because it already owns the shell `StackView`.
- Rewired `SelectBar.qml` into a manifest-driven presenter/requester so it no longer carries a second hard-coded route catalog or local selected-route ownership.
- Added a focused smoke assertion that the SelectBar harness renders from the shared manifest and keeps selected-route synchronization green.
- Revalidated the focused Stage 3B1 shell/import slice to `2 passed` for `tests/test_startup_smoke.py::test_select_bar_navigates_via_explicit_page_registry` and `tests/test_qml_imports.py`.

### 2026-04-26 - Stage 4A.1 Overlay Settings Authority Leak + Truthful Transitional Settings Route

- Removed the redundant direct `teensyController.thrust_force` mutation from `SettingsTab.qml`; the overlay thrust-force save path now routes through `settingsManager` only.
- Removed placeholder local state from `PageSettings.qml`, rewrote `MainSettingsPage.qml` summaries to stop claiming fake runtime values, and converted the unwired subpages into explicit transitional maintenance surfaces instead of fake-live controls.
- Wired the Settings subpage back buttons so they return to the top-level Settings page rather than rendering as dead affordances.
- Added a direct smoke test for `PageSettings.qml` and reran the focused Stage 4A.1 validation slices to `9 passed` for `tests/test_teensy.py` and `10 passed` for `tests/test_startup_smoke.py` plus `tests/test_qml_imports.py`.

### 2026-04-26 - Stage 4 Settings Truthfulness + Capability Model

- Added non-popup `apply*` slots in `SettingsManager` and a shared `ManagedSettingSpinBox.qml` helper so the Settings route can save schema-backed settings without fake placeholder controls or popup spam.
- Rewired the winch, wheels, arm, and main Settings pages to real schema-backed values, and kept the camera Settings page explicit about its summary-only role while base-top calibration remains overlay-primary.
- Added `CapabilityCatalog` as a thin Python-owned inventory for settings/admin capability and legality metadata, registered it in the runtime context, and pinned it with direct unit tests.
- Revalidated the focused Stage 4 slices to `27 passed` and reran the full suite to `210 passed`.

### 2026-04-26 - Stage 4.5A Status/Winch Admin Boundary Slice

- Extended the existing `DeviceActionHandler` with explicit desired-state request slots so status-oriented surfaces can express enable/relay intent without relying on invert-current semantics.
- Rewired `PageStatus.qml`, `TeensyStatus.qml`, and the winch power toggle in `PageWinch.qml` to that Python-owned boundary instead of calling raw controller mutators directly.
- Added focused handler coverage for the explicit request API and revalidated the Stage 4.5A shell/import slice to `15 passed` for `tests/test_device_actions.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`.

### 2026-04-26 - Stage 4.5 Completion

- Added a thin `AdminActionGate` so runtime-state gating is explicit in Python instead of being left to scattered QML exceptions, while still keeping later overlay-legality work as a separate stage.
- Reused and extended the existing device boundaries for status, wheel, and load-detection actions; added dedicated `WinchMotionHandler`, `TuningAdminHandler`, and `BaseTopViewAdminHandler` seams for the remaining coherent surface families.
- Rewired `PageWheel.qml`, `PageWinch.qml`, `PageTuning.qml`, and `BaseTopViewSettingsPopup.qml` off raw controller/service mutations and aligned `CapabilityCatalog` to the new authorities.
- Revalidated the combined Stage 4.5 slice to `40 passed` and reran the full suite to `224 passed`.

### 2026-04-26 - Workstream A Workflow Runtime And Editor Stabilization

- `WorkFlowExecutor` now publishes canonical workflow-order action indices, including position-triggered actions, so runtime state and workflow documents agree on current-action identity.
- `WorkFlowRunner` now owns a cached workflow read model for action summaries, current action display, progress, loop state, runtime, and loaded-document reload state; `WorkFlowTab.qml` and `WorkFlowStatusOverlay.qml` consume that declarative contract instead of rebuilding action state ad hoc.
- `WorkflowCatalog` ordering is stable, `WorkflowEditor` writes atomically with document normalization, and save/delete behavior is explicit when a workflow is loaded or executing.
- Focused Workstream A validation is green at `40 passed`, and the full suite is green at `233 passed`.

### 2026-04-26 - Workstream B1 Overlay Host And Layer Matrix

- Added `OverlayHostPolicy` as the canonical Python-owned host and layer owner for system-control overlays, joystick overlays, emergency overlays, and fullscreen-video placement.
- Kept `ShellState` narrow for screen-role policy and `OverlayController` narrow for menu session state; the host matrix now composes those seams instead of widening either owner into a coordinator.
- Rewired `MainWindow.qml` and `MultiScreenListUI.qml` to consume that host contract declaratively, added secondary-surface joystick/emergency/video host instances, and retired the remaining ad hoc host/`z` rules from the touched surfaces.
- Focused Workstream B1 validation is green at `40 passed`, and the last verified full-suite baseline remains `233 passed`.

### 2026-04-26 - Workstream B2 Operator-Action Legality

- Added `ActionLegalityModel` as the canonical QML-facing legality seam over `AdminActionGate` plus `CapabilityCatalog`, and registered it into the runtime context as `actionLegality`.
- Rewired the gated `DeviceControlTab.qml` controls through legality-aware `ControlPanel.qml` and `ActionButton.qml` contracts so blocked actions render their reason before click instead of relying only on handler rejection after click.
- Rewired `BaseTopViewSettingsPopup.qml` to consume the same legality seam for live adjustments, save, and reset affordances, and extended `CapabilityCatalog` surface metadata for the overlay device-control family.
- Focused Workstream B2 validation is green at `39 passed`, and the last verified full-suite baseline remains `233 passed`.

### 2026-04-26 - Workstream C Shell/Route Formalization

- Added a test-first route-contract checkpoint, then completed the touched shell-family route formalization without widening `ShellState`, `QtBridge`, or the AppRuntime context-property contract.
- Reworked `MainWindow.qml` so route lookup resolves by `pageKey`, demoted numeric route ordering to internal `routeOrder` metadata for StackView transitions, and rewired `SelectBar.qml` to emit key-based navigation requests without carrying duplicate route lookup logic.
- Updated the focused MainWindow and SelectBar smoke harnesses to assert key-first navigation and invalid-route no-op behavior, reran the focused shell/import band to `17 passed`, and reran the full suite to `245 passed`.

### 2026-04-26 - Workstream D1 Settings Typed-Contract Reduction

- Rewired `SettingInputField.qml` and `ManagedSettingSpinBox.qml` to use typed `SettingsManager` helper slots plus `setting_changed` refresh instead of raw `settingsManager` property/index access.
- Added direct runtime coverage for the typed QML-facing settings slots that the shared widgets now depend on.
- Revalidated the focused settings/runtime/QML smoke band to `27 passed` and reran the full suite to `247 passed`.

### 2026-04-26 - Workstream D Completion

- Added owner-side settings summary helpers in `SettingsManager`, rewired the Settings route pages to those helpers, and replaced the last inline special-case settings fields in `SettingsTab.qml` with the shared typed `SettingInputField` contract.
- Retired unused `capabilityCatalog`, `steamDeckHandler`, and `windMonitor` exposure from the QML context-property contract to make the app-scope runtime surface materially smaller.
- Fixed deterministic workflow-name ordering in `WorkflowCatalog` during the final validation pass, then reran the focused D contract band to `35 passed` and the full suite to `248 passed`.

### 2026-04-26 - Workstream E1 Contract-First Infrastructure Slices 1-2

- Added `systemControlServices` as a feature-scoped contract in `AppRuntime`, retired the ambient `workFlowRunner` and `workflowEditor` root globals, and rewired the touched system-control plus video workflow surfaces to consume explicit required inputs instead of ambient root reads.
- Extended the same boundary to carry `manualCommandHandler`, rewired `CommandTab.qml` off the root context, and retired the last direct system-control command global read path from the app-scope QML contract.
- Revalidated the focused E1 command slice to `3 passed` for `tests/test_controller_factory_runtime.py` plus `tests/test_startup_smoke.py`, then reran the full suite to `249 passed`.

## Active Risks

- The broad QML context-property contract remains the biggest remaining maintainability problem; the repo is safer than before, but the mental surface area is still too wide until touched slices retire real app-scope reads in the same change.
- Feature roots such as `SystemControlWorkspace.qml` are materially cleaner than before, the shared video subtree now consumes a bounded `videoRuntime` contract for the touched control, frame-refresh, and top-bar seams, the first five device/status sub-slices consume `winchStatus`, bounded `teensyStatus` seams, `wheelStatus`, plus `recordingStatus`, and the tracked shell/home/launcher surfaces now consume bounded `shellConnectivityStatus` plus `launcherAdmin`; the remaining PageHome video preview remainder and explicit device/status remainder are the next primary E1 targets.
- The workflow runtime/editor contract is now materially narrower, but `EditWorkFlowTab.qml` remains explicitly transitional and future automation work should start only after the app-wide contract is smaller.
- The direct-admin QML mutator gap is closed for the tracked Stage 4.5 and Workstream B surfaces, but later route families still need the same ownership discipline rather than reopening local page heuristics.
- The recent overlay-warning and SSH teardown regressions showed that harness drift and QObject cleanup discipline can still let real runtime faults escape slice-local architecture tests if the fake runtime shape or direct-controller teardown path drifts from production behavior.
- Pass-through service bundles and generic bridge concepts can still create false progress if they only rename ambient access; the next slices need before/after consumer proof and explicit quarantine calls, not just grouped names.

## Next Session Checklist

1. Resume the explicit domain telemetry remainder wave, starting with wheel detail telemetry unless a touched slice proves a higher-leverage caller; keep the landed shell/connectivity contracts stable and do not reopen `launcherAdmin`, `shellConnectivityStatus`, or the retired raw `sshHandler` path.
2. Keep wheel detail telemetry in `PageWheel.qml` and fullscreen wheel telemetry in `BaseFrontOverlay.qml` explicitly quarantined until a later dedicated mobility-telemetry checkpoint widens scope on purpose.
3. Any slice touching `python/paint_controller/core/app_runtime.py` must retire at least one direct app-scope QML read path in the same change and record the AppRuntime contract delta.
4. Treat feature contracts as true feature-facing models or bounded intent surfaces, not as passive namespace wrappers over the same ambient objects; keep `winchStatus` and `teensyStatus` bounded to the landed seams instead of growing them into generic device bags.
5. Keep `PageHome.qml` video preview, remaining fullscreen telemetry, and untouched device/status callers explicit remainder unless a touched slice deliberately picks them up; future slices should treat the landed `launcherAdmin` boundary as stable rather than reopening Launcher into another controller-shaped mirror.
6. Preserve the strengthened fullscreen smoke harness and SSH cleanup regression coverage while Workstream E continues; future slices should add runtime-parity smoke or teardown coverage whenever contract shape or QObject lifecycle is touched.