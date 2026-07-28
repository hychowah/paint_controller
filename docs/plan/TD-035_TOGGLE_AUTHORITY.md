# TD-035 Plan: Backend-Authoritative Toggles + Reconnect Reconciliation

> **Status**: draft v2 — audited (verdict: NEEDS MODIFICATION → all accepted), ready for approval
> **Lifecycle**: delete this file when TD-035 closes (per AGENTS.md Pruning Policy)
> **Tech-debt**: `docs/tech-debt.md` TD-035 (high)
> **Audit highlights**: v1's Slice 3 was **dangerous** — first-connect publish would command 6–7 outputs to default-False at every app start on a live rig (rewritten below). v1 also missed that the wheel controller has **no** state source at all (`set_enabled` is never called; `wheelStatus.enabled` is permanently False in production), mislabeled three set-style call sites as toggle sites, and missed that `WheelActions.toggleEnabled` already exists but is dead in QML.

## Goal

The backend — never the view's binding snapshot — decides the next command state for every toggle, and user intent is reconciled with the device after a *real* reconnect.

## Design decisions (confirm at plan approval)

1. **Arg-less toggles reading controller state** — per-slot state source pinned in the table below (the audit found v1's generic "controller's known state" was wrong for relay and teensy-enable).
2. **Reconciliation = re-publish intent on reconnect-after-loss only** — never on first connect (see Slice 3 for the hazard). Publish only intents that are `True`; reconcile relay by echo-compare.
3. **Lidar power**: add backend intent state, same optimistic pattern as the other six, plus an arg-less `toggleLidarPower()`.
4. **Leave `checked`-driven set-style calls** (`PageStatus.qml:69-77`, `TeensyStatus.qml:37-57`) — the switch's own `checked` is the user's desired state, genuinely authoritative, and rejection-revert exists. Caveat: `TouchSwitch.qml:54`'s assignment destroys the external `checked:` binding after first manual use (pre-existing display drift, not made worse here).
5. **Out of scope**: teensy setters returning `None` (rejection path unreachable), the `setAutoCorrectonEnabled` typo (Slice 1 touches the line anyway — opportunistic fix optional), `sprayGunLedOn` delayed wrapper refresh (TD-037).

## Slice 1 — Arg-less toggles end-to-end

**Prerequisite (audit finding):** `WheelController.setEnabled` (`wheel.py:348-359`) records nothing — `set_enabled` (`:314`) is never called, so `wheelStatus.enabled` is permanently False in production and both wheel QML sites always send enable=True today. Before any wheel toggle work, make `setEnabled` record intent via `self.set_enabled(enabled)` (the optimistic pattern teensy already uses).

**Per-slot state source (pinned by audit):**

| Slot | State source to negate |
|---|---|
| `TeensyActions.toggleStability/AutoCorrection/SprayGunLeveling/RollerSteering/SwingDamping/SprayGunLed` | controller members (`_stability_enabled` etc., teensy.py:190-196) |
| `TeensyActions.toggleYaw` | status dict `yaw_enabled` (firmware echo, `:363`) — no member exists |
| `DeviceActionHandler.toggleTeensyRelay` | intent member `_relay_enabled` (`:189`) — NOT the `relay_on` echo; the toggle axis must match the reconciliation axis |
| `DeviceActionHandler.toggleTeensyEnable` | status dict `enabled` (echo, `:341`) — member `_enabled` is dead (never written) |
| `DeviceActionHandler.toggleWinchEnable` / `WinchActions.toggleLoadDetection` | winch echo-driven state (`winch.py:131,138`) — genuinely fresh |
| `WheelActions.toggleEnabled` | wheel intent member (exists after the prerequisite above) |

**Call-site remedies (corrected — not all are "argument removal"):**
- `DeviceControlTab.qml:80,94,155,169,426-486,545`: toggle sites — remove arguments.
- `DeviceControlTab.qml:230` and `PageWheel.qml:203`: `wheelActions.setEnabled(!wheelStatus.enabled)` → `wheelActions.toggleEnabled()` (convert the existing dead slot at `wheel_actions.py:41-43` to arg-less; rewire both sites).
- `PageWinch.qml:234-240,350-357`: set-style with inline negation — replace with `deviceActionHandler.toggleWinchEnable()` / `winchActions.toggleLoadDetection()`. These sites use the return value and `desiredX` locals for notification text: after conversion, derive notification text from the post-call status property (now authoritative) or have the slot include the commanded state in its result — implementer's choice, behavior must not regress.
- Delete the dead `_run_toggle` in `device_actions.py:89-102`.

**Tests:** `test_teensy_actions.py`, `test_device_actions.py`, `test_winch_motion_handler.py`, **`tests/test_wheel_actions.py`** (v1 omitted it; :67-73 assert the old signature). Fakes gain state; inversion assertions become state-driven.
**Smoke fakes (manual update — no safety net):** the contract-parity test compares context-property *name sets only*; fake-vs-production slot signatures are **not** checked by anything (v1's "the harness will catch it" was wrong). Update `startup_smoke_support.py`: `FakeTeensyActions` (:651-681), `FakeDeviceActionHandler` (:599-629), `FakeWinchActions` (:741), `FakeWheelActions` (:767).

## Slice 2 — Lidar power backend state

- `teensy.py`: `_lidar_power` member; `setLidarPower` stores it **and** calls `_update_status_fields(lidar_power=...)` **and** emits `status_changed` (attribute-read wrapper properties refresh only on `status_changed` — the `sprayGunLedOn` staleness mechanism); add `lidar_power` to `TeensyStatusDict` (:79-85) and the initial `_status` dict (:125-181) — pyright covers `controllers/`, a TypedDict miss will be flagged.
- Add `lidar_power` to `_USER_CONTROLLED_FIELDS` (7th field: preserved + reconciled).
- `qml_context_composer.py`: expose `lidarPower` on `_TeensyStatus`.
- New arg-less `TeensyActions.toggleLidarPower()` (8th toggle — v1's "seven" is stale once this lands).
- `DeviceControlTab.qml:548-556`: drop `selfContained`, bind to `teensyStatus.lidarPower`, call `toggleLidarPower()`. Bonus: dropping `selfContained` fixes a latent bug — its click handler overwrites `controlStatus` (`ControlPanel.qml:78`), destroying the `controlStatus: enabledState ? "On" : "Off"` binding.
- Tests: extend `test_teensy.py`; add `FakeTeensyStatus.lidarPower` to `startup_smoke_support.py`.

## Slice 3 — Reconnect reconciliation (rewritten after audit)

**Rejected (v1)**: publish on every False→True availability edge including first connect. `_available` starts `False` (`_base.py:21`), so the restore edge fires within ~200 ms of the first status message at **every application startup** — commanding all 6–7 intents (default `False`) to the device, indistinguishable from a device reboot, actively disabling stability/steering on a rig that never rebooted. Worse than the bug.

**Accepted design:**
- Fire reconciliation **only on a restore edge that follows a loss**: latch on the loss edge (e.g. `_awaiting_reconcile = True` when availability drops), consume on the next restore edge. No latch, no publish — first connect stays silent.
- On reconcile, **publish only intents that are `True`** — never command `False` on restore (a `False` intent is the absence of a request, not a request to disable).
- **Relay**: reconcile by echo-compare — publish intent only when `_relay_enabled != relay_on` echo (firmware reports it; blind re-publish unnecessary).
- Winch: no local intent exists (firmware echoes everything) — verify and document, no code.
- Tests: `test_teensy.py` — inject loss (stale status → `_check_availability`), then a restoring status message; assert only `True` intents re-published on the restore edge, and assert **nothing** published on first connect (`FakePublisher` records).

## Files

- Python: `models/teensy_actions.py`, `models/winch_actions.py`, `models/wheel_actions.py`, `handlers/device_actions.py`, `controllers/teensy.py`, `controllers/wheel.py` (prerequisite), `core/qml_context_composer.py` (one property)
- QML: `DeviceControlTab.qml`, `PageWheel.qml`, `PageWinch.qml` (call-site rewrites only)
- Tests: `test_teensy_actions.py`, `test_device_actions.py`, `test_winch_motion_handler.py`, `test_wheel_actions.py`, `test_teensy.py`, `tests/startup_smoke_support.py`

## Validation gates

- Per-slice focused bands, then full suite green.
- pyright: all touched Python files are in `pyrightconfig.json` include — keep green.
- Startup smoke after fake signature updates (load-level only — it will not catch signature drift; get the fakes right by hand).

## Risks

- **Behavioral change**: buttons now send `!controllerState` instead of `!binding`. For optimistic fields the controller state can still drift from the device; Slice 3 bounds that drift to real reconnect windows, it does not eliminate it.
- **Wheel prerequisite changes production behavior** (`wheelStatus.enabled` becomes meaningful) — keep it in its own commit at the start of Slice 1 for clean revert.
- **Slice 3 is safety-adjacent**: the latch + True-only + echo-compare constraints are the whole point; do not simplify them during implementation.

## Rollback

Per-slice `git revert`; slices are independent (Slice 1 prerequisite commit first, then the bulk; Slices 2–3 additive).
