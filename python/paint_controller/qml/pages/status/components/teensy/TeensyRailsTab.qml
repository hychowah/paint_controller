import QtQuick

Item {
    id: root
    required property var teensyStatus

    Column {
        anchors.fill: parent
        anchors.topMargin: 10
        spacing: 20

        Rectangle {
            width: parent.width
            height: childrenRect.height + 20
            color: "#F8F8F8"
            border.color: "#DDDDDD"
            border.width: 1
            radius: 4

            Column {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                spacing: 10

                Text {
                    text: "Top Rail"
                    font.bold: true
                    font.pixelSize: 16
                }

                Grid {
                    width: parent.width
                    columns: 4
                    spacing: 15

                    Text { text: "Position:"; font.bold: true }
                    Text { text: root.teensyStatus.topRailPosition.toFixed(0) + " cnt" }
                    Text { text: "Speed:"; font.bold: true }
                    Text { text: root.teensyStatus.topRailSpeed.toFixed(0) + " m/s" }

                    Text { text: "Current:"; font.bold: true }
                    Text { text: root.teensyStatus.topRailCurrent.toFixed(0) + " A" }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: childrenRect.height + 20
            color: "#F8F8F8"
            border.color: "#DDDDDD"
            border.width: 1
            radius: 4

            Column {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 10
                spacing: 10

                Text {
                    text: "Arm Rail"
                    font.bold: true
                    font.pixelSize: 16
                }

                Grid {
                    width: parent.width
                    columns: 4
                    spacing: 15

                    Text { text: "Position:"; font.bold: true }
                    Text { text: root.teensyStatus.armRailPosition.toFixed(0) + " m" }
                    Text { text: "Speed:"; font.bold: true }
                    Text { text: root.teensyStatus.armRailSpeed.toFixed(0) + " m/s" }

                    Text { text: "Current:"; font.bold: true }
                    Text { text: root.teensyStatus.armRailCurrent.toFixed(0) + " A" }
                    Text { text: "Extension:"; font.bold: true }
                    Text { text: root.teensyStatus.armExtensionDist.toFixed(0) + " mm" }

                    Text { text: "Sensor:"; font.bold: true }
                    Text { text: root.teensyStatus.armSensorDist.toFixed(0) + " mm" }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 1
            color: "transparent"
        }
    }
}
