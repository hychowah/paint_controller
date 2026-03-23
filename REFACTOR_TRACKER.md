# Refactor Tracker — Paint Controller PySide6/ROS2

> **Created**: 2026-03-20  
> **Purpose**: Track structural improvements from code review. Work is split into 3 phases by risk/effort.  
> **Usage**: Check off items as completed. Each phase can span multiple prompts/sessions.

---

## Current Status

| Phase | Items | Done | Status |
|-------|-------|------|--------|
| 1 — Quick Wins | 8 | 8 | **Complete** |
| 2 — Medium Effort | 8 | 8 | **Complete** |
| 3 — Major Refactor | 6 | 3 | **Partial** (3.1-3.3 done, 3.4-3.6 deferred) |
| 4A — Safety Fixes | 4 | 4 | **Complete** |
| 4B — Logging Sweep | 1 | 1 | **Complete** |

---

## Phase 1 — Quick Wins (Low Risk, High Impact)

Safe changes. No architectural shifts. Can be done file-by-file.

### 1.1 Create `constants.py` with enums ✅

- [x] **Create** `python/paint_controller/core/constants.py`
- [x] Define `ControlMode` enum (`BASE = "base"`, `END_EFFECTOR = "ef"`)
- [x] Define `JoystickControl` enum (all control mode strings: `"Track Control Left"`, `"Track Control Right"`, `"Winch Speed"`, `"EF Force"`, etc.)
- [x] Define `QmlObjectName` enum (`"messagePopup"`, `"selectBar"`, `"videoFullscreenOverlay"`, etc.)
- [ ] Define `HeartbeatStatus` enum (if not already a proper enum) — Deferred: already exists in application.py
- [x] Replace magic strings in `handlers/input.py`, `handlers/control_processor.py`

**Files affected**: New file + 2 existing files  
**Risk**: Low — string values unchanged, just sourced from enum

---

### 1.2 Fix L5/R5 double-press variable name bug ✅

- [x] **Fix** `handlers/input.py`: `on_l5_pressed()` and `on_r5_pressed()` used wrong variable names
- [x] Replaced manual time tracking with `DoublePressDetector` instances (combined with 1.7)
- [x] Bug eliminated by design — each button gets its own detector

**Files affected**: `handlers/input.py`  
**Risk**: Low — bug fix only, restores intended behavior  
**Severity**: HIGH — was broken functionality, now fixed

---

### 1.3 Harden `_emergency_shutdown()` in workflow runner ✅

- [x] ~~**Fix** method names~~ — VERIFIED: `setSpeed()` exists on WinchController (wraps `command_speed_rpm`), `setValveTurn()` exists on ESP32ValveController. Method names are correct.
- [x] Add error handling around emergency shutdown calls (try/except per controller call)
- [x] Log each controller stop independently so partial failures don't mask others

**Files affected**: `services/workflow/workflow_runner.py`  
**Risk**: Low — adds resilience to existing correct code

---

### 1.4 Extract `DeadzoneTracker` utility class ✅

- [x] **Created** `python/paint_controller/utils/input.py` with `DeadzoneTracker` class
- [x] Encapsulates: `in_deadzone`, `deadzone_start_time`, `should_send` state
- [x] Provides `update(value, deadzone_threshold) → should_send` method
- [x] Replaced 3 deadzone triplets in `control_processor.py` with `DeadzoneTracker` instances

**Files affected**: `handlers/control_processor.py`, new `utils/input.py`  
**Risk**: Low — internal refactor, external behavior unchanged

---

### 1.5 Add ROS2 publish helpers to `teensy.py` ✅

- [x] Add `_publish_float32(publisher, value)` helper method
- [x] Add `_publish_int32(publisher, value)` helper method
- [x] Add `_publish_bool(publisher, value)` helper method
- [x] Replaced 20+ repetitive `@Slot` methods with helper calls

**Files affected**: `controllers/teensy.py`  
**Risk**: Low — mechanical replacement, same behavior

---

### 1.6 Extract CRC utility from `esp32_valve.py` ✅

- [x] Created `utils/crc.py` with `crc8(data, polynomial=0x07, init=0xFF)` function
- [x] Removed duplicate CRC constants from `UDPReceiveThread` and `ESP32ValveController`
- [x] Both classes import shared `crc8()` function

**Files affected**: `controllers/esp32_valve.py`, new `utils/crc.py`  
**Risk**: Low — pure extraction

---

### 1.7 Extract `DoublePressDetector` utility ✅

- [x] Created `DoublePressDetector` in `utils/input.py` with configurable threshold (default 1.0s)
- [x] Provides `.press() → is_double_press` method
- [x] Replaced manual double-press tracking in `handlers/input.py` (3 instances: L5, R5, A)

**Files affected**: `handlers/input.py`, `utils/input.py`  
**Risk**: Low — simplifies and fixes existing logic (see 1.2)

---

### 1.8 Document `os._exit()` rationale ✅

- [x] **Reviewed** `core/application.py` line 73: `os._exit(1)` in signal handler — already has clear comment explaining it bypasses stuck cleanup
- [x] **Reviewed** line 901: `os._exit(0)` — already has preceding comment block explaining last-resort exit
- [x] Both are intentional and correctly documented. `os._exit()` is necessary because rclpy/Qt dual- loop can block `sys.exit()`

**Files affected**: None — existing comments are sufficient  
**Risk**: N/A — review-only, no code changes needed

---

## Phase 2 — Medium Effort (Moderate Risk)

Requires more careful testing. May touch multiple files per change.

### 2.1 Auto-generate settings properties from schema ✅

- [x] Define all settings in a single `_SETTINGS_SCHEMA` dict (type, default, min, max) at module level
- [x] Write `_make_setting_pair(key)` factory to generate `(Signal, Property)` from schema
- [x] Verify signal dispatch auto-populates via `getattr(self, f"{key}_changed")`
- [x] Removed ~195 lines of manual property boilerplate from `settings.py` (829→634 lines)
- [x] Verified QML bindings work after refactor

**Files affected**: `core/settings.py`
**Risk**: Medium — if property generation fails, QML bindings break silently  
**Test**: Verified every setting readable/writable from QML; 6 schema tests in `test_settings_schema.py`

---

### 2.2 Move ESP32 hardcoded config to config file ✅

- [x] Move MAC address (`1c:db:d4:40:30:c8`) from `esp32_valve.py` to config
- [x] Move fallback IP (`192.168.101.102`) to config
- [x] Created `python/config/esp32_valve.json` with MAC/IP/ports
- [x] Added fallback defaults via `_load_esp32_config()` with hardcoded fallbacks

**Files affected**: `controllers/esp32_valve.py`, `python/config/esp32_valve.json` (new)  
**Risk**: Low-Medium — config loaded at module level before controller init

---

### 2.3 Add thread locks to shared state ✅

- [x] **Settings**: Added `threading.Lock` (`_values_lock`) to `SettingsManager._values` access in `core/settings.py`
- [x] **Teensy status**: Added `threading.Lock` (`_status_lock`) to `_status` dict in `controllers/teensy.py`
- [x] **ESP32 socket**: Added `threading.Lock` (`_sock_lock`) around `self._sock` lifecycle in `controllers/esp32_valve.py`
- [x] Audited for shared mutable state — signals emitted OUTSIDE locks to prevent deadlocks

**Files affected**: `core/settings.py`, `controllers/teensy.py`, `controllers/esp32_valve.py`  
**Risk**: Medium — locks can introduce deadlocks if not careful  
**Pattern**: Acquire lock → copy/update state → release lock → emit signals with copied values

---

### 2.4 Improve input handler architecture — Deferred

- [ ] Create centralized button mapping table (button → action → mode)
- [ ] Replace 15+ individual `register_button_callback` calls with table-driven registration
- [ ] Use `ControlMode` enum (from 1.1) instead of string comparisons
- [ ] Consider state pattern for mode switching (replace if/else chains)

**Files affected**: `handlers/input.py`, `core/application.py`  
**Risk**: Medium — button behavior is safety-critical (emergency stop)  
**Deferred reason**: Works correctly after Phase 1 enums. 12 callbacks manageable. Low ROI.

---

### 2.5 Reduce `control_processor.py` `__init__` size ✅

- [x] Extracted `_setup_settings()` — loads from settings_manager + connects change signals
- [x] Extracted `_setup_constants()` — all scaling, deadzone, interval constants
- [x] Extracted `_setup_controls()` — ControlConfig dict + handler dispatch table
- [x] `__init__` reduced to 3 setup calls + controller refs

**Files affected**: `handlers/control_processor.py`  
**Risk**: Low-Medium — reorganization only

---

### 2.6 Teensy status dictionary → TypedDict ✅

- [x] Created `TeensyStatusDict(TypedDict)` with all 55+ fields typed
- [x] Dict preserved (QML `all_status` property needs dict access)
- [x] Added `_USER_CONTROLLED_FIELDS` tuple for 6 user-controlled fields
- [x] Fixed bug: `_status_callback` now preserves user-controlled fields instead of overwriting
- [x] Return types updated to `TeensyStatusDict` for IDE autocompletion

**Files affected**: `controllers/teensy.py`  
**Risk**: Medium — TypedDict chosen over dataclass to preserve QML dict compatibility

---

### 2.7 Add error handling to workflow emergency shutdown — Deferred

- [ ] Wrap each controller stop call in try/except
- [ ] Log failures but don't prevent other controllers from stopping
- [ ] Add timeout to prevent hang during emergency
- [ ] Verify all method names match actual controller APIs

**Files affected**: `services/workflow/workflow_runner.py`  
**Risk**: Low — adds resilience to critical path  
**Deferred reason**: Already hardened in Phase 1 (item 1.3).

---

### 2.8 Typed workflow action parameters — Deferred

- [ ] Create dataclasses for each action type's parameters (e.g., `WinchIncrementParams`, `ValveTurnParams`)
- [ ] Validate params at workflow load time, not execution time
- [ ] Replace `Dict[str, Any]` with typed params in action handlers

**Files affected**: `services/workflow/actions.py`, `services/workflow/workflow_executor.py`  
**Risk**: Medium — must handle backward compatibility with existing workflow JSON files  
**Deferred reason**: Functional as-is. Good Phase 3 item alongside DI.

---

## Phase 3 — Major Refactor (High Risk, Dedicated Branch)

Architectural changes. Must be done on a feature branch with thorough testing.

### 3.1 Split `RobotController` god class ✅

- [x] Extract `PaintRosNode(Node)` in `core/ros_node.py` — pure ROS2 pub/sub, no Qt
- [x] Extract `QtBridge(QObject)` in `core/qt_bridge.py` — bridges ROS signals to Qt/QML
- [x] Extract `StateStore(QObject)` in `core/state_store.py` — shared mutable state as Qt properties
- [x] Extract `ControllerFactory` in `core/controller_factory.py` with `ControllerBundle` dataclass
- [x] Rewrite `main()` to orchestrate: factory → node → bundle → QML → app.exec()
- [x] Old `RobotController` class retained as dead code (cleanup pending)

**Files affected**: `core/application.py` (main rewrite), 4 new `core/` files, 14+ controller constructors  
**Risk**: HIGH — mitigated by strangler pattern and systematic review  
**Commit**: `2cd0ae2` on `refactor/phase3-core-split`

---

### 3.2 Introduce dependency injection ✅

- [x] Controllers receive only the interfaces they need (not the entire RobotController)
- [x] Wire dependencies in `ControllerFactory` via `ControllerBundle` dataclass
- [x] Break circular imports — all controllers take explicit deps in `__init__`
- [ ] Define protocol/ABC interfaces for each dependency type (deferred)

**Files affected**: All 14 controllers, handlers, services — constructor signatures updated  
**Risk**: HIGH — mitigated by systematic controller-by-controller update  
**Commit**: `2cd0ae2` on `refactor/phase3-core-split`

---

### 3.3 Separate ROS2 thread from Qt event loop ✅

- [x] ROS2 node runs in its own thread via `RosThread` (pre-existing)
- [x] Communication via thread-safe Qt signals only — `StateStore` is the signal hub
- [x] No direct ROS2 API calls from Qt main thread — `QtBridge` handles UI actions
- [x] Clean shutdown: stop ROS thread → stop Qt loop

**Files affected**: `core/application.py`, `core/ros_node.py` (new), `core/state_store.py` (new)  
**Risk**: HIGH — mitigated by keeping existing `RosThread` pattern  
**Commit**: `2cd0ae2` on `refactor/phase3-core-split`

---

### 3.4 Add unit test infrastructure

- [ ] Create `tests/` directory with `conftest.py`
- [ ] Add pytest + pytest-qt to requirements
- [ ] Create mock ROS2 node for testing
- [ ] Write tests for `SettingsManager` (easiest target)
- [ ] Write tests for `DeadzoneTracker`, `DoublePressDetector` (extracted utilities)
- [ ] Write tests for `ControlProcessor` (with mocked controllers)

**Files affected**: New `tests/` directory  
**Risk**: Low (additive only)  
**Prerequisite**: 3.2 (DI) makes testing much easier, but Phase 1 utilities can be tested immediately

---

### 3.5 QML module organization

- [ ] Register QML types via `qmlRegisterType` instead of `setContextProperty`
- [ ] Create proper QML module with `qmldir` file
- [ ] Replace `findChild()` with proper QML type imports
- [ ] Eliminate hardcoded QML `objectName` lookups

**Files affected**: `core/application.py`, all QML files  
**Risk**: HIGH — QML registration model change

---

### 3.6 Logging standardization

- [ ] Replace all `print()` calls with `logging.getLogger(__name__)`
- [ ] Configure log levels per module
- [ ] Add structured logging for hardware events
- [ ] Route ROS2 logger through Python logging (or vice versa)

**Files affected**: All Python files  
**Risk**: Low — but tedious, many files to touch

---

## Phase 4A — Safety Fixes (P0 Critical)

Post-Phase 3 review identified thread safety, null-check, and dead code issues.

### 4A.1 Add thread locks to StateStore ✅

- [x] Added `threading.Lock` (`_lock`) to all 8 property getters and setters
- [x] Signals emitted **outside** the lock to prevent deadlocks (KNOWLEDGE.md pattern)
- [x] For compound properties (left/right control info), both mode + value captured inside lock before emitting

**Files affected**: `core/state_store.py`  
**Risk**: Low — additive change, same pattern as `SettingsManager._values_lock`

---

### 4A.2 Fix emergency.py null-checks + dead code ✅

- [x] Verified existing null-checks on `_show_popup_fn` and `_logger` in `_trigger_emergency()` are correct
- [x] Removed dead `_stop_all_motors()` method — was never called from any code path
- [x] Emergency stop correctly stops winch + spray trigger; wheel stop not needed (tracks are gravity-locked)

**Files affected**: `handlers/emergency.py`  
**Risk**: Low — dead code removal only

---

### 4A.3 Add null-checks to ssh.py `_show_popup_fn` ✅

- [x] Added `if self._show_popup_fn:` guards on 5 unprotected call sites:
  - `update_device_config()` success popup
  - `update_device_config()` failure popup
  - `update_device_config()` exception popup
  - `handle_device_command()` initial popup
  - `handle_device_command()` callback popup

**Files affected**: `controllers/ssh.py`  
**Risk**: Low — prevents crash when `show_popup_fn=None`

---

### 4A.4 Protect `_last_input_time` in steam_deck.py ✅

- [x] Added `threading.Lock` (`_last_input_time_lock`) — separate from existing `QMutex` to avoid mixing lock types
- [x] Protected 4 access points: init, start(), `_process_input()` (writer), `_check_availability()` (reader)
- [x] Added `import threading` to module

**Files affected**: `handlers/steam_deck.py`  
**Risk**: Low — narrow lock scope (single float read/write)

---

## Phase 4B — Logging Sweep (P1 Observability)

Replace ~214 bare `print()` calls across 18 production files with `logging.getLogger(__name__)`.

### 4B.1 Replace print() with logging across all production files ✅

- [x] **Controllers** (7 files): winch.py (24), ssh.py (22), wheel.py (8), teensy.py (5), system_monitor.py (2), lidar.py (2), esp32_valve.py (2)
- [x] **Handlers** (3 files): steam_deck.py (24), control_processor.py (16 active), input.py (3)
- [x] **Services** (4 files): video_stream.py (23), ros_bag_recorder.py (22), screen_recorder.py (19), workflow_legacy.py (1)
- [x] **Core/UI/Widgets** (4 files): application.py (15 of 18 — 3 signal handler prints kept), settings.py (7), overlay.py (2), vtk_pointcloud.py (9)
- [x] Pattern: module-level `logger = logging.getLogger(__name__)` with lazy `%s` formatting
- [x] Files with existing ROS logger (`self._node.get_logger()`) keep that pattern (teensy.py)
- [x] Signal handler `print()` in application.py intentionally preserved (logging not signal-safe)
- [x] Class-name prefixes like `[SSHLauncher]` stripped (redundant with `__name__` logger)

**Files affected**: 18 production files  
**Risk**: Low — output-only change, no logic modification  
**Tests**: All 28 tests pass

---

## Code Smells Reference (Quick Lookup)

| ID | File | Line(s) | Issue | Phase |
|----|------|---------|-------|-------|
| S01 | `core/application.py` | 178-880 | God class `RobotController` | 3.1 |
| S02 | `core/application.py` | 205-360 | 150-line `__init__` | 3.1 |
| S03 | `core/application.py` | 73, 901 | `os._exit()` bypasses cleanup | 1.8 |
| S04 | `core/settings.py` | 530-721 | ~~190 lines of property boilerplate~~ Fixed (2.1) | 2.1 |
| S05 | `core/settings.py` | 401-420 | ~~Signal map completeness~~ Fixed (2.1) | 2.1 |
| S06 | `handlers/input.py` | 45-59 | Wrong variable names (L5→L1, R5→R1) | 1.2 |
| S07 | `handlers/input.py` | 140-180 | Magic string control modes | 1.1 |
| S08 | `handlers/control_processor.py` | 38-51 | Triplicated deadzone state | 1.4 |
| S09 | `handlers/control_processor.py` | 30-180 | ~~150-line `__init__`~~ Fixed (2.5) | 2.5 |
| S10 | `controllers/teensy.py` | 52-115 | ~~63-line status dict init~~ TypedDict added (2.6) | 2.6 |
| S11 | `controllers/teensy.py` | 618-690 | Duplicate thrust logic | 1.5 |
| S12 | `controllers/teensy.py` | 300-500 | 30 identical publish methods | 1.5 |
| S13 | `controllers/esp32_valve.py` | 144-145 | ~~Hardcoded MAC/IP~~ Externalized to JSON (2.2) | 2.2 |
| S14 | `controllers/esp32_valve.py` | 45-46,138-139 | Duplicate CRC constants | 1.6 |
| S15 | `controllers/esp32_valve.py` | socket | ~~Shared socket, no lock~~ Fixed (2.3) | 2.3 |
| S16 | `services/workflow/workflow_runner.py` | 387,391 | ~~Wrong method names~~ VERIFIED CORRECT — needs try/except | 1.3 |
| S17 | Multiple files | — | Magic strings (no enums) | 1.1 |
| S18 | Multiple files | — | ~~No thread locks on shared state~~ Fixed (2.3) | 2.3 |
| S19 | `core/state_store.py` | all | No thread locks on StateStore properties | 4A.1 |
| S20 | `handlers/emergency.py` | 95-119 | Dead `_stop_all_motors()` never called | 4A.2 |
| S21 | `controllers/ssh.py` | 251,272,281,293,315 | `_show_popup_fn` called without null-check | 4A.3 |
| S22 | `handlers/steam_deck.py` | 189,251,429 | `_last_input_time` cross-thread without lock | 4A.4 |

---

## Bugs Found During Review

| ID | Severity | File | Description | Phase | Fixed |
|----|----------|------|-------------|-------|-------|
| B01 | **HIGH** | `handlers/input.py:45-59` | L5/R5 double-press uses wrong variable names | 1.2 | [x] |
| B02 | ~~HIGH~~ | `workflow_runner.py:387` | ~~Method names wrong~~ VERIFIED CORRECT — `setSpeed()` exists (wraps `command_speed_rpm`) | 1.3 | [x] |
| B03 | ~~MEDIUM~~ | `core/application.py:73,901` | `os._exit()` is intentional — documented | 1.8 | [x] |
| B04 | **MEDIUM** | `esp32_valve.py` | Socket shared across threads without lock | 2.3 | [x] |
| B05 | **LOW** | `core/settings.py` | `ui_section_states` has no signal/property | 2.1 | [x] |
| B06 | **HIGH** | `core/state_store.py` | No thread lock — concurrent ROS/Qt access | 4A.1 | [x] |
| B07 | **MEDIUM** | `handlers/emergency.py` | Dead `_stop_all_motors()` + missing null-checks | 4A.2 | [x] |
| B08 | **MEDIUM** | `controllers/ssh.py` | `_show_popup_fn` crashes if None | 4A.3 | [x] |
| B09 | **MEDIUM** | `handlers/steam_deck.py` | `_last_input_time` race condition | 4A.4 | [x] |

---

## Session Log

Track what was done in each prompt/session.

### Session 1 — 2026-03-20 (Code Review)

- Completed full architectural review of Python/PySide6 codebase
- Identified 18 code smells, 5 bugs, 3 phases of work
- Created this tracker document

### Session 2 — 2026-03-20 (Phase 1 Implementation)

- Phase: 1 — Quick Wins
- Items completed: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8 (all 8)
- New files created:
  - `python/paint_controller/core/constants.py` — ControlMode, JoystickControl, QmlObjectName enums
  - `python/paint_controller/utils/__init__.py` — package init
  - `python/paint_controller/utils/crc.py` — shared CRC8 function
  - `python/paint_controller/utils/input.py` — DoublePressDetector, DeadzoneTracker
- Files modified:
  - `handlers/input.py` — fixed B01 bug, uses enums + DoublePressDetector
  - `handlers/control_processor.py` — uses DeadzoneTracker + JoystickControl enum
  - `controllers/esp32_valve.py` — uses shared crc8()
  - `controllers/teensy.py` — publish helpers replace 20+ boilerplate methods
  - `services/workflow/workflow_runner.py` — per-controller try/except in emergency shutdown
- Bugs fixed: B01 (L5/R5 wrong variable), B03 reclassified (os._exit is intentional)
- Post-fix: Moved `constants.py` from `core/` → `utils/` to resolve circular import chain. Updated imports in `handlers/input.py` and `handlers/control_processor.py`.
- Notes: Phase 1 complete. Ready for Phase 2.

### Session 3 — 2026-07-17 (Phase 2 Implementation)

- Phase: 2 — Medium Effort
- Items completed: 2.1 (B1), 2.2 (C1), 2.3 (A1+A2), 2.5 (C2), 2.6 (B2)
- Items deferred: 2.4 (low ROI), 2.7 (done in Phase 1), 2.8 (Phase 3 candidate)
- New files created:
  - `python/config/esp32_valve.json` — ESP32 hardware config
  - `tests/conftest.py` — namespace-bypass for test imports
  - `tests/pytest.ini` — pytest configuration
  - `tests/test_crc.py` — 8 CRC8 tests
  - `tests/test_input_utils.py` — 14 input utility tests
  - `tests/test_settings_schema.py` — 6 schema validation tests
- Files modified:
  - `controllers/esp32_valve.py` — socket lock, QueuedConnection, JSON config loading
  - `controllers/teensy.py` — TeensyStatusDict, status lock, user-field preservation bug fix
  - `core/settings.py` — values lock, _SETTINGS_SCHEMA, _make_setting_pair() factory (829→634 lines)
  - `handlers/control_processor.py` — valve_turn scale fix, init extracted to 3 setup methods
- Bugs fixed: B04 (socket thread safety), B05 (schema completeness)
- Critical bug found & fixed: Teensy user-controlled fields (relay_enabled, etc.) overwritten on every ROS message
- Notes: Phase 2 complete. 28 tests all passing.

### Session 4 — 2026-03-23 (Phase 4A — Safety Fixes)

- Phase: 4A — Safety Fixes (P0 Critical)
- Items completed: 4A.1 (StateStore locks), 4A.2 (emergency.py cleanup), 4A.3 (ssh.py null-checks), 4A.4 (steam_deck.py lock)
- Files modified:
  - `core/state_store.py` — Added `threading.Lock` to all 8 property getters/setters; signals emitted outside lock per KNOWLEDGE.md pattern
  - `handlers/emergency.py` — Removed dead `_stop_all_motors()` method (never called); existing null-checks on `_show_popup_fn`/`_logger` verified correct
  - `controllers/ssh.py` — Added `if self._show_popup_fn:` guards on 5 unprotected call sites
  - `handlers/steam_deck.py` — Added `threading.Lock` for `_last_input_time` (4 access points); added `import threading`
- Bugs fixed: B06 (StateStore race), B07 (dead emergency code), B08 (ssh popup crash), B09 (steam_deck race)
- Tests: All 28 existing tests pass
- Notes: Phase 4A complete. Next: Phase 4B (logging sweep).

### Session 5 — 2026-07-21 (Phase 4B — Logging Sweep)

- Phase: 4B — Logging Sweep (P1 Observability)
- Items completed: 4B.1 (replace ~214 print() calls with logging across 18 files)
- Files modified (Batch 1 — Controllers):
  - `controllers/winch.py` — 24 prints → logging
  - `controllers/ssh.py` — 22 prints → logging, stripped class-name prefixes
  - `controllers/wheel.py` — 8 prints → logging
  - `controllers/teensy.py` — 5 prints → `self._node.get_logger()` (ROS pattern)
  - `controllers/system_monitor.py` — 2 prints → logging
  - `controllers/lidar.py` — 2 prints → logging
  - `controllers/esp32_valve.py` — 2 prints → logging
- Files modified (Batch 2 — Handlers):
  - `handlers/steam_deck.py` — 24 prints → logging
  - `handlers/control_processor.py` — 16 active prints → logging
  - `handlers/input.py` — 3 prints → logging
- Files modified (Batch 3 — Services):
  - `services/video_stream.py` — 23 prints → logging (+ `_log()` fallback updated)
  - `services/ros_bag_recorder.py` — 22 prints → logging
  - `services/screen_recorder.py` — 19 prints → logging
  - `services/workflow_legacy.py` — 1 print → logging
- Files modified (Batch 4 — Core/UI/Widgets):
  - `core/application.py` — 15 prints → logging (3 signal handler prints preserved)
  - `core/settings.py` — 7 prints → logging
  - `ui/overlay.py` — 2 prints → logging
  - `widgets/vtk_pointcloud.py` — 9 prints → logging
- Tests: All 28 pass
- Notes: Phase 4B complete. All production print() replaced except signal handlers.
