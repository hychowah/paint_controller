# Tech Debt Tracker

Living document. Update when debt is discovered, addressed, or re-prioritised.

**Priority**:
- `high` = blocking quality/correctness, or breaks a stated architecture invariant (e.g. single gated write path)
- `medium` = degrades maintainability or long-term structure
- `low` = cosmetic / nice-to-have / pure UI chrome

**Architecture leverage** (optional tag on items): how much a fix improves FE↔BE program structure when doing architecture work, independent of ship-blocking urgency.

Last multi-perspective re-validation: **2026-07-28** (program-side FE+BE focus; UI/UX and industrial HMI deferred). Diagnoses from the 2026-07-27 review largely reconfirmed; priorities and gaps below were adjusted from that pass.

---

## Program-track recommended order

When the goal is **frontend + backend program architecture** (not UI chrome, not HMI product semantics), prefer this order over raw ID order:

| Rank | ID | Why |
|---|---|---|
| 1 | **TD-038** structural half | Domain out of QML; god-file size (defer tokens) |
| 2 | **TD-037** | Highest structural ROI on the QML↔Python joint; high effort — slice it |
| 3 | **TD-046 / TD-047** | Backend module shape after the surface is honest |
| 4 | **TD-044 + TD-045**, then **TD-040** | Make CI/types real control planes |
| 5 | **TD-042 / TD-043 / TD-041** | Hygiene |
| — | **TD-002 / TD-016** | Out of scope for a pure program track |
| — | **TD-032** | Resolved 2026-07-28 |
| — | **TD-036** | Resolved 2026-07-28 |
| — | **TD-039** | Resolved 2026-07-28 |

---

## Active Debt

### TD-037 — Status wrapper layer: blanket notify, stringly reads, duplicated telemetry
**Area**: QML↔Python boundary
**Priority**: medium
**Effort**: high
**Architecture leverage**: high
**Why it matters**: `qml_context_composer.py` (~1195 lines, largest Python file) re-implements the per-property NOTIFY the controllers already have — worse: one blanket `changed` signal fans ~50 properties per wrapper (every teensy tick re-evaluates every binding), `_connect_if_signal` silently skips missing signals (a controller-side rename becomes invisible drift), `_read_object_value`'s duck-typed fallbacks exist partly to tolerate test fakes in production code, and physical values are duplicated under multiple names (battery voltage ×3 across `_VideoRuntimeTopBar`/`_TeensyStatus`/`_WinchStatus`; SSH reachability ×2). Composer mixes **registration** (composition concern) with **presentation-model implementation**. Violates the retirement program's own "no controller-shaped mirrors / no shallow wrappers" principles. Also found by TD-033 contract tests (2026-07-27): `OverlayHostPolicy`'s `screen_count_changed → refresh_layout` is a dead input; `ShellRouter.route_registry_changed` has no emission path (registry built once — property could be `constant`). Both pinned as intentional in `tests/test_notify_contracts.py` until this item is worked.
**What to do**: Long-term: move per-property NOTIFY onto controller-owned (or feature-owned) read-only status QObjects; delete most composer wrapper classes; leave composer as a pure registrar that builds the context dict. Consolidate one canonical owner per physical value; keep the `*Actions`/gating models (the program's real win). Slice by family (winch/teensy/video) — do not rewrite the file in one PR.
**Files**: `python/paint_controller/core/qml_context_composer.py`, `python/paint_controller/controllers/winch.py`, `python/paint_controller/controllers/teensy.py`

---

### TD-038 — File-scale QML decomposition: PageWinch, EditWorkFlowTab, TeensyStatus
**Area**: QML structure (program) / UI tokens (deferrable)
**Priority**: medium
**Effort**: high
**Architecture leverage**: high (structural half)
**Why it matters**: `PageWinch.qml` is ~1606 lines with duplicated ~120-line control blocks and hand-rolled toggles despite `TouchSwitch` — pure **module size / change-cost** debt. `EditWorkFlowTab.qml` (~1027 lines) builds and JSON-serializes the workflow document in JavaScript (`saveWorkflow()`) — **business logic in the view layer**, the worst program-side FE smell. Zero/`CommonStyle` and ~70 hardcoded colors are real but **UI chrome** (also TD-002); do not block structural work on tokenization. These files are the maintenance risk the boundary program never touched.
**What to do**:
1. **Program first:** extract reusable winch control components; move workflow document assembly/save into the Python workflow editor model so QML only edits UI state and calls slots.
2. **UI later:** tokenize with `CommonStyle` only as files are touched (or under TD-002).
**Files**: `python/paint_controller/qml/pages/winch/PageWinch.qml`, `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`, `python/paint_controller/services/workflow/workflow_editor.py`

---

### TD-046 — ControlProcessor teleop monolith; second command path undocumented
**Area**: Backend / handlers
**Priority**: medium
**Effort**: medium
**Architecture leverage**: medium
**Why it matters**: Surfaced 2026-07-28 program-side review. `control_processor.py` (~959 LOC) owns curve math, per-effector dispatch, display sync, settings callbacks, and QML-facing properties in one unit — high blast radius for any teleop change. Continuous motion intentionally bypasses `AdminActionGate` (rate limits + winch ONTASK lock only). That split (discrete gated slots vs continuous teleop) is often correct for HMIs, but it is **not documented as a second command policy**, so new code may wrongly assume "everything goes through the gate." Related (deferred HMI/policy): after `SafetyCoordinator.halt_all_effectors()`, teleop is not latched off via ERROR/inhibit — track only if product wants hard post-halt inhibit.
**What to do**: Document the two command paths at module top (and in architecture plan if needed). Split by effector (track / winch / valve / wheel travel) behind one `process_input` dispatcher when a teleop change needs isolation. Optionally add a single `SafetyCoordinator.is_motion_allowed` (or equivalent) read if latched inhibit becomes a product requirement — not required for pure structure work.
**Files**: `python/paint_controller/handlers/control_processor.py`, `python/paint_controller/core/signal_wiring.py`, `python/paint_controller/handlers/safety_coordinator.py`

---

### TD-047 — AppRuntime service-locator attribute surface
**Area**: Backend / composition
**Priority**: medium
**Effort**: low
**Architecture leverage**: medium
**Why it matters**: Surfaced 2026-07-28. `AppRuntime` is correctly the composition root, but after Phase 8 extraction it still re-exports a large set of optional façades as `self.*` (status objects, action models, etc.) so wiring/tests can poke them. Composition roots may know everything; **mirroring every context key on the instance** blurs ownership and makes the class a god-object at the type level. Lower urgency than TD-037 (composer) but compounds mental load when adding devices.
**What to do**: Prefer `ControllerBundle` + a small ports/composer-output object; stop growing new `self.<facade>` fields when a local wire variable or bundle field suffices. No behavior change required for a first pass — reduce new surface and shrink when a touched family allows it.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/core/qml_context_composer.py`, `python/paint_controller/core/controller_factory.py`

---

### TD-040 — pyright allowlist excludes the riskiest modules
**Area**: Tooling / CI
**Priority**: medium
**Effort**: medium
**Architecture leverage**: medium
**Why it matters**: `pyrightconfig.json` `include` cherry-picks scope; it excludes `services/` (`video_stream.py`, `base_top_view_service.py`, workflow — the threading-heaviest code), `core/app_runtime.py`, `ui/`, `widgets/`, `utils/`, and runs `basic` mode. "Pyright green" currently proves little about the whole.
**What to do**: Widen `include` incrementally (services first), fix the fallout, keep the gate green.
**Files**: `pyrightconfig.json`

---

### TD-044 — Ruff lint debt on `dev` (1965 check errors, 111 format failures)
**Area**: Tooling / CI
**Priority**: medium
**Effort**: medium
**Architecture leverage**: high *for process* (until green, remote gates are theater)
**Why it matters**: Surfaced 2026-07-27 by TD-034: the CI `lint` job (ruff check + ruff format --check on `python/` and `tests/`) is red on `dev` — 1965 check errors (mostly W293 blank-line-with-whitespace, UP006, W292, I001, F401) and 111 files failing the format check. It was invisible because CI never ran on `dev`. Until fixed, the lint job is normalized-red and `typecheck`/`test` stay blocked behind `needs: lint`.
**What to do**: Bulk-fix mechanically (`ruff check --fix` + `ruff format`) in one dedicated commit with no behavior changes, then keep the job green. Coordinate with open branches to avoid merge pain. Pair with TD-045.
**Files**: `pyproject.toml` (ruff config), `python/`, `tests/`, `.github/workflows/ci.yml`

---

### TD-045 — CI test/typecheck jobs missing system dependencies
**Area**: Tooling / CI
**Priority**: medium
**Effort**: low
**Architecture leverage**: high *for process* (with TD-044)
**Why it matters**: Surfaced 2026-07-27 by TD-034: the CI `test` and `typecheck` jobs pip-install `python/paint_controller/requirements.txt`, which includes `PyGObject` — source-only (no binary wheels), needing girepository/cairo dev headers the runner lacks; PySide6 also needs Qt runtime libs (`libegl1`, `libxkbcommon`, …). The jobs have zero apt steps, so they will fail on a clean runner now that CI triggers on `dev`.
**What to do**: Add an apt step (girepository/cairo dev headers, Qt runtime libs) to both jobs, or trim `requirements.txt` for CI; verify green on a real runner.
**Files**: `.github/workflows/ci.yml`, `python/paint_controller/requirements.txt`

---

### TD-002 — Design system incomplete (systemcontrol/video remainder, pages)
**Area**: QML UI
**Priority**: low
**Effort**: medium
**Architecture leverage**: low (UI chrome)
**Why it matters**: Hardcoded colours, spacing, and font sizes in the remaining untokenized files will diverge from the rest of the UI and make theme-wide changes expensive later, but this is not the architecture-driving problem. Worst structural offender (`PageWinch.qml`) is tracked under TD-038; token cleanup there is explicitly deferrable.
**What to do**: Resume remaining `CommonStyle` rollout only after program-track structure work is stable, or when a file is already open for TD-038. Not feature-blocking.
**Files**: `python/paint_controller/qml/overlays/systemcontrol/`, `python/paint_controller/qml/overlays/video/`, `python/paint_controller/qml/pages/home/`, `python/paint_controller/qml/pages/wheel/`, `python/paint_controller/qml/pages/winch/`, `python/paint_controller/qml/pages/tuning/`, `python/paint_controller/qml/pages/settings/`, `python/paint_controller/qml/pages/status/`

---

### TD-016 — `VideoOverlayStyle.qml` compatibility-wrapper cleanup
**Area**: QML UI
**Priority**: low
**Effort**: low
**Architecture leverage**: low
**Why it matters**: `VideoOverlayStyle.qml` no longer owns its own tokens, but it still preserves a parallel style API for older video overlay components. That wrapper layer keeps imports stable, but it also delays a clean direct dependency on `CommonStyle`.
**What to do**: Retire the wrapper-only API once the remaining video overlay callers can read `CommonStyle` directly, or keep the file as a thin documented compatibility shim if import churn is intentionally deferred.
**Files**: `python/paint_controller/qml/overlays/video/components/VideoOverlayStyle.qml`

---

### TD-041 — Governance/doc hygiene: stale plan entries, KNOWLEDGE.md mis-citation
**Area**: Docs
**Priority**: low
**Effort**: low
**Architecture leverage**: low
**Why it matters**: `00_ARCHITECTURE_PROGRESS.md`'s frozen list declares route identity owned in `MainWindow.qml` in the same file that declares Phase 7 (which moved it to `ShellRouter`) complete; its quarantine list still names `PageWheel.qml`'s `baseStreamHandler` seam, which no longer exists. `KNOWLEDGE.md`'s singleton entry cites PYSIDE-2160/2310 as a "known bug family" — both are unrelated issues fixed in Qt 6.5.x and the repo runs PySide6 6.10.1; the conclusion (avoid `qmlRegisterSingletonInstance` with implicit directory imports) is defensible, but the cited reasoning blocks legitimate typed-registration options (`qmlRegisterUncreatableType`, `@QmlNamedElement`). `AGENTS.md` also references a `launch/` directory that does not exist. Progress board "Next" still soft-offers more retirement targets; TD-032 is firmer: close the program, then stop.
**What to do**: Correct the KNOWLEDGE.md entry (user confirmation required per KNOWLEDGE.md rules), refresh or retire the stale frozen/quarantine entries, align progress-board "Next" with TD-032 close-out, fix the `launch/` reference.
**Files**: `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `KNOWLEDGE.md`, `AGENTS.md`

---

### TD-042 — Over-fitted test mirror and structural-selfie assertions
**Area**: Tests
**Priority**: low
**Effort**: medium
**Architecture leverage**: medium
**Why it matters**: `startup_smoke_support.py` (~1095 lines, 27 hand-maintained fake context classes) re-implements the models' QML APIs property-by-property; `FakeShellRouter` hand-copies the route registry, so a production route reorder keeps the suite green while navigation breaks; `controller_factory_runtime_support.py` (~447 lines, ~107 recorder classes) largely asserts that wiring wires what it wires; per-test `fatal_warning_fragments` tuples are copy-pasted Qt warning strings (version-brittle). Correctness depends on a human remembering to update the mirror each phase — dual source of truth next to `_EXPECTED_CONTEXT_PROPERTY_NAMES`.
**What to do**: Derive static fake contracts from production (e.g. build `FakeShellRouter` from the real route registry), collapse warning tuples into one `assert_no_fatal_qml_warnings()` helper, keep the shutdown-order and name-parity assertions, delete the structural selfies.
**Files**: `tests/startup_smoke_support.py`, `tests/controller_factory_runtime_support.py`, `tests/test_startup_smoke_shell.py`

---

### TD-043 — Dead/duplicated state and metadata layers
**Area**: State management
**Priority**: low
**Effort**: medium
**Architecture leverage**: low–medium
**Why it matters**: `StateStore` is ~60% dead state (`left/right_joystick_control`, `*_control_mode/value` have no writers/readers; QML reads only `display_message`) while its "single source of truth" branding invites writes to the wrong place. `CapabilityCatalog` (~559 lines) + metadata registry has 3 QML call sites in one popup. `SignalWiring.wire()` writes `runtime._heartbeat_status_error`, which nothing reads; uncalled convenience functions exist in `signal_wiring.py` / `qml_context_composer.py`.
**What to do**: Delete the dead StateStore surface or make it Python-internal (pairs with TD-032 `stateStore` retirement); reduce CapabilityCatalog to what the popup consumes (or fold legality into the gate); delete dead writes and uncalled functions.
**Files**: `python/paint_controller/core/state_store.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/core/signal_wiring.py`, `python/paint_controller/core/qml_context_composer.py`

---

## Resolved Debt

| ID | Title | Resolved | Notes |
|---|---|---|---|
| TD-032 | QML boundary retirement program: close out honestly, then stop | 2026-07-28 | Retired deviceActionHandler into teensyActions/winchActions; stateStore root → qtBridge.display_message; backend renamed qtBridge; freeze root list (26 names, no vanity 12–15); boundary program closed. 62 passed focused band |
| TD-036 | Settings: ungated QML writes, dual API, in-tree path; legality ship default | 2026-07-28 | QML apply*/set*/saveSetting gated via AdminActionGate (setting-capability fallback + mixed-admin-route/safety-admin); read-only generated Properties; SettingInputField→apply*; deny refresh in ManagedSettingSpinBox; live path env/XDG with template migrate+legality sanitize; lab bypass PAINT_ACTION_LEGALITY_ENFORCED; ship template no longer disables gate. Focused band 45+ passed |
| TD-039 | Concurrency loose ends: BaseTopView race, ROS error path, in-lock emit, image null cleanup | 2026-07-28 | (1) Worker-owned map recompute via `mapsRecomputeRequested` + 0ms coalesce timer; k setters no longer write `dist_coeffs` on GUI. (2) `RosThread.error_occurred` → `SignalWiring` → `StateStore.display_message` (throttled); removed dead `_last_spin_time`/`_spin_timeout`. (3) `button_held` collected under lock, emitted after unlock. (4) `ImageProvider` never-None placeholder under lock + defensive `requestImage`. Focused band 19 passed (`test_video_stream`, `test_base_top_view_service`, `test_steam_deck_handler`, `test_signal_wiring`). Residual: GUI may still write scalar float params while worker reads them |
| TD-035 | View-authoritative toggle commands; optimistic device state never reconciled | 2026-07-28 | Arg-less backend-authoritative toggles in 5 commits (`b84346f`..`19aa335`): relay/enable negate firmware echo, six un-echoed fields negate controller intent, wheel intent tracking, TouchSwitch request-only binding fix, typo rename, lidar backend state. Hardware-validated on the live rig; suite 373 passed, pyright green. Reconnect reconciliation deliberately not built — pending the operator's firmware echo of the six user-controlled fields |
| TD-033 | Zero behavioral UI / NOTIFY-contract test coverage | 2026-07-27 | `tests/test_notify_contracts.py` (48 tests: ShellState/OverlayHostPolicy/ShellRouter + composer-wrapper connection-completeness and fan-in, mutation-checked), 7 heartbeat recovery/flap tests incl. coordinator variants, and the first real input-simulation test (`QTest.mouseClick` nav click through real `MainWindow.qml` wiring — fails on reintroduced SelectBar bug). Suite at 369 passed |
| TD-034 | colcon build broken; packaging gate normalized-red | 2026-07-27 | Removed both dead install stanzas from `CMakeLists.txt` (app runs from source tree; zero install-space consumers, verified workspace-wide), deleted stale `setup.cfg`, added `dev` CI trigger, decoupled `build` job from red `lint`; colcon build green locally (2 packages finished) |
| TD-031 | Narrowed QML structural rebuild | 2026-04-24 | Completed with an explicit page registry, dedicated `qml/features/systemcontrol/` and `qml/features/video/` roots, and canonical `qml/theme/CommonStyle.qml` ownership. Focused smoke coverage now includes the shell, multiscreen window, navigation contract, systemcontrol feature root, and video feature root. Compatibility wrappers remain intentionally at the old overlay/core paths to keep imports stable while low-priority cleanup stays backlog-only |
| TD-001 | QML structural flatten + `required` properties not enforced | 2026-04-22 | Stage 1 complete: verified-dead QML deleted, false shared folders flattened, constructor-driven surfaces hardened with `required` / `readonly`, startup smoke now covers the `MultiScreenListUI` path through `tests/test_startup_smoke_shell.py`, and warn-only `qmllint` CI was added. Remaining no-`required` files were classified as global-context, imperative, style-singleton, or otherwise non-constructor-driven surfaces rather than unfinished Stage 1 work |
| — | `qmlRegisterSingletonInstance` crashes | 2026-04-17 | Replaced with `setContextProperty` — see KNOWLEDGE.md |
| — | `findChild()` Python-side QML lookup | 2026-04-20 | Replaced with injected `close_popup_fn` callable |
| — | 4 winch move-command guards disabled | 2026-04-20 | Re-enabled with `get_logger().warning()` + early return |
| TD-018 | Controller heartbeat always publishes `IDLE` | 2026-04-21 | Fixed in `BF-6` — heartbeat state now lives in `StateStore` and `PaintRosNode.publish_heartbeat()` publishes the live value |
| TD-019 | ROS node destroyed before controller cleanup | 2026-04-21 | Fixed in `BF-7` — final node cleanup/destroy now runs in the runtime shutdown path after controller/service cleanup |
| TD-020 | Emergency halt path incomplete and fragmented | 2026-04-21 | Fixed in `BF-9` + `4.0` — `SafetyCoordinator` halts winch, wheel, spray trigger, and ESP32 valve; offscreen smoke test added |
| TD-021 | QML teardown left null-binding warnings during exit | 2026-04-21 | Fixed in shutdown hardening — the runtime shutdown path now tears down the QML runtime before backend cleanup and `tests/test_startup_smoke_shell.py` asserts no new teardown-time null-binding warnings |
| TD-022 | ESP32 UDP thread did not participate in normal shutdown | 2026-04-21 | Fixed in shutdown hardening — `ESP32ValveController.cleanup()` now stops timers and joins the UDP receive thread; covered in `tests/test_esp32_valve.py` |
| TD-023 | JSON config writes were non-atomic | 2026-04-21 | `settings.json` and `ssh_config.json` now write via temp file + flush/fsync + `os.replace`, keeping the last good file intact on write failure |
| TD-024 | Teensy status dict crossed ROS and Qt threads unsafely | 2026-04-21 | `TeensyController` now guards `_status` consistently and emits defensive copies instead of the live shared dict |
| TD-025 | SSH worker callbacks touched Qt/UI from background threads | 2026-04-21 | Availability and command results now marshal back through Qt signals on the controller thread before touching state or popups |
| TD-026 | First navigation froze while lazily-loaded QML pages initialized heavy modules | 2026-04-21 | Fixed by removing unused `QtMultimedia`/`QtCharts` imports from page QML, pre-warming the remaining heavy modules in `MainWindow.qml`, and adding `tests/test_qml_imports.py` to block regressions |
| TD-027 | ESP32 reconnect discovery blocked the Qt main thread | 2026-04-21 | `arp -a` discovery now runs off-thread and normal reconnect no longer waits on the UDP receive thread from the UI thread |
| TD-028 | Controller heartbeat publishing depended on the Qt main thread | 2026-04-21 | `PaintRosNode` now owns the 500ms heartbeat timer on the ROS side, so a transient GUI-thread stall no longer self-produces a heartbeat-loss event |
| TD-029 | SSH availability callback could emit into a deleted QObject during shutdown | 2026-04-22 | `UISSHController` now swallows late availability/command callback `RuntimeError`s during teardown and `tests/test_ssh.py` covers the late-result path |
| — | Fullscreen overlay warning regressions escaped the smoke harness | 2026-04-27 | The touched fullscreen overlays now use bindable runtime data, startup-safe reads, and anchor-safe containers, and the fullscreen smoke harness matches the real runtime shape closely enough to fail on the tracked warning signatures |
| — | SSH teardown crash during full-suite shutdown | 2026-04-27 | `UISSHController` now owns a dedicated `QThreadPool`, uses weakref-based callbacks, drains timers/workers during idempotent cleanup, and `tests/test_ssh.py` plus the full suite are green again at `4 passed` and `252 passed` |
| TD-030 | Runtime/workflow/service validation gap | 2026-04-22 | Closed by direct tests for WorkFlowRunner, WorkFlowExecutor, ActionScheduler, ActionRegistry/workflow handlers, HardwareControllers adapters, `create_controllers()`, bounded `AppRuntime` seams, `ScreenManager`, and `BaseTopViewTransformer`; focused validation is green at `22 passed` |
| TD-014 | `main()` god-function | 2026-04-21 | Bootstrap now lives in `core/app_runtime.py`; `application.py` is a thin entry-point wrapper, `RosThread` moved to `core/ros_node.py`, and the dead `robot_config.yaml` loader path was replaced by `RuntimeDefaults` |
| TD-007 | SteamDeck HID input parsing untested | 2026-04-21 | Fixed in task `3.5` — raw HID decoding now lives in `utils/steam_deck_hid.py` with direct parser tests, and cleanup coverage remains green without destructor-side crashes |
| — | Dual-inheritance `RobotController` god class | pre-2026-04-17 | Split into `PaintRosNode`, `StateStore`, `QtBridge`, `ControllerFactory` |
| — | Hardcoded ESP32 MAC/IP in source | pre-2026-04-17 | Externalised to `python/config/esp32_valve.json` |
| TD-004 | `workflow_legacy.py` not removed | 2026-04-20 | Deleted in Phase 1B along with full legacy workflow system (11 files) |
| TD-003 | `__init__.py` re-exports pollute import graph | 2026-04-20 | Fixed in task `3.0` — subpackage `__init__.py` files are now lightweight and no longer re-export heavy Qt/ROS modules |
| TD-005 | WheelController has no unit tests | 2026-04-20 | Fixed in task `3.6` — `tests/test_wheel.py` now covers unified speed publishing, status updates, error transitions, and timeout availability |
| TD-006 | ESP32ValveController and TeensyController have no unit tests | 2026-04-20 | Fixed in task `3.7` — `tests/test_esp32_valve.py` and `tests/test_teensy.py` now cover protocol conversion, keepalive/status behavior, user-field preservation, and thrust/force publishing |
| TD-012 | Workflow executor thread safety | 2026-04-20 | Fixed in Phase 0A — `threading.Lock` + `threading.Event` property wrappers |
| TD-013 | Workflow DI bypass (hardware controllers silently `None`) | 2026-04-20 | Fixed in Phase 0B — `HardwareControllers.from_controllers()` explicit DI |
| TD-015 | `BirdViewService` dead code | 2026-04-20 | Deleted in Phase 1C — `bird_view_service.py` + `PointEditorOverlay.qml` removed |
| TD-008 | `toggle_multiscreen_window()` still uses `engine.rootObjects()[0]` | 2026-04-20 | Dropped from the active debt list after review — single stable call site, not worth replacing right now |
| TD-017 | `show_popup_fn` constructor coupling | 2026-04-20 | Dropped from the active debt list after review — callable injection is acceptable DI, not harmful debt |
