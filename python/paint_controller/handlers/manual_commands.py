"""Python-owned manual command boundary for the system-control overlay."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.handlers.demo_sequence import run_demo_action
from paint_controller.ports.teensy import SupportsTeensyWorkflowBody
from paint_controller.ports.winch import SupportsWinchMotion


class SupportsManualTeensyCommands(SupportsTeensyWorkflowBody, Protocol):
    """Teensy surface used by system-control manual commands (incl. tap helpers)."""

    def startTapFreq(self, power: float, period: float) -> None: ...

    def tapOnce(self, power: float) -> None: ...


@dataclass(frozen=True)
class _ParameterSpec:
    name: str
    coerce: Callable[[str], object]


@dataclass(frozen=True)
class _CommandSpec:
    parameters: tuple[_ParameterSpec, ...]
    executor: Callable[[dict[str, object]], bool | None]


class ManualCommandHandler(QObject):
    """Own manual command validation, coercion, and dispatch for QML."""

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: SupportsManualTeensyCommands,
        winch: SupportsWinchMotion | None,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._winch = winch
        self._logger = logger
        self._command_specs: dict[str, _CommandSpec] = {
            "Set Spray Gun Angle": _CommandSpec(
                parameters=(
                    _ParameterSpec("Angle", self._to_float),
                    _ParameterSpec("Speed", self._to_float),
                ),
                executor=self._execute_set_spray_gun_angle,
            ),
            "Demo": _CommandSpec(
                parameters=(
                    _ParameterSpec("Gimbal Angle", self._to_float),
                    _ParameterSpec("Gimbal Speed", self._to_float),
                    _ParameterSpec("Cable Length", self._to_float),
                    _ParameterSpec("Cable Speed", self._to_float),
                    _ParameterSpec("Force Y", self._to_float),
                ),
                executor=self._execute_demo,
            ),
            "Winch Control": _CommandSpec(
                parameters=(
                    _ParameterSpec("Distance", self._to_int),
                    _ParameterSpec("Speed", self._to_int),
                    _ParameterSpec("Acceleration", self._to_int),
                ),
                executor=self._execute_winch_control,
            ),
            "Frequency Tap": _CommandSpec(
                parameters=(
                    _ParameterSpec("Power", self._to_float),
                    _ParameterSpec("Period", self._to_float),
                ),
                executor=self._execute_frequency_tap,
            ),
            "Tap Once": _CommandSpec(
                parameters=(_ParameterSpec("Power", self._to_float),),
                executor=self._execute_tap_once,
            ),
            "Extend Arm": _CommandSpec(
                parameters=(_ParameterSpec("Length", self._to_int),),
                executor=self._execute_extend_arm,
            ),
        }

    @Slot(str, result=bool)
    def isCommandSupported(self, command_name: str) -> bool:
        return command_name in self._command_specs

    @Slot(str, "QVariantMap", result=bool)
    def executeCommand(self, command_name: str, raw_parameters: Any) -> bool:
        if not self.isCommandSupported(command_name):
            return self._fail(f"Command '{command_name}' is not available yet")

        try:
            parameters = self._coerce_parameters(command_name, raw_parameters)
        except ValueError as exc:
            return self._fail(str(exc))

        result = self._command_specs[command_name].executor(parameters)
        if result is False:
            return self._fail(f"Command '{command_name}' was rejected by the backend")

        message = f"Command sent: {command_name}"
        self._logger.info(message)
        self.operation_result.emit(True, message)
        return True

    def _coerce_parameters(self, command_name: str, raw_parameters: Any) -> dict[str, object]:
        command_spec = self._command_specs[command_name]
        if raw_parameters is None:
            parameter_map: dict[str, Any] = {}
        elif isinstance(raw_parameters, dict):
            parameter_map = raw_parameters
        else:
            try:
                parameter_map = dict(raw_parameters)
            except Exception as exc:
                raise ValueError(f"Invalid parameter payload for '{command_name}'") from exc

        coerced: dict[str, object] = {}
        for spec in command_spec.parameters:
            raw_value = parameter_map.get(spec.name)
            if raw_value is None or str(raw_value).strip() == "":
                raise ValueError(f"Missing parameter: {spec.name}")

            try:
                coerced[spec.name] = spec.coerce(str(raw_value))
            except ValueError as exc:
                raise ValueError(f"Invalid value for {spec.name}: {raw_value}") from exc

        return coerced

    @staticmethod
    def _to_float(value: str) -> float:
        return float(value)

    @staticmethod
    def _to_int(value: str) -> int:
        return int(float(value))

    @staticmethod
    def _as_float(value: object) -> float:
        return float(str(value))

    @staticmethod
    def _as_int(value: object) -> int:
        return int(float(str(value)))

    def _execute_set_spray_gun_angle(self, parameters: dict[str, object]) -> None:
        self._teensy.setSprayGunPitchAngle(self._as_float(parameters["Angle"]), self._as_float(parameters["Speed"]))

    def _execute_demo(self, parameters: dict[str, object]) -> None:
        # TD-055: multi-device demo lives in application demo_sequence, not on Teensy.
        run_demo_action(
            self._teensy,
            self._winch,
            pitch_angle=self._as_float(parameters["Gimbal Angle"]),
            pitch_speed=self._as_float(parameters["Gimbal Speed"]),
            cable_length=self._as_float(parameters["Cable Length"]),
            cable_speed=self._as_float(parameters["Cable Speed"]),
            force_y=self._as_float(parameters["Force Y"]),
        )

    def _execute_winch_control(self, parameters: dict[str, object]) -> bool | None:
        if self._winch is None:
            return False
        distance = self._as_int(parameters["Distance"])
        speed = self._as_int(parameters["Speed"])
        acceleration = self._as_int(parameters["Acceleration"])
        # Prefer the shared workflow port name; fall back to legacy QML-facing alias.
        move = getattr(self._winch, "move_increment_with_accel", None)
        if callable(move):
            result = move(distance, speed, acceleration)
            return result if isinstance(result, bool) or result is None else bool(result)
        legacy = getattr(self._winch, "moveIncrementWithAccel", None)
        if not callable(legacy):
            return False
        result = legacy(distance, speed, acceleration)
        return result if isinstance(result, bool) or result is None else bool(result)

    def _execute_frequency_tap(self, parameters: dict[str, object]) -> None:
        self._teensy.startTapFreq(self._as_float(parameters["Power"]), self._as_float(parameters["Period"]))

    def _execute_tap_once(self, parameters: dict[str, object]) -> None:
        self._teensy.tapOnce(self._as_float(parameters["Power"]))

    def _execute_extend_arm(self, parameters: dict[str, object]) -> None:
        self._teensy.extendArm(self._as_int(parameters["Length"]))

    def _fail(self, message: str) -> bool:
        self._logger.warning(message)
        self.operation_result.emit(False, message)
        return False
