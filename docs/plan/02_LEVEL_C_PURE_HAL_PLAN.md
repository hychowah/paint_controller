# Level C — Pure-Python Device HAL (Durable Plan)

**Status**: Deferred / optional program (not the current execution track)  
**Saved**: 2026-08-05  
**Depends on**: Level A (`@Slot` strip) and Level B (`Property` → `@property`) — **both landed**  
**Do not overwrite** this file with concurrency-test or feature plans; those are separate tracks.

---

## Understanding

After Levels A+B, device adapters no longer expose QML `@Slot` / Qt `Property`. They still **are** Qt objects (`QObject`, `Signal`, `QTimer`, `RosTelemetryBridge` parenting). Level C would make ROS/device HAL classes plain Python implementing `ports/*`, with Qt confined to presentation and composition-owned I/O shells.

**Complexity**: High for full package purity; Low–Med for a partial/pilot path.

**Cross-layer impact**: High if full strip (Status, SignalWiring, factory, ESP32 transport). Partial can be contained.

---

## Prerequisites before any Level C code

Concurrency test lock pack must exist and stay green (see session plan for concurrency tests when active). Level C moves affinity/notify machinery; green full suite alone is **not** a sufficient before/after bar.

---

## Audit summary (code-only, 2026-08-05)

### Qt remaining on adapters

| Device | Qt load | Pain |
|---|---|---|
| **ESP32** | `QThread`, 3×`QTimer`, QueuedConnection discovery `@Slot`, many Signals | Highest (transport) |
| **Teensy** | Signals, availability timer, thrust ramp `QTimer`, RosTelemetryBridge, settings Signal fan-in | High |
| **Wheel / Winch** | Signals, base availability timer, RosTelemetryBridge | Med |
| **Lidar** | 2 Signals + 2 bridges | Low–Med |
| **Wind** | 2 Signals; emits from ROS spin (no bridge); not on production QML | Best pilot |
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

---

## Independent auditor recommendation

| Choice | Verdict |
|---|---|
| **Full Level C now** | **Not recommended** — multi-PR, high risk, little user-facing upside after A+B |
| **Defer entirely** | Acceptable; residual: bridge parenting, Wind spin-thread emit |
| **Partial (recommended if any Level C)** | P0–P2 + Wind/Lidar pilot; leave Teensy/ESP32 until hard requirement |

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

### P0 — Seams only (Low)
- `DeviceNotifier` Protocol
- `RosTelemetryBridge` parent may be external shell
- No behavior change required

### P1 — Pilot: Wind (+ optional Lidar) (Low–Med)
- Fix Wind spin-thread emit or purify
- Lidar plain adapter + proxy; Status names unchanged
- Structural ban: pilot modules import no PySide6

### P2 — Availability + bridge ownership (Med)
- Non-Qt availability state core
- `AvailabilityWatchdog(QObject)` at composition
- Reparent bridges off adapters

### P3 — Winch + Wheel pure (Med)
- Proxy emits Status + `error_state_changed`
- Settings inject without adapter `.connect`

### P4 — Teensy pure (High)
- Status + thrust timer shell + settings fan-in

### P5 — ESP32 split (High)
- Pure protocol/HAL + transport QObject

### Closeout
- AST/import ban: pure HAL modules no PySide6 (allowlist transport)

---

## Non-goals

- Changing QML `*Status`/`*Actions` contracts
- Polling Status from a global timer
- Folding SSH/SystemMonitor into device purity
- Renaming producer signal names without full Status rewire
- Full non-Qt event bus while app is Qt-wide

## Stop-and-ask

- Full vs partial vs defer (product choice)
- Delete WindMonitor vs purify
- Package rename (`controllers/` → adapters + transport)
- Teensy thrust timing changes without soak

## Acceptance

**Partial:** P0 + Wind fix/pilot green; P3–P5 deferred documented.  
**Full:** teensy/wheel/winch/lidar zero PySide6; ESP32 transport-only Qt; contracts + full suite green.

## Rollback

Per-phase restore of adapters/factory; no ROS msg migration.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-08-05 | Levels A+B landed on `dev` |
| 2026-08-05 | Full Level C **not** started; plan saved here before concurrency-test track |
| TBD | User chooses: defer / partial (P0–P1) / full program |

---

## Related

- Level A commit: strip device `@Slot`
- Level B commit: retire device Qt `Property`
- Structural bans: `tests/test_device_adapter_no_qml_slots.py`, `tests/test_device_adapter_no_qml_properties.py`
- Concurrency seams already in product: `core/ros_io.py` (TD-054), `core/ros_telemetry.py` (TD-056)
