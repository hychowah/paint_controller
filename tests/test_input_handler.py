"""Tests for paint_controller.handlers.input.UIInputHandler."""

from __future__ import annotations

from paint_controller.handlers.input import UIInputHandler
from paint_controller.models.joystick_selection import JoystickSelectionModel
from paint_controller.ui.overlay import OverlayController
from paint_controller.utils.constants import ControlMode


class FakeTeensy:
    def __init__(self) -> None:
        self.extend_calls: list[int] = []
        self.thrust_force_enabled = False
        self.thrust_force_set: list[bool] = []

    def extendArm(self, length: int) -> None:
        self.extend_calls.append(length)

    def set_thrust_force_enabled(self, enabled: bool) -> None:
        self.thrust_force_enabled = enabled
        self.thrust_force_set.append(enabled)


class FakeControlProcessor:
    def __init__(self) -> None:
        self.reset_winch_activation_calls = 0
        self.wheel_travel_calls = 0

    def reset_winch_activation(self) -> None:
        self.reset_winch_activation_calls += 1

    def send_wheel_travel_command(self) -> None:
        self.wheel_travel_calls += 1


class FakeStateStore:
    def __init__(self, control_mode: str) -> None:
        self.control_mode = control_mode


def test_menu_buttons_delegate_active_menu_selection_to_overlay(qt_app) -> None:
    popup_calls: list[tuple[str, str, str]] = []
    closed_popups: list[bool] = []
    selection_model = JoystickSelectionModel()
    overlay = OverlayController(selection_model=selection_model)
    handler = UIInputHandler(
        teensy=FakeTeensy(),
        overlay=overlay,
        selection_model=selection_model,
        control_processor=FakeControlProcessor(),
        settings_manager=None,
        state_store=FakeStateStore(ControlMode.BASE),
        show_popup_fn=lambda title, message, popup_type: popup_calls.append((title, message, popup_type)),
        close_popup_fn=lambda: closed_popups.append(True),
    )

    handler.on_r4_pressed()
    assert overlay.show_overlay is True
    assert overlay.active_menu == "right"

    handler.on_l4_pressed()
    assert overlay.active_menu == "left"

    handler.on_menu_pressed()
    assert overlay.active_menu == "system"


def test_l1_toggles_thrust_force(qt_app) -> None:
    popup_calls: list[tuple[str, str, str]] = []
    teensy = FakeTeensy()
    handler = UIInputHandler(
        teensy=teensy,
        overlay=OverlayController(selection_model=JoystickSelectionModel()),
        selection_model=JoystickSelectionModel(),
        control_processor=FakeControlProcessor(),
        settings_manager=None,
        state_store=FakeStateStore(ControlMode.BASE),
        show_popup_fn=lambda title, message, popup_type: popup_calls.append((title, message, popup_type)),
        close_popup_fn=lambda: None,
    )

    handler.on_l1_pressed()
    assert teensy.thrust_force_set == [True]
    assert popup_calls[-1][0] == "Thrust Force"
