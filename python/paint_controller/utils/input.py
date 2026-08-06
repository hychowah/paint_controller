"""Reusable input utilities for button press detection and deadzone tracking."""

from __future__ import annotations

import time
from typing import Any


def input_axes_active(input_state: dict[str, Any] | None, threshold: float = 1638.4) -> bool:
    """True when any stick/trigger axis exceeds ``threshold`` (default ~5% of 32768).

    Used by continuous teleop idle early-out (P-03). Pure function — no Qt.
    """
    if not input_state:
        return False
    for stick_name in ("left_stick", "right_stick"):
        stick = input_state.get(stick_name) or {}
        try:
            if abs(float(stick.get("x", 0.0) or 0.0)) > threshold:
                return True
            if abs(float(stick.get("y", 0.0) or 0.0)) > threshold:
                return True
        except (TypeError, ValueError):
            continue
    triggers = input_state.get("triggers") or {}
    try:
        if abs(float(triggers.get("left", 0.0) or 0.0)) > threshold:
            return True
        if abs(float(triggers.get("right", 0.0) or 0.0)) > threshold:
            return True
    except (TypeError, ValueError):
        pass
    return False


class DoublePressDetector:
    """Detects double-press patterns on a button.

    Tracks the time between consecutive presses and reports whether
    the second press occurred within the threshold window.

    Usage:
        detector = DoublePressDetector(threshold=1.0)
        is_double = detector.press()  # False (first press)
        is_double = detector.press()  # True if within 1 second
    """

    def __init__(self, threshold: float = 1.0):
        self._threshold = threshold
        self._last_press_time = 0.0

    def press(self) -> bool:
        """Register a press and return True if it's a double-press."""
        current_time = time.time()
        time_since_last = current_time - self._last_press_time
        self._last_press_time = current_time
        return time_since_last <= self._threshold


class DeadzoneTracker:
    """Tracks deadzone state for a control axis.

    When a value enters the deadzone, commands continue for a timeout period
    then stop. When the value leaves the deadzone, commands resume immediately.

    Usage:
        tracker = DeadzoneTracker(timeout=2.0)
        should_send = tracker.update(normalized_value=0.01, threshold=0.05)
    """

    def __init__(self, timeout: float = 2.0):
        self._timeout = timeout
        self._in_deadzone = False
        self._deadzone_start_time = 0.0
        self._should_send = True

    @property
    def should_send(self) -> bool:
        return self._should_send

    @property
    def in_deadzone(self) -> bool:
        return self._in_deadzone

    def update(self, normalized_value: float, threshold: float) -> bool:
        """Update deadzone state and return whether commands should be sent.

        Args:
            normalized_value: Current value normalized to 0-1 range.
            threshold: Deadzone threshold (e.g., 0.05 for 5%).

        Returns:
            True if commands should be sent, False if suppressed.
        """
        current_time = time.monotonic()

        if normalized_value <= threshold:
            if not self._in_deadzone:
                # Just entered deadzone
                self._in_deadzone = True
                self._deadzone_start_time = current_time
                self._should_send = True
            else:
                # Already in deadzone — check timeout
                if current_time - self._deadzone_start_time >= self._timeout:
                    self._should_send = False
        else:
            # Outside deadzone — reset
            self._in_deadzone = False
            self._should_send = True

        return self._should_send

    def reset(self):
        """Reset to initial state."""
        self._in_deadzone = False
        self._deadzone_start_time = 0.0
        self._should_send = True
