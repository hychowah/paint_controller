# pyright: reportRedeclaration=false
"""Continuous teleop Qt façade — motion core lives in ContinuousTeleopEngine (TD-055.8).

- Entry: ``ControlProcessor.process_input`` (status timer in ``SignalWiring``, ~60 Hz).
- Does **not** call ``AdminActionGate``. Continuous motion owned by ``ContinuousTeleopEngine``.
- This class owns QML properties, display formatting, and settings signal wiring only.

TD-054: when ``safety_coordinator.continuous_motion_allowed`` is False (after halt),
``process_input`` skips the engine tick so sticks cannot re-drive until clear-error.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.handlers.continuous_teleop_engine import ContinuousTeleopEngine
from paint_controller.handlers.policy.teleop_control_map import ControlConfig
from paint_controller.handlers import winch_teleop
from paint_controller.ports.teensy import SupportsTeensyTeleop
from paint_controller.ports.valve import SupportsValveCommand
from paint_controller.ports.wheel import SupportsWheelTeleop
from paint_controller.ports.winch import SupportsWinchTeleop
from paint_controller.utils.input import input_axes_active
from paint_controller.utils.perf_counters import PERF

if TYPE_CHECKING:
    from paint_controller.core.settings import SettingsManager
    from paint_controller.core.state_store import StateStore
    from paint_controller.handlers.heartbeat import UIHeartbeatHandler
    from paint_controller.handlers.safety_coordinator import SafetyCoordinator
    from paint_controller.models.joystick_selection import JoystickSelectionModel

logger = logging.getLogger(__name__)

DisplayValue = str | float | tuple[float, float]

__all__ = ["ControlConfig", "ControlProcessor", "ContinuousTeleopEngine"]


class ControlProcessor(QObject):
    left_control_mode_changed = Signal(str)
    left_control_value_changed = Signal(str)
    right_control_mode_changed = Signal(str)
    right_control_value_changed = Signal(str)
    left_control_mode_display_changed = Signal(str)
    right_control_mode_display_changed = Signal(str)

    def __init__(
        self,
        wheel: SupportsWheelTeleop,
        winch: SupportsWinchTeleop,
        teensy: SupportsTeensyTeleop,
        esp32_valve: SupportsValveCommand,
        selection_model: JoystickSelectionModel,
        heartbeat_handler: UIHeartbeatHandler,
        settings_manager: SettingsManager | None,
        state_store: StateStore,
        safety_coordinator: SafetyCoordinator | None = None,
    ) -> None:
        super().__init__()
        self._selection_model = selection_model
        self._heartbeat_handler = heartbeat_handler
        self._settings_manager = settings_manager
        self._state_store = state_store
        self._safety_coordinator = safety_coordinator
        self._teensy = teensy

        self.MESSAGE_UPDATE_INTERVAL = 0.2
        self.last_message_time = 0.0
        self._left_control_mode = "None"
        self._left_control_value = ""
        self._right_control_mode = "None"
        self._right_control_value = ""
        self._left_control_mode_display = "None"
        self._right_control_mode_display = "None"

        track_max, track_min, valve_max, winch_max, wt_max, wt_rate, wt_rpm = self._load_limit_defaults(
            settings_manager
        )
        self._engine = ContinuousTeleopEngine(
            wheel,
            winch,
            teensy,
            esp32_valve,
            is_winch_locked=self._is_winch_control_locked,
            track_max_speed=track_max,
            track_min_speed=track_min,
            valve_turn_max=valve_max,
            winch_max_speed_mmps=winch_max,
            wheel_travel_max=wt_max,
            wheel_travel_rate=wt_rate,
            wheel_travel_rpm=wt_rpm,
        )
        # Seed selection pair so first tick does not false-positive reseed yaw.
        self._engine._last_selection_pair = (
            selection_model.get_left_selected_option(),
            selection_model.get_right_selected_option(),
        )
        self._wire_settings(settings_manager)

    # --- compatibility surface used by tests / helpers ---
    @property
    def controls(self):
        return self._engine.controls

    @property
    def current_values(self):
        return self._engine.current_values

    @property
    def TRACK_MAX_SPEED(self) -> float:
        return self._engine.TRACK_MAX_SPEED

    @property
    def TRACK_MIN_SPEED(self) -> float:
        return self._engine.TRACK_MIN_SPEED

    @property
    def TRACK_DEAD_ZONE(self) -> float:
        return self._engine.TRACK_DEAD_ZONE

    @property
    def _left_wheel_travel_mm(self) -> float:
        return self._engine._left_wheel_travel_mm

    @_left_wheel_travel_mm.setter
    def _left_wheel_travel_mm(self, value: float) -> None:
        self._engine._left_wheel_travel_mm = float(value)

    @property
    def _right_wheel_travel_mm(self) -> float:
        return self._engine._right_wheel_travel_mm

    @_right_wheel_travel_mm.setter
    def _right_wheel_travel_mm(self, value: float) -> None:
        self._engine._right_wheel_travel_mm = float(value)

    @property
    def _wheel_travel_rpm(self) -> int:
        return int(self._engine._wheel_travel_rpm)

    @property
    def _wheel_travel_max(self) -> float:
        return float(self._engine._wheel_travel_max)

    @property
    def _winch_max_speed_mmps(self) -> float:
        return float(self._engine._winch_max_speed_mmps)

    @property
    def _valve_turn_max(self) -> float:
        return float(self._engine._valve_turn_max)

    @property
    def _wheel(self):
        return self._engine._wheel

    @_wheel.setter
    def _wheel(self, value) -> None:
        self._engine._wheel = value

    @property
    def winch_speed_has_been_active(self) -> bool:
        return self._engine.winch_speed_has_been_active

    @winch_speed_has_been_active.setter
    def winch_speed_has_been_active(self, value: bool) -> None:
        self._engine.winch_speed_has_been_active = value

    def _apply_nonlinear_curve(self, normalized_input: float) -> float:
        return self._engine._apply_nonlinear_curve(normalized_input)

    @property
    def _last_selection_pair(self) -> tuple[str, str]:
        return self._engine._last_selection_pair

    @_last_selection_pair.setter
    def _last_selection_pair(self, value: tuple[str, str]) -> None:
        self._engine._last_selection_pair = value

    def _load_limit_defaults(self, settings_manager: SettingsManager | None):
        if settings_manager is not None:
            sm = settings_manager
            return (
                sm.get("track_max_speed") or 500.0,
                sm.get("track_min_speed") or 50.0,
                sm.get("valve_turn_max") or 20.0,
                sm.get("winch_max_speed_mmps") or 400.0,
                sm.get("wheel_travel_max") or 500.0,
                sm.get("wheel_travel_rate") or 100.0,
                sm.get("wheel_travel_rpm") or 200,
            )
        return 500.0, 50.0, 6.0, 400.0, 500.0, 100.0, 300

    def _wire_settings(self, settings_manager: SettingsManager | None) -> None:
        if settings_manager is None:
            return
        sm = settings_manager
        sm.track_max_speed_changed.connect(self._on_track_max_speed_changed)
        sm.track_min_speed_changed.connect(self._on_track_min_speed_changed)
        sm.valve_turn_max_changed.connect(self._on_valve_turn_max_changed)
        sm.winch_max_speed_mmps_changed.connect(self._on_winch_max_speed_mmps_changed)
        sm.wheel_travel_max_changed.connect(self._on_wheel_travel_max_changed)
        sm.wheel_travel_rate_changed.connect(self._on_wheel_travel_rate_changed)
        sm.wheel_travel_rpm_changed.connect(self._on_wheel_travel_rpm_changed)

    def _is_winch_control_locked(self) -> bool:
        return winch_teleop.is_winch_control_locked(
            get_base_status=self._heartbeat_handler.get_base_status,
            get_ef_status=self._heartbeat_handler.get_ef_status,
        )

    def _can_send_message(self) -> bool:
        current_time = time.monotonic()
        if current_time - self.last_message_time >= self.MESSAGE_UPDATE_INTERVAL:
            self.last_message_time = current_time
            return True
        return False

    def process_input(self, input_state: dict[str, Any]) -> None:
        try:
            # TD-054: latched after halt_all_effectors until clear_error_state.
            safety = self._safety_coordinator
            if safety is not None and not safety.continuous_motion_allowed:
                return

            left_mode = self._selection_model.get_left_selected_option()
            right_mode = self._selection_model.get_right_selected_option()
            self.left_control_mode_display = self._selection_model.display_name_for_option(left_mode)
            self.right_control_mode_display = self._selection_model.display_name_for_option(right_mode)

            # P-03: skip engine tick when both modes idle and sticks centered.
            # E-stop / exit-hold still run every status tick in SignalWiring.
            # When a mode is selected, always tick so zero/deadzone paths fire.
            modes_active = left_mode not in ("", "None", None) or right_mode not in ("", "None", None)
            axes_active = input_axes_active(input_state)
            if modes_active or axes_active:
                PERF.incr("teleop_tick")
                self._engine.tick(input_state, left_mode, right_mode)
            else:
                PERF.incr("teleop_idle_skip")
            self._update_display()
        except Exception as e:
            logger.error("Error processing input: %s", e)

    def _format_simple_value(self, mode: str, value: object) -> str:
        """Data-driven scalar formatting from ControlConfig; special cases stay explicit."""
        config = self._engine.controls.get(mode) if hasattr(self, "_engine") else None
        unit = config.display_unit if config is not None else ""
        decimals = config.display_decimals if config is not None else 2
        if decimals is None:
            return f"{value}{unit}"
        if isinstance(value, (int, float)):
            return f"{float(value):.{decimals}f}{unit}"
        try:
            return f"{float(str(value)):.{decimals}f}{unit}"
        except (TypeError, ValueError):
            return f"{value}{unit}"

    def _update_display(self) -> None:
        if not self._can_send_message():
            return
        left_mode = self._selection_model.get_left_selected_option()
        right_mode = self._selection_model.get_right_selected_option()
        cv = self._engine.current_values

        def format_side(mode_sel: str, side: str) -> tuple[str, str, str]:
            if mode_sel == "None":
                return "None", "None", ""
            mode = str(cv[f"{side}_mode"])
            value = cv[f"{side}_value"]
            # Special cases kept explicit (winch lock, track raw, EF Force tuples).
            if mode == "Winch Speed" and self._is_winch_control_locked():
                part = f"{mode} {self._format_simple_value(mode, value)} (LOCKED)" if mode else "None"
                val_str = self._format_simple_value(mode, value)
            elif mode in ["Track Control Left", "Track Control Right"]:
                part = f"{mode} {value}" if mode else "None"
                val_str = str(value)
            elif mode == "EF Force":
                if isinstance(value, tuple):
                    val_str = f"Fx:{value[0]:.2f} Fy:{value[1]:.2f}"
                    part = f"{mode} {val_str}"
                else:
                    val_str = self._format_simple_value(mode, value)
                    part = f"{mode} {val_str}"
            else:
                val_str = self._format_simple_value(mode, value) if mode else ""
                part = f"{mode} {val_str}" if mode else "None"
            return part, mode, val_str

        left_part, left_mode_s, left_val = format_side(left_mode, "left")
        right_part, right_mode_s, right_val = format_side(right_mode, "right")

        self.left_control_mode = left_mode_s if left_mode != "None" else "None"
        self.left_control_value = left_val if left_mode != "None" else ""
        self.right_control_mode = right_mode_s if right_mode != "None" else "None"
        self.right_control_value = right_val if right_mode != "None" else ""
        self._state_store.display_message = f"{left_part} | {right_part}"

    def send_wheel_travel_command(self) -> bool:
        return self._engine.send_wheel_travel_command()

    def reset_winch_activation(self) -> None:
        self._engine.reset_winch_activation()

    def set_winch_speed_limit(self, max_speed_mmps: float) -> None:
        self._engine.set_winch_speed_limit(max_speed_mmps)

    # Settings callbacks
    def _on_track_max_speed_changed(self, new_value: float) -> None:
        self._engine.set_track_max_speed(new_value)
        logger.info("Track max speed updated to: %s", new_value)

    def _on_track_min_speed_changed(self, new_value: float) -> None:
        self._engine.set_track_min_speed(new_value)
        logger.info("Track min speed updated to: %s", new_value)

    def _on_valve_turn_max_changed(self, new_value: float) -> None:
        self._engine.set_valve_turn_max(new_value)
        logger.info("Valve turn max updated to: %s", new_value)

    def _on_winch_max_speed_mmps_changed(self, new_value: float) -> None:
        self._engine.set_winch_speed_limit(new_value)
        logger.info("Winch max speed updated to: %s mm/s", new_value)

    def _on_wheel_travel_max_changed(self, new_value: float) -> None:
        self._engine.set_wheel_travel_max(new_value)

    def _on_wheel_travel_rate_changed(self, new_value: float) -> None:
        self._engine.set_wheel_travel_rate(new_value)

    def _on_wheel_travel_rpm_changed(self, new_value: int) -> None:
        self._engine.set_wheel_travel_rpm(int(new_value))

    # Private method aliases for existing unit tests that call process helpers
    def _process_winch_speed(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        self._engine._process_winch_speed(input_state, mode, stick)

    def _process_standard_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        self._engine._process_standard_control(input_state, mode, stick)

    def _process_track_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        self._engine._process_track_control(input_state, mode, stick)

    def _process_joint_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        self._engine._process_joint_control(input_state, mode, stick)

    def _process_ef_force_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        self._engine._process_ef_force_control(input_state, mode, stick)

    def _process_yaw_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        self._engine._process_yaw_control(input_state, mode, stick)

    def _process_valve_turn(self, input_state: dict[str, Any]) -> None:
        self._engine._process_valve_turn(input_state)

    def _process_arm_rail_speed(self, input_state: dict[str, Any]) -> None:
        self._engine._process_arm_rail_speed(input_state)

    def _process_wheel_travel(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        self._engine._process_wheel_travel(input_state, mode, stick)

    def _can_send_command(self, mode: str) -> bool:
        return self._engine._can_send_command(mode)

    # Qt properties
    def _get_left_control_mode(self) -> str:
        return self._left_control_mode

    def _set_left_control_mode(self, value: str) -> None:
        if self._left_control_mode != value:
            self._left_control_mode = value
            self.left_control_mode_changed.emit(value)

    left_control_mode = Property(str, _get_left_control_mode, _set_left_control_mode, notify=left_control_mode_changed)

    def _get_left_control_value(self) -> str:
        return self._left_control_value

    def _set_left_control_value(self, value: str) -> None:
        if self._left_control_value != value:
            self._left_control_value = value
            self.left_control_value_changed.emit(value)

    left_control_value = Property(str, _get_left_control_value, _set_left_control_value, notify=left_control_value_changed)

    def _get_right_control_mode(self) -> str:
        return self._right_control_mode

    def _set_right_control_mode(self, value: str) -> None:
        if self._right_control_mode != value:
            self._right_control_mode = value
            self.right_control_mode_changed.emit(value)

    right_control_mode = Property(str, _get_right_control_mode, _set_right_control_mode, notify=right_control_mode_changed)

    def _get_right_control_value(self) -> str:
        return self._right_control_value

    def _set_right_control_value(self, value: str) -> None:
        if self._right_control_value != value:
            self._right_control_value = value
            self.right_control_value_changed.emit(value)

    right_control_value = Property(str, _get_right_control_value, _set_right_control_value, notify=right_control_value_changed)

    def _get_left_control_mode_display(self) -> str:
        return self._left_control_mode_display

    def _set_left_control_mode_display(self, value: str) -> None:
        if self._left_control_mode_display != value:
            self._left_control_mode_display = value
            self.left_control_mode_display_changed.emit(value)

    left_control_mode_display = Property(
        str, _get_left_control_mode_display, _set_left_control_mode_display, notify=left_control_mode_display_changed
    )

    def _get_right_control_mode_display(self) -> str:
        return self._right_control_mode_display

    def _set_right_control_mode_display(self, value: str) -> None:
        if self._right_control_mode_display != value:
            self._right_control_mode_display = value
            self.right_control_mode_display_changed.emit(value)

    right_control_mode_display = Property(
        str, _get_right_control_mode_display, _set_right_control_mode_display, notify=right_control_mode_display_changed
    )
