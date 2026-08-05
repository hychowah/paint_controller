# Development Notes

---
### 2026-08-05 - Level C P4 Teensy pure HAL

**Goal**: TeensyHal without PySide6; shell owns timers/bridge/settings.
**Result**: ✅ Full suite green.
**Files**: teensy.py, teensy_shell.py, factory, tests/test_teensy_pure_hal.py

---
### 2026-08-05 - Level C P3 Winch + Wheel pure HAL

**Goal**: Pure wheel/winch HAL (no PySide6) + shells; continuous-zero e-stop; settings inject on shell.
**Result**: ✅ Full suite green.
**Files**: wheel.py/winch.py pure, wheel_shell/winch_shell, factory, tests/test_wheel_winch_pure_hal.py

---
### 2026-08-05 - Level C P2 availability + bridge ownership

**Goal**: Pure AvailabilityState; watchdog + telemetry bridges parented to DeviceIoShell.
**Result**: ✅ Full suite green. Adapters still hold Signals until P3.
**Files**: `core/availability.py`, `core/availability_watchdog.py`, `core/device_io_shell.py`, `controllers/_base.py`, wheel/winch/teensy bridge parent, `tests/test_availability_p2.py`

---
### 2026-08-05 - Level C P1 Lidar pure HAL pilot

**Goal**: Lidar pure HAL (no PySide6) + Qt shell owning bridges/Signals; Status contracts intact.
**Result**: ✅ Full suite green. Pure ban in `tests/test_pure_hal_no_pyside.py`.
**Files**: `controllers/lidar.py`, `controllers/lidar_shell.py`, `core/controller_factory.py`, `tests/test_lidar_pure_hal.py`

---
### 2026-08-05 - Level C P0 seams (DeviceNotifier + external bridge parent)

**Goal**: Land Level C P0 only — notification Protocol + prove `RosTelemetryBridge` can parent to a non-adapter shell. No pure-HAL device rewires.
**Issues**: None.
**Tried**: `ports/notifier.py` (`DeviceNotifier`, Null/Recording); `core/device_notifier.py` (`SignalDeviceNotifier`); bridge docstring; tests for pure + Qt notify and external-shell apply-on-main.
**Result**: Focused notifier+telemetry green; frozen concurrency bar `71 passed`; full suite `545 passed`. Production controllers unchanged.
**Files**: `ports/notifier.py`, `ports/__init__.py`, `core/device_notifier.py`, `core/ros_telemetry.py`, `tests/test_device_notifier.py`, `tests/test_ros_telemetry.py`, `docs/plan/02_LEVEL_C_PURE_HAL_PLAN.md`

---
### 2026-08-05 - Concurrency lock pack (ROS↔Qt / command bus)

**Goal**: Prove worker-thread post/callback affinity and halt vs continuous bus races so Level C (or any threading move) has a before/after bar.
**Tried**: Bridge/bus/RosThread real-thread contracts; device worker affinity + apply tid; product path: bound `command_bus` no raw publish until pump; SafetyCoordinator+live teleop+latch blocks ControlProcessor; wheel error signal only after main processEvents; Wind residual fence (documents sync mutate on calling thread).
**Result**: ✅ Full suite green. Level C deferred at `docs/plan/02_LEVEL_C_PURE_HAL_PLAN.md`. Residual still open: ESP32 real-thread stress; Wind not yet on TD-056 (fence only).
**Files**: `tests/test_ros_telemetry.py`, `tests/test_ros_io.py`, `tests/test_ros_node.py`, `tests/test_wheel.py`, `tests/test_winch.py`, `tests/test_teensy.py`, `tests/test_concurrency_product_paths.py`

---
### 2026-08-05 - Level B: strip Qt `@Property` from device adapters

**Goal**: Device HAL telemetry is plain Python `@property` + Signals; QML reads only via `*Status`.
**Tried**: Convert Property→`@property` on teensy/wheel/winch/lidar/esp32/wind; keep all producer Signals and public names for getattr. Structural ban `tests/test_device_adapter_no_qml_properties.py`.
**Result**: ✅ Full suite green (see session validation). Level C (no-QObject HAL) still deferred.
**Files**: `controllers/{teensy,wheel,winch,lidar,esp32_valve,wind_monitor}.py`, `tests/test_device_adapter_no_qml_properties.py`

---
### 2026-08-05 - Level A: strip device-adapter QML `@Slot` (dual-role)

**Goal**: Device HAL adapters must not expose QML-invokable `@Slot` command APIs; QML stays on `*Actions` / `*Status`.
**Tried**: Decorator-only strip on teensy/wheel/winch/lidar + `setValveTurn`; keep ESP32 `_finish_discovery_and_connect` (QueuedConnection worker). Structural ban `tests/test_device_adapter_no_qml_slots.py`. SSH/SystemMonitor out of scope.
**Result**: ✅ Full suite **517 passed**. Level B (Property retirement) deferred.
**Files**: `controllers/{teensy,wheel,winch,lidar,esp32_valve}.py`, `tests/test_device_adapter_no_qml_slots.py`

---
### 2026-07-31 - Extensibility slices: ActionKey, GatedActionMixin, context schema, status base, workflow ActionType

**Goal**: Reduce manual wiring when adding controllers/actions while preserving QML↔Python boundaries, safety gates, and deterministic construction/cleanup order.
**Issues**: Action keys duplicated across QML/catalog/actions/overrides; `*Actions` repeated `_run`/`_fail` boilerplate; context-property list and `compose()` updated separately; simple status wrappers were ~100 LOC of mechanical boilerplate; workflow action type knowledge duplicated in handlers/runner/scheduler/editor.
**Tried**: 
- `ActionKey(str, Enum)` + `tests/test_action_key_integrity.py` for Python/catalog/QML parity
- `GatedActionMixin` with `_run_gated`/`_run_ungated`/`_fail` for `WheelActions`, `WinchActions`, `TeensyActions`, `TuningActions`, `BaseTopViewActions`
- `ContextProp`/`BundleProp`/`PortsProp`/`WrapperProp` schema in `qml_context_composer.py`; `_EXPECTED_CONTEXT_PROPERTY_NAMES` derived from it
- `SimpleDeviceStatus` base + `_make_status_field` for `WheelStatus`, `WinchStatus`, `ValveStatus`, `LidarStatus`; `TeensyStatus` stays custom
- `ActionType`/`ParamSpec`/`ActionMetadata` registry in `services/workflow/action_schema.py`; drives handler registration, runner descriptions, scheduler winch detection, and editor param validation
**Result**: ✅ Full suite **515 passed**; startup smoke **12 passed**; pyright green on touched files. Committed as five separate slices.
**Files**: `models/action_keys.py`, `models/gated_action_mixin.py`, `models/simple_device_status.py`, `core/qml_context_composer.py`, `services/workflow/action_schema.py`, `docs/extensibility-review.md`, plus refactored actions/status/workflow files and new integrity tests

---
### 2026-07-31 - JoystickOverlay lingering pressed background fix

**Goal**: Fix the lighter-blue pressed background that remained on the previously selected control mode in the joystick selection menu.
**Issues**: The delegate's `visuallyPressed` state was set on press but never cleared when the commit timer fired and closed the menu. `ListView` recycles delegates, so the stale pressed highlight could reappear on the wrong row when the menu reopened. Also, `parent` inside a `Timer` refers to the Timer's parent (the `MouseArea`), not the delegate, so clearing had to use the delegate's id.
**Tried**: Added `delegateRoot.visuallyPressed = false` in the commit timer trigger and guarded the pressed-feedback `Rectangle` with `visible: delegateRoot.visuallyPressed && menuOverlay.menuVisible`. Added object names to the delegate, ListView, menu containers, and pressed feedback for testability. Added a QML regression test that asserts the feedback disappears when the menu is hidden.
**Result**: ✅ Focused band `30 passed` (joystick_overlay, joystick_selection, overlay_controller, startup_smoke_shell, startup_smoke_home, qml_imports); `qmllint` clean on `JoystickOverlay.qml`.
**Files**: `python/paint_controller/qml/overlays/JoystickOverlay.qml`, `tests/test_joystick_overlay.py`

---
### 2026-07-29 - Teleop mode catalog (A+B+C)

**Goal**: Single SOT for continuous stick modes; kill index-based selection policy.
**Tried**: `handlers/policy/teleop_modes.py` (menu/display/configs/standard apply/policy sets); selection + engine wire; `build_default_control_configs` delegates; integrity tests.
**Result**: ✅ Focused band **90 passed** (teleop_modes, joystick_selection, control_processor, layer_depth, input, overlay).
**Files**: `teleop_modes.py`, `teleop_control_map.py`, `continuous_teleop_engine.py`, `joystick_selection.py`, `ARCHITECTURE.md`, tests

---
### 2026-07-29 - Workflow halt-stop + Teensy bridge residual

**Goal**: Halt stops workflow execution without dual matrix; Teensy status on RosTelemetryBridge.
**Tried**: `stop_execution` / `request_stop_nonblocking` (no join, no `_emergency_shutdown`); coordinator bind after factory runner create; play/resume gate on latch; Teensy ROS posts device keys only, main apply preserves user fields.
**Result**: ✅ Full suite **484 passed**. Residual: in-flight workflow oneshot; UI stop still has local emergency retract.
**Files**: safety_coordinator, workflow_runner/executor, controller_factory, teensy, tests, ARCHITECTURE

---
### 2026-07-29 - Concurrency residual band (structure consistency)

**Goal**: Clear high-value residuals after TD-054/056 for one telemetry dialect.
**Tried**: Heartbeat per-channel `RosTelemetryBridge` + main apply; remove dual `/controller/heartbeat` pub from handler (PaintRosNode sole outbound; clear only `/clear/error`); lidar distance/angle bridges.
**Result**: ✅ Full suite **495 passed**. Residual left: workflow-after-halt; Teensy lock+snapshot dialect.
**Files**: `handlers/heartbeat.py`, `controllers/lidar.py`, tests, ARCHITECTURE/tech-debt/progress

---
### 2026-07-29 - TD-056 resolved (ROS→Qt telemetry marshal)

**Goal**: Wheel/winch status paths: no unlocked ROS-thread mutation of QML/teleop-visible fields.
**Tried**: Deep `RosTelemetryBridge` (QueuedConnection + last-wins); frozen POD snapshots; main `_apply_status_snapshot`; affinity tests (callback alone does not mutate; processEvents applies).
**Result**: ✅ Focused + full suite green. TD-056 → Resolved. Residual: heartbeat restore/status from ROS; Teensy stays lock+snapshot (TD-024).
**Files**: `core/ros_telemetry.py`, wheel/winch controllers, tests, ARCHITECTURE §8, tech-debt, progress board

---
### 2026-07-29 - TD-054 resolved (RosCommandBus + motion latch)

**Goal**: Sole ROS command publish affinity on RosThread; fail-closed continuous teleop after halt.
**Tried**: Option A2 `RosCommandBus` (continuous last-wins + oneshot); bind wheel/winch/teensy at construct; `SafetyCoordinator.continuous_motion_allowed` + `invalidate_continuous` + teensy `suppress_continuous_thrust`; status tick e-stop before teleop.
**Result**: ✅ Full suite **477 passed**. TD-054 → Resolved. Next integrity: **TD-056**. Residuals: workflow-after-halt, dual heartbeat pub, pre-existing `ef_yaw_control_pub` never created in Teensy setup (unrelated).
**Files**: `core/ros_io.py`, `ros_node.py`, `app_runtime.py`, `controller_factory.py`, `signal_wiring.py`, wheel/winch/teensy, safety_coordinator, control_processor, tests, ARCHITECTURE §8, tech-debt, progress board

---
### 2026-07-29 - TD-048 resolved (full inject-first)

**Goal**: Finish QML injection depth — *Actions/legality/settings/chrome via `required property` on pages/features.
**Tried**: A PageWheel; B PageWinch+children; C SystemControl+DeviceControl dual-surface; D Tuning; E Status/Teensy; F settingsManager threading; G video base-top write path; H TopBar/Emergency/Joystick/overlayController. Smoke harnesses avoid required-prop name-shadowing.
**Result**: ✅ Full suite **434 passed**. Root bag still 26 names (retire-last later). TD-048 → Resolved.
**Files**: MainWindow, MultiScreenListUI, pages/features/overlays/navigation QML, startup smokes, tech-debt, progress board

---
### 2026-07-29 - TD-044 + TD-045 + TD-040 (CI control plane)

**Goal**: Make lint/typecheck/test real gates — ruff green, CI install resilient, pyright meaningful.
**Tried**: TD-044: format + autofix + N815 ignore + residual F841/E722/F601/test fixes; ruff pin. TD-045: `requirements-ci.txt` (no PyGObject/vtk) + apt xcb/egl/hidapi on typecheck/test. TD-040: fix 2 allowlist errors; strict⊆include; widen models/app_runtime/workflow; exclude video services residual.
**Result**: ✅ ruff check/format clean; pyright 0; full suite **434 passed**. GHA not re-run here (local gates green).
**Files**: `pyproject.toml`, `requirements-ci.txt`, `requirements-dev.txt`, `.github/workflows/ci.yml`, `pyrightconfig.json`, core/models/workflow fixes, mass format, tech-debt

---
### 2026-07-28 - TD-047 resolved (façade demirror + ports)

**Goal**: Close AppRuntime service-locator debt: demirror façades, then ports for wiring/composer.
**Tried**: Slice 1: removed ~18 context-key mirrors; façades only in `_context_properties`; dead free wrappers/`_heartbeat_status_error` gone. Slice 2: `SignalWiringPorts` + `QmlComposePorts` frozen dataclasses; `SignalWiring`/`QmlContextComposer` no longer take `AppRuntime`; `start_timers()` returns timer; tests construct ports only.
**Result**: ✅ Full suite **434 passed**. TD-047 moved to Resolved.
**Files**: `app_runtime.py`, `signal_wiring.py`, `qml_context_composer.py`, runtime tests, tech-debt, progress board

---
### 2026-07-28 - Software architecture research → tech-debt refresh

**Goal**: Multi-agent deep research on software-only professional Qt gaps; update debt board (no HMI product work, no code refactors).
**Tried**: Five parallel explore agents — composition/DI/lifecycle, QML contract injection, QML modules/tokens/kit, ports/domain modularity, test/CI control plane. Cross-checked against existing TD-032…047.
**Result**: ✅ `docs/tech-debt.md` program-track refreshed. New **TD-048–053** (injection depth, device ports, late injection, cleanup inventory, QML schemas, dual overlay stack). Reworded TD-047/040/042/002/016 from evidence. Progress board Next aligned. Explicit non-goals: mega-Backend, TD-032 reopen, HMI safety track.
**Files**: `docs/tech-debt.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `DEVNOTES.md`

---
### 2026-07-28 - TD-046 resolved (teleop docs + selective structure)

**Goal**: Document dual command paths (gate vs continuous teleop); extract high-state winch/wheel teleop without product UX latch.
**Tried**: Module docstring on `control_processor`; ARCHITECTURE §7 table/do-not; AdminActionGate discrete-only note; `winch_teleop` + `wheel_travel_teleop` flat helpers with façade delegates. Skipped `handlers/teleop/` package and EF mode splits.
**Result**: ✅ 35 control_processor tests + full suite 433 passed. Residual: EF stick mass in façade; post-halt stick inhibit still product-only.
**Files**: `control_processor.py`, `winch_teleop.py`, `wheel_travel_teleop.py`, `admin_action_gate.py`, `ARCHITECTURE.md`, tech-debt

---
### 2026-07-28 - TD-037 resolved (device status honesty + valve/lidar)

**Goal**: Per-property/fine-grained QML status models outside the composer for device telemetry families.
**Tried**: Winch/Wheel/Teensy + residual Valve/Lidar status models with `connect_required`; shellConnectivity wheel rewire; Teensy cache/diff; QML lidar `onChanged` → `onDistanceChanged`/`onAngleChanged`; notify isolation tests.
**Result**: ✅ Full suite green. Composer ~1191→~730 LOC. Residual: videoRuntime multi-home, aggregator wrappers, TD-033 soft pins.
**Files**: `models/{status_wiring,winch,wheel,teensy,valve,lidar}_status.py`, `qml_context_composer.py`, WallDetectionOverlay/PageMonitor, notify/composer tests, docs

---
### 2026-07-28 - TD-038 resolved (C+D + close-out)

**Goal**: Finish residual TeensyStatus tab extract (C) and EditWorkFlowTab param-panel extract (D); mark TD-038 resolved.
**Tried**: Teensy tabs under `pages/status/components/teensy/*`; host TeensyStatus as header+tab bar+StackLayout. Workflow param forms + shared `WorkflowParamField` under `overlays/systemcontrol/components/`; EditWorkFlowTab Component wrappers only.
**Result**: ✅ TeensyStatus ~103 LOC; EditWorkFlowTab ~715 LOC. Focused band 11+ passed (status smoke, workflow editor smoke/unit, winch smoke, qml imports). TD-038 moved to Resolved; next program-track item TD-037.
**Files**: TeensyStatus + teensy tabs, EditWorkFlowTab + Workflow*Params, `docs/tech-debt.md`, progress board

---
### 2026-07-28 - TD-038 Slice B: PageWinch component extraction

**Goal**: Shrink `PageWinch.qml` god page into a composer + page-local components without restyle or TouchSwitch migration.
**Tried**: Extracted notification popup, shared enable toggle (power/load as-is dual-button + toast), move increment/absolute panels, quick actions bar, and right-column telemetry panel under `qml/pages/winch/components/`. Notify/activity via signals to keep toast/log ownership on the page.
**Result**: ✅ PageWinch ~213 LOC (from ~1606). `test_page_winch_loads_with_explicit_winch_status` + `test_qml_imports` green. Structural TD-038 A1+B complete; C/D optional.
**Files**: `python/paint_controller/qml/pages/winch/PageWinch.qml`, `python/paint_controller/qml/pages/winch/components/*`, `docs/tech-debt.md`

---
### 2026-07-28 - TD-038 Slice A1: workflow document ownership → Python

**Goal**: Remove workflow document assembly/JSON transport from `EditWorkFlowTab.qml` so Python owns save-time document construction (TD-038 program half, first slice).
**Tried**: Added `WorkflowEditor.load_document` / `save_document` with shared `_persist_workflow` (collision → normalize → atomic write). Retired JSON `get_workflow_data` / `save_workflow_data`. QML keeps local edit buffers for in-place param edits; only load/save crossed the boundary. Updated `FakeWorkflowEditor` + unit/smoke tests.
**Result**: ✅ `9 passed` for `tests/test_workflow_editor.py tests/test_startup_smoke_workflow_editor.py tests/test_qml_imports.py`. No `JSON.stringify`/`JSON.parse` remain in `EditWorkFlowTab.qml`.
**Files**: `python/paint_controller/services/workflow/workflow_editor.py`, `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `tests/test_workflow_editor.py`, `tests/startup_smoke_support.py`, `docs/tech-debt.md`

---
### 2026-07-28 - TD-032 QML boundary close-out

**Goal**: Close boundary retirement program — retire dual-owner `deviceActionHandler`, drop residual root globals, freeze contract.
**Tried**: Folded power enable/relay/home into `teensyActions` / winch enable into `winchActions` (home stays ungated); QML call sites updated; deleted `device_actions.py`; `qtBridge.display_message` forwards StateStore; renamed context `backend`→`qtBridge`; removed `stateStore` root; smoke/factory/composer/catalog tests updated.
**Result**: ✅ 62 passed focused band (device power, teensy actions, composer, catalog, factory, app_runtime, startup smokes, qml imports). Root expected names ~26. Program closed.
**Files**: teensy/winch actions, controller_factory, qml_context_composer, qt_bridge, QML pages/overlays, tests, tech-debt, progress board, ARCHITECTURE.md

---
### 2026-07-28 - System-control toggles unblocked; legality default off in dev

**Goal**: System control menu toggles must work regardless of heartbeat; keep legality enforcement off by default until development finishes.
**Tried**: Expanded `status-admin` / `status-admin-warning-ok` to all heartbeat states (IDLE/ONTASK/WARNING/ERROR). Schema + gate default `action_legality_enforced=false`; removed load-time force-true. Lab/field can force on with `PAINT_ACTION_LEGALITY_ENFORCED=1`.
**Result**: ✅ 46 passed settings/gate band. Motion/maintenance actions still blocked in ERROR when enforcement is on.
**Files**: `admin_action_gate.py`, `settings.py`, related tests

---
### 2026-07-28 - TD-036 gated settings writes, XDG path, legality default

**Goal**: Close TD-036 — last free-form machine-affecting QML write path, dual settings API, in-tree config path, legality ship bypass.
**Issues**: `settingsManager.apply*/set*` unguarded; Property setters wrote via ungated `set`; package-tree `settings.json`; `action_legality_enforced: false` in file; gate only knew action capabilities not setting keys; `mixed-admin-route`/`safety-admin` unregistered.
**Tried**: Gate QML slots in `SettingsManager` after `set_admin_action_gate` from AppRuntime; `_action_metadata` falls back to `getSettingCapability`; env `PAINT_ACTION_LEGALITY_ENFORCED`; force-true legality on load/migrate; live path `PAINT_CONTROLLER_SETTINGS_PATH` → XDG; package file template-only; read-only generated Properties; SettingInputField→apply*; deny refresh on ManagedSettingSpinBox; hard-block QML writes to legality key.
**Result**: ✅ Focused band `tests/test_settings_runtime.py tests/test_settings_schema.py tests/test_admin_action_gate.py tests/test_capability_catalog.py` green at 45 passed; app_runtime gate injection fixed.
**Files**: `python/paint_controller/core/settings.py`, `admin_action_gate.py`, `action_legality_model.py`, `app_runtime.py`, QML ManagedSettingSpinBox/SettingInputField, `python/config/settings.json`, tests, `docs/tech-debt.md`

---
### 2026-07-28 - TD-039 concurrency loose ends

**Goal**: Close the four TD-039 concurrency items (BaseTopView map race, ROS error consumer, Steam Deck in-lock emit, CameraStream null image cleanup).
**Issues**: GUI `_reinitialize_maps` wrote `map1`/`map2` while worker `cv2.remap` ran; k setters also wrote `dist_coeffs` in-place from GUI; `CameraStream.cleanup` set `image=None` unlocked; `button_held` emitted under non-recursive mutex; `RosThread.error_occurred` unwired and spin bookkeeping dead.
**Tried**: Worker-owned recompute via service `mapsRecomputeRequested` → `QueuedConnection` to `worker.recompute_maps`, coalesced with 0ms single-shot `QTimer`; k setters only set floats; image provider black placeholder under lock + defensive `requestImage`; hold signals collected then emitted after unlock; ROS errors → throttled `display_message`; deleted `_last_spin_time`/`_spin_timeout`.
**Result**: ✅ Focused band 19 passed: `tests/test_video_stream.py tests/test_base_top_view_service.py tests/test_steam_deck_handler.py tests/test_signal_wiring.py`. Residual accepted: GUI scalar float writes while worker reads (low risk vs map tables).
**Files**: `python/paint_controller/services/base_top_view_service.py`, `python/paint_controller/services/video_stream.py`, `python/paint_controller/handlers/steam_deck.py`, `python/paint_controller/core/ros_node.py`, `python/paint_controller/core/signal_wiring.py`, `tests/test_video_stream.py`, `tests/test_base_top_view_service.py`, `tests/test_steam_deck_handler.py`, `tests/test_signal_wiring.py`, `docs/tech-debt.md`

---
### 2026-07-28 - Tech debt re-prioritisation (program-side architecture review)

**Goal**: Fold multi-perspective architecture review insights into `docs/tech-debt.md` for a program-side FE+BE track (UI/UX and industrial HMI deferred).
**Issues**: Active TDs were accurate but mostly `medium`; TD-032 still pointed at resolved TD-033; backend module-shape gaps (ControlProcessor, AppRuntime bag) and legality ship default were untracked; progress board "Next" soft-offered more retirement work past diminishing returns.
**Tried**: Revalidated diagnoses against the live tree; rewrote Active Debt with priority definition + architecture-leverage tags; program-track recommended order; TD-039 and TD-036 → high; TD-038 split into program-first vs UI-later; added TD-046 (teleop monolith / second command path) and TD-047 (AppRuntime service-locator surface); legality default folded into TD-036; fixed TD-032 close-out redirect; aligned `00_ARCHITECTURE_PROGRESS.md` Next/snapshot.
**Result**: Docs only — no code or tests run. Tracker is the control plane for the next program slices.
**Files**: `docs/tech-debt.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `DEVNOTES.md`

---
### 2026-07-24 22:30 - Phase 8: AppRuntime Wiring Extraction

**Goal**: Execute Phase 8 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: keep `AppRuntime` as a thin composition root by moving QML context-property construction and signal wiring into focused helpers.
**Issues**: `python/paint_controller/core/app_runtime.py` had grown to ~1650 lines, mixing runtime orchestration with status-wrapper classes, context-property dict construction, and signal/timer wiring. This made the QML contract hard to test in isolation and blurred ownership.
**Tried**: Created `python/paint_controller/core/qml_context_composer.py` owning `_EXPECTED_CONTEXT_PROPERTY_NAMES`, `_SystemControlServices`, all `_*Status` / `_VideoRuntime*` wrapper classes, the `_read_*` helpers, and `QmlContextComposer.compose()`. Created `python/paint_controller/core/signal_wiring.py` owning `SignalWiring.wire()` (Steam Deck callbacks + all signal connections) and `SignalWiring.start_timers()` (status timer, system monitor, deferred video startup). Slimmed `AppRuntime` to object creation, bootstrap orchestration, context-property registration, and shutdown sequencing. Updated `tests/test_app_runtime_runtime.py` to import `_EXPECTED_CONTEXT_PROPERTY_NAMES` from `qml_context_composer` and to call `SignalWiring(runtime).wire()` directly. Added `tests/test_qml_context_composer.py` and `tests/test_signal_wiring.py` for focused coverage. Extended `_StatusTimerRecorder` and `_SystemMonitorRecorder` and updated `_SignalRecorder`/`_QtBridgeRecorder` to support the new tests. Added the two new modules to `pyrightconfig.json`.
**Result**: ✅ Focused band `tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_startup_smoke.py tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_qml_imports.py tests/test_shell_router.py tests/test_qml_context_composer.py tests/test_signal_wiring.py` green at `58 passed`; full suite green at `313 passed`; `qmllint` clean; pyright clean on included scope. `colcon build --packages-select paint_interfaces paint_controller_ros2` still fails pre-existingly because the `resource/` directory is missing from the package root.
**Files**: `python/paint_controller/core/qml_context_composer.py`, `python/paint_controller/core/signal_wiring.py`, `python/paint_controller/core/app_runtime.py`, `tests/test_app_runtime_runtime.py`, `tests/test_qml_context_composer.py`, `tests/test_signal_wiring.py`, `tests/controller_factory_runtime_support.py`, `pyrightconfig.json`, `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`.

---
### 2026-07-24 21:30 - Phase 7: MainWindow.qml Shell Simplification

**Goal**: Execute Phase 7 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: move routing and multi-screen window policy out of `MainWindow.qml` into Python models, and move backend fullscreen-video signal handling from QML into Python wiring.
**Issues**: `MainWindow.qml` owned the full page registry (keys, titles, icons, route order) and imperative navigation helpers (`navigateToPage`, `getRouteOrder`, `getPageConfig`). It also owned the secondary `MultiScreenListUI` window lifecycle inline. A `Connections { target: backend }` block imperatively toggled fullscreen video from QML. `winchController` was still registered as a context property but had no live QML consumers.
**Tried**: Created `ShellRouter` in `python/paint_controller/models/shell_router.py` owning the route registry, `currentRoute` property, `currentRouteOrder` property, and `navigateTo`/`routeOrder` slots. Created `MultiScreenHost.qml` to encapsulate secondary window creation, placement, and destruction. Updated `MainWindow.qml` to use `shellRouter.routeRegistry`, `shellRouter.currentRoute`, and `shellRouter.navigateTo()`, keeping only a minimal QML-side route-to-component map. Replaced inline multi-screen code with `MultiScreenHost`. Removed the backend `onToggleVideoOverlayRequested`/`onUpdateVideoSourceRequested` handlers from `MainWindow.qml` and wired `qt_bridge.toggleVideoOverlayRequested` → `overlay_host.toggle_video_fullscreen(source)` and `qt_bridge.updateVideoSourceRequested` → `overlay_host.set_video_fullscreen_source(source)` in `AppRuntime._wire_signals()`. Removed `winchController` from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`. Updated `SelectBar.qml` to consume `shellRouter` directly. Added `FakeShellRouter` and `FakeShellState` to `tests/startup_smoke_support.py`, removed `winchController` from smoke fixtures, and updated startup-smoke tests that exercised `navigateToPage`/`selectedPageKey`. Added `tests/test_shell_router.py` for focused unit coverage.
**Result**: ✅ Focused band `tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_startup_smoke.py tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_qml_imports.py tests/test_shell_router.py` green at `45 passed`; full suite green at `300 passed`; `qmllint` clean on touched QML files; `shell_router.py` pyright clean. `colcon build --packages-select paint_interfaces paint_controller_ros2` fails pre-existingly because `resource/` directory is missing from package root.
**Files**: `python/paint_controller/models/shell_router.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/core/MultiScreenHost.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `python/paint_controller/core/app_runtime.py`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`, `tests/test_startup_smoke.py`, `tests/test_startup_smoke_shell.py`, `tests/test_shell_router.py`, `pyrightconfig.json`.

---
### 2026-07-24 20:30 - Phase 6: Remaining Raw Controller Retirement

**Goal**: Execute Phase 6 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: retire the remaining raw controllers from the app-scope QML context.
**Issues**: `TeensyStatus.qml` still read `teensyController.all_status.*` for rails, propellers, IMU, and spray-gun details. `PageWheel.qml` read frame-ready signals from `baseStreamHandler`. `MainWindow.qml` listened to `screenManager.screens_changed` and called `screenManager.get_screen_count()`. The raw globals `teensyController`, `esp32ValveController`, `lidarController`, `controlProcessor`, `systemMonitor`, `screenRecorder`, `rosBagRecorder`, `screenManager`, and `baseStreamHandler` were still in `_EXPECTED_CONTEXT_PROPERTY_NAMES` even though bounded status/action models (`teensyStatus`, `valveStatus`, `lidarStatus`, `videoRuntime`, `recordingStatus`, `shellState`) already covered their live QML consumers.
**Tried**: Extended `_TeensyStatus` in `python/paint_controller/core/app_runtime.py` with the missing Teensy `all_status` fields: rails (`topRailPosition`, `topRailSpeed`, `topRailCurrent`, `armRailPosition`, `armRailSpeed`, `armSensorDist`), props (`leftPropPosition`, `rightPropPosition`, `leftPropPwm`, `rightPropPwm`), and spray-gun details (`sprayGunPitch`, `gimbalPitchMotorTemp`, `gimbalRollMotorAngle`, `gimbalRollMotorCurrent`, `gimbalRollMotorTemp`, `sprayGunTrigger`). Updated `TeensyStatus.qml` to bind to `teensyStatusRect.teensyStatus.*` for all reads. Repointed `PageWheel.qml` to `videoRuntime.feeds` for `baseFrontFrameReady`/`baseRearFrameReady`. Repointed `MainWindow.qml` to `shellState.screen_count_changed` and `shellState.screen_count`. Removed the nine retired names from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()` in `AppRuntime`. Updated `tests/startup_smoke_support.py` to drop retired globals and add the new `teensyStatus` properties. Removed workaround `context_objects[...] = None` injections from startup-smoke tests. Extended `_TeensyControllerRecorder` and added assertions in `tests/test_app_runtime_runtime.py` for the new properties plus retirement assertions.
**Result**: ✅ Focused band `tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_startup_smoke.py tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_qml_imports.py tests/test_teensy.py` green at `48 passed`; full suite green at `294 passed`; `qmllint` clean on touched QML files; no remaining references to the nine retired raw globals in `python/paint_controller/qml`.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`, `python/paint_controller/qml/pages/wheel/PageWheel.qml`, `python/paint_controller/qml/core/MainWindow.qml`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`, `tests/controller_factory_runtime_support.py`, `tests/test_startup_smoke.py`, `tests/test_startup_smoke_shell.py`, `tests/test_startup_smoke_home.py`.

---
### 2026-07-24 19:00 - Phase 5: Device Operations Split (`recordingActions`, `teensyActions`, `systemActions`, extended `winchActions`)

**Goal**: Execute Phase 5 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: dissolve `DeviceOperationsHandler` into feature-root action models without creating shallow mirrors.
**Issues**: `DeviceOperationsHandler` mixed recording toggles, Teensy feature toggles, winch load detection, lidar power, and error clearing in a single handler-shaped global. `DeviceControlTab.qml` and `PageWinch.qml` called it for writes while reads already flowed through bounded status models. Keeping it blocked further QML surface retirement.
**Tried**: Created `RecordingActions` in `python/paint_controller/models/recording_actions.py` owning EF/base camera, screen, and ROS bag recording toggles. Created `TeensyActions` in `python/paint_controller/models/teensy_actions.py` (named to align with the existing `*_actions.py` family) owning stability, yaw, auto-correction, spray-gun leveling, roller steering, swing damping, spray-gun LED, and lidar power toggles. Created `SystemActions` in `python/paint_controller/models/system_actions.py` owning `clearErrors`. Extended `WinchActions` with `setLoadDetectionEnabled` and `toggleLoadDetection` so load detection stays in the winch feature root. Deleted `python/paint_controller/handlers/device_operations.py`. Updated `controller_factory.py` to instantiate the new models, add them to `ControllerBundle`, and remove `device_operations_handler`. Updated `AppRuntime` to register `recordingActions`, `teensyActions`, and `systemActions`, remove `deviceOperationsHandler` from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`, and wire the new models from the bundle. Updated `DeviceControlTab.qml` to call the new models and `PageWinch.qml` to use `winchActions.setLoadDetectionEnabled`. Updated `CapabilityCatalog` authority for `winch.load_detection` to `winchActions.setLoadDetectionEnabled`. Replaced `tests/test_device_operations.py` with `tests/test_recording_actions.py`, `tests/test_teensy_actions.py`, and `tests/test_system_actions.py`; extended `tests/test_winch_motion_handler.py` with load-detection coverage. Updated smoke fakes, factory/AppRuntime tests, and `pyrightconfig.json`.
**Result**: ✅ Focused band `tests/test_recording_actions.py tests/test_teensy_actions.py tests/test_system_actions.py tests/test_winch_motion_handler.py tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_capability_catalog.py tests/test_startup_smoke.py tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_startup_smoke_workflow_editor.py tests/test_qml_imports.py` green at `59 passed`; full suite green at `294 passed`; `qmllint` clean on touched QML files; pyright clean per `pyrightconfig.json`; no remaining `deviceOperationsHandler` references in production code, tests, or QML context.
**Files**: `python/paint_controller/models/recording_actions.py`, `python/paint_controller/models/teensy_actions.py`, `python/paint_controller/models/system_actions.py`, `python/paint_controller/models/winch_actions.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/pages/winch/PageWinch.qml`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`, `tests/test_controller_factory_runtime.py`, `tests/test_capability_catalog.py`, `tests/test_recording_actions.py`, `tests/test_teensy_actions.py`, `tests/test_system_actions.py`, `tests/test_winch_motion_handler.py`, `pyrightconfig.json` (plus deletion of `python/paint_controller/handlers/device_operations.py` and `tests/test_device_operations.py`).

---
### 2026-07-24 18:15 - Phase 4: Base Top-View Family (`baseTopViewActions` / `baseTopViewStatus`)

**Goal**: Execute Phase 4 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: retire `baseTopViewAdminHandler` and the raw `baseTopViewController` global from the app-scope QML context, and fix the `BaseTopViewService` teardown race.
**Issues**: `BaseTopViewSettingsPopup.qml` wrote calibration values through `baseTopViewAdminHandler.request*` and read them from `baseTopViewController.*`. `BaseFrontOverlay.qml` also read `baseTopViewController.editMode` and refreshed on its `frameReady`. Both globals kept a handler-shaped boundary and a `*Controller`-named global alive in the QML contract. `BaseTopViewService.cleanup()` quit the worker thread without first disconnecting `stream.frameReady` from `worker.process_frame`, which could deliver frames to a dying worker.
**Tried**: Created `BaseTopViewActions` in `python/paint_controller/models/base_top_view_actions.py` with QML-facing camelCase slots (`setZoom`, `setOffsetX`, `setOffsetY`, `setCropEnabled`, `setCropWidthRatio`, `setCropCenterX`, `setK1`–`setK4`, `saveSettings`, `resetToDefaults`), owning admin-gate, logging, error emission, and dispatch like `WheelActions`/`TuningActions`. Created `_BaseTopViewStatus` in `python/paint_controller/core/app_runtime.py` following the existing `_WheelStatus`/`_TeensyStatus` pattern, exposing read-only properties and re-emitting `frameReady`. Deleted `python/paint_controller/handlers/base_top_view_admin.py`. Updated `controller_factory.py` to instantiate `BaseTopViewActions`, add `base_top_view_actions` to `ControllerBundle`, and remove `base_top_view_admin_handler`. Updated `AppRuntime` to register `baseTopViewActions`/`baseTopViewStatus` and remove `baseTopViewAdminHandler`/`baseTopViewController` from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`. Updated `CapabilityCatalog` authorities for the base-top view action keys to `baseTopViewActions`, `baseTopViewActions.saveSettings`, and `baseTopViewActions.resetToDefaults`. Updated `BaseTopViewSettingsPopup.qml` to read from `baseTopViewStatus` and write through `baseTopViewActions`; updated `BaseFrontOverlay.qml` to use `baseTopViewStatus` for `editMode` and `frameReady`. Fixed `BaseTopViewService.cleanup()` to set `_enabled = False`, disconnect `frameReady` (guarded by a new `_frame_ready_connected` flag) before `worker_thread.quit()`, and updated the setter to maintain the flag. Replaced `tests/test_base_top_view_admin_handler.py` with `tests/test_base_top_view_actions.py` and added a teardown regression test in `tests/test_base_top_view_service.py`. Updated smoke fakes, factory/AppRuntime tests, and `pyrightconfig.json`.
**Result**: ✅ Focused band `tests/test_base_top_view_actions.py tests/test_base_top_view_service.py tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_startup_smoke.py tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_startup_smoke_workflow_editor.py tests/test_qml_imports.py` green at `45 passed`; full suite green at `287 passed`; `qmllint` clean on touched QML files; pyright clean per `pyrightconfig.json`; no remaining `baseTopViewAdminHandler` or `baseTopViewController` references in production QML, Python, or tests.
**Files**: `python/paint_controller/models/base_top_view_actions.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/services/base_top_view_service.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/overlays/video/components/BaseTopViewSettingsPopup.qml`, `python/paint_controller/qml/overlays/video/components/BaseFrontOverlay.qml`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`, `tests/test_controller_factory_runtime.py`, `tests/test_base_top_view_actions.py`, `tests/test_base_top_view_service.py`, `pyrightconfig.json` (plus deletion of `python/paint_controller/handlers/base_top_view_admin.py` and `tests/test_base_top_view_admin_handler.py`).

---
### 2026-07-24 17:15 - Phase 3: Tuning Family (`tuningActions`)

**Goal**: Execute Phase 3 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: retire `tuningAdminHandler` from the app-scope QML context and stop direct `teensyController.all_status` reads in `PageTuning.qml`.
**Issues**: `PageTuning.qml` called `tuningAdminHandler.requestShortYawPid` / `requestLongYawPid` and read `teensyController.all_status` for `imu_yaw`, `imu_pitch`, `imu_roll`, `yaw_command`, and the yaw PID gains. `CapabilityCatalog` authorities pointed to `tuningAdminHandler`. `TuningAdminHandler` was a handler-shaped global that belonged in a feature-root action model.
**Tried**: Created `TuningActions` in `python/paint_controller/models/tuning_actions.py` with QML-facing camelCase slots `setShortYawPid` and `setLongYawPid`, owning admin-gate, logging, error emission, and dispatch like `WheelActions`/`WinchActions`. Deleted `python/paint_controller/handlers/tuning_admin.py`. Updated `controller_factory.py` to instantiate `TuningActions`, add `tuning_actions` to `ControllerBundle`, and remove `tuning_admin_handler`. Updated `AppRuntime` to register `tuningActions`, remove `tuningAdminHandler` from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`, and extend `_TeensyStatus` with `yawCommand`, `yawPidP`, `yawPidI`, `yawPidD`. Updated `CapabilityCatalog` authorities to `tuningActions.setShortYawPid` / `tuningActions.setLongYawPid`. Updated `PageTuning.qml` to use `tuningActions.*` and `teensyStatus.*` exclusively. Replaced `tests/test_tuning_admin_handler.py` with `tests/test_tuning_actions.py`. Updated smoke fakes, factory/AppRuntime tests, `test_capability_catalog.py`, and `test_controller_factory_runtime.py`. Added `tuning_actions.py` to `pyrightconfig.json`.
**Result**: ✅ Focused band `tests/test_tuning_actions.py tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_capability_catalog.py tests/test_action_legality_model.py tests/test_startup_smoke.py tests/test_qml_imports.py` green at `41 passed`; full suite green at `286 passed`; `qmllint` clean on all QML files; pyright clean per `pyrightconfig.json`; no remaining `tuningAdminHandler` references in production code, tests, or QML context.
**Files**: `python/paint_controller/models/tuning_actions.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/pages/tuning/PageTuning.qml`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`, `tests/test_controller_factory_runtime.py`, `tests/test_capability_catalog.py`, `tests/test_tuning_actions.py`, `pyrightconfig.json` (plus deletion of `python/paint_controller/handlers/tuning_admin.py` and `tests/test_tuning_admin_handler.py`).

---
### 2026-07-24 16:54 - Phase 2: Wheel Family (`wheelActions`)

**Goal**: Execute Phase 2 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: retire `wheelController` from the app-scope QML context and move wheel enable/reset policy out of `DeviceActionHandler` into a feature-root `wheelActions` model.
**Issues**: `PageWheel.qml` and `DeviceControlTab.qml` called `deviceActionHandler.requestWheelEnabled`, `deviceActionHandler.toggleWheelEnable`, and `deviceActionHandler.resetWheelPosition`. `CapabilityCatalog` authorities pointed to `deviceActionHandler`. `wheelController` was still exposed as a root context property even though QML only read `wheelStatus`. These kept the wheel family tied to handler-shaped globals and raw controller exposure.
**Tried**: Created `WheelActions` in `python/paint_controller/models/wheel_actions.py` with QML-facing camelCase slots `setEnabled`, `toggleEnabled`, and `resetPosition`, owning admin-gate, logging, error emission, and dispatch like `WinchActions`. Updated `controller_factory.py` to instantiate `WheelActions` and removed the `wheel` dependency from `DeviceActionHandler`. Removed wheel methods from `DeviceActionHandler`. Added `wheelActions` to `ControllerBundle`. Updated `AppRuntime` to register `wheelActions` and remove `wheelController` from `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `_build_context_properties()`. Updated `CapabilityCatalog` authorities for `wheel.enable` and `wheel.reset_position` to `wheelActions.setEnabled` and `wheelActions.resetPosition`. Updated `PageWheel.qml` and `DeviceControlTab.qml` call sites. Updated smoke fakes, factory/AppRuntime tests, `test_device_actions.py`, `test_capability_catalog.py`, `test_action_legality_model.py`, and added `tests/test_wheel_actions.py`. Added `wheel_actions.py` to `pyrightconfig.json`.
**Result**: ✅ Focused band `tests/test_wheel_actions.py tests/test_device_actions.py tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_capability_catalog.py tests/test_action_legality_model.py tests/test_startup_smoke.py tests/test_qml_imports.py` green at `44 passed`; full suite green at `282 passed`; `qmllint` clean on touched QML files; pyright clean per `pyrightconfig.json`; no remaining `deviceActionHandler` wheel-method references or `wheelController` QML-context references in production code or tests.
**Files**: `python/paint_controller/models/wheel_actions.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/pages/wheel/PageWheel.qml`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`, `tests/test_controller_factory_runtime.py`, `tests/test_device_actions.py`, `tests/test_capability_catalog.py`, `tests/test_action_legality_model.py`, `tests/test_wheel_actions.py`, `pyrightconfig.json`.

---
### 2026-07-24 16:28 - Phase 1: Winch Family (`winchActions`)

**Goal**: Execute Phase 1 of `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md`: retire `winchMotionHandler` from the QML context by moving its policy into a feature-root `winchActions` model.
**Issues**: `PageWinch.qml` was the only QML consumer of `winchMotionHandler`, but the context-property contract and `CapabilityCatalog` authorities still pointed to the handler-shaped global. Keeping it would block the broader QML surface retirement program.
**Tried**: Created `WinchActions` in `python/paint_controller/models/winch_actions.py` with the same admin-gate, logging, error emission, and dispatch policy as `WinchMotionHandler`, using QML-facing camelCase slots (`moveIncrement`, `moveAbsolute`, `retractFull`, `extendOneMeter`, `emergencyStop`). Merged the handler by updating `controller_factory.py` and `ControllerBundle`, then deleted `python/paint_controller/handlers/winch_motion.py`. Replaced `winchMotionHandler` with `winchActions` in AppRuntime's expected context-property list and registration. Updated `PageWinch.qml` call sites. Updated `CapabilityCatalog` authorities and `tests/test_capability_catalog.py`. Updated smoke fakes in `tests/startup_smoke_support.py` and factory/AppRuntime tests.
**Result**: ✅ Focused band `tests/test_winch_motion_handler.py tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py tests/test_capability_catalog.py tests/test_startup_smoke.py tests/test_qml_imports.py` green at `35 passed`; full suite green at `276 passed`; `qmllint` clean; pyright clean per `pyrightconfig.json`; no remaining `winchMotionHandler` references in production code or tests.
**Files**: `python/paint_controller/models/winch_actions.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/pages/winch/PageWinch.qml`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`, `tests/test_controller_factory_runtime.py`, `tests/test_winch_motion_handler.py`, `pyrightconfig.json` (plus deletion of `python/paint_controller/handlers/winch_motion.py`).

---
### 2026-07-24 15:37 - Phase 0: QML Contract-Parity Harness And Cleanup

**Goal**: Begin executing `docs/plan/MASTER_PLAN_QML_SURFACE_RETIREMENT.md` from Phase 0: make the AppRuntime → QML context-property contract drift-visible, fix shallow QML issues, and add teardown regression coverage.
**Issues**: `_EXPECTED_CONTEXT_PROPERTY_NAMES` and `tests/startup_smoke_support._context_objects()` were out of sync (smoke fixture was missing `winchMotionHandler` and `tuningAdminHandler` while including non-contract extras `steamDeckHandler`, `windMonitor`, `heartbeatHandler`). `MainWindow.qml` used both `visible` and `visibility`. `core/CommonStyle.qml` was a forwarding duplicate of `theme/CommonStyle.qml`. `OverlayController` and `BaseTopViewService` lacked teardown regression tests.
**Tried**: Added a parity test that fails if the smoke fixture keys diverge from `_EXPECTED_CONTEXT_PROPERTY_NAMES`. Aligned the fixture by adding `FakeWinchMotionHandler`/`FakeTuningAdminHandler` and removing the non-contract extras. Removed `visible: true` from `MainWindow.qml` and retired the duplicate `core/CommonStyle.qml` singleton, repointing all `import ".../core"` imports that were only for `CommonStyle` to the equivalent `theme/` path. Added a `cleanup()` method to `OverlayController` that stops the input timer and disables model callbacks via a `_cleaned_up` guard. Added teardown regression tests for `OverlayController` and `BaseTopViewService`.
**Result**: ✅ Contract-parity test passes; focused validation band `tests/test_app_runtime_runtime.py tests/test_startup_smoke*.py tests/test_qml_imports.py tests/test_overlay_controller.py tests/test_base_top_view_service.py tests/test_steam_deck_handler.py` green at `45 passed`; full suite green at `276 passed`; `qmllint` clean on all QML files; pyright clean on touched Python files.
**Files**: `tests/test_app_runtime_runtime.py`, `tests/startup_smoke_support.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/core/CommonStyle.qml`, `python/paint_controller/qml/core/qmldir`, `python/paint_controller/ui/overlay.py`, `tests/test_overlay_controller.py`, `tests/test_base_top_view_service.py`, plus all QML files whose `CommonStyle` import path changed.

---
### 2026-07-24 15:01 - Video Overlay As Default Startup View

**Goal**: Make the fullscreen video overlay (`VideoFullscreenWorkspace`) the default view on startup instead of the multi-page navigation home page (`PageHome`).
**Issues**: The application booted into `PageHome` and required the operator to manually toggle the video overlay. Making the overlay the default touches the Python startup sequence, the QML visibility binding, and the smoke-test fixtures that stand in for `OverlayHostPolicy`.
**Tried**: A first plan proposed defaulting `OverlayHostPolicy.video_fullscreen_active` to `True`, but a peer review showed this would turn a reusable state-owner into a startup-decision footgun and break tests that instantiate a clean policy. Kept the policy default inactive and instead added an explicit `_activate_default_video_overlay()` step in `AppRuntime._bootstrap` after controller-bundle creation. Extracted `_video_source_for_control_mode()` in `QtBridge` so the control-mode → video-source mapping is not duplicated a third time. Tied `VideoFullscreenWorkspace.active` in `MainWindow.qml` to `selectedPageKey === "home"` so page navigation remains usable underneath the overlay. Added a `FakeOverlayHost` test double because the existing `DynamicObject` properties with underscores were not readable from QML, which made the new default-overlay smoke test fail; the fake implements the same property names and slots as the real `OverlayHostPolicy`. Added regression tests verifying the overlay is active by default and hides when navigating away.
**Result**: ✅ The video overlay is now active on startup with the correct source for the current control mode. Navigation to other pages hides the overlay; returning to home restores it. Full suite green at `273 passed`; pyright clean on touched Python files.
**Files**: `python/paint_controller/core/qt_bridge.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `tests/startup_smoke_support.py`, `tests/test_startup_smoke_shell.py`

### 2026-07-24 12:00 - ControlInfoPanel Touch Feedback And Compact Mode Labels

**Goal**: Add visual feedback when touching the fullscreen-video `ControlInfoPanel` and joystick menu, and stop long control-mode names like `"Track Control Right"` from eliding in the small panel.
**Issues**: Touch-selecting a joystick menu item closed the menu with no visible highlight; touching an info panel to open the menu had no pressed state; the mode label elided long names because the panel width is only 200 px.
**Tried**: A first plan proposed adding a new `OverlayController.set_temporary_index` slot so the menu highlight followed the finger, but a peer review showed this would widen the QML/Python boundary and could commit a selection if the user pressed then cancelled. Kept all touch feedback inside QML using `MouseArea.pressed` overlays. Owned the compact labels in Python by adding a `JoystickSelectionModel.display_name_for_option` mapping and threading `left_control_mode_display` / `right_control_mode_display` through `ControlProcessor` and `_VideoRuntimeControls` to a new `controlModeDisplay` property in `ControlInfoPanel.qml`. Added a delegate pressed highlight in `JoystickOverlay.qml`, a focused-border pressed overlay in `ControlInfoPanel.qml`, and regression tests for the mapping and processor properties. On review the highlights were still too brief to notice, so both the delegate and the panel now keep the pressed state visible for 150 ms after release; the panel also got a default thin border so it looks like a tappable card. Further feedback that the border was too thin over video led to a brighter `accentPrimary` pressed overlay at 0.45–0.5 opacity with a 3 px focused border. Also fixed the legacy joystick-menu scrollbar thumb alignment by converting it to a proportional thumb positioned relative to the ListView viewport.
**Result**: ✅ Touch-down on a panel or menu item now shows immediate visual feedback; long mode names render as compact labels (e.g., `"Track Right"`, `"Yaw"`); full names remain in the selection menu. Touched validation band green at `74 passed`; full suite green at `271 passed`; pyright clean on touched Python files.
**Files**: `python/paint_controller/models/joystick_selection.py`, `python/paint_controller/handlers/control_processor.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/overlays/video/components/ControlInfoPanel.qml`, `python/paint_controller/qml/features/video/VideoFullscreenWorkspace.qml`, `python/paint_controller/qml/overlays/JoystickOverlay.qml`, `tests/startup_smoke_support.py`, `tests/test_joystick_selection.py`, `tests/test_control_processor.py`, `tests/fakes.py`

### 2026-07-23 18:08 - Touch Joystick Control Selection And ControlInfoPanel Default Text

**Goal**: Fix the default `ControlInfoPanel` mode text showing `JoystickControl...`, and add touchscreen control of joystick mode selection in fullscreen video.
**Issues**: `ControlProcessor` initialized `_left_control_mode` / `_right_control_mode` with the `JoystickControl.NONE` enum member; `str(enum_member)` returns the member name (`JoystickControl.NONE`), which QML elided to `JoystickControl...`. Joystick mode selection was only reachable via physical buttons (L4/R4 and D-pad), not touch.
**Tried**: Initialized the control-mode fields to the plain string `"None"`. Added `select_left_control` / `select_right_control` to `JoystickSelectionModel` so selection rules live with the model. Added `open_menu` and `select_index` slots to `OverlayController`, keeping it as a visibility/button coordinator while delegating direct selection to the model. Added a `panelClicked` signal + `MouseArea` to `ControlInfoPanel.qml`, wired it in `VideoFullscreenWorkspace.qml` to open the matching side menu, and added a scrim-dismiss tap in `JoystickOverlay.qml`. On-device touch tests still showed the overlay dismissing on any tap: the `ScrollView`-wrapped `ListView` created a nested flickable and the delegate handler never consumed the press, so every touch fell through to the scrim. Removed the redundant `ScrollView` so the `ListView` is the single flickable, switched the delegate back to a plain `MouseArea` with `onClicked`, hardened the menu-background blocker to consume both `onPressed` and `onClicked`, and added explicit `z` values so the menus sit unambiguously above the scrim. Touch selection then reached Python but the `ControlInfoPanel` still showed `"None"` because `select_index` committed directly while `hide_menu()` unconditionally committed the temporary index, which had been initialized to the old value and therefore overwrote the new selection. Added `JoystickSelectionModel.set_temporary_index()` and changed `OverlayController.select_index()` to set the temporary index and let `hide_menu()` commit it through the same path as button navigation. Updated the startup-smoke fake `OverlayController` and added regression tests.
**Result**: ✅ `ControlInfoPanel` now defaults to `"None"`. Tapping either info panel opens the corresponding joystick menu; tapping a menu item selects, commits, and closes the menu; flick scrolling still works; taps on the menu chrome or scrim dismiss the menu without changing the selection. Full suite green at `269 passed`.
**Files**: `python/paint_controller/handlers/control_processor.py`, `python/paint_controller/models/joystick_selection.py`, `python/paint_controller/ui/overlay.py`, `python/paint_controller/qml/overlays/video/components/ControlInfoPanel.qml`, `python/paint_controller/qml/features/video/VideoFullscreenWorkspace.qml`, `python/paint_controller/qml/overlays/JoystickOverlay.qml`, `tests/startup_smoke_support.py`, `tests/test_joystick_selection.py`, `tests/test_overlay_controller.py`

### 2026-07-23 17:33 - VideoOverlayTopBar Connection State And Tap-To-Switch

**Goal**: Give the fullscreen video top bar a clearer EF/Base connection indicator and let the operator tap the EF or Base side to switch overlays.
**Issues**: The existing top bar only showed ping/"Net OK", which did not clearly communicate disconnection, and there was no way to switch between EF and Base overlays from inside fullscreen video.
**Tried**: Added `endEffectorConnected`/`baseConnected` properties to `_VideoRuntimeTopBar` driven by `ssh_controller.deviceAvailability`, added `requestEndEffectorVideo()`/`requestBaseVideo()` slots that route through `AppRuntime._wire_signals` to `OverlayHostPolicy.set_video_fullscreen_source()`, rewired `VideoOverlayTopBar.qml` to show a colored connection dot, replace "Net OK" with "DISC" when ping is absent, highlight the selected side with a background tint + accent bottom border, and added `MouseArea` tap targets. Updated overlay components to pass `selectedOverlay` and extended the smoke-test fake top-bar model.
**Result**: ✅ EF/Base connection state is now visible at a glance, the side panels are tappable, selection is visually indicated, and the full test suite is green at `263 passed`.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/overlays/video/components/VideoOverlayTopBar.qml`, `python/paint_controller/qml/overlays/video/components/EndEffectorOverlay.qml`, `python/paint_controller/qml/overlays/video/components/BaseFrontOverlay.qml`, `tests/startup_smoke_support.py`, `tests/test_app_runtime_runtime.py`

### 2026-04-27 22:58 - Workstream E1 Launcher SSH-Admin Contract Reduction

**Goal**: Continue Workstream E1 by retiring the last live raw `sshHandler` QML dependency without widening the slice into SSH worker/timer internals, PageHome video preview, or explicit domain telemetry remainder.
**Issues**: `PageLauncher.qml` was the only remaining QML consumer of `sshHandler`, still calling raw config load/save and device command methods directly from the root context bag. The first focused validation failure was local: the new bounded wrapper used `@Slot`, but `app_runtime.py` had not imported `Slot` yet.
**Tried**: Added a narrow `launcherAdmin` QObject in `AppRuntime` that wraps only Launcher config load/save and command dispatch over `UISSHController`, threaded that contract explicitly through `MainWindow.qml` into `PageLauncher.qml`, replaced the remaining raw QML method calls, removed `sshHandler` from the root QML context contract, extended the runtime seam recorder/assertions, updated the Launcher startup harness to pass the new required contract, fixed the missing `Slot` import, and reran the focused runtime/startup/import band.
**Result**: ✅ The bounded Launcher SSH-admin slice is landed. `PageLauncher.qml` no longer reads raw `sshHandler`, the root QML context no longer exposes `sshHandler`, the shell/connectivity family is complete for the tracked shell/home/launcher seams, and the focused validation band is green at `28 passed` for `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/pages/home/PageLauncher.qml`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `PLANNING.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `DEVNOTES.md`

### 2026-04-27 22:45 - Workstream E1 PageLauncher Read-Side Shell Status Reduction

**Goal**: Continue Workstream E1 by retiring the remaining read-side Launcher LED seam without widening the slice into Launcher SSH config/command behavior or PageHome video preview.
**Issues**: `PageLauncher.qml` still read raw `sshHandler.deviceAvailability` for the BASE and END_EFFECTOR LED indicators even though the same reachability state already lived in the bounded `shellConnectivityStatus` contract. The first focused smoke rerun was green but ambiguous because the existing startup harness did not instantiate `PageLauncher.qml` directly after the new required property was added.
**Tried**: Threaded `shellConnectivityStatus` explicitly into `PageLauncher.qml` from `MainWindow.qml`, rebound only the two Launcher LED colors to `baseReachable` and `endEffectorReachable`, left SSH config load/save plus command dispatch on `sshHandler`, added a focused Launcher instantiation smoke harness, and reran the touched startup/import band.
**Result**: ✅ The bounded Launcher read-side shell status slice is landed. `PageLauncher.qml` no longer reads raw `sshHandler.deviceAvailability`, the remaining Launcher SSH config and command surface stays intentionally separate, and the focused validation band is green at `21 passed` for `tests/test_startup_smoke.py` plus `tests/test_qml_imports.py`.
**Files**: `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/pages/home/PageLauncher.qml`, `tests/test_startup_smoke.py`, `PLANNING.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `DEVNOTES.md`

### 2026-04-27 22:32 - Workstream E1 PageHome Shell Telemetry Contract Reduction

**Goal**: Continue Workstream E1 by retiring the PageHome status-card and footer shell telemetry seam without widening the slice into Launcher SSH-admin behavior or PageHome video preview.
**Issues**: `PageHome.qml` still mixed direct `sshHandler.deviceAvailability` and `heartbeatHandler` reads in both video-status headers and the bottom status bar, so the shell/home surface still depended on the root context bag even after the shared shell chrome moved behind `shellConnectivityStatus`. The local implementation defect was narrow: the runtime seam test recorder did not expose `deviceAvailability`, so the new bounded reachability fields initially validated as false even though the runtime contract itself was correct.
**Tried**: Extended `shellConnectivityStatus` with bounded SSH reachability fields, threaded that contract explicitly into `PageHome.qml` from `MainWindow.qml`, rewired the touched PageHome status headers and footer to the bounded shell model, removed `heartbeatHandler` from the AppRuntime QML context surface because this slice retired its last live QML consumer, fixed the local SSH recorder gap in the runtime seam test, reran the focused runtime/startup band, then reran QML import smoke.
**Result**: ✅ The bounded PageHome shell telemetry slice is landed. `PageHome.qml` no longer reads `heartbeatHandler` or raw SSH availability directly for the touched header/footer surface, `heartbeatHandler` is removed from the root QML contract, the focused validation band is green at `26 passed` for `tests/test_controller_factory_runtime.py` plus `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py` is green at `1 passed`. The remaining Launcher command/config and LED surface plus PageHome video preview remain explicit later concern rather than being widened into this slice.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/pages/home/PageHome.qml`, `tests/test_controller_factory_runtime.py`, `PLANNING.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `DEVNOTES.md`

### 2026-04-27 16:35 - Workstream E1 Shell/Connectivity Panel Contract Reduction

**Goal**: Start the shell/connectivity telemetry family by retiring the shared `ConnectionStatusPanel.qml` ambient read seam without widening launcher commands/config editing, home video preview, or the already-landed device/status models.
**Issues**: `ConnectionStatusPanel.qml` still mixed direct `winchController`, `teensyController`, `heartbeatHandler`, and `wheelStatus` reads with an undeclared `uiData` IP fallback, so the shared shell chrome still depended on a broad app-scope context bag. The only local execution defect was in the startup smoke harness: the inline QML object literal for the new shell model needed exact escaped braces inside the Python f-string before the `SelectBar` harness would instantiate.
**Tried**: Added a bounded `shellConnectivityStatus` QObject in `AppRuntime`, sourced the panel IP strings from the existing SSH config API instead of the ghost `uiData` fallback, rewired `ConnectionStatusPanel.qml`, `SelectBar.qml`, and `MainWindow.qml` to that contract, extended the direct runtime seam test, updated the startup context bundle and `SelectBar` harness, fixed the local f-string brace defect, and reran the focused runtime/shell startup validation band.
**Result**: ✅ The first shell/connectivity slice is landed. The shared shell `ConnectionStatusPanel.qml` surface now consumes bounded `shellConnectivityStatus` instead of direct `winchController`, `teensyController`, `heartbeatHandler`, `wheelStatus`, or `uiData` reads, and the focused validation band is green at `6 passed` across the touched runtime plus shell startup checks. The next bounded shell/connectivity follow-up is the `PageHome.qml` status-header slice, while launcher commands/config editing and home video preview remain explicit remainder.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/navigation/ConnectionStatusPanel.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `python/paint_controller/qml/core/MainWindow.qml`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-27 16:05 - Workstream E1 Teensy Feature-Toggle Status Contract Reduction

**Goal**: Continue Workstream E1 by retiring the shared teensy feature-toggle read seam from the system-control stabilization and LED block without widening the earlier teensy power/header slice into a generic controller mirror.
**Issues**: `DeviceControlTab.qml` still mixed direct `teensyController` reads for stability, yaw, auto-correction, leveling, roller steering, swing damping, and spray-gun LED state even though the write side already flowed through `deviceOperationsHandler`. The first broader startup rerun also exposed one local harness gap because `SystemControlWorkspace` smoke coverage was still passing only a partial required-model set after the shared system-control boundary tightened.
**Tried**: Extended the bounded `teensyStatus` QObject in `AppRuntime` with only the shared feature-toggle fields this slice needed, kept `yawEnabled` derived from bounded status state instead of exposing raw `all_status`, rewired the touched `DeviceControlTab.qml` controls to those bounded fields while preserving the existing handler-owned write calls, updated the runtime seam test and the `DeviceControlTab` startup smoke harness, fixed the `SystemControlWorkspace` smoke harness to pass the full bounded status model set, and reran the focused runtime/startup validation band.
**Result**: ✅ The teensy feature-toggle slice is landed. The shared system-control teensy toggle surface now consumes bounded `teensyStatus` fields instead of raw ambient `teensyController` toggle reads, the focused validation band is green at `5 passed` across the touched runtime and startup smoke checks, and a direct search confirms the shared `DeviceControlTab.qml` surface no longer reads those raw teensy toggle fields. The next named Workstream E family is shell/connectivity telemetry.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-27 15:40 - Workstream E1 Recording-Status Contract Reduction

**Goal**: Continue Workstream E1 by retiring the mixed recording-status read seam from the shared system-control recording block without reopening the already-bounded fullscreen top-bar path.
**Issues**: The real remaining recording debt was narrower than the roadmap shorthand implied: `DeviceControlTab.qml` still mixed direct `baseStreamHandler`, `screenRecorder`, and `rosBagRecorder` reads with handler-owned recording intents. The implementation also hit one local harness issue because the `DeviceControlTab` smoke test needed deterministic inline models for the new required props rather than relying on the ad hoc timing of test context wiring.
**Tried**: Added a bounded `recordingStatus` QObject in `AppRuntime`, threaded it through the live system-control roots, rewired the touched recording block in `DeviceControlTab.qml` to consume that contract, left `videoRuntime.topBar` unchanged, extended the runtime seam test, and stabilized the startup smoke harness with explicit inline models for the required recording/status props before rerunning the focused runtime and QML validation band.
**Result**: ✅ The recording-status slice is landed. The touched system-control recording surface now consumes `recordingStatus` instead of direct ambient `baseStreamHandler`, `screenRecorder`, and `rosBagRecorder` reads, the fullscreen top bar remains correctly owned by `videoRuntime.topBar`, and the focused validation band is green at `6 passed` across the touched runtime and startup smoke checks. The next bounded device/status follow-up is teensy feature-toggle status, then the named shell/connectivity telemetry family.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-27 15:05 - Workstream E1 Wheel Shared Summary/Control Contract Reduction

**Goal**: Continue Workstream E1 by retiring the shared wheel summary/control read path from the touched system-control, status, monitor, and shell-status surfaces without widening the wheel seam into a controller-shaped global bag.
**Issues**: The approved wheel slice had one local execution failure before landing because the first large multi-file patch drifted from the live `MainWindow.qml` and `SelectBar.qml` call-site context. The real architecture risk stayed the same: shared wheel status and enable intent still depended on direct `wheelController` reads across bounded surfaces, while `PageWheel.qml` and fullscreen/base-front telemetry needed to stay explicit remainder instead of being swept into the first slice.
**Tried**: Added a bounded `wheelStatus` QObject in `AppRuntime`, rewired the touched shared consumers to accept and pass that contract explicitly, left the detailed wheel and fullscreen telemetry callers untouched, expanded the runtime seam test plus startup smoke fixtures/harnesses, then reran a focused pytest band covering the runtime contract plus the touched `MainWindow`, `MultiScreenListUI`, `PageStatus`, and `DeviceControlTab` paths.
**Result**: ✅ The wheel shared summary/control slice is landed. The touched shared QML surfaces now consume `wheelStatus` instead of direct ambient `wheelController` reads, the wheel detail/fullscreen remainder stays explicitly outside this checkpoint, and the focused validation band is green at `8 passed` for `tests/test_controller_factory_runtime.py` and `tests/test_startup_smoke.py`. The next bounded device/status follow-up is recording status, then teensy feature-toggle status, before the named shell/connectivity telemetry family.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/pages/status/PageStatus.qml`, `python/paint_controller/qml/pages/status/PageMonitor.qml`, `python/paint_controller/qml/pages/status/components/WheelsCard.qml`, `python/paint_controller/qml/pages/status/components/WheelStatus.qml`, `python/paint_controller/qml/navigation/ConnectionStatusPanel.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-27 14:15 - Workstream E Roadmap Tightening

**Goal**: Continue the architecture plan by tightening the Workstream E execution model before more implementation slices land.
**Issues**: The roadmap direction was still correct, but the docs were too loose in three ways: video/runtime was described as complete even though direct fullscreen telemetry reads remain, device/status had no hard proof rules for sub-slice completion, and shell/home/launcher connectivity debt was still effectively untracked residual context-bag exposure.
**Tried**: Re-audited the live QML/runtime callers, updated the roadmap and progress tracker to use explicit family states plus retirement-ledger rules, named shell/connectivity telemetry as a downstream family, and made the next concrete implementation slice explicit as wheel shared summary/control rather than another generic device/status sub-slice.
**Result**: ✅ Workstream E keeps the same ownership-first direction, but the execution framework is now tighter: video/runtime is partial retirement with explicit remainder, future slices must record before/after consumer proof plus AppRuntime deltas, the next bounded slice is wheel shared summary/control, and shell/connectivity telemetry is now a tracked future family before opportunistic settings cleanup.
**Files**: `PLANNING.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-27 13:24 - SSH Teardown Crash Fix

**Goal**: Eliminate the late full-suite segmentation fault that appeared after the overlay-warning work and return `python/paint_controller/venv/bin/python -m pytest tests -q` to green.
**Issues**: The crash reproduced only near suite shutdown, with `QObject::killTimer` cross-thread warnings and several threads still blocked inside `python/paint_controller/controllers/ssh.py`. The local fault line was `UISSHController`: it owned `QTimer` polling, used the global `QThreadPool` for ping checks, and `tests/test_ssh.py` instantiated live controllers without explicit cleanup, so timers and worker callbacks could outlive the controller QObject during teardown.
**Tried**: Switched `UISSHController` to a dedicated `QThreadPool`, changed availability and command callbacks to use `weakref` instead of capturing the controller strongly, made cleanup idempotent, disconnected result handlers defensively, stopped and disconnected availability timers before clearing them, waited for the dedicated worker pool to finish, and added a focused cleanup-order regression test. Also added explicit `controller.cleanup()` teardown in the direct SSH tests so they no longer leak live timer/worker state across the suite.
**Result**: ✅ The late SSH teardown crash is fixed. `tests/test_ssh.py` passes at `4 passed`, and the full suite is green at `252 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. The prior `QObject::killTimer` warnings and exit-code `139` failure did not recur.
**Files**: `python/paint_controller/controllers/ssh.py`, `tests/test_ssh.py`, `DEVNOTES.md`

### 2026-04-27 13:05 - Fullscreen Overlay Warning Hardening

**Goal**: Remove the remaining live fullscreen overlay warnings after the post-commit startup regression repair and make the smoke tests fail on those warning classes.
**Issues**: The real app still emitted fullscreen warnings that the focused tests missed: `WorkFlowRunner::workflow_runtime` was non-bindable, the video overlay compatibility shim was missing style properties, `EndEffectorOverlay.qml` and `BaseFrontOverlay.qml` used anchored children inside `Row`, startup reads assumed controllers/status bags were always populated, `WallDetectionOverlay.qml` still used the deprecated `Connections` syntax, and the fullscreen smoke fixture did not match the base-top-view/image-provider contract closely enough to catch the base-front path.
**Tried**: Made `workflow_runtime` a notify-backed cached property, extended `qml/core/CommonStyle.qml` with the video helper aliases used by the overlay components, guarded startup reads in the EF/base-front overlays and workflow overlay, replaced the invalid `Row` containers with anchor-safe `Item` containers, updated the wall-detection `Connections` block and lidar fallbacks, then rebuilt `tests/test_startup_smoke.py` with a real `FakeBaseTopViewController`, `FakeLidarController`, explicit `base_top_view` provider registration, and source-specific warning assertions for EF and base-front fullscreen paths before rerunning focused tests and a live app launch.
**Result**: ✅ The targeted fullscreen warning slice is repaired. `tests/test_startup_smoke.py`, `tests/test_qml_imports.py`, and `tests/test_workflow_runner.py` are green at `26 passed`, the strengthened base-front fullscreen smoke path now fails on the warning signatures it previously missed, and a live `python/paint_controller/venv/bin/paint_controller` run no longer shows the tracked `WorkFlowStatusOverlay`, `EndEffectorOverlay`, `WallDetectionOverlay`, `VideoOverlayTopBar`, or `BaseFrontOverlay` warning classes while switching fullscreen sources. A separate full-suite run now crashes late with a Qt/threading segfault around SSH-controller activity, which appears outside this overlay slice.
**Files**: `python/paint_controller/services/workflow/workflow_runner.py`, `python/paint_controller/qml/core/CommonStyle.qml`, `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml`, `python/paint_controller/qml/overlays/video/components/EndEffectorOverlay.qml`, `python/paint_controller/qml/overlays/video/components/WallDetectionOverlay.qml`, `python/paint_controller/qml/overlays/video/components/VideoOverlayTopBar.qml`, `python/paint_controller/qml/overlays/video/components/BaseFrontOverlay.qml`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-27 12:24 - Post-Commit Runtime Regression Repair

**Goal**: Restore live `paint_controller` startup after the architecture commit by removing the QML/runtime regressions that escaped the pre-commit suite.
**Issues**: The app launched with green tests but failed at runtime because `MainWindow.qml` passed self-referential same-name bindings into the system-control and video feature roots, `AdminActionGate` re-emitted a parameterized backend signal through a zero-arg Qt signal, `WorkFlowTab.qml` referenced `workFlowRunner` even though its required property was `workflowRunner`, and the MainWindow smoke fixture was looser than the real runtime contract shape.
**Tried**: Typed the exposed nested runtime properties as `QObject` in the Python wrappers, changed signal forwarding to discard backend arguments before re-emitting, added explicit `systemControlServicesModel` and `videoRuntimeModel` aliases in `MainWindow.qml`, fixed the `WorkFlowTab.qml` property-name mismatch, tightened `tests/test_startup_smoke.py` to assert the specific regression signatures stay absent, and aligned the smoke fixture with QObject-based fake service/video runtime contracts before rerunning focused validation and a real app launch.
**Result**: ✅ The post-commit startup regression is repaired. Focused validation is green at `30 passed` for `tests/test_controller_factory_runtime.py`, `tests/test_action_legality_model.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`, and a real `python/paint_controller/venv/bin/paint_controller` startup no longer emits the original `manualCommandHandler`, `workflowRunner`, `videoRuntime.controls/feeds`, or zero-arg signal-forwarding failures. Remaining live warnings are older overlay/layout/runtime debt, not this regression.
**Files**: `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/admin_action_gate.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-26 22:48 - Workstream E1 Slice 2 Command Contract Reduction

**Goal**: Continue Workstream E1 by retiring the `manualCommandHandler` app-scope QML read path and moving the system-control command surface onto the same explicit feature-scoped contract pattern as the workflow/editor tabs.
**Issues**: After E1 slice 1, `CommandTab.qml` was still the remaining live system-control consumer of a root-context global (`manualCommandHandler`). Leaving that path in place would keep the app-scope contract wider than necessary even though the feature root already existed as the correct ownership boundary.
**Tried**: Extended `_SystemControlServices` in `AppRuntime` to carry `manualCommandHandler`, rewired `SystemControlWorkspace.qml` and `CommandTab.qml` to pass and require that service explicitly, removed `manualCommandHandler` from the root QML context-property contract after confirming there were no other live QML consumers, added a direct `CommandTab` startup-smoke harness, reran the focused E1 command/runtime smoke slice, then reran the full suite.
**Result**: ✅ Workstream E1 slice 2 is complete. The system-control command surface no longer depends on an ambient app-scope global, the root QML contract is smaller again, the focused slice is green at `3 passed`, and the full suite is green at `249 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. The next E1 slice should continue shrinking system-control or shared app-scope read families with the same contract-first rule.
**Files**: `PLANNING.md`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml`, `python/paint_controller/qml/overlays/systemcontrol/CommandTab.qml`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `DEVNOTES.md`

### 2026-04-26 22:41 - Workstream E1 Slice 1 Workflow Contract Reduction

**Goal**: Start Workstream E1 with a real app-scope contract reduction by retiring the ambient workflow/editor globals and making the touched system-control and video feature roots consume one explicit workflow-services boundary.
**Issues**: `WorkFlowTab.qml`, `EditWorkFlowTab.qml`, and `WorkFlowStatusOverlay.qml` still depended on `workFlowRunner` / `workflowEditor` as root-context globals. That kept the app-wide QML contract broader than necessary and made nested feature surfaces depend on ambient state instead of explicit ownership boundaries.
**Tried**: Added a `_SystemControlServices` contract in `AppRuntime`, replaced the two root workflow globals with one `systemControlServices` context property, rewired `SystemControlWorkspace.qml`, `VideoFullscreenWorkspace.qml`, and their wrappers to accept that contract explicitly, added required workflow inputs on the touched tabs/overlays, aligned the runtime seam test and startup smoke harnesses to the new boundary, reran the focused E1 validation band, then reran the full suite.
**Result**: ✅ The first Workstream E1 slice is complete. The touched workflow/editor surfaces no longer read ambient root globals directly, the app-scope workflow contract is reduced to one explicit service boundary, the focused E1 validation band is green, and the full suite is green at `248 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. The next E1 checkpoint should continue shrinking remaining app-scope feature contracts with the same boundary-first rule.
**Files**: `PLANNING.md`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml`, `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `python/paint_controller/qml/features/video/VideoFullscreenWorkspace.qml`, `python/paint_controller/qml/overlays/video/VideoFullscreenOverlay.qml`, `python/paint_controller/qml/overlays/video/components/EndEffectorOverlay.qml`, `python/paint_controller/qml/overlays/video/components/BaseFrontOverlay.qml`, `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-26 21:33 - Workstream D QML Contract Reduction Complete

**Goal**: Finish Workstream D by retiring the remaining settings-family raw QML read/write paths and shrinking the app-scope QML context contract where the remaining exposure was clearly unused.
**Issues**: After the first D slice, the repo still had raw settings summary reads on the Settings route pages, two inline special-case settings fields in `SettingsTab.qml`, and extra app-scope QML context exposure that no longer had direct QML consumers. The first final-suite rerun also exposed an unrelated but deterministic `WorkflowCatalog` sorting defect for equal `casefold()` names.
**Tried**: Added owner-side settings summary helpers to `SettingsManager`, rewired the Settings route pages to consume those helpers with explicit refresh on `setting_changed`, replaced the remaining inline thrust-force and thrust-ramp fields in `SettingsTab.qml` with the shared typed `SettingInputField` contract, retired `capabilityCatalog`, `steamDeckHandler`, and `windMonitor` from the QML context-property surface, added direct runtime tests for the new settings summary helpers, and fixed `WorkflowCatalog` sorting to use a deterministic tie-break during the final validation pass.
**Result**: ✅ Workstream D is complete. The settings family now consumes typed owner helpers instead of raw setting-bag semantics, unused app-scope QML context exposure is reduced, focused Workstream D validation is green at `35 passed`, and the full suite is green at `248 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. At that point, the next recommended checkpoint was Workstream E future automation seam design; that later evolved into the current contract-first Workstream E family order now tracked in the roadmap and progress docs.
**Files**: `PLANNING.md`, `python/paint_controller/core/settings.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`, `python/paint_controller/qml/pages/settings/components/ManagedSettingSpinBox.qml`, `python/paint_controller/qml/pages/settings/pages/MainSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/CameraSettingsPage.qml`, `python/paint_controller/services/workflow/workflow_catalog.py`, `tests/test_settings_runtime.py`, `tests/test_controller_factory_runtime.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `README.md`, `DEVNOTES.md`

### 2026-04-26 21:22 - Workstream D1 Settings Typed-Contract Reduction

**Goal**: Start Workstream D with the smallest real settings-family contract-retirement slice by removing raw `settingsManager` property/index save semantics from the shared settings widgets instead of adding a new runtime facade.
**Issues**: `SettingInputField.qml` and `ManagedSettingSpinBox.qml` still treated `settingsManager` as a raw property bag, so shared QML widgets owned value lookup, typed conversion, and save behavior directly. That kept the settings contract broader than necessary and made the generic settings path harder to reason about.
**Tried**: Rewired the shared settings widgets to consume `SettingsManager`'s typed `get*`, `set*`, and `apply*` slots plus `setting_changed` refresh instead of raw `settingsManager[key]` reads and writes; added direct runtime tests for the typed QML-facing slots; reran the focused settings/runtime/QML smoke band; then reran the full suite.
**Result**: ✅ The first Workstream D slice is in place. Shared settings widgets no longer own raw setting lookup and mutation semantics, the focused Workstream D validation band is green at `27 passed`, and the full suite is green at `247 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. The next recommended checkpoint is to continue Workstream D by retiring the remaining direct settings-family summary and special-field reads.
**Files**: `PLANNING.md`, `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`, `python/paint_controller/qml/pages/settings/components/ManagedSettingSpinBox.qml`, `tests/test_settings_runtime.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `README.md`, `DEVNOTES.md`

### 2026-04-26 21:14 - Workstream C Shell/Route Formalization Complete

**Goal**: Finish Workstream C by making the touched shell-family route contract key-first, retiring the duplicate int-based route request path, and validating that the shell behavior stays green before moving on to broader contract reduction.
**Issues**: After the C0 test slice, the real shell still navigated by `pageIndex`, `MainWindow.qml` and `SelectBar.qml` still duplicated route lookup logic, and the sparse numeric page registry still carried more semantic weight than intended. The work had to avoid widening `ShellState`, `QtBridge`, or the AppRuntime context-property contract.
**Tried**: Reworked `MainWindow.qml` so route lookup resolves by `buttonKey`, demoted numeric route order to internal-only `routeOrder` metadata for StackView transitions, rewired `SelectBar.qml` to emit key-based navigation requests and removed its local route lookup duplication, updated the startup smoke harnesses to drive route changes by key and assert the internal ordering remains stable, reran the focused shell/import validation band, then reran the full pytest suite to confirm the whole repo stayed green.
**Result**: ✅ Workstream C is complete for the touched shell family. `pageKey` is now the canonical top-level route identity, `SelectBar.qml` no longer carries a second route lookup path, the focused shell/import validation band is green at `17 passed`, and the full suite is green at `245 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. The next recommended checkpoint is Workstream D dedicated QML-contract reduction.
**Files**: `PLANNING.md`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `README.md`, `DEVNOTES.md`

### 2026-04-26 21:08 - Workstream C0 Route Contract Tests

**Goal**: Start Workstream C with a test-first slice that proves the real shell route owner before any route-identity refactor lands.
**Issues**: The shell still keeps both `selectedPageIndex` and `selectedPageKey`, `MainWindow.qml` and `SelectBar.qml` still duplicate route lookup behavior, and the existing smoke coverage proved the SelectBar harness more directly than the real MainWindow route contract.
**Tried**: Added focused startup-smoke harnesses that instantiate the real `MainWindow` type with the existing fake context bundle, drive route changes through `navigateToPage(...)`, assert that route selection is reflected through `selectedPageKey` plus the shell `stackView`, and assert that an invalid route request leaves the previous route intact. Revalidated first with the narrow route-only slice, then with the broader shell/import validation band.
**Result**: ✅ Workstream C0 is in place. The repo now has direct smoke coverage for MainWindow-owned route transitions and invalid-route no-op behavior, the focused route slice passed at `3 passed`, and the broader shell/import band is green at `17 passed` for `tests/test_startup_smoke.py` plus `tests/test_qml_imports.py`.
**Files**: `PLANNING.md`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-26 20:16 - Workstream B2 Operator-Action Legality Complete

**Goal**: Finish Workstream B by making pre-click operator affordance state consume the same legality seam as backend enforcement instead of leaving legality visible only after a rejected click.
**Issues**: `AdminActionGate` already enforced legality in Python handlers, but QML still decided `enabled` locally on the touched surfaces. `DeviceControlTab.qml` exposed blocked device actions as clickable controls until handlers rejected them, and `BaseTopViewSettingsPopup.qml` still relied on optimistic interaction with rollback on failure. That left two operator contracts for the same action.
**Tried**: Added `ActionLegalityModel` as the QML-facing legality seam over `AdminActionGate` plus `CapabilityCatalog`, registered it as `actionLegality`, rewired `ControlPanel.qml` and `ActionButton.qml` to render blocked reasons before click, wired the gated `DeviceControlTab.qml` controls to that seam, wired `BaseTopViewSettingsPopup.qml` live-adjustment/save/reset affordances to the same legality contract, extended overlay surface metadata in `CapabilityCatalog`, added direct legality model tests, extended startup smoke with legality-aware component harnesses, and reran the adjacent handler/runtime/smoke validation band.
**Result**: ✅ Workstream B is complete for the touched overlay families. Handler enforcement and QML affordance state now share one legality seam, blocked overlay actions are explained before click on the touched surfaces, focused B2 validation is green at `39 passed`, and Workstream C shell/route formalization is now the next recommended checkpoint.
**Files**: `PLANNING.md`, `python/paint_controller/models/action_legality_model.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/overlays/systemcontrol/components/ActionButton.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/ControlPanel.qml`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/overlays/video/components/BaseTopViewSettingsPopup.qml`, `tests/test_action_legality_model.py`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `README.md`, `DEVNOTES.md`

### 2026-04-26 20:03 - Workstream B1 Overlay Host And Layer Matrix Complete

**Goal**: Finish the first Workstream B checkpoint by making overlay host placement and precedence explicit before operator-action legality work begins.
**Issues**: Overlay host behavior was split across `MainWindow.qml`, `MultiScreenListUI.qml`, `ShellState`, `QtBridge`, and `OverlayController`. System control, joystick overlays, fullscreen video, and emergency overlays still depended on ad hoc `visible` and `z` rules in root QML, so host topology was not represented by one canonical owner.
**Tried**: Added a narrow `OverlayHostPolicy` model to own the touched host/layer matrix and fullscreen-video state, wired it into `AppRuntime` as a context property, kept `ShellState` narrow for screen-role policy and `OverlayController` narrow for menu-session state, rewired `MainWindow.qml` and `MultiScreenListUI.qml` to consume the host policy declaratively, added the missing secondary-surface joystick/video/emergency host instances, and validated the touched Python/QML seams with focused tests.
**Result**: ✅ Workstream B1 is complete. The touched overlay surfaces now consume one Python-owned host policy, fullscreen-video state no longer lives only as a local QML toggle, focused Workstream B1 validation is green at `40 passed`, and the next recommended checkpoint is Workstream B2 operator-action legality.
**Files**: `PLANNING.md`, `python/paint_controller/models/overlay_host_policy.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `tests/test_overlay_host_policy.py`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `README.md`, `DEVNOTES.md`

### 2026-04-26 19:50 - Commit-Prep Documentation Truth Pass Before Workstream B

**Goal**: Scan the current-facing markdown set after Workstream A completion and make sure the repo is commit-ready before Workstream B begins.
**Issues**: The live control-plane docs were mostly aligned already, but the active roadmap still had one leftover “next implementation slice” block written as if workflow stabilization were still next, the session-order tail had duplicate workstream ordering, and the active debt summary still described workflow cleanup as remaining active debt. Older DEVNOTES entries also still contained next-step references that were accurate at the time but could read as current guidance during a quick scan.
**Tried**: Audited the current-facing markdown set, updated the active roadmap and debt tracker to point cleanly at Workstream B1, removed the duplicated session-order tail, rewrote the next-slice block around overlay host/layer matrix work, and clarified the two older DEVNOTES next-step references as historical context rather than live guidance.
**Result**: ✅ The current-facing docs now consistently point at Workstream B1 overlay host and layer matrix, workflow cleanup is no longer described as remaining active debt, and the remaining older next-step references are clearly marked as historical. The repo is doc-ready for a commit-prep pass before Workstream B implementation starts.
**Files**: `PLANNING.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-26 19:29 - Workstream A Workflow Runtime And Editor Stabilization Complete

**Goal**: Finish Workstream A by stabilizing the workflow runtime read contract, hardening workflow persistence, and making editor/runtime collision behavior explicit before overlay-host and legality work begins.
**Issues**: The root workflow defect was deeper than QML bindings alone: `WorkFlowExecutor` published schedule-order indices instead of workflow-document indices, QML rebuilt action state ad hoc through `get_current_workflow_actions()`, workflow ordering inherited raw directory iteration, workflow saves were non-atomic and weakly validated, and save/delete behavior while a workflow was loaded or executing was not explicit enough for a long-lived operator feature.
**Tried**: Fixed `WorkFlowExecutor` to publish canonical workflow-order action indices, including position-triggered actions; added a cached declarative read model plus notify-driven runtime/progress fields to `WorkFlowRunner`; rewired `WorkFlowTab.qml` and `WorkFlowStatusOverlay.qml` to that contract; made `WorkflowCatalog` ordering stable; added normalized atomic saves plus runtime collision rules to `WorkflowEditor`; attached the editor to the runtime boundary in `controller_factory.py`; expanded workflow runner/editor/executor tests; added focused smoke harnesses for the workflow QML surfaces; and reran both the focused workflow slice and the full suite.
**Result**: ✅ Workstream A is complete. The live workflow surfaces now consume one Python-owned runtime contract, workflow persistence semantics are stable and explicit, focused workflow validation is green at `40 passed`, and the full suite is green at `233 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. The next recommended checkpoint is Workstream B1 overlay host and layer matrix.
**Files**: `PLANNING.md`, `python/paint_controller/services/workflow/workflow_catalog.py`, `python/paint_controller/services/workflow/workflow_runner.py`, `python/paint_controller/services/workflow/workflow_editor.py`, `python/paint_controller/services/workflow/workflow_executor.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/qml/overlays/systemcontrol/WorkFlowTab.qml`, `python/paint_controller/qml/overlays/video/components/WorkFlowStatusOverlay.qml`, `tests/test_workflow_runner.py`, `tests/test_workflow_editor.py`, `tests/test_workflow_executor.py`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `DEVNOTES.md`

### 2026-04-26 19:09 - Roadmap Realignment To Workstreams + Immediate Contract Retirement

**Goal**: Re-check the architecture plan from first principles against the real outcome target: a more professional Qt program that is easier to maintain, scale, and understand.
**Issues**: The roadmap direction was broadly correct, but the live docs still treated contract narrowing as too late and left contradictory future-language across the debt plan, progress tracker, debt tracker, and repo entry docs. That risked rearranging complexity instead of reducing it.
**Tried**: Ran adversarial pre-mortem and architecture-challenge reviews, cross-checked the strongest findings against the actual roadmap and runtime/QML files, kept the workstream framework, then rewrote the live planning docs so the unfinished tail now has one explicit north star and an immediate retirement rule for superseded QML read paths.
**Result**: ✅ At that point, the validated roadmap preserved completed stages as history, governed unfinished work through active workstreams, made Workstream A1 workflow public read-model stabilization the next checkpoint, and required touched slices to retire old read paths instead of leaving two equal contracts alive.
**Files**: `PLANNING.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/tech-debt.md`, `INDEX.md`, `DEVNOTES.md`

### 2026-04-26 18:05 - Stage 4.5 Direct-Admin Boundaries Complete

**Goal**: Finish Stage 4.5 by removing the remaining raw admin/calibration QML mutators, making default runtime gating explicit in Python, and leaving later legality work with a real enforcement seam instead of metadata-only inventory.
**Issues**: After the first Stage 4.5 status slice, raw QML mutations still remained on `PageWheel.qml`, parts of `PageWinch.qml`, `PageTuning.qml`, and `BaseTopViewSettingsPopup.qml`. The repo also had no explicit Python-owned owner for maintenance-versus-live action gating, so simply adding more handlers without a shared policy seam would still leave legality scattered across UI surfaces.
**Tried**: Added a thin `AdminActionGate`; extended `DeviceActionHandler` and `DeviceOperationsHandler`; added dedicated `WinchMotionHandler`, `TuningAdminHandler`, and `BaseTopViewAdminHandler`; rewired the remaining wheel/winch/tuning/base-top surfaces to those boundaries; aligned `CapabilityCatalog` to the new authorities; validated each family incrementally; reran the combined Stage 4.5 slice; then reran the full suite.
**Result**: ✅ Stage 4.5 is complete. The tracked status, wheel, winch, tuning, and base-top calibration surfaces no longer call raw controller or service mutators from QML, default gating is explicit in Python through `AdminActionGate`, focused Stage 4.5 validation is green at `40 passed`, and the full suite is green at `224 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. At that point, the next recommended slice was Stage 6A current workflow public-model stabilization.
**Files**: `PLANNING.md`, `python/paint_controller/models/admin_action_gate.py`, `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/handlers/device_operations.py`, `python/paint_controller/handlers/winch_motion.py`, `python/paint_controller/handlers/tuning_admin.py`, `python/paint_controller/handlers/base_top_view_admin.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/pages/wheel/PageWheel.qml`, `python/paint_controller/qml/pages/winch/PageWinch.qml`, `python/paint_controller/qml/pages/tuning/PageTuning.qml`, `python/paint_controller/qml/overlays/video/components/BaseTopViewSettingsPopup.qml`, `tests/test_device_actions.py`, `tests/test_device_operations.py`, `tests/test_winch_motion_handler.py`, `tests/test_tuning_admin_handler.py`, `tests/test_base_top_view_admin_handler.py`, `tests/test_controller_factory_runtime.py`, `tests/test_capability_catalog.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `DEVNOTES.md`

### 2026-04-26 17:05 - Stage 4.5A Status/Winch Admin Boundary Slice

**Goal**: Start Stage 4.5 with the smallest coherent direct-admin surface family by moving the live enable/relay toggles on the Status and Winch pages behind an existing Python-owned boundary.
**Issues**: `PageStatus.qml`, `TeensyStatus.qml`, and the winch power toggle in `PageWinch.qml` still called raw controller mutators directly. The repo already had a `DeviceActionHandler`, but its status-toggle API was expressed as invert-current helpers for the system-control overlay rather than as explicit desired-state requests for page-level surfaces.
**Tried**: Extended `DeviceActionHandler` with explicit `request*Enabled(...)` slots while preserving the older toggle API, rewired the status/winch surfaces to those new request slots, added local UI rollback on rejected `TouchSwitch` actions, added focused handler coverage for the explicit request path, and reran the focused Stage 4.5A validation slice.
**Result**: ✅ The first Stage 4.5 slice is in place. Status and winch enable/relay toggles no longer call raw controller mutators directly, the boundary stays narrow by reusing the existing handler instead of creating a new admin framework, and focused validation is green at `15 passed` for `tests/test_device_actions.py`, `tests/test_startup_smoke.py`, and `tests/test_qml_imports.py`. Remaining Stage 4.5 work is now concentrated on tuning, base-top calibration, overlay-settings, and explicit default gating policy.
**Files**: `PLANNING.md`, `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/qml/pages/status/PageStatus.qml`, `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`, `python/paint_controller/qml/pages/winch/PageWinch.qml`, `tests/test_device_actions.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `DEVNOTES.md`

### 2026-04-26 16:45 - Stage 3B1 Route Normalization Complete

**Goal**: Finish the first shell implementation slice by removing the split route catalog and split selected-route ownership between `MainWindow.qml` and `SelectBar.qml` without widening `ShellState`.
**Issues**: The route manifest lived in `MainWindow.qml`, but `SelectBar.qml` still hard-coded a second route catalog and owned local selected-route state. That kept shell navigation harder to reason about and made the selected-route write path ambiguous. The first focused validation also exposed a local syntax error in the updated smoke harness.
**Tried**: Made `MainWindow.qml` the canonical owner of route manifest data and selected-route writes, rewired `SelectBar.qml` into a manifest-driven presenter/requester over that shared route source, extended the focused SelectBar smoke harness to verify manifest-driven navigation and selection sync, fixed the local test indentation defect revealed by the first rerun, then reran the focused Stage 3B1 shell/import slice.
**Result**: ✅ Stage 3B1 is complete. Route ownership is now canonical in the shell, the hard-coded sidebar route catalog is gone, focused validation is green at `2 passed` for `tests/test_startup_smoke.py::test_select_bar_navigates_via_explicit_page_registry` plus `tests/test_qml_imports.py`, and the next recommended slice is the new Stage 4.5 direct-admin boundary/default-gating work.
**Files**: `PLANNING.md`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `tests/test_startup_smoke.py`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/tech-debt.md`, `INDEX.md`, `DEVNOTES.md`

### 2026-04-26 16:20 - Validated Roadmap Realignment Before Stage 3B1

**Goal**: Bring the live architecture roadmap, progress tracker, and tech-debt tracker into line with the validated first-principles plan before implementation resumes.
**Issues**: The repo had already validated that Stage 3B1 stays next, but the planning docs still lagged in three ways: they still implied `ShellState` might absorb route ownership, they still placed Stage 6A and Stage 3B2 too early relative to remaining direct-admin QML mutator debt, and they did not state the professional Qt end state clearly enough in terms of a smaller app-scope contract, feature-scoped models where justified, and one canonical owner per concern.
**Tried**: Re-audited the roadmap against the code and attack-review findings, added the missing first-principles maintenance rule (reduce places to look, not just places to write), inserted a new Stage 4.5 direct-admin boundary/default-gating stage, moved Stage 3B2 later behind overlay hosting and legality clarification, and aligned `00_ARCHITECTURE_PROGRESS.md` plus `docs/tech-debt.md` to the same sequence.
**Result**: ✅ The planning control plane now matches the validated direction: Stage 3B1 is still next, the remaining raw admin/calibration QML mutators are now explicitly the next risk after it, later legality work is no longer pretending metadata is enforcement, and route formalization is deferred until overlay semantics are clearer.
**Files**: `PLANNING.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-26 12:20 - Stage 4 Settings Truthfulness + Capability Model Complete

**Goal**: Finish Stage 4 by turning the Settings route into a real mixed admin surface where schema-backed settings exist, and by codifying the remaining admin/calibration mutators in one Python-owned capability inventory instead of leaving the policy in prose.
**Issues**: The first Stage 4A slice removed the overlay thrust-force authority leak and made the Settings route honest, but Stage 4 was still incomplete: winch, wheel, and arm pages needed real schema-backed settings rather than transitional placeholders; camera needed an honest summary-only route stance; and the repo still lacked executable metadata covering admin/calibration mutators such as base-top-view calibration, PID tuning, and status toggles.
**Tried**: Added non-popup `apply*` slots to `SettingsManager`; exposed schema-backed settings on the Settings route through a new `ManagedSettingSpinBox.qml` helper; rewired the winch, wheels, arm, and main Settings pages to real `SettingsManager` values; kept the camera Settings page summary-only and explicit about overlay-primary calibration; added `CapabilityCatalog` as a thin Python-owned metadata layer for settings/admin legality and mutator inventory; registered it in `AppRuntime`; added direct catalog tests; and reran focused validation followed by the full suite.
**Result**: ✅ Stage 4 is complete. The Settings route is now a truthful mixed admin surface for schema-backed settings, the remaining camera/admin exceptions are explicit, a thin executable capability inventory exists for later route/overlay stages, focused Stage 4 slices are green at `27 passed`, and the full suite is green at `210 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`.
**Files**: `PLANNING.md`, `python/paint_controller/core/settings.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/models/capability_catalog.py`, `python/paint_controller/qml/pages/settings/components/DetailSettingItem.qml`, `python/paint_controller/qml/pages/settings/components/ManagedSettingSpinBox.qml`, `python/paint_controller/qml/pages/settings/components/qmldir`, `python/paint_controller/qml/pages/settings/PageSettings.qml`, `python/paint_controller/qml/pages/settings/pages/MainSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/WinchSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/WheelsSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/ArmSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/CameraSettingsPage.qml`, `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `tests/test_settings_runtime.py`, `tests/test_startup_smoke.py`, `tests/test_qml_imports.py`, `tests/test_controller_factory_runtime.py`, `tests/test_capability_catalog.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-26 12:09 - Stage 4A.1 Overlay Settings Authority Leak + Truthful Transitional Settings Route

**Goal**: Start Stage 4A with the smallest falsifiable ownership slice: remove the remaining direct controller mutation from the overlay settings quick-apply path and stop the top-level Settings route from presenting placeholder values as truthful runtime state.
**Issues**: `SettingsTab.qml` still mixed `SettingsManager` persistence with a direct `teensyController` write for thrust force, and `PageSettings.qml` plus its subpages still presented placeholder values and fake controls as if they were a legitimate maintenance surface. The subpage back buttons were also visually present but not wired.
**Tried**: Verified that `TeensyController` already subscribes to `SettingsManager` thrust-setting signals, removed the redundant direct `teensyController.thrust_force` mutation from `SettingsTab.qml`, removed placeholder top-level state from `PageSettings.qml`, rewrote the Settings route copy so unwired subpages are explicitly transitional instead of fake-live, wired subpage back navigation to return to the main Settings page, and added a direct startup smoke test for `PageSettings.qml`.
**Result**: ✅ Stage 4A is started with a green first slice. The overlay thrust-force quick-apply path now routes through `SettingsManager` only, the Settings route no longer invents placeholder runtime values, the unwired subpages are explicit transitional surfaces, and direct validation is green at `9 passed` for `tests/test_teensy.py` plus `10 passed` for `tests/test_startup_smoke.py` and `tests/test_qml_imports.py`.
**Files**: `PLANNING.md`, `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/pages/settings/PageSettings.qml`, `python/paint_controller/qml/pages/settings/pages/MainSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/WinchSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/CameraSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/WheelsSettingsPage.qml`, `python/paint_controller/qml/pages/settings/pages/ArmSettingsPage.qml`, `tests/test_startup_smoke.py`, `DEVNOTES.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`

### 2026-04-26 14:30 - Stage 3A Shell Policy Split

**Goal**: Start Stage 3 by extracting dual-surface shell policy out of `MainWindow.qml` without widening into route hardening.
**Issues**: Root QML still turned raw screen count into product behavior, owned secondary-surface policy directly, and coupled shell composition to screen-role policy. The slice also had to avoid recreating a broad coordinator object or accidentally pulling `SelectBar` route metadata work into Stage 3A.
**Tried**: Added a narrow `ShellState` model for main-surface role, secondary-surface activation/fullscreen policy, system-control host-surface policy, and fullscreen host policy; registered it in the QML context; rewired `MainWindow.qml` and `MultiScreenListUI.qml` to consume that policy; added direct `ShellState` tests; and reran focused shell/startup/runtime coverage.
**Result**: ✅ Stage 3A is complete. Product shell policy now lives in `ShellState` instead of root QML, startup/runtime validation is green at `26 passed` for `tests/test_shell_state.py`, `tests/test_startup_smoke.py`, `tests/test_services_runtime.py`, and `tests/test_qt_bridge.py`, and the full suite is green at `205 passed`. The remaining Stage 3 work is Stage 3B route hardening after Stage 4A settings truthfulness.
**Files**: `python/paint_controller/models/shell_state.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/overlays/MultiScreenListUI.qml`, `tests/test_shell_state.py`, `tests/test_startup_smoke.py`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `DEVNOTES.md`

### 2026-04-26 10:42 - Stage 2 Overlay/Input Ownership Freeze

**Goal**: Freeze the Stage 2 overlay/input seam by pinning the live `OverlayController` compatibility behavior and moving mode-specific joystick preset memory out of `UIInputHandler` into the dedicated selection owner.
**Issues**: The overlay/menu contract had no direct regression file, so the current temporary-selection and commit timing behavior was easy to break during refactor. `UIInputHandler` also still owned base/EF preset memory even though those selections are part of joystick-selection state, not raw input translation.
**Tried**: Added direct `OverlayController` regressions for menu visibility, temporary-vs-committed selection behavior, and yaw reset handling; added remembered-controls storage to `JoystickSelectionModel`; rewired `UIInputHandler` and `controller_factory.py` to use the model directly for mode restoration; removed the redundant input-side `set_active_menu(...)` step so menu selection stays overlay-owned; centralized the overlay toggle behavior behind one internal helper; removed the dead overlay compatibility wrappers with no live callers; and expanded focused handler/model/factory/startup tests.
**Result**: ✅ Stage 2 is complete. The seam now has direct regression coverage, preset memory lives with selection ownership instead of input handling, the live `overlayController` surface is narrowed to the actual QML-facing menu/presentation contract, focused overlay/input/startup validation is green, and the full suite is green at `202 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`.
**Files**: `python/paint_controller/models/joystick_selection.py`, `python/paint_controller/handlers/input.py`, `python/paint_controller/ui/overlay.py`, `python/paint_controller/core/controller_factory.py`, `tests/test_overlay_controller.py`, `tests/test_input_handler.py`, `tests/test_joystick_selection.py`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `INDEX.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-26 08:51 - Stage 2 Selection Model Extraction

**Goal**: Continue Stage 2 past the initial cycle break by moving joystick selection ownership into a dedicated Qt-facing model while preserving the existing `overlayController` QML contract.
**Issues**: Even after the direct cycle was removed, `OverlayController` still mixed overlay presentation state with operator selection state, and `ControlProcessor` still had to read selection through the overlay surface. The extraction needed to preserve temporary-vs-committed selection behavior, duplicate-selection rules, and mode-switch behavior without destabilizing QML bindings.
**Tried**: Added `JoystickSelectionModel`, rewired `OverlayController` into a thin presentation facade over that model, made `ControlProcessor` read the model directly, updated factory wiring, added direct selection-model tests, and reran focused Stage 2 slices plus the full suite.
**Result**: ✅ Stage 2 now has a dedicated selection owner in code, `OverlayController` is narrowed to overlay/menu presentation, and validation is green at `196 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. Remaining Stage 2 work is now about finishing long-term ownership cleanup, not extracting the core model itself.
**Files**: `python/paint_controller/models/joystick_selection.py`, `python/paint_controller/ui/overlay.py`, `python/paint_controller/handlers/control_processor.py`, `python/paint_controller/core/controller_factory.py`, `tests/test_joystick_selection.py`, `tests/test_control_processor.py`, `tests/test_controller_factory_runtime.py`, `DEVNOTES.md`

### 2026-04-26 08:51 - Stage 2 Control-Selection Cycle Break

**Goal**: Start Stage 2 by removing the live `OverlayController` ↔ `ControlProcessor` cycle without changing the existing QML-facing overlay contract or joystick behavior.
**Issues**: The actual reverse dependency was narrower than the roadmap label implied: `OverlayController` only reached back into `ControlProcessor` to seed `EF Yaw Angle` offset on selection changes, but that still forced explicit deferred wiring in `controller_factory.py` and made control-selection ownership harder to explain. The yaw path also needed to preserve selection-time seeding behavior rather than resetting continuously.
**Tried**: Moved yaw-offset seeding into `ControlProcessor` as selection-transition logic, removed `OverlayController`'s processor back-reference and mutation path, deleted the deferred cycle wiring from `controller_factory.py`, added focused tests for yaw-selection transitions, and reran both the Stage 2 regression slice and the full suite.
**Result**: ✅ The concrete cycle is gone, the factory no longer needs special-case overlay/control wiring, and the repo stays green at `193 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`. This slice opened the door for the dedicated selection-model extraction that followed.
**Files**: `python/paint_controller/handlers/control_processor.py`, `python/paint_controller/ui/overlay.py`, `python/paint_controller/core/controller_factory.py`, `tests/test_control_processor.py`, `tests/test_controller_factory_runtime.py`, `DEVNOTES.md`

### 2026-04-26 00:37 - Stage 1B Through 1E Boundary Freeze

**Goal**: Finish the approved Stage 1 boundary slices by moving remaining `DeviceControlTab.qml` actions behind Python-owned handlers, splitting workflow editor persistence away from runtime execution, and hardening the `workFlowRunner` execution seam without breaking the existing runtime-facing QML contract.
**Issues**: `DeviceControlTab.qml` still owned direct controller, recorder, and heartbeat side effects; `WorkFlowRunner` still mixed file watching and editor persistence with runtime execution; and the runtime boundary still allowed `load_workflow()` during active execution, which could replace the executor's current workflow while a run was in progress.
**Tried**: Added `DeviceOperationsHandler` for Stage 1C side effects; added shared `WorkflowCatalog` plus `WorkflowEditor`; rewired `EditWorkFlowTab.qml` to `workflowEditor`; kept `workFlowRunner` as the runtime-facing context while moving it onto the shared catalog; added a runtime guard that rejects workflow loads during active execution; expanded the direct handler/runtime/factory/startup tests; and reran both focused slices and the full pytest suite.
**Result**: ✅ Stage 1B through 1E is now implemented. `DeviceControlTab.qml` no longer drives raw device/recorder/heartbeat side effects, workflow editor persistence no longer shares the same QML-facing object as runtime execution, and the hardened runtime boundary now blocks workflow replacement while execution is active. Validation is green at `190 passed` for `python/paint_controller/venv/bin/python -m pytest tests -q`.
**Files**: `python/paint_controller/handlers/device_actions.py`, `python/paint_controller/handlers/device_operations.py`, `python/paint_controller/services/workflow/workflow_catalog.py`, `python/paint_controller/services/workflow/workflow_editor.py`, `python/paint_controller/services/workflow/workflow_runner.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `tests/test_device_actions.py`, `tests/test_device_operations.py`, `tests/test_workflow_editor.py`, `tests/test_workflow_runner.py`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-25 23:55 - Validated Master Plan Reconciliation

**Goal**: Replace stale architecture-roadmap sequencing with the validated master plan before code-boundary work continues.
**Issues**: `00_ARCHITECTURE_PROGRESS.md` still pointed future sessions at Stage 1B settings outliers, the roadmap still placed shell work ahead of the documented overlay/control cycle, workflow editor persistence still appeared after workflow execution even though both concerns live on `WorkFlowRunner`, and the shell direction was still phrased too broadly as a new coordinator instead of a narrower ownership split.
**Tried**: Rewrote `PLANNING.md`, published the durable Stage 0 authority map in `00_ARCHITECTURE_PROGRESS.md`, rewrote the staged order in `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, and aligned TD-032 in `docs/tech-debt.md` with the validated sequence.
**Result**: ✅ The current-facing architecture docs now agree on the validated order: Stage 1B hard device actions next, workflow editor persistence before workflow execution, control-selection decoupling before broader shell placement work, and a narrower `ScreenManager` facts + `ShellState` policy + `QtBridge` intents split instead of a broad ShellCoordinator.
**Files**: `PLANNING.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-25 18:05 - Post-Rebase Validation And Architecture-Doc Truth Pass

**Goal**: Revalidate the rebased `refactor-python-qt-architecture-boundaries` branch on Linux and make the current-facing docs match the new architecture-boundary roadmap.
**Issues**: After rebasing onto `refactor`, the branch was green in code but the current-facing docs drifted: `INDEX.md` had duplicated architecture-direction text, `README.md` still spoke as if the active work lived specifically on `refactor`, `00_ARCHITECTURE_PROGRESS.md` still said Linux validation was pending at `14 passed`, and `docs/tech-debt.md` still used stale next-step wording plus a deleted-plan reference model for the design-system backlog.
**Tried**: Reran the focused Stage 1A Linux slice (`tests/test_manual_command_handler.py`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`), reran the full pytest suite, then updated the repo entry docs, architecture progress tracker, and tech-debt tracker to match the rebased branch state and the architecture-boundary roadmap.
**Result**: ✅ The rebased branch validates on Linux at `20 passed` for the focused Stage 1A slice and `179 passed` for the full pytest suite, and the current-facing docs now consistently point at `00_ARCHITECTURE_PROGRESS.md` + `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` instead of mixing in stale branch/status wording.
**Files**: `INDEX.md`, `README.md`, `docs/plan/00_ARCHITECTURE_PROGRESS.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-25 17:19 - CommandTab Python-Owned Boundary Freeze

**Goal**: Start the roadmap implementation with the first bounded Stage 1 slice by moving manual command validation, coercion, and dispatch out of `CommandTab.qml` and into a Python-owned boundary.
**Issues**: `CommandTab.qml` still owned the command catalog, parameter-name semantics, and raw controller calls. The Demo command also had a live mismatch: the QML form defined `Gimbal Angle` / `Gimbal Speed` while the dispatch path read `Pitch Angle` / `Pitch Speed`. Follow-up validation also exposed workspace/runtime gaps on Windows: missing `cv2`, PySide6 QML plugin DLL resolution failing until the package directory was added to the DLL search path, and missing optional `gi` / message / `rclpy` stub coverage in the test harness.
**Tried**: Added a dedicated `ManualCommandHandler` QObject with a small command registry, coercion rules, unsupported-command handling, and controller dispatch; registered it as a new QML context property; rewired `CommandTab.qml` to call the handler instead of raw controllers; made unsupported commands explicitly unavailable in the UI; added focused tests for the new boundary plus DI/runtime-harness updates; added a reusable Windows Qt environment helper for PySide6 DLL resolution; declared `opencv-python-headless` as an explicit dependency; and expanded the test harness stubs for `gi`, `std_msgs.msg.String`, and `rclpy.ok` / `shutdown`.
**Result**: ✅ The bounded command slice is implemented and the broader focused validation is green at `14 passed` for `tests/test_manual_command_handler.py`, `tests/test_controller_factory_runtime.py`, and `tests/test_startup_smoke.py`.
**Files**: `PLANNING.md`, `python/paint_controller/handlers/manual_commands.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/qml/overlays/systemcontrol/CommandTab.qml`, `python/paint_controller/utils/qt_env.py`, `python/paint_controller/requirements.txt`, `tests/conftest.py`, `tests/test_manual_command_handler.py`, `tests/test_controller_factory_runtime.py`, `tests/test_startup_smoke.py`, `DEVNOTES.md`

### 2026-04-25 15:46 - Architecture Plan Doc Realignment

**Goal**: Make the live documentation set point at the new single-file architecture roadmap before branch/commit work continues
**Issues**: `INDEX.md`, `README.md`, and `docs/tech-debt.md` still treated deleted plan docs (`00_README.md`, `01_MASTER_PLAN.md`, `02_ARCHITECTURE.md`, `03_QML_BINDINGS.md`) as live authorities even though `docs/plan/` now contains only `01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md`
**Tried**: Repointed the repo entry docs at the new roadmap, updated the current-strategy wording away from the older `TD-031` page-structure framing, and rewrote the active tech-debt item so it matches the current authority-first architecture plan
**Result**: ✅ Fresh sessions now land on the live roadmap instead of deleted files. Repo-wide markdown validation still finds the old plan names only inside historical DEVNOTES entries, which were intentionally left unchanged as past-session records.
**Files**: `INDEX.md`, `README.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-25 10:15 - QML Backlog Commit Prep Truth Pass

**Goal**: Prepare the current QML backlog slice for commit by aligning the planning/debt docs with the already-landed code and revalidating the touched startup/import surfaces.
**Issues**: The working tree already advanced `2.5b` and `2.5c`, narrowed `TD-016` by turning `VideoOverlayStyle.qml` into a compatibility shim over `CommonStyle`, and deduplicated `JoystickOverlay.qml`, but the plan/debt docs still described `2.7` as untouched backlog and overstated the remaining video-style drift.
**Tried**: Rewrote the active `PLANNING.md` scratch for the commit-prep task, updated the master plan, plan-doc navigator, debt tracker, and architecture summary to match the current QML/token state, then reran `python/paint_controller/venv/bin/python -m pytest tests/test_startup_smoke.py tests/test_qml_imports.py -q`.
**Result**: ✅ The docs now describe the live backlog truthfully: `2.5b` and `2.5c` remain partial, `2.7` is complete through the shared `JoystickMenuOverlay` extraction, `TD-016` is narrowed to wrapper cleanup, and the focused QML validation slice is green at `9 passed`.
**Files**: `PLANNING.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/00_README.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-24 17:10 - Final Validation And Doc Truth Pass

**Goal**: Revalidate the startup/runtime follow-up changes and align current-facing docs before commit
**Issues**: The new startup smoke harnesses initially failed under Qt 6.10 because `QQmlComponent.setData()` stayed in `Status.Loading` briefly for file-URL directory imports, and several current-facing docs still described `TD-031` as upcoming or carried stale fixed validation counts and deleted QML paths.
**Tried**: Added a small readiness wait helper to `tests/test_startup_smoke.py`, reran the focused startup/runtime slices, reran the full pytest suite, then updated the repo status/docs to match the completed TD-031 state and the live QML tree.
**Result**: ✅ Focused startup/runtime regressions are green, full pytest is green at `170 passed`, and the current-facing docs now point at the post-TD-031 backlog instead of an already-completed structural stage.
**Files**: `tests/test_startup_smoke.py`, `README.md`, `INDEX.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/plan/03_QML_BINDINGS.md`, `DEVNOTES.md`

### 2026-04-24 16:20 - CommonStyle Wrapper Regression

**Goal**: Fix the runtime QML load failure introduced by the `CommonStyle` theme relocation
**Issues**: `qml/core/CommonStyle.qml` had been changed into `Theme.CommonStyle {}`. QML treats that as a composite singleton type, which is not creatable, so every QML file importing `core` failed with `Type CommonStyle unavailable`. `AppRuntime._load_qml()` also logged `MainWindow QML loaded` even when `QQmlApplicationEngine` had no root object. A follow-on bootstrap failure exposed that `AppRuntime.__init__()` could raise before `main()` had a bound runtime instance, leaving the ROS `QThread` alive during process teardown.
**Tried**: Replaced the wrapper with a real `QtObject` singleton that mirrors properties from `qml/theme/CommonStyle.qml`, restored the missing legacy `systemcontrol` tab import in `SystemControlWorkspace.qml`, made `_load_qml()` raise if `engine.load()` produces no root object, and wrapped `AppRuntime._bootstrap()` so construction-time failures call `shutdown()` before re-raising.
**Result**: ✅ The invalid singleton composition is gone, the feature-root workspace can resolve its legacy tab types again, and future QML/bootstrap load failures fail fast while still shutting down the partially started runtime.
**Files**: `python/paint_controller/qml/core/CommonStyle.qml`, `python/paint_controller/qml/features/systemcontrol/SystemControlWorkspace.qml`, `python/paint_controller/core/app_runtime.py`, `tests/test_controller_factory_runtime.py`, `DEVNOTES.md`

### 2026-04-24 16:05 - TD-031 Closeout

**Goal**: Finish `TD-031` and close the blocking structural refactor stage truthfully
**Issues**: The remaining gap was not structure but proof. The new `systemcontrol` and video feature roots existed, but the smoke suite did not yet load them directly. The chat task runner still rejected one-off pytest execution, so closeout had to rely on tighter in-repo smoke coverage plus editor diagnostics rather than a live command run from this session.
**Tried**: Added direct smoke tests for `qml/features/systemcontrol/SystemControlWorkspace.qml` and `qml/features/video/VideoFullscreenWorkspace.qml`, then updated the debt tracker, master plan, repo index, and plan README to move `TD-031` out of active blocking work and into the resolved set.
**Result**: ✅ `TD-031` is complete. The narrowed scope is fully implemented, focused smoke coverage now exists for the shell, multiscreen host, navigation registry, and both new feature roots, and only low-priority UI consistency backlog remains.
**Files**: `tests/test_startup_smoke.py`, `docs/tech-debt.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `INDEX.md`, `DEVNOTES.md`

### 2026-04-22 16:20 - TD-001 Stage 1 Closeout

**Goal**: Finish the remaining meaningful Stage 1 QML hardening work, add the planned warn-only `qmllint` CI gate, and close the debt item without pretending every QML file should have `required property`
**Issues**: The raw "files without `required property`" count had become misleading because several remaining QML files are global-context consumers, style/token holders, or objects configured imperatively after construction. Forcing `required` onto those surfaces would create bad contracts instead of better failure modes.
**Tried**: Used a bounded classification pass to separate true constructor-driven APIs from non-candidates, hardened the remaining real constructor surfaces (`ControlInfoPanel`, `JoystickOverlay`, `SystemControlMenu`, `SettingsTab`, plus the max-value monitor cards), converted local constants/derived values to `readonly` where that clarified intent, added a warn-only `qmllint` job in `.github/workflows/ci.yml`, and updated the authoritative docs to move `TD-001` out of active debt.
**Result**: ✅ `TD-001` Stage 1 is complete. `tests/test_startup_smoke.py` stayed green at `3 passed`, `tests/test_qml_imports.py` stayed green, whole-tree `qmllint` stayed clean, and repeated offscreen `paint_controller` startup still reached `MainWindow QML loaded`. Remaining QML files without `required` were reviewed and intentionally left alone because they are not constructor-driven surfaces.
**Files**: `.github/workflows/ci.yml`, `python/paint_controller/qml/overlays/video/components/ControlInfoPanel.qml`, `python/paint_controller/qml/overlays/JoystickOverlay.qml`, `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml`, `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/pages/status/components/WheelsCard.qml`, `python/paint_controller/qml/pages/status/components/TeensyArmCard.qml`, `python/paint_controller/qml/pages/status/components/WinchCard.qml`, `python/paint_controller/qml/components/popups/CustomPopup.qml`, `python/paint_controller/qml/overlays/systemcontrol/CommandTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `python/paint_controller/qml/overlays/video/components/VideoOverlayTopBar.qml`, `python/paint_controller/qml/pages/status/components/IMUCard.qml`, `python/paint_controller/qml/pages/status/components/ValvesCard.qml`, `INDEX.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/plan/03_QML_BINDINGS.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-22 15:54 - First Required/Readonly Hardening Pass

**Goal**: Start Stage 1 QML API hardening on surviving reusable components without widening into large caller rewrites
**Issues**: Several shared display/control components still relied on silent default values for semantic inputs, which means structural mistakes can render plausible-but-wrong UI instead of failing early. The hardening pass had to stay limited to components with small, verified caller sets so the new `required` contracts would be falsifiable immediately.
**Tried**: Hardened `MetricPanel`, `BatteryDisplay`, `WindVisualizer`, `TouchSwitch`, `PitchIndicatorDial`, `SelectBar`, `ConnectionStatusPanel`, `SettingInputField`, `ControlPanel`, and `ActionButton` by making their semantic inputs `required`, and added small `readonly` helpers where that simplified repeated derived calculations. After approval, deleted the now-empty `components/inputs` and `components/panels` buckets. Verified caller coverage first, then revalidated with `tests/test_startup_smoke.py`, `tests/test_qml_imports.py`, whole-tree `qmllint`, and repeated offscreen `paint_controller` startup.
**Result**: ✅ The first reusable-component hardening slice is green and the empty shared buckets are gone. Startup smoke stayed at `3 passed`, the QML import smoke stayed green, `qmllint` stayed clean with `status=0`, and offscreen app startup still reached `MainWindow QML loaded` and entered the event loop after each slice. Remaining Stage 1 work is the next hardening slice on surviving reusable surfaces.
**Files**: `python/paint_controller/qml/components/displays/MetricPanel.qml`, `python/paint_controller/qml/components/displays/BatteryDisplay.qml`, `python/paint_controller/qml/components/displays/WindVisualizer.qml`, `python/paint_controller/qml/components/displays/PitchIndicatorDial.qml`, `python/paint_controller/qml/components/buttons/TouchSwitch.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `python/paint_controller/qml/navigation/ConnectionStatusPanel.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/SettingInputField.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/ControlPanel.qml`, `python/paint_controller/qml/overlays/systemcontrol/components/ActionButton.qml`, `python/paint_controller/qml/components/inputs`, `python/paint_controller/qml/components/panels`, `DEVNOTES.md`

### 2026-04-22 15:45 - Secondary-Screen QML Smoke Guard + Import Cleanup

**Goal**: Add a regression test for the real `MultiScreenListUI -> PageMonitor` startup path before continuing the Stage 1 QML cleanup, then prune the stale broad imports that kept the empty shared buckets looking live
**Issues**: `tests/test_qml_imports.py` plus `qmllint` were not enough to catch the moved monitor family losing `ProgressBarIndicator` at runtime. The secondary-screen path was only exercised by a full app launch, so structural edits could still pass static checks and fail during real startup.
**Tried**: Extended `tests/test_startup_smoke.py` with a direct offscreen load of `MultiScreenListUI.qml`, expanded the fake context bundle with the monitor-page controller properties that actually bind during startup, then removed stale `components/buttons`, `components/inputs`, and `components/panels` imports from files that no longer use those buckets.
**Result**: ✅ The monitor branch now has direct regression coverage, `tests/test_startup_smoke.py` revalidated at `3 passed`, `tests/test_qml_imports.py` stayed green, and whole-tree `qmllint` stayed clean. There are no remaining imports of `components/inputs` or `components/panels`; only the now-empty `qmldir` stubs remain, which need explicit delete approval.
**Files**: `tests/test_startup_smoke.py`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/pages/status/PageMonitor.qml`, `python/paint_controller/qml/pages/status/PageStatus.qml`, `python/paint_controller/qml/pages/status/components/TeensyStatus.qml`, `python/paint_controller/qml/pages/home/PageLauncher.qml`, `python/paint_controller/qml/pages/winch/PageWinch.qml`, `python/paint_controller/qml/pages/tuning/PageTuning.qml`, `python/paint_controller/qml/pages/wheel/PageWheel.qml`, `python/paint_controller/qml/overlays/systemcontrol/SystemControlMenu.qml`, `python/paint_controller/qml/overlays/video/VideoFullscreenOverlay.qml`, `DEVNOTES.md`

### 2026-04-22 15:33 - Stage 1 QML Structural Flatten Slices

**Goal**: Keep reducing misleading shared QML buckets by moving single-host widget families beside the page or overlay that actually owns them
**Issues**: Dead-file reachability in this repo depends on both `qmldir` exports and broad folder imports, so several live-looking shared folders were really just historical buckets. The remaining risk was breaking relative imports while relocating QML families that only had one real caller.
**Tried**: Deleted the approved dead-file rings, renamed `OverlayLayer` to `JoystickOverlay`, moved `ConnectionStatusPanel` into `navigation/`, moved the `PageMonitor` card family into `pages/status/components/`, and moved the `DeviceControlTab` plus settings/input support widgets into `overlays/systemcontrol/components/`. Revalidated after each slice with `tests/test_qml_imports.py` and whole-tree `qmllint`.
**Result**: ✅ Stage 1 structural flatten is materially smaller and still green. The narrow QML import smoke test stayed green after every slice, and whole-tree `qmllint` remained clean with `status=0` throughout. Remaining cleanup is mostly stale broad imports and deletion of now-empty bucket files/directories.
**Files**: `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `python/paint_controller/qml/navigation/ConnectionStatusPanel.qml`, `python/paint_controller/qml/overlays/JoystickOverlay.qml`, `python/paint_controller/qml/pages/status/PageMonitor.qml`, `python/paint_controller/qml/pages/status/components/qmldir`, `python/paint_controller/qml/overlays/systemcontrol/DeviceControlTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/SettingsTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/CommandTab.qml`, `python/paint_controller/qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `DEVNOTES.md`

### 2026-04-22 13:03 - TD-030 Runtime Validation Closeout

**Goal**: Finish the runtime/workflow/service validation gate so the branch can move to the remaining defensive QML debt with the live composition path under direct regression coverage
**Issues**: The first TD-030 batch still left the composition root, bounded `AppRuntime` seams, selected service lifecycles, and direct `WorkFlowExecutor` control-path behavior outside the new focused test slice
**Tried**: Added direct tests for `create_controllers()` and `ControllerBundle.cleanup()`, bounded `AppRuntime` bundle/context/shutdown seams, `ScreenManager`, `BaseTopViewTransformer`, and `WorkFlowExecutor`, then iterated the new fakes until the tests matched the real runtime callback surfaces instead of Qt-global shortcuts
**Result**: ✅ TD-030 is complete. The focused runtime/workflow/service batch now covers scheduler/actions, hardware adapters, runner, executor, controller factory, bounded runtime seams, and selected services, with revalidation green at `22 passed`
**Files**: `tests/test_workflow_scheduler.py`, `tests/test_workflow_runner.py`, `tests/test_workflow_executor.py`, `tests/test_controller_factory_runtime.py`, `tests/test_services_runtime.py`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/tech-debt.md`, `INDEX.md`, `DEVNOTES.md`


### 2026-04-22 12:40 - Branch Gate Rebase + Workflow Validation Batch 1

**Goal**: Rebase the refactor endgame around the highest remaining integration risk and start the new runtime/workflow validation stage with a bounded first slice
**Issues**: The live docs still pointed future sessions at TD-001 and deferred theming before the larger runtime gap, PLANNING.md still contained stale TD-014 scratch state, and the workflow stack had almost no direct tests despite being a live actuator-facing path
**Tried**: Added a branch gate plus exit bar to the plan docs, promoted TD-030 runtime/workflow/service validation into the active debt queue, added a namespace-only paint_controller.services test stub to avoid the heavy services/__init__.py import path, and added direct tests for ActionScheduler, ActionRegistry, HardwareControllers, and WorkFlowRunner
**Result**: ✅ The planning control plane now points at TD-030 first, the first workflow validation slice is in place, tests/test_workflow_scheduler.py plus tests/test_workflow_runner.py passed at 8 passed, and the shared harness plus workflow slice revalidated at 14 passed
**Files**: PLANNING.md, INDEX.md, docs/plan/00_README.md, docs/plan/01_MASTER_PLAN.md, docs/plan/02_ARCHITECTURE.md, docs/tech-debt.md, tests/conftest.py, tests/test_workflow_scheduler.py, tests/test_workflow_runner.py, DEVNOTES.md


### 2026-04-22 10:45 - Typing Gate Expansion + Page Naming + Shared ROS Status Base

**Goal**: Complete the approved next refactor stage by finishing `3.10`, closing `2.8`, and extracting a narrow shared base for the duplicated availability lifecycle in wheel/winch/teensy
**Issues**: The pyright gate still only covered the factory/core slice, shell navigation still used generic `pageNComponent` IDs with one dead switch branch, wheel/winch/teensy repeated the same availability timer + timestamp + cleanup lifecycle, and a short offscreen runtime launch exposed a late SSH availability callback emitting into a deleted QObject during teardown
**Tried**: Renamed page component IDs in `MainWindow.qml`/`SelectBar.qml` and removed the dead `case 6`, expanded handler/controller typing with real constructor annotations, widened `pyrightconfig.json` to cover `handlers/` + `controllers/`, added a narrow `RosStatusController` base in `controllers/_base.py`, promoted `core/config.py`, `core/controller_factory.py`, `handlers/safety_coordinator.py`, and `utils/steam_deck_hid.py` to strict mode, and hardened `UISSHController` to ignore late availability/command results during QObject teardown with a new regression test
**Result**: ✅ `3.10` and `2.8` are complete. Full pytest revalidated at `148 passed`, pyright is green at `0 errors`, focused handler/controller regressions stayed green, and an offscreen runtime launch still reached `MainWindow QML loaded` without the previous SSH teardown `RuntimeError`. The known non-blocking Qt Quick 3D/RHI warning remains in offscreen mode.
**Files**: `PLANNING.md`, `pyrightconfig.json`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/navigation/SelectBar.qml`, `python/paint_controller/controllers/_base.py`, `python/paint_controller/controllers/wheel.py`, `python/paint_controller/controllers/winch.py`, `python/paint_controller/controllers/teensy.py`, `python/paint_controller/controllers/lidar.py`, `python/paint_controller/controllers/wind_monitor.py`, `python/paint_controller/controllers/system_monitor.py`, `python/paint_controller/controllers/ssh.py`, `python/paint_controller/controllers/esp32_valve.py`, `python/paint_controller/handlers/control_processor.py`, `python/paint_controller/handlers/emergency.py`, `python/paint_controller/handlers/heartbeat.py`, `python/paint_controller/handlers/input.py`, `python/paint_controller/handlers/safety_coordinator.py`, `python/paint_controller/handlers/steam_deck.py`, `python/paint_controller/handlers/warnings.py`, `python/paint_controller/utils/steam_deck_hid.py`, `tests/test_control_processor.py`, `tests/test_emergency.py`, `tests/test_heartbeat.py`, `tests/test_ssh.py`, `tests/test_steam_deck_handler.py`, `tests/test_startup_smoke.py`, `tests/test_teensy.py`, `tests/test_wheel.py`, `tests/test_winch.py`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-21 14:15 - First-Touch UI Freeze + Main-Thread Reconnect Jank

**Goal**: Eliminate the 5–20s whole-UI freeze on the first page switch after startup and remove the recurring ESP32 reconnect hitch that could still jank the UI while hardware was disconnected
**Issues**: Non-Home pages lazily instantiated on first navigation and some of them imported heavyweight QML modules (`QtMultimedia`, `QtCharts`, `Qt5Compat.GraphicalEffects`) even when the page did not use those types. That meant the first user touch paid plugin-init cost on the GUI thread. Separately, `ESP32ValveController` ran `arp -a` discovery and a UDP thread wait from the main thread during reconnect attempts, and `/controller/heartbeat` publishing still depended on a Qt timer so a GUI stall self-reported as heartbeat loss
**Tried**: Removed dead heavyweight imports from `PageWheel.qml` and `PageSpray.qml`, pre-warmed the still-needed `QtCharts` and `Qt5Compat.GraphicalEffects` modules inside `MainWindow.qml`, moved controller heartbeat publishing onto a ROS-side timer in `PaintRosNode`, dropped the dead `signal_timer`, moved ESP32 ARP discovery onto a background thread, and made normal reconnect stop/close the old UDP socket without waiting on the Qt thread. Added `tests/test_qml_imports.py` plus focused ROS/ESP32 regressions and revalidated startup smoke
**Result**: ✅ The targeted regression set passed at `13 passed`, the full suite revalidated at `148 passed`, and an offscreen runtime launch still reached `MainWindow QML loaded`, entered the event loop, and completed deferred video startup. The first-navigation stall should now be paid at startup only for the genuinely-used chart/effect modules, while the unused `QtMultimedia` import path is gone entirely. The known non-blocking Qt Quick 3D/RHI warning remains in offscreen mode
**Files**: `PLANNING.md`, `python/paint_controller/qml/core/MainWindow.qml`, `python/paint_controller/qml/pages/wheel/PageWheel.qml`, `python/paint_controller/qml/pages/spray/PageSpray.qml`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/core/ros_node.py`, `python/paint_controller/controllers/esp32_valve.py`, `tests/test_qml_imports.py`, `tests/test_ros_node.py`, `tests/test_esp32_valve.py`, `DEVNOTES.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/tech-debt.md`

### 2026-04-21 13:27 - TD-014 AppRuntime Extraction

**Goal**: Decompose the bootstrap path so startup and shutdown stop living inside one large `main()` function
**Issues**: `core/application.py` mixed process signal handling, dead config loading, ROS threading, runtime construction, QML setup, controller wiring, and shutdown teardown in one file. The `robot_config.yaml` path was also fake — the file did not exist anywhere in the repo, so the loader only masked hardcoded defaults.
**Tried**: Replaced the dead yaml loader with `RuntimeDefaults` in `core/config.py`, moved `RosThread` into `core/ros_node.py`, extracted startup/shutdown orchestration into `core/app_runtime.py`, kept `application.py` as the public entry-point wrapper for signals and compatibility, restored early signal-handler access to the `QApplication` during bootstrap, and replaced the duplicated context-property name list with a registration table guarded by an explicit expected-name contract check. Revalidated with startup smoke, `py_compile`, full pytest, pyright, and an offscreen real-app launch.
**Result**: ✅ TD-014 is complete. `tests/test_startup_smoke.py` stayed green, the full suite revalidated at `145 passed`, pyright stayed green (`0 errors`), and the offscreen app launch still reached `MainWindow QML loaded`. The known non-blocking Qt Quick 3D/RHI warning remains in offscreen mode.
**Files**: `PLANNING.md`, `python/paint_controller/core/application.py`, `python/paint_controller/core/app_runtime.py`, `python/paint_controller/core/config.py`, `python/paint_controller/core/ros_node.py`, `python/paint_controller/core/controller_factory.py`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-21 12:20 - Atomic Persistence + Teensy/SSH Thread Hardening

**Goal**: Close the remaining correctness gaps below the active safety plan: non-atomic config writes, a live shared Teensy status dict crossing ROS/Qt threads, and SSH callbacks touching UI state from background threads
**Issues**: `SettingsManager.save_all()` and `UISSHController._save_json_file()` still rewrote JSON in place, `TeensyController` emitted and returned the live `_status` dict while ROS callbacks could replace it, and SSH command / availability callbacks were mutating Qt-facing state directly from worker threads
**Tried**: Switched both JSON write paths to temp-file + flush/fsync + `os.replace` with parent-directory fsync, added SSH connect/auth/banner timeouts plus daemon worker tracking, marshaled SSH results back through Qt signals, and changed Teensy status readers/writers to lock consistently and emit defensive snapshots. Added focused regressions in `tests/test_settings_runtime.py`, `tests/test_teensy.py`, and new `tests/test_ssh.py`
**Result**: ✅ First hardening batch is green. Focused regressions passed at `19 passed`, and the later full-suite run stayed green at `145 passed`
**Files**: `PLANNING.md`, `python/paint_controller/core/settings.py`, `python/paint_controller/controllers/ssh.py`, `python/paint_controller/controllers/teensy.py`, `tests/test_settings_runtime.py`, `tests/test_teensy.py`, `tests/test_ssh.py`

### 2026-04-21 12:35 - Steam Deck HID Parser Extraction + Cleanup Stability

**Goal**: Finish task `3.5` by making Steam Deck HID decoding directly testable without dragging Qt threads and HID devices into every parser test
**Issues**: `_process_input()` mixed raw byte decoding, stick shaping, button debounce/hold timing, callback scheduling, and Qt signal emission in one function. Initial parser tests passed, but the existing cleanup regression still exposed a segmentation fault at interpreter shutdown because `SteamDeckHandler.__del__()` was touching QObject/QThread state too late
**Tried**: Extracted a pure `parse_hid_frame()` helper into `utils/steam_deck_hid.py`, rewired `_process_input()` to consume that decoder while leaving all stateful timing/callback logic in place, added `tests/test_steam_deck_hid.py`, isolated the shutdown crash to the old destructor path, and removed destructor-side cleanup in favor of the explicit cleanup lifecycle already owned by app shutdown/tests
**Result**: ✅ Steam Deck parsing now has direct coverage and cleanup stability is improved. `tests/test_steam_deck_hid.py` + `tests/test_steam_deck_handler.py` passed together at `5 passed` with no segfault
**Files**: `PLANNING.md`, `python/paint_controller/utils/steam_deck_hid.py`, `python/paint_controller/handlers/steam_deck.py`, `tests/test_steam_deck_hid.py`, `tests/test_steam_deck_handler.py`

### 2026-04-21 12:50 - Safety Integration Coverage + Initial Pyright Gate

**Goal**: Prove the real heartbeat-loss → halt-all convergence path and stand up the first truthful static typing gate without pretending the whole PySide-heavy core is type-ready
**Issues**: Safety coverage was split across isolated unit tests rather than one real handler/coordinator wiring path; the first pyright attempt also showed that strict mode on PySide `Signal`/`Property` descriptor-heavy modules was dominated by framework stub noise rather than actionable typing defects; final offscreen smoke additionally exposed a runtime bug where `SafetyCoordinator` used stdlib-style `%s` logger formatting against the ROS logger API
**Tried**: Added `tests/test_safety_integration.py` with real `UIHeartbeatHandler` + `SafetyCoordinator` and fake effectors, installed/configured pyright in CI with strict mode limited to `core/controller_factory.py` and basic visibility on selected PySide-heavy core files, suppressed the Qt `Property` redeclaration false-positive at the file boundary in `state_store.py`, and converted `SafetyCoordinator` logger calls to ROS-compatible single-string messages. Revalidated with targeted safety tests, pyright, a serial full-suite run, and a short offscreen launch
**Result**: ✅ New safety integration coverage is in place, the initial pyright gate is green (`0 errors`), the full suite revalidated at `145 passed`, and offscreen startup still reaches `MainWindow QML loaded`. Offscreen mode still logs the known non-blocking Qt Quick 3D/RHI warning. The old missing `robot_config.yaml` startup message was later eliminated by TD-014 when the dead loader path was replaced with `RuntimeDefaults`.
**Files**: `PLANNING.md`, `python/paint_controller/handlers/safety_coordinator.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/state_store.py`, `python/paint_controller/core/qt_bridge.py`, `requirements-dev.txt`, `.github/workflows/ci.yml`, `pyrightconfig.json`, `tests/test_safety_integration.py`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`

### 2026-04-21 11:30 - Final Shutdown Thread Owner: ESP32 Valve UDP Thread

**Goal**: Eliminate the remaining real-app exit abort after QML teardown had already been fixed
**Issues**: The app still ended with `QThread: Destroyed while thread is still running` even after the QML teardown and Steam Deck fixes. Thread-owner review showed `ESP32ValveController` starts `UDPReceiveThread` but had no public `cleanup()` method, so normal `ControllerBundle.cleanup()` never reached that thread. It only stopped during object destruction, which was too late.
**Tried**: Added explicit `ESP32ValveController.cleanup()` to stop timers and disconnect/join the UDP thread, upgraded `_disconnect()` to warn and force-terminate if the thread does not exit in time, and added regression coverage in `tests/test_esp32_valve.py`. Then made the destructor tolerant of already-deleted Qt timers.
**Result**: ✅ Remaining app-owned thread now participates in normal shutdown. Focused shutdown regressions passed and the full suite revalidated at `133 passed`
**Files**: `PLANNING.md`, `python/paint_controller/controllers/esp32_valve.py`, `tests/test_esp32_valve.py`

### 2026-04-21 11:25 - Shutdown Smoke Harness For QML Teardown

**Goal**: Add an automated shutdown regression test for the real `MainWindow.qml` shell so termination bugs stop depending on manual app exits to reproduce
**Issues**: The first teardown fix still left post-exit QML `Cannot read property ... of null` warnings in the real app, so startup-only smoke coverage was insufficient. The original teardown helper also touched `QQmlApplicationEngine` after scheduling it for deletion.
**Tried**: Strengthened `_teardown_qml_runtime()` to clear the component cache before `engine.deleteLater()` and flush deferred deletes with `QCoreApplication.sendPostedEvents(...)`; added a shutdown-side smoke test in `tests/test_startup_smoke.py` that loads real `MainWindow.qml`, records baseline warnings, runs the teardown helper, and fails on new post-teardown `Cannot read property` / `Unable to assign [undefined]` warnings.
**Result**: ✅ Shutdown teardown now has direct regression coverage and the full suite revalidated at `132 passed`
**Files**: `PLANNING.md`, `python/paint_controller/core/application.py`, `tests/test_startup_smoke.py`

### 2026-04-21 11:20 - Shutdown Teardown Ordering Regression

**Goal**: Fix the post-exit termination regression where shutdown logged many QML `Cannot read property ... of null` errors and then aborted with `QThread: Destroyed while thread is still running`
**Issues**: The QML engine/root object tree outlived backend QObject cleanup, so bindings were still reevaluating while Python context-property objects were already being torn down. Separately, `SteamDeckHandler.cleanup()` had been accidentally defined twice, and the later weaker version overrode the real cleanup path so the HID reader thread was not reliably waited/joined during shutdown.
**Tried**: Added explicit QML teardown in `application.py` to close/delete root objects and flush Qt events before controller/service cleanup, restored a single authoritative Steam Deck cleanup path that always delegates to the reader-thread cleanup helper, and made `ScreenManager.cleanup()` disconnect its global `QGuiApplication` screen signals.
**Result**: ✅ Shutdown lifetime ordering is fixed at the Python side; targeted shutdown tests passed and the full suite revalidated at `131 passed`
**Files**: `PLANNING.md`, `python/paint_controller/core/application.py`, `python/paint_controller/handlers/steam_deck.py`, `python/paint_controller/services/screen_manager.py`, `tests/test_steam_deck_handler.py`

### 2026-04-21 11:04 - Safety Hardening Batch A + Offscreen Startup Smoke

**Goal**: Implement the approved first-principles safety batch: live controller heartbeat state, safe shutdown ordering, settings-backed emergency hold duration, unified halt-all behavior, and a headless startup smoke gate
**Issues**: `PaintRosNode.publish_heartbeat()` always published `IDLE`; `RosThread._cleanup()` destroyed the shared node before controller cleanup; `EmergencyButtonHandler` used `0.2` seconds despite a "1 second" contract comment; emergency missed the ESP32 valve and heartbeat-loss halt path; full-suite validation also exposed a flaky `SystemMonitor` worker-start timing assumption
**Tried**: Added `HeartbeatStatus` constants and `StateStore.controller_heartbeat_state`, moved ROS-node cleanup into `main()` after service/controller shutdown, added `emergency_hold_duration_s` to `SettingsManager`, introduced `SafetyCoordinator.halt_all_effectors(reason)`, wired emergency/heartbeat/wheel-error through it, added `tests/test_startup_smoke.py` plus new focused safety tests, then made `SystemMonitor` worker start deterministic and hardened its test to poll briefly instead of assuming a fixed 50ms budget
**Result**: ✅ Safety batch complete. Targeted safety/startup tests are green, the offscreen `MainWindow.qml` smoke gate now exists, and the full suite revalidated at `130 passed`
**Files**: `PLANNING.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/tech-debt.md`, `python/paint_controller/core/application.py`, `python/paint_controller/core/controller_factory.py`, `python/paint_controller/core/ros_node.py`, `python/paint_controller/core/settings.py`, `python/paint_controller/core/state_store.py`, `python/paint_controller/controllers/system_monitor.py`, `python/paint_controller/handlers/emergency.py`, `python/paint_controller/handlers/heartbeat.py`, `python/paint_controller/handlers/safety_coordinator.py`, `python/paint_controller/utils/constants.py`, `tests/conftest.py`, `tests/fakes.py`, `tests/test_emergency.py`, `tests/test_heartbeat.py`, `tests/test_ros_node.py`, `tests/test_safety_coordinator.py`, `tests/test_settings_runtime.py`, `tests/test_startup_smoke.py`, `tests/test_state_store.py`, `tests/test_system_monitor.py`

### 2026-04-20 21:46 - First-Principles Plan Reprioritization

**Goal**: Reconcile the active modernization plan with the approved first-principles review before implementation resumes
**Issues**: `01_MASTER_PLAN.md` still pointed future sessions at design-system work first, carried stale test-count language, and still listed two low-value debt items that were intentionally dropped after review
**Tried**: Updated the master plan queue to front-load BF-1..BF-4 and Phase 3 hardening, marked the remaining Phase 2 theming work as deferred, corrected the required-props scope away from deleted workflow/widgets paths, and synchronized `00_README.md` plus `docs/tech-debt.md`
**Result**: ✅ The planning docs now agree on the active queue: hotfixes → `3.0` → `3.6` → `3.7` → `3.5` → `1.11a-e` → `2.8`, with theming intentionally deferred until the hardening queue is complete
**Files**: `PLANNING.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/tech-debt.md`

### 2026-04-20 21:52 - Hotfix Queue + Import Cleanup + Wheel Coverage

**Goal**: Start implementation with the highest-value approved batch: BF-1..BF-4, task `3.0`, and the missing WheelController coverage in `3.6`
**Issues**: `set_load_detection_mode()` still published when the winch was unavailable, `SystemMonitorWorker` started its timer from the wrong thread, wheel error handling was connected directly from the ROS thread, package `__init__.py` files still re-exported heavy modules, and WheelController had no dedicated unit tests
**Tried**: Replaced remaining unavailable winch guard `print()` calls with node logger warnings and added the missing early return, moved SystemMonitor timer ownership/startup fully onto the worker-thread path, connected wheel error handling with `Qt.QueuedConnection`, removed subpackage re-exports, expanded the test stubs/fakes for wheel messages and logger formatting, and added focused tests for WinchController, SystemMonitor, and WheelController behavior
**Result**: ✅ Focused validation is green: `tests/test_winch.py` (8 passed), `tests/test_system_monitor.py` (1 passed), and `tests/test_wheel.py` + `tests/test_test_infrastructure.py` (11 passed combined). The active queue now starts at `3.7`.
**Files**: `python/paint_controller/controllers/winch.py`, `python/paint_controller/controllers/system_monitor.py`, `python/paint_controller/core/application.py`, `python/paint_controller/core/__init__.py`, `python/paint_controller/handlers/__init__.py`, `python/paint_controller/controllers/__init__.py`, `tests/conftest.py`, `tests/fakes.py`, `tests/test_winch.py`, `tests/test_system_monitor.py`, `tests/test_wheel.py`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/tech-debt.md`, `PLANNING.md`

### 2026-04-20 22:05 - ESP32 + Teensy Controller Coverage

**Goal**: Complete task `3.7` with direct regression coverage for `ESP32ValveController` and `TeensyController`
**Issues**: The harness lacked stubs for `Float32`, multi-array/int ROS messages, `geometry_msgs`, `ValveStatus`, `TeensyStatus`, and `TeensyYaw`; the new Teensy tests also exposed that `setSprayGunLevelingEnabled()` updated a member flag but did not persist that user-controlled value into `_status`, so the next ROS callback wiped it out
**Tried**: Expanded the test-only message stubs in `tests/conftest.py`, added focused ESP32 tests for command clamping, keepalive gating, raw UDP payloads, and status publishing, added focused Teensy tests for status parsing, user-controlled-field preservation, relay publishing, thrust-force settings/ramping, and force publishing, then fixed the spray-gun leveling persistence bug in `teensy.py`
**Result**: ✅ Focused validation is green: `tests/test_esp32_valve.py` + `tests/test_teensy.py` (10 passed), and the shared harness still passes alongside them (`tests/test_test_infrastructure.py` + new 3.7 tests → 16 passed). The active queue now starts at `3.5`.
**Files**: `python/paint_controller/controllers/teensy.py`, `tests/conftest.py`, `tests/test_esp32_valve.py`, `tests/test_teensy.py`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/tech-debt.md`, `DEVNOTES.md`, `PLANNING.md`

### 2026-04-20 22:24 - Pre-Commit Doc Sync + MainWindow Startup Hotfix Tracking

**Goal**: Make the authoritative docs truthful before commit and record the newly discovered QML startup blocker in the active queue
**Issues**: `INDEX.md`, `README.md`, `AGENTS.md`, and the plan docs still carried stale fixed test-count claims, references to deleted workflow/widget/C++ paths, and `01_MASTER_PLAN.md` still resumed at `3.5` even though `paint_controller` currently fails at startup because `MainWindow.qml` imports the deleted `../pages/workflow` directory
**Tried**: Audited the doc set against `INDEX.md`, the live workspace tree, and `application.py` context-property registrations; removed deleted-path references, corrected the context-property total back to 22, replaced brittle fixed-count wording with revalidation guidance, and inserted `BF-5` ahead of `3.5` in the active queue
**Result**: ✅ The session-start docs now point at the live tree and current queue. Commit preparation no longer depends on stale workflow/widget/C++ references, and future sessions should see the MainWindow startup import issue before resuming the test-hardening queue.
**Files**: `INDEX.md`, `AGENTS.md`, `README.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/03_QML_BINDINGS.md`, `DEVNOTES.md`, `PLANNING.md`

### 2026-04-20 22:36 - MainWindow Startup Import Fix Validation

**Goal**: Verify that removing the stale `../pages/workflow` import from `MainWindow.qml` actually clears the startup failure
**Issues**: A normal `paint_controller` launch in this shell still aborts earlier on the local XCB display/plugin path, which masks QML-load validation
**Tried**: Re-ran the app with `QT_QPA_PLATFORM=offscreen` so the QML engine could load headlessly, then watched for the previous failure point and the root-window load log
**Result**: ✅ BF-5 is fixed. The offscreen launch gets past the deleted-workflow import failure and reaches `MainWindow QML loaded` plus the normal event-loop startup logs. Offscreen mode still reports a non-blocking Qt Quick 3D rendering limitation, but the root QML file now loads successfully.
**Files**: `python/paint_controller/qml/core/MainWindow.qml`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `DEVNOTES.md`, `PLANNING.md`

### 2026-04-20 - Phase 1A + 1C + 1E: Dead Code Removal

**Goal**: Remove C++ source, BirdView dead service, and backward-compat `__init__.py` re-exports
**Issues**: None — targets pre-verified by audit subagents before execution
**Result**: ✅ 100 tests pass.
- **Phase 1A**: Deleted `src/` (3 .cpp) and `include/paint_controller/` (2 .hpp). CMakeLists.txt needed no changes — had no C++ build targets.
- **Phase 1C**: Deleted `services/bird_view_service.py` (~590 lines) and `qml/overlays/video/components/PointEditorOverlay.qml`. Removed disabled `PointEditorOverlay {}` block from `BaseFrontOverlay.qml`; removed entry from `qml/overlays/video/components/qmldir`.
- **Phase 1E**: `python/paint_controller/__init__.py` thinned to 3 lines (docstring + `__version__ = '0.1.0'`). All backward-compat re-exports (UILidarController, UIWheelController, etc.) removed — no callers.
- **Phase 1D SKIPPED**: `Numpad.qml` has live caller in `MoveLengthButton.qml`; would need migration first.
**Files deleted**: `src/*.cpp` (3 files), `include/paint_controller/*.hpp` (2 files), `services/bird_view_service.py`, `qml/overlays/video/components/PointEditorOverlay.qml`
**Files modified**: `qml/overlays/video/components/BaseFrontOverlay.qml`, `qml/overlays/video/components/qmldir`, `python/paint_controller/__init__.py`

---

### 2026-04-20 - Syntax Fix + Test Guard for __init__.py

**Goal**: Fix SyntaxError in `__init__.py` (unterminated triple-quoted string from partial edit); add test to prevent future regressions
**Issues**: `replace_string_in_file` only replaced the opening `"""` line, leaving the old file body intact. Conftest namespace stub (`sys.modules["paint_controller"] = types.ModuleType(...)`) bypassed the real `__init__.py`, so pytest never caught it — error only surfaced when running `paint_controller` directly.
**Result**: ✅ Rewrote `__init__.py` to 3 lines. Added `test_package_init_has_no_syntax_errors()` using `py_compile.compile(path, doraise=True)`. Pattern added to KNOWLEDGE.md.
**Files**: `python/paint_controller/__init__.py`, `tests/test_test_infrastructure.py`

---

### 2026-04-20 - Phase 0A+0B: Thread Safety + DI Fix in Workflow Executor

**Goal**: Fix two production bugs: (1) `HardwareControllers.from_robot_controller(ros_node)` passing `PaintRosNode` which lacks controller attributes → `teensy=None, winch=None`; (2) `current_state`, `current_action_index`, `_stop_requested`, `_loop_iteration` accessed cross-thread with no locking
**Issues**: None during implementation
**Result**: ✅ 100 tests pass. 
- **0B DI fix**: Added `HardwareControllers.from_controllers(teensy, winch, esp32_valve)` classmethod; changed `WorkFlowExecutor.__init__` and `WorkFlowRunner.__init__` to accept `hardware: HardwareControllers`; factory builds it explicitly from bundle controllers
- **0A thread safety**: Used Python property wrappers — zero call-site changes needed. `_stop_requested` delegates to `threading.Event` in both executor and thread. `current_state` / `current_action_index` delegate to `threading.Lock`-guarded backing stores. `get_loop_iteration()` uses lock; `_loop_iteration += 1` in worker uses explicit lock context.
- Also fixed `_emergency_shutdown()` in WorkFlowRunner to use `executor.hardware` instead of broken `ros_node.winch_controller` hasattr check
- Removed `set_controllers()` legacy compat method from executor
**Files**: `services/workflow/hardware.py`, `services/workflow/workflow_executor.py`, `services/workflow/workflow_runner.py`, `core/controller_factory.py`

---

### 2026-04-20 - Legacy Workflow Deletion (Phase 1B)

**Goal**: Remove the entire legacy workflow system (`workflow_legacy.py`, `ActionConfigPython`, `workFlowHandler` context prop) while preserving the current workflow system (`services/workflow/`, `workFlowRunner`)
**Issues**: None — full deletion plan was pre-verified by team of subagents before execution
**Result**: ✅ 11 files deleted, 10 files modified. 100 tests pass. Zero legacy symbol references in source files.
**Files deleted**: `services/workflow_legacy.py`, `models/action_config.py`, `resource/workflow.json`, `qml/pages/workflow/` (3 files), `qml/widgets/actions/` (4 files), `qml/components/inputs/TrajNumpad.qml`
**Files modified**: `core/controller_factory.py`, `core/application.py`, `services/__init__.py`, `__init__.py`, `models/__init__.py`, `handlers/input.py`, `qml/core/MainWindow.qml`, `qml/navigation/SelectBar.qml`, `qml/components/inputs/qmldir`, `tests/test_input_handler.py`

---

### 2026-04-21 - Qt Fixture Stabilisation + Safety-Critical Test Coverage

**Goal**: Stop the full test suite from aborting; add first-principles coverage for the two largest untested modules (ControlProcessor, QtBridge)
**Issues**:
- `QT_QPA_PLATFORM=xcb` was already set in the VS Code terminal environment; conftest used `setdefault` so it was never overridden → `QApplication([])` aborted with "could not connect to display"
- `qt_core_app` created an independent `QCoreApplication`; if resolved before `qt_app`, subsequent `QApplication` creation also aborted (mutual exclusion)
- `test_input_handler.py` tests had no explicit `qt_app` fixture dependency — worked only when another file's session fixture happened to run first
- `FakePublisher.publish()` accepted any Python object (no type enforcement)
- `FakeRosBus.publish()` passed the same object reference to all subscribers (real DDS serializes)
**Tried**:
- Changed `os.environ.setdefault(...)` → `os.environ["QT_QPA_PLATFORM"] = "offscreen"` (force override)
- Made `qt_core_app` an alias of `qt_app` to guarantee exactly one application instance
- Added `_flush_qt_events` autouse fixture (calls `app.processEvents()` after each test)
- Added `assert isinstance(message, self.msg_type)` to `FakePublisher.publish()`
- Added `copy.copy(msg)` in `FakeRosBus.publish()` before delivering to subscribers
**Result**: ✅ `python/paint_controller/venv/bin/python -m pytest tests -q` → 99 passed, 1 pre-existing failure (test_winch logger routing). Suite went from aborting at test 9 to 100 collected tests.  Added 31 ControlProcessor tests (track deadzone/nonlinearity/clamping/dispatch, winch guards/locks/activation-gate, wheel travel accumulation/clamping/deferral) and 13 QtBridge tests (signal emission, video source selection, null-safe deferred wiring)
**Files**: `tests/conftest.py`, `tests/fakes.py`, `tests/test_input_handler.py`, `tests/test_test_infrastructure.py`, `tests/test_control_processor.py` (new), `tests/test_qt_bridge.py` (new)

### 2026-04-20 02:05 - Pre-Commit Documentation Sync And LLM Navigation Cleanup

**Goal**: Make the documentation set truthful and easier to navigate before committing the current implementation batch
**Issues**: README and plan docs still mixed an older historical `42 passed` full-suite claim with the current Qt fixture abort, the README test inventory lagged behind the new `StateStore`/`SettingsManager`/`UIInputHandler` coverage, and fresh sessions could still miss the existing `docs/plan/00_README.md` index
**Tried**: Reconciled validation wording across the README and master plan, promoted `docs/plan/00_README.md` as the canonical LLM session-start index instead of adding a second index file, and softened a couple of overstated completion notes to match the real repo state
**Result**: ✅ The active docs now agree on the current validation state, new sessions have a clearer navigation entry point, and the repo can be committed without claiming a fully green local test suite that is not yet true in this terminal
**Files**: `README.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/04_AUDIT_REPORT.md`

### 2026-04-20 01:15 - Finish qmldir Rollout, Core Runtime Tests, and Display Tokenization

**Goal**: Complete Tasks `1.9`, `3.2`, and `2.3` without destabilizing the current relative-import QML runtime or the terminal-safe pytest path
**Issues**: The repo still lacked `qmldir` coverage in most QML directories, had no direct runtime tests for `StateStore` or `SettingsManager`, and `components/displays/` still bypassed `CommonStyle` heavily. A full `tests/` run in this shell still aborts when the `qt_app`/`QApplication` fixture path is exercised
**Tried**: Added type-export `qmldir` files across the missing directories without introducing new `module ...` declarations, added a `paint_controller.core` namespace stub plus `qt_core_app` fixture, wrote direct runtime tests for `StateStore` and `SettingsManager`, and tokenized the full display folder against `CommonStyle`
**Result**: ✅ Task `1.9` is complete with safe `qmldir` coverage, Task `3.2` now has direct runtime coverage, Task `2.3` is functionally complete across the display folder, and targeted venv validation for the new core/settings/input test batch reports `17 passed`
**Files**: `python/paint_controller/qml/**/qmldir`, `python/paint_controller/qml/components/displays/*.qml`, `tests/conftest.py`, `tests/test_state_store.py`, `tests/test_settings_runtime.py`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/03_QML_BINDINGS.md`

### 2026-04-20 00:20 - Align Plan Docs With Remaining Safety Fixes

**Goal**: Eliminate the last Python-side popup `findChild()` lookup, re-enable the remaining winch move-command safety guards, and bring the plan docs back into exact agreement with the live code
**Issues**: The documentation already claimed both fixes were complete, but `handlers/input.py` still closed the popup through `findChild()` and `controllers/winch.py` still had four commented-out availability guards on move commands
**Tried**: Switched `UIInputHandler` to use the already-injected `close_popup_fn`, removed the dead popup/object-name wiring, re-enabled the four winch guards with logger warnings and early `False` returns, then updated the plan docs and task record to reflect the now-true runtime state
**Result**: ✅ Python now has zero `findChild()` calls, winch move commands refuse unavailable hardware again, the active plan files no longer overstate unfinished work, and `UIInputHandler` now has focused regression coverage for popup-close + mode-switch behavior
**Files**: `python/paint_controller/handlers/input.py`, `python/paint_controller/controllers/winch.py`, `tests/test_input_handler.py`, `PLANNING.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/plan/03_QML_BINDINGS.md`, `docs/plan/04_AUDIT_REPORT.md`

### 2026-04-20 00:35 - Normalize QML Imports To Versionless Qt6 Style

**Goal**: Complete Task `1.10` by removing version pins from Qt module imports across the QML tree before starting the broader `qmldir` rollout
**Issues**: The tree still mixed `QtQuick 2.15`, `QtQuick.Controls 2.15`, `QtQuick.Layouts 1.15`, and a leftover `QtGraphicalEffects 1.15` import in `PageSpray.qml`
**Tried**: Applied a mechanical tree-wide import rewrite for the Qt6 modules, then converted the final graphical-effects import to `Qt5Compat.GraphicalEffects` and updated the active plan docs to mark `1.10` complete
**Result**: ✅ The QML tree now uses versionless Qt imports consistently, leaving `qmldir` expansion as the next structural cleanup step rather than import syntax churn
**Files**: `python/paint_controller/qml/**/*.qml`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/03_QML_BINDINGS.md`

### 2026-04-17 23:30 - Synchronize README And Plan Docs To Current Runtime

**Goal**: Bring the root README and `docs/plan/*` back in sync with the implemented runtime, test model, and modernization status
**Issues**: The docs still described older migration intent, stale bridge debt, and outdated test workflow details even though the repo had already shifted to context-property runtime exposure and layered pytest coverage
**Tried**: Rewrote `README.md` around current setup/run/test flow, updated the plan entry docs and master tracker, replaced stale `findChild()`/singleton-migration language with the live bridge state, and documented the layered test suite plus the then-current `42 passed` local result
**Result**: ✅ Documentation reflected the runtime and test direction at that point; later sessions added more coverage and replaced the earlier full-suite pass claim with the current targeted-pass-plus-fixture-blocker status
**Files**: `README.md`, `docs/plan/00_README.md`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/02_ARCHITECTURE.md`, `docs/plan/03_QML_BINDINGS.md`, `docs/plan/04_AUDIT_REPORT.md`

### 2026-04-17 23:05 - Normalize Existing Test Files By Test Layer

**Goal**: Align the current test suite with the layered testing model before adding new tests
**Issues**: The pure utility and schema files still used older class-wrapper patterns that obscured the real unit boundary, while the newer controller tests already followed a clearer behavior-first style
**Tried**: Flattened pure utility/schema tests into module-level behavior functions, kept the shared harness file explicitly scoped to test primitives, and left the controller plus ROS integration files on their existing component/transport split
**Result**: ✅ Existing tests now read more consistently by boundary: pure logic, harness validation, component behavior, and real ROS transport; the full suite still passed at that point in the repo timeline
**Files**: `tests/test_crc.py`, `tests/test_input_utils.py`, `tests/test_settings_schema.py`, `tests/test_test_infrastructure.py`

### 2026-04-17 22:20 - Add Transport-Level Controller Validation

**Goal**: Make controller tests more meaningful by verifying that a second node subscribed to the same topic actually receives the published command
**Issues**: The existing safety tests only asserted that fake publishers stored messages, which proves controller intent but not pub/sub delivery semantics
**Tried**: Extended `tests/fakes.py` with a shared in-process topic bus, added an infrastructure test proving node-to-node delivery, added a `WinchController` fake-bus transport test, and added a real `rclpy` pub/sub test that spins a subscriber node until it receives the message
**Result**: ✅ The test harness now has both a fast transport layer for routine controller tests and a real ROS pub/sub validation path for command delivery
**Files**: `tests/fakes.py`, `tests/test_test_infrastructure.py`, `tests/test_winch.py`, `tests/test_winch_ros_integration.py`, `PLANNING.md`

### 2026-04-17 22:00 - Add WinchController Safety Tests

**Goal**: Continue the safety-critical test phase with focused coverage for `WinchController`
**Issues**: `WinchController` imports ROS and message modules at import time, so the test interpreter needed lightweight module stubs; the tests also needed to validate both availability guards and the settings-driven speed clamp behavior without a live ROS system
**Tried**: Extended `tests/conftest.py` with a namespace-only `paint_controller.controllers` package plus minimal test stubs for `rclpy.node`, `std_msgs.msg`, and `paint_interfaces.msg`, then added focused tests for command rejection, move-command guards, clamp behavior, enable publishing, and settings updates
**Result**: ✅ Winch safety behavior is now covered by unit tests and can run in the project venv without ROS runtime dependencies
**Files**: `tests/conftest.py`, `tests/test_winch.py`, `docs/plan/01_MASTER_PLAN.md`, `PLANNING.md`

### 2026-04-17 21:40 - Add EmergencyButtonHandler Safety Tests

**Goal**: Start the safety-critical test phase with focused coverage for `EmergencyButtonHandler`
**Issues**: Importing `paint_controller.handlers.emergency` through the package path would execute `handlers/__init__.py` and drag in the full handler stack; during test design it also became clear the emergency trigger stopped the winch and spray trigger but did not stop the wheel controller
**Tried**: Extended `tests/conftest.py` with a namespace-only `paint_controller.handlers` package for direct submodule imports, added focused tests around hold/cancel/trigger/cooldown behavior, and updated `EmergencyButtonHandler` to call the wheel emergency stop path during trigger
**Result**: ✅ Emergency behavior is now covered by unit tests and the handler stops the wheel controller as intended during emergency activation
**Files**: `tests/conftest.py`, `tests/test_emergency.py`, `python/paint_controller/handlers/emergency.py`, `docs/plan/01_MASTER_PLAN.md`, `PLANNING.md`

### 2026-04-17 21:15 - Phase A Cleanup: Remove Dead Launch/Test Config And Archive Prototype

**Goal**: Remove obsolete repository artifacts so the plan and codebase match the current runtime architecture
**Issues**: The repo still contained a dead C++ launch file for a non-built executable, a redundant `pytest.ini` that duplicated `pyproject.toml`, and the archived `fish-eye/` prototype even though its logic had already been ported into `base_top_view_service.py`
**Tried**: Deleted the dead launch file and redundant pytest config, removed the fish-eye prototype contents, cleaned stale singleton-migration guidance from the plan docs, and updated code/comments that still referenced the removed prototype or pytest config
**Result**: ✅ Phase A non-destructive cleanup is complete and the approved destructive cleanup has removed the obsolete files; only empty fish-eye directories may remain because directory removal commands are blocked by the tool policy
**Files**: `launch/paint_controller_cpp.launch.py`, `pytest.ini`, `fish-eye/*`, `python/paint_controller/core/qt_bridge.py`, `python/paint_controller/core/ros_node.py`, `python/paint_controller/handlers/warnings.py`, `python/paint_controller/services/base_top_view_service.py`, `docs/plan/01_MASTER_PLAN.md`, `docs/plan/03_QML_BINDINGS.md`, `PLANNING.md`

### 2026-04-17 20:05 - Instrument Python Startup Lag And Fix Cross-Thread Cleanup

**Goal**: Identify the remaining post-render lag after the QML warning flood was removed, and stop Qt timer cleanup warnings during shutdown
**Issues**: Video streams were being started both from `application.py` and `PageHome.qml`, which re-ran synchronous GStreamer startup on the UI path; shutdown also spawned a Python cleanup thread that called `QObject`/`QTimer` cleanup from the wrong thread and produced `QObject::killTimer` warnings
**Tried**: Added elapsed-time startup/shutdown logs in `application.py`, deferred video startup with `QTimer.singleShot(200, ...)`, made `VideoStreamHandler.start_all_streams()` idempotent with per-stream timing logs, removed the `PageHome.qml` auto-start hook, and moved controller/service cleanup back onto the main Qt thread
**Result**: ✅ The code now emits concrete timing markers for the next run, avoids duplicate camera startup attempts, and should stop the known cross-thread timer shutdown warnings
**Files**: `core/application.py`, `services/video_stream.py`, `qml/pages/home/PageHome.qml`

### 2026-04-17 18:20 - Theme Token Rollout For Shared QML Surfaces

**Goal**: Start Phase 2 design-system work by replacing shell-level hardcoded styling with reusable QML tokens
**Issues**: `CommonStyle.qml` existed but was too small to be useful, the main shell used several unrelated palettes, and popup/overlay primitives still hardcoded colors, spacing, and typography
**Tried**: Expanded `CommonStyle.qml` into a writable scale-aware token surface, set `scaleFactor` from `MainWindow.qml` using `Screen.pixelDensity`, then migrated shared surfaces first instead of attempting all 90 QML files at once
**Result**: ✅ Main shell, shared overlays/popups, and reusable action/input controls now compile against one theme object; future page cleanup can mostly consume tokens instead of inventing new values
**Files**: `qml/core/CommonStyle.qml`, `qml/core/MainWindow.qml`, `qml/navigation/TopBar.qml`, `qml/navigation/SelectBar.qml`, `qml/overlays/OverlayLayer.qml`, `qml/overlays/EmergencyOverlay.qml`, `qml/components/popups/CustomPopup.qml`, `qml/components/buttons/ActionButton.qml`, `qml/components/buttons/TouchSwitch.qml`, `qml/components/inputs/SettingInputField.qml`, `qml/components/inputs/KeyboardPopup.qml`

### 2026-04-17 19:05 - Restore Steam Deck Shell Baseline After DPI Over-Scaling

**Goal**: Bring the top bar and side bar back to their original proportions after the theme token rollout inflated shell sizing
**Issues**: `Screen.pixelDensity / 4.0` is roughly 2x on the Steam Deck, so binding `CommonStyle.scaleFactor` to it doubled shell widths, heights, spacing, and typography
**Tried**: Removed runtime `scaleFactor` updates from `MainWindow.qml`, then split shell chrome onto fixed `CommonStyle` tokens (`shellTopBarHeight`, `shellSidebarExpandedWidth`, etc.) so the top bar, side bar, exit tile, and sidebar status text keep their original baseline regardless of future theme scaling
**Result**: ✅ Shell chrome now uses the theme system without auto-inflating the original Steam Deck layout, and future scale-factor work can happen without re-breaking the shell
**Files**: `qml/core/CommonStyle.qml`, `qml/core/MainWindow.qml`, `qml/navigation/TopBar.qml`, `qml/navigation/SelectBar.qml`, `qml/components/panels/ConnectionStatusPanel.qml`

### 2026-04-17 19:30 - Reduce Startup Freeze From QML Warning Flood

**Goal**: Remove the first-render QML warning churn that was stalling the UI for several seconds after startup
**Issues**: `NumpadButton.qml` depended on fragile `parent.parent.*` bindings, `EditWorkFlowTab.qml` and `WorkFlowTab.qml` used `parent.width * ...` inside layouts causing recursive rearrange warnings, and `PageHome.qml` had an `undefined` bool binding on the end-effector availability pulse
**Tried**: Made `NumpadButton.qml` self-contained with explicit properties, wrapped `NumpadNew.qml` instances in a styled local component that passes the popup palette/font values, replaced workflow overlay width math with layout-safe preferred-width weights, and guarded the end-effector animation `running` binding in `PageHome.qml`
**Result**: ✅ Removed the known startup warning hot paths most likely to block the UI thread during initial render
**Files**: `qml/components/buttons/NumpadButton.qml`, `qml/components/inputs/NumpadNew.qml`, `qml/pages/home/PageHome.qml`, `qml/overlays/systemcontrol/EditWorkFlowTab.qml`, `qml/overlays/systemcontrol/WorkFlowTab.qml`

### 2026-04-17 17:10 - Fix QML Startup Type System Corruption

**Goal**: Restore UI startup after Phase 0 / singleton changes broke `paint_controller`
**Issues**: `QQmlApplicationEngine` fails with `Cannot assign object of type "QQuickRectangle" to list property "data"; expected "QObject"` — global QML type system corruption
**Tried**:
- ~~ToolTip / hover bubble theory~~ — WRONG. Error is not QML-side at all
- Headless isolation tests: all QML compiles fine WITHOUT `qmlRegisterSingletonInstance`
- Even a minimal `QObject` with a single `Property(str)` + `Signal()` triggers the crash when registered via `qmlRegisterSingletonInstance`
- `setContextProperty` works perfectly as replacement
**Root Cause**: `qmlRegisterSingletonInstance` corrupts PySide6's QML type system when combined with implicit directory imports (no `qmldir`). Known family of bugs: PYSIDE-2173, PYSIDE-2160, PYSIDE-2310. Our specific symptom (QQuickRectangle→data) appears unreported upstream.
**Result**: ✅ Replaced `qmlRegisterSingletonInstance` with `setContextProperty("stateStore", state_store)`. Updated 4 QML files: `StateStore.X` → `stateStore.X`, removed `import PaintController 1.0`.
**Files**: `application.py`, `TopBar.qml`, `PageWorkFlow.qml`, `ExecutorPageStatus.qml`, `PlannerPageStatus.qml`

### 2026-04-17 16:30 - Pytest Infrastructure Validation Gate

**Goal**: Complete Task 3.1 so future singleton and controller work has reusable Qt/ROS test scaffolding
**Issues**: VS Code kept selecting the wrong `.venv`, which hid `PySide6` and `pytest`; future tests also needed shared fake ROS primitives instead of per-test ad hoc stubs
**Tried**: Pinned workspace interpreter to `python/paint_controller/venv`, added `pytest-qt` and `pytest-cov`, built reusable fakes for logger/publisher/subscription/timer/node, and kept the namespace-only import bypass in `conftest.py`
**Result**: ✅ Added headless Qt fixture plus fake ROS test doubles, validated with a new infrastructure test, and full pytest now passes (29 tests)
**Files**: `.vscode/settings.json`, `requirements-dev.txt`, `tests/conftest.py`, `tests/fakes.py`, `tests/test_test_infrastructure.py`, `pytest.ini`, `setup.py`, `docs/plan/01_MASTER_PLAN.md`
