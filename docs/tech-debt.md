# Tech Debt Tracker

Living document. Update when debt is discovered, addressed, or re-prioritised.

**Priority**:
- `high` = blocking quality/correctness, or breaks a stated architecture invariant (e.g. single gated write path)
- `medium` = degrades maintainability or long-term structure
- `low` = cosmetic / nice-to-have / pure UI chrome

**Architecture leverage** (optional tag on items): how much a fix improves FE↔BE program structure when doing architecture work, independent of ship-blocking urgency.

Last multi-perspective re-validation: **2026-07-28** (deep software-only pass). **2026-07-29**: TD-055 Wave 1+2 landed; **TD-054** and **TD-056** concurrency track closed (command bus + telemetry marshal for wheel/winch).

**Research non-goals (do not invent debt for):** mega-`Backend` object; reopening TD-032 name-retirement mega-program; full URI QML module rewrite as a program; universal visual skin unification; HMI safety/legality ship defaults; `qmlRegisterSingletonInstance`. Concurrency non-goals: MultiThreadedExecutor-first rewrite; UI/control process split; moving the teleop loop onto RosThread; forcing ESP32 UDP through the ROS command bus; reintroducing raw multi-thread command `publish` or unlocked ROS-thread QObject field mutation on property-bag devices.

---

## Program-track recommended order

When the goal is **software architecture toward a professional Qt program** (not UI chrome, not HMI product semantics), prefer this order over raw ID order:

| Rank | ID | Why |
|---|---|---|
| — | **TD-056** | **Resolved 2026-07-29** — `RosTelemetryBridge` + wheel/winch main-thread apply (see Resolved). Residual: heartbeat restore fields; Teensy stays lock+snapshot |
| — | **TD-054** | **Resolved 2026-07-29** — RosCommandBus + continuous-motion latch (see Resolved table) |
| — | **TD-055** | Landed Wave 1+2; residual only (see Active Debt). Not the primary next program track. |
| — | **TD-052 / TD-053** | When touching tuning/commands or dual-surface overlays |
| — | **TD-002 / TD-016** | Opportunistic chrome only; out of pure program track |
| — | **TD-040 residual** | Optional: `video_stream` / `base_top_view_service` pyright include (deferred 2026-07-29) |
| — | **TD-041 / TD-042 / TD-043 / TD-051** | Resolved 2026-07-29 (hygiene band) |
| — | **TD-049** | Resolved 2026-07-29 (shared ports Teensy teleop+halt+workflow body; residual *Actions Any — continued under TD-055) |
| — | **TD-050** | Resolved 2026-07-29 (public setters + require_ui_ports finalize; set-once not enforced) |
| — | **TD-048** | Resolved 2026-07-29 (page/feature inject for actions/legality/settings/chrome) |
| — | **TD-044 / TD-045 / TD-040** | Resolved 2026-07-29 (CI control plane) |
| — | **TD-047** | Resolved 2026-07-28 (façade demirror + wiring/composer ports) |
| — | **TD-046** | Resolved 2026-07-28 (docs + winch/wheel teleop extract). **Post-halt inhibit residual moved into TD-054** (coupled acceptance). EF stick mass residual remains unscheduled. |
| — | **TD-037** | Resolved 2026-07-28 (residual: videoRuntime multi-home only) |
| — | **TD-038 / TD-032 / TD-036 / TD-039** | Resolved 2026-07-28 |

---

## Active Debt

### TD-055 — Layer responsibility depth (Problem 2)
**Area**: Backend / package boundaries / module depth  
**Priority**: medium (maintainability / long-term structure; residual only — integrity track is TD-054/056)  
**Effort**: high (phased; not one PR)  
**Architecture leverage**: high  
**Status**: **Wave 1+2 landed** 2026-07-29 on `td-055/layer-responsibility-depth`. Execution plan deleted (git history is archive). Optional 4′/5′ rehome deferred.  
**Why it matters**: Layer/responsibility depth (Problem 2).  
**What landed**: dual HAL collapse; ContinuousTeleopEngine; Actions invoke family; wheel port honesty; factory subsystem builders; workflow port dialect; Teensy format off-device.  
**Residual**: SignalWiring still takes whole bundle; CP test-compat proxies over engine remain; package rehome not done.  
**Acceptance**: Structural coverage in `tests/test_layer_responsibility_depth.py`; full suite green at land.  
**Files**: `ports/*`, `handlers/continuous_teleop_engine.py`, `handlers/control_processor.py`, `models/*_actions.py`, `core/controller_factory.py`, `services/workflow/*`

---

### TD-052 — Command/tuning parameter schemas still owned in QML
**Area**: QML ↔ Python boundary
**Priority**: low–medium
**Effort**: medium
**Architecture leverage**: medium
**Why it matters**: Post-TD-038, workflow **document** load/save is Python-owned, but `PageTuning.qml` still embeds large `parameterSetDefinitions` (names, units, getters, send functions → `tuningActions.*`) and `CommandTab.qml` embeds `commandDefinitions` schemas. That is untyped view-owned schema/policy: adding a PID set or command requires editing QML, not config/Python.
**What to do**: Move definition tables to Python models (list/map APIs); QML renders generic forms and calls one send API — same pattern as workflow document ownership. Do not reopen EditWorkFlowTab LOC vanity; residual type→form routing there is acceptable.
**Acceptance**: No command/PID parameter schema literals in QML (layout metadata only); adding a set is a Python/config change; focused smokes green.
**Files**: `qml/pages/tuning/PageTuning.qml`, `qml/overlays/systemcontrol/CommandTab.qml`, corresponding Python action/handler modules

---

### TD-053 — Dual-surface overlay composition duplication
**Area**: QML shell composition
**Priority**: low
**Effort**: medium
**Architecture leverage**: medium *for shell contracts*
**Why it matters**: `MainWindow.qml` and `MultiScreenListUI.qml` each instantiate `SystemControlWorkspace`, `JoystickOverlay`, `VideoFullscreenWorkspace`, and `EmergencyOverlay` with parallel prop lists. `OverlayHostPolicy` / `ShellState` correctly own visibility and z; composition wiring is dual-maintained. Adding a required property (pairs with TD-048) is a two-file change with silent drift risk. Shell contracts are otherwise frozen — do not schedule as active program work unless a multi-surface change forces dual edits.
**What to do**: Extract `ShellOverlayStack.qml` (or similar) taking surface/policy flags + models; both hosts become thin. Visibility remains driven by `overlayHost` flags.
**Acceptance**: Overlay types appear once in composition QML; shell + multiscreen smokes green; status/command inject props not copy-pasted across hosts.
**Files**: `qml/core/MainWindow.qml`, `qml/overlays/MultiScreenListUI.qml`, optional new stack QML under `qml/core/` or `qml/overlays/`

---

### TD-002 — Design-token adoption incomplete on page/admin islands
**Area**: QML UI
**Priority**: low
**Effort**: medium
**Architecture leverage**: low (UI chrome)
**Why it matters**: Shell, navigation, features, and global `components/` are largely token-clean via `CommonStyle`. Page families (home/wheel/winch/settings/tuning) and systemcontrol tabs still use **local Material/dark hex islands** (including winch components redeclaring local palettes). Dual skins may be product-intentional; the software cost is theme-wide change archaeology, not FE↔BE structure. Not program-track.
**What to do**: Opportunistic only when a page family is already open — bind `CommonStyle` or one page-level palette object; stop redeclaring Material `primaryColor`/`dangerColor` per winch component. Do not schedule a global “one skin” program.
**Files**: `qml/pages/home|wheel|winch|settings|status|tuning/`, `qml/overlays/systemcontrol/` tabs, `qml/theme/CommonStyle.qml`

---

### TD-016 — Dead `VideoOverlayStyle.qml` façade
**Area**: QML UI
**Priority**: low
**Effort**: very low
**Architecture leverage**: low
**Why it matters**: Research 2026-07-28: `VideoOverlayStyle.qml` only aliases `CommonStyle` and has **zero runtime callers** (qmldir only). Multi-step “migrate callers” framing is obsolete. Optional: prune unused legacy aliases on `CommonStyle` (`primaryColor`, `fontSizeNormal`, …) after a reference check.
**What to do**: Delete `VideoOverlayStyle.qml` + qmldir entry when any video file is touched; optional orphan-alias prune on `CommonStyle`.
**Acceptance**: No type named `VideoOverlayStyle` in the tree; `tests/test_qml_imports.py` / relevant smokes green.
**Files**: `qml/overlays/video/components/VideoOverlayStyle.qml`, video `qmldir`, optionally `qml/theme/CommonStyle.qml`

---

## Resolved Debt

| ID | Title | Resolved | Notes |
|---|---|---|---|
| TD-056 | ROS callback → Qt telemetry marshal | 2026-07-29 | `RosTelemetryBridge` (QueuedConnection + last-wins); wheel/winch frozen POD + main `_apply_status_snapshot`; affinity tests. Follow-on residual band (same day): heartbeat per-channel bridge + lidar bridge; handler no longer dual-publishes `/controller/heartbeat` (PaintRosNode sole outbound; clear via `/clear/error`). Teensy remains lock+snapshot (TD-024). Residual: workflow-after-halt. ARCHITECTURE §8 |
| TD-054 | Concurrent ROS command I/O + post-halt motion latch | 2026-07-29 | Option A2 `RosCommandBus`; continuous-motion latch; e-stop before teleop. Residual: workflow-after-halt. ARCHITECTURE §8 |
| TD-041 | Governance/doc hygiene: stale plan entries, KNOWLEDGE mis-citation | 2026-07-29 | Frozen route ownership → ShellRouter; AGENTS launch/ fixed; KNOWLEDGE singleton note accurate for this repo; progress checklist no longer offers Phase 7 |
| TD-042 | Over-fitted test mirror and structural-selfie assertions | 2026-07-29 | Shared `assert_no_fatal_qml_warnings`; FakeShellRouter uses `DEFAULT_ROUTE_REGISTRY`; residual: large property-level smoke Fake* set (not rewritten) |
| TD-043 | Dead/duplicated state and metadata layers | 2026-07-29 | Dead StateStore joystick/control_* surface removed; live: control_mode/display_message/heartbeat. CapabilityCatalog left (live for gate/legality) — residual size only |
| TD-051 | Bundle cleanup string-list drift and unparented composition timers | 2026-07-29 | `_CLEANUP_ORDER` + leftover detection; `selection_model` on bundle; status_timer parented to qt_bridge + stop/disconnect/deleteLater; tests cover order inventory + shutdown |
| TD-049 | Device ports exist only for workflow; teleop/actions/safety bypass them | 2026-07-29 | Shared `ports/` Protocols (Teensy teleop+halt+status+workflow body; winch/wheel/valve halt). ControlProcessor off raw Teensy pubs (method dispatch; dual-sign joints; int casts). SafetyCoordinator halt Protocols. Workflow adapter types body as `SupportsTeensyWorkflowBody` + gimbal→`setSprayGunPitchAngle`. FakeTeensy method-only + new EF mode tests. Residual: `*Actions` still `Any`+getattr; not TD-054 |
| TD-050 | Two-phase collaborator injection and private-field wiring | 2026-07-29 | Public `SettingsManager.set_show_popup_fn` + `require_ui_ports`; `QtBridge.require_ui_ports`; `AppRuntime._finalize_ui_ports` before QML load; direct gate inject (no soft getattr); direct `workflow_editor.attach_runtime` (no hasattr). Set-once **not** enforced — overwrite-allowed setters + finalize non-None. Focused band green |
| TD-048 | QML feature/page injection depth incomplete | 2026-07-29 | Inject-first for *Actions/legality/settings/chrome: PageWheel/Winch/Status/Tuning/Settings; SystemControl+DeviceControl dual-surface; VideoFullscreen base-top write path; TopBar/Emergency/Joystick/overlayController. Root bag still 26 names (retire last-consumer later). Smoke harnesses inject. Full suite 434 passed |
| TD-044 | Ruff lint/format debt blocking CI | 2026-07-29 | `ruff format` + `ruff check --fix` + residual manual fixes; N815 ignored for Qt Signal/Property; ruff pinned `<0.17` in requirements-dev + CI. Local: check 0, format clean |
| TD-045 | CI test/typecheck missing system deps | 2026-07-29 | `requirements-ci.txt` omits PyGObject/vtk (conftest stubs gi; vtk not under test). typecheck/test apt: xcb/egl/gl/hidapi. Device installs still use full `requirements.txt` |
| TD-040 | Pyright allowlist excludes riskiest modules | 2026-07-29 | Fixed allowlist errors; strict ⊆ include; widened to full `models/`, `app_runtime`/`application`/`ros_node`, `services/workflow`. Residual exclude: `video_stream.py`, `base_top_view_service.py` (Gst/Property redeclaration noise). pyright 0 errors |
| TD-047 | AppRuntime service-locator façades + wiring/composer whole-runtime coupling | 2026-07-28 | Slice 1: removed ~18 context-key mirrors; façades only in `_context_properties`; dead `_heartbeat_status_error` + free wrappers gone. Slice 2: `SignalWiringPorts` / `QmlComposePorts` frozen dataclasses; `SignalWiring`/`QmlContextComposer` no longer take `AppRuntime`; `start_timers()` returns timer for root ownership. Full suite green |
| TD-046 | ControlProcessor teleop monolith; second command path undocumented | 2026-07-28 | Docs: module policy + ARCHITECTURE §7 table/do-not + AdminActionGate discrete-only note. Structure: high-state winch + wheel-travel helpers (`handlers/winch_teleop.py`, `wheel_travel_teleop.py`) behind stable `ControlProcessor` façade/`process_input` entry. Residual: EF stick modes still in façade. **Post-halt teleop latch absorbed into TD-054** (coupled acceptance, 2026-07-29). Full suite green |
| TD-037 | Status wrapper layer: blanket notify, stringly reads, duplicated telemetry | 2026-07-28 | Device status honesty: `models.{Winch,Wheel,Teensy,Valve,Lidar}Status` with per-property or fine-grained NOTIFY + `connect_required`; composer thinned (~1191→~730 LOC); shellConnectivity rewired to `wheel.availableChanged`; QML lidar Connections retargeted off blanket `changed`. Residual: videoRuntime/topBar multi-home voltages/SSH; recording multi-home; aggregator wrappers (recording/video/baseTopView); TD-033 soft pins. Full suite green |
| TD-038 | File-scale QML decomposition: PageWinch, EditWorkFlowTab, TeensyStatus | 2026-07-28 | A1: `WorkflowEditor.load_document`/`save_document`, no QML JSON document assembly. B: PageWinch ~1606→~213 LOC + `winch/components/*`. C: TeensyStatus ~831→~103 LOC + `status/components/teensy/*` tabs. D: workflow param forms under `systemcontrol/components/` (EditWorkFlowTab ~1027→~715). Tokens remain TD-002. Focused band green (workflow editor, winch/status smokes, qml imports) |
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
