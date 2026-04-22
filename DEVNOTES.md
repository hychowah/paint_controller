# Development Notes

---
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
