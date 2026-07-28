import QtQuick

Item {
    id: root
    required property var teensyStatus

    Column {
        anchors.fill: parent
        anchors.topMargin: 10
        spacing: 15

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
                    text: "Orientation"
                    font.bold: true
                    font.pixelSize: 16
                }

                Grid {
                    width: parent.width
                    columns: 6
                    spacing: 15

                    Text { text: "Pitch:"; font.bold: true }
                    Text { text: root.teensyStatus.imuPitch }
                    Text { text: "Roll:"; font.bold: true }
                    Text { text: root.teensyStatus.imuRoll }
                    Text { text: "Yaw:"; font.bold: true }
                    Text { text: root.teensyStatus.imuYaw }
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
                    text: "Linear Acceleration"
                    font.bold: true
                    font.pixelSize: 16
                }

                Grid {
                    width: parent.width
                    columns: 6
                    spacing: 15

                    Text { text: "X:"; font.bold: true }
                    Text { text: root.teensyStatus.imuAccX + " m/s²" }
                    Text { text: "Y:"; font.bold: true }
                    Text { text: root.teensyStatus.imuAccY + " m/s²" }
                    Text { text: "Z:"; font.bold: true }
                    Text { text: root.teensyStatus.imuAccZ + " m/s²" }
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
                    text: "Angular Velocity"
                    font.bold: true
                    font.pixelSize: 16
                }

                Grid {
                    width: parent.width
                    columns: 6
                    spacing: 15

                    Text { text: "X:"; font.bold: true }
                    Text { text: root.teensyStatus.imuAngularAccX + " rad/s" }
                    Text { text: "Y:"; font.bold: true }
                    Text { text: root.teensyStatus.imuAngularAccY + " rad/s" }
                    Text { text: "Z:"; font.bold: true }
                    Text { text: root.teensyStatus.imuAngularAccZ + " rad/s" }
                }
            }
        }
    }
}
