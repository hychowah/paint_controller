"""Pure HID report tests for the Steam Deck parser."""

from __future__ import annotations

from paint_controller.utils.steam_deck_hid import parse_hid_frame


def _empty_report(length: int = 64) -> bytearray:
    return bytearray(length)


def _write_i16(report: bytearray, offset: int, value: int) -> None:
    report[offset : offset + 2] = int(value).to_bytes(2, byteorder="little", signed=True)


def test_parse_hid_frame_returns_none_for_short_packets():
    assert parse_hid_frame(b"") is None
    assert parse_hid_frame(bytes(63)) is None


def test_parse_hid_frame_extracts_button_bits_and_ignores_tail():
    report = _empty_report(65)
    report[8] = (1 << 7) | (1 << 2) | (1 << 0)
    report[9] = (1 << 6) | (1 << 4) | (1 << 0)
    report[10] = (1 << 6) | (1 << 4) | (1 << 0)
    report[13] = (1 << 2) | (1 << 1)
    report[14] = 1 << 2

    parsed = parse_hid_frame(bytes(report))

    assert parsed is not None
    assert parsed["buttons"]["a"] is True
    assert parsed["buttons"]["r1"] is True
    assert parsed["buttons"]["r2_click"] is True
    assert parsed["buttons"]["up"] is True
    assert parsed["buttons"]["switch"] is True
    assert parsed["buttons"]["menu"] is True
    assert parsed["buttons"]["r5"] is True
    assert parsed["buttons"]["right_touchpad_touch"] is True
    assert parsed["buttons"]["l3"] is True
    assert parsed["buttons"]["l4"] is True
    assert parsed["buttons"]["r4"] is True
    assert parsed["buttons"]["dot"] is True


def test_parse_hid_frame_extracts_signed_analog_values():
    report = _empty_report()
    _write_i16(report, 38, -32768)
    _write_i16(report, 40, -1)
    _write_i16(report, 42, 32767)
    _write_i16(report, 44, 123)
    _write_i16(report, 46, -456)
    _write_i16(report, 48, 789)
    _write_i16(report, 50, -987)
    _write_i16(report, 52, 1357)
    _write_i16(report, 54, -2468)

    parsed = parse_hid_frame(bytes(report))

    assert parsed is not None
    assert parsed["imu"] == {"pitch": -32768, "roll": -1, "yaw": 32767}
    assert parsed["triggers"] == {"left": 123, "right": -456}
    assert parsed["sticks"] == {
        "left": {"x": 789, "y": -987},
        "right": {"x": 1357, "y": -2468},
    }


def test_parse_hid_frame_exposes_auxiliary_buttons_for_future_use():
    report = _empty_report()
    report[8] = 1 << 1
    report[10] = 1 << 3

    parsed = parse_hid_frame(bytes(report))

    assert parsed is not None
    assert parsed["buttons"]["l2_click"] is True
    assert parsed["buttons"]["left_touchpad_touch"] is True
