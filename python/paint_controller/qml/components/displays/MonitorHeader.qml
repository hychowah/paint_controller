// Monitor Header - Telemetry, Status Badges, and Emergency Stop
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"

Rectangle {
    id: headerBar
    height: 80
    color: CommonStyle.backgroundL1
    radius: CommonStyle.radiusMd
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: CommonStyle.spacingSm + 2
        spacing: CommonStyle.spacingXl - CommonStyle.spacingXs
        
        // LEFT SECTION: Telemetry
        RowLayout {
            Layout.preferredWidth: 350
            spacing: CommonStyle.spacingLg - 1
            
            // Voltage indicator
            Rectangle {
                Layout.preferredWidth: 110
                Layout.fillHeight: true
                color: CommonStyle.cardBackground
                radius: CommonStyle.radiusSm
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: "⚡"
                        font.pixelSize: CommonStyle.fontHeading + 2
                        color: CommonStyle.accentPrimary
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: (teensyController.all_status.voltage || 0).toFixed(1) + "V"
                        font.pixelSize: CommonStyle.fontHeading
                        font.family: CommonStyle.fontMono
                        font.bold: true
                        color: CommonStyle.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
            
            // Temperature indicator
            Rectangle {
                Layout.preferredWidth: 110
                Layout.fillHeight: true
                color: CommonStyle.cardBackground
                radius: CommonStyle.radiusSm
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: "🌡️"
                        font.pixelSize: CommonStyle.fontHeading + 2
                        color: CommonStyle.statusWarning
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: (teensyController.all_status.temperature || 0).toFixed(0) + "°C"
                        font.pixelSize: CommonStyle.fontHeading
                        font.family: CommonStyle.fontMono
                        font.bold: true
                        color: CommonStyle.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
            
            // Loop time indicator
            Rectangle {
                Layout.preferredWidth: 110
                Layout.fillHeight: true
                color: CommonStyle.cardBackground
                radius: CommonStyle.radiusSm
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 4
                    
                    Text {
                        text: "⏱️"
                        font.pixelSize: CommonStyle.fontHeading + 2
                        color: CommonStyle.statusSuccess
                        horizontalAlignment: Text.AlignHCenter
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: "Loop: " + (teensyController.all_status.loop_time || 0).toFixed(0) + "us"
                        font.pixelSize: CommonStyle.fontBody
                        font.family: CommonStyle.fontMono
                        font.bold: true
                        color: CommonStyle.textPrimary
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
                spacing: CommonStyle.spacingMd
                
                // Relay Status Badge
                Rectangle {
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 48
                    color: teensyController.all_status.relay_on ? CommonStyle.statusSuccess : CommonStyle.textDisabled
                    radius: CommonStyle.radiusSm
                    
                    Text {
                        anchors.centerIn: parent
                        text: teensyController.all_status.relay_on ? "RELAY ON" : "RELAY OFF"
                        font.pixelSize: CommonStyle.fontBody
                        font.family: CommonStyle.fontSans
                        font.bold: true
                        color: CommonStyle.textPrimary
                    }
                }
                
                // Enable Status Badge
                Rectangle {
                    Layout.preferredWidth: 180
                    Layout.preferredHeight: 48
                    color: teensyController.all_status.enabled ? CommonStyle.statusSuccess : CommonStyle.textDisabled
                    radius: CommonStyle.radiusSm
                    
                    Text {
                        anchors.centerIn: parent
                        text: teensyController.all_status.enabled ? "SYSTEM ENABLED" : "SYSTEM DISABLED"
                        font.pixelSize: CommonStyle.fontBody
                        font.family: CommonStyle.fontSans
                        font.bold: true
                        color: CommonStyle.textPrimary
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
                color: exitButton.pressed ? CommonStyle.buttonPressed : CommonStyle.buttonDanger
                radius: CommonStyle.radiusSm
                border.color: CommonStyle.statusError
                border.width: 2
            }
            
            contentItem: Text {
                text: "EXIT"
                font.pixelSize: CommonStyle.fontHeading
                font.family: CommonStyle.fontSans
                font.bold: true
                color: CommonStyle.textPrimary
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
