# TD-033 Plan: Behavioral UI & NOTIFY-Contract Tests

> **Status**: draft v2 — audited (verdict: NEEDS MODIFICATION → all accepted), ready for approval
> **Lifecycle**: delete this file when TD-033 closes (per AGENTS.md Pruning Policy)
> **Tech-debt**: `docs/tech-debt.md` TD-033 (high)
> **Audit highlights**: offscreen mouse delivery **experimentally proven viable** against the real `MainWindow.qml`, but the v1 test spec fails for three fixture/geometry reasons (fixed below); wrapper fan-in tests as v1-specified could not detect the silent-skip they target.

## Goal

Catch wiring regressions the load-only smoke suite is blind to (the Phase-7 SelectBar navigation break is the reference incident), pin the NOTIFY contracts of QML-exposed models, and cover the heartbeat recovery/flap half of the safety story.

## Scope

- **In**: (1) NOTIFY-contract tests for QML-exposed models; (2) heartbeat recovery/flap tests; (3) one true interaction test through the real shell wiring (nav click → route change).
- **Out**: qmltestrunner/Qt Quick Test adoption (disproportionate); per-page behavioral coverage; visual/pixel testing; mass conversion of existing smoke tests; an e-stop interaction test (conscious cut — the safety halt path is already integration-tested in `test_safety_integration.py`).

## Slice 1 — NOTIFY-contract tests (Python-only, no QML)

New `tests/test_notify_contracts.py`, using `QSignalSpy` (verified importable in this PySide6 6.10.1 venv):

- `ShellState`: mutate each setter / `apply_screen_count`; assert exactly one emission of the matching per-property signal with correct payload; assert no emission on no-op set. Note: one `apply_screen_count(2)` can emit up to 7 of the 8 signals in a single call — assert per-signal, not per-call.
- `OverlayHostPolicy`: `layout_changed` is driven by `refresh_layout`; `video_fullscreen_active_changed`/`video_fullscreen_source_changed` are driven only by the `show/hide/toggle/set_video_fullscreen_source` slots (`overlay_host_policy.py:121-154`) — test each path separately. Note: `screen_count_changed → refresh_layout` is a dead input (refresh never reads screen count) — pin it as intentional or file under TD-037; do not "fix" here.
- `ShellRouter.route_registry_changed`: currently unasserted (existing `current_route_changed` coverage stays).
- Composer wrapper fleet (`_TeensyStatus`, `_WinchStatus`, `_WheelStatus`, `_ValveStatus`, `_LidarStatus`, `_RecordingStatus`, `_ShellConnectivityStatus`, `_VideoRuntimeControls`, `_VideoRuntimeTopBar`, `_BaseTopViewStatus`): **two assertion layers, both required** —
  1. *Connection completeness*: assert every signal name in each wrapper's `_connect_if_signal` list actually got connected (recorder fakes with `Signal`-counting, or real-QObject fakes). Without this layer the tests only pin signals the fake happens to define — `_connect_if_signal` (`qml_context_composer.py:49-53`) silently skips the rest, which is exactly the failure mode being pinned.
  2. *Fan-in emission*: emit each connected backing signal, assert the wrapper's `changed` fires exactly once per backing emission. (Existing `_SignalRecorderForComposer` in `test_qml_context_composer.py:87-92` is connect-only; tests must invoke recorded callbacks or add `emit`.)

## Slice 2 — Heartbeat recovery/flap (extend `tests/test_heartbeat.py`)

- **Recovery (no-coordinator variant)**: after injected loss (stale `_X_last_seen` + patched time + `_check_availability()`), deliver a fresh callback → assert online `True`, "restored" status message, and WARNING→ONTASK promotion once all three components are online (`heartbeat.py:120-121`).
- **Coordinator variant**: with a `safety_coordinator` present, loss routes to `halt_all_effectors` (`:123-132`) and the fake coordinator never touches `state_store` — promotion assertions apply only to the no-coordinator variant. Test both.
- **ERROR latch**: force ERROR, deliver callbacks, assert no auto-downgrade (`:83-100`). Then `clear_error_state()` — two variants: with coordinator it delegates (`:538-541`) and does **not** reset runtime state; without, it resets and publishes CLEAR_ERROR (`:514-544`). Assert accordingly.
- **EF-loss and controller-loss** variants of the existing base-loss test.
- **Flap**: alternate loss/restore for 3 cycles; assert exactly one halt per loss edge (online-guard at `:195,201` provides structural protection) and clean re-promotion.
- **Timer discipline** (mandatory): stop the real 200 ms availability timer (`heartbeat.py:77-79`) per test — left running it consumes patched `time.time` side-effect lists and races the assertions.

## Slice 3 — Real-shell interaction test (SelectBar regression test)

Extend `tests/test_startup_smoke_shell.py`. **Experiment-validated configuration** (auditor ran the real file offscreen):

- Load `qml/core/MainWindow.qml` via `QQmlApplicationEngine` with a `_context_objects()` variant built with `FakeOverlayHost(video_fullscreen_active=False)` — the default fixture's fullscreen video overlay has full-window MouseAreas that swallow every sidebar click on the home route.
- Click the **"base" or "winch"** delegate — "settings" maps outside the 800×800 offscreen window and `ConnectionStatusPanel`'s full-area MouseArea covers the middle delegates. (Resizing to `Windowed` + scrolling the Flickable also works but adds moving parts — avoid.)
- Locate delegates via `repeater.parentItem().childItems()` — `repeater.itemAt()` returns `None` from Python for all indices.
- Assert: delegate count > 0, `shellRouter.currentRoute` changed to the clicked key, `stackView.property("currentIndex")` matches (precedent at `test_startup_smoke_shell.py:233-236`), video overlay inactive off-home.
- **Regression mechanism, corrected**: with the original bug (`shellRouter` undefined), the Repeater's model collapses (`shellRouter ? shellRouter.routeRegistry : []`, `SelectBar.qml:203`) — zero delegates render. The test catches it via delegate absence *and* the guard no-op; both assertions are required. The QML-invocation fallback catches the same bug, so v1's "weaker fallback" worry is moot.

## Files

- New: `tests/test_notify_contracts.py`
- Modify: `tests/test_heartbeat.py`, `tests/test_startup_smoke_shell.py`
- No production code changes expected. NOTIFY gaps found along the way (e.g. `sprayGunLedOn` refresh delay) are filed under TD-037, not fixed here.

## Validation gates

- Focused: `python/paint_controller/venv/bin/python -m pytest tests/test_notify_contracts.py tests/test_heartbeat.py tests/test_startup_smoke_shell.py -q`
- Full suite green. pyright unaffected (verify whether `pyrightconfig.json` covers test files before assuming).

## Risks

- Blanket-`changed` wrappers make "exactly one emission" timing-sensitive → `QSignalSpy.wait` / `qtbot.waitUntil` with bounded timeouts; process events between steps.
- Offscreen geometry (800×800) constrains which delegates are clickable → Slice 3 pins the validated configuration; if the QML layout changes, re-validate the click target rather than deleting the test.

## Rollback

Tests-only change: delete `tests/test_notify_contracts.py`, `git revert` the two modified test files.
