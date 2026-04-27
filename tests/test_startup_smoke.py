"""Headless startup smoke tests for the QML shell and safety runtime wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtCore import Property, QCoreApplication, QEvent, QObject, QSize, Signal, Slot, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickImageProvider

from paint_controller.core.application import _teardown_qml_runtime
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
    def __init__(self) -> None:
        super().__init__()
        self._end_effector_ping_ms = 38.0
        self._base_ping_ms = 42.0
        self._end_effector_battery_voltage = 24.0
        self._base_battery_voltage = 24.0
        self._is_recording = False
        self._recording_duration = 0
        self._system_battery_percent = 100
        self._cpu_temperature = 0.0
        self._battery_remaining_time = "--"

    @Property(float, constant=True)
    def endEffectorPingMs(self) -> float:
        return self._end_effector_ping_ms

    @Property(float, constant=True)
    def basePingMs(self) -> float:
        return self._base_ping_ms

    @Property(float, constant=True)
    def endEffectorBatteryVoltage(self) -> float:
        return self._end_effector_battery_voltage

    @Property(float, constant=True)
    def baseBatteryVoltage(self) -> float:
        return self._base_battery_voltage

    @Property(bool, constant=True)
    def isRecording(self) -> bool:
        return self._is_recording

    @Property(int, constant=True)
    def recordingDuration(self) -> int:
        return self._recording_duration

    @Property(int, constant=True)
    def systemBatteryPercent(self) -> int:
        return self._system_battery_percent

    @Property(float, constant=True)
    def cpuTemperature(self) -> float:
        return self._cpu_temperature

    @Property(str, constant=True)
    def batteryRemainingTime(self) -> str:
        return self._battery_remaining_time


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
    availability = DynamicObject(BASE=True, EF=True)
    ping_times = DynamicObject(BASE="42", END_EFFECTOR="38")
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
        stabilityEnabled=True,
        yawEnabled=False,
        autoCorrectionEnabled=False,
        sprayGunLevelingEnabled=True,
        rollerSteeringEnabled=False,
        swingDampingEnabled=True,
        sprayGunLedOn=False,
    )
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


def test_main_window_loads_offscreen_with_context_properties(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "core" / "MainWindow.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MainWindow.qml failed to load"
    for name in context_objects:
        assert ctx.contextProperty(name) is not None

    fatal_warning_fragments = (
        "failed to load component",
        "no such file or directory",
        "is not a type",
        "manualcommandhandler' of undefined",
        "workflowrunner' of undefined",
        "workfloweditor' of undefined",
        "cannot read property 'controls' of undefined",
        "cannot read property 'feeds' of undefined",
        "cannot read property 'topbar' of undefined",
        "referenceerror: workflowrunner is not defined",
        "detected function \"onendeffectorframeready\"",
        "detected function \"onbasefrontframeready\"",
        "detected function \"onbaserearframeready\"",
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


def test_main_window_navigation_updates_selected_page_key(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    core_import_url = _qml_import_url(qml_dir / "core")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{core_import_url}"

MainWindow {{
    id: rootWindow
    objectName: "mainWindowHarness"
    property bool routeScenarioComplete: false

    Timer {{
        interval: 0
        running: true
        repeat: false
        onTriggered: {{
            rootWindow.navigateToPage("settings")
            rootWindow.routeScenarioComplete = true
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:MainWindowRouteHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        qtbot.waitUntil(lambda: root.property("routeScenarioComplete") is True, timeout=2000)
        qt_app.processEvents()

        stack_view = root.findChild(QObject, "stackView")
        assert stack_view is not None
        assert root.property("selectedPageKey") == "settings"
        assert stack_view.property("currentIndex") == 6
        assert stack_view.property("targetIndex") == 6

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_main_window_invalid_navigation_keeps_previous_route(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    core_import_url = _qml_import_url(qml_dir / "core")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{core_import_url}"

MainWindow {{
    id: rootWindow
    objectName: "mainWindowInvalidRouteHarness"
    property bool routeScenarioComplete: false

    Timer {{
        interval: 0
        running: true
        repeat: false
        onTriggered: {{
            rootWindow.navigateToPage("settings")
            rootWindow.navigateToPage("missing")
            rootWindow.routeScenarioComplete = true
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:MainWindowInvalidRouteHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        qtbot.waitUntil(lambda: root.property("routeScenarioComplete") is True, timeout=2000)
        qt_app.processEvents()

        stack_view = root.findChild(QObject, "stackView")
        assert stack_view is not None
        assert root.property("selectedPageKey") == "settings"
        assert stack_view.property("currentIndex") == 6
        assert stack_view.property("targetIndex") == 6
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_main_window_teardown_does_not_emit_null_binding_warnings(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "core" / "MainWindow.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MainWindow.qml failed to load before teardown"

    warning_count_before_teardown = len(warnings)

    _teardown_qml_runtime(engine, qt_app, lambda _stage: None)

    for _ in range(5):
        qt_app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        qt_app.processEvents()

    teardown_warnings = warnings[warning_count_before_teardown:]
    null_binding_fragment = "cannot read property"
    undefined_assignment_fragment = "unable to assign [undefined]"
    assert not any(
        null_binding_fragment in warning.lower() or undefined_assignment_fragment in warning.lower()
        for warning in teardown_warnings
    ), teardown_warnings


def test_multi_screen_monitor_window_loads_offscreen(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "overlays" / "MultiScreenListUI.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MultiScreenListUI.qml failed to load"

    fatal_warning_fragments = (
        "failed to load component",
        "no such file or directory",
        "is not a type",
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


def test_multi_screen_monitor_window_consumes_overlay_host_matrix(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "overlays" / "MultiScreenListUI.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())

    context_objects = _context_objects(monkeypatch, tmp_path)
    context_objects["overlayHost"] = DynamicObject(
        system_control_on_main_surface=False,
        system_control_on_secondary_surface=True,
        joystick_overlay_on_main_surface=False,
        joystick_overlay_on_secondary_surface=True,
        video_fullscreen_on_main_surface=True,
        video_fullscreen_on_secondary_surface=False,
        emergency_overlay_on_main_surface=True,
        emergency_overlay_on_secondary_surface=True,
        system_control_layer=1001,
        joystick_overlay_layer=1000,
        video_fullscreen_layer=500,
        emergency_overlay_layer=3000,
        video_fullscreen_active=True,
        video_fullscreen_source="image://base_front_live/frame",
    )

    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MultiScreenListUI.qml failed to load with overlay host matrix"

    root = engine.rootObjects()[0]
    assert root.findChild(QObject, "systemControlMenuSecondary").property("visible") is True
    assert root.findChild(QObject, "joystickOverlaySecondary").property("visible") is True
    assert root.findChild(QObject, "emergencyOverlaySecondary").property("visible") is True
    assert root.findChild(QObject, "videoFullscreenOverlaySecondary").property("active") is False


def test_settings_route_loads_offscreen(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "pages" / "settings" / "PageSettings.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "PageSettings.qml failed to load"

    fatal_warning_fragments = (
        "failed to load component",
        "no such file or directory",
        "is not a type",
        "required property",
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


def test_system_control_workspace_loads_with_required_properties(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    systemcontrol_import_url = _qml_import_url(qml_dir / "features" / "systemcontrol")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{systemcontrol_import_url}"

Item {{
    width: 1280
    height: 800
    property var servicesModel: systemControlServices
    property var recordingStatusModel: recordingStatus
    property var wheelStatusModel: wheelStatus
    property var winchStatusModel: winchStatus
    property var teensyStatusModel: teensyStatus

    SystemControlWorkspace {{
        anchors.fill: parent
        showOverlay: true
        activeMenu: "system"
        systemControlServices: servicesModel
        recordingStatus: recordingStatusModel
        wheelStatus: wheelStatusModel
        winchStatus: winchStatusModel
        teensyStatus: teensyStatusModel
    }}
}}
'''.encode(),
        QUrl("inmemory:SystemControlWorkspaceHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


@pytest.mark.parametrize("video_source", ["image://ef_live/frame", "image://base_front_live/frame"])
def test_video_fullscreen_workspace_loads_with_stream_context(monkeypatch, tmp_path, qt_app, qtbot, video_source):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    video_import_url = _qml_import_url(qml_dir / "features" / "video")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{video_import_url}"

Item {{
    width: 1280
    height: 800
    property var videoRuntimeModel: videoRuntime

    VideoFullscreenWorkspace {{
        anchors.fill: parent
        active: true
        videoSource: "{video_source}"
        workflowServices: systemControlServices
        videoRuntime: videoRuntimeModel
    }}
}}
'''.encode(),
        QUrl("inmemory:VideoFullscreenWorkspaceHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        if video_source == "image://ef_live/frame":
            fatal_warning_fragments += (
                "endeffectoroverlay.qml: qml row: cannot specify",
                "videooverlaytopbar.qml: qml row: cannot specify",
                "walldetectionoverlay.qml: qml connections",
                "cannot read property 'imu_pitch' of undefined",
                "cannot call method 'tofixed' of undefined",
            )
        if video_source == "image://base_front_live/frame":
            fatal_warning_fragments += (
                "basefrontoverlay.qml: qml row: cannot specify",
                "basefrontoverlay.qml: qml connections",
                "basetopviewsettingspopup.qml: unable to assign [undefined]",
                "cannot call method 'tofixed' of undefined",
                "invalid image provider: image://base_top_view/frame",
            )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_page_winch_loads_with_explicit_winch_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    winch_import_url = _qml_import_url(qml_dir / "pages" / "winch")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{winch_import_url}"

Item {{
    width: 1280
    height: 800
    property var winchStatusModel: winchStatus

    PageWinch {{
        anchors.fill: parent
        winchStatus: winchStatusModel
    }}
}}
'''.encode(),
        QUrl("inmemory:PageWinchHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_page_status_loads_with_explicit_winch_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    status_import_url = _qml_import_url(qml_dir / "pages" / "status")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{status_import_url}"

Item {{
    width: 1280
    height: 800
    property var winchStatusModel: winchStatus
    property var teensyStatusModel: teensyStatus
    property var wheelStatusModel: wheelStatus

    PageStatus {{
        anchors.fill: parent
        wheelStatus: wheelStatusModel
        winchStatus: winchStatusModel
        teensyStatus: teensyStatusModel
    }}
}}
'''.encode(),
        QUrl("inmemory:PageStatusHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_video_fullscreen_overlay_wrapper_loads_with_stream_context(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    overlay_import_url = _qml_import_url(qml_dir / "overlays" / "video")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{overlay_import_url}"

Item {{
    width: 1280
    height: 800

    VideoFullscreenOverlay {{
        anchors.fill: parent
        active: true
        videoSource: "image://base_front_live/frame"
        workflowServices: systemControlServices
        videoRuntime: videoRuntime
    }}
}}
'''.encode(),
        QUrl("inmemory:VideoFullscreenOverlayHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_workflow_tab_loads_with_runner_read_model(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    systemcontrol_import_url = _qml_import_url(qml_dir / "overlays" / "systemcontrol")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{systemcontrol_import_url}"

Item {{
    width: 1280
    height: 800

    WorkFlowTab {{
        anchors.fill: parent
        workflowRunner: systemControlServices.workflowRunner
    }}
}}
'''.encode(),
        QUrl("inmemory:WorkFlowTabHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()
        assert not any("failed to load component" in warning.lower() for warning in warnings), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_command_tab_loads_with_explicit_handler(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    systemcontrol_import_url = _qml_import_url(qml_dir / "overlays" / "systemcontrol")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{systemcontrol_import_url}"

Item {{
    width: 1280
    height: 800

    CommandTab {{
        anchors.fill: parent
        manualCommandHandler: systemControlServices.manualCommandHandler
    }}
}}
'''.encode(),
        QUrl("inmemory:CommandTabHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()
        assert not any("failed to load component" in warning.lower() for warning in warnings), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_workflow_status_overlay_loads_with_runner_read_model(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    overlay_import_url = _qml_import_url(qml_dir / "overlays" / "video" / "components")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    context_objects["systemControlServices"] = DynamicObject(
        workflowRunner=FakeWorkFlowRunner(execution_state=1),
        workflowEditor=FakeWorkflowEditor(),
    )
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{overlay_import_url}"

Item {{
    width: 1280
    height: 800

    WorkFlowStatusOverlay {{
        anchors.fill: parent
        workflowRunner: systemControlServices.workflowRunner
    }}
}}
'''.encode(),
        QUrl("inmemory:WorkFlowStatusOverlayHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()
        assert not any("failed to load component" in warning.lower() for warning in warnings), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_device_control_tab_consumes_action_legality_affordance(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    systemcontrol_import_url = _qml_import_url(qml_dir / "overlays" / "systemcontrol")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    context_objects["actionLegality"] = FakeActionLegality(
        {
            "status.winch_enable": {
                "actionKey": "status.winch_enable",
                "allowed": False,
                "reason": "Winch enable requires the controller heartbeat to be idle",
                "title": "Winch Enable Toggle",
                "legalStateClass": "status-admin",
            },
            "wheel.reset_position": {
                "actionKey": "wheel.reset_position",
                "allowed": False,
                "reason": "Reset Wheel Position requires the system to be idle",
                "title": "Reset Wheel Position",
                "legalStateClass": "maintenance-preset",
            },
        }
    )

    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{systemcontrol_import_url}"

Item {{
    width: 1280
    height: 800
    property var recordingStatusModel: ({{
        endEffectorRecording: true,
        baseRecording: false,
        screenRecording: true,
        screenRecordingDuration: 125,
        screenFreeSpaceGb: 8.5,
        rosBagRecording: false,
        rosBagRecordingDuration: 0,
        rosBagCompressing: true,
        rosBagStatusMessage: "Remote EF ready"
    }})
    property var wheelStatusModel: ({{
        available: true,
        enabled: true,
        leftMotorAvailable: true,
        rightMotorAvailable: true,
        leftWheelSpeed: 0,
        rightWheelSpeed: 0,
        leftWheelCurrent: 0,
        rightWheelCurrent: 0,
        leftWheelPosition: 0,
        rightWheelPosition: 0
    }})
    property var winchStatusModel: ({{
        available: true,
        enabled: true,
        loadDetectionEnabled: false,
        cableLength: 0,
        cableSpeed: 0,
        winchTorque: 0,
        motorTemperature: 25,
        motorVoltage: 24,
        motorBrake: true,
        unusualLoadDetected: false
    }})
    property var teensyStatusModel: ({{
        enabled: true,
        relayOn: false,
        voltage: 24,
        current: 1.2,
        temperature: 32,
        runTime: 120,
        loopTime: 450,
        loopTimeCounter: 900,
        stabilityEnabled: true,
        yawEnabled: false,
        autoCorrectionEnabled: false,
        sprayGunLevelingEnabled: true,
        rollerSteeringEnabled: false,
        swingDampingEnabled: true,
        sprayGunLedOn: false
    }})

    DeviceControlTab {{
        anchors.fill: parent
        recordingStatus: recordingStatusModel
        wheelStatus: wheelStatusModel
        winchStatus: winchStatusModel
        teensyStatus: teensyStatusModel
    }}
}}
'''.encode(),
        QUrl("inmemory:DeviceControlTabHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        winch_enable = root.findChild(QObject, "winchEnableControl")
        wheel_reset = root.findChild(QObject, "wheelResetAction")
        ef_recording = root.findChild(QObject, "efRecordingControl")
        screen_recording = root.findChild(QObject, "screenRecordingControl")
        rosbag_recording = root.findChild(QObject, "rosBagRecordingControl")
        stability_control = root.findChild(QObject, "stabilityControl")
        yaw_control = root.findChild(QObject, "yawControl")
        spray_gun_led_control = root.findChild(QObject, "sprayGunLedControl")
        assert winch_enable is not None
        assert wheel_reset is not None
        assert ef_recording is not None
        assert screen_recording is not None
        assert rosbag_recording is not None
        assert stability_control is not None
        assert yaw_control is not None
        assert spray_gun_led_control is not None
        assert winch_enable.property("actionAllowed") is False
        assert winch_enable.property("blockedReason") == "Winch enable requires the controller heartbeat to be idle"
        assert wheel_reset.property("actionAllowed") is False
        assert wheel_reset.property("blockedReason") == "Reset Wheel Position requires the system to be idle"
        assert ef_recording.property("controlStatus") == "Recording"
        assert screen_recording.property("controlStatus") == "Recording 2:05 (8.5 GB free)"
        assert rosbag_recording.property("controlStatus") == "Compressing..."
        assert rosbag_recording.property("enabled") is False
        assert stability_control.property("controlStatus") == "Active"
        assert yaw_control.property("controlStatus") == "Inactive"
        assert spray_gun_led_control.property("controlStatus") == "Off"

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_base_top_view_settings_popup_disables_blocked_actions(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    video_components_import_url = _qml_import_url(qml_dir / "overlays" / "video" / "components")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    context_objects["actionLegality"] = FakeActionLegality(
        {
            "camera.base_top_view.live_adjustments": {
                "actionKey": "camera.base_top_view.live_adjustments",
                "allowed": False,
                "reason": "Base top view live adjustments require the controller heartbeat to be idle",
                "title": "Base Top View Live Adjustments",
                "legalStateClass": "overlay-primary-calibration",
            },
            "camera.base_top_view.save": {
                "actionKey": "camera.base_top_view.save",
                "allowed": False,
                "reason": "Base top view save requires the controller heartbeat to be idle",
                "title": "Base Top View Save",
                "legalStateClass": "overlay-primary-calibration",
            },
            "camera.base_top_view.reset": {
                "actionKey": "camera.base_top_view.reset",
                "allowed": False,
                "reason": "Base top view reset requires the controller heartbeat to be idle",
                "title": "Base Top View Reset",
                "legalStateClass": "overlay-primary-calibration",
            },
        }
    )

    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import QtQuick.Controls
import "{video_components_import_url}"

ApplicationWindow {{
    width: 1280
    height: 800
    visible: false

    BaseTopViewSettingsPopup {{
        visible: true
    }}
}}
'''.encode(),
        QUrl("inmemory:BaseTopViewSettingsPopupHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        zoom_slider = root.findChild(QObject, "zoomSlider")
        warning_banner = root.findChild(QObject, "baseTopViewLegalityBanner")
        action_reason = root.findChild(QObject, "baseTopViewActionReason")
        save_button = root.findChild(QObject, "saveSettingsButton")
        reset_button = root.findChild(QObject, "resetDefaultsButton")

        assert zoom_slider is not None
        assert warning_banner is not None
        assert action_reason is not None
        assert save_button is not None
        assert reset_button is not None
        assert zoom_slider.property("enabled") is False
        assert warning_banner.property("visible") is True
        assert action_reason.property("text") == "Base top view save requires the controller heartbeat to be idle"
        assert save_button.property("enabled") is False
        assert reset_button.property("enabled") is False

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_select_bar_navigates_via_explicit_page_registry(qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    core_import_url = _qml_import_url(qml_dir / "core")
    navigation_import_url = _qml_import_url(qml_dir / "navigation")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import QtQuick.Controls
import "{core_import_url}"
import "{navigation_import_url}"

Item {{
    id: harnessRoot
    width: 1280
    height: 800
    property string selectedPageKey: "home"
    property var shellConnectivityStatusModel: ({{
        winchAvailable: true,
        wheelAvailable: true,
        endEffectorAvailable: false,
        baseOnline: true,
        baseStatus: 0,
        endEffectorOnline: false,
        endEffectorStatus: 2,
        baseIpAddress: "10.0.0.2",
        endEffectorIpAddress: "10.0.0.3"
    }})

    property var pageRegistry: [
        {{ routeOrder: 0, buttonKey: "home", buttonText: "Home", component: homeComponent }},
        {{ routeOrder: 1, buttonKey: "settings", buttonText: "Settings", component: settingsComponent }}
    ]

    function getPageConfig(pageKey) {{
        for (var i = 0; i < pageRegistry.length; i++) {{
            if (pageRegistry[i].buttonKey === pageKey) {{
                return pageRegistry[i]
            }}
        }}
        return null
    }}

    QtObject {{
        id: fakeStackView
        objectName: "fakeStackView"
        property int currentIndex: 0
        property int targetIndex: 0
        property var currentItem: null
        property var lastComponent: null

        function replace(currentItemArg, targetComponentArg) {{
            currentItem = currentItemArg
            lastComponent = targetComponentArg
        }}
    }}

    Component {{
        id: homeComponent
        Item {{ objectName: "homePage" }}
    }}

    Component {{
        id: settingsComponent
        Item {{ objectName: "settingsPage" }}
    }}

    SelectBar {{
        id: selectBar
        objectName: "selectBar"
        pageRegistry: harnessRoot.pageRegistry
        selectedPageKey: harnessRoot.selectedPageKey
        shellConnectivityStatus: harnessRoot.shellConnectivityStatusModel
        onNavigateRequested: function(pageKey) {{
            var targetPage = harnessRoot.getPageConfig(pageKey)
            if (!targetPage) {{
                return
            }}

            harnessRoot.selectedPageKey = targetPage.buttonKey
            fakeStackView.targetIndex = targetPage.routeOrder
            fakeStackView.replace(fakeStackView.currentItem, targetPage.component)
            fakeStackView.currentIndex = targetPage.routeOrder
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:SelectBarHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        select_bar = root.findChild(QObject, "selectBar")
        assert select_bar is not None

        connection_status_panel = root.findChild(QObject, "connectionStatusPanel")
        assert connection_status_panel is not None

        fake_stack_view = root.findChild(QObject, "fakeStackView")
        assert fake_stack_view is not None
        assert select_bar.property("navigationCount") == 2
        assert connection_status_panel.property("baseIpAddress") == "10.0.0.2"
        assert connection_status_panel.property("efIpAddress") == "10.0.0.3"

        select_bar.navigateToPage("settings")
        qt_app.processEvents()

        assert fake_stack_view.property("currentIndex") == 1
        assert fake_stack_view.property("targetIndex") == 1
        assert select_bar.property("selectedPageKey") == "settings"
        assert fake_stack_view.property("lastComponent") is not None

        select_bar.navigateToPage("missing")
        qt_app.processEvents()

        assert fake_stack_view.property("currentIndex") == 1
        assert select_bar.property("selectedPageKey") == "settings"
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_page_launcher_loads_with_shell_connectivity_status(qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    home_import_url = _qml_import_url(qml_dir / "pages" / "home")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.rootContext().setContextProperty("launcherAdmin", FakeLauncherAdmin())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{home_import_url}"

Item {{
    width: 1280
    height: 800
    property var shellConnectivityStatusModel: ({{
        baseReachable: true,
        endEffectorReachable: false
    }})
    property var launcherAdminModel: launcherAdmin

    PageLauncher {{
        objectName: "pageLauncher"
        anchors.fill: parent
        shellConnectivityStatus: parent.shellConnectivityStatusModel
        launcherAdmin: parent.launcherAdminModel
    }}
}}
'''.encode(),
        QUrl("inmemory:PageLauncherHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        assert root.findChild(QObject, "pageLauncher") is not None

        qt_app.processEvents()

        fatal_warning_fragments = (
            "required property",
            "cannot read property",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()