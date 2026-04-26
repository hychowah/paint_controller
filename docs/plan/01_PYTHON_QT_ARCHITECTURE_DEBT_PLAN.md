# Python Qt Architecture Debt Plan

> Created: 2026-04-25
> Reframed: 2026-04-25 after first-principles review
> Scope: Planning only. This document is a multi-session roadmap for making the Python `paint_controller` UI a more professional Qt/PySide6 application while preserving the working runtime, operator ergonomics, and safety boundaries already present in the repo.

## Executive Summary

The direction remains ownership-first. The product should stay Python-first, overlay-first, dual-surface aware, and safety conservative. What changed after the attack review is not the destination. It is the precision of the route.

The validated truths are these:

- Stage 1 command, device, and workflow boundary work is complete, but the roadmap must stop pretending the Settings quick-apply path is already solved. `SettingsTab.qml` still contains a mixed QML path that combines operator intent, persistence, and direct controller mutation, and that gap is now carried explicitly into Stage 4A instead of being hand-waved as finished.
- Stage 2 has removed the live `OverlayController` / `ControlProcessor` cycle, extracted `JoystickSelectionModel`, moved per-mode preset memory to the selection owner, and trimmed dead overlay compatibility wrappers. The remaining overlay/menu facade is now stable enough for shell work to bind to it.
- Shell work is no longer blocked on Stage 2. Stage 3A shell policy is now complete, and the next architecture slice is Stage 4A settings truthfulness so Stage 3B route hardening has a truthful Settings route to formalize.
- The top-level Settings route remains a real long-term admin or maintenance surface.
- In dual-screen mode, the built-in Steam Deck display remains the dedicated touch/control surface and the external display remains the mission surface.
- Behavior-tree migration is now a committed future direction, but the current workflow system is still a live product surface and must be stabilized on its own terms.
- The broad QML context-property contract is still a scalability risk, but it should be reduced only after the right owners are explicit.

The roadmap now centers on six architecture goals:

1. One clear Python-owned boundary for machine-affecting application actions initiated from QML.
2. One clear authority for the coordinated two-surface shell, route semantics, and fullscreen activation state.
3. One clear authority for operational overlay state, legality, and host-surface policy.
4. One truthful settings architecture: one Python authority, intentional operator/admin surfaces, and explicit capability and legality classes.
5. One stable workflow path for the current system plus explicit seams for future behavior-tree migration.
6. A narrower, explicit QML contract that exposes operator-facing state instead of runtime internals.

That is the path toward a professional Qt program for this robot controller.

## How Future LLM Sessions Should Use This Plan

Every future implementation session must still follow `AGENTS.md`:

1. Read `INDEX.md`, `AGENTS.md`, `KNOWLEDGE.md`, this plan, and `docs/tech-debt.md`.
2. Read `docs/plan/00_ARCHITECTURE_PROGRESS.md` for the current stage/slice status.
3. Pick exactly one slice from this roadmap.
4. Create or update root `PLANNING.md` for that slice.
5. Ask: "Here is my plan in PLANNING.md. Ready to proceed?"
6. Implement only after explicit approval.
7. Validate with the tests listed for that slice.
8. Update `DEVNOTES.md` after meaningful debugging or implementation.
9. Update `docs/tech-debt.md` and `docs/plan/00_ARCHITECTURE_PROGRESS.md` when debt is discovered, split, resolved, or reprioritized.
10. Delete root `PLANNING.md` before merge if the repo workflow requires cleanup.

This document is a roadmap, not approval to modify code.

## What "Professional Qt" Means Here

For this repo, a professional Qt/PySide6 application should have these properties:

- QML is declarative, task-oriented, and mostly policy-free.
- Python owns hardware, ROS, safety, persistence, execution policy, and screen-role decisions that matter across surfaces.
- QML-facing objects are introduced to clarify ownership, not to wrap everything mechanically.
- The shell has one source of truth for navigation, surface role, fullscreen activation, and major surface visibility.
- Operational overlays are allowed to be first-class UI when the operator must preserve video or machine context during adjustments.
- Settings may appear in more than one surface if the surfaces serve different operator roles, but they must still come from one authority and present truthful semantics.
- Safety, actuator math, and emergency behavior never move into QML.
- The built-in Steam Deck display remains the touch/control surface in dual-screen mode; that is product architecture, not an incidental layout choice.
- The system is testable at the level of startup, shell behavior, screen policy, focused model logic, and safety-sensitive controller boundaries.

This is not a generic desktop CRUD app. A DJI-style operating surface can be a professional result here. The professionalism comes from explicit contracts and ownership, not from forcing everything into conventional pages.

## Root Reasons The UI Feels Over-Complicated

The repo is not over-complicated mainly because it has many files. The file count is not the core problem. The real causes are below.

### Root Reason A: QML-To-Application Action Boundaries Are Too Loose

Current evidence:

- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml` performs persisted updates and immediate hardware-side effects in the same QML interaction path.
- QML operational surfaces can directly trigger device, command, and workflow actions through raw runtime objects.
- The runtime context contract still exposes many internal objects directly to QML.

Why it matters:

- The highest-risk UI boundary is not only visual complexity; it is that QML can still orchestrate application behavior too directly.
- Rearranging pages or shells without first narrowing these action paths mostly moves symptoms around.
- A professional Qt program in this domain should let QML express user intent, while Python owns machine-facing application behavior.

### Root Reason B: Shell Authority Is Split

Current evidence:

- `python/paint_controller/qml/core/MainWindow.qml` owns root window configuration, screen selection, page component creation, overlay composition, and backend connections.
- `python/paint_controller/qml/navigation/SelectBar.qml` owns page-index routing and selected-button state.
- `python/paint_controller/services/screen_manager.py` exists, but screen policy is still partly computed in QML.

Why it matters:

- Shell behavior is hard to reason about because no single layer owns it.
- Navigation cleanup alone will not solve the problem if screen and overlay policy remain in the root QML file.
- Future sessions can easily change the wrong layer because the shell decision path is spread across QML and Python.

### Root Reason C: Operational Overlay Ownership Is Implicit

Current evidence:

- `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml` contains device, command, settings, workflow, and editing surfaces.
- `python/paint_controller/qml/overlays/video/` is not just cosmetic overlay content; it is part of the main operating workflow.
- `MainWindow.qml` decides when the system-control overlay appears on the main window versus the secondary screen.

Why it matters:

- The operator overlay is a primary surface but is not documented as such in the architecture.
- Without an explicit contract, future cleanup work can accidentally weaken operator ergonomics.
- Overlay visibility and ownership are too easy to entangle with unrelated joystick or window logic.

### Root Reason D: QML Can Still See Too Many Runtime Internals

Current evidence:

- `python/paint_controller/core/app_runtime.py` registers a broad set of context properties directly into QML.
- Pages and overlays bind directly to controllers, services, handlers, recorders, and managers.

Why it matters:

- QML becomes structurally coupled to internal runtime construction.
- Python refactors have a wider blast radius than necessary.
- It is difficult to answer which UI surface truly owns which backend contract.

### Root Reason E: Settings Truthfulness Is Still Weak

Current evidence:

- `python/paint_controller/core/settings.py` is the strong persistence and validation core.
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml` is the stronger live settings surface for real machine control, but still has a mixed quick-apply mutation path in QML.
- `python/paint_controller/qml/pages/settings/PageSettings.qml` still contains placeholder-like local values and should not yet be treated as a truthful architecture surface.

Why it matters:

- The problem is not that multiple settings surfaces exist. The problem is that their authority relationship is still unclear.
- Trying to collapse everything into one settings location too early would solve the wrong problem.
- A professional Qt architecture should support both operational quick-adjust surfaces and broader admin/setup surfaces when the workflow demands it.

### Root Reason F: Selection, Menu, And Mode-Preset Ownership Are Still Split

Current evidence:

- `python/paint_controller/ui/overlay.py` still owns active-menu state, overlay visibility, temporary-selection initialization, and commit timing.
- `python/paint_controller/handlers/input.py` still owns per-mode joystick preset memory even though `JoystickSelectionModel` is now the selection owner.
- `python/paint_controller/models/joystick_selection.py` owns committed and temporary indices, but the remaining compatibility facade is still spread across more than one layer.

Why it matters:

- Stage 2 is no longer about a live circular dependency, but it is still about ownership truth.
- Small mistakes in this seam can change operator muscle memory or selection-commit timing.
- Shell and overlay work should not start binding to this seam until its responsibilities are frozen.

### Root Reason G: Workflow Has Present-System Debt And Future-Migration Debt

Current evidence:

- `python/paint_controller/services/workflow/workflow_runner.py` is already the Qt-facing runtime surface, but QML still repeatedly pulls derived workflow action data from it.
- `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml` still keeps a large mutable workflow document model in QML JavaScript.
- A future behavior-tree runtime is now a committed direction, but the migration seams are still not explicit.

Why it matters:

- The current workflow system still needs immediate maintainability and stability work.
- Future migration pressure exists, but it should not be used to justify speculative rewrites of the live workflow UI.
- The roadmap must separate current-system hardening from future-system seam design.

## Product Decisions And Non-Negotiable Invariants

These decisions are part of the architecture contract unless the user explicitly changes them later.

- Keep the Python-first runtime. Do not revive a second UI architecture path.
- Preserve the DJI-style overlay-first operating model.
- Treat the operator overlay as a first-class operating surface, not as an accidental anti-pattern.
- Keep the top-level Settings route as a real long-term admin or maintenance surface.
- In dual-monitor mode, keep the built-in Steam Deck display as the dedicated touch/control surface and the external monitor as the mission surface.
- Treat behavior-tree migration as a committed future direction, but keep the current workflow system safe and maintainable until that migration exists.
- Use `setContextProperty()` rather than `qmlRegisterSingletonInstance()` in this repo.
- Keep migrations additive until the existing context-property contract is safely retired.
- Do not move safety, actuator math, or emergency behavior into QML.
- Do not invest heavily in current workflow UI architecture as if it were the final long-term automation architecture.

## Architectural Anti-Goals

This plan deliberately avoids these traps:

- Do not replace the broad context-property contract with one giant `Backend` object.
- Do not build a broad `OperatorSession` or similar mega session object that centralizes shell policy, workflow runtime, settings authority, and machine actions.
- Do not create six new facade objects just because facade objects sound architectural.
- Do not define success as “everything is a page.”
- Do not define success as “there is only one settings screen.”
- Do not start with large visual recomposition before ownership is clarified.
- Do not merge shell cleanup, overlay redesign, settings redesign, and control-model work into one session.

## Recommended Architecture Direction

The most defensible direction is:

1. Keep the Stage 1 command, device, and workflow boundary work as complete, but stop claiming the remaining Settings quick-apply path is already frozen. Carry that gap explicitly into the settings roadmap instead of burying it.
2. Treat Stage 2 as complete and keep its stabilized overlay/menu facade as the shell-facing contract unless a concrete regression forces reopening it.
3. Run Stage 3A next: shell policy only. `ScreenManager` keeps screen facts, a narrow `ShellState` keeps product shell policy, `QtBridge` keeps imperative UI intents, and QML stays responsible for composition.
4. Run Stage 4A before route semantics harden: convert the top-level Settings route from a placeholder surface into a truthful admin/maintenance surface, and remove the remaining mixed QML persistence plus direct-controller mutation from the overlay settings path.
5. Return to Stage 3B after Stage 4A to harden route metadata and selected-route ownership without canonizing false settings semantics.
6. Run Stage 4B after that to classify settings by role, capability, and legality using a per-setting matrix rather than broad prose.
7. Formalize the overlay contract across all live overlay classes: system-control overlay, joystick overlay, emergency precedence, and fullscreen-video HUD layering.
8. Split workflow work into current-system stabilization and future behavior-tree preparation instead of treating both concerns as one vague stage.
9. Narrow the QML contract only after those owners are actually clear.
10. Leave feature-shell recomposition and design-system cleanup downstream.

The broad `OperatorSession` alternative was considered and rejected. A narrow shell coordinator is practical here. A broad session object would centralize unrelated concerns and recreate the coordinator problem in a different form.

## Multi-Session Roadmap

The stages below are ordered by architecture value and risk reduction, not by visual neatness.

## Stage 0: Baseline Authority Map

Goal: build a durable map of who currently owns shell policy, overlay policy, settings policy, control-selection state, automation state, and machine-affecting application actions.

Complexity: Low
Risk: Low
Suggested sessions: 1

Primary files:

- Read-only: `python/paint_controller/core/app_runtime.py`
- Read-only: `python/paint_controller/qml/core/MainWindow.qml`
- Read-only: `python/paint_controller/qml/navigation/SelectBar.qml`
- Read-only: `python/paint_controller/qml/overlays/systemcontrol/`
- Read-only: `python/paint_controller/qml/overlays/video/`
- Read-only: `python/paint_controller/qml/pages/settings/`
- Read-only: `python/paint_controller/ui/overlay.py`
- Read-only: `python/paint_controller/handlers/control_processor.py`

Tasks:

1. Classify each significant UI surface as `shell`, `operational overlay`, `admin/setup surface`, `diagnostic surface`, or `transitional surface`.
2. For each surface, list which runtime objects it touches directly.
3. Identify where QML currently triggers machine-affecting commands, persistence writes, and immediate side effects.
4. Identify where screen policy is computed today.
5. Identify where overlay visibility and active-tab policy are computed today.
6. Classify settings surfaces as `authoritative`, `role-specific consumer`, `duplicate`, `placeholder`, or `transitional`.
7. Classify workflow surfaces as `transitional`, `long-term`, or `behavior-tree replacement candidate`.
8. Record the top five ownership ambiguities where more than one layer appears to decide the same thing.

Exit criteria:

- The repo has an explicit authority map.
- Overlay-first operating use cases are documented.
- QML-to-application action paths are identified before implementation.
- Settings and workflow surfaces are classified before any rewrite work starts.

Validation:

- Read-only stage; no tests required unless files are changed accidentally.

## Stage 1: Freeze QML-To-Application Action Boundaries

Goal: stop QML from directly orchestrating high-risk application behavior before broader shell or surface cleanup, while being explicit about the still-open Settings quick-apply gap.

Complexity: High
Risk: High
Suggested sessions: functionally complete

Primary files:

- `python/paint_controller/qml/overlays/systemcontrol/CommandTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`
- candidate Python-side application boundary files justified by the chosen slice
- `tests/test_settings_runtime.py`
- `tests/test_workflow_runner.py`
- relevant command, device, and runtime tests for the touched slice

Current problem:

The live architectural risk is not only broad QML visibility. It is that some QML interactions still combine user intent, persistence, controller side effects, and runtime orchestration in one place. That is mostly addressed for command, device, and workflow families, but one live quick-apply settings path still remains in QML.

Validated Stage 1 sub-slices:

- Stage 1A: manual command boundary freeze in `CommandTab.qml` — complete.
- Stage 1B: hard device-action boundary freeze in `DeviceControlTab.qml` — complete.
- Stage 1C: device and operations side-effect boundary freeze in `DeviceControlTab.qml` — complete.
- Stage 1D: workflow editor persistence split — complete.
- Stage 1E: workflow execution boundary freeze — complete.

Remaining explicit caveat:

- The quick-apply settings path in `SettingsTab.qml` is not treated as fully complete boundary work. It is carried forward explicitly into Stage 4A because it overlaps long-term settings truthfulness and surface-legitimacy work.

Exit criteria:

- The highest-risk command, device, and workflow action paths no longer directly combine persistence writes and hardware-side effects.
- Any remaining settings quick-apply exceptions are explicitly called out in the roadmap instead of being described as closed.
- The chosen action family has focused tests.
- Visible operator workflow remains unchanged.

Validation:

- relevant focused tests for the touched action family
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

## Stage 2: Finish The Overlay/Input Ownership Freeze

Goal: freeze the remaining ownership seam between `OverlayController`, `UIInputHandler`, and `JoystickSelectionModel` before shell work binds to it.

Complexity: High
Risk: High
Suggested sessions: 2 to 4

Primary files:

- `python/paint_controller/ui/overlay.py`
- `python/paint_controller/handlers/input.py`
- `python/paint_controller/handlers/control_processor.py`
- `python/paint_controller/core/controller_factory.py`
- `python/paint_controller/models/joystick_selection.py`
- `python/paint_controller/qml/overlays/JoystickOverlay.qml`
- `tests/test_joystick_selection.py`
- `tests/test_input_handler.py`
- `tests/test_control_processor.py`
- `tests/test_controller_factory_runtime.py`
- `tests/test_safety_integration.py`
- `tests/test_startup_smoke.py`

Delivered result:

The live cycle is gone, selection ownership is extracted into `JoystickSelectionModel`, per-mode joystick preset memory is selection-owned, direct overlay compatibility regressions exist, and the remaining public `OverlayController` surface is narrowed to the live QML-facing menu and presentation contract.

Professional target:

- `JoystickSelectionModel` owns committed and temporary selection state.
- `UIInputHandler` turns hardware events into intent instead of storing long-term UI-operational state that belongs elsewhere.
- `OverlayController` becomes a stable compatibility and presentation facade, not a hidden owner of selection policy.
- `ControlProcessor` owns command math and hardware dispatch.

Important design rule:

Do not “shrink” `OverlayController` by intuition. Freeze a symbol-level contract first, then move one ownership seam at a time.

Required ownership freeze before edits:

Classify and document these symbols before moving them:

- `set_active_menu`
- `toggle_left_menu`
- `toggle_right_menu`
- `toggle_system_menu`
- `show_menu`
- `hide_menu`
- `move_up`
- `move_down`
- `move_to_first`
- `move_to_last`
- `set_joystick_controls`
- `get_current_joystick_controls`
- `avoidAutoRunOverwrite`
- the base-mode and end-effector-mode joystick preset memory currently held in `UIInputHandler`

Progress note:

- 2026-04-26: The Stage 2 cycle break is complete and `JoystickSelectionModel` owns committed and temporary joystick selection state.
- 2026-04-26: The bounded overlay/input ownership freeze is complete, direct overlay/menu regressions exist, and the shell can now bind to the stabilized overlay/menu facade.

Exit criteria:

- Remaining menu and preset ownership is explainable without reading both `OverlayController` and `UIInputHandler` together.
- A direct OverlayController-compatible regression slice exists before more ownership moves happen.
- Selection state is explainable without reading command-dispatch code.
- Safety-sensitive command behavior remains covered by tests.

Status: completed on 2026-04-26.

Validation:

- `tests/test_joystick_selection.py`
- `tests/test_input_handler.py`
- `tests/test_control_processor.py`
- `tests/test_controller_factory_runtime.py`
- `tests/test_safety_integration.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- focused OverlayController compatibility regressions for the touched symbols

## Stage 3: Establish The Two-Surface Shell With A Narrow ShellState Split

Goal: make shell policy professional by treating the product as a coordinated two-surface operator shell, without collapsing facts, policy, bridge intents, and QML composition into one new god object.

Complexity: Medium
Risk: High
Suggested sessions: 2 to 4

Primary files:

- `python/paint_controller/qml/core/MainWindow.qml`
- `python/paint_controller/qml/overlays/MultiScreenListUI.qml`
- `python/paint_controller/qml/navigation/SelectBar.qml`
- `python/paint_controller/services/screen_manager.py`
- `python/paint_controller/core/qt_bridge.py`
- candidate `ShellState` model file justified by the chosen slice
- `tests/test_startup_smoke.py`
- `tests/test_services_runtime.py`
- `tests/test_qt_bridge.py`

Current problem:

The product already behaves as a coordinated external mission surface plus built-in touch-operated surface, and Stage 3A has now made that shell policy explicit with a narrow `ShellState`. The remaining Stage 3 work is narrower: route metadata and selected-route hardening are still split across `MainWindow.qml` and `SelectBar.qml`, and that formalization should still wait until Stage 4A has made the Settings route truthful.

Professional target:

- `ScreenManager` remains the owner of screen facts, not product policy.
- `ShellState` becomes the owner of product shell policy such as route identity, surface roles, selected route, secondary-surface existence, and fullscreen activation policy.
- `QtBridge` remains the owner of imperative UI intents.
- Root QML becomes thinner and more declarative, but still composes the actual windows.

Stage structure:

- Stage 3A: shell policy only. Name the two product surfaces explicitly, move surface-role assignment, secondary-window ownership, emergency precedence, and fullscreen activation policy out of root QML, and keep video-workspace internals out of scope.
- Stage 3B: route metadata and selected-route hardening, after Stage 4A has made the Settings route truthful enough to formalize.

Progress note:

- 2026-04-26: Stage 3A is complete. `ShellState` now owns screen-role and secondary-surface policy, `MainWindow.qml` consumes shell policy instead of inventing it from raw screen count, and focused shell/startup/runtime validation is green.

Exit criteria:

- The dual-surface shell is explicitly modeled.
- `MainWindow.qml` is no longer the place where raw screen count becomes product policy.
- Stage 3A can complete before Stage 3B route hardening if the shell policy owner is already explicit.
- `SelectBar.qml` no longer carries a hard-coded button catalog that duplicates route knowledge owned elsewhere by the end of Stage 3B.
- Secondary-window behavior has focused tests.

Validation:

- `tests/test_startup_smoke.py`
- `tests/test_services_runtime.py`
- `tests/test_qt_bridge.py`
- `tests/test_qml_imports.py`
- Manual multi-screen validation on hardware when available.

## Stage 4: Define Settings Truthfulness, Authority, Capability Classes, And Role-Based Surfaces

Goal: first make settings surfaces truthful, then make the overall settings architecture explicit by clarifying authority, role, and operating-state legality.

Complexity: Medium
Risk: High
Suggested sessions: 2 to 4

Primary files:

- `python/paint_controller/core/settings.py`
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`
- `python/paint_controller/qml/pages/settings/PageSettings.qml`
- `python/paint_controller/qml/pages/settings/components/`
- `python/paint_controller/qml/pages/settings/pages/`
- `python/paint_controller/qml/pages/tuning/PageTuning.qml`
- `tests/test_settings_runtime.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

Current problem:

The repo already has a good settings authority on the Python side. The UI problem is that settings surfaces do not yet have a clear relationship by role and capability, the top-level Settings route is still partly placeholder local state, and a remaining overlay quick-apply path still mixes persistence with direct runtime mutation.

Professional target:

- One authority for persisted values and validation.
- One truthful top-level Settings route with a clear admin or maintenance role.
- One explicit distinction between quick operational adjustments and broader maintenance/setup surfaces.
- Clear capability classes such as `live-adjustable`, `safe-stop-required`, `commissioning-only`, and `diagnostic-only`.
- No placeholder settings surface pretending to be authoritative.
- No duplicated local QML state where Python authority already exists.

Implementation strategy:

Stage 4A: settings truthfulness and surface legitimacy.

1. Remove placeholder local state from `PageSettings.qml` and its subpages before treating the Settings route as a real architecture surface.
2. Decide the long-term role of each Settings-route sub-surface as admin, maintenance, commissioning, or diagnostics.
3. Remove the remaining mixed QML persistence plus direct-controller mutation path from `SettingsTab.qml`.

Stage 4B: broader settings capability and legality model.

4. Classify each setting as `persisted only`, `persisted + immediate apply`, `runtime-only`, or `deprecated`.
5. Classify each setting by capability and operating-state legality.
6. Identify which settings belong in the operator overlay because they are genuinely in-operation adjustments.
7. Identify which settings belong in maintenance/setup surfaces.
8. Use a per-setting matrix with key, authority, consumers, legality, and verification instead of broad prose only.
9. Introduce grouped metadata or a settings adapter only if it simplifies the UI contract meaningfully.

Exit criteria:

- The Settings route is truthful before route semantics are hardened elsewhere.
- Each setting has one authority.
- Multiple surfaces may exist, but their roles and legality rules are explicit.
- Placeholder local settings state is removed or clearly marked transitional.
- Atomic persistence and validation remain intact.

Validation:

- `tests/test_settings_runtime.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

## Stage 5: Formalize The Overlay Contract

Goal: turn the overlay-first operating model into explicit architecture after the action boundary, selection-state boundary, and shell-policy boundary are cleaner.

Complexity: High
Risk: High
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`
- `python/paint_controller/qml/overlays/JoystickOverlay.qml`
- `python/paint_controller/qml/features/video/VideoFullscreenWorkspace.qml`
- `python/paint_controller/qml/core/MainWindow.qml`
- `python/paint_controller/ui/overlay.py`
- `python/paint_controller/handlers/input.py`

Current problem:

The operator overlay is real product architecture, but its rules are implicit. The project benefits from it ergonomically while still carrying it as architecture debt. The plan also needs to cover more than the system-control overlay alone.

Professional target:

Define the overlay contract explicitly:

- which surfaces are operational overlays versus modal overlays versus maintenance/setup surfaces
- which actions are allowed during active operation
- which settings are safe quick-adjust settings
- which actions require confirmation, safe-stop, or maintenance mode
- which screen owns the touch-oriented overlay in single-screen and dual-screen modes
- how overlay visibility interacts with joystick menus, emergency UI, and fullscreen video HUD layering

Validation:

- `tests/test_input_handler.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- services runtime tests if screen behavior changes
- workflow tests only if workflow tabs are touched

## Stage 6: Workflow Stabilization And Behavior-Tree Preparation

Goal: keep the current workflow path safe and maintainable as a real current service, then define explicit seams for the committed future behavior-tree direction.

Complexity: Medium
Risk: Medium
Suggested sessions: 2 to 4

Primary files:

- `python/paint_controller/services/workflow/workflow_runner.py`
- `python/paint_controller/services/workflow/workflow_executor.py`
- `python/paint_controller/services/workflow/scheduler.py`
- `python/paint_controller/services/workflow/workflow_editor.py`
- `python/paint_controller/services/workflow/workflow_catalog.py`
- `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`
- `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml`
- `tests/test_workflow_runner.py`
- `tests/test_workflow_editor.py`
- `tests/test_workflow_executor.py`
- `tests/test_workflow_scheduler.py`

Current problem:

The workflow runtime already exposes a Qt-facing interface and should be stabilized where necessary, but current QML polling and local document editing still create present-day maintainability debt, and the future migration seams are not yet explicit.

Professional target:

- Safe start, stop, and recover behavior.
- Less repeated QML polling and less repeated recomputation of workflow action data.
- Less fragile persistence and editing seams.
- Clear identification of transitional workflow UI pieces.
- Explicit seams for a future behavior-tree runtime.

Design rule:

Prefer tightening the existing workflow runtime in place after the Stage 1 editor/runtime split, rather than inventing a large second abstraction layer.

Stage structure:

- Stage 6A: current-system stabilization. Reduce repeated QML polling and repeated action-list recomputation, tighten persistence boundaries, and harden the live editor/runtime split.
- Stage 6B: behavior-tree preparation. Define future seams explicitly around runner contract, action schema, status surface, and editor/runtime boundaries without rebuilding the current workflow UI preemptively.

Validation:

- `tests/test_workflow_runner.py`
- `tests/test_workflow_editor.py`
- `tests/test_workflow_executor.py`
- `tests/test_workflow_scheduler.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

## Stage 7: Narrow The QML Contract After Owners Are Clear

Goal: reduce raw context-property exposure only after action boundaries, shell ownership, overlay ownership, settings authority, and control ownership are better defined.

Complexity: Medium
Risk: Medium
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/core/app_runtime.py`
- candidate new adapter/model files only where justified
- tests around runtime registration and any new model logic

Current problem:

The repo has too many QML-visible runtime objects, but the earlier plan risked solving that with a broad facade taxonomy before the right ownership boundaries were known.

Professional target:

- Introduce QML-facing adapters only where they reduce real cross-cutting coupling.
- Reduce direct controller/service exposure where pages or overlays should depend on an operator-facing contract instead.
- Treat context-property reduction as an outcome of better architecture, not as the opening move.

Good candidates after earlier stages succeed:

- a `ShellState` contract if shell ownership is stabilized
- a control-selection model as part of Stage 2
- a settings adapter only if it meaningfully clarifies grouped metadata, capability classes, and legality rules
- a workflow editor/runtime split if it remains clearer than keeping both responsibilities on one object

Bad candidates:

- wrappers added only to reduce a number in a metric
- large “everything UI needs” objects
- a workflow facade built before the automation direction is settled

Exit criteria:

- Fewer raw runtime internals are directly referenced by QML.
- New adapters have crisp ownership and focused tests.
- The context-property count goes down because architecture improved, not because everything was hidden behind one umbrella object.

Validation:

- `tests/test_controller_factory_runtime.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- focused tests for any new adapter/model

Risks:

- Mechanical wrapping can create indirection without reducing coupling.

Rollback:

- Keep old context properties while new contracts are proven.

## Stage 8: Optional Feature-Shell Recomposition

Goal: reorganize visible destinations only if earlier ownership work shows a real product benefit.

Complexity: High
Risk: High
Suggested sessions: optional, many small slices

Status in this roadmap:

This is explicitly optional and downstream. It is not the main architecture lane.

Why:

Feature-shell recomposition is product design work enabled by architecture improvements, not architecture debt paydown by itself.

Use this stage only when:

- the action boundary is safer
- the dual-surface shell is stable
- overlay ownership is explicit
- settings authority is clear
- route registry is already maintainable

Possible outcomes:

- fewer top-level destinations
- clearer separation between operation, maintenance/setup, diagnostics, and automation
- better alignment between route names and operator language

Important:

Do not use this stage to force common in-operation work out of the overlay.

Validation:

- startup smoke
- QML import smoke
- affected focused tests
- manual operator-task trace on real hardware when possible

Rollback:

- keep legacy destinations available until new flows are validated

## Stage 9: Design-System And Styling Cleanup

Goal: finish visual consistency after architecture is stable.

Complexity: Low to Medium
Risk: Low
Suggested sessions: as needed

Primary files:

- `python/paint_controller/qml/core/CommonStyle.qml`
- `python/paint_controller/qml/overlays/video/components/VideoOverlayStyle.qml`
- remaining hardcoded colors and spacing in pages and overlays
- `docs/tech-debt.md` items TD-002 and TD-016

Professional target:

- one theme source or clearly layered theme extensions
- good 7-inch readability
- touch-sized targets
- no layout anti-patterns inside `RowLayout` / `ColumnLayout`

Validation:

- `tests/test_qml_imports.py`
- `tests/test_startup_smoke.py`
- `qmllint` if available
- manual visual pass on target display when possible

## Suggested Session Order

Use this order unless a production bug interrupts it:

1. Stage 0 authority map.
2. Stage 1 command, device, and workflow action-boundary freeze, with the remaining settings quick-apply gap carried explicitly into Stage 4A.
3. Stage 2 overlay and input ownership freeze.
4. Stage 3A narrow shell policy split for the two-surface shell.
5. Stage 4A settings truthfulness and Settings-route legitimacy.
6. Stage 3B route metadata and selected-route hardening.
7. Stage 4B broader settings authority, capability classes, and legality rules.
8. Stage 5 overlay contract.
9. Stage 6A current workflow stabilization.
10. Stage 6B behavior-tree preparation.
11. Stage 7 narrower QML contract where justified.
12. Stage 8 optional feature-shell recomposition.
13. Stage 9 design-system cleanup.

Why this order changed:

The validated order keeps the ownership-first direction but adds three corrections. First, it stops overstating Stage 1 by carrying the remaining settings quick-apply gap forward explicitly. Second, it blocks shell work only on the narrow Stage 2 ownership freeze rather than on every residual Stage 2 cleanup item. Third, it inserts Settings-route truthfulness before route hardening so the shell does not canonize a placeholder surface as if it were already legitimate.

## Technical Guardrails

- Never use `qmlRegisterSingletonInstance()` in this repo.
- Do not move safety logic or actuator command math into QML.
- Do not let new QML surfaces directly combine persistence writes, controller side effects, and operator intent handling in one place.
- Do not replace the broad context-property contract with one giant `Backend` object.
- Do not broaden `ShellState` into a large session or coordinator object that absorbs workflow runtime, settings authority, machine actions, and shell policy together.
- Do not let `ShellState` grow into a new shell god object that absorbs facts, bridge intents, and QML composition.
- Do not remove the overlay-first operating workflow unless the user explicitly changes product direction.
- Do not treat all overlays as transient by default.
- Do not treat the built-in touchscreen window as an auxiliary surface; it is part of the product shell.
- Do not treat “one settings location” as the architecture goal.
- Do not invest heavily in current workflow UI abstraction as if it were the final long-term automation architecture.
- Keep migrations additive while old QML consumers still exist.
- Keep `AppRuntime` as the composition root, not as a behavior god object.
- Keep cleanup order explicit and validated.
- After shell or screen changes, run startup and services validation.
- After overlay or input changes, run input and smoke validation.
- After control-state changes, run control processor and safety validation.
- After workflow changes, run workflow validation.
- After settings changes, run settings runtime validation.

## Success Metrics

Track these across sessions:

- Number of machine-affecting actions initiated directly from QML.
- Number of remaining quick-apply settings mutations that still happen directly in QML.
- Number of shell decisions computed in `MainWindow.qml` versus owned elsewhere.
- Number of places where raw screen count or raw `Qt.application.screens` data becomes product policy.
- Whether the two-surface shell has explicit named ownership.
- Number of operational overlays with explicit ownership and lifecycle rules.
- Number of settings surfaces classified by role, capability class, and authority.
- Number of placeholder local settings values remaining in QML.
- Whether the OverlayController compatibility surface has direct regression tests.
- Number of raw controller/service objects directly referenced by each major surface.
- Whether workflow UI is explicitly treated as transitional or long-term.
- Startup smoke status.
- QML import smoke status.
- Relevant focused test status.

Secondary metrics, not primary goals:

- context-property count
- number of top-level routes
- files touched to add a route

Suggested target after major refactor:

- High-risk QML action paths route through Python-owned application boundaries.
- Shell and screen policy have one obvious owner.
- The two-surface operator shell is explicit in the architecture.
- The operator overlay is explicitly part of the architecture, not accidental inherited behavior.
- Settings authority is singular even if role-specific surfaces remain plural.
- Control selection no longer shares an ownership cycle with command execution.
- Workflow remains safe and maintainable without overcommitting to a possibly transitional UI architecture.
- QML consumes fewer runtime internals because the right owners became clear.

## Plan Maintenance

When a stage is completed:

1. Add a short completion note here or in `docs/tech-debt.md`.
2. Move any resolved debt in `docs/tech-debt.md` to the resolved table.
3. Add a `DEVNOTES.md` entry if meaningful debugging occurred.
4. Update `docs/plan/00_ARCHITECTURE_PROGRESS.md` so the current stage/slice status stays truthful.
5. If a reusable gotcha is discovered, ask the user before adding it to `KNOWLEDGE.md`.

When a stage becomes wrong:

1. Do not keep following it mechanically.
2. Update this document with the new decision and reason.
3. Prefer a targeted correction over another full rewrite unless the architecture direction truly changed.

## Next Recommended Session

Stage 0 is published, Stage 1 command, device, and workflow boundaries are complete with the remaining settings quick-apply gap now carried explicitly into Stage 4A, Stage 2 is complete, and Stage 3A shell policy is complete. The next recommended session is to start Stage 4A settings truthfulness before returning to Stage 3B route hardening.

Task title: Start Stage 4A settings truthfulness.

The session should:

1. Remove placeholder or local-only state from the top-level Settings route before treating it as a real architecture surface.
2. Classify the Settings-route surfaces by real role so Stage 3B does not formalize false route semantics.
3. Remove the remaining mixed QML persistence plus direct-controller mutation path from `SettingsTab.qml`.
4. Keep the new `shellState` narrow and avoid pulling route hardening into the Stage 4A slice.
5. Create `PLANNING.md`.
6. Ask for confirmation.

The likely next implementation slice after approval:

- freeze symbol-level ownership for the overlay and input seam without changing operator behavior
- preserve dual-screen behavior
- preserve overlay-first operation
- validate joystick-selection, input, control-selection, startup, and QML import regressions before widening scope