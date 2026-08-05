# Level C — Pure-Python Device HAL (Durable Plan)

**Status**: Full Level C program in progress — **P0–P4 landed**  
**Saved**: 2026-08-05  
**Last refreshed**: 2026-08-05 (P4 Teensy pure HAL landed)  
**Depends on**: Level A (`@Slot` strip) and Level B (`Property` → `@property`) — **both landed**  
**Do not overwrite** this file with concurrency-test or feature plans; those are separate tracks. Refresh this file when Level C scope or prerequisites change.

---

## Understanding

After Levels A+B, device adapters no longer expose QML `@Slot` / Qt `Property`. They still **are** Qt objects (`QObject`, `Signal`, `QTimer`, `RosTelemetryBridge` parenting). Level C would make ROS/device HAL classes plain Python implementing `ports/*`, with Qt confined to presentation and composition-owned I/O shells.

**Complexity**: High for full package purity; Low–Med for a partial/pilot path.

**Cross-layer impact**: High if full strip (Status, SignalWiring, factory, ESP32 transport). Partial can be contained.

---

## Prerequisites before any Level C code

### Landed (do not re-discover)

| Item | Status | Commit / location |
|---|---|---|
| Level A — strip device `@Slot` | Done | `5b225cc` |
| Level B — retire device Qt `Property` | Done | `5c722c9` |
| Structural bans (slots / properties) | Done | `tests/test_device_adapter_no_qml_slots.py`, `tests/test_device_adapter_no_qml_properties.py` |
| Concurrency lock pack (ROS↔Qt / bus) | Done | `7e5f78c` |

Level C moves affinity/notify ownership. **Green full suite alone is not enough** — keep the concurrency band below green after each Level C slice.

### Frozen bar (Level C seam gate — do not infinite-audit)

Level C work on marshal/mailbox/status-apply seams is allowed when this bar stays green:

1. ROS status apply only on main for **wheel / winch / teensy** (worker callback + `processEvents` / apply thread-id).
2. Bound `command_bus` → **no raw publish until `pump`** (wheel continuous; winch continuous).
3. Concurrent **pump ↔ continuous enqueue** and **invalidate under load** do not crash; mailbox semantics hold.
4. Halt **latch** blocks ControlProcessor re-command (`continuous_motion_allowed`).
5. Wind residual is **documented** (fence test); not required fixed before P0/Lidar pilot.
6. Device adapter structural bans (no public `@Slot` / Qt `Property` on HAL classes) still pass.

**Explicitly not required** before starting P0 or a Lidar pilot:

- Perfect “halt zeros win under live pump + teleop” content proof (open residual / product design note below).
- ESP32 real-thread affinity stress (unless a phase touches ESP32 transport).
- Open-ended re-audits with “always add must-haves.”

### Focused regression command

```bash
python/paint_controller/venv/bin/python -m pytest \
  tests/test_ros_telemetry.py \
  tests/test_ros_io.py \
  tests/test_ros_node.py \
  tests/test_wheel.py \
  tests/test_winch.py \
  tests/test_teensy.py \
  tests/test_concurrency_product_paths.py \
  tests/test_device_adapter_no_qml_slots.py \
  tests/test_device_adapter_no_qml_properties.py \
  -q --tb=short

# After Status / wiring / factory changes also:
python/paint_controller/venv/bin/python -m pytest \
  tests/test_notify_contracts.py \
  tests/test_status_schema_integrity.py \
  tests/test_safety_coordinator.py \
  -q --tb=short

# Gate before merge
python/paint_controller/venv/bin/python -m pytest tests -q
```

---

## Audit summary (code-only, 2026-08-05; still accurate)

### Qt remaining on adapters

| Device | Qt load | Pain |
|---|---|---|
| **ESP32** | `QThread`, 3×`QTimer`, QueuedConnection discovery `@Slot`, many Signals | Highest (transport) |
| **Teensy** | Signals, availability timer, thrust ramp `QTimer`, RosTelemetryBridge, settings Signal fan-in | High |
| **Wheel / Winch** | Signals, base availability timer, RosTelemetryBridge | Med |
| **Lidar** | 2 Signals + 2 bridges | Low–Med — **preferred first pure pilot** |
| **Wind** | 2 Signals; emits from ROS spin (no bridge); not on production QML | Optional pilot / residual fence exists |
| **SSH / SystemMonitor** | Heavy Qt | **OUT of Level C device HAL** |

### Who still needs device Signals

- `SimpleDeviceStatus` / `TeensyStatus` via `connect_required`
- Shell façades: winch `available_changed`, teensy `connection_changed`, winch `motor_voltage_changed`
- Safety: wheel `error_state_changed` → `SignalWiring`
- Tests: notify contracts, device unit tests with `processEvents`

QML does **not** bind raw device controllers (Actions/Status only).

### RosTelemetryBridge / RosStatusController

- Bridges parented to adapters (`parent=self`) on teensy/wheel/winch/lidar
- Availability is QObject + `QTimer` in `RosStatusController`
- Pure HAL needs external bridge parent + external availability watchdog

### Design hazard (not Level C P0 blocker)

`WheelController.emergency_stop` uses **continuous** zero (last-wins overwritable by later `command_speed`). Do **not** silently change halt traffic kind in P3 without a product decision + explicit tests. Concurrency pack documents mailbox vs product halt limits; full live e-stop content under concurrent pump remains open residual.

---

## Independent auditor recommendation

| Choice | Verdict |
|---|---|
| **Full Level C now** | **Not recommended** — multi-PR, high risk, little user-facing upside after A+B |
| **Defer entirely** | Acceptable product-wise; residual: bridge parenting, Wind residual, continuous-zero e-stop design |
| **Partial (recommended if any Level C)** | **P0**, then **Lidar pilot**; optional Wind fix/quarantine; leave Teensy/ESP32 until hard requirement |

A+B already harvested the dual-role win. Remaining Qt is **affinity + notification transport**, which the app still needs *somewhere*.

---

## Target architecture (end-state)

```text
ports/* + plain adapters          # no PySide6
        │ mutate state + notifier.notify(name)
        ▼
DeviceTelemetryProxy / IoShell (QObject)   # Signals, QTimer, RosTelemetryBridge parent
        │
        ▼
*Status / *Actions / SignalWiring / QML    # unchanged contracts
```

**Notification strategy**: composition-owned **Qt telemetry proxy** (preserve Status signal names; adapter mutates + notifies). Avoid polling. Avoid a second non-Qt bus while the app remains Qt-centric.

**ESP32 exception**: split pure protocol/HAL from **transport shell** (`QThread`/timers stay).

**Must remain QObject even after full Level C**: `*Status`/`*Actions`, `RosTelemetryBridge`, timer hosts, ESP32 transport, SettingsManager, SSH/SystemMonitor, SignalWiring/QtBridge, etc.

---

## Phases

### P0 — Seams only (Low) — **LANDED 2026-08-05**

**Work**

- Introduce `DeviceNotifier` Protocol (duck-typed notify / signal mirror).
- Allow `RosTelemetryBridge(parent=shell)` where shell ≠ adapter (no behavior change required for all devices at once).
- Unit/contract tests for notifier + external bridge parent if production path not yet switched.

**Landed**

| Piece | Location |
|---|---|
| `DeviceNotifier` + Null/Recording | `ports/notifier.py` (Protocol exported from `ports`) |
| `SignalDeviceNotifier` | `core/device_notifier.py` |
| Bridge parent docs | `core/ros_telemetry.py` (parent = lifetime/shell owner) |
| Tests | `tests/test_device_notifier.py`; external-shell parent apply in `tests/test_ros_telemetry.py` |

Production controllers still parent bridges on adapters (unchanged). No QML / factory rewires.

**Acceptance (measurable)**

1. Protocol exists and is importable without circular deps on controllers. ✅
2. At least one construction path (test or pilot) uses bridge with **external** parent. ✅ (test)
3. Frozen concurrency bar + full suite green. ✅ (`545 passed`)
4. No QML / `CONTEXT_PROPERTIES` contract change. ✅

### P1 — Pilot pure HAL (Low–Med) — **LANDED 2026-08-05 (Lidar)**

**Primary: Lidar**

- Plain adapter + composition proxy for `distance_changed` / `angle_changed`.
- `LidarStatus` keeps QML names; wiring may attach to proxy for Signals and adapter for fields (or proxy forwards getattr).
- Structural ban: `lidar.py` imports no PySide6 after pilot.

**Landed**

| Piece | Location |
|---|---|
| Pure HAL | `controllers/lidar.py` (`LidarHal`, no PySide6) |
| Qt shell | `controllers/lidar_shell.py` (`LidarController` + bridges + `SignalDeviceNotifier`) |
| Factory | imports shell `LidarController` |
| Tests | `tests/test_lidar_pure_hal.py`, `tests/test_pure_hal_no_pyside.py` |

**Why Lidar first**

- Already on `RosTelemetryBridge` + `LidarStatus` + production QML path.
- Small surface (2 signals).
- Higher proof value than Wind (Wind not on production QML context).

**Wind (optional / second)**

- Residual fence: `tests/test_concurrency_product_paths.py::test_wind_monitor_residual_mutates_on_calling_thread`.
- Choose explicitly: (a) fix affinity + pure HAL, (b) delete/quarantine if unused, or (c) leave residual until after Lidar proof.
- Do **not** treat Wind as the default “best pilot” without that choice.

**Acceptance**

1. Pilot module(s) have no PySide6 imports (allowlist none for pure HAL file).
2. Status / notify contracts green; concurrency band green.
3. Full suite green.

### P2 — Availability + bridge ownership (Med) — **LANDED 2026-08-05**

- Non-Qt availability state core (extract from `RosStatusController`).
- `AvailabilityWatchdog(QObject)` at composition or per-shell.
- Reparent bridges off adapters for ROS devices that use the bridge.
- Adapters may still temporarily hold Signals until P3.

**Landed**

| Piece | Location |
|---|---|
| Pure state | `core/availability.py` (`AvailabilityState`) |
| Watchdog | `core/availability_watchdog.py` |
| Shell parent | `core/device_io_shell.py`; `RosStatusController` + wheel/winch/teensy bridge parent |
| Tests | `tests/test_availability_p2.py` |

**Acceptance**: availability still timeouts correctly under unit tests; bridges parented to shells; frozen bar + full suite green. ✅

### P3 — Winch + Wheel pure (Med) — **LANDED 2026-08-05**

- Proxy emits Status schema signals + wheel `error_state_changed`.
- Settings max-speed inject without adapter `.connect` to SettingsManager Signals.
- Halt traffic kind: **no silent change** (see design hazard).

**Landed**: pure `wheel.py`/`winch.py`; shells `wheel_shell.py`/`winch_shell.py`; continuous-zero e-stop retained.

**Acceptance**: Status/shell/safety notify paths green; bound bus + worker affinity tests green. ✅

### P4 — Teensy pure (High) — **LANDED 2026-08-05**

- Status dict + intent signals + thrust ramp timer on shell.
- Settings fan-in extraction.
- videoRuntime / shell connectivity still work.

**Landed**: pure `teensy.py` (`TeensyHal`); `teensy_shell.TeensyController` owns Signals/bridge/watchdog/thrust timer/settings.

### P5 — ESP32 split (High)

- Pure protocol + HAL (`setValveTurn`, status apply).
- Transport QObject (thread, discovery, timers) remains.
- `ValveStatus` wires to shell/proxy.

### Closeout

- AST/import ban: pure HAL modules no PySide6 (allowlist transport modules).
- Update decision log; optional DEVNOTES one-liner.

---

## Non-goals

- Changing QML `*Status`/`*Actions` contracts
- Polling Status from a global timer
- Folding SSH/SystemMonitor into device purity
- Renaming producer signal names without full Status rewire
- Full non-Qt event bus while app is Qt-wide
- Re-opening open-ended concurrency audit loops before each phase (use frozen bar)

## Stop-and-ask

- Full vs partial vs defer (product choice at session start)
- Wind: fix vs quarantine vs leave residual
- Package rename (`controllers/` → adapters + transport)
- Teensy thrust timing changes without soak
- Changing wheel emergency_stop from continuous zero to oneshot sticky zero
- High-complexity P4/P5 without successful P0 + Lidar pilot proof

## Acceptance

**Partial (recommended program slice):**

1. P0 acceptance met.
2. Lidar pilot pure (or explicit alternate pilot) green.
3. P3–P5 deferred and still documented here.
4. Frozen concurrency bar green; full suite green.

**Full Level C:**

1. teensy/wheel/winch/lidar (+ optional wind) have **zero** PySide6 imports.
2. ESP32 transport shell is the only Qt near valve.
3. All Status/safety/façade contracts green.
4. Structural ban on pure HAL modules.
5. Full pytest green.

## Rollback

Per-phase restore of adapters/factory/proxy; no ROS msg migration.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-08-05 | Levels A+B landed (`5b225cc`, `5c722c9`) |
| 2026-08-05 | Full Level C **not** started; plan saved before concurrency-test track |
| 2026-08-05 | Concurrency lock pack landed (`7e5f78c`); frozen bar defined for Level C seam gate |
| 2026-08-05 | Plan refresh: Lidar preferred P1 pilot; Wind optional; prerequisites + validation commands |
| 2026-08-05 | User chose **P0 only** this session (not full program; not auto-P1) |
| 2026-08-05 | **P0 landed**: `DeviceNotifier`, `SignalDeviceNotifier`, external-shell bridge test path; no production adapter rewires |
| 2026-08-05 | **P1 landed**: Lidar pure HAL + shell; factory uses `lidar_shell.LidarController`; PySide ban on `lidar.py` |
| 2026-08-05 | **P2 landed**: AvailabilityState + AvailabilityWatchdog + DeviceIoShell; wheel/winch/teensy bridges parented to shells |

---

## Related

| Item | Ref |
|---|---|
| Level A | `5b225cc` — Strip QML `@Slot` from device HAL adapters |
| Level B | `5c722c9` — Retire Qt Property on device HAL adapters |
| Concurrency pack | `7e5f78c` — tests under `tests/test_ros_*.py`, `test_concurrency_product_paths.py`, device affinity tests |
| Structural bans | `tests/test_device_adapter_no_qml_slots.py`, `tests/test_device_adapter_no_qml_properties.py` |
| Production seams | `core/ros_io.py` (TD-054), `core/ros_telemetry.py` (TD-056), `core/ros_node.py` (RosThread pump) |
| Qt architecture guide | `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` (do not treat as Level C execution board) |
| Live board | `docs/plan/00_ARCHITECTURE_PROGRESS.md` (update only if Level C becomes the live next slice) |

---

## New-session entry recipe

1. Read **this file** (`docs/plan/02_LEVEL_C_PURE_HAL_PLAN.md`).
2. Confirm frozen bar green (focused pytest command above).
3. Choose scope: **P1 Lidar pilot** | Wind choice | defer (P0 is already landed).
4. Implement one phase; re-run concurrency band + full suite.
5. Do **not** start P3–P5 until P0 + pilot prove notifier/bridge ownership.
6. Do **not** re-run open-ended “always find more concurrency tests” audits unless changing halt design or affinity ownership outside the frozen bar.
