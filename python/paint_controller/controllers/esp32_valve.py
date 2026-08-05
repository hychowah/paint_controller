#!/usr/bin/env python3
"""Pure ESP32 valve protocol + HAL (Level C P5) — no PySide6.

UDP transport, QThread, and timers live on ``esp32_valve_shell``.
"""

from __future__ import annotations

import logging
import struct
import time
from enum import IntEnum

from paint_controller.ports.notifier import DeviceNotifier, NullDeviceNotifier
from paint_controller.utils.crc import crc8

logger = logging.getLogger(__name__)


class MessageType(IntEnum):
    """UDP message type identifiers."""

    VALVE_STATUS = 0x00
    MOVE_VEL = 0x11
    TURN_VALVE = 0x12


START_BYTE = 0xAA


def build_udp_message(msg_type: MessageType, payload: bytes, *, start_byte: int = START_BYTE) -> bytes:
    """Build complete UDP message with CRC8 trailer."""
    message = bytes([start_byte, int(msg_type)]) + payload
    return message + bytes([crc8(message)])


def build_turn_valve_message(position_raw: int, *, start_byte: int = START_BYTE) -> bytes:
    """Pack TURN_VALVE command (position clamped 0–1000)."""
    position = max(0, min(1000, int(position_raw)))
    payload = struct.pack("<i", position)
    return build_udp_message(MessageType.TURN_VALVE, payload, start_byte=start_byte)


def parse_valve_status_frame(data: bytes, *, start_byte: int = START_BYTE) -> dict | None:
    """Parse a VALVE_STATUS UDP frame into a status dict, or None if invalid."""
    if len(data) != 15 or data[0] != start_byte:
        return None
    if crc8(data[:-1]) != data[-1]:
        return None
    if data[1] != MessageType.VALVE_STATUS:
        return None
    motor_current = struct.unpack("<h", data[2:4])[0]
    valve_pos = struct.unpack("<h", data[4:6])[0]
    flow_rate = struct.unpack("<h", data[6:8])[0]
    total_volume = struct.unpack("<i", data[8:12])[0]
    motor_connected = bool(data[12])
    flow_connected = bool(data[13])
    return {
        "motor_current": motor_current,
        "valve_position_raw": valve_pos,
        "valve_position": valve_pos / 100.0,
        "flow_rate": flow_rate / 100.0,
        "total_volume": total_volume / 100.0,
        "motor_connected": motor_connected,
        "flow_connected": flow_connected,
        "timestamp": time.time(),
    }


class Esp32ValveHal:
    """Valve state + command packing (Qt-free)."""

    def __init__(self, *, notifier: DeviceNotifier | None = None) -> None:
        self._notifier: DeviceNotifier = notifier if notifier is not None else NullDeviceNotifier()
        self._valve_position = 0.0
        self._valve_rate = 0.0
        self._total_volume = 0.0
        self._valve_motor_current = 0
        self._valve_motor_connected = False
        self._flow_meter_connected = False
        self._esp32_connected = False
        self._last_command = 0.0
        self._last_command_time = 0.0

    def apply_status(self, status: dict) -> None:
        """Apply UDP status snapshot and notify presentation signals."""
        self._valve_position = status["valve_position"]
        self._valve_rate = status["flow_rate"]
        self._total_volume = status["total_volume"]
        self._valve_motor_current = status["motor_current"]
        self._valve_motor_connected = status["motor_connected"]
        self._flow_meter_connected = status["flow_connected"]

        if not self._esp32_connected:
            self._esp32_connected = True
            self._notifier.notify("esp32_connected_changed")

        self._notifier.notify("valve_position_changed")
        self._notifier.notify("valve_rate_changed")
        self._notifier.notify("total_volume_changed")
        self._notifier.notify("valve_motor_current_changed")
        self._notifier.notify("valve_motor_connected_changed")
        self._notifier.notify("flow_meter_connected_changed")

    def mark_connection_lost(self) -> None:
        if self._esp32_connected:
            self._esp32_connected = False
            self._notifier.notify("esp32_connected_changed")
            if self._valve_motor_connected:
                self._valve_motor_connected = False
                self._notifier.notify("valve_motor_connected_changed")
            if self._flow_meter_connected:
                self._flow_meter_connected = False
                self._notifier.notify("flow_meter_connected_changed")

    def setValveTurn(self, position_pct: float) -> int:
        """Record operator command; return raw 0–1000 position for transport send."""
        position_pct = max(0.0, min(100.0, float(position_pct)))
        position_raw = int(position_pct * 10.0)
        self._last_command = position_pct
        self._last_command_time = time.time()
        return position_raw

    def keepalive_raw_position(self) -> int | None:
        """Return raw position for keepalive, or None if a recent command was sent."""
        if time.time() - self._last_command_time < 1.0:
            return None
        return int(self._last_command * 10.0)

    def turn_message_for_pct(self, position_pct: float) -> bytes:
        raw = self.setValveTurn(position_pct)
        return build_turn_valve_message(raw)

    def turn_message_for_raw(self, position_raw: int) -> bytes:
        return build_turn_valve_message(position_raw)

    @property
    def valve_position(self) -> float:
        return self._valve_position

    @property
    def valve_rate(self) -> float:
        return self._valve_rate

    @property
    def total_volume(self) -> float:
        return self._total_volume

    @property
    def valve_motor_current(self) -> int:
        return self._valve_motor_current

    @property
    def valve_motor_connected(self) -> bool:
        return self._valve_motor_connected

    @property
    def flow_meter_connected(self) -> bool:
        return self._flow_meter_connected

    @property
    def esp32_connected(self) -> bool:
        return self._esp32_connected
