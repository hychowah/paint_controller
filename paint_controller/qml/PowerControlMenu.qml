import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: powerMenuContainer
    width: 400
    height: 300
    radius: 20
    color: "#4374A2"
    opacity: visible ? 1 : 0
    border.color: "#28445E"
    border.width: 4
    
    // Properties
    property bool isVisible: false
    
    // Signals for switch state changes
    signal mainPowerChanged(bool checked)
    signal auxPowerChanged(bool checked)
    signal batteryBackupChanged(bool checked)

    // Position and animation setup
    anchors {
        horizontalCenter: parent.horizontalCenter
        top: parent.top
        topMargin: isVisible ? (parent.height - height) / 2 : -height
    }

    Behavior on anchors.topMargin {
        NumberAnimation {
            duration: 300
            easing.type: Easing.OutBack
            easing.overshoot: 0.5
        }
    }

    ColumnLayout {
        anchors {
            fill: parent
            margins: 20
        }

        Text {
            text: "Power Control"
            color: "#E2E2E2"
            font.pixelSize: 30
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }

        Rectangle {
            height: 3
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width * 0.8
            color: "#28445E"
        }

        Item { Layout.fillHeight: true }

        Switch {
            id: menuWinchEnableSwitch
            text: "Winch Enable" 
            checked: uiData.winch_enabled
            Layout.fillWidth: true
            
            onCheckedChanged: backend.setWinchEnabled(checked)
            
            indicator: Rectangle {
                implicitWidth: parent.width * 0.2
                implicitHeight: implicitWidth * 0.5
                x: mainPowerSwitch.leftPadding
                y: parent.height / 2 - height / 2
                radius: implicitHeight / 2
                color: uiData.winch_enabled ? "#4CAF50" : "#666666"

                Rectangle {
                    x: menuWinchEnableSwitch.checked ? parent.width - width - 2 : 2
                    y: height * 0.1
                    width: parent.height * 0.8
                    height: parent.height * 0.8
                    radius: parent.height * 0.4
                    color: "white"

                    Behavior on x {
                        NumberAnimation { duration: 200 }
                    }
                }
            }

            contentItem: Text {
                text: menuWinchEnableSwitch.text
                font.pixelSize: 20
                font.bold: true
                color: "black"
                verticalAlignment: Text.AlignVCenter
                leftPadding: menuWinchEnableSwitch.indicator.width + 12
            }
        }

        Switch {
            id: menuTeensyRelaySwitch
            text: "Teensy Relay"
            checked: uiData.teensy_enabled
            Layout.fillWidth: true
            
            onToggled: backend.setTeensyEnabled(checked)

            indicator: Rectangle {
                implicitWidth: parent.width * 0.2
                implicitHeight: implicitWidth * 0.5
                x: mainPowerSwitch.leftPadding
                y: parent.height / 2 - height / 2
                radius: implicitHeight / 2
                color: uiData.teensy_enabled ? "#4CAF50" : "#666666"

                Rectangle {
                    x: menuTeensyRelaySwitch.checked ? parent.width - width - 2 : 2
                    y: height * 0.1
                    width: parent.height * 0.8
                    height: parent.height * 0.8
                    radius: parent.height * 0.4
                    color: "white"

                    Behavior on x {
                        NumberAnimation { duration: 200 }
                    }
                }
            }

            contentItem: Text {
                text: menuTeensyRelaySwitch.text
                font.pixelSize: 20
                font.bold: true
                color: "black"
                verticalAlignment: Text.AlignVCenter
                leftPadding: menuTeensyRelaySwitch.indicator.width + 12
            }
        }

        Switch {
            id: menuTeensyEnableSwitch
            text: "Teensy Enable"
            checked: false
            Layout.fillWidth: true
            
            onCheckedChanged: batteryBackupChanged(checked)

            indicator: Rectangle {
                implicitWidth: parent.width * 0.2
                implicitHeight: implicitWidth * 0.5
                x: mainPowerSwitch.leftPadding
                y: parent.height / 2 - height / 2
                radius: implicitHeight / 2
                color: batterySwitch.checked ? "#4CAF50" : "#666666"

                Rectangle {
                    x: batterySwitch.checked ? parent.width - width - 2 : 2
                    y: height * 0.1
                    width: parent.height * 0.8
                    height: parent.height * 0.8
                    radius: parent.height * 0.4
                    color: "white"

                    Behavior on x {
                        NumberAnimation { duration: 200 }
                    }
                }
            }

            contentItem: Text {
                font.pixelSize: 20
                font.bold: true
                color: "black"
                verticalAlignment: Text.AlignVCenter
                leftPadding: batterySwitch.indicator.width + 12
            }
        }

        Item { Layout.fillHeight: true }
    }
}