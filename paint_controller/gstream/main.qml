import QtQuick 2.15
import QtQuick.Window 2.15

Window {
    width: 640
    height: 480
    visible: true
    title: qsTr("Video Stream")

    Image {
        id: videoFrame
        anchors.fill: parent
        cache: false
        source: "image://live/frame"
    }

    Connections {
        target: videoStreamer
        function onFrame_ready() {
            videoFrame.source = ""
            videoFrame.source = "image://live/frame"
        }
    }
}