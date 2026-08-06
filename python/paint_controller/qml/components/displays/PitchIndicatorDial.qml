import QtQuick
import "../../theme"

// ADI-style pitch ladder. Pure QML (no Canvas/Context2D) for Deck main-thread budget.
Item {
    id: root
    width: 180
    height: 120

    required property real currentPitch

    property real backgroundOpacity: 0.45
    property real pitchRange: 10.0
    property real pitchScale: 4.5
    readonly property string pitchText: (root.currentPitch >= 0 ? "+" : "") + root.currentPitch.toFixed(1) + "°"

    readonly property color skyColor: "#3a7ebd"
    readonly property color groundColor: "#8b5a2b"
    readonly property color markColor: "#f4f7fb"

    // Fixed ladder marks every 2.5° (skip 0° — horizon is separate).
    readonly property var pitchMarkModel: [-10, -7.5, -5, -2.5, 2.5, 5, 7.5, 10]

    Rectangle {
        id: container
        anchors.fill: parent
        color: "transparent"
        radius: CommonStyle.radiusSm
        border.width: 0
        clip: true

        Item {
            id: pitchLadder
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            height: parent.height * 3
            y: parent.height / 2 - height / 2 - root.currentPitch * root.pitchScale

            Behavior on y {
                NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                y: 0
                height: parent.height / 2
                color: root.skyColor
                opacity: root.backgroundOpacity
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                y: parent.height / 2
                height: parent.height / 2
                color: root.groundColor
                opacity: root.backgroundOpacity
            }

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: parent.height / 2 - 1.5
                width: parent.width * 0.85
                height: 3
                color: CommonStyle.textPrimary
                radius: 1.5
                z: 2
            }

            Repeater {
                model: root.pitchMarkModel
                Item {
                    id: mark
                    required property real modelData
                    readonly property real pitch: modelData
                    readonly property bool major: Math.abs(pitch % 5) < 0.01
                    readonly property real lineW: major ? 50 : 30
                    readonly property real cy: pitchLadder.height / 2 + pitch * root.pitchScale

                    width: pitchLadder.width
                    height: 1
                    y: cy
                    z: 2

                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.verticalCenter: parent.verticalCenter
                        width: mark.lineW
                        height: 2
                        color: root.markColor
                        opacity: 0.9
                    }

                    Text {
                        visible: mark.major
                        anchors.verticalCenter: parent.verticalCenter
                        x: parent.width / 2 - mark.lineW / 2 - 18
                        width: 16
                        horizontalAlignment: Text.AlignHCenter
                        text: Math.abs(mark.pitch).toString()
                        color: root.markColor
                        font.pixelSize: 11
                        font.family: CommonStyle.fontSans
                        opacity: 0.9
                    }

                    Text {
                        visible: mark.major
                        anchors.verticalCenter: parent.verticalCenter
                        x: parent.width / 2 + mark.lineW / 2 + 2
                        width: 16
                        horizontalAlignment: Text.AlignHCenter
                        text: Math.abs(mark.pitch).toString()
                        color: root.markColor
                        font.pixelSize: 11
                        font.family: CommonStyle.fontSans
                        opacity: 0.9
                    }
                }
            }
        }

        Item {
            id: centerReference
            anchors.centerIn: parent
            width: parent.width
            height: 30
            z: 10

            Rectangle {
                x: parent.width / 2 - 50
                y: parent.height / 2 - 1.5
                width: 40
                height: 3
                color: CommonStyle.statusWarning
                radius: 1.5
            }

            Rectangle {
                x: parent.width / 2 + 10
                y: parent.height / 2 - 1.5
                width: 40
                height: 3
                color: CommonStyle.statusWarning
                radius: 1.5
            }

            Rectangle {
                anchors.centerIn: parent
                width: 6
                height: 6
                radius: 3
                color: CommonStyle.statusWarning
                border.color: CommonStyle.backgroundL0
                border.width: 1
            }
        }

        Text {
            id: pitchLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 5
            text: "PITCH"
            color: CommonStyle.textSecondary
            font.pixelSize: CommonStyle.fontLabel - 2
            font.bold: true
            z: 11
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: pitchLabel.bottom
            anchors.topMargin: 25
            text: root.pitchText
            color: CommonStyle.textPrimary
            font.pixelSize: CommonStyle.fontLabel
            font.bold: true
            font.family: CommonStyle.fontMono
            z: 11
        }
    }
}
