import QtQuick
import "../../features/video"

Item {
    id: root

    property string videoSource: ""
    property bool active: false
    required property var workflowServices
    required property var videoRuntime
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus
    required property var valveStatus
    required property var lidarStatus
    required property var overlayController
    required property var baseTopViewStatus
    required property var baseTopViewActions
    required property var actionLegality

    VideoFullscreenWorkspace {
        anchors.fill: parent
        videoSource: root.videoSource
        active: root.active
        workflowServices: root.workflowServices
        videoRuntime: root.videoRuntime
        wheelStatus: root.wheelStatus
        winchStatus: root.winchStatus
        teensyStatus: root.teensyStatus
        valveStatus: root.valveStatus
        lidarStatus: root.lidarStatus
        overlayController: root.overlayController
        baseTopViewStatus: root.baseTopViewStatus
        baseTopViewActions: root.baseTopViewActions
        actionLegality: root.actionLegality
    }
}
