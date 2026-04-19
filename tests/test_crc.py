"""Behavior tests for paint_controller.utils.crc."""

from paint_controller.utils.crc import crc8


def test_empty_data_returns_initial_crc_value() -> None:
    assert crc8(b"") == 0xFF


def test_single_byte_produces_byte_sized_checksum() -> None:
    result = crc8(b"\x00")
    assert 0 <= result <= 255


def test_same_input_is_deterministic() -> None:
    data = b"\xAA\x00\x01\x02\x03\x04"
    assert crc8(data) == crc8(data)


def test_different_messages_produce_different_crc_values() -> None:
    assert crc8(b"\x01\x02\x03") != crc8(b"\x04\x05\x06")


def test_known_esp32_message_crc_validates_trailing_checksum() -> None:
    message_without_crc = bytes([0xAA, 0x12, 0x00, 0x00, 0x00, 0x00])
    expected_crc = crc8(message_without_crc)
    full_message = message_without_crc + bytes([expected_crc])

    assert crc8(full_message[:-1]) == full_message[-1]


def test_custom_polynomial_changes_crc_value() -> None:
    data = b"\xAA\x55"
    default_crc = crc8(data)
    custom_crc = crc8(data, polynomial=0x1D)
    assert default_crc != custom_crc


def test_custom_init_changes_crc_value() -> None:
    data = b"\xAA\x55"
    default_crc = crc8(data)
    custom_crc = crc8(data, init=0x00)
    assert default_crc != custom_crc


def test_crc_output_stays_in_byte_range() -> None:
    for i in range(256):
        result = crc8(bytes([i]))
        assert 0 <= result <= 255
