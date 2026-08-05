import QtQuick
import "../features/systemcontrol"
import "../features/video"
import "../features/workflow"

/**
 * Shared dual-surface overlay composition (TD-053 / Ousterhout Slice 5).
 *
 * Hosts inject visibility/active flags, objectNames, z-layers, and models.
 * This stack must not read root-context globals; all deps are required properties.
 */
Item {
    id: stack
    anchors.fill: parent

    // --- Surface visibility / active (host-computed) ---
    required property bool systemControlVisible
    required property bool joystickVisible
    required property bool emergencyVisible
    required property bool videoFullscreenActive

    // --- Smoke/test objectNames (host-specific Main vs Secondary) ---
    required property string systemControlObjectName
    required property string joystickObjectName
    required property string videoFullscreenObjectName
    required property string emergencyObjectName

    // --- Z layers (host binds overlayHost.*_layer) ---
    required property int systemControlLayer
    required property int joystickLayer
    required property int videoFullscreenLayer
    required property int emergencyLayer

    // --- Models / controllers ---
    required property var overlayController
    required property var systemControlServices
    required property var recordingStatus
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus
    required property var valveStatus
    required property var lidarStatus
    required property var videoRuntime
    required property var wheelActions
    required property var winchActions
    required property var teensyActions
    required property var recordingActions
    required property var systemActions
    required property var actionLegality
    required property var settingsManager
    required property var baseTopViewStatus
    required property var baseTopViewActions
    required property var qtBridge
    required property string videoSource

    // Re-export for MainWindow property alias / findChild stability
    property alias videoFullscreenOverlay: videoFullscreenWorkspace
    property alias systemControlMenu: systemControlWorkspace
    property alias joystickOverlay: joystickOverlayItem
    property alias emergencyOverlay: emergencyOverlayItem
    property alias workflowEditorWorkspace: workflowEditorWorkspaceItem

    SystemControlWorkspace {
        id: systemControlWorkspace
        anchors.fill: parent
        objectName: stack.systemControlObjectName
        z: stack.systemControlLayer
        showOverlay: stack.overlayController ? stack.overlayController.show_overlay : false
        activeMenu: stack.overlayController ? stack.overlayController.active_menu : ""
        systemControlServices: stack.systemControlServices
        recordingStatus: stack.recordingStatus
        wheelStatus: stack.wheelStatus
        winchStatus: stack.winchStatus
        teensyStatus: stack.teensyStatus
        wheelActions: stack.wheelActions
        winchActions: stack.winchActions
        teensyActions: stack.teensyActions
        recordingActions: stack.recordingActions
        systemActions: stack.systemActions
        actionLegality: stack.actionLegality
        settingsManager: stack.settingsManager
        overlayController: stack.overlayController
        visible: stack.systemControlVisible
                   && !(stack.systemControlServices
                        && stack.systemControlServices.workflowEditor
                        && stack.systemControlServices.workflowEditor.is_open)
    }

    WorkflowEditorWorkspace {
        id: workflowEditorWorkspaceItem
        anchors.fill: parent
        z: stack.systemControlLayer + 50
        workflowEditor: stack.systemControlServices
                        ? stack.systemControlServices.workflowEditor
                        : null
        overlayController: stack.overlayController
    }

    JoystickOverlay {
        id: joystickOverlayItem
        anchors.fill: parent
        objectName: stack.joystickObjectName
        z: stack.joystickLayer
        showOverlay: stack.overlayController ? stack.overlayController.show_overlay : false
        leftSelectedIndex: stack.overlayController ? stack.overlayController.left_selected_index : 0
        rightSelectedIndex: stack.overlayController ? stack.overlayController.right_selected_index : 0
        activeMenu: stack.overlayController ? stack.overlayController.active_menu : ""
        controlOptions: stack.overlayController ? stack.overlayController.control_options : []
        overlayController: stack.overlayController
        visible: stack.joystickVisible
    }

    VideoFullscreenWorkspace {
        id: videoFullscreenWorkspace
        anchors.fill: parent
        objectName: stack.videoFullscreenObjectName
        z: stack.videoFullscreenLayer
        active: stack.videoFullscreenActive
        videoSource: stack.videoSource
        workflowServices: stack.systemControlServices
        videoRuntime: stack.videoRuntime
        wheelStatus: stack.wheelStatus
        winchStatus: stack.winchStatus
        teensyStatus: stack.teensyStatus
        valveStatus: stack.valveStatus
        lidarStatus: stack.lidarStatus
        overlayController: stack.overlayController
        baseTopViewStatus: stack.baseTopViewStatus
        baseTopViewActions: stack.baseTopViewActions
        actionLegality: stack.actionLegality
    }

    EmergencyOverlay {
        id: emergencyOverlayItem
        anchors.fill: parent
        objectName: stack.emergencyObjectName
        z: stack.emergencyLayer
        qtBridge: stack.qtBridge
        visible: stack.emergencyVisible
    }
}
