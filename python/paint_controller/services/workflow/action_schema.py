"""Central registry for workflow action types.

Single source of truth for:
- action type name
- parameter specification (validation + editor field lists)
- human-readable description template
- handler factory
- duration estimate policy
- wait-done completion policy
- palette visibility

Execution logic stays in ``actions.py`` handler classes.
Estimate math lives in ``estimate.py``; wait-done in ``completion.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .hardware import HardwareControllers


# ---------------------------------------------------------------------------
# Parameter specs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParamField:
    """Specification for one action parameter."""

    required: bool
    py_type: type
    default: Any = None
    min: float | None = None
    max: float | None = None
    label: str | None = None


@dataclass(frozen=True)
class ParamSpec:
    """Ordered parameter specification for an action type."""

    fields: dict[str, ParamField]

    def validate(self, params: dict[str, Any], *, action_name: str) -> None:
        """Validate params against the spec.

        Raises ValueError on missing required fields, unknown fields, or
        type/range mismatches.
        """
        for name, field_spec in self.fields.items():
            if field_spec.required and name not in params:
                raise ValueError(f"{action_name}: missing required param {name!r}")

        for name, value in params.items():
            if name not in self.fields:
                raise ValueError(f"{action_name}: unknown param {name!r}")

            field_spec = self.fields[name]
            if not isinstance(value, field_spec.py_type):
                try:
                    value = field_spec.py_type(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"{action_name}: param {name!r} expected {field_spec.py_type.__name__}, "
                        f"got {type(value).__name__}"
                    ) from exc

            if field_spec.min is not None and value < field_spec.min:
                raise ValueError(f"{action_name}: param {name!r} below min {field_spec.min}")
            if field_spec.max is not None and value > field_spec.max:
                raise ValueError(f"{action_name}: param {name!r} above max {field_spec.max}")

    def with_defaults(self, params: dict[str, Any]) -> dict[str, Any]:
        """Return params merged with defaults for missing optional fields."""
        merged = dict(params)
        for name, field_spec in self.fields.items():
            if not field_spec.required and name not in merged and field_spec.default is not None:
                merged[name] = field_spec.default
        return merged

    def fields_for_qml(self) -> list[dict[str, Any]]:
        """Editor-binding list of param fields (presentation only)."""
        rows: list[dict[str, Any]] = []
        for name, field_spec in self.fields.items():
            rows.append(
                {
                    "key": name,
                    "label": field_spec.label or name.replace("_", " ").title(),
                    "required": field_spec.required,
                    "type": field_spec.py_type.__name__,
                    "default": field_spec.default,
                    "min": field_spec.min,
                    "max": field_spec.max,
                }
            )
        return rows


# ---------------------------------------------------------------------------
# Estimate + completion policies
# ---------------------------------------------------------------------------


class EstimateMode:
    FIXED_MS = "fixed_ms"
    DURATION_MS_PARAM = "duration_ms_param"
    ABS_PARAM_OVER_SPEED = "abs_param_over_speed"
    SIGNED_PARAM_OVER_SPEED = "signed_param_over_speed"


@dataclass(frozen=True)
class EstimateSpec:
    """How to compute schedule duration for an action type."""

    mode: str = EstimateMode.FIXED_MS
    fixed_ms: int = 1000
    primary_param: str = ""
    speed_param: str = "speed"
    default_speed: float = 1.0
    use_hardware_delta: bool = False  # absolute targets may use |target-current|

    @staticmethod
    def fixed(ms: int) -> EstimateSpec:
        return EstimateSpec(mode=EstimateMode.FIXED_MS, fixed_ms=ms)

    @staticmethod
    def duration_ms_param(param: str = "duration_ms") -> EstimateSpec:
        return EstimateSpec(mode=EstimateMode.DURATION_MS_PARAM, primary_param=param)

    @staticmethod
    def abs_over_speed(
        primary: str = "length",
        speed: str = "speed",
        *,
        default_speed: float = 1.0,
        use_hardware_delta: bool = False,
    ) -> EstimateSpec:
        return EstimateSpec(
            mode=EstimateMode.ABS_PARAM_OVER_SPEED,
            primary_param=primary,
            speed_param=speed,
            default_speed=default_speed,
            use_hardware_delta=use_hardware_delta,
        )

    @staticmethod
    def signed_over_speed(
        primary: str = "length",
        speed: str = "speed",
        *,
        default_speed: float = 1.0,
    ) -> EstimateSpec:
        return EstimateSpec(
            mode=EstimateMode.SIGNED_PARAM_OVER_SPEED,
            primary_param=primary,
            speed_param=speed,
            default_speed=default_speed,
        )


class CompletionKind:
    TIMED = "timed"
    FEEDBACK = "feedback"
    HYBRID = "hybrid"
    IMMEDIATE = "immediate"


@dataclass(frozen=True)
class FeedbackSource:
    """Scalar feedback used for wait-done (reader key is registered on CompletionTracker)."""

    reader_key: str
    target_param: str
    tolerance: float = 50.0
    timeout_scale: float = 2.0


@dataclass(frozen=True)
class CompletionSpec:
    """How Wait-done decides the action is finished."""

    kind: str = CompletionKind.TIMED
    feedback: FeedbackSource | None = None

    @staticmethod
    def timed() -> CompletionSpec:
        return CompletionSpec(kind=CompletionKind.TIMED)

    @staticmethod
    def hybrid_feedback(source: FeedbackSource) -> CompletionSpec:
        return CompletionSpec(kind=CompletionKind.HYBRID, feedback=source)

    @staticmethod
    def feedback_only(source: FeedbackSource) -> CompletionSpec:
        return CompletionSpec(kind=CompletionKind.FEEDBACK, feedback=source)

    @staticmethod
    def immediate() -> CompletionSpec:
        return CompletionSpec(kind=CompletionKind.IMMEDIATE)


@dataclass(frozen=True)
class ActionMetadata:
    """Registry metadata: estimate, completion, palette, schedule hints."""

    # Schedule / position-trigger family (not the same as completion policy).
    is_winch_action: bool = False
    supports_position_trigger: bool = False
    palette: bool = False
    palette_label: str | None = None
    estimate: EstimateSpec = field(default_factory=lambda: EstimateSpec.fixed(1000))
    completion: CompletionSpec = field(default_factory=CompletionSpec.timed)


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
        "length": ParamField(required=True, py_type=int, label="Length (mm)"),
        "speed": ParamField(required=False, py_type=int, default=1, min=1, label="Speed (mm/s)"),
        "acceleration": ParamField(
            required=False, py_type=int, default=10, min=5, max=30, label="Acceleration"
        ),
    }
)

_WINCH_FEEDBACK = FeedbackSource(
    reader_key="winch_cable_length",
    target_param="length",
    tolerance=50.0,
    timeout_scale=2.0,
)

_WINCH_META_LEGACY = ActionMetadata(
    is_winch_action=True,
    supports_position_trigger=True,
    palette=False,
    estimate=EstimateSpec.abs_over_speed("length", "speed", default_speed=1.0, use_hardware_delta=True),
    completion=CompletionSpec.hybrid_feedback(_WINCH_FEEDBACK),
)

# Increment uses signed distance (no absolute hardware delta); timed wait-done.
_WINCH_INC_META = ActionMetadata(
    is_winch_action=True,
    supports_position_trigger=True,
    palette=True,
    palette_label="Winch Increment",
    estimate=EstimateSpec.signed_over_speed("length", "speed", default_speed=1.0),
    completion=CompletionSpec.timed(),
)

ACTION_TYPES: tuple[ActionType, ...] = (
    ActionType(
        name="winch_increment",
        param_spec=_WINCH_PARAMS,
        description_template=_winch_increment_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["WinchIncrementHandler"]
        ).WinchIncrementHandler(hardware, logger),
        metadata=_WINCH_INC_META,
    ),
    ActionType(
        name="winch_absolute",
        param_spec=_WINCH_PARAMS,
        description_template=_winch_absolute_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["WinchAbsoluteHandler"]
        ).WinchAbsoluteHandler(hardware, logger),
        metadata=ActionMetadata(
            is_winch_action=True,
            supports_position_trigger=True,
            palette=True,
            palette_label="Winch Absolute",
            estimate=EstimateSpec.abs_over_speed(
                "length", "speed", default_speed=1.0, use_hardware_delta=True
            ),
            completion=CompletionSpec.hybrid_feedback(_WINCH_FEEDBACK),
        ),
    ),
    ActionType(
        name="winch_move_absolute",
        param_spec=_WINCH_PARAMS,
        description_template=_winch_absolute_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["WinchAbsoluteHandler"]
        ).WinchAbsoluteHandler(hardware, logger),
        metadata=_WINCH_META_LEGACY,
    ),
    ActionType(
        name="valve_turn",
        param_spec=ParamSpec(
            {"turn_value": ParamField(required=True, py_type=float, label="Turn value")}
        ),
        description_template=_valve_turn_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["ValveTurnHandler"]
        ).ValveTurnHandler(hardware, logger),
        metadata=ActionMetadata(
            palette=True,
            palette_label="Valve",
            estimate=EstimateSpec.fixed(500),
            completion=CompletionSpec.timed(),
        ),
    ),
    ActionType(
        name="spray_gimbal",
        param_spec=ParamSpec(
            {
                "angle": ParamField(required=True, py_type=float, label="Angle (°)"),
                "speed": ParamField(
                    required=False, py_type=float, default=10.0, min=0.1, label="Speed (°/s)"
                ),
            }
        ),
        description_template=_spray_gimbal_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["SprayGimbalHandler"]
        ).SprayGimbalHandler(hardware, logger),
        metadata=ActionMetadata(
            palette=True,
            palette_label="Spray Gimbal",
            estimate=EstimateSpec.abs_over_speed(
                "angle", "speed", default_speed=10.0, use_hardware_delta=False
            ),
            completion=CompletionSpec.timed(),
        ),
    ),
    ActionType(
        name="arm_extend",
        param_spec=ParamSpec(
            {"distance": ParamField(required=True, py_type=int, label="Distance (mm)")}
        ),
        description_template=_arm_extend_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["ArmExtendHandler"]
        ).ArmExtendHandler(hardware, logger, ros_node),
        metadata=ActionMetadata(
            palette=True,
            palette_label="Arm Extend",
            estimate=EstimateSpec.fixed(2000),
            completion=CompletionSpec.timed(),
        ),
    ),
    ActionType(
        name="ef_force",
        param_spec=ParamSpec(
            {
                "fx": ParamField(required=True, py_type=float, label="Fx"),
                "fy": ParamField(required=True, py_type=float, label="Fy"),
            }
        ),
        description_template=_ef_force_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["EFForceHandler"]
        ).EFForceHandler(hardware, logger, ros_node),
        metadata=ActionMetadata(
            palette=True,
            palette_label="EF Force",
            estimate=EstimateSpec.fixed(1500),
            completion=CompletionSpec.timed(),
        ),
    ),
    ActionType(
        name="time_wait",
        param_spec=ParamSpec(
            {
                "duration_ms": ParamField(
                    required=True, py_type=int, min=1, default=1000, label="Duration (ms)"
                ),
            }
        ),
        description_template=_time_wait_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["TimeWaitHandler"]
        ).TimeWaitHandler(logger),
        metadata=ActionMetadata(
            palette=True,
            palette_label="Wait",
            estimate=EstimateSpec.duration_ms_param("duration_ms"),
            completion=CompletionSpec.timed(),
        ),
    ),
    # Legacy aliases (not on palette)
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
        metadata=ActionMetadata(
            palette=False,
            estimate=EstimateSpec.abs_over_speed("angle", "speed", default_speed=10.0),
            completion=CompletionSpec.timed(),
        ),
    ),
    ActionType(
        name="teensy_arm_extend",
        param_spec=ParamSpec({"distance": ParamField(required=True, py_type=int)}),
        description_template=_arm_extend_description,
        handler_factory=lambda hardware, logger, ros_node: __import__(
            "paint_controller.services.workflow.actions", fromlist=["ArmExtendHandler"]
        ).ArmExtendHandler(hardware, logger, ros_node),
        metadata=ActionMetadata(
            palette=False,
            estimate=EstimateSpec.fixed(2000),
            completion=CompletionSpec.timed(),
        ),
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


def param_fields_for_type(action_type: str) -> list[dict[str, Any]]:
    """QML/editor field list for an action type (empty if unknown)."""
    action = get_action_type(action_type)
    if action is None:
        return []
    return action.param_spec.fields_for_qml()


def palette_action_types() -> list[ActionType]:
    """Registered action types marked for the editor palette (excludes structural kinds)."""
    return [a for a in ACTION_TYPES if a.metadata.palette]


def registry_palette_entries() -> list[dict[str, Any]]:
    """Editor palette entries derived from the action registry (+ structural parallel)."""
    entries: list[dict[str, Any]] = []
    for action in palette_action_types():
        kind = "wait" if action.name == "time_wait" else "action"
        entries.append(
            {
                "type": action.name,
                "kind": kind,
                "label": action.metadata.palette_label
                or action.name.replace("_", " ").title(),
                "description": action.name,
            }
        )
    entries.append(
        {
            "type": "parallel",
            "kind": "parallel",
            "label": "Parallel group",
            "description": "Start multiple actions together",
        }
    )
    return entries


def build_operator_summary(
    action_type: str,
    params: dict[str, Any] | None,
    *,
    action: dict[str, Any] | None = None,
) -> str:
    """Single operator-facing summary (runner list + editor cards)."""
    action = action or {}
    params = dict(params or action.get("params") or {})
    base = action.get("description") or build_action_description(action_type, params)

    timing_parts: list[str] = []
    estimated_duration = action.get("estimated_duration")
    if estimated_duration is not None:
        try:
            duration_sec = float(estimated_duration) / 1000.0
            if duration_sec < 1:
                timing_parts.append(f"~{int(estimated_duration)}ms")
            else:
                timing_parts.append(f"~{duration_sec:.1f}s")
        except (TypeError, ValueError):
            pass

    trigger = action.get("trigger")
    if isinstance(trigger, dict):
        ref_action = trigger.get("reference_action", "?")
        timing_mode = trigger.get("timing_mode", "after_start")
        offset_ms = int(trigger.get("offset_ms", 0) or 0)
        if timing_mode == "before_complete":
            timing_parts.append(f"{offset_ms}ms before '{ref_action}' completes")
        elif timing_mode in ("after_complete", "on_complete"):
            if offset_ms > 0:
                timing_parts.append(f"{offset_ms}ms after '{ref_action}' completes")
            else:
                timing_parts.append(f"after '{ref_action}' completes")
        elif timing_mode == "after_start":
            if offset_ms > 0:
                timing_parts.append(f"{offset_ms}ms after '{ref_action}' starts")
            else:
                timing_parts.append(f"with '{ref_action}'")

    if timing_parts:
        return f"{base} ({', '.join(timing_parts)})"
    return base
