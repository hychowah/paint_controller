"""Tests for paint_controller.handlers.exit_hold.ExitHoldHandler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from paint_controller.handlers.exit_hold import ExitHoldHandler
from paint_controller.utils.constants import DEFAULT_EXIT_HOLD_DURATION_S


def test_default_hold_duration_is_one_second(qt_app) -> None:
    handler = ExitHoldHandler()
    assert DEFAULT_EXIT_HOLD_DURATION_S == 1.0
    assert handler._state["duration_target"] == 1.0


def test_missing_switch_key_is_idle_no_op(qt_app) -> None:
    quit_calls: list[bool] = []
    handler = ExitHoldHandler(quit_fn=lambda: quit_calls.append(True))
    overlay_events: list[tuple[bool, float, float]] = []
    handler.overlay_changed.connect(lambda *args: overlay_events.append(args))

    handler.check_exit_button({})
    handler.check_exit_button({"steam": True})

    assert overlay_events == []
    assert quit_calls == []


def test_release_before_threshold_cancels_without_quit(qt_app) -> None:
    quit_calls: list[bool] = []
    handler = ExitHoldHandler(duration_target_s=1.0, quit_fn=lambda: quit_calls.append(True))
    overlay_events: list[tuple[bool, float, float]] = []
    exit_count: list[bool] = []
    handler.overlay_changed.connect(lambda visible, current, target: overlay_events.append((visible, current, target)))
    handler.exit_triggered.connect(lambda: exit_count.append(True))

    with patch("paint_controller.handlers.exit_hold.time.time", side_effect=[0.0, 0.5, 0.6]):
        handler.check_exit_button({"switch": True})
        handler.check_exit_button({"switch": True})
        handler.check_exit_button({"switch": False})

    assert overlay_events == [
        (True, 0.0, 1.0),
        (True, 0.5, 1.0),
        (False, 0.0, 0.0),
    ]
    assert exit_count == []
    assert quit_calls == []


def test_hold_threshold_hides_overlay_and_triggers_quit_once(qt_app) -> None:
    quit_calls: list[bool] = []
    handler = ExitHoldHandler(duration_target_s=1.0, quit_fn=lambda: quit_calls.append(True))
    overlay_events: list[tuple[bool, float, float]] = []
    exit_count: list[bool] = []
    handler.overlay_changed.connect(lambda visible, current, target: overlay_events.append((visible, current, target)))
    handler.exit_triggered.connect(lambda: exit_count.append(True))

    with patch("paint_controller.handlers.exit_hold.time.time", side_effect=[0.0, 1.0, 1.5]):
        handler.check_exit_button({"switch": True})
        handler.check_exit_button({"switch": True})
        # Still held after complete: must not re-trigger.
        handler.check_exit_button({"switch": True})

    assert exit_count == [True]
    assert quit_calls == [True]
    assert overlay_events[0] == (True, 0.0, 1.0)
    assert overlay_events[1] == (True, 1.0, 1.0)
    assert overlay_events[-1] == (False, 0.0, 0.0)
    assert len(overlay_events) == 3


def test_release_after_complete_allows_new_hold_session(qt_app) -> None:
    quit_calls: list[bool] = []
    handler = ExitHoldHandler(duration_target_s=1.0, quit_fn=lambda: quit_calls.append(True))

    with patch(
        "paint_controller.handlers.exit_hold.time.time",
        side_effect=[0.0, 1.0, 1.1, 2.0, 3.0],
    ):
        handler.check_exit_button({"switch": True})
        handler.check_exit_button({"switch": True})  # completes
        handler.check_exit_button({"switch": False})  # release clears latch
        handler.check_exit_button({"switch": True})  # new press
        handler.check_exit_button({"switch": True})  # completes again

    assert quit_calls == [True, True]


def test_request_quit_uses_qapplication_when_no_quit_fn(qt_app) -> None:
    handler = ExitHoldHandler(duration_target_s=1.0, quit_fn=None)
    fake_app = MagicMock()

    with (
        patch("paint_controller.handlers.exit_hold.time.time", side_effect=[0.0, 1.0]),
        patch("paint_controller.handlers.exit_hold.QApplication.instance", return_value=fake_app),
    ):
        handler.check_exit_button({"switch": True})
        handler.check_exit_button({"switch": True})

    fake_app.quit.assert_called_once_with()
