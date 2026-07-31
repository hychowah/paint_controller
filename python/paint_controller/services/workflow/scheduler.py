#!/usr/bin/env python3
"""
Action scheduler for workflow execution.

Handles timing calculations and action scheduling with clean separation from execution logic.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .action_schema import get_action_type


class TimingMode(Enum):
    """Timing modes for action scheduling."""

    AFTER_START = "after_start"
    BEFORE_COMPLETE = "before_complete"
    ON_COMPLETE = "on_complete"
    AT_POSITION = "at_position"  # Position-based trigger (runtime evaluated)


@dataclass
class ScheduledAction:
    """Action scheduled for execution with timing information."""

    action_index: int
    action_id: str
    action_config: dict[str, Any]
    scheduled_time: float  # Absolute time in seconds when action should execute (None for position triggers)
    estimated_duration: float  # Estimated duration in seconds
    # Position trigger fields (optional)
    position_trigger_mm: float | None = None  # Target position to trigger at
    position_reference_action: str | None = None  # Reference action ID for position trigger
    is_position_triggered: bool = False  # True if this action uses position-based triggering
    # Winch completion tracking (optional)
    winch_target_mm: float | None = None  # Target position for winch actions
    is_winch_action: bool = False  # True if this is a winch movement action
    # Completion dependency tracking
    must_complete_before_workflow_end: bool = False  # True if workflow must wait for this action to complete


class ActionScheduler:
    """
    Schedules actions with support for sequential and relative timing.

    All timing internally uses seconds for consistency.
    """

    def __init__(self, logger=None, hardware=None):
        """
        Initialize scheduler.

        Args:
            logger: Optional logger for diagnostic messages
            hardware: Optional HardwareControllers instance for reading current state
        """
        self.logger = logger
        self.hardware = hardware

    def build_schedule(self, actions: list[dict[str, Any]]) -> list[ScheduledAction]:
        """
        Build execution schedule from action configurations.

        Args:
            actions: List of action configurations from YAML

        Returns:
            List of ScheduledAction sorted by execution time
        """
        scheduled = []
        action_map = {}  # id -> ScheduledAction
        current_time = 0.0

        for idx, action in enumerate(actions):
            action_id = action.get("id", f"action_{idx}")
            action_name = action.get("name", action_id)

            # Calculate duration
            duration = self._calculate_duration(action)

            # Calculate scheduled time and check for position triggers
            trigger = action.get("trigger")
            position_trigger_mm = None
            position_reference_action = None
            is_position_triggered = False

            if trigger:
                timing_mode_str = trigger.get("timing_mode", "after_start")
                if timing_mode_str == "at_position":
                    # Position-triggered action
                    is_position_triggered = True
                    position_trigger_mm = trigger.get("position_mm")
                    position_reference_action = trigger.get("reference_action")
                    scheduled_time = -1.0  # Sentinel - will be evaluated at runtime

                    if position_trigger_mm is None:
                        raise ValueError(f"Position trigger for '{action_id}' missing 'position_mm'")
                    if not position_reference_action:
                        raise ValueError(f"Position trigger for '{action_id}' missing 'reference_action'")
                else:
                    scheduled_time = self._calculate_trigger_time(trigger, action_map)
            else:
                # Sequential: check for delay_before (legacy support)
                delay_before = action.get("delay_before", 0)
                if delay_before != 0:
                    scheduled_time = self._calculate_legacy_timing(delay_before, idx, scheduled, current_time)
                else:
                    scheduled_time = current_time

            # Ensure non-negative time (except for position triggers which use -1 sentinel)
            if not is_position_triggered:
                scheduled_time = max(0.0, scheduled_time)

            # Check if this is a winch action and extract target position
            action_type = action.get("type")
            action_meta = get_action_type(action_type)
            is_winch_action = action_meta is not None and action_meta.metadata.is_winch_action
            winch_target_mm = None
            if is_winch_action:
                params = action.get("params", {})
                winch_target_mm = params.get("length")

            sched = ScheduledAction(
                action_index=idx,
                action_id=action_id,
                action_config=action,
                scheduled_time=scheduled_time,
                estimated_duration=duration,
                position_trigger_mm=position_trigger_mm,
                position_reference_action=position_reference_action,
                is_position_triggered=is_position_triggered,
                winch_target_mm=winch_target_mm,
                is_winch_action=is_winch_action,
            )

            scheduled.append(sched)
            action_map[action_id] = sched

            # Update current time for next sequential action
            wait_for_completion = action.get("wait_for_completion", True)
            if wait_for_completion:
                current_time = scheduled_time + duration

            if self.logger:
                self.logger.debug(
                    f"Scheduled '{action_name}' (id={action_id}): time={scheduled_time:.2f}s, duration={duration:.2f}s"
                )

        # Sort by scheduled time (important for triggered actions)
        scheduled.sort(key=lambda x: x.scheduled_time)

        # Mark reference actions that must complete before workflow ends
        # (Industry pattern: implicit dependency tracking)
        self._mark_must_complete_actions(scheduled, action_map)

        if self.logger:
            self.logger.info(f"Built schedule with {len(scheduled)} actions")

        return scheduled

    def _calculate_duration(self, action: dict[str, Any]) -> float:
        """
        Calculate estimated duration for an action in seconds.

        Args:
            action: Action configuration

        Returns:
            Duration in seconds
        """
        action_type = action.get("type")

        # Check for explicit duration
        if "estimated_duration" in action:
            return action["estimated_duration"] / 1000.0  # Convert ms to seconds

        if "wait_after" in action:
            return action["wait_after"] / 1000.0  # Convert ms to seconds

        # Auto-calculate for winch movements
        action_meta = get_action_type(action_type)
        if action_meta is not None and action_meta.metadata.is_winch_action:
            params = action.get("params", {})
            target_length = params.get("length", 0)
            distance = params.get("distance", 0)
            speed = params.get("speed", 1)

            # If distance is explicitly provided, use it
            if distance > 0:
                actual_distance = distance
            else:
                # Calculate distance from current position to target
                actual_distance = target_length
                if self.hardware and self.hardware.winch:
                    try:
                        current_length = self.hardware.winch.get_cable_length()
                        actual_distance = abs(target_length - current_length)
                        if self.logger:
                            self.logger.debug(
                                f"Winch duration calculation: target={target_length}mm, "
                                f"current={current_length}mm, distance={actual_distance}mm"
                            )
                    except Exception as e:
                        if self.logger:
                            self.logger.warn(f"Could not get current cable length: {e}, using target as distance")

            if speed > 0:
                return actual_distance / speed  # Returns seconds

        # Default duration
        return 1.0  # 1 second default

    def _calculate_trigger_time(self, trigger: dict[str, Any], action_map: dict[str, ScheduledAction]) -> float:
        """
        Calculate scheduled time based on trigger configuration.

        Args:
            trigger: Trigger configuration with reference_action, timing_mode, offset_ms
            action_map: Map of action_id to ScheduledAction

        Returns:
            Scheduled time in seconds
        """
        ref_id = trigger.get("reference_action")
        if not ref_id or ref_id not in action_map:
            raise ValueError(f"Referenced action '{ref_id}' not found or not yet scheduled")

        ref_action = action_map[ref_id]
        timing_mode = TimingMode(trigger.get("timing_mode", "after_start"))
        offset_seconds = trigger.get("offset_ms", 0) / 1000.0

        if timing_mode == TimingMode.AFTER_START:
            return ref_action.scheduled_time + offset_seconds
        elif timing_mode == TimingMode.BEFORE_COMPLETE:
            completion_time = ref_action.scheduled_time + ref_action.estimated_duration
            return completion_time - offset_seconds
        elif timing_mode == TimingMode.ON_COMPLETE:
            completion_time = ref_action.scheduled_time + ref_action.estimated_duration
            return completion_time + offset_seconds
        elif timing_mode == TimingMode.AT_POSITION:
            # Position triggers are evaluated at runtime, not scheduled
            # Return a sentinel value - executor will handle these specially
            return -1.0  # Sentinel for position-triggered actions
        else:
            raise ValueError(f"Unknown timing mode: {timing_mode}")

    def _calculate_legacy_timing(
        self, delay_before: int, idx: int, scheduled: list[ScheduledAction], current_time: float
    ) -> float:
        """
        Calculate timing using legacy delay_before format.

        Args:
            delay_before: Delay in milliseconds (positive=after, negative=before)
            idx: Current action index
            scheduled: List of already scheduled actions
            current_time: Current sequential time

        Returns:
            Scheduled time in seconds
        """
        delay_seconds = delay_before / 1000.0

        if delay_before > 0:
            # Positive: after previous completes
            return current_time + delay_seconds
        elif delay_before < 0 and idx > 0:
            # Negative: before previous completes
            prev_action = scheduled[-1]
            prev_type = prev_action.action_config.get("type")
            prev_meta = get_action_type(prev_type)

            if prev_meta is not None and prev_meta.metadata.is_winch_action:
                # Use the already calculated duration from prev_action
                # which now includes actual current position
                completion_time = prev_action.scheduled_time + prev_action.estimated_duration
                return completion_time + delay_seconds  # delay_seconds is negative
            else:
                return current_time + delay_seconds
        else:
            return current_time

    def _mark_must_complete_actions(
        self, scheduled: list[ScheduledAction], action_map: dict[str, ScheduledAction]
    ) -> None:
        """
        Mark reference actions that must complete before workflow ends.

        Industry pattern: Actions referenced by position triggers create
        implicit dependencies - they must finish before workflow completes.

        Args:
            scheduled: List of all scheduled actions
            action_map: Map of action_id to ScheduledAction
        """
        for action in scheduled:
            if action.is_position_triggered and action.position_reference_action:
                ref_id = action.position_reference_action

                # Check for optional override in trigger config
                trigger = action.action_config.get("trigger", {})
                wait_for_ref = trigger.get("wait_for_reference_complete", True)

                if wait_for_ref and ref_id in action_map:
                    ref_action = action_map[ref_id]
                    ref_action.must_complete_before_workflow_end = True

                    if self.logger:
                        self.logger.debug(
                            f"Marked '{ref_id}' as must-complete (referenced by position trigger '{action.action_id}')"
                        )
