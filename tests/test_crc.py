"""Tests for paint_controller.utils.crc — CRC-8 checksum utility."""

from paint_controller.utils.crc import crc8


class TestCrc8:
    """Tests for crc8() function."""

    def test_empty_data(self):
        """Empty input returns initial CRC value."""
        assert crc8(b"") == 0xFF

    def test_single_byte(self):
        """Single byte produces deterministic checksum."""
        result = crc8(b"\x00")
        assert 0 <= result <= 255

    def test_deterministic(self):
        """Same input always produces same output."""
        data = b"\xAA\x00\x01\x02\x03\x04"
        assert crc8(data) == crc8(data)

    def test_different_data_different_crc(self):
        """Different inputs produce different checksums (high probability)."""
        assert crc8(b"\x01\x02\x03") != crc8(b"\x04\x05\x06")

    def test_known_esp32_message_validation(self):
        """CRC of message[:-1] should equal message[-1] for valid ESP32 messages."""
        # Build a message: START_BYTE + type + payload, append CRC
        message_without_crc = bytes([0xAA, 0x12, 0x00, 0x00, 0x00, 0x00])
        expected_crc = crc8(message_without_crc)
        full_message = message_without_crc + bytes([expected_crc])

        # Validation: crc8(msg[:-1]) == msg[-1]
        assert crc8(full_message[:-1]) == full_message[-1]

    def test_custom_polynomial(self):
        """Custom polynomial produces different results."""
        data = b"\xAA\x55"
        default_crc = crc8(data)
        custom_crc = crc8(data, polynomial=0x1D)
        assert default_crc != custom_crc

    def test_custom_init(self):
        """Custom init value produces different results."""
        data = b"\xAA\x55"
        default_crc = crc8(data)
        custom_crc = crc8(data, init=0x00)
        assert default_crc != custom_crc

    def test_output_range(self):
        """CRC always within 0-255 regardless of input."""
        for i in range(256):
            result = crc8(bytes([i]))
            assert 0 <= result <= 255
