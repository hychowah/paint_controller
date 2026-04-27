# Tech Debt Tracker

Living document. Update when debt is discovered, addressed, or re-prioritised.

**Priority**: `high` = blocking quality or correctness | `medium` = degrades maintainability | `low` = cosmetic / nice-to-have

---

## Active Debt

### TD-032 — Python Qt architecture boundary work in progress
**Area**: QML UI
**Priority**: medium
**Effort**: high
**Why it matters**: The next major debt is no longer a generic "deep QML structural rebuild". The first-principles problem is that the permanent QML runtime surface is still too broad, which keeps the app harder to maintain, scale, and understand than a more professional Qt program should be. The core purpose of the refactor is still to reduce global coupling, clarify ownership, shrink the app-scope QML contract, and make operator-visible behavior easier for humans to trace. Stage 1, Stage 2, Stage 3A, Stage 3B1, Stage 4, Stage 4.5, Workstream A, Workstream B, Workstream C, and Workstream D are complete for the targeted families. The unfinished tail now needs to retire the highest-fanout remaining ambient read families in sequence rather than treating all remaining work as one blob.
**What to do**: Follow `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` as the active roadmap and `docs/plan/00_ARCHITECTURE_PROGRESS.md` for current family status. Treat completed stages through Stage 4.5 plus completed Workstreams A through D as historical record. Under Workstream E, the shared video/runtime family is already retired for the touched subtree; the current active family is device/status in bounded sub-slices, the next family after that is settings cleanup only where it still materially reduces ambient reads, and narrower automation-contract work stays downstream of those contract-reduction checkpoints.
**Files**: `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `python/paint_controller/handlers/manual_commands.py`, `python/paint_controller/qml/core/`, `python/paint_controller/qml/navigation/`, `python/paint_controller/qml/overlays/systemcontrol/`, `python/paint_controller/qml/overlays/video/`, `python/paint_controller/qml/pages/settings/`, `python/paint_controller/ui/overlay.py`, `python/paint_controller/handlers/input.py`, `python/paint_controller/handlers/control_processor.py`, `python/paint_controller/core/app_runtime.py`

---

### TD-002 — Design system incomplete (systemcontrol/video remainder, pages)
**Area**: QML UI
**Priority**: low
**Effort**: medium
**Why it matters**: Hardcoded colours, spacing, and font sizes in the remaining untokenized files will diverge from the rest of the UI and make theme-wide changes expensive later, but this is no longer the architecture-driving problem.
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

## Resolved Debt

| ID | Title | Resolved | Notes |
|---|---|---|---|
| TD-031 | Narrowed QML structural rebuild | 2026-04-24 | Completed with an explicit page registry, dedicated `qml/features/systemcontrol/` and `qml/features/video/` roots, and canonical `qml/theme/CommonStyle.qml` ownership. Focused smoke coverage now includes the shell, multiscreen window, navigation contract, systemcontrol feature root, and video feature root. Compatibility wrappers remain intentionally at the old overlay/core paths to keep imports stable while low-priority cleanup stays backlog-only |
| TD-001 | QML structural flatten + `required` properties not enforced | 2026-04-22 | Stage 1 complete: verified-dead QML deleted, false shared folders flattened, constructor-driven surfaces hardened with `required` / `readonly`, `tests/test_startup_smoke.py` now covers the `MultiScreenListUI` path, and warn-only `qmllint` CI was added. Remaining no-`required` files were classified as global-context, imperative, style-singleton, or otherwise non-constructor-driven surfaces rather than unfinished Stage 1 work |
| — | `qmlRegisterSingletonInstance` crashes | 2026-04-17 | Replaced with `setContextProperty` — see KNOWLEDGE.md |
| — | `findChild()` Python-side QML lookup | 2026-04-20 | Replaced with injected `close_popup_fn` callable |
| — | 4 winch move-command guards disabled | 2026-04-20 | Re-enabled with `get_logger().warning()` + early return |
| TD-018 | Controller heartbeat always publishes `IDLE` | 2026-04-21 | Fixed in `BF-6` — heartbeat state now lives in `StateStore` and `PaintRosNode.publish_heartbeat()` publishes the live value |
| TD-019 | ROS node destroyed before controller cleanup | 2026-04-21 | Fixed in `BF-7` — final node cleanup/destroy now runs in the runtime shutdown path after controller/service cleanup |
| TD-020 | Emergency halt path incomplete and fragmented | 2026-04-21 | Fixed in `BF-9` + `4.0` — `SafetyCoordinator` halts winch, wheel, spray trigger, and ESP32 valve; offscreen smoke test added |
| TD-021 | QML teardown left null-binding warnings during exit | 2026-04-21 | Fixed in shutdown hardening — the runtime shutdown path now tears down the QML runtime before backend cleanup and `tests/test_startup_smoke.py` asserts no new teardown-time null-binding warnings |
| TD-022 | ESP32 UDP thread did not participate in normal shutdown | 2026-04-21 | Fixed in shutdown hardening — `ESP32ValveController.cleanup()` now stops timers and joins the UDP receive thread; covered in `tests/test_esp32_valve.py` |
| TD-023 | JSON config writes were non-atomic | 2026-04-21 | `settings.json` and `ssh_config.json` now write via temp file + flush/fsync + `os.replace`, keeping the last good file intact on write failure |
| TD-024 | Teensy status dict crossed ROS and Qt threads unsafely | 2026-04-21 | `TeensyController` now guards `_status` consistently and emits defensive copies instead of the live shared dict |
| TD-025 | SSH worker callbacks touched Qt/UI from background threads | 2026-04-21 | Availability and command results now marshal back through Qt signals on the controller thread before touching state or popups |
| TD-026 | First navigation froze while lazily-loaded QML pages initialized heavy modules | 2026-04-21 | Fixed by removing unused `QtMultimedia`/`QtCharts` imports from page QML, pre-warming the remaining heavy modules in `MainWindow.qml`, and adding `tests/test_qml_imports.py` to block regressions |
| TD-027 | ESP32 reconnect discovery blocked the Qt main thread | 2026-04-21 | `arp -a` discovery now runs off-thread and normal reconnect no longer waits on the UDP receive thread from the UI thread |
| TD-028 | Controller heartbeat publishing depended on the Qt main thread | 2026-04-21 | `PaintRosNode` now owns the 500ms heartbeat timer on the ROS side, so a transient GUI-thread stall no longer self-produces a heartbeat-loss event |
| TD-029 | SSH availability callback could emit into a deleted QObject during shutdown | 2026-04-22 | `UISSHController` now swallows late availability/command callback `RuntimeError`s during teardown and `tests/test_ssh.py` covers the late-result path |
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
