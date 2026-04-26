"""Direct tests for joystick selection ownership separate from overlay presentation."""

from __future__ import annotations

from paint_controller.models.joystick_selection import JoystickSelectionModel


def test_selection_model_commits_temporary_selection_independently(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    model.initialize_temporary_selection()
    model.move_selection_down("left")
    model.move_selection_down("left")

    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]
    assert model.display_left_index(show_overlay=True) != model.display_left_index(show_overlay=False)

    model.commit_temporary_selection()

    assert model.get_current_joystick_controls() == ["Wheel Travel Left", "Track Control Right"]


def test_selection_model_prevents_duplicate_non_track_selection(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "None")

    model.initialize_temporary_selection()
    model.move_selection_to_last("right")

    assert model.get_current_joystick_controls() == ["Winch Speed", "None"]
    assert model.display_right_index(show_overlay=True) != 1


def test_selection_model_allows_independent_track_selection_on_both_sides(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    model.initialize_temporary_selection()
    model.move_selection_to_first("right")
    model.move_selection_down("right")
    model.move_selection_down("right")

    model.commit_temporary_selection()

    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Left"]