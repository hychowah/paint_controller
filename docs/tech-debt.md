# Tech Debt Tracker

Living document. Update when debt is discovered, addressed, or re-prioritised.

**Priority**: `high` = blocking quality or correctness | `medium` = degrades maintainability | `low` = cosmetic / nice-to-have

---

## Active Debt

### TD-033 — Zero behavioral UI / NOTIFY-contract test coverage
**Area**: Tests
**Priority**: high
**Effort**: medium
**Why it matters**: ~18k QML lines have load-only smoke coverage ("component loads, no fatal warnings"); there is no input simulation anywhere in the suite. The Phase 7 shell-routing change shipped broken primary navigation — `SelectBar { shellRouter: mainWindow.shellRouter }` does not resolve context properties through a qualified id lookup, and `SelectBar.qml`'s `if (shellRouter)` guard made nav clicks silently no-op — and no gate caught it (fixed by the uncommitted `shellRouterModel`/`shellStateModel` alias change in `MainWindow.qml`). Separately, none of the new `*Status`/`*Actions` models have NOTIFY-contract tests (`QSignalSpy` is unused), and heartbeat recovery/flap is untested — only the loss path is.
**What to do**: Extend the existing Python-driven `QQmlComponent` harness (do NOT adopt qmltestrunner) with: (1) a few interaction tests through real wiring — navigation round-trip, e-stop button → halt; (2) NOTIFY-contract tests for each QML-exposed model (mutate → exactly one emission with correct payload); (3) heartbeat recovery/flap cases in `test_heartbeat.py` / `test_safety_integration.py`.
**Files**: `tests/startup_smoke_support.py`, `tests/test_startup_smoke_shell.py`, `tests/test_heartbeat.py`, `tests/test_safety_integration.py`, `python/paint_controller/qml/navigation/SelectBar.qml`

---

### TD-034 — colcon build broken; packaging gate normalized-red
**Area**: Build / Packaging
**Priority**: high
**Effort**: low
**Why it matters**: `CMakeLists.txt` installs a `resource/` directory that does not exist at repo root, so `colcon build` fails pre-existingly while `AGENTS.md` lists it as validation gate #3 — a permanently red gate trains everyone to route around gates (this is how TD-033's navigation regression shipped "validated"). `setup.py` and the ament_cmake `CMakeLists.txt` also coexist as two half-configured build systems.
**What to do**: Remove or repair the `resource/` install stanza, resolve the `setup.py` vs `CMakeLists.txt` ambiguity, and get `colcon build` green in CI. (CMakeLists.txt / package.xml changes are stop-and-ask per AGENTS.md — confirm with the user before editing.)
**Files**: `CMakeLists.txt`, `setup.py`, `package.xml`, `.github/workflows/ci.yml`

---

### TD-035 — View-authoritative toggle commands; optimistic device state never reconciled
**Area**: State management
**Priority**: high
**Effort**: medium
**Why it matters**: QML passes its binding snapshot as the toggle authority (`teensyActions.toggleStability(deviceControlTab.teensyStatus.stabilityEnabled)` at `DeviceControlTab.qml:426`, plus call sites in `PageWheel.qml` and `PageStatus.qml`); if the binding is one emission behind, the operator toggles a safety-relevant control the wrong way. The backend already owns the truth (`teensy.py` `_stability_enabled`). Additionally `_USER_CONTROLLED_FIELDS` (`teensy.py:89`) are local intent published one-way and never read back — after a firmware restart/reconnect the HMI can display "enabled" while the device is actually disabled.
**What to do**: Change `*Actions.toggleX(current)` to `toggleX()` reading controller-owned state (or use checkable controls calling `setX(bool)`); reconcile user-controlled fields against device state on reconnect.
**Files**: `python/paint_controller/models/teensy_actions.py`, `python/paint_controller/controllers/teensy.py`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/pages/wheel/PageWheel.qml`, `python/paint_controller/qml/pages/status/PageStatus.qml`

---

### TD-036 — Settings persisted inside source tree; QML settings writes ungated
**Area**: Settings / Deployment
**Priority**: medium
**Effort**: low
**Why it matters**: `settings.py:316-318` resolves `settings.json` inside the repo (docstrings hardcode `~/ros2_ws/src/...`) — breaks under colcon install or read-only deployment. The QML settings UI mutates persisted machine limits via raw `settingsManager.getInt/applyFloat/setFloat` (~18 call sites) with no AdminActionGate legality check — the last unguarded machine-affecting write path. The generated per-setting Qt Properties are also unused by QML (hand-rolled `Connections` refresh instead) — two parallel APIs with the weaker one in use.
**What to do**: Move settings to an XDG/env-overridable path; route QML settings mutations through one gated slot; pick one settings API (bind the generated Properties or drop them).
**Files**: `python/paint_controller/core/settings.py`, `python/paint_controller/qml/pages/settings/components/ManagedSettingSpinBox.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`

---

### TD-032 — QML boundary retirement program: close out honestly, then stop
**Area**: QML UI
**Priority**: medium
**Effort**: low
**Why it matters**: The 2026-07-27 multi-perspective architecture review found the program's headline metric unmet (target ~12–15 root-context properties; actual 28 in `_EXPECTED_CONTEXT_PROPERTY_NAMES`) and its explicit elimination targets still live: `deviceActionHandler` (call sites in `DeviceControlTab.qml`, `PageStatus.qml`, `PageWinch.qml`, `TeensyStatus.qml`), `stateStore` (1 QML use), `backend` (2 QML uses). The substantive win (no raw controllers in QML; gated action models) is real and done; the remaining tail is small and the program is past diminishing returns (Phases 7–8 produced the TD-033 navigation regression and net line growth).
**What to do**: One final close-out slice: retire `deviceActionHandler`, `stateStore`, and `backend` per the board's own "remove when last consumer is gone" rule — or formally amend the 12–15 target in the plan docs. Correct the stale frozen/quarantine entries (TD-041), then declare the program closed and redirect effort to TD-033…TD-038. Do not open new boundary phases.
**Files**: `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `python/paint_controller/core/qml_context_composer.py`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/pages/status/PageStatus.qml`, `python/paint_controller/qml/pages/winch/PageWinch.qml`, `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`

---

### TD-037 — Status wrapper layer: blanket notify, stringly reads, duplicated telemetry
**Area**: QML↔Python boundary
**Priority**: medium
**Effort**: high
**Why it matters**: `qml_context_composer.py` (1191 lines, now the largest Python file) re-implements the per-property NOTIFY the controllers already have — worse: one blanket `changed` signal fans ~50 properties per wrapper (every teensy tick re-evaluates every binding), `_connect_if_signal` silently skips missing signals (a controller-side rename becomes invisible drift), `_read_object_value`'s duck-typed fallbacks exist partly to tolerate test fakes in production code, and physical values are duplicated under multiple names (battery voltage ×3 across `_VideoRuntimeTopBar`/`_TeensyStatus`/`_WinchStatus`; SSH reachability ×2). This violates the retirement program's own "no controller-shaped mirrors / no shallow wrappers" principles.
**What to do**: Long-term: move per-property NOTIFY onto controller-owned read-only status QObjects and delete most of the composer wrapper classes; consolidate one canonical owner per physical value; keep the `*Actions`/gating models (the program's real win). Also found by TD-033 Slice 1's contract tests (2026-07-27): `OverlayHostPolicy`'s `screen_count_changed → refresh_layout` connection is a dead input (`refresh_layout` never reads screen count), and `ShellRouter.route_registry_changed` has no emission path (registry built once in `__init__`, never mutated — the property could be `constant`). Both are pinned as intentional in `tests/test_notify_contracts.py` until this item is worked.
**Files**: `python/paint_controller/core/qml_context_composer.py`, `python/paint_controller/controllers/winch.py`, `python/paint_controller/controllers/teensy.py`

---

### TD-038 — File-scale QML decomposition: PageWinch, EditWorkFlowTab, TeensyStatus
**Area**: QML UI
**Priority**: medium
**Effort**: high
**Why it matters**: `PageWinch.qml` is 1606 lines with zero `CommonStyle` uses, 70 hardcoded colors, two near-identical ~120-line control blocks, and two hand-rolled toggle switches despite an existing `TouchSwitch` component — one extracted control card deletes several hundred lines. `EditWorkFlowTab.qml` (1027 lines) builds and JSON-serializes the workflow document in JavaScript (`saveWorkflow()`) — business logic in the view layer. These files are the actual maintenance risk the boundary program never touched. Absorbs the worst of TD-002.
**What to do**: Extract a reusable winch control card; move workflow JSON assembly into the Python editor model; tokenize with `CommonStyle` as files are touched.
**Files**: `python/paint_controller/qml/pages/winch/PageWinch.qml`, `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`

---

### TD-039 — Concurrency loose ends: BaseTopView race, unconsumed ROS error path, in-lock emit
**Area**: Concurrency
**Priority**: medium
**Effort**: low
**Why it matters**: (1) `base_top_view_service.py` property setters / `_reinitialize_maps()` mutate worker-thread remap tables from the main thread while the worker reads them in `cv2.remap` — torn frames exactly while the operator drags calibration sliders (the one true remaining data race). (2) `RosThread.error_occurred` has zero consumers and `_last_spin_time`/`_spin_timeout` are written but never read — ROS/network loss is invisible to the operator. (3) `steam_deck.py:544` emits `button_held` while holding a non-recursive `QMutex`, violating the repo's own emit-outside-lock rule (deadlock landmine; no current connections). (4) `CameraStream.cleanup()` writes `image_provider.image = None` without the provider mutex (`video_stream.py`), so `requestImage` can hit `None.copy()` on the render thread if the configurable-stream path is enabled.
**What to do**: Marshal calibration mutations into the worker thread (or guard `map1`/`map2`); wire `error_occurred` to a user-visible status or delete the dead signal/bookkeeping; move the `button_held` emit outside the lock; hold the image mutex or keep a placeholder `QImage` in cleanup.
**Files**: `python/paint_controller/services/base_top_view_service.py`, `python/paint_controller/core/ros_node.py`, `python/paint_controller/core/signal_wiring.py`, `python/paint_controller/handlers/steam_deck.py`, `python/paint_controller/services/video_stream.py`

---

### TD-040 — pyright allowlist excludes the riskiest modules
**Area**: Tooling / CI
**Priority**: medium
**Effort**: medium
**Why it matters**: `pyrightconfig.json` `include` cherry-picks scope; it excludes `services/` (`video_stream.py` 772 lines, `base_top_view_service.py` 783, workflow ~1270 — the threading-heaviest code), `core/app_runtime.py`, `ui/`, `widgets/`, `utils/`, and runs `basic` mode. "Pyright green" currently proves little about the whole.
**What to do**: Widen `include` incrementally (services first), fix the fallout, keep the gate green.
**Files**: `pyrightconfig.json`

---

### TD-044 — Ruff lint debt on `dev` (1965 check errors, 111 format failures)
**Area**: Tooling / CI
**Priority**: medium
**Effort**: medium
**Why it matters**: Surfaced 2026-07-27 by TD-034: the CI `lint` job (ruff check + ruff format --check on `python/` and `tests/`) is red on `dev` — 1965 check errors (mostly W293 blank-line-with-whitespace, UP006, W292, I001, F401) and 111 files failing the format check. It was invisible because CI never ran on `dev`. Until fixed, the lint job is normalized-red and `typecheck`/`test` stay blocked behind `needs: lint`.
**What to do**: Bulk-fix mechanically (`ruff check --fix` + `ruff format`) in one dedicated commit with no behavior changes, then keep the job green. Coordinate with open branches to avoid merge pain.
**Files**: `pyproject.toml` (ruff config), `python/`, `tests/`, `.github/workflows/ci.yml`

---

### TD-045 — CI test/typecheck jobs missing system dependencies
**Area**: Tooling / CI
**Priority**: medium
**Effort**: low
**Why it matters**: Surfaced 2026-07-27 by TD-034: the CI `test` and `typecheck` jobs pip-install `python/paint_controller/requirements.txt`, which includes `PyGObject` — source-only (no binary wheels), needing girepository/cairo dev headers the runner lacks; PySide6 also needs Qt runtime libs (`libegl1`, `libxkbcommon`, …). The jobs have zero apt steps, so they will fail on a clean runner now that CI triggers on `dev`.
**What to do**: Add an apt step (girepository/cairo dev headers, Qt runtime libs) to both jobs, or trim `requirements.txt` for CI; verify green on a real runner.
**Files**: `.github/workflows/ci.yml`, `python/paint_controller/requirements.txt`

---

### TD-002 — Design system incomplete (systemcontrol/video remainder, pages)
**Area**: QML UI
**Priority**: low
**Effort**: medium
**Why it matters**: Hardcoded colours, spacing, and font sizes in the remaining untokenized files will diverge from the rest of the UI and make theme-wide changes expensive later, but this is no longer the architecture-driving problem. The worst single offender (`PageWinch.qml`: 0 `CommonStyle` uses, 70 hardcoded colors) is now tracked with the decomposition work in TD-038.
**What to do**: Resume the remaining `CommonStyle` rollout only after the boundary-retirement roadmap is stable, unless the user explicitly reprioritizes it. The remaining debt is limited design-token cleanup across the residual systemcontrol, video, and page surfaces, not unresolved structural duplication.
**Files**: `python/paint_controller/qml/overlays/systemcontrol/`, `python/paint_controller/qml/overlays/video/`, `python/paint_controller/qml/pages/home/`, `python/paint_controller/qml/pages/wheel/`, `python/paint_controller/qml/pages/winch/`, `python/paint_controller/qml/pages/tuning/`, `python/paint_controller/qml/pages/settings/`, `python/paint_controller/qml/pages/status/`

---

### TD-016 — `VideoOverlayStyle.qml` compatibility-wrapper cleanup
**Area**: QML UI  
**Priority**: low  
**Effort**: low  
**Why it matters**: `VideoOverlayStyle.qml` no longer owns its own tokens, but it still preserves a parallel style API for older video overlay components. That wrapper layer keeps imports stable, but it also delays a clean direct dependency on `CommonStyle`.  
**What to do**: Retire the wrapper-only API once the remaining video overlay callers can read `CommonStyle` directly, or keep the file as a thin documented compatibility shim if import churn is intentionally deferred.  
**Files**: `python/paint_controller/qml/overlays/video/components/VideoOverlayStyle.qml`

---

### TD-041 — Governance/doc hygiene: stale plan entries, KNOWLEDGE.md mis-citation
**Area**: Docs
**Priority**: low
**Effort**: low
**Why it matters**: `00_ARCHITECTURE_PROGRESS.md`'s frozen list declares route identity owned in `MainWindow.qml` in the same file that declares Phase 7 (which moved it to `ShellRouter`) complete; its quarantine list still names `PageWheel.qml`'s `baseStreamHandler` seam, which no longer exists. `KNOWLEDGE.md`'s singleton entry cites PYSIDE-2160/2310 as a "known bug family" — both are unrelated issues fixed in Qt 6.5.x and the repo runs PySide6 6.10.1; the conclusion (avoid `qmlRegisterSingletonInstance` with implicit directory imports) is defensible, but the cited reasoning blocks legitimate typed-registration options (`qmlRegisterUncreatableType`, `@QmlNamedElement`). `AGENTS.md` also references a `launch/` directory that does not exist.
**What to do**: Correct the KNOWLEDGE.md entry (user confirmation required per KNOWLEDGE.md rules), refresh or retire the stale frozen/quarantine entries, fix the `launch/` reference.
**Files**: `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `KNOWLEDGE.md`, `AGENTS.md`

---

### TD-042 — Over-fitted test mirror and structural-selfie assertions
**Area**: Tests
**Priority**: low
**Effort**: medium
**Why it matters**: `startup_smoke_support.py` (1095 lines, 27 hand-maintained fake context classes) re-implements the models' QML APIs property-by-property; `FakeShellRouter` hand-copies the route registry, so a production route reorder keeps the suite green while navigation breaks; `controller_factory_runtime_support.py` (447 lines, ~107 recorder classes) largely asserts that wiring wires what it wires; per-test `fatal_warning_fragments` tuples are copy-pasted Qt warning strings (version-brittle). Correctness currently depends on a human remembering to update the mirror each phase.
**What to do**: Derive static fake contracts from production (e.g. build `FakeShellRouter` from the real route registry), collapse warning tuples into one `assert_no_fatal_qml_warnings()` helper, keep the shutdown-order and name-parity assertions, delete the structural selfies.
**Files**: `tests/startup_smoke_support.py`, `tests/controller_factory_runtime_support.py`, `tests/test_startup_smoke_shell.py`

---

### TD-043 — Dead/duplicated state and metadata layers
**Area**: State management
**Priority**: low
**Effort**: medium
**Why it matters**: `StateStore` is ~60% dead state (`left/right_joystick_control`, `*_control_mode/value` have no writers/readers; QML reads only `display_message`) while its "single source of truth" branding invites writes to the wrong place. `CapabilityCatalog` (559 lines) + metadata registry has 3 QML call sites in one popup. `SignalWiring.wire()` writes `runtime._heartbeat_status_error`, which nothing reads; uncalled "master-plan signature" convenience functions exist in `signal_wiring.py` / `qml_context_composer.py`.
**What to do**: Delete the dead StateStore surface or make it Python-internal; reduce CapabilityCatalog to what the popup consumes (or fold legality into the gate); delete dead writes and uncalled functions.
**Files**: `python/paint_controller/core/state_store.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/core/signal_wiring.py`, `python/paint_controller/core/qml_context_composer.py`

---

## Resolved Debt

| ID | Title | Resolved | Notes |
|---|---|---|---|
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
