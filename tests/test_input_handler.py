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


def _make_handler(
    *,
    selection_model: JoystickSelectionModel | None = None,
    control_processor: FakeControlProcessor | None = None,
    state_store: FakeStateStore | None = None,
    popup_calls: list | None = None,
    closed_popups: list | None = None,
) -> tuple[UIInputHandler, JoystickSelectionModel, FakeControlProcessor, FakeStateStore, list, list]:
    model = selection_model or JoystickSelectionModel()
    processor = control_processor or FakeControlProcessor()
    store = state_store or FakeStateStore(ControlMode.BASE)
    popups: list = popup_calls if popup_calls is not None else []
    closed: list = closed_popups if closed_popups is not None else []
    handler = UIInputHandler(
        teensy=FakeTeensy(),
        overlay=OverlayController(selection_model=model),
        selection_model=model,
        control_processor=processor,
        settings_manager=None,
        state_store=store,
        show_popup_fn=lambda title, message, popup_type: popups.append((title, message, popup_type)),
        close_popup_fn=lambda: closed.append(True),
    )
    return handler, model, processor, store, popups, closed


def test_switch_control_mode_to_ef_applies_defaults_and_resets_winch(qt_app, monkeypatch) -> None:
    import paint_controller.handlers.input as input_module

    deferred: list = []
    monkeypatch.setattr(
        input_module.QTimer,
        "singleShot",
        staticmethod(lambda _ms, callback: deferred.append(callback)),
    )
    handler, model, processor, store, popups, closed = _make_handler()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    handler.switch_control_mode(ControlMode.END_EFFECTOR)

    assert store.control_mode == ControlMode.END_EFFECTOR.value
    assert model.get_current_joystick_controls() == ["None", "Winch Speed"]
    assert processor.reset_winch_activation_calls == 1
    assert closed == [True]
    assert deferred  # popup deferred
    deferred[0]()
    assert popups[-1][0] == "Control Mode"
    assert "EF" in popups[-1][1]


def test_switch_control_mode_round_trip_restores_remembered_sticks(qt_app, monkeypatch) -> None:
    import paint_controller.handlers.input as input_module

    monkeypatch.setattr(
        input_module.QTimer,
        "singleShot",
        staticmethod(lambda _ms, _callback: None),
    )
    handler, model, processor, store, _popups, _closed = _make_handler()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    handler.switch_control_mode(ControlMode.END_EFFECTOR)
    model.set_joystick_controls("EF arm", "EF Yaw Angle")
    handler.switch_control_mode(ControlMode.BASE)

    assert store.control_mode == ControlMode.BASE.value
    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]
    assert processor.reset_winch_activation_calls == 1  # only on EF enter

    handler.switch_control_mode(ControlMode.END_EFFECTOR)
    assert model.get_current_joystick_controls() == ["EF arm", "EF Yaw Angle"]
    assert processor.reset_winch_activation_calls == 2


def test_switch_control_mode_same_mode_is_noop(qt_app, monkeypatch) -> None:
    import paint_controller.handlers.input as input_module

    monkeypatch.setattr(
        input_module.QTimer,
        "singleShot",
        staticmethod(lambda _ms, _callback: None),
    )
    handler, model, processor, store, _popups, closed = _make_handler()
    model.set_joystick_controls("EF arm", "Winch Speed")
    store.control_mode = ControlMode.END_EFFECTOR.value

    handler.switch_control_mode(ControlMode.END_EFFECTOR)

    assert model.get_current_joystick_controls() == ["EF arm", "Winch Speed"]
    assert processor.reset_winch_activation_calls == 0
    assert closed == []
