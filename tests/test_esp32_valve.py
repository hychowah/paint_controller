"""Tests for paint_controller.controllers.esp32_valve.ESP32ValveController."""

from __future__ import annotations

import importlib
import socket
import time


class FakeSocket:
    def __init__(self) -> None:
        self.sent = []
        self.closed = False

    def sendto(self, payload: bytes, destination: tuple[str, int]) -> None:
        self.sent.append((payload, destination))

    def close(self) -> None:
        self.closed = True


class FakeTimer:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class FakeUdpThread:
    def __init__(self, wait_result: bool = True) -> None:
        self.stop_calls = 0
        self.wait_calls = []
        self.terminate_calls = 0
        self.wait_result = wait_result

    def stop(self) -> None:
        self.stop_calls += 1

    def wait(self, timeout: int) -> bool:
        self.wait_calls.append(timeout)
        return self.wait_result

    def terminate(self) -> None:
        self.terminate_calls += 1


class FakeSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback) -> None:
        self._callbacks.append(callback)

    def emit(self) -> None:
        for callback in list(self._callbacks):
            callback()


class FakeRetiredThread:
    def __init__(self, *, running: bool) -> None:
        self._running = running
        self.finished = FakeSignal()
        self.delete_later_calls = 0

    def isRunning(self) -> bool:
        return self._running

    def deleteLater(self) -> None:
        self.delete_later_calls += 1


def _esp32_controller_class():
    return importlib.import_module("paint_controller.controllers.esp32_valve").ESP32ValveController


def _message_type():
    return importlib.import_module("paint_controller.controllers.esp32_valve").MessageType


def _float32_class():
    return importlib.import_module("std_msgs.msg").Float32


def test_set_valve_turn_clamps_and_tracks_last_command(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    sent_positions = []

    monkeypatch.setattr(controller, "_send_turn_valve", lambda raw: sent_positions.append(raw))

    try:
        controller.setValveTurn(150.0)
        assert sent_positions == [1000]
        assert controller._last_command == 100.0

        controller.setValveTurn(-5.0)
        assert sent_positions[-1] == 0
        assert controller._last_command == 0.0
    finally:
        controller._disconnect()


def test_keepalive_resends_last_command_only_after_idle_threshold(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    sent_positions = []
    controller._esp32_connected = True
    controller._last_command = 42.5

    monkeypatch.setattr(controller, "_send_turn_valve", lambda raw: sent_positions.append(raw))
    monkeypatch.setattr(time, "time", lambda: 10.5)
    controller._last_command_time = 10.0
    controller._send_keepalive()
    assert sent_positions == []

    monkeypatch.setattr(time, "time", lambda: 11.1)
    controller._send_keepalive()

    try:
        assert sent_positions == [425]
    finally:
        controller._disconnect()


def test_send_turn_valve_clamps_raw_message_and_destination(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    controller._esp32_ip = "192.168.0.50"
    controller._sock = FakeSocket()

    try:
        controller._send_turn_valve(9999)
        payload, destination = controller._sock.sent[-1]
        assert destination == ("192.168.0.50", controller.RECEIVE_PORT)
        assert payload[0] == controller.START_BYTE
        assert payload[1] == _message_type().TURN_VALVE
        assert int.from_bytes(payload[2:6], byteorder="little", signed=True) == 1000
    finally:
        controller._disconnect()


def test_handle_status_and_publish_status_update_properties(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    status = {
        "valve_position": 37.5,
        "flow_rate": 1.25,
        "total_volume": 9.5,
        "motor_current": 17,
        "motor_connected": True,
        "flow_connected": True,
        "timestamp": 123.0,
    }
    monkeypatch.setattr(time, "time", lambda: 5.0)

    try:
        controller._handle_status(status)
        controller._publish_status()

        published = fake_node.publishers[0].published_messages[-1]
        assert controller.valve_position == 37.5
        assert controller.valve_rate == 1.25
        assert controller.total_volume == 9.5
        assert controller.valve_motor_current == 17
        assert controller.valve_motor_connected is True
        assert controller.flow_meter_connected is True
        assert controller.esp32_connected is True
        assert published.valve_position == 37.5
        assert published.valve_rate == 1.25
        assert published.total_volume == 9.5
        assert published.valve_motor_current == 17
    finally:
        controller._disconnect()


def test_command_callback_clamps_percent_and_sends_raw_position(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    sent_positions = []
    monkeypatch.setattr(controller, "_send_turn_valve", lambda raw: sent_positions.append(raw))
    msg = _float32_class()()
    msg.data = 125.0

    try:
        controller._command_callback(msg)
        assert sent_positions == [1000]
        assert controller._last_command == 100.0
    finally:
        controller._disconnect()


def test_cleanup_stops_timers_and_udp_thread(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    reconnect_timer = FakeTimer()
    keepalive_timer = FakeTimer()
    publish_timer = FakeTimer()
    udp_thread = FakeUdpThread(wait_result=True)
    fake_socket = FakeSocket()

    controller._reconnect_timer = reconnect_timer
    controller._keepalive_timer = keepalive_timer
    controller._publish_timer = publish_timer
    controller._udp_thread = udp_thread
    controller._sock = fake_socket

    controller.cleanup()

    assert reconnect_timer.stopped is True
    assert keepalive_timer.stopped is True
    assert publish_timer.stopped is True
    assert udp_thread.stop_calls == 1
    assert udp_thread.wait_calls == [1000]
    assert udp_thread.terminate_calls == 0
    assert fake_socket.closed is True
    assert controller._udp_thread is None
    assert controller._sock is None


def test_check_reconnect_does_not_wait_for_udp_thread(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    udp_thread = FakeUdpThread(wait_result=True)
    fake_socket = FakeSocket()
    discover_calls = []

    controller._esp32_connected = False
    controller._udp_thread = udp_thread
    controller._sock = fake_socket
    monkeypatch.setattr(controller, "_discover_and_connect", lambda: discover_calls.append(True))

    controller._check_reconnect()

    assert udp_thread.stop_calls == 1
    assert udp_thread.wait_calls == []
    assert fake_socket.closed is True
    assert discover_calls == [True]


def test_track_retired_thread_skips_already_finished_threads(monkeypatch, qt_app, fake_node):
    controller_cls = _esp32_controller_class()
    monkeypatch.setattr(controller_cls, "_discover_and_connect", lambda self: None)
    controller = controller_cls(fake_node)
    retired_thread = FakeRetiredThread(running=False)

    controller._track_retired_thread(retired_thread)

    assert controller._retired_udp_threads == []
    assert retired_thread.delete_later_calls == 1