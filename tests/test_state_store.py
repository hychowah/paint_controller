"""Runtime tests for paint_controller.core.state_store.StateStore."""

from paint_controller.core.state_store import StateStore
from paint_controller.utils.constants import HeartbeatStatus


def test_state_store_defaults_are_initialized_consistently(qt_core_app):
    store = StateStore()

    assert store.control_mode == "base"
    assert store.display_message == ""
    assert store.left_joystick_control == "None"
    assert store.right_joystick_control == "None"
    assert store.left_control_mode == "None"
    assert store.left_control_value == ""
    assert store.right_control_mode == "None"
    assert store.right_control_value == ""
    assert store.controller_heartbeat_state == HeartbeatStatus.IDLE.value


def test_state_store_simple_properties_emit_once_on_change_and_not_on_duplicate(qt_core_app):
    store = StateStore()
    control_mode_events = []
    display_message_events = []
    left_joystick_events = []
    right_joystick_events = []

    store.control_mode_changed.connect(control_mode_events.append)
    store.display_message_changed.connect(display_message_events.append)
    store.left_joystick_control_changed.connect(left_joystick_events.append)
    store.right_joystick_control_changed.connect(right_joystick_events.append)

    store.control_mode = "ef"
    store.control_mode = "ef"
    store.display_message = "Ready"
    store.display_message = "Ready"
    store.left_joystick_control = "Track Left"
    store.left_joystick_control = "Track Left"
    store.right_joystick_control = "Track Right"
    store.right_joystick_control = "Track Right"

    assert control_mode_events == ["ef"]
    assert display_message_events == ["Ready"]
    assert left_joystick_events == ["Track Left"]
    assert right_joystick_events == ["Track Right"]
    assert store.control_mode == "ef"
    assert store.display_message == "Ready"


def test_state_store_control_info_signals_use_current_companion_values(qt_core_app):
    store = StateStore()
    left_events = []
    right_events = []

    store.left_control_info_changed.connect(lambda mode, value: left_events.append((mode, value)))
    store.right_control_info_changed.connect(lambda mode, value: right_events.append((mode, value)))

    store.left_control_mode = "Track"
    store.left_control_mode = "Track"
    store.left_control_value = "150"
    store.left_control_value = "150"

    store.right_control_mode = "Yaw"
    store.right_control_value = "-12"
    store.right_control_value = "-12"

    assert left_events == [("Track", ""), ("Track", "150")]
    assert right_events == [("Yaw", ""), ("Yaw", "-12")]
    assert store.left_control_mode == "Track"
    assert store.left_control_value == "150"
    assert store.right_control_mode == "Yaw"
    assert store.right_control_value == "-12"


def test_state_store_heartbeat_state_emits_once_on_change(qt_core_app):
    store = StateStore()
    events = []

    store.controller_heartbeat_state_changed.connect(events.append)

    store.controller_heartbeat_state = HeartbeatStatus.WARNING.value
    store.controller_heartbeat_state = HeartbeatStatus.WARNING.value
    store.controller_heartbeat_state = HeartbeatStatus.ERROR.value

    assert events == [HeartbeatStatus.WARNING.value, HeartbeatStatus.ERROR.value]
    assert store.controller_heartbeat_state == HeartbeatStatus.ERROR.value
