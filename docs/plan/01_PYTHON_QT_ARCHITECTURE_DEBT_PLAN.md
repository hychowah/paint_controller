# Python Qt Architecture Debt Plan

> Created: 2026-04-25
> Reframed: 2026-04-25 after first-principles review
> Scope: Planning only. This document is a multi-session roadmap for making the Python `paint_controller` UI a more professional Qt/PySide6 application while preserving the working runtime, operator ergonomics, and safety boundaries already present in the repo.

## Executive Summary

The direction remains ownership-first. The product should stay Python-first, overlay-first, dual-surface aware, and safety conservative. What changed after the attack review and final first-principles review is not the destination. It is the precision of the route and the convergence rule.

The core purpose of this refactor is explicit:

- make the app easier to maintain by reducing blast radius and equal-owner ambiguity
- make the app easier to scale by shrinking the app-scope QML contract and clarifying feature boundaries
- make the app easier for humans to understand by ensuring each operator-visible behavior has one obvious Python owner and one obvious QML consumer
- make the app feel more like a professional Qt program because QML composes and presents, while Python owns policy, state, persistence, and machine-affecting behavior

This refactor is not being done to chase aesthetics, framework purity, or page-based neatness. It is being done to reduce global coupling and make future development more coherent.

The validated truths are these:

- Stage 1 command, device, and workflow boundary work is complete, and the last Settings quick-apply authority leak that was carried into Stage 4A has now been removed. `SettingsTab.qml` no longer mutates `teensyController` directly for thrust force.
- Stage 2 has removed the live `OverlayController` / `ControlProcessor` cycle, extracted `JoystickSelectionModel`, moved per-mode preset memory to the selection owner, and trimmed dead overlay compatibility wrappers. The remaining overlay/menu facade is now stable enough for shell work to bind to it.
- Shell work is no longer blocked on Stage 2. Stage 3A shell policy is complete, Stage 3B1 route normalization is complete, Stage 4 is complete, Stage 4.5 direct-admin boundary/default-gating is complete, Workstream A workflow runtime/editor stabilization is complete, Workstream B overlay host plus touched-surface operator legality are complete, Workstream C shell/route formalization is complete for the touched shell family, and Workstream D QML-contract reduction is now complete. The next architecture checkpoint is hybrid contract-first infrastructure: reduce the app-wide QML contract and feature-surface coupling before future automation work.
- Stage 4 is now complete: the Settings route is truthful for schema-backed mixed-admin settings, the camera route is explicit summary-only while overlay calibration remains primary, and a thin `CapabilityCatalog` now inventories settings/admin legality metadata for later shell and overlay stages.
- The top-level Settings route remains a real long-term admin or maintenance surface.
- In dual-screen mode, the built-in Steam Deck display remains the dedicated touch/control surface and the external display remains the mission surface.
- Behavior-tree migration is now a committed future direction, but the current workflow system is still a live product surface and must be stabilized on its own terms.
- The broad QML context-property contract is still the biggest remaining professionalism and scalability risk, so the next checkpoint must reduce that global surface before the roadmap invests in future automation seams or optional shell/design cleanup.

The north star is now explicit:

- each operator-visible behavior should have one canonical Python owner and one declarative QML consumer
- no checkpoint is complete until the old read path it supersedes is retired or clearly quarantined
- contract retirement starts with the first touched slice of the unfinished tail, not at the end

The roadmap now centers on six architecture goals:

1. One clear Python-owned boundary for machine-affecting application actions initiated from QML.
2. One clear authority for the coordinated two-surface shell, route semantics, and fullscreen activation state.
3. One clear authority for operational overlay state, legality, and host-surface policy.
4. One truthful settings architecture: one Python authority, intentional operator/admin surfaces, and explicit capability and legality classes.
5. One stable workflow path for the current system plus explicit seams for future behavior-tree migration.
6. A narrower, explicit QML contract that exposes operator-facing state instead of runtime internals.

That is the path toward a professional Qt program for this robot controller.

## Core Purpose Of This Refactor

The purpose of this refactor is not simply to "clean up QML" or make the tree look more modular. It is to produce a more professional Qt application in the ways that matter long-term:

- fewer places to look when understanding one operator-visible behavior
- smaller blast radius when Python internals change
- clearer ownership boundaries between QML presentation, Python policy, persistence, and machine actions
- less app-wide global exposure and more intentional feature contracts
- future changes that are easier to validate because the contract surface is smaller and more explicit

That is why the roadmap favors ownership, contract retirement, and explicit invariants over broad UI rearrangement.

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
- The runtime contract trends toward a smaller app-scope surface plus feature-scoped QObject or model contracts, not a growing global context-property bag.
- Any new read-side model or adapter should retire the old direct QML read path in the same slice when practical.
- The shell has one source of truth for navigation, surface role, fullscreen activation, and major surface visibility.
- Operational overlays are allowed to be first-class UI when the operator must preserve video or machine context during adjustments.
- Settings may appear in more than one surface if the surfaces serve different operator roles, but they must still come from one authority and present truthful semantics.
- Safety, actuator math, and emergency behavior never move into QML.
- The built-in Steam Deck display remains the touch/control surface in dual-screen mode; that is product architecture, not an incidental layout choice.
- The system is testable at the level of startup, shell behavior, screen policy, focused model logic, and safety-sensitive controller boundaries.
- A feature should have one canonical owner and one obvious read path; completing a stage should retire or quarantine superseded read paths rather than leaving two equal places to understand the same behavior.

This is not a generic desktop CRUD app. A DJI-style operating surface can be a professional result here. The professionalism comes from explicit contracts and ownership, not from forcing everything into conventional pages.

## Root Reasons The UI Feels Over-Complicated

The repo is not over-complicated mainly because it has many files. The file count is not the core problem. The real causes are below.

### Root Reason A: QML-To-Application Action Boundaries Are Too Loose

Current evidence:

- The former direct admin/calibration mutators on status, wheel, winch, tuning, and base-top calibration surfaces now route through `DeviceActionHandler`, `DeviceOperationsHandler`, `WinchMotionHandler`, `TuningAdminHandler`, and `BaseTopViewAdminHandler`.
- `AdminActionGate` now makes default runtime gating explicit in Python rather than leaving it implicit in per-surface QML behavior.
- `CapabilityCatalog` now inventories the new handler-owned authorities rather than only the old raw controller mutators.
- The runtime context contract still exposes many internal objects directly to QML, even though the highest-risk write paths are narrower than before.

Why it matters:

- The highest-risk UI boundary is not only visual complexity; it is that QML can still orchestrate application behavior too directly.
- Rearranging pages or shells without first narrowing these action paths mostly moves symptoms around.
- A professional Qt program in this domain should let QML express user intent, while Python owns machine-facing application behavior.

### Root Reason B: Shell Authority Is Split

Current evidence:

- `python/paint_controller/qml/core/MainWindow.qml` now owns the shared route manifest and selected-route writes, but it still also owns route registry details, overlay composition, and multi-screen window lifecycle.
- `python/paint_controller/models/shell_state.py` now owns narrow shell policy, while `python/paint_controller/core/qt_bridge.py` still carries imperative UI intents.
- `python/paint_controller/services/screen_manager.py` owns screen facts, but the full shell contract is still spread across Python and root QML rather than represented as one small, explicit consumer-facing contract.

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

### Root Reason E: Settings Truthfulness Is Stronger, But Admin Capability Enforcement Still Lags

Current evidence:

- `python/paint_controller/core/settings.py` is the strong persistence and validation core.
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml` now routes the thrust-force quick-apply path through `SettingsManager` only.
- `python/paint_controller/qml/pages/settings/PageSettings.qml` and its winch/wheels/arm pages are now truthful for schema-backed mixed-admin settings, while the camera route is explicit summary-only.
- `python/paint_controller/models/capability_catalog.py` now inventories settings/admin capability and legality metadata, but later stages still need to decide where legality is enforced in UI behavior.

Why it matters:

- The problem is no longer fake settings data. The remaining problem is consistent legality enforcement across route, overlay, tuning, and status surfaces.
- Trying to collapse everything into one settings location would still solve the wrong problem.
- A professional Qt architecture should support both operational quick-adjust surfaces and broader admin/setup surfaces when the workflow demands it, but it should not duplicate legality rules per surface.

### Root Reason F: Selection, Menu, And Mode-Preset Ownership Are Still Split

Current evidence:

- `python/paint_controller/models/joystick_selection.py` now owns committed and temporary selection state, and per-mode preset memory has moved to the selection owner.
- `python/paint_controller/ui/overlay.py` remains the stabilized compatibility facade for overlay/menu session behavior consumed by multiple QML surfaces.
- The live cycle is gone, but the remaining overlay-session contract is still a compatibility seam that later shell and overlay work must not widen again.

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

1. Keep the Stage 1 command, device, and workflow boundary work as complete, and keep the former Settings quick-apply exception closed now that Stage 4 resolved it explicitly instead of leaving it ambiguous.
2. Treat Stage 2 as complete and keep its stabilized overlay/menu facade as the shell-facing contract unless a concrete regression forces reopening it.
3. Run Stage 3A next: shell policy only. `ScreenManager` keeps screen facts, a narrow `ShellState` keeps product shell policy, `QtBridge` keeps imperative UI intents, and QML stays responsible for composition.
4. Treat Stage 4 as complete: the Settings route is now truthful where schema-backed settings exist, the camera route is explicit summary-only, and a thin `CapabilityCatalog` now carries executable settings/admin metadata.
5. Treat Stage 3B1 as complete: route manifest data and selected-route ownership are now unified in `MainWindow.qml` without widening `ShellState`.
6. Run the direct-admin boundary/default-gating stage next so the remaining raw QML admin/calibration mutators are removed before later legality work.
7. Treat Workstream A as complete: the workflow runner now owns the public read model, runtime/persistence semantics are explicit, and the old direct workflow QML read path is retired from the live workflow surfaces.
8. Treat Workstream B1 as complete: overlay host placement, fullscreen-video placement, joystick-overlay placement, and safety-overlay precedence are now published through one Python-owned host policy consumed declaratively by the touched QML surfaces.
9. Treat Workstream B as complete for the touched overlay families: host topology is explicit and pre-click legality now shares one result seam with handler enforcement.
10. Treat Workstream C as complete for the touched shell family: `pageKey` is canonical, the duplicate int-based shell route request path is retired, and numeric route order is internal-only.
11. Treat Workstream D as complete: the settings-family raw property-bag reads are retired and unused app-scope QML context exposure is reduced.
12. Run Workstream E1 contract-first infrastructure next: reduce the app-wide QML contract and feature-surface coupling before any future automation seam work.
13. Run the narrowed automation-contract work only after the contract-first slice materially reduces global coupling.
14. Leave optional feature-shell recomposition and design-system cleanup downstream only if they are still justified after the contract-first and automation slices.

## Active Execution Framework

Completed stages through Stage 4.5 remain the historical record of how the repo reached the current state.

Unfinished work is now governed by active workstreams rather than a simple future stage ladder. That change is deliberate because the remaining dependency graph is only partially linear: workflow stabilization, overlay hosting, legality, route formalization, and contract reduction are related, but they are not best managed as one serial bucket list.

The governing rules for the unfinished tail are:

- one active checkpoint per workstream at a time
- at most two workstreams in active implementation simultaneously
- each checkpoint must name the canonical owner it is establishing
- each checkpoint must retire or clearly quarantine the old read path it supersedes
- no new additive QML contract should be introduced without an explicit retirement or quarantine decision for the touched family

The current unfinished tail now starts with contract-first infrastructure. That means reducing the app-wide QML contract and giving feature surfaces smaller, more legible contracts before the roadmap invests in future automation seams or optional shell/design recomposition.

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

- At the end of Stage 1, the quick-apply settings path in `SettingsTab.qml` was not treated as fully complete boundary work. It was carried forward explicitly into Stage 4A because it overlapped long-term settings truthfulness and surface-legitimacy work.

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

The product already behaves as a coordinated external mission surface plus built-in touch-operated surface, and Stage 3A has now made that shell policy explicit with a narrow `ShellState`. Stage 4 has also completed the Settings-route truthfulness prerequisite. The remaining Stage 3 work is narrower: route manifest data and selected-route ownership are still split across `MainWindow.qml` and `SelectBar.qml`, and the next step is to normalize that before formal route semantics are frozen.

Professional target:

- `ScreenManager` remains the owner of screen facts, not product policy.
- `ShellState` remains the owner of screen-derived shell policy such as surface roles, secondary-surface existence, and fullscreen activation policy.
- `QtBridge` remains the owner of imperative UI intents.
- Route identity and selected-route ownership stay out of `ShellState`; if a dedicated route owner is still justified later, it should be introduced as its own narrow contract.
- Root QML becomes thinner and more declarative, but still composes the actual windows.

Stage structure:

- Stage 3A: shell policy only. Name the two product surfaces explicitly, move surface-role assignment, secondary-window ownership, emergency precedence, and fullscreen activation policy out of root QML, and keep video-workspace internals out of scope.
- Stage 3B1: route manifest normalization and selected-route ownership unification now that Stage 4 has made the Settings route truthful enough to formalize later.
- Stage 3B2: route metadata and selected-route formalization only after overlay hosting and legality semantics are clear enough to freeze route vocabulary without guessing.

Progress note:

- 2026-04-26: Stage 3A is complete. `ShellState` now owns screen-role and secondary-surface policy, `MainWindow.qml` consumes shell policy instead of inventing it from raw screen count, and focused shell/startup/runtime validation is green.
- 2026-04-26: Stage 3B1 is complete. `MainWindow.qml` now owns the shared route manifest and selected-route writes, `SelectBar.qml` renders from that manifest and emits navigation requests, and focused Stage 3B1 shell/import validation is green.

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

Status: completed on 2026-04-26.

Implementation summary:

- Stage 4A is complete: `PageSettings.qml` no longer carries fake placeholder state, schema-backed settings now live truthfully on the mixed admin route for winch/wheels/arm, the camera route is explicit summary-only, and `SettingsTab.qml` no longer mutates `teensyController` directly for thrust force.
- Stage 4B is complete: `CapabilityCatalog` now publishes executable settings/admin metadata covering route pages, settings surfaces, and the admin/calibration mutators that were still direct at the end of Stage 4 before Stage 4.5 moved them behind Python-owned boundaries.
- The next work is no longer Stage 4, Workstream A, or Workstream B. Stage 3B1 route normalization, Stage 4.5 direct-admin boundary/default-gating, Workstream A workflow runtime/editor stabilization, and Workstream B overlay host plus touched-surface operator legality are complete, and the next checkpoint is Workstream C shell/route formalization before later contract-reduction slices.

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

## Stage 4.5: Freeze Direct-Admin Boundaries And Default Gating

Goal: remove the remaining raw QML admin/calibration mutators and make maintenance or safe-stop gating explicit before overlay-legality or route-formalization work freezes the wrong seams.

Complexity: High
Risk: High
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/qml/pages/status/PageStatus.qml`
- `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`
- `python/paint_controller/qml/pages/winch/PageWinch.qml`
- `python/paint_controller/qml/pages/tuning/PageTuning.qml`
- `python/paint_controller/qml/overlays/video/components/BaseTopViewSettingsPopup.qml`
- `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`
- `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`
- candidate narrow Python-side admin boundary files justified by the chosen slice
- `python/paint_controller/core/app_runtime.py`
- `python/paint_controller/models/capability_catalog.py`
- relevant focused controller/settings/runtime tests for the touched slice

Current problem:

The largest remaining professionalism and safety gap is no longer fake settings state. It is that several admin and calibration surfaces still call live controller or service mutators directly from QML. That keeps legality and maintenance-mode policy split across QML exceptions instead of giving Python one clear boundary for machine-affecting admin intent.

Professional target:

- QML expresses admin or calibration intent through one narrow Python-owned boundary per coherent surface family.
- Maintenance or safe-stop gating is explicit by default, with live-operational exceptions called out deliberately rather than inherited accidentally.
- `CapabilityCatalog` can remain metadata, but later legality work must consume it through a real boundary or UI contract rather than prose alone.
- Stage completion reduces places to look, not just places to write: once a surface gets a canonical owner, the old direct read/write path is retired or clearly quarantined.

Design rule:

Prefer one coherent admin boundary only while it stays understandable. If calibration and live admin paths diverge enough to make one object incoherent, split by surface family rather than forcing a broad catch-all gateway.

Exit criteria:

- The remaining direct admin/calibration mutators on status, winch, tuning, base-top calibration, and overlay settings surfaces no longer call raw controller or service mutators from QML.
- Maintenance versus live-operational exceptions are explicit in code and tests.
- Later legality work has a real enforcement or presentation seam to consume instead of metadata-only inventory.

Validation:

- focused tests for the touched admin boundary slice
- `tests/test_settings_runtime.py`
- `tests/test_teensy.py`
- `tests/test_winch.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

## Active Workstream A: Workflow Runtime And Editor Stabilization

Historical aliases: Stage 6A current-system stabilization and Stage 6B behavior-tree preparation.

Goal: make the current workflow system behave like a professional Qt-facing feature contract now, while keeping future automation seam design separate and explicit.

Complexity: Medium
Risk: High
Suggested sessions: 3 to 5 small checkpoints
Status: completed on 2026-04-26

Completion summary:

- `WorkFlowExecutor` now publishes canonical workflow-order current-action identity, including position-triggered actions.
- `WorkFlowRunner` now owns the workflow display/read model, progress/runtime state, and loaded-document reload signal consumed by the live QML workflow surfaces.
- `WorkflowCatalog` ordering is stable, `WorkflowEditor` writes atomically with normalization and explicit runtime collision rules, and focused workflow validation plus the full suite are green.

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

The workflow runtime is already a QML-facing contract, but QML still reconstructs action data ad hoc, persistence semantics remain weaker than the rest of the repo, and the editor/runtime interaction rules are not explicit enough for a long-lived operator-facing feature.

North-star rule for this workstream:

- one canonical Python owner for workflow runtime state
- one declarative QML consumer contract for workflow status and action display
- the old direct QML read path must be retired or quarantined in the same slice that introduces the replacement

Checkpoint A1: Workflow public read model

- Establish one canonical source of truth for current action identity, current action description, progress, loop state, and runtime.
- Remove repeated binding-time reconstruction of workflow action summaries from QML.
- Preserve current operator behavior unless the slice intentionally clarifies an already-ambiguous contract.
- Retire the old direct QML workflow read path it replaces, starting with ad hoc `workFlowRunner.get_current_workflow_actions()` reconstruction.

Checkpoint A2: Workflow persistence hardening

- Define atomic save semantics for workflow persistence.
- Make workflow ordering stable instead of inheriting raw directory iteration order.
- Clarify normalization and validation boundaries for editor-facing workflow documents.
- Keep the shared catalog as the single directory owner for runtime and editor surfaces.

Checkpoint A3: Workflow editor/runtime collision rules

- Make explicit what happens if a workflow is edited, saved, deleted, or reloaded while loaded or executing.
- Keep `EditWorkFlowTab.qml` explicitly transitional and do not treat it as the final automation architecture.
- Keep future behavior-tree migration as a seam-design checkpoint, not a preemptive rewrite.

Validation:

- `tests/test_workflow_runner.py`
- `tests/test_workflow_editor.py`
- `tests/test_workflow_executor.py`
- `tests/test_workflow_scheduler.py`
- focused smoke for `WorkFlowTab.qml` and `WorkFlowStatusOverlay.qml`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`

## Active Workstream B: Overlay Contract And Operator Legality

Historical aliases: Stage 5A overlay hosting/layering and Stage 5B operator-action legality.

Goal: turn the overlay-first operator model into an explicit, testable contract before route semantics and broader contract-reduction work depend on it.

Complexity: High
Risk: High
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`
- `python/paint_controller/qml/overlays/JoystickOverlay.qml`
- `python/paint_controller/qml/features/video/VideoFullscreenWorkspace.qml`
- `python/paint_controller/qml/core/MainWindow.qml`
- `python/paint_controller/qml/overlays/MultiScreenListUI.qml`
- `python/paint_controller/ui/overlay.py`
- `python/paint_controller/models/capability_catalog.py`
- `python/paint_controller/models/admin_action_gate.py`

Current problem:

The operator overlay is real product architecture. Workstream B made the touched host placement, layering, and legality rules explicit enough that later route and contract-reduction work can consume them without guessing.

Status: Workstream B completed on 2026-04-26.

Checkpoint B1: Overlay host and layer matrix

- Publish the canonical host matrix for single-screen mode, dual-screen mode, emergency active, joystick menu active, and video fullscreen active.
- Classify each overlay-like surface as operational overlay, safety override, modal popup, admin/setup overlay, diagnostic overlay, or transitional overlay.
- Define coexistence and precedence rules explicitly instead of leaving them in ad hoc `z` relationships.
- Move any state that must survive host changes out of duplicated local QML instances.

Checkpoint B1 completion summary:

- `OverlayHostPolicy` now owns the touched overlay host and layer matrix in Python.
- `MainWindow.qml` and `MultiScreenListUI.qml` now consume that contract declaratively for system-control, joystick, emergency, and fullscreen-video placement.
- `ShellState` remains the narrow screen-role owner and `OverlayController` remains the menu-session owner rather than absorbing host policy.

Checkpoint B2: Operator-action legality

- Use `CapabilityCatalog` and `AdminActionGate` as seams, not as already-finished legality architecture.
- Make handler enforcement and UI affordance state come from the same legality result shape.
- Do not call legality complete until blocked actions can be explained before click, not only rejected after click.

Checkpoint B2 completion summary:

- `ActionLegalityModel` now exposes one QML-facing legality result seam over `AdminActionGate` plus `CapabilityCatalog`, and `AppRuntime` registers it as `actionLegality`.
- The gated `DeviceControlTab.qml` affordance family now consumes legality through the shared `ControlPanel.qml` and `ActionButton.qml` contracts instead of relying only on post-click handler rejection.
- `BaseTopViewSettingsPopup.qml` now consumes the same legality seam for live adjustments, save, and reset, so blocked actions are explained before click on the touched overlay-primary calibration surface.

Validation:

- `tests/test_input_handler.py`
- `tests/test_shell_state.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- services runtime tests if screen behavior changes
- focused legality tests for touched handler and UI families
- manual operator validation on target hardware when possible

## Completed Workstream C: Shell And Route Formalization

Historical alias: deferred Stage 3B2 route formalization.

Goal: finish the shell contract only after overlay host and legality semantics are explicit enough that route vocabulary will not freeze the wrong product shape.

Complexity: Medium
Risk: High
Suggested sessions: 1 to 3

Primary files:

- `python/paint_controller/qml/core/MainWindow.qml`
- `python/paint_controller/qml/navigation/SelectBar.qml`
- `python/paint_controller/models/shell_state.py`
- `tests/test_startup_smoke.py`
- `tests/test_qt_bridge.py`
- `tests/test_services_runtime.py`

Rules:

- Keep `ShellState` narrow.
- Do not smuggle route ownership, legality, workflow state, or broad session coordination into shell policy objects.
- Make `pageKey` the canonical route identity before formal route work proceeds.
- Treat numeric `pageIndex` as transitional presentation state only.

Validation:

- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- `tests/test_qt_bridge.py`
- `tests/test_services_runtime.py`

Delivered result:

- `pageKey` is now the canonical top-level route identity in the touched shell family.
- `MainWindow.qml` owns key-based route resolution and keeps numeric route order internal-only for StackView transition behavior.
- `SelectBar.qml` now emits key-based navigation requests and no longer carries duplicate route lookup logic.
- Focused shell/import validation is green at `17 passed`, and the full suite is green at `245 passed`.

## Completed Workstream D: QML Contract Reduction

Historical alias: Stage 7 narrower QML contract.

Goal: reduce the mental surface area of the runtime/QML contract by retiring direct access paths as stable owners become real.

Complexity: Medium
Risk: Medium
Suggested sessions: 2 to 5

Primary files:

- `python/paint_controller/core/app_runtime.py`
- `python/paint_controller/core/controller_factory.py`
- candidate focused models/adapters only where justified

Rules:

- This remains a dedicated workstream, but its retirement rule starts immediately in any earlier touched slice.
- New models or adapters must reduce real cross-cutting coupling, not just move names around.
- Success is not a lower context-property count by itself. Success is fewer places a maintainer must inspect to understand one operator-visible behavior.

Bad outcomes:

- wrappers added only to reduce a metric
- large “everything UI needs” objects
- additive context properties with no retirement decision

Validation:

- `tests/test_settings_runtime.py`
- `tests/test_controller_factory_runtime.py`
- `tests/test_startup_smoke.py`
- `tests/test_qml_imports.py`
- focused tests for any new adapter/model

Delivered result:

- `SettingInputField.qml` and `ManagedSettingSpinBox.qml` consume typed `SettingsManager` helper slots plus `setting_changed` refresh instead of raw `settingsManager` property/index access.
- The Settings route summary pages now consume owner-side summary helpers instead of formatting raw settings values directly in page QML.
- The last inline thrust-force and thrust-ramp-rate special cases in `SettingsTab.qml` now use the same shared typed settings contract as the rest of the settings family.
- Unused `capabilityCatalog`, `steamDeckHandler`, and `windMonitor` exposure is retired from the app-scope QML context contract.
- Focused Workstream D contract validation is green at `35 passed`, and the full suite is green at `248 passed`.

## Active Workstream E: Contract-First Infrastructure And Downstream Automation

Historical aliases: the former Workstream E future automation seam design, Stage 6B behavior-tree preparation, Stage 8 optional feature-shell recomposition, and Stage 9 design-system cleanup.

Goal: make the app more professional first by shrinking the app-wide QML contract and feature-surface coupling before future automation and optional shell/design cleanup proceed.

Complexity: High
Risk: High
Suggested sessions: 2 to 5 for the contract-first slice, downstream only afterward for automation and optional cleanup

Rules:

- Treat `AppRuntime` as the composition root, not as a behavior god object or permanent service locator.
- Any slice that touches `python/paint_controller/core/app_runtime.py` must retire at least one direct app-scope QML read path in the same change, or it does not count as maintainability progress.
- Keep `ShellState`, `OverlayHostPolicy`, and the completed route/overlay ownership splits narrow; shell cleanup is allowed only when it directly retires a global dependency or duplicate ownership path.
- Keep `EditWorkFlowTab.qml` explicitly transitional; do not use its current placement as justification for broad shell recomposition.
- Future automation work stays downstream from the contract-first slice, and optional feature-shell recomposition plus design-system cleanup stay non-blocking unless the user explicitly reprioritizes them.

Checkpoint E1: App-wide QML contract reduction

- Reduce the app-scope context-property surface where a touched slice can retire a real direct QML read path.
- Prefer smaller feature-facing contracts over continued reliance on app-wide global exposure.
- Do not add new mega-owners such as `Backend`, `OperatorSession`, or an expanded `ShellState`.

Checkpoint E2: Feature-surface contract reduction

- Make feature roots such as `SystemControlWorkspace.qml` more architectural and less dependent on broad app-scope runtime exposure.
- Touch `MainWindow.qml` only when it directly clarifies ownership or retires a global dependency.
- Keep existing workflow runtime boundaries valid while reducing feature-surface coupling.

Checkpoint E3: Narrowed automation-contract work

- Only after E1 and E2 materially reduce global coupling.
- Define future automation seams without speculative workflow UI rewrites.
- Keep behavior-tree preparation explicit and downstream from the already-stabilized current workflow contract.

## Suggested Session Order

Use this order unless a production bug interrupts it:

1. Stage 0 authority map.
2. Stage 1 command, device, and workflow action-boundary freeze, with the remaining settings quick-apply gap carried explicitly into Stage 4A.
3. Stage 2 overlay and input ownership freeze.
4. Stage 3A narrow shell policy split for the two-surface shell.
5. Stage 4 settings truthfulness and executable capability model.
6. Stage 3B1 route normalization.
7. Stage 4.5 direct-admin boundary and default gating.
8. Workstream A workflow runtime and editor stabilization.
9. Workstream B1 overlay host and layer matrix.
10. Workstream B2 operator-action legality.
11. Workstream C route formalization.
12. Workstream D dedicated QML-contract reduction, while continuing touched-slice retirement rules.
13. Workstream E1 app-wide QML contract reduction and feature-surface narrowing.
14. Workstream E2 narrowed automation-contract work only after the contract-first slice materially reduces global coupling.
15. Optional feature-shell recomposition if still justified.
16. Design-system cleanup.

Why this order changed:

The validated order keeps the ownership-first direction but adds one more first-principles rule to the previous corrections: contract retirement starts now. The next workflow checkpoint is not allowed to add a new read model while leaving the old workflow QML read path equally live. That rule exists to make the repo materially easier to understand, not only safer to modify.

## Technical Guardrails

- Never use `qmlRegisterSingletonInstance()` in this repo.
- Do not move safety logic or actuator command math into QML.
- Do not let new QML surfaces directly combine persistence writes, controller side effects, and operator intent handling in one place.
- Do not replace the broad context-property contract with one giant `Backend` object.
- Prefer a smaller app-scope contract plus feature-scoped models over continued growth of the global context-property surface.
- Do not broaden `ShellState` into a large session or coordinator object that absorbs workflow runtime, settings authority, machine actions, and shell policy together.
- Do not let `ShellState` grow into a new shell god object that absorbs facts, bridge intents, and QML composition.
- A stage is not complete until it names the canonical owner and retires or clearly quarantines the superseded read path.
- Do not remove the overlay-first operating workflow unless the user explicitly changes product direction.
- Do not treat all overlays as transient by default.
- Do not treat the built-in touchscreen window as an auxiliary surface; it is part of the product shell.
- Do not treat “one settings location” as the architecture goal.
- Do not invest heavily in current workflow UI abstraction as if it were the final long-term automation architecture.
- Contract retirement starts with the next touched slice of the unfinished tail, not as a final cleanup-only stage.
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
- Number of touched slices that retire an old read path in the same change.
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

Stage 0 is published, Stage 1 command, device, and workflow boundaries are complete, Stage 2 is complete, Stage 3A shell policy is complete, Stage 3B1 route normalization is complete, Stage 4 is complete, Stage 4.5 is complete, Workstream A is complete, Workstream B is complete, Workstream C is complete for the touched shell family, Workstream D is complete, and Workstream E is active in progress. The next recommended session is to continue Workstream E1 contract-first infrastructure after slices 1-2 retired the workflow/editor and system-control command globals behind `systemControlServices`.

Task title: Continue Workstream E1 app-wide QML contract reduction after slices 1-2.

The session should:

1. Use the completed shell route contract, host matrix, legality seam, Workstream D reductions, and the completed E1 slices 1-2 as fixed inputs rather than reopening them in the same slice.
2. Continue reducing the app-wide QML contract or feature-surface dependence in a way that retires at least one additional real direct app-scope read path.
3. Preserve the narrow `ShellState` / `OverlayHostPolicy` / `QtBridge` ownership boundaries while contract reduction proceeds.
4. Keep future automation work separate from optional feature-shell redesign or broader product/UI cleanup.
5. Keep startup/import smoke green and add focused tests for any new feature-facing contract.
6. Create `PLANNING.md`.
7. Ask for confirmation.

The likely next implementation slice after approval:

- keep the current shell, overlay, legality, settings, and workflow runtime contracts stable while reducing app-scope QML exposure further
- make the next touched feature surfaces consume smaller, clearer contracts before future automation work starts
- validate focused contract tests plus startup and QML import coverage before widening scope