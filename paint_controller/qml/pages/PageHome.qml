import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import "../"
import "../components"

Rectangle {
    id: pageHomeRect
    width: parent.width
    height: parent.height
    color: "#5E5C64"  // Match your original background color
    
    // Function to show message popup
    function showMessage(message, type) {
        if (typeof messagePopup !== 'undefined') {
            messagePopup.messageTitle = "Button Action"
            messagePopup.messageText = message
            messagePopup.messageType = type
            messagePopup.open()
        }
    }
    
    // Reusable Control Card Component
    component ControlCard: Rectangle {
        property string deviceHost: ""
        property string deviceName: ""
        property string startButtonText: "START"
        property string stopButtonText: "STOP"
        property color startButtonColor: "#66BB6A"
        property color startButtonHoverColor: "#5CBF60"
        property color startButtonPressedColor: "#4CAF50"
        property color stopButtonColor: "#FC8181"
        property color stopButtonHoverColor: "#F56565"
        property color stopButtonPressedColor: "#E53E3E"
        
        Layout.fillWidth: true
        Layout.preferredHeight: 85
        radius: 10
        color: "#4A4A54"  // Match the card color from your design
        border.color: "#6A6A74"
        border.width: 1
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8
            
            Text {
                text: deviceName
                font.pixelSize: 18
                font.bold: true
                font.weight: Font.Medium
                color: "#ffffff"
                Layout.alignment: Qt.AlignLeft
            }
            
            RowLayout {
                spacing: 12
                Layout.fillWidth: true
                
                Button {
                    text: startButtonText
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 36
                    background: Rectangle {
                        radius: 6
                        color: parent.pressed ? startButtonPressedColor : (parent.hovered ? startButtonHoverColor : startButtonColor)
                        border.color: startButtonPressedColor
                        border.width: 1
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "#ffffff"
                        font.weight: Font.Medium
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        sshHandler.handle_device_command(deviceHost, deviceName, "start")
                    }
                }
                
                Button {
                    text: stopButtonText
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 36
                    background: Rectangle {
                        radius: 6
                        color: parent.pressed ? stopButtonPressedColor : (parent.hovered ? stopButtonHoverColor : stopButtonColor)
                        border.color: stopButtonPressedColor
                        border.width: 1
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "#ffffff"
                        font.weight: Font.Medium
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        sshHandler.handle_device_command(deviceHost, deviceName, "stop")
                    }
                }
            }
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 20
        
        // TOP ROW - Title
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "transparent"
            
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12
                
                Text {
                    text: "PAINT CONTROLLER"
                    font.pixelSize: 24
                    font.weight: Font.Light
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Rectangle {
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: 2
                    radius: 1
                    color: "#64B5F6"
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
        
        // BOTTOM ROW - Two Columns
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 40
        
            // LEFT SIDE - BASE SETTINGS
            Rectangle {
                Layout.fillHeight: true
                Layout.fillWidth: true
                color: "transparent"
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    
                    // Header
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        radius: 8
                        color: "#4A4A54"  // Match your card color
                        border.color: "#6A6A74"
                        border.width: 1
                        
                        Text {
                            text: "BASE SETTINGS"
                            font.pixelSize: 16
                            font.weight: Font.Medium
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                    
                    // Control Cards Container - anchored to top
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        spacing: 12
                        
                        ControlCard {
                            deviceHost: "BASE"
                            deviceName: "Winch"
                        }
                        
                        ControlCard {
                            deviceHost: "BASE"
                            deviceName: "Wheel"
                        }
                        
                        ControlCard {
                            deviceHost: "BASE"
                            deviceName: "Camera"
                            startButtonText: "STREAM"
                            startButtonColor: "#64B5F6"
                            startButtonHoverColor: "#42A5F5"
                            startButtonPressedColor: "#2196F3"
                        }
                    }
                    
                    // Spacer to push cards to top
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
            
            // RIGHT SIDE - END EFFECTOR
            Rectangle {
                Layout.fillHeight: true
                Layout.fillWidth: true
                color: "transparent"
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    
                    // Header
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        radius: 8
                        color: "#4A4A54"  // Match your card color
                        border.color: "#6A6A74"
                        border.width: 1
                        
                        Text {
                            text: "END EFFECTOR"
                            font.pixelSize: 16
                            font.weight: Font.Medium
                            color: "#ffffff"
                            anchors.centerIn: parent
                        }
                    }
                    
                    // Control Cards Container - anchored to top
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        spacing: 12
                        
                        ControlCard {
                            deviceHost: "END_EFFECTOR"
                            deviceName: "Teensy"
                        }
                        
                        ControlCard {
                            deviceHost: "END_EFFECTOR"
                            deviceName: "Wind Sensor"
                        }
                        
                        ControlCard {
                            deviceHost: "END_EFFECTOR"
                            deviceName: "Lidar"
                        }
                        
                        ControlCard {
                            deviceHost: "END_EFFECTOR"
                            deviceName: "Camera"
                            startButtonText: "STREAM"
                            startButtonColor: "#64B5F6"
                            startButtonHoverColor: "#42A5F5"
                            startButtonPressedColor: "#2196F3"
                        }
                    }
                    
                    // Spacer to push cards to top
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
        }
    }
}