import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../components/buttons"
import "../../components/panels"
import "../../components/inputs"
import "../../components/popups"

Item {
    id: settingsTab

    ColumnLayout {
        anchors.fill: parent
        spacing: 20
        
        // Header
        Item {
            Layout.fillWidth: true
            height: 32
            
            Text {
                text: "Settings"
                color: "#FFFFFF"
                font.family: "Helvetica"
                font.pixelSize: 18
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            
            Rectangle {
                height: 1
                width: parent.width - 180
                color: "#333333"
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        
        // Settings content
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#252A36"
            border.color: "#3A5A8C"
            border.width: 1
            radius: 10
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20
                
                // Thrust Force Control Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 15
                    
                    // Title
                    Text {
                        Layout.fillWidth: true
                        text: "Thrust Force Control"
                        color: "#FFFFFF"
                        font.pixelSize: 16
                        font.bold: true
                    }
                    
                    Text {
                        Layout.fillWidth: true
                        text: "Configure the thrust force for vertical movement"
                        color: "#AAAAAA"
                        font.pixelSize: 12
                    }
                    
                    // Force value input
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Text {
                            text: "Force Value (Range: -1.0 to +1.0)"
                            color: "#FFFFFF"
                            font.pixelSize: 14
                            font.bold: true
                        }
                        
                        // Input field with numpad button
                        Rectangle {
                            Layout.fillWidth: true
                            height: 50
                            color: "#1A1A1A"
                            border.color: thrustValueInput.activeFocus ? "#3A5A8C" : "#333333"
                            border.width: 1
                            radius: 6
                            
                            Behavior on border.color {
                                ColorAnimation { duration: 150 }
                            }
                            
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 0
                                spacing: 0
                                
                                TextInput {
                                    id: thrustValueInput
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    leftPadding: 15
                                    rightPadding: 10
                                    text: teensyController.thrust_force.toFixed(2)
                                    color: "#FFFFFF"
                                    font.pixelSize: 14
                                    verticalAlignment: TextInput.AlignVCenter
                                    horizontalAlignment: TextInput.AlignRight
                                    selectByMouse: true
                                    
                                    onTextChanged: {
                                        // Allow only numbers, minus sign, and decimal point
                                        var filtered = text.replace(/[^0-9.\-]/g, '')
                                        
                                        // Ensure only one minus at start
                                        if (filtered.indexOf('-') !== filtered.lastIndexOf('-')) {
                                            filtered = filtered.replace(/-/g, '')
                                        }
                                        if (filtered.indexOf('-') > 0) {
                                            filtered = filtered.replace('-', '')
                                        }
                                        
                                        // Ensure only one decimal point
                                        if (filtered.indexOf('.') !== filtered.lastIndexOf('.')) {
                                            filtered = filtered.substring(0, filtered.lastIndexOf('.'))
                                        }
                                        
                                        if (text !== filtered) {
                                            text = filtered
                                            return
                                        }
                                        
                                        // Update backend when text changes
                                        var num = parseFloat(text)
                                        if (!isNaN(num) && text !== "") {
                                            teensyController.thrust_force = num
                                        }
                                    }
                                    
                                    onActiveFocusChanged: {
                                        if (activeFocus) {
                                            numberPad.targetField = thrustValueInput
                                            numberPad.open()
                                        }
                                    }
                                }
                                
                                // Numpad button in input field
                                Rectangle {
                                    Layout.preferredWidth: 45
                                    Layout.fillHeight: true
                                    color: numpadButtonArea.containsMouse ? "#2A3F60" : "transparent"
                                    radius: 6
                                    
                                    Behavior on color {
                                        ColorAnimation { duration: 150 }
                                    }
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "🔢"
                                        font.pixelSize: 16
                                        color: "#CCCCCC"
                                    }
                                    
                                    MouseArea {
                                        id: numpadButtonArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            numberPad.targetField = thrustValueInput
                                            numberPad.open()
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Quick preset buttons
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            
                            Item {
                                Layout.fillWidth: true
                            }
                            
                            // Set button
                            Rectangle {
                                width: 100
                                height: 45
                                radius: 6
                                color: setButtonArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                border.color: "#4CAF50"
                                border.width: 1
                                
                                Behavior on color {
                                    ColorAnimation { duration: 150 }
                                }
                                
                                MouseArea {
                                    id: setButtonArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        var num = parseFloat(thrustValueInput.text)
                                        if (!isNaN(num)) {
                                            teensyController.thrust_force = num
                                            console.log("Thrust force set to:", num)
                                            
                                            // Show confirmation popup
                                            confirmationPopup.messageTitle = "Success"
                                            confirmationPopup.messageText = "Thrust force set to " + num.toFixed(2)
                                            confirmationPopup.messageType = "info"
                                            confirmationPopup.open()
                                        }
                                    }
                                }
                                
                                RowLayout {
                                    anchors.centerIn: parent
                                    spacing: 8
                                    
                                    Text {
                                        text: "✓"
                                        color: "#FFFFFF"
                                        font.pixelSize: 14
                                        font.bold: true
                                    }
                                    
                                    Text {
                                        text: "Set"
                                        color: "#FFFFFF"
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Spacer
                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }
    
    // Numpad component for number input
    NumpadNew {
        id: numberPad
    }
    
    // Confirmation popup for settings
    CustomPopup {
        id: confirmationPopup
        width: 400
        height: 180
        dismissDelay: 2000
    }
}
