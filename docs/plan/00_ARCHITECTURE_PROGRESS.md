# Architecture Progress

Status board for the active architecture roadmap in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`.

Use this file for current stage status and next-slice tracking.
Use `DEVNOTES.md` for verified implementation history.
Use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for the architecture rationale and staged roadmap.

## Current State

- Overall status: in progress
- Most recent completed slice: Workstream E1 slice 2 system-control command contract reduction
- Last completed implementation slice: Workstream E1 slice 2 system-control command contract reduction
- Core refactor purpose: turn the app into a more professional Qt program by reducing global coupling, clarifying ownership, shrinking the app-scope QML contract, and making the codebase easier to maintain, scale, and understand
- Active execution framework: completed stages remain historical record; unfinished work now executes as workstreams with hard checkpoints and touched-slice contract-retirement rules
- North-star rule: each operator-visible behavior should have one canonical Python owner and one declarative QML consumer, with no equal second read path left behind after a checkpoint lands
- Next recommended checkpoint: Continue Workstream E1 by retiring the next app-scope QML read path after the workflow/editor and command globals moved behind `systemControlServices`
- Linux validation status: complete after rebasing onto `refactor`
- Last focused validation: focused Workstream E1 command-contract validation is green at `3 passed` for `tests/test_controller_factory_runtime.py` plus `tests/test_startup_smoke.py`
- Latest full validation: `249 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`

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
| Workstream E — Contract-first infrastructure and downstream automation | active in progress | E1 workflow/editor globals plus the system-control command global read path are now retired behind `systemControlServices` | Continue E1 by shrinking the next system-control or shared app-scope read family before E2 automation-contract work | Keep `AppRuntime` as the composition root, but any touched slice must retire at least one app-scope QML read path and must not widen `ShellState`, `OverlayHostPolicy`, or the global context bag |

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
- Feature roots such as `SystemControlWorkspace.qml` are materially cleaner than before and now own workflow/editor plus command handoff explicitly, but settings/device/admin families still depend on broad app-scope runtime exposure and remain the next likely E1 targets.
- The workflow runtime/editor contract is now materially narrower, but `EditWorkFlowTab.qml` remains explicitly transitional and future automation work should start only after the app-wide contract is smaller.
- The direct-admin QML mutator gap is closed for the tracked Stage 4.5 and Workstream B surfaces, but later route families still need the same ownership discipline rather than reopening local page heuristics.
- Workstream D is complete for the settings family, but the remaining downstream work now shifts first to contract-first infrastructure and only then to future automation and optional product/UI cleanup.

## Next Session Checklist

1. Continue Workstream E1 by retiring the next app-scope QML read path after the workflow/editor and command system-control slices.
2. Any slice touching `python/paint_controller/core/app_runtime.py` must retire at least one direct app-scope QML read path in the same change.
3. Keep `pageKey` canonical and keep `ShellState` plus `OverlayHostPolicy` narrow; do not reopen the completed shell/overlay ownership split while contract reduction proceeds.
4. Keep `EditWorkFlowTab.qml` explicitly transitional and do not treat current workflow-editor placement as a reason to broaden shell recomposition; keep reusing bounded feature contracts instead.
5. Keep future automation work downstream from the contract-first slice, and keep optional feature-shell recomposition and design-system cleanup non-blocking unless a later checkpoint proves they are still justified.