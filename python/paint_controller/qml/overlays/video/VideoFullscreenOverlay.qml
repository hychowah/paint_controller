import QtQuick
import "../../features/video"

Item {
    id: root

    property string videoSource: ""
    property bool active: false

    VideoFullscreenWorkspace {
        anchors.fill: parent
        videoSource: root.videoSource
        active: root.active
    }
}
