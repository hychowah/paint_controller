"""NOTIFY-contract tests for QML-exposed models (TD-033, Slice 1).

Pins which state changes emit which signals, exactly once, with what payload —
the contract QML bindings silently depend on:

- ``ShellState`` per-property signals (guarded setters + ``apply_screen_count``)
- ``OverlayHostPolicy`` ``layout_changed`` vs. the video-fullscreen slots
- ``ShellRouter.routeRegistryChanged``
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
from paint_controller.models.lidar_status import (
    LIDAR_STATUS_PROPERTY_NAMES,
    LIDAR_STATUS_SIGNAL_MAP,
    LidarStatus,
)
from paint_controller.models.overlay_host_policy import OverlayHostPolicy
from paint_controller.models.shell_router import ShellRouter
from paint_controller.models.shell_state import ShellState
from paint_controller.models.teensy_status import TEENS_STATUS_PROPERTY_NAMES, TeensyStatus
from paint_controller.models.valve_status import (
    VALVE_STATUS_PROPERTY_NAMES,
    VALVE_STATUS_SIGNAL_MAP,
    ValveStatus,
)
from paint_controller.models.wheel_status import (
    WHEEL_STATUS_PROPERTY_NAMES,
    WHEEL_STATUS_SIGNAL_MAP,
    WheelStatus,
)
from paint_controller.models.winch_status import (
    WINCH_STATUS_PROPERTY_NAMES,
    WINCH_STATUS_SIGNAL_MAP,
    WinchStatus,
)
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


def _assert_shell_emissions(spies: dict[str, QSignalSpy], expected: dict[str, list[list[object]]]) -> None:
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
    # so routeRegistryChanged currently never fires (navigation only emits
    # currentRouteChanged, covered in tests/test_shell_router.py). If a
    # dynamic registry is ever added, it must emit this signal on change.
    router = ShellRouter()
    spy = QSignalSpy(router.routeRegistryChanged)

    for route in ("base", "winch", "monitor", "tuning", "launcher", "settings", "home"):
        router.navigateTo(route)

    assert spy.count() == 0


def test_shell_router_route_registry_returns_defensive_copy(qt_core_app) -> None:
    router = ShellRouter()

    registry = router.routeRegistry
    registry.append({"key": "bogus", "title": "Bogus", "order": 99})

    assert [entry["key"] for entry in router.routeRegistry] == [
        "home",
        "base",
        "winch",
        "monitor",
        "tuning",
        "launcher",
        "settings",
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
    return [(owner_key, name) for owner_key, hub in owners.items() for name in hub.signal_names]


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
def _spec_recording_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    video = _SignalHub("recordingStatusChanged", "baseRecordingStatusChanged")
    screen = _SignalHub("is_recording_changed", "recording_duration_changed", "free_space_gb_changed")
    bag = _SignalHub(
        "is_bag_recording_changed",
        "bag_recording_duration_changed",
        "is_compressing_changed",
        "bag_status_message_changed",
    )
    wrapper = qcc._RecordingStatus(video_stream_handler=video, screen_recorder=screen, ros_bag_recorder=bag)
    owners = {"video": video, "screen": screen, "bag": bag}
    return wrapper, owners, _table(owners)


def _spec_shell_connectivity_status() -> tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]:
    ssh = _SignalHub("deviceAvailabilityChanged", "configUpdated")
    heartbeat = _SignalHub("base_online_changed", "base_status_changed", "ef_online_changed", "ef_status_changed")
    winch = _SignalHub("available_changed")
    # WheelStatus per-property surface (TD-037 B)
    wheel = _SignalHub("availableChanged")
    wheel.available = True
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
    monitor = _SignalHub("battery_level_changed", "battery_remaining_time_changed", "cpu_temperature_changed")
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


# Blanket-changed wrappers still living in qml_context_composer.py.
# Migrated device status families use dedicated per-property tests below.
_FLEET_SPECS: dict[str, Callable[[], tuple[QObject, dict[str, _SignalHub], list[tuple[str, str]]]]] = {
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
        assert spy.count() == 1, f"{owner_key}.{signal_name}: expected exactly 1 changed emission, got {spy.count()}"


# ---------------------------------------------------------------------------
# WinchStatus (TD-037 Slice A) — per-property NOTIFY fleet
# ---------------------------------------------------------------------------


def _make_winch_controller_hub() -> _SignalHub:
    return _SignalHub(*(producer for producer, _ in WINCH_STATUS_SIGNAL_MAP))


def test_winch_status_connects_every_required_producer_signal(qt_core_app) -> None:
    hub = _make_winch_controller_hub()
    # Attach typed attribute defaults so property getters stay usable.
    for name, value in (
        ("available", True),
        ("enabled", False),
        ("load_detection_enabled", True),
        ("cable_length", 100.0),
        ("cable_speed", 1.0),
        ("winch_torque", 2.0),
        ("motor_temperature", 30.0),
        ("motor_voltage", 24.0),
        ("motor_brake", True),
        ("unusual_load_detected", False),
    ):
        setattr(hub, name, value)

    WinchStatus(hub)
    for producer, _ in WINCH_STATUS_SIGNAL_MAP:
        recorder = getattr(hub, producer)
        assert len(recorder.connections) == 1, f"{producer}: expected 1 connection"


def test_winch_status_raises_when_required_signal_missing(qt_core_app) -> None:
    hub = _SignalHub("available_changed")  # incomplete
    hub.available = True
    with pytest.raises(AttributeError, match="enabled_changed"):
        WinchStatus(hub)


@pytest.mark.parametrize(
    ("producer", "status_signal"),
    list(WINCH_STATUS_SIGNAL_MAP),
)
def test_winch_status_producer_emits_only_matching_property_notify(
    qt_core_app, producer: str, status_signal: str
) -> None:
    hub = _make_winch_controller_hub()
    for name, value in (
        ("available", True),
        ("enabled", False),
        ("load_detection_enabled", True),
        ("cable_length", 100.0),
        ("cable_speed", 1.0),
        ("winch_torque", 2.0),
        ("motor_temperature", 30.0),
        ("motor_voltage", 24.0),
        ("motor_brake", True),
        ("unusual_load_detected", False),
    ):
        setattr(hub, name, value)

    status = WinchStatus(hub)
    spies = {notify_name: QSignalSpy(getattr(status, notify_name)) for _, notify_name in WINCH_STATUS_SIGNAL_MAP}

    getattr(hub, producer).emit()

    for notify_name, spy in spies.items():
        if notify_name == status_signal:
            assert spy.count() == 1, f"{producer} should fire {notify_name}"
        else:
            assert spy.count() == 0, f"{producer} must not fire {notify_name}"


def test_winch_status_projects_controller_values(qt_core_app) -> None:
    hub = _make_winch_controller_hub()
    hub.available = True
    hub.enabled = True
    hub.load_detection_enabled = False
    hub.cable_length = 1234.5
    hub.cable_speed = -12.0
    hub.winch_torque = 9.5
    hub.motor_temperature = 41.0
    hub.motor_voltage = 23.5
    hub.motor_brake = False
    hub.unusual_load_detected = True

    status = WinchStatus(hub)
    assert status.available is True
    assert status.enabled is True
    assert status.loadDetectionEnabled is False
    assert status.cableLength == 1234.5
    assert status.cableSpeed == -12.0
    assert status.winchTorque == 9.5
    assert status.motorTemperature == 41.0
    assert status.motorVoltage == 23.5
    assert status.motorBrake is False
    assert status.unusualLoadDetected is True
    for name in WINCH_STATUS_PROPERTY_NAMES:
        assert hasattr(status, name), name


# ---------------------------------------------------------------------------
# WheelStatus (TD-037 Slice B)
# ---------------------------------------------------------------------------


def _make_wheel_controller_hub() -> _SignalHub:
    hub = _SignalHub(*(producer for producer, _ in WHEEL_STATUS_SIGNAL_MAP))
    for name, value in (
        ("available", True),
        ("enabled", True),
        ("left_motor_available", True),
        ("right_motor_available", False),
        ("left_wheel_speed", 1.0),
        ("right_wheel_speed", 2.0),
        ("left_wheel_current", 3.0),
        ("right_wheel_current", 4.0),
        ("left_wheel_position", 5.0),
        ("right_wheel_position", 6.0),
    ):
        setattr(hub, name, value)
    return hub


def test_wheel_status_connects_every_required_producer_signal(qt_core_app) -> None:
    hub = _make_wheel_controller_hub()
    status = WheelStatus(hub)
    assert status is not None
    for producer, _ in WHEEL_STATUS_SIGNAL_MAP:
        assert len(getattr(hub, producer).connections) == 1


def test_wheel_status_raises_when_required_signal_missing(qt_core_app) -> None:
    hub = _SignalHub("available_changed")
    hub.available = True
    with pytest.raises(AttributeError, match="enabled_changed"):
        WheelStatus(hub)


@pytest.mark.parametrize(
    ("producer", "status_signal"),
    list(WHEEL_STATUS_SIGNAL_MAP),
)
def test_wheel_status_producer_emits_only_matching_property_notify(
    qt_core_app, producer: str, status_signal: str
) -> None:
    hub = _make_wheel_controller_hub()
    status = WheelStatus(hub)
    spies = {notify_name: QSignalSpy(getattr(status, notify_name)) for _, notify_name in WHEEL_STATUS_SIGNAL_MAP}
    getattr(hub, producer).emit()
    for notify_name, spy in spies.items():
        if notify_name == status_signal:
            assert spy.count() == 1
        else:
            assert spy.count() == 0


def test_wheel_status_projects_controller_values(qt_core_app) -> None:
    hub = _make_wheel_controller_hub()
    status = WheelStatus(hub)
    assert status.available is True
    assert status.leftWheelSpeed == 1.0
    assert status.rightMotorAvailable is False
    for name in WHEEL_STATUS_PROPERTY_NAMES:
        assert hasattr(status, name)


def test_shell_connectivity_updates_on_wheel_available_changed(qt_core_app) -> None:
    """Regression: shell connectivity must not depend on removed wheel.changed."""
    wrapper, owners, _table = _spec_shell_connectivity_status()
    spy = QSignalSpy(wrapper.changed)
    owners["wheel"].availableChanged.emit()
    assert spy.count() == 1
    assert wrapper.wheelAvailable is True


# ---------------------------------------------------------------------------
# TeensyStatus (TD-037 Slice C) — cached fine-grained notify
# ---------------------------------------------------------------------------


def _make_teensy_controller_hub(all_status: dict | None = None) -> _SignalHub:
    hub = _SignalHub(
        "status_changed",
        "stability_enabled_changed",
        "auto_correction_enabled_changed",
        "spray_gun_leveling_changed",
        "roller_steering_enabled_changed",
        "swing_damping_enabled_changed",
        "spray_gun_led_changed",
    )
    hub.stability_enabled = True
    hub.auto_correction_enabled = False
    hub.spray_gun_leveling_enabled = True
    hub.roller_steering_enabled = False
    hub.swing_damping_enabled = True
    hub.spray_gun_led_on = False
    hub.all_status = (
        all_status
        if all_status is not None
        else {
            "enabled": True,
            "relay_on": False,
            "voltage": 24.0,
            "current": 1.0,
            "temperature": 30.0,
            "run_time": 10.0,
            "loop_time": 100.0,
            "loop_time_counter": 1.0,
            "imu_pitch": 1.0,
            "imu_roll": 2.0,
            "imu_yaw": 3.0,
            "yaw_command": 0.0,
            "yaw_pid_p": 0.1,
            "yaw_pid_i": 0.2,
            "yaw_pid_d": 0.3,
            "imu_acc_x": 0.0,
            "imu_acc_y": 0.0,
            "imu_acc_z": 0.0,
            "imu_angular_acc_x": 0.0,
            "imu_angular_acc_y": 0.0,
            "imu_angular_acc_z": 0.0,
            "arm_extension_dist": 0.0,
            "arm_rail_current": 0.0,
            "gimbal_pitch_motor_current": 0.0,
            "gimbal_pitch_motor_angle": 0.0,
            "top_rail_position": 100.0,
            "top_rail_speed": 0.0,
            "top_rail_current": 0.0,
            "arm_rail_position": 0.0,
            "arm_rail_speed": 0.0,
            "arm_sensor_dist": 0.0,
            "left_prop_position": 0.0,
            "right_prop_position": 0.0,
            "left_prop_pwm": 0,
            "right_prop_pwm": 0,
            "spray_gun_pitch": 0.0,
            "gimbal_pitch_motor_temp": 0.0,
            "gimbal_roll_motor_angle": 0.0,
            "gimbal_roll_motor_current": 0.0,
            "gimbal_roll_motor_temp": 0.0,
            "spray_gun_trigger": False,
            "yaw_enabled": False,
            "lidar_power": False,
        }
    )
    return hub


def test_teensy_status_connects_required_signals(qt_core_app) -> None:
    hub = _make_teensy_controller_hub()
    status = TeensyStatus(hub)
    assert status is not None
    assert len(hub.status_changed.connections) == 1
    assert len(hub.stability_enabled_changed.connections) == 1


def test_teensy_status_raises_when_status_changed_missing(qt_core_app) -> None:
    hub = _SignalHub("stability_enabled_changed")
    hub.stability_enabled = False
    hub.all_status = {}
    with pytest.raises(AttributeError, match="status_changed"):
        TeensyStatus(hub)


def test_teensy_status_diff_emits_only_changed_fields(qt_core_app) -> None:
    hub = _make_teensy_controller_hub()
    status = TeensyStatus(hub)

    pitch_spy = QSignalSpy(status.imuPitchChanged)
    roll_spy = QSignalSpy(status.imuRollChanged)
    voltage_spy = QSignalSpy(status.voltageChanged)

    # Change only imu_pitch in the snapshot; re-read path uses all_status.
    hub.all_status = {**hub.all_status, "imu_pitch": 9.5}
    hub.status_changed.emit(hub.all_status)

    assert pitch_spy.count() == 1
    assert status.imuPitch == 9.5
    assert roll_spy.count() == 0
    assert voltage_spy.count() == 0


def test_teensy_status_projects_seeded_values(qt_core_app) -> None:
    hub = _make_teensy_controller_hub()
    status = TeensyStatus(hub)
    assert status.imuPitch == 1.0
    assert status.topRailPosition == 100.0
    assert status.stabilityEnabled is True
    assert status.autoCorrectionEnabled is False
    for name in TEENS_STATUS_PROPERTY_NAMES:
        assert hasattr(status, name)


def test_teensy_status_discrete_enable_signal_updates_cache(qt_core_app) -> None:
    hub = _make_teensy_controller_hub()
    status = TeensyStatus(hub)
    spy = QSignalSpy(status.stabilityEnabledChanged)
    hub.stability_enabled = False
    hub.stability_enabled_changed.emit()
    assert spy.count() == 1
    assert status.stabilityEnabled is False


def test_teensy_status_paint_interval_coalesces_rapid_status_changed(qt_core_app) -> None:
    """P-04: rapid status_changed updates cache last-wins but NOTIFY at paint rate."""
    hub = _make_teensy_controller_hub()
    status = TeensyStatus(hub, paint_interval_s=1.0)
    pitch_spy = QSignalSpy(status.imuPitchChanged)

    hub.all_status = {**hub.all_status, "imu_pitch": 2.0}
    hub.status_changed.emit(hub.all_status)
    assert pitch_spy.count() == 1
    assert status.imuPitch == 2.0

    # Within paint window: no extra NOTIFY; pending holds latest.
    hub.all_status = {**hub.all_status, "imu_pitch": 3.0}
    hub.status_changed.emit(hub.all_status)
    hub.all_status = {**hub.all_status, "imu_pitch": 4.0}
    hub.status_changed.emit(hub.all_status)
    assert pitch_spy.count() == 1
    # Cache not flushed yet — property still shows last painted value.
    assert status.imuPitch == 2.0

    # Force paint window open.
    status._last_paint_at = 0.0
    hub.status_changed.emit(hub.all_status)
    assert pitch_spy.count() == 2
    assert status.imuPitch == 4.0


# ---------------------------------------------------------------------------
# ValveStatus / LidarStatus (TD-037 residual)
# ---------------------------------------------------------------------------


def _make_valve_controller_hub() -> _SignalHub:
    hub = _SignalHub(*(p for p, _ in VALVE_STATUS_SIGNAL_MAP))
    hub.valve_position = 42.0
    hub.valve_rate = 1.5
    hub.total_volume = 8.0
    hub.valve_motor_current = 0.7
    hub.valve_motor_connected = True
    hub.flow_meter_connected = False
    hub.esp32_connected = True
    return hub


def test_valve_status_connects_and_isolates_notifies(qt_core_app) -> None:
    hub = _make_valve_controller_hub()
    status = ValveStatus(hub)
    for producer, _ in VALVE_STATUS_SIGNAL_MAP:
        assert len(getattr(hub, producer).connections) == 1
    spies = {n: QSignalSpy(getattr(status, n)) for _, n in VALVE_STATUS_SIGNAL_MAP}
    hub.valve_position_changed.emit()
    assert spies["valvePositionChanged"].count() == 1
    assert spies["valveRateChanged"].count() == 0
    assert status.valvePosition == 42.0
    for name in VALVE_STATUS_PROPERTY_NAMES:
        assert hasattr(status, name)


def test_valve_status_raises_when_required_signal_missing(qt_core_app) -> None:
    hub = _SignalHub("valve_position_changed")
    with pytest.raises(AttributeError, match="valve_rate_changed"):
        ValveStatus(hub)


def _make_lidar_controller_hub() -> _SignalHub:
    hub = _SignalHub(*(p for p, _ in LIDAR_STATUS_SIGNAL_MAP))
    hub.distance = 1.25
    hub.angle = -3.5
    return hub


def test_lidar_status_connects_and_isolates_notifies(qt_core_app) -> None:
    hub = _make_lidar_controller_hub()
    status = LidarStatus(hub)
    for producer, _ in LIDAR_STATUS_SIGNAL_MAP:
        assert len(getattr(hub, producer).connections) == 1
    dist_spy = QSignalSpy(status.distanceChanged)
    angle_spy = QSignalSpy(status.angleChanged)
    hub.distance_changed.emit()
    assert dist_spy.count() == 1
    assert angle_spy.count() == 0
    assert status.distance == 1.25
    assert status.angle == -3.5
    for name in LIDAR_STATUS_PROPERTY_NAMES:
        assert hasattr(status, name)


def test_lidar_status_raises_when_required_signal_missing(qt_core_app) -> None:
    hub = _SignalHub("distance_changed")
    with pytest.raises(AttributeError, match="angle_changed"):
        LidarStatus(hub)


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
