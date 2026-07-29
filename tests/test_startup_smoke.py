"""Headless startup smoke tests for QML feature and page surfaces."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from tests.startup_smoke_support import (
    BlankImageProvider,
    DynamicObject,
    FakeActionLegality,
    FakeWorkflowEditor,
    FakeWorkFlowRunner,
    _assert_component_ready,
    _context_objects,
    _qml_import_url,
)


def test_settings_route_loads_offscreen(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    settings_import_url = _qml_import_url(qml_dir / "pages" / "settings")

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
import "{settings_import_url}"

Item {{
    width: 1280
    height: 800
    property var injectedSettings: settingsManager
    property var injectedBridge: qtBridge

    PageSettings {{
        anchors.fill: parent
        settingsManager: parent.injectedSettings
        qtBridge: parent.injectedBridge
    }}
}}
'''.encode(),
        QUrl("inmemory:PageSettingsHarness.qml"),
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
        assert not any(
            fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments
        ), (warnings)
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


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
        wheelActions: wheelActions
        winchActions: winchActions
        teensyActions: teensyActions
        recordingActions: recordingActions
        systemActions: systemActions
        actionLegality: actionLegality
        settingsManager: settingsManager
        overlayController: overlayController
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
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
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
        wheelStatus: wheelStatus
        winchStatus: winchStatus
        teensyStatus: teensyStatus
        valveStatus: valveStatus
        lidarStatus: lidarStatus
        overlayController: overlayController
        baseTopViewStatus: baseTopViewStatus
        baseTopViewActions: baseTopViewActions
        actionLegality: actionLegality
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
                "cannot read property 'imu_pitch' of undefined",
                "cannot call method 'tofixed' of undefined",
                "cannot read property 'winch_torque'",
                "cannot read property 'cable_length'",
                "cannot read property 'distance'",
                "cannot read property 'angle'",
            )
        if video_source == "image://base_front_live/frame":
            fatal_warning_fragments += (
                "basefrontoverlay.qml: qml row: cannot specify",
                "basefrontoverlay.qml: qml connections",
                "basetopviewsettingspopup.qml: unable to assign [undefined]",
                "cannot call method 'tofixed' of undefined",
                "cannot read property 'left_wheel_speed'",
                "cannot read property 'right_wheel_speed'",
                "invalid image provider: image://base_top_view/frame",
            )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
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

    PageWinch {{
        anchors.fill: parent
        winchStatus: winchStatusModel
        winchActions: winchActions
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
            "typeerror",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_page_wheel_loads_with_explicit_wheel_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    wheel_import_url = _qml_import_url(qml_dir / "pages" / "wheel")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("base_front_live", BlankImageProvider())

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
import "{wheel_import_url}"

Item {{
    id: harnessRoot
    width: 1280
    height: 800
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
    // Capture context-bag fakes before required-property name shadowing
    property var injectedWheelActions: wheelActions
    property var injectedVideoRuntime: videoRuntime

    // TD-048: constructor inject status + command + video (root bag still registered)
    PageWheel {{
        anchors.fill: parent
        wheelStatus: harnessRoot.wheelStatusModel
        wheelActions: harnessRoot.injectedWheelActions
        videoRuntime: harnessRoot.injectedVideoRuntime
    }}
}}
'''.encode(),
        QUrl("inmemory:PageWheelHarness.qml"),
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
            "typeerror",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
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
        winchActions: winchActions
        teensyActions: teensyActions
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
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_winch_card_loads_with_explicit_winch_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    status_components_import_url = _qml_import_url(qml_dir / "pages" / "status" / "components")

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
import "{status_components_import_url}"

Item {{
    width: 1280
    height: 800
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

    WinchCard {{
        anchors.fill: parent
        winchStatus: winchStatusModel
        maxWinchCurrent: 10
    }}
}}
'''.encode(),
        QUrl("inmemory:WinchCardHarness.qml"),
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
            "typeerror",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_imu_card_loads_with_explicit_teensy_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    status_components_import_url = _qml_import_url(qml_dir / "pages" / "status" / "components")

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
import "{status_components_import_url}"

Item {{
    width: 1280
    height: 800
    property var teensyStatusModel: ({{
        imuPitch: 1.5,
        imuRoll: -0.5,
        imuYaw: 2.0,
        imuAccX: 0.01,
        imuAccY: 0.02,
        imuAccZ: 0.03,
        imuAngularAccX: 0.11,
        imuAngularAccY: 0.12,
        imuAngularAccZ: 0.13
    }})

    IMUCard {{
        anchors.fill: parent
        teensyStatus: teensyStatusModel
    }}
}}
'''.encode(),
        QUrl("inmemory:IMUCardHarness.qml"),
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
            "typeerror",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_teensy_arm_card_loads_with_explicit_teensy_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    status_components_import_url = _qml_import_url(qml_dir / "pages" / "status" / "components")

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
import "{status_components_import_url}"

Item {{
    width: 1280
    height: 800
    property var teensyStatusModel: ({{
        armExtensionDist: 320,
        armRailCurrent: 90,
        gimbalPitchMotorCurrent: 50
    }})

    TeensyArmCard {{
        anchors.fill: parent
        teensyStatus: teensyStatusModel
        maxArmCurrent: 200
        maxArmExtension: 1500
    }}
}}
'''.encode(),
        QUrl("inmemory:TeensyArmCardHarness.qml"),
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
            "typeerror",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_valves_card_loads_with_explicit_valve_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    status_components_import_url = _qml_import_url(qml_dir / "pages" / "status" / "components")

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
import "{status_components_import_url}"

Item {{
    width: 1280
    height: 800
    property var valveStatusModel: ({{
        valvePosition: 42,
        valveRate: 1.5,
        totalVolume: 8.0,
        valveMotorCurrent: 0.7,
        valveMotorConnected: true,
        flowMeterConnected: true
    }})

    ValvesCard {{
        anchors.fill: parent
        valveStatus: valveStatusModel
    }}
}}
'''.encode(),
        QUrl("inmemory:ValvesCardHarness.qml"),
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
            "typeerror",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
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
        wheelStatus: wheelStatus
        winchStatus: winchStatus
        teensyStatus: teensyStatus
        valveStatus: valveStatus
        lidarStatus: lidarStatus
        overlayController: overlayController
        baseTopViewStatus: baseTopViewStatus
        baseTopViewActions: baseTopViewActions
        actionLegality: actionLegality
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
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_base_front_overlay_loads_with_explicit_wheel_status(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    overlay_components_import_url = _qml_import_url(qml_dir / "overlays" / "video" / "components")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
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
import "{overlay_components_import_url}"

Item {{
    width: 1280
    height: 800
    property var workflowRunnerModel: systemControlServices.workflowRunner
    property var videoRuntimeModel: videoRuntime
    property var wheelStatusModel: ({{
        leftWheelSpeed: 1.5,
        rightWheelSpeed: -1.0,
        leftWheelCurrent: 0.7,
        rightWheelCurrent: 0.8,
        leftWheelPosition: 120,
        rightWheelPosition: 118
    }})

    BaseFrontOverlay {{
        anchors.fill: parent
        workflowRunner: workflowRunnerModel
        videoRuntime: videoRuntimeModel
        wheelStatus: wheelStatusModel
        baseTopViewStatus: baseTopViewStatus
        baseTopViewActions: baseTopViewActions
        actionLegality: actionLegality
    }}
}}
'''.encode(),
        QUrl("inmemory:BaseFrontOverlayHarness.qml"),
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
            "cannot read property 'left_wheel_speed'",
            "cannot read property 'left_wheel_current'",
            "cannot read property 'left_wheel_position'",
            "cannot read property 'right_wheel_speed'",
            "cannot read property 'right_wheel_current'",
            "cannot read property 'right_wheel_position'",
            "cannot call method 'tofixed' of undefined",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_end_effector_overlay_loads_with_explicit_status_models(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    overlay_components_import_url = _qml_import_url(qml_dir / "overlays" / "video" / "components")

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
import "{overlay_components_import_url}"

Item {{
    width: 1280
    height: 800
    property var workflowRunnerModel: systemControlServices.workflowRunner
    property var videoRuntimeModel: videoRuntime
    property var winchStatusModel: ({{
        winchTorque: 125,
        cableLength: 2400
    }})
    property var lidarStatusModel: lidarStatus
    property var teensyStatusModel: ({{
        imuPitch: 1.2,
        armExtensionDist: 280,
        gimbalPitchMotorAngle: -4.5
    }})
    property var valveStatusModel: ({{
        valvePosition: 23,
        valveRate: 1.1,
        totalVolume: 5.5,
        valveMotorConnected: true,
        flowMeterConnected: false
    }})

    EndEffectorOverlay {{
        anchors.fill: parent
        workflowRunner: workflowRunnerModel
        videoRuntime: videoRuntimeModel
        winchStatus: winchStatusModel
        teensyStatus: teensyStatusModel
        valveStatus: valveStatusModel
        lidarStatus: lidarStatusModel
    }}
}}
'''.encode(),
        QUrl("inmemory:EndEffectorOverlayHarness.qml"),
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
            "cannot read property 'imu_pitch' of undefined",
            "cannot read property 'valve_position' of undefined",
            "cannot read property 'winch_torque' of undefined",
            "cannot read property 'cable_length' of undefined",
            "cannot read property 'distance'",
            "cannot read property 'angle'",
            "cannot call method 'tofixed' of undefined",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
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

    property var injectedWheelActions: wheelActions
    property var injectedWinchActions: winchActions
    property var injectedTeensyActions: teensyActions
    property var injectedRecordingActions: recordingActions
    property var injectedSystemActions: systemActions
    property var injectedActionLegality: actionLegality

    DeviceControlTab {{
        anchors.fill: parent
        recordingStatus: recordingStatusModel
        wheelStatus: wheelStatusModel
        winchStatus: winchStatusModel
        teensyStatus: teensyStatusModel
        wheelActions: parent.injectedWheelActions
        winchActions: parent.injectedWinchActions
        teensyActions: parent.injectedTeensyActions
        recordingActions: parent.injectedRecordingActions
        systemActions: parent.injectedSystemActions
        actionLegality: parent.injectedActionLegality
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
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
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
    id: popupHost
    width: 1280
    height: 800
    visible: false
    property var injectedStatus: baseTopViewStatus
    property var injectedActions: baseTopViewActions
    property var injectedLegality: actionLegality

    BaseTopViewSettingsPopup {{
        visible: true
        baseTopViewStatus: popupHost.injectedStatus
        baseTopViewActions: popupHost.injectedActions
        actionLegality: popupHost.injectedLegality
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
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()
