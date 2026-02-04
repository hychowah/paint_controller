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
                        text: "Loop: " + (teensyController.all_status.loop_time || 0).toFixed(0) + "us"
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
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 48
                    color: teensyController.all_status.relay_on ? "#2ecc71" : "#7f8c8d"
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: teensyController.all_status.relay_on ? "RELAY ON" : "RELAY OFF"
                        font.pixelSize: 14
                        font.family: "Roboto"
                        font.bold: true
                        color: "#FFFFFF"
                    }
                }
                
                // Enable Status Badge
                Rectangle {
                    Layout.preferredWidth: 180
                    Layout.preferredHeight: 48
                    color: teensyController.all_status.enabled ? "#2ecc71" : "#7f8c8d"
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: teensyController.all_status.enabled ? "SYSTEM ENABLED" : "SYSTEM DISABLED"
                        font.pixelSize: 14
                        font.family: "Roboto"
                        font.bold: true
                        color: "#FFFFFF"
                    }
                }
            }
        }
        
        // RIGHT SECTION: Exit Button
        Button {
            id: exitButton
            Layout.preferredWidth: 120
            Layout.preferredHeight: 60
            
            // IMPORTANT: Prevent keyboard focus to avoid accidental activation from other windows
            // But still allow mouse clicks
            focusPolicy: Qt.ClickFocus  // Only get focus on mouse click, not keyboard navigation
            activeFocusOnTab: false
            
            background: Rectangle {
                color: exitButton.pressed ? "#c0392b" : "#FF5733"
                radius: 8
                border.color: "#a93226"
                border.width: 2
            }
            
            contentItem: Text {
                text: "EXIT"
                font.pixelSize: 20
                font.family: "Roboto"
                font.bold: true
                color: "#FFFFFF"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            
            // Block keyboard activation (Space/Enter) but allow mouse clicks
            Keys.onPressed: function(event) {
                if (event.key === Qt.Key_Space || event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                    event.accepted = true  // Block Space and Enter keys
                }
            }
            
            onClicked: {
                console.log("EXIT button clicked - starting shutdown timer")
                exitTimer.start()
            }
        }
        
        Timer {
            id: exitTimer
            interval: 1000
            onTriggered: {
                console.log("Exiting application via EXIT button")
                Qt.quit()
            }
        }
    }
}
