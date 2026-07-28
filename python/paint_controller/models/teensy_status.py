"""QML-facing teensy telemetry with cached fields and fine-grained NOTIFY (TD-037 Slice C)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.models.status_wiring import connect_required

# Dict-key projection from TeensyController.all_status / status_changed payload.
# (status_key, property_name, kind) where kind is "bool" | "float" | "int"
_TEENS_DICT_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("enabled", "enabled", "bool"),
    ("relay_on", "relayOn", "bool"),
    ("voltage", "voltage", "float"),
    ("current", "current", "float"),
    ("temperature", "temperature", "float"),
    ("run_time", "runTime", "float"),
    ("loop_time", "loopTime", "float"),
    ("loop_time_counter", "loopTimeCounter", "float"),
    ("imu_pitch", "imuPitch", "float"),
    ("imu_roll", "imuRoll", "float"),
    ("imu_yaw", "imuYaw", "float"),
    ("yaw_command", "yawCommand", "float"),
    ("yaw_pid_p", "yawPidP", "float"),
    ("yaw_pid_i", "yawPidI", "float"),
    ("yaw_pid_d", "yawPidD", "float"),
    ("imu_acc_x", "imuAccX", "float"),
    ("imu_acc_y", "imuAccY", "float"),
    ("imu_acc_z", "imuAccZ", "float"),
    ("imu_angular_acc_x", "imuAngularAccX", "float"),
    ("imu_angular_acc_y", "imuAngularAccY", "float"),
    ("imu_angular_acc_z", "imuAngularAccZ", "float"),
    ("arm_extension_dist", "armExtensionDist", "float"),
    ("arm_rail_current", "armRailCurrent", "float"),
    ("gimbal_pitch_motor_current", "gimbalPitchMotorCurrent", "float"),
    ("gimbal_pitch_motor_angle", "gimbalPitchMotorAngle", "float"),
    ("top_rail_position", "topRailPosition", "float"),
    ("top_rail_speed", "topRailSpeed", "float"),
    ("top_rail_current", "topRailCurrent", "float"),
    ("arm_rail_position", "armRailPosition", "float"),
    ("arm_rail_speed", "armRailSpeed", "float"),
    ("arm_sensor_dist", "armSensorDist", "float"),
    ("left_prop_position", "leftPropPosition", "float"),
    ("right_prop_position", "rightPropPosition", "float"),
    ("left_prop_pwm", "leftPropPwm", "int"),
    ("right_prop_pwm", "rightPropPwm", "int"),
    ("spray_gun_pitch", "sprayGunPitch", "float"),
    ("gimbal_pitch_motor_temp", "gimbalPitchMotorTemp", "float"),
    ("gimbal_roll_motor_angle", "gimbalRollMotorAngle", "float"),
    ("gimbal_roll_motor_current", "gimbalRollMotorCurrent", "float"),
    ("gimbal_roll_motor_temp", "gimbalRollMotorTemp", "float"),
    ("spray_gun_trigger", "sprayGunTrigger", "bool"),
    ("yaw_enabled", "yawEnabled", "bool"),
    ("lidar_power", "lidarPower", "bool"),
)

# Controller Property (not only all_status) → status notify signal name.
_TEENS_CONTROLLER_BOOL_FIELDS: tuple[tuple[str, str, str], ...] = (
    # (controller_attr, property_name, producer_signal)
    ("stability_enabled", "stabilityEnabled", "stability_enabled_changed"),
    ("auto_correction_enabled", "autoCorrectionEnabled", "auto_correction_enabled_changed"),
    ("spray_gun_leveling_enabled", "sprayGunLevelingEnabled", "spray_gun_leveling_changed"),
    ("roller_steering_enabled", "rollerSteeringEnabled", "roller_steering_enabled_changed"),
    ("swing_damping_enabled", "swingDampingEnabled", "swing_damping_enabled_changed"),
    ("spray_gun_led_on", "sprayGunLedOn", "spray_gun_led_changed"),
)

TEENS_STATUS_PROPERTY_NAMES: tuple[str, ...] = tuple(
    [name for _, name, _ in _TEENS_DICT_FIELDS]
    + [name for _, name, _ in _TEENS_CONTROLLER_BOOL_FIELDS]
)


def _coerce(value: Any, kind: str) -> Any:
    if kind == "bool":
        return bool(value)
    if kind == "int":
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


class TeensyStatus(QObject):
    """Cached camelCase teensy face for QML with fine-grained property notifies."""

    enabledChanged = Signal()
    relayOnChanged = Signal()
    voltageChanged = Signal()
    currentChanged = Signal()
    temperatureChanged = Signal()
    runTimeChanged = Signal()
    loopTimeChanged = Signal()
    loopTimeCounterChanged = Signal()
    imuPitchChanged = Signal()
    imuRollChanged = Signal()
    imuYawChanged = Signal()
    yawCommandChanged = Signal()
    yawPidPChanged = Signal()
    yawPidIChanged = Signal()
    yawPidDChanged = Signal()
    imuAccXChanged = Signal()
    imuAccYChanged = Signal()
    imuAccZChanged = Signal()
    imuAngularAccXChanged = Signal()
    imuAngularAccYChanged = Signal()
    imuAngularAccZChanged = Signal()
    armExtensionDistChanged = Signal()
    armRailCurrentChanged = Signal()
    gimbalPitchMotorCurrentChanged = Signal()
    gimbalPitchMotorAngleChanged = Signal()
    topRailPositionChanged = Signal()
    topRailSpeedChanged = Signal()
    topRailCurrentChanged = Signal()
    armRailPositionChanged = Signal()
    armRailSpeedChanged = Signal()
    armSensorDistChanged = Signal()
    leftPropPositionChanged = Signal()
    rightPropPositionChanged = Signal()
    leftPropPwmChanged = Signal()
    rightPropPwmChanged = Signal()
    sprayGunPitchChanged = Signal()
    gimbalPitchMotorTempChanged = Signal()
    gimbalRollMotorAngleChanged = Signal()
    gimbalRollMotorCurrentChanged = Signal()
    gimbalRollMotorTempChanged = Signal()
    sprayGunTriggerChanged = Signal()
    yawEnabledChanged = Signal()
    lidarPowerChanged = Signal()
    stabilityEnabledChanged = Signal()
    autoCorrectionEnabledChanged = Signal()
    sprayGunLevelingEnabledChanged = Signal()
    rollerSteeringEnabledChanged = Signal()
    swingDampingEnabledChanged = Signal()
    sprayGunLedOnChanged = Signal()

    def __init__(self, teensy_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._c = teensy_controller
        self._cache: dict[str, Any] = {}
        # property_name -> notify signal
        self._notifiers: dict[str, Any] = {
            "enabled": self.enabledChanged,
            "relayOn": self.relayOnChanged,
            "voltage": self.voltageChanged,
            "current": self.currentChanged,
            "temperature": self.temperatureChanged,
            "runTime": self.runTimeChanged,
            "loopTime": self.loopTimeChanged,
            "loopTimeCounter": self.loopTimeCounterChanged,
            "imuPitch": self.imuPitchChanged,
            "imuRoll": self.imuRollChanged,
            "imuYaw": self.imuYawChanged,
            "yawCommand": self.yawCommandChanged,
            "yawPidP": self.yawPidPChanged,
            "yawPidI": self.yawPidIChanged,
            "yawPidD": self.yawPidDChanged,
            "imuAccX": self.imuAccXChanged,
            "imuAccY": self.imuAccYChanged,
            "imuAccZ": self.imuAccZChanged,
            "imuAngularAccX": self.imuAngularAccXChanged,
            "imuAngularAccY": self.imuAngularAccYChanged,
            "imuAngularAccZ": self.imuAngularAccZChanged,
            "armExtensionDist": self.armExtensionDistChanged,
            "armRailCurrent": self.armRailCurrentChanged,
            "gimbalPitchMotorCurrent": self.gimbalPitchMotorCurrentChanged,
            "gimbalPitchMotorAngle": self.gimbalPitchMotorAngleChanged,
            "topRailPosition": self.topRailPositionChanged,
            "topRailSpeed": self.topRailSpeedChanged,
            "topRailCurrent": self.topRailCurrentChanged,
            "armRailPosition": self.armRailPositionChanged,
            "armRailSpeed": self.armRailSpeedChanged,
            "armSensorDist": self.armSensorDistChanged,
            "leftPropPosition": self.leftPropPositionChanged,
            "rightPropPosition": self.rightPropPositionChanged,
            "leftPropPwm": self.leftPropPwmChanged,
            "rightPropPwm": self.rightPropPwmChanged,
            "sprayGunPitch": self.sprayGunPitchChanged,
            "gimbalPitchMotorTemp": self.gimbalPitchMotorTempChanged,
            "gimbalRollMotorAngle": self.gimbalRollMotorAngleChanged,
            "gimbalRollMotorCurrent": self.gimbalRollMotorCurrentChanged,
            "gimbalRollMotorTemp": self.gimbalRollMotorTempChanged,
            "sprayGunTrigger": self.sprayGunTriggerChanged,
            "yawEnabled": self.yawEnabledChanged,
            "lidarPower": self.lidarPowerChanged,
            "stabilityEnabled": self.stabilityEnabledChanged,
            "autoCorrectionEnabled": self.autoCorrectionEnabledChanged,
            "sprayGunLevelingEnabled": self.sprayGunLevelingEnabledChanged,
            "rollerSteeringEnabled": self.rollerSteeringEnabledChanged,
            "swingDampingEnabled": self.swingDampingEnabledChanged,
            "sprayGunLedOn": self.sprayGunLedOnChanged,
        }

        connect_required(teensy_controller, "status_changed", self._on_status_changed)
        for _attr, prop_name, signal_name in _TEENS_CONTROLLER_BOOL_FIELDS:
            notify = self._notifiers[prop_name]
            connect_required(
                teensy_controller,
                signal_name,
                lambda n=notify, a=_attr, p=prop_name: self._refresh_controller_bool(a, p, n),
            )

        # Seed cache from current controller snapshot.
        initial = getattr(teensy_controller, "all_status", None)
        if isinstance(initial, dict):
            self._apply_dict_snapshot(initial, emit=False)
        for attr, prop_name, _signal in _TEENS_CONTROLLER_BOOL_FIELDS:
            self._cache[prop_name] = bool(getattr(teensy_controller, attr, False))

    def _on_status_changed(self, *args: Any) -> None:
        if args and isinstance(args[0], dict):
            snapshot = args[0]
        else:
            snapshot = getattr(self._c, "all_status", {}) or {}
        if not isinstance(snapshot, dict):
            snapshot = {}
        self._apply_dict_snapshot(snapshot, emit=True)
        # Keep controller-property flags in sync when only status_changed fires.
        for attr, prop_name, _signal in _TEENS_CONTROLLER_BOOL_FIELDS:
            notify = self._notifiers[prop_name]
            self._refresh_controller_bool(attr, prop_name, notify)

    def _apply_dict_snapshot(self, snapshot: dict[str, Any], *, emit: bool) -> None:
        for key, prop_name, kind in _TEENS_DICT_FIELDS:
            new_value = _coerce(snapshot.get(key), kind)
            old_value = self._cache.get(prop_name, object())
            if old_value != new_value:
                self._cache[prop_name] = new_value
                if emit:
                    self._notifiers[prop_name].emit()

    def _refresh_controller_bool(self, attr: str, prop_name: str, notify: Any) -> None:
        new_value = bool(getattr(self._c, attr, False))
        if self._cache.get(prop_name, object()) != new_value:
            self._cache[prop_name] = new_value
            notify.emit()

    def _get(self, prop_name: str, default: Any = 0) -> Any:
        if prop_name in self._cache:
            return self._cache[prop_name]
        return default

    # --- QML properties (camelCase surface unchanged from composer wrapper) ---

    @Property(bool, notify=enabledChanged)
    def enabled(self) -> bool:
        return bool(self._get("enabled", False))

    @Property(bool, notify=relayOnChanged)
    def relayOn(self) -> bool:
        return bool(self._get("relayOn", False))

    @Property(float, notify=voltageChanged)
    def voltage(self) -> float:
        return float(self._get("voltage", 0.0))

    @Property(float, notify=currentChanged)
    def current(self) -> float:
        return float(self._get("current", 0.0))

    @Property(float, notify=temperatureChanged)
    def temperature(self) -> float:
        return float(self._get("temperature", 0.0))

    @Property(float, notify=runTimeChanged)
    def runTime(self) -> float:
        return float(self._get("runTime", 0.0))

    @Property(float, notify=loopTimeChanged)
    def loopTime(self) -> float:
        return float(self._get("loopTime", 0.0))

    @Property(float, notify=loopTimeCounterChanged)
    def loopTimeCounter(self) -> float:
        return float(self._get("loopTimeCounter", 0.0))

    @Property(float, notify=imuPitchChanged)
    def imuPitch(self) -> float:
        return float(self._get("imuPitch", 0.0))

    @Property(float, notify=imuRollChanged)
    def imuRoll(self) -> float:
        return float(self._get("imuRoll", 0.0))

    @Property(float, notify=imuYawChanged)
    def imuYaw(self) -> float:
        return float(self._get("imuYaw", 0.0))

    @Property(float, notify=yawCommandChanged)
    def yawCommand(self) -> float:
        return float(self._get("yawCommand", 0.0))

    @Property(float, notify=yawPidPChanged)
    def yawPidP(self) -> float:
        return float(self._get("yawPidP", 0.0))

    @Property(float, notify=yawPidIChanged)
    def yawPidI(self) -> float:
        return float(self._get("yawPidI", 0.0))

    @Property(float, notify=yawPidDChanged)
    def yawPidD(self) -> float:
        return float(self._get("yawPidD", 0.0))

    @Property(float, notify=imuAccXChanged)
    def imuAccX(self) -> float:
        return float(self._get("imuAccX", 0.0))

    @Property(float, notify=imuAccYChanged)
    def imuAccY(self) -> float:
        return float(self._get("imuAccY", 0.0))

    @Property(float, notify=imuAccZChanged)
    def imuAccZ(self) -> float:
        return float(self._get("imuAccZ", 0.0))

    @Property(float, notify=imuAngularAccXChanged)
    def imuAngularAccX(self) -> float:
        return float(self._get("imuAngularAccX", 0.0))

    @Property(float, notify=imuAngularAccYChanged)
    def imuAngularAccY(self) -> float:
        return float(self._get("imuAngularAccY", 0.0))

    @Property(float, notify=imuAngularAccZChanged)
    def imuAngularAccZ(self) -> float:
        return float(self._get("imuAngularAccZ", 0.0))

    @Property(float, notify=armExtensionDistChanged)
    def armExtensionDist(self) -> float:
        return float(self._get("armExtensionDist", 0.0))

    @Property(float, notify=armRailCurrentChanged)
    def armRailCurrent(self) -> float:
        return float(self._get("armRailCurrent", 0.0))

    @Property(float, notify=gimbalPitchMotorCurrentChanged)
    def gimbalPitchMotorCurrent(self) -> float:
        return float(self._get("gimbalPitchMotorCurrent", 0.0))

    @Property(float, notify=gimbalPitchMotorAngleChanged)
    def gimbalPitchMotorAngle(self) -> float:
        return float(self._get("gimbalPitchMotorAngle", 0.0))

    @Property(float, notify=topRailPositionChanged)
    def topRailPosition(self) -> float:
        return float(self._get("topRailPosition", 0.0))

    @Property(float, notify=topRailSpeedChanged)
    def topRailSpeed(self) -> float:
        return float(self._get("topRailSpeed", 0.0))

    @Property(float, notify=topRailCurrentChanged)
    def topRailCurrent(self) -> float:
        return float(self._get("topRailCurrent", 0.0))

    @Property(float, notify=armRailPositionChanged)
    def armRailPosition(self) -> float:
        return float(self._get("armRailPosition", 0.0))

    @Property(float, notify=armRailSpeedChanged)
    def armRailSpeed(self) -> float:
        return float(self._get("armRailSpeed", 0.0))

    @Property(float, notify=armSensorDistChanged)
    def armSensorDist(self) -> float:
        return float(self._get("armSensorDist", 0.0))

    @Property(float, notify=leftPropPositionChanged)
    def leftPropPosition(self) -> float:
        return float(self._get("leftPropPosition", 0.0))

    @Property(float, notify=rightPropPositionChanged)
    def rightPropPosition(self) -> float:
        return float(self._get("rightPropPosition", 0.0))

    @Property(int, notify=leftPropPwmChanged)
    def leftPropPwm(self) -> int:
        return int(self._get("leftPropPwm", 0))

    @Property(int, notify=rightPropPwmChanged)
    def rightPropPwm(self) -> int:
        return int(self._get("rightPropPwm", 0))

    @Property(float, notify=sprayGunPitchChanged)
    def sprayGunPitch(self) -> float:
        return float(self._get("sprayGunPitch", 0.0))

    @Property(float, notify=gimbalPitchMotorTempChanged)
    def gimbalPitchMotorTemp(self) -> float:
        return float(self._get("gimbalPitchMotorTemp", 0.0))

    @Property(float, notify=gimbalRollMotorAngleChanged)
    def gimbalRollMotorAngle(self) -> float:
        return float(self._get("gimbalRollMotorAngle", 0.0))

    @Property(float, notify=gimbalRollMotorCurrentChanged)
    def gimbalRollMotorCurrent(self) -> float:
        return float(self._get("gimbalRollMotorCurrent", 0.0))

    @Property(float, notify=gimbalRollMotorTempChanged)
    def gimbalRollMotorTemp(self) -> float:
        return float(self._get("gimbalRollMotorTemp", 0.0))

    @Property(bool, notify=sprayGunTriggerChanged)
    def sprayGunTrigger(self) -> bool:
        return bool(self._get("sprayGunTrigger", False))

    @Property(bool, notify=yawEnabledChanged)
    def yawEnabled(self) -> bool:
        return bool(self._get("yawEnabled", False))

    @Property(bool, notify=lidarPowerChanged)
    def lidarPower(self) -> bool:
        return bool(self._get("lidarPower", False))

    @Property(bool, notify=stabilityEnabledChanged)
    def stabilityEnabled(self) -> bool:
        return bool(self._get("stabilityEnabled", False))

    @Property(bool, notify=autoCorrectionEnabledChanged)
    def autoCorrectionEnabled(self) -> bool:
        return bool(self._get("autoCorrectionEnabled", False))

    @Property(bool, notify=sprayGunLevelingEnabledChanged)
    def sprayGunLevelingEnabled(self) -> bool:
        return bool(self._get("sprayGunLevelingEnabled", False))

    @Property(bool, notify=rollerSteeringEnabledChanged)
    def rollerSteeringEnabled(self) -> bool:
        return bool(self._get("rollerSteeringEnabled", False))

    @Property(bool, notify=swingDampingEnabledChanged)
    def swingDampingEnabled(self) -> bool:
        return bool(self._get("swingDampingEnabled", False))

    @Property(bool, notify=sprayGunLedOnChanged)
    def sprayGunLedOn(self) -> bool:
        return bool(self._get("sprayGunLedOn", False))
