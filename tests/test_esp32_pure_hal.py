"""Level C P5: pure ESP32 protocol/HAL + transport shell contracts."""

from __future__ import annotations

from paint_controller.controllers.esp32_valve import (
    Esp32ValveHal,
    MessageType,
    build_turn_valve_message,
    build_udp_message,
    parse_valve_status_frame,
)
from paint_controller.ports.notifier import RecordingDeviceNotifier
from paint_controller.utils.crc import crc8


def test_build_turn_valve_message_has_valid_crc() -> None:
    msg = build_turn_valve_message(500)
    assert msg[0] == 0xAA
    assert msg[1] == MessageType.TURN_VALVE
    assert crc8(msg[:-1]) == msg[-1]


def test_parse_status_roundtrip() -> None:
    import struct

    # Layout matches UDPReceiveThread: h h h i B B  (12 bytes payload)
    payload = (
        struct.pack("<h", 10)  # motor_current
        + struct.pack("<h", 2500)  # valve_pos raw (25.00%)
        + struct.pack("<h", 100)  # flow_rate raw
        + struct.pack("<i", 1234)  # total_volume raw
        + bytes([1, 1])  # motor_connected, flow_connected
    )
    assert len(payload) == 12
    body = bytes([0xAA, int(MessageType.VALVE_STATUS)]) + payload
    frame = body + bytes([crc8(body)])
    status = parse_valve_status_frame(frame)
    assert status is not None
    assert status["valve_position"] == 25.0
    assert status["motor_connected"] is True


def test_esp32_hal_apply_and_set_valve(fake_node=None) -> None:
    rec = RecordingDeviceNotifier()
    hal = Esp32ValveHal(notifier=rec)
    raw = hal.setValveTurn(50.0)
    assert raw == 500
    assert hal._last_command == 50.0
    hal.apply_status(
        {
            "valve_position": 12.0,
            "flow_rate": 1.0,
            "total_volume": 2.0,
            "motor_current": 3,
            "motor_connected": True,
            "flow_connected": True,
        }
    )
    assert hal.valve_position == 12.0
    assert "valve_position_changed" in rec.names
    assert "esp32_connected_changed" in rec.names


def test_esp32_shell_delegates_set_valve(qt_app, fake_node, monkeypatch) -> None:
    from paint_controller.controllers.esp32_valve_shell import ESP32ValveController

    # Avoid real discovery/network during construction side effects where possible.
    monkeypatch.setattr(
        ESP32ValveController,
        "_discover_and_connect",
        lambda self: None,
    )
    ctrl = ESP32ValveController(fake_node)
    sent: list[int] = []

    def fake_send(raw: int) -> None:
        sent.append(raw)

    monkeypatch.setattr(ctrl, "_send_turn_valve", fake_send)
    ctrl.setValveTurn(25.0)
    assert sent == [250]
    assert ctrl.valve_position == 0.0  # no status yet
    ctrl._handle_status(
        {
            "valve_position": 5.0,
            "flow_rate": 0.0,
            "total_volume": 0.0,
            "motor_current": 0,
            "motor_connected": False,
            "flow_connected": False,
        }
    )
    assert ctrl.valve_position == 5.0
    ctrl.cleanup()
