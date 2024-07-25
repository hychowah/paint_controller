import QtQuick 6.7
import QtQuick.Controls 6.7
import QtMultimedia 6.7

Item {
    id: videoStream
    width: 640
    height: 480

    MediaPlayer {
        id: mediaPlayer
        objectName: "mediaPlayer"
        videoOutput: videoOutput
        autoPlay: true  // Ensure it starts playing automatically

        onErrorChanged: {
            console.log("MediaPlayer error:", error)
        }
    }

    VideoOutput {
        id: videoOutput
        anchors.fill: parent
    }

    Component.onCompleted: {
        console.log("MediaPlayer initialized, starting playback")
        mediaPlayer.play()
    }
}
