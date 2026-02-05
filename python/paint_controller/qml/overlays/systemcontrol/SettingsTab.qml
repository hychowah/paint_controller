import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../components/buttons"
import "../../components/panels"
import "../../components/inputs"

Item {
    id: settingsTab
    
    // Popup reference passed from parent
    property var confirmationPopup: null
    
    // Helper function to create setting input field
    function createSettingRow(key, label, currentValue, minVal, maxVal, isFloat) {
        // This is handled inline in the repeater below
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 15
        
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
        
        // Scrollable settings content
        ScrollView {
            id: settingsScrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            
            ColumnLayout {
                width: settingsScrollView.width - 20
                spacing: 15
                
                // ==========================================
                // Winch Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "Winch Settings"
                    description: "Configure winch motor parameters"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            implicitHeight: childrenRect.height
                            
                            SettingInputField {
                                label: "Max Speed (Range: 0 - 100 RPM)"
                                settingKey: "winch_max_speed_mmps"
                                decimalPlaces: 1
                                unitSuffix: " mm/s"
                                defaultValue: "400.0"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                        }
                    }
                }
                
                // ==========================================
                // Track Control Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "Track Control"
                    description: "Configure track/wheel speed parameters"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            implicitHeight: childrenRect.height
                            
                            SettingInputField {
                                label: "Max Speed (Range: 5 - 50)"
                                settingKey: "track_max_speed"
                                decimalPlaces: 1
                                defaultValue: "25.0"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                            
                            SettingInputField {
                                label: "Min Speed (Range: 0 - 30)"
                                settingKey: "track_min_speed"
                                decimalPlaces: 1
                                defaultValue: "15.0"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                            
                            SettingInputField {
                                label: "Wheel Travel Max Distance (Range: 100 - 1000 mm)"
                                settingKey: "wheel_travel_max"
                                decimalPlaces: 0
                                unitSuffix: " mm"
                                defaultValue: "500"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                            
                            SettingInputField {
                                label: "Wheel Travel Rate (Range: 10 - 500 mm/sec)"
                                settingKey: "wheel_travel_rate"
                                decimalPlaces: 0
                                unitSuffix: " mm/sec"
                                defaultValue: "100"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                            
                            SettingInputField {
                                label: "Wheel Travel Speed (Range: 50 - 600 RPM)"
                                settingKey: "wheel_travel_rpm"
                                decimalPlaces: 0
                                unitSuffix: " RPM"
                                defaultValue: "300"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                        }
                    }
                }
                
                // ==========================================
                // End Effector Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "End Effector"
                    description: "Configure thrust force and valve parameters"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            implicitHeight: childrenRect.height
                            
                            // Thrust Force - kept inline due to special teensyController logic
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Thrust Force (Range: -1.0 to +1.0)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: thrustForceInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: thrustForceInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.thrust_force.toFixed(2) : "-1.00"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = thrustForceInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: thrustForceSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: thrustForceSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(thrustForceInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.thrust_force = num
                                                    // Also update teensyController for immediate effect
                                                    if (teensyController) {
                                                        teensyController.thrust_force = num
                                                    }
                                                    settingsManager.saveSetting("thrust_force")
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Thrust Ramp Rate - kept inline due to special clamping logic
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Thrust Ramp Rate (thrust/second, Range: 0.1 - 10.0)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                Text {
                                    text: "Controls how fast thrust force ramps up/down (1.0 = 0 to max in 1 second)"
                                    color: "#AAAAAA"
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: thrustRampRateInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: thrustRampRateInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.thrust_ramp_rate.toFixed(2) : "1.00"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = thrustRampRateInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: thrustRampRateSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: thrustRampRateSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(thrustRampRateInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    // Clamp to valid range (0.1 - 10.0)
                                                    num = Math.max(0.1, Math.min(10.0, num))
                                                    settingsManager.thrust_ramp_rate = num
                                                    thrustRampRateInput.text = num.toFixed(2)  // Update display with clamped value
                                                    settingsManager.saveSetting("thrust_ramp_rate")
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            SettingInputField {
                                label: "Valve Turn Max (Range: 0 - 10)"
                                settingKey: "valve_turn_max"
                                decimalPlaces: 1
                                defaultValue: "6.0"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                        }
                    }
                }
                
                // ==========================================
                // Arm Extension Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "Arm Extension Presets"
                    description: "Configure arm retract/extend positions"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            implicitHeight: childrenRect.height
                            
                            SettingInputField {
                                label: "Retract Position (Range: 0 - 1000)"
                                settingKey: "arm_retract_length"
                                decimalPlaces: 0
                                defaultValue: "250"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                            
                            SettingInputField {
                                label: "Extend Position (Range: 0 - 1500)"
                                settingKey: "arm_extend_length"
                                decimalPlaces: 0
                                defaultValue: "800"
                                numberPadTarget: numberPad
                                confirmationPopup: confirmationPopup
                            }
                        }
                    }
                }
                
                // Bottom spacer
                Item {
                    Layout.fillWidth: true
                    height: 20
                }
            }
        }
    }
    
    // Numpad component for number input
    NumpadNew {
        id: numberPad
    }
}
