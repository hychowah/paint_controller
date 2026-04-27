import QtQuick
import "../../features/video"

Item {
    id: root

    property string videoSource: ""
    property bool active: false
    required property var workflowServices
    required property var videoRuntime

    VideoFullscreenWorkspace {
        anchors.fill: parent
        videoSource: root.videoSource
        active: root.active
        workflowServices: root.workflowServices
        videoRuntime: root.videoRuntime
    }
}
