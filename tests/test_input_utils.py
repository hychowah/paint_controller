"""Tests for paint_controller.utils.input — DoublePressDetector and DeadzoneTracker."""

from unittest.mock import patch

from paint_controller.utils.input import DoublePressDetector, DeadzoneTracker


class TestDoublePressDetector:
    """Tests for DoublePressDetector."""

    def test_first_press_is_not_double(self):
        """First press ever should return False."""
        detector = DoublePressDetector(threshold=1.0)
        assert detector.press() is False

    def test_rapid_second_press_is_double(self):
        """Two presses within threshold are detected as double."""
        detector = DoublePressDetector(threshold=1.0)
        detector.press()
        assert detector.press() is True

    def test_slow_second_press_is_not_double(self):
        """Two presses separated by more than threshold are not double."""
        detector = DoublePressDetector(threshold=0.5)
        times = iter([0.0, 1.0])
        with patch("paint_controller.utils.input.time.time", side_effect=times):
            detector.press()
            assert detector.press() is False

    def test_custom_threshold(self):
        """Custom threshold is respected."""
        detector = DoublePressDetector(threshold=0.2)
        times = iter([0.0, 0.15])
        with patch("paint_controller.utils.input.time.time", side_effect=times):
            detector.press()
            assert detector.press() is True

    def test_threshold_boundary_inclusive(self):
        """Press at exactly threshold time IS a double press."""
        detector = DoublePressDetector(threshold=1.0)
        times = iter([0.0, 1.0])
        with patch("paint_controller.utils.input.time.time", side_effect=times):
            detector.press()
            assert detector.press() is True

    def test_triple_press_detects_second_double(self):
        """Third press is also detected as double if within threshold of second."""
        detector = DoublePressDetector(threshold=1.0)
        times = iter([0.0, 0.5, 1.0])
        with patch("paint_controller.utils.input.time.time", side_effect=times):
            detector.press()       # first → False
            detector.press()       # second → True (double)
            assert detector.press() is True  # third → True (double of second)

    def test_reset_after_gap(self):
        """After a gap exceeding threshold, resets to single-press."""
        detector = DoublePressDetector(threshold=0.5)
        times = iter([0.0, 0.3, 5.0])
        with patch("paint_controller.utils.input.time.time", side_effect=times):
            detector.press()
            detector.press()  # double
            assert detector.press() is False  # too far from last


class TestDeadzoneTracker:
    """Tests for DeadzoneTracker."""

    def test_outside_deadzone_always_sends(self):
        """Values above threshold always return True."""
        tracker = DeadzoneTracker(timeout=2.0)
        assert tracker.update(0.5, threshold=0.05) is True
        assert tracker.update(1.0, threshold=0.05) is True

    def test_entering_deadzone_initially_sends(self):
        """Value entering deadzone initially still allows sending (for stop command)."""
        tracker = DeadzoneTracker(timeout=2.0)
        # First update inside deadzone
        assert tracker.update(0.01, threshold=0.05) is True
        assert tracker.in_deadzone is True

    def test_deadzone_timeout_stops_sending(self):
        """After timeout in deadzone, sending stops."""
        tracker = DeadzoneTracker(timeout=2.0)
        times = iter([0.0, 2.5])
        with patch("paint_controller.utils.input.time.monotonic", side_effect=times):
            tracker.update(0.01, threshold=0.05)  # Enter deadzone at t=0
            result = tracker.update(0.01, threshold=0.05)  # t=2.5, past timeout
            assert result is False
            assert tracker.should_send is False

    def test_leaving_deadzone_resumes_sending(self):
        """Exiting deadzone immediately resumes sending."""
        tracker = DeadzoneTracker(timeout=2.0)
        times = iter([0.0, 3.0])
        with patch("paint_controller.utils.input.time.monotonic", side_effect=times):
            tracker.update(0.01, threshold=0.05)  # Enter deadzone
            tracker.update(0.01, threshold=0.05)  # Still in deadzone, timed out
            assert tracker.should_send is False

        # Leave deadzone — no time mock needed
        result = tracker.update(0.5, threshold=0.05)
        assert result is True
        assert tracker.in_deadzone is False

    def test_deadzone_boundary_exact_threshold(self):
        """Value exactly at threshold is considered inside deadzone."""
        tracker = DeadzoneTracker(timeout=2.0)
        result = tracker.update(0.05, threshold=0.05)
        assert result is True  # First entry sends
        assert tracker.in_deadzone is True

    def test_reset(self):
        """Reset restores initial state."""
        tracker = DeadzoneTracker(timeout=2.0)
        times = iter([0.0, 3.0])
        with patch("paint_controller.utils.input.time.monotonic", side_effect=times):
            tracker.update(0.01, threshold=0.05)  # Enter deadzone
            tracker.update(0.01, threshold=0.05)  # Timed out
            assert tracker.should_send is False

        tracker.reset()
        assert tracker.should_send is True
        assert tracker.in_deadzone is False

    def test_re_enter_deadzone_restarts_timeout(self):
        """Leaving and re-entering deadzone restarts the timeout."""
        tracker = DeadzoneTracker(timeout=2.0)
        times = iter([0.0, 1.5, 1.6, 3.0])
        with patch("paint_controller.utils.input.time.monotonic", side_effect=times):
            tracker.update(0.01, threshold=0.05)  # Enter deadzone at t=0
            tracker.update(0.5, threshold=0.05)   # Leave deadzone at t=1.5
            tracker.update(0.01, threshold=0.05)  # Re-enter at t=1.6
            result = tracker.update(0.01, threshold=0.05)  # t=3.0, 1.4s since re-entry (< 2.0)
            assert result is True  # Still within new timeout window
