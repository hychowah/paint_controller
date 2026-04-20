"""Tests for paint_controller.handlers.input.UIInputHandler."""

from __future__ import annotations

from unittest.mock import patch

from paint_controller.handlers.input import UIInputHandler
from paint_controller.utils.constants import ControlMode, JoystickControl


class FakeTeensy:
    def __init__(self) -> None:
        self.extend_calls: list[int] = []

    def extendArm(self, length: int) -> None:
        self.extend_calls.append(length)


class FakeOverlay:
    def __init__(self, controls: tuple[str, str]) -> None:
        self._controls = controls
        self.set_calls: list[tuple[str, str]] = []

    def get_current_joystick_controls(self) -> tuple[str, str]:
        return self._controls

    def set_joystick_controls(self, left_control: str, right_control: str) -> None:
        self.set_calls.append((left_control, right_control))


class FakeControlProcessor:
    def __init__(self) -> None:
        self.reset_winch_activation_calls = 0

    def reset_winch_activation(self) -> None:
        self.reset_winch_activation_calls += 1


class FakeWorkflowHandler:
    pass


class FakeStateStore:
    def __init__(self, control_mode: str) -> None:
        self.control_mode = control_mode


def _build_handler(
    control_mode: str,
    overlay_controls: tuple[str, str],
    popup_calls: list[tuple[str, str, str]],
    closed_popups: list[bool],
):
    overlay = FakeOverlay(overlay_controls)
    control_processor = FakeControlProcessor()
    state_store = FakeStateStore(control_mode)
    handler = UIInputHandler(
        teensy=FakeTeensy(),
        overlay=overlay,
        control_processor=control_processor,
        workflow_handler=FakeWorkflowHandler(),
        settings_manager=None,
        state_store=state_store,
        show_popup_fn=lambda title, message, popup_type: popup_calls.append((title, message, popup_type)),
        close_popup_fn=lambda: closed_popups.append(True),
    )
    return handler, overlay, control_processor, state_store


def test_switch_from_base_to_ef_closes_popup_and_restores_default_ef_controls(qt_app):
    popup_calls: list[tuple[str, str, str]] = []
    closed_popups: list[bool] = []
    handler, overlay, control_processor, state_store = _build_handler(
        control_mode=ControlMode.BASE,
        overlay_controls=(JoystickControl.TRACK_LEFT, JoystickControl.TRACK_RIGHT),
        popup_calls=popup_calls,
        closed_popups=closed_popups,
    )

    with patch("paint_controller.handlers.input.QTimer.singleShot", side_effect=lambda _delay, fn: fn()):
        handler.on_switch_pressed()

    assert closed_popups == [True]
    assert state_store.control_mode == ControlMode.END_EFFECTOR
    assert overlay.set_calls == [(JoystickControl.NONE, JoystickControl.WINCH_SPEED)]
    assert control_processor.reset_winch_activation_calls == 1
    assert popup_calls == [("Control Mode", "Switched to EF control mode", "info")]


def test_switch_from_ef_to_base_closes_popup_and_restores_default_track_controls(qt_app):
    popup_calls: list[tuple[str, str, str]] = []
    closed_popups: list[bool] = []
    handler, overlay, control_processor, state_store = _build_handler(
        control_mode=ControlMode.END_EFFECTOR,
        overlay_controls=(JoystickControl.NONE, JoystickControl.WINCH_SPEED),
        popup_calls=popup_calls,
        closed_popups=closed_popups,
    )

    with patch("paint_controller.handlers.input.QTimer.singleShot", side_effect=lambda _delay, fn: fn()):
        handler.on_switch_pressed()

    assert closed_popups == [True]
    assert state_store.control_mode == ControlMode.BASE
    assert overlay.set_calls == [(JoystickControl.TRACK_LEFT, JoystickControl.TRACK_RIGHT)]
    assert control_processor.reset_winch_activation_calls == 0
    assert popup_calls == [("Control Mode", "Switched to Base control mode (Track Control)", "info")]