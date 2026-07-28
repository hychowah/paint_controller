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
            height: 40
            color: "#F8F8F8"
            border.color: "#DDDDDD"
            border.width: 1
            radius: 4

            Row {
                anchors.fill: parent

                Rectangle {
                    width: parent.width / 2
                    height: parent.height
                    color: "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "Left Propeller"
                        font.bold: true
                        font.pixelSize: 16
                    }

                    Rectangle {
                        anchors.right: parent.right
                        width: 1
                        height: parent.height
                        color: "#DDDDDD"
                    }
                }

                Rectangle {
                    width: parent.width / 2
                    height: parent.height
                    color: "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "Right Propeller"
                        font.bold: true
                        font.pixelSize: 16
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 40
            color: "white"
            border.color: "#EEEEEE"
            border.width: 1

            Row {
                anchors.fill: parent

                Rectangle {
                    width: parent.width / 2
                    height: parent.height
                    color: "transparent"

                    Row {
                        anchors.centerIn: parent
                        spacing: 10
                        Text { text: "Position:"; font.bold: true }
                        Text { text: root.teensyStatus.leftPropPosition.toFixed(0) + "°" }
                    }

                    Rectangle {
                        anchors.right: parent.right
                        width: 1
                        height: parent.height
                        color: "#EEEEEE"
                    }
                }

                Rectangle {
                    width: parent.width / 2
                    height: parent.height
                    color: "transparent"

                    Row {
                        anchors.centerIn: parent
                        spacing: 10
                        Text { text: "Position:"; font.bold: true }
                        Text { text: root.teensyStatus.rightPropPosition.toFixed(0) + "°" }
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 40
            color: "#F9F9F9"
            border.color: "#EEEEEE"
            border.width: 1

            Row {
                anchors.fill: parent

                Rectangle {
                    width: parent.width / 2
                    height: parent.height
                    color: "transparent"

                    Row {
                        anchors.centerIn: parent
                        spacing: 10
                        Text { text: "PWM:"; font.bold: true }
                        Text { text: root.teensyStatus.leftPropPwm.toFixed(0) }
                    }

                    Rectangle {
                        anchors.right: parent.right
                        width: 1
                        height: parent.height
                        color: "#EEEEEE"
                    }
                }

                Rectangle {
                    width: parent.width / 2
                    height: parent.height
                    color: "transparent"

                    Row {
                        anchors.centerIn: parent
                        spacing: 10
                        Text { text: "PWM:"; font.bold: true }
                        Text { text: root.teensyStatus.rightPropPwm.toFixed(0) }
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 120
            color: "#F8F8F8"
            border.color: "#DDDDDD"
            border.width: 1
            radius: 4

            Row {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Rectangle {
                    width: parent.width / 2 - 5
                    height: parent.height
                    color: "white"
                    radius: 4

                    Rectangle {
                        anchors.centerIn: parent
                        width: 80
                        height: 80
                        radius: 40
                        color: "#EEEEEE"
                        border.color: "#DDDDDD"
                        border.width: 1

                        Rectangle {
                            anchors.centerIn: parent
                            width: 70
                            height: 6
                            color: "#666666"
                            transform: Rotation {
                                origin.x: 35
                                origin.y: 3
                                angle: root.teensyStatus.leftPropPosition + 90
                            }
                        }

                        Rectangle {
                            anchors.centerIn: parent
                            width: 10
                            height: 10
                            radius: 5
                            color: "#999999"
                        }
                    }
                }

                Rectangle {
                    width: parent.width / 2 - 5
                    height: parent.height
                    color: "white"
                    radius: 4

                    Rectangle {
                        anchors.centerIn: parent
                        width: 80
                        height: 80
                        radius: 40
                        color: "#EEEEEE"
                        border.color: "#DDDDDD"
                        border.width: 1

                        Rectangle {
                            anchors.centerIn: parent
                            width: 70
                            height: 6
                            color: "#666666"
                            transform: Rotation {
                                origin.x: 35
                                origin.y: 3
                                angle: root.teensyStatus.rightPropPosition + 90
                            }
                        }

                        Rectangle {
                            anchors.centerIn: parent
                            width: 10
                            height: 10
                            radius: 5
                            color: "#999999"
                        }
                    }
                }
            }
        }
    }
}
