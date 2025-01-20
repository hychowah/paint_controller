import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: powerControlMenu

    property bool showOverlay: false
    property string activeMenu: ""
    property bool showPowerMenu: showOverlay && activeMenu === "power"

    Rectangle {
        id: powerOverlayBackground
        anchors.fill: parent
        color: "#000000"
        opacity: showPowerMenu ? 0.7 : 0
        visible: opacity > 0  // Only visible when opacity > 0
        
        Behavior on opacity {
            NumberAnimation { 
                duration: 300
                easing.type: Easing.InOutQuad 
            }
        }
    }

    Rectangle {
        id: powerMenuContainer
        width: 400
        height: 300
        radius: 20
        color: "#2c2c2c"
        opacity: showPowerMenu ? 1 : 0
        visible: opacity > 0  // Only visible when opacity > 0
        border.color: "#28445E"
        border.width: 4
        
        // Position and animation setup
        anchors {
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            topMargin: showPowerMenu ? (parent.height - height) / 2 : -height
        }

        Behavior on anchors.topMargin {
            NumberAnimation {
                duration: 300
                easing.type: Easing.OutBack
                easing.overshoot: 0.5
            }
        }

        Behavior on opacity {
            NumberAnimation {
                duration: 300
                easing.type: Easing.InOutQuad
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
                font.family: "Helvetica"
                font.pixelSize: 30
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }

            Rectangle {
                height: 6
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
                    font.family: "Helvetica"
                    font.pixelSize: 20
                    color: "#cccccc"
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: menuWinchEnableSwitch.indicator.width + 12
                }
            }

            Switch {
                id: menuTeensyRelaySwitch
                text: "Teensy Relay"
                checked: uiData.teensy_relay_enabled
                Layout.fillWidth: true
                
                onToggled: backend.setTeensyRelayEnabled(checked)

                indicator: Rectangle {
                    implicitWidth: parent.width * 0.2
                    implicitHeight: implicitWidth * 0.5
                    x: mainPowerSwitch.leftPadding
                    y: parent.height / 2 - height / 2
                    radius: implicitHeight / 2
                    color: uiData.teensy_relay_enabled ? "#4CAF50" : "#666666"

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
                    font.family: "Helvetica"
                    color: "#cccccc"
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: menuTeensyRelaySwitch.indicator.width + 12
                }
            }

            Switch {
                id: menuTeensyEnableSwitch
                text: "Teensy Enable"
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
                        x: menuTeensyEnableSwitch.checked ? parent.width - width - 2 : 2
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
                    text: menuTeensyEnableSwitch.text
                    font.pixelSize: 20
                    font.family: "Helvetica"
                    color: "#cccccc"
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: menuTeensyEnableSwitch.indicator.width + 12
                }
            }

            Switch {
                id: menuYawEnableSwitch
                text: "Yaw Control Enable"
                checked: uiData.teensy_yaw_enabled
                Layout.fillWidth: true
                
                onToggled: backend.setYawControl(checked, uiData.teensy_yaw_command, uiData.teensy_yaw_pid_p, uiData.teensy_yaw_pid_i, uiData.teensy_yaw_pid_d, uiData.teensy_yaw_pwm)

                indicator: Rectangle {
                    implicitWidth: parent.width * 0.2
                    implicitHeight: implicitWidth * 0.5
                    x: mainPowerSwitch.leftPadding
                    y: parent.height / 2 - height / 2
                    radius: implicitHeight / 2
                    color: uiData.teensy_yaw_enabled ? "#4CAF50" : "#666666"

                    Rectangle {
                        x: menuYawEnableSwitch.checked ? parent.width - width - 2 : 2
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
                    text: menuYawEnableSwitch.text
                    font.pixelSize: 20
                    font.family: "Helvetica"
                    color: "#cccccc"
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: menuYawEnableSwitch.indicator.width + 12
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}

