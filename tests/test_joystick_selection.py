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


def test_selection_model_remembers_controls_per_mode(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Track Control Left", "Track Control Right")
    model.remember_current_controls("base")

    model.set_joystick_controls("EF arm", "Winch Speed")
    model.remember_current_controls("ef")

    assert model.get_remembered_controls("base") == ("Track Control Left", "Track Control Right")
    assert model.get_remembered_controls("ef") == ("EF arm", "Winch Speed")


# Indices match JoystickSelectionModel._control_options order.
_TRACK_LEFT = 2
_TRACK_RIGHT = 3
_EF_ARM = 6


def test_select_left_control_commits_allowed_option(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "None")

    assert model.select_left_control(_TRACK_LEFT) is True
    assert model.get_left_selected_option() == "Track Control Left"


def test_select_left_control_blocks_duplicate_of_committed_right(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "EF arm")

    assert model.select_left_control(_EF_ARM) is False
    assert model.get_left_selected_option() == "Winch Speed"


def test_select_control_allows_track_options_independently_on_both_sides(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    assert model.select_left_control(_TRACK_RIGHT) is True
    assert model.select_right_control(_TRACK_LEFT) is True
    assert model.get_current_joystick_controls() == ["Track Control Right", "Track Control Left"]


def test_display_name_mapping_abbreviates_long_modes(qt_app) -> None:
    model = JoystickSelectionModel()

    assert model.display_name_for_option("Track Control Left") == "Track Left"
    assert model.display_name_for_option("Track Control Right") == "Track Right"
    assert model.display_name_for_option("Wheel Travel Left") == "Wheel Left"
    assert model.display_name_for_option("EF Yaw Angle") == "Yaw"
    assert model.display_name_for_option("None") == "None"
    assert model.display_name_for_option("Unknown Mode") == "Unknown Mode"
