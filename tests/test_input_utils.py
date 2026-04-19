"""Behavior tests for paint_controller.utils.input."""

from unittest.mock import patch

from paint_controller.utils.input import DoublePressDetector, DeadzoneTracker


def test_first_press_is_not_double() -> None:
    detector = DoublePressDetector(threshold=1.0)
    assert detector.press() is False


def test_rapid_second_press_is_double() -> None:
    detector = DoublePressDetector(threshold=1.0)
    detector.press()
    assert detector.press() is True


def test_slow_second_press_is_not_double() -> None:
    detector = DoublePressDetector(threshold=0.5)
    with patch("paint_controller.utils.input.time.time", side_effect=[0.0, 1.0]):
        detector.press()
        assert detector.press() is False


def test_custom_threshold_is_respected() -> None:
    detector = DoublePressDetector(threshold=0.2)
    with patch("paint_controller.utils.input.time.time", side_effect=[0.0, 0.15]):
        detector.press()
        assert detector.press() is True


def test_threshold_boundary_is_inclusive() -> None:
    detector = DoublePressDetector(threshold=1.0)
    with patch("paint_controller.utils.input.time.time", side_effect=[0.0, 1.0]):
        detector.press()
        assert detector.press() is True


def test_third_press_can_form_a_second_double_press() -> None:
    detector = DoublePressDetector(threshold=1.0)
    with patch("paint_controller.utils.input.time.time", side_effect=[0.0, 0.5, 1.0]):
        detector.press()
        detector.press()
        assert detector.press() is True


def test_gap_beyond_threshold_resets_to_single_press() -> None:
    detector = DoublePressDetector(threshold=0.5)
    with patch("paint_controller.utils.input.time.time", side_effect=[0.0, 0.3, 5.0]):
        detector.press()
        detector.press()
        assert detector.press() is False


def test_values_outside_deadzone_always_send() -> None:
    tracker = DeadzoneTracker(timeout=2.0)
    assert tracker.update(0.5, threshold=0.05) is True
    assert tracker.update(1.0, threshold=0.05) is True


def test_entering_deadzone_still_sends_initial_stop_signal() -> None:
    tracker = DeadzoneTracker(timeout=2.0)
    assert tracker.update(0.01, threshold=0.05) is True
    assert tracker.in_deadzone is True


def test_deadzone_timeout_stops_sending() -> None:
    tracker = DeadzoneTracker(timeout=2.0)
    with patch("paint_controller.utils.input.time.monotonic", side_effect=[0.0, 2.5]):
        tracker.update(0.01, threshold=0.05)
        result = tracker.update(0.01, threshold=0.05)
    assert result is False
    assert tracker.should_send is False


def test_leaving_deadzone_resumes_sending() -> None:
    tracker = DeadzoneTracker(timeout=2.0)
    with patch("paint_controller.utils.input.time.monotonic", side_effect=[0.0, 3.0]):
        tracker.update(0.01, threshold=0.05)
        tracker.update(0.01, threshold=0.05)
    assert tracker.should_send is False

    result = tracker.update(0.5, threshold=0.05)
    assert result is True
    assert tracker.in_deadzone is False


def test_value_exactly_on_threshold_counts_as_deadzone() -> None:
    tracker = DeadzoneTracker(timeout=2.0)
    result = tracker.update(0.05, threshold=0.05)
    assert result is True
    assert tracker.in_deadzone is True


def test_reset_restores_initial_deadzone_state() -> None:
    tracker = DeadzoneTracker(timeout=2.0)
    with patch("paint_controller.utils.input.time.monotonic", side_effect=[0.0, 3.0]):
        tracker.update(0.01, threshold=0.05)
        tracker.update(0.01, threshold=0.05)
    assert tracker.should_send is False

    tracker.reset()
    assert tracker.should_send is True
    assert tracker.in_deadzone is False


def test_re_entering_deadzone_restarts_timeout_window() -> None:
    tracker = DeadzoneTracker(timeout=2.0)
    with patch("paint_controller.utils.input.time.monotonic", side_effect=[0.0, 1.5, 1.6, 3.0]):
        tracker.update(0.01, threshold=0.05)
        tracker.update(0.5, threshold=0.05)
        tracker.update(0.01, threshold=0.05)
        result = tracker.update(0.01, threshold=0.05)

    assert result is True
