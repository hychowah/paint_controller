"""Pure Steam Deck HID report decoding helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional
import struct


_REPORT_LENGTH = 64


def _read_int16_le(data: bytes, offset: int) -> int:
    return struct.unpack("<h", data[offset:offset + 2])[0]


def parse_hid_frame(data: bytes) -> Optional[Dict[str, Any]]:
    """Decode one Steam Deck HID input frame.

    Returns ``None`` for short packets so callers can preserve the current
    ignore-on-short-frame behavior.
    """
    if len(data) < _REPORT_LENGTH:
        return None

    button_byte1 = data[8]
    button_byte2 = data[9]
    button_byte3 = data[10]
    button_byte4 = data[13]
    button_byte5 = data[14]

    return {
        "buttons": {
            "r2_click": bool(button_byte1 & (1 << 0)),
            "l2_click": bool(button_byte1 & (1 << 1)),
            "r1": bool(button_byte1 & (1 << 2)),
            "l1": bool(button_byte1 & (1 << 3)),
            "y": bool(button_byte1 & (1 << 4)),
            "b": bool(button_byte1 & (1 << 5)),
            "x": bool(button_byte1 & (1 << 6)),
            "a": bool(button_byte1 & (1 << 7)),
            "up": bool(button_byte2 & (1 << 0)),
            "right": bool(button_byte2 & (1 << 1)),
            "left": bool(button_byte2 & (1 << 2)),
            "down": bool(button_byte2 & (1 << 3)),
            "switch": bool(button_byte2 & (1 << 4)),
            "steam": bool(button_byte2 & (1 << 5)),
            "menu": bool(button_byte2 & (1 << 6)),
            "l5": bool(button_byte2 & (1 << 7)),
            "r5": bool(button_byte3 & (1 << 0)),
            "left_touchpad_touch": bool(button_byte3 & (1 << 3)),
            "right_touchpad_touch": bool(button_byte3 & (1 << 4)),
            "l3": bool(button_byte3 & (1 << 6)),
            "l4": bool(button_byte4 & (1 << 1)),
            "r4": bool(button_byte4 & (1 << 2)),
            "dot": bool(button_byte5 & (1 << 2)),
        },
        "imu": {
            "pitch": _read_int16_le(data, 38),
            "roll": _read_int16_le(data, 40),
            "yaw": _read_int16_le(data, 42),
        },
        "triggers": {
            "left": _read_int16_le(data, 44),
            "right": _read_int16_le(data, 46),
        },
        "sticks": {
            "left": {
                "x": _read_int16_le(data, 48),
                "y": _read_int16_le(data, 50),
            },
            "right": {
                "x": _read_int16_le(data, 52),
                "y": _read_int16_le(data, 54),
            },
        },
    }