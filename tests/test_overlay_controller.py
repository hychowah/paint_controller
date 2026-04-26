"""Direct regression coverage for the overlay compatibility surface."""

from __future__ import annotations

from paint_controller.models.joystick_selection import JoystickSelectionModel
from paint_controller.ui.overlay import OverlayController


def _build_overlay() -> tuple[JoystickSelectionModel, OverlayController]:
    model = JoystickSelectionModel()
    overlay = OverlayController(selection_model=model)
    return model, overlay


def test_left_menu_uses_temporary_selection_until_hide_commits(qt_app) -> None:
    model, overlay = _build_overlay()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    overlay.toggle_left_menu()

    assert overlay.show_overlay is True
    assert overlay.active_menu == "left"
    assert overlay.left_selected_index == 2
    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]

    overlay.move_down()

    assert overlay.left_selected_index == 3
    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]

    overlay._reset_input_lock()
    overlay.move_down()

    assert overlay.left_selected_index == 4
    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]

    overlay.hide_menu()

    assert overlay.show_overlay is False
    assert model.get_current_joystick_controls() == ["Wheel Travel Left", "Track Control Right"]


def test_system_menu_toggle_changes_visibility_without_committing_selection(qt_app) -> None:
    model, overlay = _build_overlay()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    overlay.toggle_system_menu()

    assert overlay.show_overlay is True
    assert overlay.active_menu == "system"
    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]

    overlay.toggle_system_menu()

    assert overlay.show_overlay is False
    assert overlay.active_menu == "system"
    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]


def test_hiding_yaw_selection_resets_temporary_indices(qt_app) -> None:
    model, overlay = _build_overlay()
    model.set_joystick_controls("EF Yaw Angle", "None")

    overlay.toggle_left_menu()
    overlay.hide_menu()

    assert model.get_current_joystick_controls() == ["EF Yaw Angle", "None"]
    assert model.display_left_index(show_overlay=True) == 0
    assert model.display_right_index(show_overlay=True) == 0