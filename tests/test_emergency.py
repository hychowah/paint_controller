"""Tests for paint_controller.handlers.emergency.EmergencyButtonHandler."""

from __future__ import annotations

from unittest.mock import patch

from paint_controller.handlers.emergency import EmergencyButtonHandler


class FakeWinch:
    def __init__(self) -> None:
        self.commanded_rpm: list[float] = []

    def command_speed_rpm(self, speed: float) -> bool:
        self.commanded_rpm.append(speed)
        return True


class FakeTeensy:
    def __init__(self) -> None:
        self.trigger_values: list[int] = []

    def setSprayTrigger(self, value: int) -> None:
        self.trigger_values.append(value)


class FakeWheel:
    def __init__(self) -> None:
        self.emergency_stop_calls = 0
        self.speed_commands: list[tuple[int, int]] = []

    def emergency_stop(self) -> None:
        self.emergency_stop_calls += 1

    def setSpeed(self, left_rpm: int, right_rpm: int) -> None:
        self.speed_commands.append((left_rpm, right_rpm))


def _build_handler(show_popup_fn=None) -> tuple[EmergencyButtonHandler, FakeWinch, FakeTeensy, FakeWheel]:
    winch = FakeWinch()
    teensy = FakeTeensy()
    wheel = FakeWheel()
    handler = EmergencyButtonHandler(
        steam_deck_handler=None,
        winch=winch,
        teensy=teensy,
        wheel=wheel,
        show_popup_fn=show_popup_fn,
        logger=None,
    )
    return handler, winch, teensy, wheel


def test_release_before_threshold_cancels_without_trigger(qt_app):
    handler, winch, teensy, wheel = _build_handler()
    overlay_events: list[tuple[bool, float, float]] = []
    emergency_count: list[bool] = []
    handler.overlay_changed.connect(lambda visible, current, target: overlay_events.append((visible, current, target)))
    handler.emergency_triggered.connect(lambda: emergency_count.append(True))

    with patch("paint_controller.handlers.emergency.time.time", side_effect=[0.0, 0.05, 0.06]):
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": False})

    assert len(overlay_events) == 3
    assert overlay_events[0] == (True, 0.0, 0.2)
    assert overlay_events[1] == (True, 0.05, 0.2)
    assert overlay_events[2] == (False, 0, 0)
    assert emergency_count == []
    assert winch.commanded_rpm == []
    assert teensy.trigger_values == []
    assert wheel.emergency_stop_calls == 0


def test_hold_past_threshold_triggers_all_emergency_actions(qt_app):
    popup_calls: list[tuple[str, str, str, int]] = []
    handler, winch, teensy, wheel = _build_handler(show_popup_fn=lambda *args: popup_calls.append(args))
    overlay_events: list[tuple[bool, float, float]] = []
    emergency_count: list[bool] = []
    handler.overlay_changed.connect(lambda visible, current, target: overlay_events.append((visible, current, target)))
    handler.emergency_triggered.connect(lambda: emergency_count.append(True))

    with patch("paint_controller.handlers.emergency.time.time", side_effect=[1.0, 1.25]):
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": True})

    assert winch.commanded_rpm == [0]
    assert teensy.trigger_values == [1000]
    assert wheel.emergency_stop_calls == 1
    assert popup_calls == [("EMERGENCY", "Emergency stop activated!", "error", 1000)]
    assert emergency_count == [True]
    assert overlay_events[0][0] is True
    assert overlay_events[-1] == (False, 0, 0)


def test_cooldown_blocks_immediate_retrigger_then_allows_new_trigger(qt_app):
    handler, winch, teensy, wheel = _build_handler()

    with patch(
        "paint_controller.handlers.emergency.time.time",
        side_effect=[0.0, 0.25, 0.30, 0.40, 0.45, 1.50, 1.60, 1.85],
    ):
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": False})
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": False})
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": True})

    assert winch.commanded_rpm == [0, 0]
    assert teensy.trigger_values == [1000, 1000]
    assert wheel.emergency_stop_calls == 2


def test_force_reset_bypasses_cooldown_and_allows_immediate_reuse(qt_app):
    handler, winch, teensy, wheel = _build_handler()

    with patch("paint_controller.handlers.emergency.time.time", side_effect=[5.0, 5.3]):
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": True})

    handler.force_reset()

    with patch("paint_controller.handlers.emergency.time.time", side_effect=[5.35, 5.60]):
        handler.check_emergency_button({"steam": True})
        handler.check_emergency_button({"steam": True})

    assert winch.commanded_rpm == [0, 0]
    assert teensy.trigger_values == [1000, 1000]
    assert wheel.emergency_stop_calls == 2