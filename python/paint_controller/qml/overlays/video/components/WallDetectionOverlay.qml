import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"

// Wall detection HUD. Pure QML (no Canvas/Context2D) for Deck main-thread budget.
Rectangle {
    id: overlay
    required property var lidarStatus

    width: 250
    height: 120

    property real scaleFactor: height / 160.0
    property real backgroundOpacity: 40

    property var lastLidarUpdateTime: new Date()
    property real messageTimeoutMs: 1000
    property bool isLidarActive: false
    readonly property real lidarDistance: (lidarStatus && typeof lidarStatus.distance === "number")
        ? lidarStatus.distance : 0.0
    readonly property real lidarAngle: (lidarStatus && typeof lidarStatus.angle === "number")
        ? lidarStatus.angle : 0.0
    readonly property real clampedDistance: Math.min(overlay.lidarDistance, 2.0)
    readonly property real distancePx: Math.max(4, clampedDistance * 40 * scaleFactor)
    readonly property real angleRad: overlay.lidarAngle * Math.PI / 180
    readonly property real sensorLenPx: Math.max(
        4, distancePx / Math.max(0.15, Math.cos(angleRad)))

    Connections {
        target: overlay.lidarStatus

        function onDistanceChanged() {
            overlay.lastLidarUpdateTime = new Date()
            overlay.isLidarActive = true
        }

        function onAngleChanged() {
            overlay.lastLidarUpdateTime = new Date()
            overlay.isLidarActive = true
        }
    }

    Timer {
        id: lidarTimeoutTimer
        interval: 500
        running: overlay.visible
        repeat: true
        onTriggered: {
            var now = new Date()
            overlay.isLidarActive =
                (now.getTime() - overlay.lastLidarUpdateTime.getTime()) < overlay.messageTimeoutMs
        }
    }

    anchors.bottom: parent.bottom
    anchors.bottomMargin: 5
    anchors.horizontalCenter: parent.horizontalCenter

    color: Qt.rgba(0, 0, 0, backgroundOpacity / 100)
    radius: 8 * scaleFactor

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10 * scaleFactor
        spacing: 10 * scaleFactor

        Item {
            Layout.fillWidth: true
            Layout.preferredWidth: 120 * scaleFactor
            Layout.fillHeight: true

            Text {
                text: "WALL DETECTION"
                color: "#00FF00"
                font.pixelSize: 11 * scaleFactor
                font.bold: true
                font.letterSpacing: 1.0
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
            }

            // Pure-QML geometry diagram (replaces Canvas)
            Item {
                id: diagram
                anchors.top: parent.top
                anchors.topMargin: 22 * scaleFactor
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right

                readonly property real cx: width * 0.5
                readonly property real cy: height * 0.75
                readonly property real sF: overlay.scaleFactor

                // Horizontal reference
                Rectangle {
                    x: diagram.cx - 30 * diagram.sF
                    y: diagram.cy - 0.5
                    width: 60 * diagram.sF
                    height: 1
                    color: "#666666"
                    opacity: 0.8
                }

                // Forward distance (green vertical)
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: diagram.cy - overlay.distancePx
                    width: 2 * diagram.sF
                    height: overlay.distancePx
                    color: "#00FF00"
                }

                // Sensor ray + wall (rotated about EF point)
                Item {
                    id: sensorArm
                    x: diagram.cx
                    y: diagram.cy
                    width: 1
                    height: 1
                    transform: Rotation {
                        origin.x: 0
                        origin.y: 0
                        // Screen y grows down; negate so positive angle matches canvas convention
                        angle: -overlay.lidarAngle
                    }

                    Rectangle {
                        x: -1 * diagram.sF
                        y: -overlay.sensorLenPx
                        width: 2 * diagram.sF
                        height: overlay.sensorLenPx
                        color: "#FFAA00"
                    }

                    Rectangle {
                        x: -overlay.width * 0.2
                        y: -overlay.sensorLenPx - 1.5 * diagram.sF
                        width: overlay.width * 0.4
                        height: 3 * diagram.sF
                        color: "#FF6600"
                        radius: 1
                    }
                }

                // End effector (on top)
                Rectangle {
                    x: diagram.cx - 6 * diagram.sF
                    y: diagram.cy - 6 * diagram.sF
                    width: 12 * diagram.sF
                    height: 12 * diagram.sF
                    radius: 6 * diagram.sF
                    color: "#00FF00"
                }
            }
        }

        Rectangle {
            Layout.preferredWidth: 2
            Layout.fillHeight: true
            color: "#333333"
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredWidth: 140 * scaleFactor
            Layout.fillHeight: true
            spacing: 8 * scaleFactor

            Column {
                Layout.fillWidth: true
                spacing: 4 * scaleFactor

                Text {
                    text: "DISTANCE"
                    color: "#00FF00"
                    font.pixelSize: 10 * scaleFactor
                    font.bold: true
                    font.letterSpacing: 0.5
                }

                Rectangle {
                    width: parent.width
                    height: 30 * scaleFactor
                    color: "#1A1A1A"
                    radius: 4 * scaleFactor
                    border.width: 1
                    border.color: "#00FF00"

                    Text {
                        anchors.centerIn: parent
                        text: overlay.lidarDistance.toFixed(2) + " m"
                        color: "#00FF00"
                        font.pixelSize: 20 * scaleFactor
                        font.bold: true
                        font.family: CommonStyle.fontMono
                    }
                }
            }

            Column {
                Layout.fillWidth: true
                spacing: 4 * scaleFactor

                Text {
                    text: "ANGLE DEVIATION"
                    color: "#FFAA00"
                    font.pixelSize: 10 * scaleFactor
                    font.bold: true
                    font.letterSpacing: 0.5
                }

                Rectangle {
                    width: parent.width
                    height: 30 * scaleFactor
                    color: "#1A1A1A"
                    radius: 4 * scaleFactor
                    border.width: 1
                    border.color: Math.abs(overlay.lidarAngle) > 5 ? "#FF6600" : "#FFAA00"

                    Text {
                        anchors.centerIn: parent
                        text: (overlay.lidarAngle > 0 ? "+" : "") + overlay.lidarAngle.toFixed(1) + "°"
                        color: Math.abs(overlay.lidarAngle) > 5 ? "#FF6600" : "#FFAA00"
                        font.pixelSize: 20 * scaleFactor
                        font.bold: true
                        font.family: CommonStyle.fontMono
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 25 * scaleFactor
                color: "transparent"

                Rectangle {
                    width: 8 * scaleFactor
                    height: 8 * scaleFactor
                    radius: 4 * scaleFactor
                    color: overlay.isLidarActive ? "#00FF00" : "#FF3333"
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter

                    NumberAnimation on opacity {
                        running: overlay.isLidarActive && overlay.visible
                        from: 1.0
                        to: 0.4
                        duration: 600
                        loops: Animation.Infinite
                    }
                }

                Text {
                    text: overlay.isLidarActive ? "ACTIVE" : "NO SIGNAL"
                    color: overlay.isLidarActive ? "#00FF00" : "#FF3333"
                    font.pixelSize: 10 * scaleFactor
                    font.bold: true
                    anchors.left: parent.left
                    anchors.leftMargin: 14 * scaleFactor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
