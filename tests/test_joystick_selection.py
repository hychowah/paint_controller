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


def test_selection_model_exclusive_duplicate_clears_other_temp_stick(qt_app) -> None:
    """Selecting an exclusive mode already on the other stick clears that stick to None."""
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "None")

    model.initialize_temporary_selection()
    winch_index = model.control_options.index("Winch Speed")
    assert model.set_temporary_index("right", winch_index) is True

    # Temporary preview: right took Winch, left cleared to None.
    assert model.display_left_index(show_overlay=True) == 0
    assert model.display_right_index(show_overlay=True) == winch_index
    # Committed unchanged until commit.
    assert model.get_current_joystick_controls() == ["Winch Speed", "None"]

    model.commit_temporary_selection()
    assert model.get_current_joystick_controls() == ["None", "Winch Speed"]


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


def test_transition_controls_applies_defaults_then_restores_memory(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    model.transition_controls("base", "ef")
    assert model.get_current_joystick_controls() == ["None", "Winch Speed"]
    assert model.get_remembered_controls("base") == ("Track Control Left", "Track Control Right")

    model.set_joystick_controls("EF arm", "EF Yaw Angle")
    model.transition_controls("ef", "base")
    assert model.get_current_joystick_controls() == ["Track Control Left", "Track Control Right"]
    assert model.get_remembered_controls("ef") == ("EF arm", "EF Yaw Angle")

    model.transition_controls("base", "ef")
    assert model.get_current_joystick_controls() == ["EF arm", "EF Yaw Angle"]


def _index_of(model: JoystickSelectionModel, label: str) -> int:
    return model.control_options.index(label)


def test_select_left_control_commits_allowed_option(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "None")

    assert model.select_left_control(_index_of(model, "Track Control Left")) is True
    assert model.get_left_selected_option() == "Track Control Left"


def test_select_left_control_takes_exclusive_mode_and_clears_right(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "EF arm")

    assert model.select_left_control(_index_of(model, "EF arm")) is True
    assert model.get_current_joystick_controls() == ["EF arm", "None"]


def test_select_right_control_takes_exclusive_mode_and_clears_left(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "None")

    assert model.select_right_control(_index_of(model, "Winch Speed")) is True
    assert model.get_current_joystick_controls() == ["None", "Winch Speed"]


def test_select_control_allows_track_options_independently_on_both_sides(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Track Control Left", "Track Control Right")

    assert model.select_left_control(_index_of(model, "Track Control Right")) is True
    assert model.select_right_control(_index_of(model, "Track Control Left")) is True
    assert model.get_current_joystick_controls() == ["Track Control Right", "Track Control Left"]


def test_avoid_autorun_clears_named_modes_not_indices(qt_app) -> None:
    model = JoystickSelectionModel()
    model.set_joystick_controls("Winch Speed", "EF prop pwm")

    model.avoidAutoRunOverwrite()

    assert model.get_current_joystick_controls() == ["None", "None"]


def test_display_name_mapping_abbreviates_long_modes(qt_app) -> None:
    model = JoystickSelectionModel()

    assert model.display_name_for_option("Track Control Left") == "Track Left"
    assert model.display_name_for_option("Track Control Right") == "Track Right"
    assert model.display_name_for_option("Wheel Travel Left") == "Wheel Left"
    assert model.display_name_for_option("EF Yaw Angle") == "Yaw"
    assert model.display_name_for_option("None") == "None"
    assert model.display_name_for_option("Unknown Mode") == "Unknown Mode"
