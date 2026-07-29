"""Multi-device demo orchestration (TD-055 Phase 2).

Deep module: one entrypoint hides Teensy pitch/force + winch absolute sequencing.
Does **not** live on device controllers — application/workflow ownership only.
"""

from __future__ import annotations

from paint_controller.ports.teensy import SupportsTeensyWorkflowBody
from paint_controller.ports.winch import SupportsWinchWorkflow


def run_demo_action(
    teensy: SupportsTeensyWorkflowBody,
    winch: SupportsWinchWorkflow | None,
    *,
    pitch_angle: float,
    pitch_speed: float,
    cable_length: float,
    cable_speed: float,
    force_y: float,
) -> None:
    """Run the system-control Demo sequence across Teensy and optional winch."""
    teensy.setSprayGunPitchAngle(float(pitch_angle), float(pitch_speed))
    if winch is not None:
        winch.move_absolute_with_accel(int(cable_length), int(cable_speed), 30)
    teensy.set_ef_force(0.0, float(force_y))
