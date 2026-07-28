"""NOTIFY-contract tests for QML-exposed models (TD-033, Slice 1).

Pins which state changes emit which signals, exactly once, with what payload —
the contract QML bindings silently depend on:

- ``ShellState`` per-property signals (guarded setters + ``apply_screen_count``)
- ``OverlayHostPolicy`` ``layout_changed`` vs. the video-fullscreen slots
- ``ShellRouter.route_registry_changed``
- The blanket-``changed`` composer wrappers in ``qml_context_composer.py``
  (connection completeness + fan-in emission)

All connections here are direct same-thread connections, so emissions are
synchronous: ``QSignalSpy.count()`` is reliable immediately after the mutating
call returns — no ``wait()`` needed. This PySide6 build exposes ``count()`` /
``at(i)`` on ``QSignalSpy`` (no ``len()``/``clear()``).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from PySide6.QtCore import QObject
from PySide6.QtTest import QSignalSpy

from paint_controller.core import qml_context_composer as qcc
from paint_controller.models.overlay_host_policy import OverlayHostPolicy
from paint_controller.models.shell_router import ShellRouter
from paint_controller.models.shell_state import ShellState
from tests.test_shell_state import FakeScreenManager


def _emissions(spy: QSignalSpy) -> list[list[object]]:
    """Snapshot of a spy's recorded emissions as a list of argument lists."""
    return [spy.at(index) for index in range(spy.count())]


# ---------------------------------------------------------------------------
# ShellState
# ---------------------------------------------------------------------------

_SHELL_SIGNAL_NAMES: tuple[str, ...] = (
    "screen_count_changed",
    "main_surface_screen_index_changed",
    "secondary_surface_screen_index_changed",
    "secondary_surface_active_changed",
    "secondary_surface_fullscreen_changed",
    "show_system_control_on_main_surface_changed",
    "show_system_control_on_secondary_surface_changed",
    "video_fullscreen_on_main_surface_changed",
)

# Expected per-signal emissions for one apply_screen_count(2) from the
# single-screen baseline. secondary_surface_screen_index stays 0 and
# video_fullscreen_on_main_surface stays True, so those two must NOT emit.
_TO_DUAL: dict[str, list[list[object]]] = {
    "screen_count_changed": [[2]],
    "main_surface_screen_index_changed": [[1]],
    "secondary_surface_screen_index_changed": [],
    "secondary_surface_active_changed": [[True]],
    "secondary_surface_fullscreen_changed": [[True]],
    "show_system_control_on_main_surface_changed": [[False]],
    "show_system_control_on_secondary_surface_changed": [[True]],
    "video_fullscreen_on_main_surface_changed": [],
}

# Reverse transition (dual -> single). Same two signals stay silent.
_TO_SINGLE: dict[str, list[list[object]]] = {
    "screen_count_changed": [[1]],
    "main_surface_screen_index_changed": [[0]],
    "secondary_surface_screen_index_changed": [],
    "secondary_surface_active_changed": [[False]],
    "secondary_surface_fullscreen_changed": [[False]],
    "show_system_control_on_main_surface_changed": [[True]],
    "show_system_control_on_secondary_surface_changed": [[False]],
    "video_fullscreen_on_main_surface_changed": [],
}


def _attach_shell_spies(shell_state: ShellState) -> dict[str, QSignalSpy]:
    return {name: QSignalSpy(getattr(shell_state, name)) for name in _SHELL_SIGNAL_NAMES}


def _assert_shell_emissions(
    spies: dict[str, QSignalSpy], expected: dict[str, list[list[object]]]
) -> None:
    for name, want in expected.items():
        got = _emissions(spies[name])
        assert got == want, f"{name}: expected emissions {want}, got {got}"


@pytest.mark.parametrize(
    ("setter_name", "signal_name", "value"),
    [
        ("_set_screen_count", "screen_count_changed", 2),
        ("_set_main_surface_screen_index", "main_surface_screen_index_changed", 1),
        ("_set_secondary_surface_screen_index", "secondary_surface_screen_index_changed", 1),
        ("_set_secondary_surface_active", "secondary_surface_active_changed", True),
        ("_set_secondary_surface_fullscreen", "secondary_surface_fullscreen_changed", True),
        ("_set_show_system_control_on_main_surface", "show_system_control_on_main_surface_changed", False),
        ("_set_show_system_control_on_secondary_surface", "show_system_control_on_secondary_surface_changed", True),
        ("_set_video_fullscreen_on_main_surface", "video_fullscreen_on_main_surface_changed", False),
    ],
)
def test_shell_state_setter_emits_once_with_payload_and_guards_noop(
    qt_core_app, setter_name: str, signal_name: str, value: object
) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))
    spy = QSignalSpy(getattr(shell_state, signal_name))

    getattr(shell_state, setter_name)(value)
    assert _emissions(spy) == [[value]]

    # Guarded setter: re-applying the current value must not re-emit.
    getattr(shell_state, setter_name)(value)
    assert _emissions(spy) == [[value]]


def test_shell_state_apply_screen_count_to_dual_emits_per_signal(qt_core_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))
    spies = _attach_shell_spies(shell_state)

    shell_state.apply_screen_count(2)

    _assert_shell_emissions(spies, _TO_DUAL)


def test_shell_state_apply_screen_count_back_to_single_emits_per_signal(qt_core_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))
    shell_state.apply_screen_count(2)
    spies = _attach_shell_spies(shell_state)

    shell_state.apply_screen_count(1)

    _assert_shell_emissions(spies, _TO_SINGLE)


def test_shell_state_apply_screen_count_noop_emits_nothing(qt_core_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))
    spies = _attach_shell_spies(shell_state)

    shell_state.apply_screen_count(1)
    # Values below 1 are normalized to 1 by max(1, count) — still a no-op here.
    shell_state.apply_screen_count(0)

    _assert_shell_emissions(spies, {name: [] for name in _SHELL_SIGNAL_NAMES})


def test_shell_state_apply_screen_count_normalizes_below_one(qt_core_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))
    shell_state.apply_screen_count(2)
    spies = _attach_shell_spies(shell_state)

    # max(1, 0) == 1, so this must behave exactly like apply_screen_count(1).
    shell_state.apply_screen_count(0)

    _assert_shell_emissions(spies, _TO_SINGLE)


def test_shell_state_refresh_from_screen_manager_uses_same_contract(qt_core_app) -> None:
    screen_manager = FakeScreenManager(screen_count=1)
    shell_state = ShellState(screen_manager=screen_manager)
    spies = _attach_shell_spies(shell_state)

    # screens_changed -> refresh_from_screen_manager -> apply_screen_count
    screen_manager.set_screen_count(2)

    _assert_shell_emissions(spies, _TO_DUAL)


# ---------------------------------------------------------------------------
# OverlayHostPolicy
# ---------------------------------------------------------------------------


def _make_policy(screen_count: int = 1) -> tuple[ShellState, OverlayHostPolicy]:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=screen_count))
    return shell_state, OverlayHostPolicy(shell_state=shell_state)


def test_overlay_layout_changed_fires_once_per_shell_input_flip(qt_core_app) -> None:
    shell_state, policy = _make_policy()
    spy = QSignalSpy(policy.layout_changed)

    # Each connected shell signal drives one refresh_layout; a refresh that
    # changes layout attrs emits layout_changed exactly once (no payload).
    shell_state._set_secondary_surface_active(True)
    assert _emissions(spy) == [[]]

    shell_state._set_show_system_control_on_main_surface(False)
    assert spy.count() == 2

    shell_state._set_show_system_control_on_secondary_surface(True)
    assert spy.count() == 3

    shell_state._set_video_fullscreen_on_main_surface(False)
    assert spy.count() == 4


def test_overlay_refresh_layout_noop_emits_nothing(qt_core_app) -> None:
    _, policy = _make_policy()
    spy = QSignalSpy(policy.layout_changed)

    policy.refresh_layout()

    assert spy.count() == 0


def test_overlay_screen_count_changed_is_a_dead_layout_input(qt_core_app) -> None:
    # Intentional pin of current behavior: OverlayHostPolicy connects
    # screen_count_changed to refresh_layout, but refresh_layout never reads
    # the screen count, so this wiring can never produce layout_changed.
    # The dead input itself is a production observation flagged for TD-037 —
    # do not "fix" it here.
    shell_state, policy = _make_policy()
    spy = QSignalSpy(policy.layout_changed)

    shell_state._set_screen_count(2)

    assert shell_state.screen_count == 2  # the change (and signal) really happened
    assert spy.count() == 0


def test_overlay_refresh_layout_batches_multiple_changes_into_one_emission(qt_core_app) -> None:
    shell_state, policy = _make_policy()
    # Bypass the guarded setters so no shell signal fires; two layout inputs
    # change before a single refresh_layout call.
    shell_state._secondary_surface_active = True
    shell_state._show_system_control_on_main_surface = False
    spy = QSignalSpy(policy.layout_changed)

    policy.refresh_layout()

    assert spy.count() == 1


def test_overlay_show_video_fullscreen_emits_source_and_active(qt_core_app) -> None:
    _, policy = _make_policy()
    source_spy = QSignalSpy(policy.video_fullscreen_source_changed)
    active_spy = QSignalSpy(policy.video_fullscreen_active_changed)
    layout_spy = QSignalSpy(policy.layout_changed)

    policy.show_video_fullscreen("image://ef_live/frame")

    assert _emissions(source_spy) == [["image://ef_live/frame"]]
    assert _emissions(active_spy) == [[True]]
    # The fullscreen slots never drive layout_changed.
    assert layout_spy.count() == 0


def test_overlay_show_video_fullscreen_noop_when_already_active(qt_core_app) -> None:
    _, policy = _make_policy()
    policy.show_video_fullscreen("image://ef_live/frame")
    source_spy = QSignalSpy(policy.video_fullscreen_source_changed)
    active_spy = QSignalSpy(policy.video_fullscreen_active_changed)

    policy.show_video_fullscreen("image://ef_live/frame")

    assert source_spy.count() == 0
    assert active_spy.count() == 0


def test_overlay_hide_video_fullscreen_emits_active_only(qt_core_app) -> None:
    _, policy = _make_policy()
    policy.show_video_fullscreen("image://ef_live/frame")
    source_spy = QSignalSpy(policy.video_fullscreen_source_changed)
    active_spy = QSignalSpy(policy.video_fullscreen_active_changed)

    policy.hide_video_fullscreen()

    # Hiding does not clear or re-emit the source.
    assert _emissions(active_spy) == [[False]]
    assert source_spy.count() == 0
    assert policy.video_fullscreen_source == "image://ef_live/frame"


def test_overlay_hide_video_fullscreen_noop_when_inactive(qt_core_app) -> None:
    _, policy = _make_policy()
    source_spy = QSignalSpy(policy.video_fullscreen_source_changed)
    active_spy = QSignalSpy(policy.video_fullscreen_active_changed)

    policy.hide_video_fullscreen()

    assert source_spy.count() == 0
    assert active_spy.count() == 0


def test_overlay_toggle_video_fullscreen_shows_then_hides_keeping_source(qt_core_app) -> None:
    _, policy = _make_policy()
    source_spy = QSignalSpy(policy.video_fullscreen_source_changed)
    active_spy = QSignalSpy(policy.video_fullscreen_active_changed)

    # Inactive -> toggle shows with the given source.
    policy.toggle_video_fullscreen("image://base_front_live/frame")
    assert _emissions(source_spy) == [["image://base_front_live/frame"]]
    assert _emissions(active_spy) == [[True]]

    # Active -> toggle hides; the source argument is ignored on the hide path.
    policy.toggle_video_fullscreen("image://ef_live/frame")
    assert _emissions(source_spy) == [["image://base_front_live/frame"]]
    assert _emissions(active_spy) == [[True], [False]]
    assert policy.video_fullscreen_source == "image://base_front_live/frame"


def test_overlay_set_video_fullscreen_source_emits_only_source(qt_core_app) -> None:
    _, policy = _make_policy()
    policy.show_video_fullscreen("image://ef_live/frame")
    source_spy = QSignalSpy(policy.video_fullscreen_source_changed)
    active_spy = QSignalSpy(policy.video_fullscreen_active_changed)

    policy.set_video_fullscreen_source("image://base_rear_live/frame")
    assert _emissions(source_spy) == [["image://base_rear_live/frame"]]
    assert active_spy.count() == 0

    # Same value is a guarded no-op.
    policy.set_video_fullscreen_source("image://base_rear_live/frame")
    assert source_spy.count() == 1


def test_overlay_refresh_layout_never_emits_video_fullscreen_signals(qt_core_app) -> None:
    shell_state, policy = _make_policy()
    policy.show_video_fullscreen("image://ef_live/frame")
    source_spy = QSignalSpy(policy.video_fullscreen_source_changed)
    active_spy = QSignalSpy(policy.video_fullscreen_active_changed)

    # Drive real layout changes through refresh_layout.
    shell_state._set_secondary_surface_active(True)
    shell_state._set_secondary_surface_active(False)

    assert source_spy.count() == 0
    assert active_spy.count() == 0


# ---------------------------------------------------------------------------
# ShellRouter
# ---------------------------------------------------------------------------


def test_shell_router_route_registry_changed_has_no_emission_path(qt_core_app) -> None:
    # Pinned as-is: the registry is built once in __init__ and never mutated,
    # so route_registry_changed currently never fires (navigation only emits
    # current_route_changed, covered in tests/test_shell_router.py). If a
    # dynamic registry is ever added, it must emit this signal on change.
    router = ShellRouter()
    spy = QSignalSpy(router.route_registry_changed)

    for route in ("base", "winch", "monitor", "tuning", "launcher", "settings", "home"):
        router.navigateTo(route)

    assert spy.count() == 0


def test_shell_router_route_registry_returns_defensive_copy(qt_core_app) -> None:
    router = ShellRouter()

    registry = router.routeRegistry
    registry.append({"key": "bogus", "title": "Bogus", "order": 99})

    assert [entry["key"] for entry in router.routeRegistry] == [
        "home", "base", "winch", "monitor", "tuning", "launcher", "settings",
    ]
    assert router.navigateTo("bogus") is False


# ---------------------------------------------------------------------------
# Composer wrapper fleet (qml_context_composer.py)
# ---------------------------------------------------------------------------


class _FakeSignal:
    """Recorder double for a Qt signal: counts connections and replays emits.

    Unlike the connect-only recorders in test_qml_context_composer.py, emit()
    invokes the recorded callbacks synchronously, so fan-in through the
    wrapper is exercised for real.
    """

    def __init__(self) -> None:
        self.connections: list[Callable[..., None]] = []

    def connect(self, callback: Callable[..., None]) -> None:
        self.connections.append(callback)

    def emit(self, *args: object) -> None:
        for callback in list(self.connections):
            callback(*args)


class _SignalHub:
    """Plain-object fake exposing named _FakeSignal attributes."""

    def __init__(self, *signal_names: str) -> None:
        self.signal_names = signal_names
        for name in signal_names:
            setattr(self, name, _FakeSignal())


def _table(owners: dict[str, _SignalHub]) -> list[tuple[str, str]]:
    return [
        (owner_key, name)
        for owner_key, hub in owners.items()
        for name in hub.signal_names
    ]


_BASE_TOP_VIEW_CHANGED_SIGNALS: tuple[str, ...] = (
    "zoomChanged",
    "offsetXChanged",
    "offsetYChanged",
    "cropEnabledChanged",
    "cropWidthRatioChanged",
    "cropCenterXChanged",
    "k1Changed",
    "k2Changed",
    "k3Changed",
    "k4Changed",
    "editModeChanged",
    "enabledChanged",
    "sourcePointsChanged",
)


# Each builder returns (wrapper, owners, expected (owner_key, signal_name)
# table). The signal names mirror the wrapper's _connect_if_signal lists in
# qml_context_composer.py — that list is the contract being pinned.
def _spec_teensy_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    teensy = _SignalHub("status_changed")
    wrapper = qcc._TeensyStatus(teensy_controller=teensy)
    owners = {"teensy": teensy}
    return wrapper, owners, _table(owners)


def _spec_winch_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    winch = _SignalHub(
        "available_changed",
        "enabled_changed",
        "load_detection_changed",
        "cable_length_changed",
        "cable_speed_changed",
        "winch_torque_changed",
        "motor_temperature_changed",
        "motor_voltage_changed",
        "motor_brake_changed",
        "unusual_load_detected_changed",
    )
    wrapper = qcc._WinchStatus(winch_controller=winch)
    owners = {"winch": winch}
    return wrapper, owners, _table(owners)


def _spec_wheel_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    wheel = _SignalHub(
        "available_changed",
        "enabled_changed",
        "left_motor_available_changed",
        "right_motor_available_changed",
        "left_wheel_speed_changed",
        "right_wheel_speed_changed",
        "left_wheel_current_changed",
        "right_wheel_current_changed",
        "left_wheel_position_changed",
        "right_wheel_position_changed",
    )
    wrapper = qcc._WheelStatus(wheel_controller=wheel)
    owners = {"wheel": wheel}
    return wrapper, owners, _table(owners)


def _spec_valve_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    valve = _SignalHub(
        "valve_position_changed",
        "valve_rate_changed",
        "total_volume_changed",
        "valve_motor_current_changed",
        "valve_motor_connected_changed",
        "flow_meter_connected_changed",
        "esp32_connected_changed",
    )
    wrapper = qcc._ValveStatus(valve_controller=valve)
    owners = {"valve": valve}
    return wrapper, owners, _table(owners)


def _spec_lidar_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    lidar = _SignalHub("distance_changed", "angle_changed")
    wrapper = qcc._LidarStatus(lidar_controller=lidar)
    owners = {"lidar": lidar}
    return wrapper, owners, _table(owners)


def _spec_recording_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    video = _SignalHub("recordingStatusChanged", "baseRecordingStatusChanged")
    screen = _SignalHub("is_recording_changed", "recording_duration_changed", "free_space_gb_changed")
    bag = _SignalHub(
        "is_bag_recording_changed",
        "bag_recording_duration_changed",
        "is_compressing_changed",
        "bag_status_message_changed",
    )
    wrapper = qcc._RecordingStatus(
        video_stream_handler=video, screen_recorder=screen, ros_bag_recorder=bag
    )
    owners = {"video": video, "screen": screen, "bag": bag}
    return wrapper, owners, _table(owners)


def _spec_shell_connectivity_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    ssh = _SignalHub("deviceAvailabilityChanged", "configUpdated")
    heartbeat = _SignalHub(
        "base_online_changed", "base_status_changed", "ef_online_changed", "ef_status_changed"
    )
    winch = _SignalHub("available_changed")
    wheel = _SignalHub("changed")
    teensy = _SignalHub("connection_changed")
    wrapper = qcc._ShellConnectivityStatus(
        ssh_controller=ssh,
        heartbeat_handler=heartbeat,
        winch_controller=winch,
        wheel_status=wheel,
        teensy_controller=teensy,
    )
    owners = {"ssh": ssh, "heartbeat": heartbeat, "winch": winch, "wheel": wheel, "teensy": teensy}
    return wrapper, owners, _table(owners)


def _spec_video_runtime_controls() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    controls = _SignalHub(
        "left_control_mode_changed",
        "left_control_value_changed",
        "right_control_mode_changed",
        "right_control_value_changed",
        "left_control_mode_display_changed",
        "right_control_mode_display_changed",
    )
    wrapper = qcc._VideoRuntimeControls(control_processor=controls)
    owners = {"controls": controls}
    return wrapper, owners, _table(owners)


def _spec_video_runtime_top_bar() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    ssh = _SignalHub("deviceAvailabilityChanged")
    screen = _SignalHub("is_recording_changed", "recording_duration_changed")
    monitor = _SignalHub(
        "battery_level_changed", "battery_remaining_time_changed", "cpu_temperature_changed"
    )
    teensy = _SignalHub("status_changed")
    winch = _SignalHub("motor_voltage_changed")
    wrapper = qcc._VideoRuntimeTopBar(
        ssh_controller=ssh,
        screen_recorder=screen,
        system_monitor=monitor,
        teensy_controller=teensy,
        winch_controller=winch,
    )
    owners = {"ssh": ssh, "screen": screen, "monitor": monitor, "teensy": teensy, "winch": winch}
    return wrapper, owners, _table(owners)


def _spec_base_top_view_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    service = _SignalHub(*_BASE_TOP_VIEW_CHANGED_SIGNALS, "frameReady")
    wrapper = qcc._BaseTopViewStatus(base_top_view_service=service)
    owners = {"service": service}
    # frameReady is a separate pass-through (covered below), not a changed fan-in.
    return wrapper, owners, [("service", name) for name in _BASE_TOP_VIEW_CHANGED_SIGNALS]


_FLEET_SPECS: dict[str, Callable[[], tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]]] = {
    "_TeensyStatus": _spec_teensy_status,
    "_WinchStatus": _spec_winch_status,
    "_WheelStatus": _spec_wheel_status,
    "_ValveStatus": _spec_valve_status,
    "_LidarStatus": _spec_lidar_status,
    "_RecordingStatus": _spec_recording_status,
    "_ShellConnectivityStatus": _spec_shell_connectivity_status,
    "_VideoRuntimeControls": _spec_video_runtime_controls,
    "_VideoRuntimeTopBar": _spec_video_runtime_top_bar,
    "_BaseTopViewStatus": _spec_base_top_view_status,
}


@pytest.mark.parametrize("build_spec", _FLEET_SPECS.values(), ids=list(_FLEET_SPECS))
def test_wrapper_connects_every_listed_backing_signal(qt_core_app, build_spec) -> None:
    """Connection completeness: every name in the wrapper's _connect_if_signal
    list must actually be connected — _connect_if_signal silently skips names
    the backing object lacks, which is the failure mode being pinned."""
    _, owners, table = build_spec()
    assert table, "spec table must not be empty"
    for owner_key, signal_name in table:
        recorder = getattr(owners[owner_key], signal_name, None)
        assert recorder is not None, f"fake is missing signal {owner_key}.{signal_name}"
        assert len(recorder.connections) == 1, (
            f"{owner_key}.{signal_name}: expected exactly 1 connection from the wrapper, "
            f"got {len(recorder.connections)}"
        )


@pytest.mark.parametrize("build_spec", _FLEET_SPECS.values(), ids=list(_FLEET_SPECS))
def test_wrapper_changed_fires_once_per_backing_emission(qt_core_app, build_spec) -> None:
    """Fan-in emission: each connected backing signal drives the blanket
    ``changed`` exactly once per emission."""
    wrapper, owners, table = build_spec()
    for owner_key, signal_name in table:
        spy = QSignalSpy(wrapper.changed)
        getattr(owners[owner_key], signal_name).emit()
        assert spy.count() == 1, (
            f"{owner_key}.{signal_name}: expected exactly 1 changed emission, got {spy.count()}"
        )


def test_base_top_view_frame_ready_passes_through_without_changed(qt_core_app) -> None:
    service = _SignalHub(*_BASE_TOP_VIEW_CHANGED_SIGNALS, "frameReady")
    wrapper = qcc._BaseTopViewStatus(base_top_view_service=service)
    changed_spy = QSignalSpy(wrapper.changed)
    frame_spy = QSignalSpy(wrapper.frameReady)

    service.frameReady.emit()

    assert frame_spy.count() == 1
    assert changed_spy.count() == 0


def test_base_top_view_changed_signals_do_not_emit_frame_ready(qt_core_app) -> None:
    service = _SignalHub(*_BASE_TOP_VIEW_CHANGED_SIGNALS, "frameReady")
    wrapper = qcc._BaseTopViewStatus(base_top_view_service=service)
    frame_spy = QSignalSpy(wrapper.frameReady)

    for name in _BASE_TOP_VIEW_CHANGED_SIGNALS:
        getattr(service, name).emit()

    assert frame_spy.count() == 0
