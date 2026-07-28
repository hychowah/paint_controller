import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#FFFFFF"
    radius: 15
    border.width: 1
    border.color: "#E0E0E0"

    required property var winchStatus
    property color primaryColor: "#2196F3"
    property color dangerColor: "#F44336"

    signal notifyRequested(string message, int duration)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        Rectangle {
            Layout.fillWidth: true
            height: 60
            visible: root.winchStatus.loadDetectionEnabled && root.winchStatus.unusualLoadDetected
            color: "#FFEBEE"
            radius: 12

            SequentialAnimation on opacity {
                running: root.winchStatus.loadDetectionEnabled && root.winchStatus.unusualLoadDetected
                loops: Animation.Infinite
                PropertyAnimation { to: 0.7; duration: 500 }
                PropertyAnimation { to: 1.0; duration: 500 }
            }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Rectangle {
                    width: 24
                    height: 24
                    radius: 12
                    color: root.dangerColor

                    Text {
                        anchors.centerIn: parent
                        text: "!"
                        color: "white"
                        font.bold: true
                        font.pixelSize: 16
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: "UNUSUAL LOAD DETECTED"
                        font.bold: true
                        color: root.dangerColor
                        font.pixelSize: 16
                    }

                    Text {
                        text: "Immediate attention required"
                        color: "#D32F2F"
                        font.pixelSize: 12
                    }
                }

                Button {
                    text: "RESET"
                    onClicked: root.notifyRequested("Load alarm acknowledged", 2000)

                    background: Rectangle {
                        radius: 4
                        color: "#FFCDD2"
                        border.color: root.dangerColor
                        border.width: 1
                    }

                    contentItem: Text {
                        text: parent.text
                        font.pixelSize: 12
                        font.bold: true
                        color: root.dangerColor
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 220
            color: "#F5F5F5"
            radius: 12

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10

                Text {
                    text: "Cable Status"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#212121"
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 10

                    Rectangle {
                        width: parent.width / 2 - 5
                        height: 110
                        color: "#FFFFFF"
                        radius: 8
                        border.width: 1
                        border.color: "#E0E0E0"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 4

                            Text {
                                text: "Cable Length"
                                font.pixelSize: 14
                                color: "#757575"
                            }

                            Text {
                                text: Math.round(root.winchStatus.cableLength)
                                font.pixelSize: 36
                                font.bold: true
                                color: "#2196F3"
                            }

                            Text {
                                text: "mm"
                                font.pixelSize: 14
                                color: "#757575"
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 4
                                color: "#E0E0E0"
                                radius: 2

                                Rectangle {
                                    width: Math.min(parent.width * (root.winchStatus.cableLength / 10000), parent.width)
                                    height: parent.height
                                    radius: 2
                                    color: {
                                        const percent = root.winchStatus.cableLength / 100
                                        if (percent < 70) return "#2196F3"
                                        else if (percent < 90) return "#FF9800"
                                        else return "#F44336"
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width / 2 - 5
                        height: 110
                        color: "#FFFFFF"
                        radius: 8
                        border.width: 1
                        border.color: "#E0E0E0"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 4

                            Text {
                                text: "Cable Speed"
                                font.pixelSize: 14
                                color: "#757575"
                            }

                            RowLayout {
                                spacing: 4

                                Text {
                                    text: root.winchStatus.cableSpeed.toFixed(1)
                                    font.pixelSize: 36
                                    font.bold: true
                                    color: Math.abs(root.winchStatus.cableSpeed) > 0.5 ? "#FF9800" : "#2196F3"
                                }

                                Text {
                                    visible: Math.abs(root.winchStatus.cableSpeed) > 0.05
                                    text: root.winchStatus.cableSpeed > 0 ? "▶" : "◀"
                                    font.pixelSize: 24
                                    color: "#FF9800"
                                    Layout.alignment: Qt.AlignBottom
                                    Layout.bottomMargin: 6
                                }
                            }

                            Text {
                                text: "mm/s"
                                font.pixelSize: 14
                                color: "#757575"
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 4
                                color: "#E0E0E0"
                                radius: 2
                                visible: Math.abs(root.winchStatus.cableSpeed) > 0

                                Rectangle {
                                    property real maxSpeed: 500
                                    width: Math.min(parent.width * (Math.abs(root.winchStatus.cableSpeed) / maxSpeed), parent.width)
                                    height: parent.height
                                    radius: 2
                                    color: Math.abs(root.winchStatus.cableSpeed) > 1.5 ? "#FF9800" : "#2196F3"
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 60
                    color: "#FFFFFF"
                    radius: 8
                    border.width: 1
                    border.color: "#E0E0E0"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 6

                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                text: "Cable Extension"
                                font.pixelSize: 14
                                color: "#757575"
                            }

                            Item { Layout.fillWidth: true }

                            Text {
                                text: Math.round(root.winchStatus.cableLength / 100) + "%"
                                font.pixelSize: 16
                                font.bold: true
                                color: {
                                    const percent = root.winchStatus.cableLength / 100
                                    if (percent < 70) return "#2196F3"
                                    else if (percent < 90) return "#FF9800"
                                    else return "#F44336"
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 20
                            color: "#E0E0E0"
                            radius: 4

                            Rectangle {
                                width: Math.min(parent.width * (root.winchStatus.cableLength / 10000), parent.width)
                                height: parent.height
                                radius: 4
                                color: {
                                    const percent = root.winchStatus.cableLength / 100
                                    if (percent < 70) return "#2196F3"
                                    else if (percent < 90) return "#FF9800"
                                    else return "#F44336"
                                }
                            }

                            Row {
                                anchors.fill: parent
                                spacing: 0

                                Repeater {
                                    model: 10
                                    Rectangle {
                                        width: 1
                                        height: parent.height
                                        x: (index + 1) * (parent.width / 10)
                                        color: "#9E9E9E"
                                        visible: index > 0 && index < 9
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#F5F5F5"
            radius: 12

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10

                Text {
                    text: "Motor Metrics"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#212121"
                }

                Flow {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10

                    Rectangle {
                        width: parent.width / 2 - 5
                        height: 90
                        color: "#FFFFFF"
                        radius: 8
                        border.width: 1
                        border.color: root.winchStatus.winchTorque > 50 ? "#F44336" : "#E0E0E0"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 4

                            RowLayout {
                                Layout.fillWidth: true

                                Text {
                                    text: "Torque"
                                    font.pixelSize: 14
                                    color: "#757575"
                                }

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    visible: root.winchStatus.winchTorque > 50
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "#F44336"

                                    Text {
                                        anchors.centerIn: parent
                                        text: "!"
                                        color: "white"
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                }
                            }

                            Text {
                                text: root.winchStatus.winchTorque.toFixed(1)
                                font.pixelSize: 32
                                font.bold: true
                                color: {
                                    const torque = root.winchStatus.winchTorque
                                    if (torque < 30) return "#2196F3"
                                    else if (torque < 50) return "#FF9800"
                                    else return "#F44336"
                                }
                            }

                            Text {
                                text: "Nm"
                                font.pixelSize: 14
                                color: "#757575"
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width / 2 - 5
                        height: 90
                        color: "#FFFFFF"
                        radius: 8
                        border.width: 1
                        border.color: root.winchStatus.motorTemperature > 60 ? "#F44336" : "#E0E0E0"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 4

                            RowLayout {
                                Layout.fillWidth: true

                                Text {
                                    text: "Temperature"
                                    font.pixelSize: 14
                                    color: "#757575"
                                }

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    visible: root.winchStatus.motorTemperature > 50
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: root.winchStatus.motorTemperature > 60 ? "#F44336" : "#FF9800"

                                    Text {
                                        anchors.centerIn: parent
                                        text: "!"
                                        color: "white"
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                }
                            }

                            Text {
                                text: root.winchStatus.motorTemperature.toFixed(1)
                                font.pixelSize: 32
                                font.bold: true
                                color: {
                                    const temp = root.winchStatus.motorTemperature
                                    if (temp < 40) return "#2196F3"
                                    else if (temp < 60) return "#FF9800"
                                    else return "#F44336"
                                }
                            }

                            Text {
                                text: "°C"
                                font.pixelSize: 14
                                color: "#757575"
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width / 2 - 5
                        height: 90
                        color: "#FFFFFF"
                        radius: 8
                        border.width: 1
                        border.color: (root.winchStatus.motorVoltage < 22 || root.winchStatus.motorVoltage > 25) ? "#F44336" : "#E0E0E0"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 4

                            RowLayout {
                                Layout.fillWidth: true

                                Text {
                                    text: "Voltage"
                                    font.pixelSize: 14
                                    color: "#757575"
                                }

                                Item { Layout.fillWidth: true }

                                Rectangle {
                                    visible: root.winchStatus.motorVoltage < 22 || root.winchStatus.motorVoltage > 25
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: "#F44336"

                                    Text {
                                        anchors.centerIn: parent
                                        text: "!"
                                        color: "white"
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                }
                            }

                            Text {
                                text: root.winchStatus.motorVoltage.toFixed(1)
                                font.pixelSize: 32
                                font.bold: true
                                color: {
                                    const voltage = root.winchStatus.motorVoltage
                                    if (voltage > 22 && voltage < 25) return "#2196F3"
                                    else return "#F44336"
                                }
                            }

                            Text {
                                text: "V"
                                font.pixelSize: 14
                                color: "#757575"
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width / 2 - 5
                        height: 90
                        color: "#FFFFFF"
                        radius: 8
                        border.width: 1
                        border.color: root.winchStatus.motorBrake ? "#F44336" : "#4CAF50"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 4

                            Text {
                                text: "Brake"
                                font.pixelSize: 14
                                color: "#757575"
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                Rectangle {
                                    width: 16
                                    height: 16
                                    radius: 8
                                    color: root.winchStatus.motorBrake ? "#F44336" : "#4CAF50"
                                }

                                Text {
                                    text: root.winchStatus.motorBrake ? "ENGAGED" : "RELEASED"
                                    font.pixelSize: 24
                                    font.bold: true
                                    color: root.winchStatus.motorBrake ? "#F44336" : "#4CAF50"
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: 60
                        color: "#FFFFFF"
                        radius: 8
                        border.width: 1
                        border.color: root.winchStatus.unusualLoadDetected ? "#F44336" : "#4CAF50"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 10

                            Text {
                                text: "Load Status:"
                                font.pixelSize: 14
                                color: "#757575"
                            }

                            Rectangle {
                                width: 16
                                height: 16
                                radius: 8
                                color: root.winchStatus.unusualLoadDetected ? "#F44336" : "#4CAF50"
                            }

                            Text {
                                text: root.winchStatus.unusualLoadDetected ? "ABNORMAL" : "NORMAL"
                                font.pixelSize: 24
                                font.bold: true
                                color: root.winchStatus.unusualLoadDetected ? "#F44336" : "#4CAF50"
                            }

                            Item { Layout.fillWidth: true }

                            Button {
                                visible: root.winchStatus.unusualLoadDetected
                                text: "RESET"
                                enabled: root.winchStatus.unusualLoadDetected

                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: "#F44336"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    radius: 4
                                    color: "#FFEBEE"
                                    border.color: "#F44336"
                                    border.width: 1
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
