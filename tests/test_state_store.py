"""Runtime tests for paint_controller.core.state_store.StateStore."""

from paint_controller.core.state_store import StateStore
from paint_controller.utils.constants import HeartbeatStatus


def test_state_store_defaults_are_initialized_consistently(qt_core_app):
    store = StateStore()

    assert store.control_mode == "base"
    assert store.display_message == ""
    assert store.controller_heartbeat_state == HeartbeatStatus.IDLE.value


def test_state_store_simple_properties_emit_once_on_change_and_not_on_duplicate(qt_core_app):
    store = StateStore()
    control_mode_events = []
    display_message_events = []

    store.control_mode_changed.connect(control_mode_events.append)
    store.display_message_changed.connect(display_message_events.append)

    store.control_mode = "ef"
    store.control_mode = "ef"
    store.display_message = "Ready"
    store.display_message = "Ready"

    assert control_mode_events == ["ef"]
    assert display_message_events == ["Ready"]
    assert store.control_mode == "ef"
    assert store.display_message == "Ready"


def test_state_store_heartbeat_state_emits_once_on_change(qt_core_app):
    store = StateStore()
    events = []

    store.controller_heartbeat_state_changed.connect(events.append)

    store.controller_heartbeat_state = HeartbeatStatus.WARNING.value
    store.controller_heartbeat_state = HeartbeatStatus.WARNING.value
    store.controller_heartbeat_state = HeartbeatStatus.ERROR.value

    assert events == [HeartbeatStatus.WARNING.value, HeartbeatStatus.ERROR.value]
    assert store.controller_heartbeat_state == HeartbeatStatus.ERROR.value
