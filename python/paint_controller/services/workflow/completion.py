"""Wait-done completion policies for workflow execution.

The executor waits through this module instead of hard-coding device-named
branches. New feedback types register a reader key + CompletionSpec on the
action registry; they do not require new ``if is_*`` paths in the executor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .action_schema import CompletionKind, FeedbackSource, get_action_type


ReaderFn = Callable[[], float]


@dataclass
class ActiveCompletion:
    """In-flight completion tracking for the action currently being waited on."""

    action_id: str
    kind: str
    wait_until: float  # schedule end time (elapsed seconds) for timed/hybrid timeout
    target: float | None = None
    tolerance: float = 50.0
    reader_key: str | None = None
    timeout_elapsed: float | None = None  # hybrid absolute timeout


class CompletionTracker:
    """Owns active Wait-done completion state for one executor."""

    def __init__(
        self,
        hardware: Any | None = None,
        *,
        readers: dict[str, ReaderFn] | None = None,
        default_winch_tolerance: float = 50.0,
        logger: Any | None = None,
    ) -> None:
        self._hardware = hardware
        self._logger = logger
        self._default_winch_tolerance = default_winch_tolerance
        self._readers: dict[str, ReaderFn] = dict(readers or {})
        self._active: ActiveCompletion | None = None
        self._register_default_readers()

    def _register_default_readers(self) -> None:
        if "winch_cable_length" not in self._readers:
            self._readers["winch_cable_length"] = self._read_winch_cable_length

    def register_reader(self, key: str, reader: ReaderFn) -> None:
        """Register or replace a feedback reader (extension point for new sensors)."""
        self._readers[key] = reader

    def clear(self) -> None:
        self._active = None

    @property
    def active(self) -> ActiveCompletion | None:
        return self._active

    def begin_from_scheduled(self, scheduled: Any, *, wait_until: float) -> None:
        """Start tracking completion for a scheduled action about to be waited on."""
        action_config = getattr(scheduled, "action_config", {}) or {}
        action_type = action_config.get("type")
        action_id = getattr(scheduled, "action_id", "") or action_config.get("id", "")
        params = dict(action_config.get("params") or {})

        meta = get_action_type(action_type)
        if meta is None:
            self._active = ActiveCompletion(
                action_id=str(action_id),
                kind=CompletionKind.TIMED,
                wait_until=wait_until,
            )
            return

        completion = meta.metadata.completion
        kind = completion.kind
        target: float | None = None
        tolerance = self._default_winch_tolerance
        reader_key: str | None = None
        timeout_elapsed: float | None = None

        feedback: FeedbackSource | None = completion.feedback
        if feedback is not None and kind in (CompletionKind.FEEDBACK, CompletionKind.HYBRID):
            reader_key = feedback.reader_key
            tolerance = float(feedback.tolerance)
            raw_target = params.get(feedback.target_param)
            try:
                target = float(raw_target) if raw_target is not None else None
            except (TypeError, ValueError):
                target = None
            # Prefer scheduler-bound target when present (generic field)
            bound = getattr(scheduled, "completion_target", None)
            if bound is not None:
                try:
                    target = float(bound)
                except (TypeError, ValueError):
                    pass
            if kind == CompletionKind.HYBRID:
                estimate = float(getattr(scheduled, "estimated_duration", 0.0) or 0.0)
                # Timeout measured from action start ≈ wait_until for sequential timed start,
                # but hybrid uses scale * estimate from scheduled end of timed portion.
                # Use wait_until as the soft schedule end; hard timeout = start + scale*estimate.
                # wait_until is already scheduled_time + estimate; scale extends it.
                timeout_elapsed = wait_until + max(estimate * (feedback.timeout_scale - 1.0), 0.0)

        if kind == CompletionKind.IMMEDIATE:
            self._active = ActiveCompletion(
                action_id=str(action_id),
                kind=kind,
                wait_until=wait_until,
            )
            return

        self._active = ActiveCompletion(
            action_id=str(action_id),
            kind=kind,
            wait_until=wait_until,
            target=target,
            tolerance=tolerance,
            reader_key=reader_key,
            timeout_elapsed=timeout_elapsed if kind == CompletionKind.HYBRID else (
                wait_until if kind == CompletionKind.TIMED else None
            ),
        )

    def is_complete(self, elapsed: float) -> bool:
        """Return True when Wait-done for the active action is satisfied."""
        active = self._active
        if active is None:
            return True

        if active.kind == CompletionKind.IMMEDIATE:
            return True

        if active.kind == CompletionKind.TIMED:
            return elapsed >= active.wait_until

        if active.kind in (CompletionKind.FEEDBACK, CompletionKind.HYBRID):
            feedback_done = self._feedback_reached(active)
            if feedback_done:
                return True
            if active.kind == CompletionKind.HYBRID:
                deadline = active.timeout_elapsed if active.timeout_elapsed is not None else active.wait_until
                return elapsed >= deadline
            # pure feedback: also fall back to wait_until to avoid infinite hang
            return elapsed >= active.wait_until

        return elapsed >= active.wait_until

    def _feedback_reached(self, active: ActiveCompletion) -> bool:
        if active.target is None or not active.reader_key:
            return False
        reader = self._readers.get(active.reader_key)
        if reader is None:
            return False
        try:
            current = float(reader())
        except Exception as exc:
            if self._logger is not None:
                self._logger.warn(f"Completion reader {active.reader_key!r} failed: {exc}")
            return False
        return abs(current - active.target) <= active.tolerance

    def _read_winch_cable_length(self) -> float:
        if self._hardware is None or getattr(self._hardware, "winch", None) is None:
            raise RuntimeError("Winch controller not available")
        return float(self._hardware.winch.get_cable_length())
