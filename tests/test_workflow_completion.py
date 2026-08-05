"""Wait-done completion policy tests (timed + hybrid feedback via reader keys)."""

from __future__ import annotations

from paint_controller.services.workflow.action_schema import CompletionKind, get_action_type
from paint_controller.services.workflow.completion import CompletionTracker
from paint_controller.services.workflow.scheduler import ScheduledAction


class _FakeWinch:
    def __init__(self) -> None:
        self.length = 0.0

    def get_cable_length(self) -> float:
        return self.length


class _FakeHardware:
    def __init__(self) -> None:
        self.winch = _FakeWinch()


def _scheduled(
    *,
    action_type: str,
    params: dict,
    estimated_duration: float = 1.0,
    scheduled_time: float = 0.0,
    action_id: str = "a1",
) -> ScheduledAction:
    meta = get_action_type(action_type)
    assert meta is not None
    cspec = meta.metadata.completion
    target = None
    reader = None
    tolerance = 50.0
    if cspec.feedback is not None:
        reader = cspec.feedback.reader_key
        tolerance = cspec.feedback.tolerance
        raw = params.get(cspec.feedback.target_param)
        target = float(raw) if raw is not None else None
    return ScheduledAction(
        action_index=0,
        action_id=action_id,
        action_config={"id": action_id, "type": action_type, "params": params},
        scheduled_time=scheduled_time,
        estimated_duration=estimated_duration,
        completion_kind=cspec.kind,
        completion_target=target,
        completion_reader=reader,
        completion_tolerance=tolerance,
        winch_target_mm=target if meta.metadata.is_winch_action else None,
        is_winch_action=meta.metadata.is_winch_action,
    )


def test_timed_completion_uses_wait_until() -> None:
    hardware = _FakeHardware()
    tracker = CompletionTracker(hardware)
    scheduled = _scheduled(action_type="valve_turn", params={"turn_value": 1.0}, estimated_duration=0.5)
    wait_until = 0.5
    tracker.begin_from_scheduled(scheduled, wait_until=wait_until)
    assert tracker.is_complete(0.0) is False
    assert tracker.is_complete(0.49) is False
    assert tracker.is_complete(0.5) is True


def test_winch_hybrid_completes_on_feedback_within_tolerance() -> None:
    hardware = _FakeHardware()
    hardware.winch.length = 0.0
    tracker = CompletionTracker(hardware, default_winch_tolerance=50.0)
    scheduled = _scheduled(
        action_type="winch_absolute",
        params={"length": 1000, "speed": 100, "acceleration": 10},
        estimated_duration=10.0,
    )
    assert scheduled.completion_kind == CompletionKind.HYBRID
    assert scheduled.completion_reader == "winch_cable_length"
    tracker.begin_from_scheduled(scheduled, wait_until=10.0)

    assert tracker.is_complete(0.0) is False
    hardware.winch.length = 960.0  # within 50mm of 1000
    assert tracker.is_complete(1.0) is True


def test_winch_hybrid_timeout_if_feedback_never_arrives() -> None:
    hardware = _FakeHardware()
    hardware.winch.length = 0.0
    tracker = CompletionTracker(hardware)
    scheduled = _scheduled(
        action_type="winch_absolute",
        params={"length": 1000, "speed": 100},
        estimated_duration=2.0,
    )
    # wait_until = 2.0; hybrid timeout extends by (scale-1)*estimate
    tracker.begin_from_scheduled(scheduled, wait_until=2.0)
    assert tracker.is_complete(0.0) is False
    assert tracker.is_complete(1.9) is False
    # timeout_elapsed = 2 + 2*(2-1) = 4 with scale 2.0
    assert tracker.is_complete(4.0) is True


def test_new_feedback_type_needs_reader_registration_not_executor_branch() -> None:
    """Structure proof: custom reader key works without executor is_winch_* logic."""
    hardware = _FakeHardware()
    tracker = CompletionTracker(hardware)
    values = {"pos": 0.0}
    tracker.register_reader("custom_sensor", lambda: values["pos"])

    scheduled = ScheduledAction(
        action_index=0,
        action_id="x",
        action_config={"type": "valve_turn", "params": {"turn_value": 0.0}},
        scheduled_time=0.0,
        estimated_duration=5.0,
        completion_kind=CompletionKind.HYBRID,
        completion_target=10.0,
        completion_reader="custom_sensor",
        completion_tolerance=0.5,
    )
    # Override begin by manually setting active with custom reader
    from paint_controller.services.workflow.completion import ActiveCompletion

    tracker._active = ActiveCompletion(
        action_id="x",
        kind=CompletionKind.HYBRID,
        wait_until=5.0,
        target=10.0,
        tolerance=0.5,
        reader_key="custom_sensor",
        timeout_elapsed=10.0,
    )
    assert tracker.is_complete(0.0) is False
    values["pos"] = 10.0
    assert tracker.is_complete(0.1) is True


def test_winch_absolute_metadata_is_hybrid_not_executor_named_flag() -> None:
    action = get_action_type("winch_absolute")
    assert action is not None
    assert action.metadata.completion.kind == CompletionKind.HYBRID
    assert action.metadata.completion.feedback is not None
    assert action.metadata.completion.feedback.reader_key == "winch_cable_length"
