"""Central registry for workflow action types.

Single source of truth for:
- action type name
- parameter specification (validation)
- human-readable description template
- handler factory
- scheduler metadata (winch/position-trigger flags)

Execution logic stays in ``actions.py`` handler classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .hardware import HardwareControllers


@dataclass(frozen=True)
class ParamField:
    """Specification for one action parameter."""

    required: bool
    py_type: type
    default: Any = None
    min: float | None = None
    max: float | None = None


@dataclass(frozen=True)
class ParamSpec:
    """Ordered parameter specification for an action type."""

    fields: dict[str, ParamField]

    def validate(self, params: dict[str, Any], *, action_name: str) -> None:
        """Validate params against the spec.

        Raises ValueError on missing required fields, unknown fields, or
        type/range mismatches.
        """
        for name, field in self.fields.items():
            if field.required and name not in params:
                raise ValueError(f"{action_name}: missing required param {name!r}")

        for name, value in params.items():
            if name not in self.fields:
                raise ValueError(f"{action_name}: unknown param {name!r}")

            field = self.fields[name]
            if not isinstance(value, field.py_type):
                try:
                    value = field.py_type(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"{action_name}: param {name!r} expected {field.py_type.__name__}, got {type(value).__name__}"
                    ) from exc

            if field.min is not None and value < field.min:
                raise ValueError(f"{action_name}: param {name!r} below min {field.min}")
            if field.max is not None and value > field.max:
                raise ValueError(f"{action_name}: param {name!r} above max {field.max}")

    def with_defaults(self, params: dict[str, Any]) -> dict[str, Any]:
        """Return params merged with defaults for missing optional fields."""
        merged = dict(params)
        for name, field in self.fields.items():
            if not field.required and name not in merged and field.default is not None:
                merged[name] = field.default
        return merged


@dataclass(frozen=True)
class ActionMetadata:
    """Scheduler/runner metadata for an action type."""

    is_winch_action: bool = False
    supports_position_trigger: bool = False


@dataclass(frozen=True)
class ActionType:
    """Complete specification for one workflow action type."""

    name: str
    param_spec: ParamSpec
    description_template: str | Callable[[dict[str, Any]], str]
    handler_factory: Callable[[HardwareControllers, Any, Any], Any]
    metadata: ActionMetadata


def _clamp_acceleration(acceleration: int) -> int:
    return max(5, min(30, acceleration))


def _winch_increment_description(params: dict[str, Any]) -> str:
    length = params.get("length", 0)
    speed = params.get("speed", 1)
    direction = "up" if length < 0 else "down"
    return f"Move {abs(length)}mm {direction} at {speed}mm/s"


def _winch_absolute_description(params: dict[str, Any]) -> str:
    length = params.get("length", 0)
    speed = params.get("speed", 1)
    return f"Move to {length}mm at {speed}mm/s"


def _valve_turn_description(params: dict[str, Any]) -> str:
    turn_value = params.get("turn_value", 0.0)
    if turn_value == 0.0:
        return "Close valve"
    return f"Open valve to {turn_value:.1f}"


def _spray_gimbal_description(params: dict[str, Any]) -> str:
    angle = params.get("angle", 0)
    speed = params.get("speed", 10)
    return f"Gimbal to {angle}° at {speed}°/s"


def _arm_extend_description(params: dict[str, Any]) -> str:
    distance = params.get("distance", 0)
    return f"Extend arm to {distance}mm"


def _ef_force_description(params: dict[str, Any]) -> str:
    fx = params.get("fx", 0.0)
    fy = params.get("fy", 0.0)
    return f"Set force Fx={fx:.1f}, Fy={fy:.1f}"


def _time_wait_description(params: dict[str, Any]) -> str:
    duration_ms = int(params.get("duration_ms", 0) or 0)
    if duration_ms >= 1000 and duration_ms % 1000 == 0:
        return f"Wait {duration_ms // 1000}s"
    return f"Wait {duration_ms}ms"


_WINCH_PARAMS = ParamSpec(
    {
        "length": ParamField(required=True, py_type=int),
        "speed": ParamField(required=False, py_type=int, default=1, min=1),
        "acceleration": ParamField(required=False, py_type=int, default=10, min=5, max=30),
    }
)

ACTION_TYPES: tuple[ActionType, ...] = (
    ActionType(
        name="winch_increment",
        param_spec=_WINCH_PARAMS,
        description_template=_winch_increment_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["WinchIncrementHandler"]
        ).WinchIncrementHandler(hardware, logger),
        metadata=ActionMetadata(is_winch_action=True, supports_position_trigger=True),
    ),
    ActionType(
        name="winch_absolute",
        param_spec=_WINCH_PARAMS,
        description_template=_winch_absolute_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["WinchAbsoluteHandler"]
        ).WinchAbsoluteHandler(hardware, logger),
        metadata=ActionMetadata(is_winch_action=True, supports_position_trigger=True),
    ),
    ActionType(
        name="winch_move_absolute",
        param_spec=_WINCH_PARAMS,
        description_template=_winch_absolute_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["WinchAbsoluteHandler"]
        ).WinchAbsoluteHandler(hardware, logger),
        metadata=ActionMetadata(is_winch_action=True, supports_position_trigger=True),
    ),
    ActionType(
        name="valve_turn",
        param_spec=ParamSpec({"turn_value": ParamField(required=True, py_type=float)}),
        description_template=_valve_turn_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["ValveTurnHandler"]
        ).ValveTurnHandler(hardware, logger),
        metadata=ActionMetadata(),
    ),
    ActionType(
        name="spray_gimbal",
        param_spec=ParamSpec(
            {
                "angle": ParamField(required=True, py_type=float),
                "speed": ParamField(required=False, py_type=float, default=10.0, min=0.1),
            }
        ),
        description_template=_spray_gimbal_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["SprayGimbalHandler"]
        ).SprayGimbalHandler(hardware, logger),
        metadata=ActionMetadata(),
    ),
    ActionType(
        name="arm_extend",
        param_spec=ParamSpec({"distance": ParamField(required=True, py_type=int)}),
        description_template=_arm_extend_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["ArmExtendHandler"]
        ).ArmExtendHandler(hardware, logger, ros_node),
        metadata=ActionMetadata(),
    ),
    ActionType(
        name="ef_force",
        param_spec=ParamSpec(
            {
                "fx": ParamField(required=True, py_type=float),
                "fy": ParamField(required=True, py_type=float),
            }
        ),
        description_template=_ef_force_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["EFForceHandler"]
        ).EFForceHandler(hardware, logger, ros_node),
        metadata=ActionMetadata(),
    ),
    ActionType(
        name="time_wait",
        param_spec=ParamSpec(
            {
                "duration_ms": ParamField(required=True, py_type=int, min=1),
            }
        ),
        description_template=_time_wait_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["TimeWaitHandler"]
        ).TimeWaitHandler(logger),
        metadata=ActionMetadata(),
    ),
    # Legacy aliases
    ActionType(
        name="teensy_gimbal",
        param_spec=ParamSpec(
            {
                "angle": ParamField(required=True, py_type=float),
                "speed": ParamField(required=False, py_type=float, default=10.0, min=0.1),
            }
        ),
        description_template=_spray_gimbal_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["SprayGimbalHandler"]
        ).SprayGimbalHandler(hardware, logger),
        metadata=ActionMetadata(),
    ),
    ActionType(
        name="teensy_arm_extend",
        param_spec=ParamSpec({"distance": ParamField(required=True, py_type=int)}),
        description_template=_arm_extend_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["ArmExtendHandler"]
        ).ArmExtendHandler(hardware, logger, ros_node),
        metadata=ActionMetadata(),
    ),
)

_ACTION_TYPE_MAP: dict[str, ActionType] = {action.name: action for action in ACTION_TYPES}


def get_action_type(name: str | None) -> ActionType | None:
    """Return the ActionType for a name, or None if unknown/missing."""
    if name is None:
        return None
    return _ACTION_TYPE_MAP.get(name)


def validate_action_params(action_type: str, params: dict[str, Any], *, action_name: str) -> None:
    """Validate params for an action type; raises ValueError for unknown types."""
    action = get_action_type(action_type)
    if action is None:
        raise ValueError(f"{action_name}: unknown action type {action_type!r}")
    action.param_spec.validate(params, action_name=action_name)


def build_action_description(action_type: str, params: dict[str, Any]) -> str:
    """Build the base human-readable description for an action."""
    action = get_action_type(action_type)
    if action is None:
        return ", ".join([f"{k}={v}" for k, v in params.items()]) if params else "No parameters"

    if callable(action.description_template):
        return action.description_template(params)
    return action.description_template.format(**params)
