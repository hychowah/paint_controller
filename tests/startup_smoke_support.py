"""Shared support objects for QML startup smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Property, QObject, QSize, Signal, Slot, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickImageProvider

from paint_controller.core.settings import SettingsManager
from paint_controller.core.state_store import StateStore


class DynamicObject(QObject):
    def __init__(self, **properties) -> None:
        super().__init__()
        for key, value in properties.items():
            self.setProperty(key, value)


class FakeLauncherAdmin(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.configs = {
            "BASE": {"ip": "10.0.0.2", "port": "22", "username": "deck", "key_path": "~/.ssh/id_base"},
            "END_EFFECTOR": {"ip": "10.0.0.3", "port": "22", "username": "deck", "key_path": "~/.ssh/id_ef"},
        }

    @Slot(str, result=str)
    def getDeviceConfig(self, device_name: str) -> str:
        return json.dumps(self.configs.get(device_name, {}))

    @Slot(str, str, str, str, str, result=bool)
    def updateDeviceConfig(self, device_name: str, ip: str, port: str, username: str, key_path: str) -> bool:
        self.configs[device_name] = {
            "ip": ip,
            "port": port,
            "username": username,
            "key_path": key_path,
        }
        return True

    @Slot(str, str, str)
    def handleDeviceCommand(self, device_name: str, service_name: str, action: str) -> None:
        return


class FakeBackend(QObject):
    showPopupRequested = Signal(str, str, str, int)
    closePopupRequested = Signal()
    toggleSidebarRequested = Signal()
    toggleVideoOverlayRequested = Signal(bool, str)
    updateVideoSourceRequested = Signal(str)
    emergency_overlay_changed = Signal(bool, float, float)
    emergency_triggered = Signal()
    frame_ready = Signal()
    status_updated = Signal()


class FakeStreamHandler(QObject):
    endEffectorFrameReady = Signal()
    baseFrontFrameReady = Signal()
    baseRearFrameReady = Signal()


class FakeScreenManager(DynamicObject):
    screens_changed = Signal()

    def __init__(self) -> None:
        super().__init__()

    @Slot(result=int)
    def get_screen_count(self) -> int:
        return 1


class FakeBaseTopViewController(QObject):
    frameReady = Signal()
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._enabled = False
        self._edit_mode = False
        self._zoom = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._crop_enabled = False
        self._crop_width_ratio = 0.5
        self._crop_center_x = 0.5
        self._k1 = 0.0
        self._k2 = 0.0
        self._k3 = 0.0
        self._k4 = 0.0

    @Property(bool, notify=changed)
    def enabled(self) -> bool:
        return self._enabled

    @Property(bool, notify=changed)
    def editMode(self) -> bool:
        return self._edit_mode

    @Property(float, notify=changed)
    def zoom(self) -> float:
        return self._zoom

    @Property(float, notify=changed)
    def offsetX(self) -> float:
        return self._offset_x

    @Property(float, notify=changed)
    def offsetY(self) -> float:
        return self._offset_y

    @Property(bool, notify=changed)
    def cropEnabled(self) -> bool:
        return self._crop_enabled

    @Property(float, notify=changed)
    def cropWidthRatio(self) -> float:
        return self._crop_width_ratio

    @Property(float, notify=changed)
    def cropCenterX(self) -> float:
        return self._crop_center_x

    @Property(float, notify=changed)
    def k1(self) -> float:
        return self._k1

    @Property(float, notify=changed)
    def k2(self) -> float:
        return self._k2

    @Property(float, notify=changed)
    def k3(self) -> float:
        return self._k3

    @Property(float, notify=changed)
    def k4(self) -> float:
        return self._k4


class FakeLidarController(QObject):
    distanceChanged = Signal()
    angleChanged = Signal()

    def __init__(self, distance: float = 0.0, angle: float = 0.0) -> None:
        super().__init__()
        self._distance = distance
        self._angle = angle

    @Property(float, notify=distanceChanged)
    def distance(self) -> float:
        return self._distance

    @Property(float, notify=angleChanged)
    def angle(self) -> float:
        return self._angle


class FakeLidarStatus(QObject):
    changed = Signal()

    def __init__(self, distance: float = 0.0, angle: float = 0.0) -> None:
        super().__init__()
        self._distance = distance
        self._angle = angle

    @Property(float, notify=changed)
    def distance(self) -> float:
        return self._distance

    @Property(float, notify=changed)
    def angle(self) -> float:
        return self._angle


class FakeManualCommandHandler(QObject):
    @Slot(str, result=bool)
    def isCommandSupported(self, command_name: str) -> bool:
        return command_name != "Move to Position"

    @Slot(str, "QVariantMap", result=bool)
    def executeCommand(self, _command_name: str, _parameter_values) -> bool:
        return True


class FakeSystemControlServices(QObject):
    def __init__(self, workflow_runner: QObject, workflow_editor: QObject, manual_command_handler: QObject) -> None:
        super().__init__()
        self._workflow_runner = workflow_runner
        self._workflow_editor = workflow_editor
        self._manual_command_handler = manual_command_handler

    @Property(QObject, constant=True)
    def workflowRunner(self) -> QObject:
        return self._workflow_runner

    @Property(QObject, constant=True)
    def workflowEditor(self) -> QObject:
        return self._workflow_editor

    @Property(QObject, constant=True)
    def manualCommandHandler(self) -> QObject:
        return self._manual_command_handler


class FakeVideoRuntimeControls(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._left_mode = "None"
        self._left_value = ""
        self._right_mode = "None"
        self._right_value = ""

    @Property(str, constant=True)
    def leftMode(self) -> str:
        return self._left_mode

    @Property(str, constant=True)
    def leftValue(self) -> str:
        return self._left_value

    @Property(str, constant=True)
    def rightMode(self) -> str:
        return self._right_mode

    @Property(str, constant=True)
    def rightValue(self) -> str:
        return self._right_value


class FakeVideoRuntimeTopBar(QObject):
    changed = Signal()
    endEffectorVideoRequested = Signal()
    baseVideoRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._end_effector_ping_ms = 38.0
        self._base_ping_ms = 42.0
        self._end_effector_battery_voltage = 24.0
        self._base_battery_voltage = 24.0
        self._end_effector_connected = True
        self._base_connected = True
        self._is_recording = False
        self._recording_duration = 0
        self._system_battery_percent = 100
        self._cpu_temperature = 0.0
        self._battery_remaining_time = "--"

    @Property(float, notify=changed)
    def endEffectorPingMs(self) -> float:
        return self._end_effector_ping_ms

    @Property(float, notify=changed)
    def basePingMs(self) -> float:
        return self._base_ping_ms

    @Property(bool, notify=changed)
    def endEffectorConnected(self) -> bool:
        return self._end_effector_connected

    @Property(bool, notify=changed)
    def baseConnected(self) -> bool:
        return self._base_connected

    @Property(float, notify=changed)
    def endEffectorBatteryVoltage(self) -> float:
        return self._end_effector_battery_voltage

    @Property(float, notify=changed)
    def baseBatteryVoltage(self) -> float:
        return self._base_battery_voltage

    @Property(bool, notify=changed)
    def isRecording(self) -> bool:
        return self._is_recording

    @Property(int, notify=changed)
    def recordingDuration(self) -> int:
        return self._recording_duration

    @Property(int, notify=changed)
    def systemBatteryPercent(self) -> int:
        return self._system_battery_percent

    @Property(float, notify=changed)
    def cpuTemperature(self) -> float:
        return self._cpu_temperature

    @Property(str, notify=changed)
    def batteryRemainingTime(self) -> str:
        return self._battery_remaining_time

    @Slot()
    def requestEndEffectorVideo(self) -> None:
        self.endEffectorVideoRequested.emit()

    @Slot()
    def requestBaseVideo(self) -> None:
        self.baseVideoRequested.emit()


class FakeVideoRuntime(QObject):
    def __init__(self) -> None:
        super().__init__()
        self._controls = FakeVideoRuntimeControls()
        self._feeds = FakeStreamHandler()
        self._top_bar = FakeVideoRuntimeTopBar()

    @Property(QObject, constant=True)
    def controls(self) -> QObject:
        return self._controls

    @Property(QObject, constant=True)
    def feeds(self) -> QObject:
        return self._feeds

    @Property(QObject, constant=True)
    def topBar(self) -> QObject:
        return self._top_bar


class FakeDeviceActionHandler(QObject):
    @Slot(bool, result=bool)
    def toggleTeensyRelay(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleTeensyEnable(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def requestTeensyRelayEnabled(self, _enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def requestTeensyEnabled(self, _enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleWinchEnable(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def requestWinchEnabled(self, _enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleWheelEnable(self, _current_enabled: bool) -> bool:
        return True

    @Slot(result=bool)
    def resetWheelPosition(self) -> bool:
        return True

    @Slot(result=bool)
    def homeTopRail(self) -> bool:
        return True

    @Slot(result=bool)
    def homeArm(self) -> bool:
        return True


class FakeDeviceOperationsHandler(QObject):
    @Slot(bool, result=bool)
    def toggleLoadDetection(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def requestLoadDetectionEnabled(self, _enabled: bool) -> bool:
        return True

    @Slot(result=bool)
    def toggleEndEffectorRecording(self) -> bool:
        return True

    @Slot(result=bool)
    def toggleBaseRecording(self) -> bool:
        return True

    @Slot(result=bool)
    def toggleScreenRecording(self) -> bool:
        return True

    @Slot(result=bool)
    def toggleRosBagRecording(self) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleStability(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleYaw(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleAutoCorrection(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleSprayGunLeveling(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleRollerSteering(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleSwingDamping(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def toggleSprayGunLed(self, _current_enabled: bool) -> bool:
        return True

    @Slot(bool, result=bool)
    def setLidarPower(self, _enabled: bool) -> bool:
        return True

    @Slot(result=bool)
    def clearErrors(self) -> bool:
        return True


class FakeBaseTopViewAdminHandler(QObject):
    @Slot(float, result=bool)
    def requestZoom(self, _value: float) -> bool:
        return True

    @Slot(float, result=bool)
    def requestOffsetX(self, _value: float) -> bool:
        return True

    @Slot(float, result=bool)
    def requestOffsetY(self, _value: float) -> bool:
        return True

    @Slot(bool, result=bool)
    def requestCropEnabled(self, _value: bool) -> bool:
        return True

    @Slot(float, result=bool)
    def requestCropWidthRatio(self, _value: float) -> bool:
        return True

    @Slot(float, result=bool)
    def requestCropCenterX(self, _value: float) -> bool:
        return True

    @Slot(float, result=bool)
    def requestK1(self, _value: float) -> bool:
        return True

    @Slot(float, result=bool)
    def requestK2(self, _value: float) -> bool:
        return True

    @Slot(float, result=bool)
    def requestK3(self, _value: float) -> bool:
        return True

    @Slot(float, result=bool)
    def requestK4(self, _value: float) -> bool:
        return True

    @Slot(result=bool)
    def saveSettings(self) -> bool:
        return True

    @Slot(result=bool)
    def resetToDefaults(self) -> bool:
        return True


class FakeActionLegality(QObject):
    legalityChanged = Signal()

    def __init__(self, legalities: dict[str, dict] | None = None) -> None:
        super().__init__()
        self._legalities = dict(legalities or {})

    @Slot(str, result="QVariantMap")
    def getActionLegality(self, action_key: str):
        return dict(
            self._legalities.get(
                action_key,
                {
                    "actionKey": action_key,
                    "allowed": True,
                    "reason": "",
                    "title": action_key,
                    "legalStateClass": "status-admin",
                    "surfaceKeys": [],
                    "primarySurface": "",
                },
            )
        )


class FakeWorkflowEditor(QObject):
    workflow_list_changed = Signal()

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self):
        return []

    @Slot(str, result=str)
    def get_workflow_data(self, _workflow_name: str) -> str:
        return ""

    @Slot(str, str, result=bool)
    def save_workflow_data(self, _workflow_name: str, _workflow_json: str) -> bool:
        return True


class FakeWorkFlowRunner(QObject):
    workflow_list_changed = Signal()
    execution_state_changed = Signal(int)
    current_workflow_changed = Signal(str)
    current_action_index_changed = Signal(int)
    current_action_details_changed = Signal()
    workflow_actions_changed = Signal()
    loop_iteration_changed = Signal(int)
    loop_enabled_changed = Signal(bool)
    workflow_runtime_changed = Signal(int)
    loaded_workflow_reload_state_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self, execution_state: int = 0) -> None:
        super().__init__()
        self._workflow_list = ["demo"]
        self._current_workflow = "demo"
        self._execution_state = execution_state
        self._current_action_index = 0
        self._workflow_actions = [
            {
                "action_id": "move",
                "index": 0,
                "number": 1,
                "name": "Move Winch",
                "display_name": "1. Move Winch",
                "type": "winch_absolute",
                "description": "Move to 420mm at 35mm/s",
            },
            {
                "action_id": "spray",
                "index": 1,
                "number": 2,
                "name": "Open Valve",
                "display_name": "2. Open Valve",
                "type": "valve_turn",
                "description": "Open valve to 25.0",
            },
        ]

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self):
        return self._workflow_list

    @Property(str, notify=current_workflow_changed)
    def current_workflow(self):
        return self._current_workflow

    @Property(int, notify=execution_state_changed)
    def execution_state(self):
        return self._execution_state

    @Property(int, notify=current_action_index_changed)
    def current_action_index(self):
        return self._current_action_index

    @Property(list, notify=workflow_actions_changed)
    def workflow_actions(self):
        return self._workflow_actions

    @Property(bool, notify=loop_enabled_changed)
    def is_loop_enabled(self):
        return True

    @Property(int, notify=loop_iteration_changed)
    def loop_iteration(self):
        return 2

    @Property(int, notify=workflow_runtime_changed)
    def workflow_runtime(self):
        return 12

    @Property(str, notify=current_action_details_changed)
    def current_action_display(self):
        return self._workflow_actions[self._current_action_index]["display_name"]

    @Property(str, notify=current_action_details_changed)
    def current_action_description(self):
        return self._workflow_actions[self._current_action_index]["description"]

    @Property(str, notify=current_action_details_changed)
    def workflow_progress_text(self):
        return "1 / 2"

    @Slot(str, result=bool)
    def load_workflow(self, workflow_name: str) -> bool:
        self._current_workflow = workflow_name
        self.current_workflow_changed.emit(workflow_name)
        return True

    @Slot(result=list)
    def get_current_workflow_actions(self):
        return self._workflow_actions


class BlankImageProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, image_id, size, requested_size):
        image = QImage(4, 4, QImage.Format_RGB32)
        image.fill(QColor("black"))
        if size is not None:
            size.setWidth(4)
            size.setHeight(4)
        return image


def _qml_import_url(path: Path) -> str:
    return QUrl.fromLocalFile(f"{path}/").toString()


def _assert_component_ready(qtbot, component: QQmlComponent) -> None:
    qtbot.waitUntil(lambda: component.isReady() or component.isError(), timeout=2000)
    assert component.isReady(), [str(error) for error in component.errors()]


def _teensy_all_status() -> DynamicObject:
    return DynamicObject(
        voltage=24.0,
        current=0.0,
        temperature=35.0,
        run_time=0.0,
        loop_time=1000.0,
        loop_time_counter=1.0,
        relay_on=False,
        enabled=True,
        yaw_enabled=False,
        arm_extension_dist=0.0,
        arm_rail_current=0.0,
        gimbal_pitch_motor_current=0.0,
        imu_pitch=0.0,
        imu_roll=0.0,
        imu_yaw=0.0,
        imu_acc_x=0.0,
        imu_acc_y=0.0,
        imu_acc_z=0.0,
        imu_angular_acc_x=0.0,
        imu_angular_acc_y=0.0,
        imu_angular_acc_z=0.0,
    )


def _settings_manager(monkeypatch, tmp_path: Path) -> SettingsManager:
    config_path = tmp_path / "config" / "settings.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)
    return SettingsManager()


def _context_objects(monkeypatch, tmp_path: Path) -> dict[str, QObject]:
    settings_manager = _settings_manager(monkeypatch, tmp_path)
    workflow_runner = FakeWorkFlowRunner()
    workflow_editor = FakeWorkflowEditor()
    manual_command_handler = FakeManualCommandHandler()
    video_runtime = FakeVideoRuntime()
    recording_status = DynamicObject(
        endEffectorRecording=True,
        baseRecording=False,
        screenRecording=True,
        screenRecordingDuration=125,
        screenFreeSpaceGb=8.5,
        rosBagRecording=False,
        rosBagRecordingDuration=0,
        rosBagCompressing=True,
        rosBagStatusMessage="Remote EF ready",
    )
    wheel_status = DynamicObject(
        available=True,
        enabled=True,
        leftMotorAvailable=True,
        rightMotorAvailable=True,
        leftWheelSpeed=0.0,
        rightWheelSpeed=0.0,
        leftWheelCurrent=0.0,
        rightWheelCurrent=0.0,
        leftWheelPosition=0.0,
        rightWheelPosition=0.0,
    )
    winch_status = DynamicObject(
        available=True,
        enabled=True,
        loadDetectionEnabled=False,
        cableLength=0.0,
        cableSpeed=0.0,
        winchTorque=0.0,
        motorTemperature=25.0,
        motorVoltage=24.0,
        motorBrake=True,
        unusualLoadDetected=False,
    )
    teensy_status = DynamicObject(
        enabled=True,
        relayOn=False,
        voltage=24.0,
        current=1.2,
        temperature=32.0,
        runTime=120.0,
        loopTime=450.0,
        loopTimeCounter=900.0,
        imuPitch=0.0,
        imuRoll=0.0,
        imuYaw=0.0,
        imuAccX=0.0,
        imuAccY=0.0,
        imuAccZ=0.0,
        imuAngularAccX=0.0,
        imuAngularAccY=0.0,
        imuAngularAccZ=0.0,
        armExtensionDist=0.0,
        armRailCurrent=0.0,
        gimbalPitchMotorCurrent=0.0,
        gimbalPitchMotorAngle=0.0,
        stabilityEnabled=True,
        yawEnabled=False,
        autoCorrectionEnabled=False,
        sprayGunLevelingEnabled=True,
        rollerSteeringEnabled=False,
        swingDampingEnabled=True,
        sprayGunLedOn=False,
    )
    valve_status = DynamicObject(
        valvePosition=0.0,
        valveRate=0.0,
        totalVolume=0.0,
        valveMotorCurrent=0.0,
        valveMotorConnected=False,
        flowMeterConnected=False,
        connected=False,
    )
    lidar_status = FakeLidarStatus(distance=0.0, angle=0.0)
    shell_connectivity_status = DynamicObject(
        winchAvailable=True,
        wheelAvailable=True,
        endEffectorAvailable=True,
        baseOnline=True,
        baseStatus=0x00,
        endEffectorOnline=True,
        endEffectorStatus=0x00,
        baseIpAddress="10.0.0.2",
        endEffectorIpAddress="10.0.0.3",
    )

    return {
        "stateStore": StateStore(),
        "backend": FakeBackend(),
        "shellState": DynamicObject(
            screen_count=1,
            main_surface_screen_index=0,
            secondary_surface_screen_index=0,
            secondary_surface_active=False,
            secondary_surface_fullscreen=False,
            show_system_control_on_main_surface=True,
            show_system_control_on_secondary_surface=False,
            video_fullscreen_on_main_surface=True,
        ),
        "overlayHost": DynamicObject(
            system_control_on_main_surface=True,
            system_control_on_secondary_surface=False,
            joystick_overlay_on_main_surface=True,
            joystick_overlay_on_secondary_surface=False,
            video_fullscreen_on_main_surface=True,
            video_fullscreen_on_secondary_surface=False,
            emergency_overlay_on_main_surface=True,
            emergency_overlay_on_secondary_surface=False,
            system_control_layer=1001,
            joystick_overlay_layer=1000,
            video_fullscreen_layer=500,
            emergency_overlay_layer=3000,
            video_fullscreen_active=False,
            video_fullscreen_source="",
        ),
        "overlayController": DynamicObject(
            show_overlay=False,
            left_selected_index=0,
            right_selected_index=0,
            active_menu="",
            control_options=[],
        ),
        "actionLegality": FakeActionLegality(),
        "systemControlServices": FakeSystemControlServices(
            workflow_runner=workflow_runner,
            workflow_editor=workflow_editor,
            manual_command_handler=manual_command_handler,
        ),
        "videoRuntime": video_runtime,
        "recordingStatus": recording_status,
        "wheelStatus": wheel_status,
        "winchStatus": winch_status,
        "teensyStatus": teensy_status,
        "valveStatus": valve_status,
        "lidarStatus": lidar_status,
        "shellConnectivityStatus": shell_connectivity_status,
        "warningHandler": DynamicObject(active_warning=""),
        "baseStreamHandler": FakeStreamHandler(),
        "wheelController": DynamicObject(
            available=True,
            enabled=True,
            left_motor_available=True,
            right_motor_available=True,
            left_wheel_speed=0.0,
            right_wheel_speed=0.0,
            left_wheel_current=0.0,
            right_wheel_current=0.0,
        ),
        "winchController": DynamicObject(
            available=True,
            enabled=True,
            load_detection_enabled=False,
            cable_length=0.0,
            cable_speed=0.0,
            motor_voltage=24.0,
            motor_temperature=25.0,
            winch_torque=0.0,
        ),
        "steamDeckHandler": DynamicObject(),
        "windMonitor": DynamicObject(speed=0.0, direction=0.0),
        "teensyController": DynamicObject(
            available=True,
            all_status=_teensy_all_status(),
            stability_enabled=False,
            auto_correction_enabled=False,
            spray_gun_leveling_enabled=False,
            roller_steering_enabled=False,
            swing_damping_enabled=False,
            spray_gun_led_on=False,
        ),
        "esp32ValveController": DynamicObject(
            valve_position=0.0,
            valve_rate=0.0,
            valve_motor_current=0.0,
            total_volume=0.0,
            valve_motor_connected=False,
            flow_meter_connected=False,
        ),
        "lidarController": FakeLidarController(distance=0.0, angle=0.0),
        "heartbeatHandler": DynamicObject(
            controller_online=True,
            controller_status=0x01,
            base_online=True,
            base_status=0x00,
            ef_online=True,
            ef_status=0x00,
        ),
        "controlProcessor": DynamicObject(
            left_control_mode="None",
            left_control_value="",
            right_control_mode="None",
            right_control_value="",
        ),
        "deviceActionHandler": FakeDeviceActionHandler(),
        "deviceOperationsHandler": FakeDeviceOperationsHandler(),
        "launcherAdmin": FakeLauncherAdmin(),
        "systemMonitor": DynamicObject(
            battery_level=100,
            battery_percentage=100,
            battery_remaining_time="--",
            battery_time_remaining="--",
            cpu_temperature=0.0,
        ),
        "screenRecorder": DynamicObject(
            isRecording=False,
            is_recording=False,
            recording_duration=0,
            free_space_gb=10.0,
        ),
        "rosBagRecorder": DynamicObject(
            isRecording=False,
            is_recording=False,
            is_compressing=False,
            is_bag_recording=False,
            bag_recording_duration=0,
            bag_status_message="",
        ),
        "settingsManager": settings_manager,
        "baseTopViewAdminHandler": FakeBaseTopViewAdminHandler(),
        "screenManager": FakeScreenManager(),
        "baseTopViewController": FakeBaseTopViewController(),
    }