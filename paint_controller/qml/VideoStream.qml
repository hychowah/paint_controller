import QtQuick 6.7
import QtQuick.Controls 6.7
import QtMultimedia 6.7

Item {
    width: 640
    height: 480

    MediaPlayer {
        id: mediaPlayer
        objectName: "mediaPlayer"
        source: "gst-pipeline"
    }

    VideoOutput {
        source: mediaPlayer
        anchors.fill: parent
    }

    Component.onCompleted: {
        mediaPlayer.play()
    }
}
