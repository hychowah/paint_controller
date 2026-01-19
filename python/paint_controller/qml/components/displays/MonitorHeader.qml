// Monitor Header - Telemetry, Status Badges, and Emergency Stop
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: headerBar
    height: 80
    color: "#252a35"
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 20
        
        // LEFT SECTION: Telemetry
        RowLayout {
            Layout.preferredWidth: 350
            spacing: 15
            
            // Voltage indicator
            Rectangle {
                Layout.preferredWidth: 110
                Layout.fillHeight: true
                color: "#29303b"
                radius: 6
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: "⚡"
                        font.pixelSize: 22
                        color: "#3498db"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: (teensyController.all_status.voltage || 0).toFixed(1) + "V"
                        font.pixelSize: 20
                        font.family: "Monospace"
                        font.bold: true
                        color: "#FFFFFF"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
            
            // Temperature indicator
            Rectangle {
                Layout.preferredWidth: 110
                Layout.fillHeight: true
                color: "#29303b"
                radius: 6
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: "🌡️"
                        font.pixelSize: 22
                        color: "#f39c12"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: (teensyController.all_status.temperature || 0).toFixed(0) + "°C"
                        font.pixelSize: 20
                        font.family: "Monospace"
                        font.bold: true
                        color: "#FFFFFF"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
            
            // Loop time indicator
            Rectangle {
                Layout.preferredWidth: 110
                Layout.fillHeight: true
                color: "#29303b"
                radius: 6
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: "⏱️"
                        font.pixelSize: 22
                        color: "#2ecc71"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: "Loop: " + (teensyController.all_status.loop_time || 0).toFixed(0) + "ms"
                        font.pixelSize: 16
                        font.family: "Monospace"
                        font.bold: true
                        color: "#FFFFFF"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }
        
        // MIDDLE SECTION: Status Badges (PASSIVE)
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 12
                
                // Relay Status Badge
                Rectangle {
                    Layout.preferredWidth: 110
                    Layout.preferredHeight: 38
                    color: "transparent"
                    border.color: teensyController.all_status.relay_on ? "#2ecc71" : "#7f8c8d"
                    border.width: 2
                    radius: 6
                    
                    Text {
                        anchors.centerIn: parent
                        text: "RELAY: " + (teensyController.all_status.relay_on ? "ON" : "OFF")
                        font.pixelSize: 13
                        font.family: "Roboto"
                        font.bold: true
                        color: teensyController.all_status.relay_on ? "#2ecc71" : "#7f8c8d"
                    }
                }
                
                // Enable Status Badge
                Rectangle {
                    Layout.preferredWidth: 190
                    Layout.preferredHeight: 52
                    color: teensyController.all_status.enabled ? "#2ecc71" : "#7f8c8d"
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: teensyController.all_status.enabled ? "SYSTEM ENABLED" : "SYSTEM DISABLED"
                        font.pixelSize: 15
                        font.family: "Roboto"
                        font.bold: true
                        color: "#FFFFFF"
                    }
                }
            }
        }
        
        // RIGHT SECTION: Emergency Stop
        Button {
            id: emergencyStopButton
            Layout.preferredWidth: 200
            Layout.preferredHeight: 60
            
            background: Rectangle {
                color: emergencyStopButton.pressed ? "#c0392b" : "#e74c3c"
                radius: 8
                border.color: "#a93226"
                border.width: 3
                
                SequentialAnimation on opacity {
                    running: true
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.85; duration: 1000 }
                    NumberAnimation { to: 1.0; duration: 1000 }
                }
                
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -2
                    color: "transparent"
                    border.color: "#00000040"
                    border.width: 2
                    radius: 10
                    z: -1
                }
            }
            
            contentItem: Text {
                text: "EMERGENCY STOP"
                font.pixelSize: 17
                font.family: "Roboto"
                font.bold: true
                font.letterSpacing: 1.5
                color: "#FFFFFF"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            
            onClicked: {
                console.log("EMERGENCY STOP ACTIVATED")
                if (typeof teensyController !== 'undefined') {
                    teensyController.setEnabled(false)
                }
                if (typeof wheelController !== 'undefined') {
                    wheelController.setEnabled(false)
                }
                if (typeof winchController !== 'undefined') {
                    winchController.setEnabled(false)
                }
            }
        }
    }
}
