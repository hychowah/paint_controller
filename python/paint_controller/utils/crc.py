"""CRC-8 checksum utility.

Extracted from ESP32ValveController to eliminate duplication between
UDPReceiveThread._validate_message() and ESP32ValveController._calculate_crc8().
"""


def crc8(data: bytes, polynomial: int = 0x07, init: int = 0xFF) -> int:
    """Calculate CRC-8 checksum over data bytes.

    Args:
        data: Bytes to checksum.
        polynomial: CRC polynomial (default 0x07 for CRC-8/CCITT).
        init: Initial CRC value (default 0xFF).

    Returns:
        Computed CRC-8 value (0-255).
    """
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ polynomial) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc
