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
    }
}
