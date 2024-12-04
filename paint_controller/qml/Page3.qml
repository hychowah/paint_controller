import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page3Rect
    objectName: "page3Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Helper function to update available options
    // Store the complete list of options
    property var allControlOptions: ["None", "Winch Speed", "Wheel Speed", "EF arm", "EF top rail", "EF Prop"]
    
    // Properties to store current selections
    property string leftCurrentControl: "None"
    property string rightCurrentControl: "None"

    // Helper function to get available options for a combo box
    function getAvailableOptions(isLeftComboBox) {
        let otherSelection = isLeftComboBox ? rightCurrentControl : leftCurrentControl
        return allControlOptions.filter(option => 
            option === "None" || option !== otherSelection
        )
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Left Side: Winch Status
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                Label {
                    text: "Winch Status"
                    font.pixelSize: 24
                    font.bold: true
                    Layout.alignment: Qt.AlignTop
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    Label { text: "Status:"; font.bold: true }
                    Label { 
                        text: uiData.winch_available ? "Connected" : "Disconnected"
                        color: uiData.winch_available ? "green" : "red"
                    }

                    Label { text: "Enable Winch:"; font.bold: true }
                    RowLayout {
                        Switch {
                            id: winchEnableSwitch
                            checked: uiData.winch_enabled
                            onToggled: backend.setWinchEnabled(checked)
                        }
                        Label {
                            text: winchEnableSwitch.checked ? "Enabled" : "Disabled"
                            color: winchEnableSwitch.checked ? "green" : "red"
                        }
                    }

                    Label { text: "Cable Length:"; font.bold: true }
                    Label { text: uiData.winch_length + " m" }

                    Label { text: "Cable Speed:"; font.bold: true }
                    Label { text: uiData.winch_speed + " m/s" }

                    Label { text: "Torque:"; font.bold: true }
                    Label { text: uiData.winch_torque + " Nm" }

                    Label { text: "Temperature:"; font.bold: true }
                    Label { text: uiData.winch_temperature + " °C" }

                    Label { text: "Voltage:"; font.bold: true }
                    Label { text: uiData.winch_voltage + " V" }

                    Label { text: "Brake:"; font.bold: true }
                    Label { 
                        text: uiData.winch_brake ? "Engaged" : "Released"
                        color: uiData.winch_brake ? "red" : "green"
                    }
                }
            }
        }

        // Right Side: Steam Deck Input Status
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                Label {
                    text: "Steam Deck Input"
                    font.pixelSize: 24
                    font.bold: true
                }

                // Control Mapping Section
                 GroupBox {
                    title: "Control Mapping"
                    Layout.fillWidth: true

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Label {
                                text: "Left Joystick:"
                                font.bold: true
                            }

                            ComboBox {
                                id: leftJoystickMapping
                                Layout.fillWidth: true
                                model: getAvailableOptions(true)
                                currentIndex: model.indexOf(leftCurrentControl)
                                
                                onActivated: {
                                    let newValue = model[currentIndex]
                                    if (newValue !== leftCurrentControl) {
                                        leftCurrentControl = newValue
                                        backend.setLeftJoystickControl(newValue)
                                        // Update right combo box model
                                        rightJoystickMapping.model = getAvailableOptions(false)
                                        rightJoystickMapping.currentIndex = rightJoystickMapping.model.indexOf(rightCurrentControl)
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Label {
                                text: "Right Joystick:"
                                font.bold: true
                            }

                            ComboBox {
                                id: rightJoystickMapping
                                Layout.fillWidth: true
                                model: getAvailableOptions(false)
                                currentIndex: model.indexOf(rightCurrentControl)
                                
                                onActivated: {
                                    let newValue = model[currentIndex]
                                    if (newValue !== rightCurrentControl) {
                                        rightCurrentControl = newValue
                                        backend.setRightJoystickControl(newValue)
                                        // Update left combo box model
                                        leftJoystickMapping.model = getAvailableOptions(true)
                                        leftJoystickMapping.currentIndex = leftJoystickMapping.model.indexOf(leftCurrentControl)
                                    }
                                }
                            }
                        }
                    }
                }

                // Input Status Display
                GridLayout {
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    // Analog Sticks
                    Label { text: "Left Stick:"; font.bold: true }
                    Label { text: "X: " + uiData.left_joystick_x + ", Y: " + uiData.left_joystick_y }

                    Label { text: "Right Stick:"; font.bold: true }
                    Label { text: "X: " + uiData.right_joystick_x + ", Y: " + uiData.right_joystick_y }

                    // Triggers
                    Label { text: "Left Trigger:"; font.bold: true }
                    Label { text: uiData.left_trigger }

                    Label { text: "Right Trigger:"; font.bold: true }
                    Label { text: uiData.right_trigger }

                    // Face Buttons
                    Label { text: "A Button:"; font.bold: true }
                    Label { 
                        text: uiData.button_a ? "Pressed" : "Released"
                        color: uiData.button_a ? "green" : "gray"
                    }

                    Label { text: "B Button:"; font.bold: true }
                    Label { 
                        text: uiData.button_b ? "Pressed" : "Released"
                        color: uiData.button_b ? "green" : "gray"
                    }

                    Label { text: "X Button:"; font.bold: true }
                    Label { 
                        text: uiData.button_x ? "Pressed" : "Released"
                        color: uiData.button_x ? "green" : "gray"
                    }

                    Label { text: "Y Button:"; font.bold: true }
                    Label { 
                        text: uiData.button_y ? "Pressed" : "Released"
                        color: uiData.button_y ? "green" : "gray"
                    }

                    // Shoulder Buttons
                    Label { text: "L1 Button:"; font.bold: true }
                    Label { 
                        text: uiData.button_l1 ? "Pressed" : "Released"
                        color: uiData.button_l1 ? "green" : "gray"
                    }

                    Label { text: "R1 Button:"; font.bold: true }
                    Label { 
                        text: uiData.button_r1 ? "Pressed" : "Released"
                        color: uiData.button_r1 ? "green" : "gray"
                    }

                    // D-Pad
                    Label { text: "D-Pad:"; font.bold: true }
                    RowLayout {
                        spacing: 5
                        Label { 
                            text: "↑"
                            color: uiData.dpad_up ? "red" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "↓"
                            color: uiData.dpad_down ? "red" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "←"
                            color: uiData.dpad_left ? "red" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "→"
                            color: uiData.dpad_right ? "red" : "gray"
                            font.bold: true
                        }
                    }

                    // Menu Button
                    Label { text: "Menu:"; font.bold: true }
                    Label { 
                        text: uiData.menu_pressed ? "Pressed" : "Released"
                        color: uiData.menu_pressed ? "green" : "gray"
                    }

                    // IMU Data
                    Label { text: "IMU:"; font.bold: true }
                    Label { text: "Pitch: " + uiData.imu_pitch + "°, Roll: " + uiData.imu_roll + "°, Yaw: " + uiData.imu_yaw + "°" }
                }
            }
        }
    }
}