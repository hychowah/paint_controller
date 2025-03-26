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
    property var allControlOptions: ["None", "Winch Speed", "Wheel Speed", "EF arm", "EF top rail", "EF prop pwm", "EF prop joint", "EF spray trigger", "EF spray gimbal"]
    
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
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                RowLayout {
                    spacing: 10
                    Label {
                        text: "Winch Status"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    // rectange for spacing
                    Rectangle {
                        Layout.fillWidth: true
                    }
                    TouchSwitch {
                            id: winchEnableSwitch
                            checked: winchController.enabled
                            onToggled: winchController.setEnabled(checked)
                    }
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
                        text: winchController.available ? "Connected" : "Disconnected"
                        color: winchController.available ? "green" : "red"
                    }

                    Label { text: "Enable Winch:"; font.bold: true }
                    RowLayout {
                        
                    }

                    Label { text: "Cable Length:"; font.bold: true }
                    Label { text: String((winchController.cable_length).toFixed(0)) + " mm" }

                    Label {text: "Cable Speed:"; font.bold: true}
                    Label {text: String(winchController.cable_speed) + " m/s"}

                    Label { text: "Torque:"; font.bold: true }
                    Label { text: String(winchController.winch_torque) + " Nm" }

                    Label { text: "Temperature:"; font.bold: true }
                    Label { text: winchController.motor_temperature + " °C" }

                    Label { text: "Voltage:"; font.bold: true }
                    Label { text: winchController.motor_voltage + " V" }

                    Label { text: "Brake:"; font.bold: true }
                    Label { 
                        text: winchController.motor_brake ? "Engaged" : "Released"
                        color: winchController.motor_brake ? "red" : "green"
                    }

                    Label { text: "Load Detection:"; font.bold: true }
                    Label { 
                        text: winchController.load_detection_enabled ? "True" : "False"
                        color: winchController.load_detection_enabled ? "green" : "red"
                    }

                    Label { text: "Unusual Load:"; font.bold: true }
                    Label { 
                        text: winchController.unusual_load_detected ? "True" : "False"
                        color: winchController.unusual_load_detected ? "green" : "red"
                    }

                    MoveLengthButton {
                        id: moveWinchButton
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                        applicationRoot: page3Rect
                        onArrowAboveClicked: console.log("Arrow above clicked")
                        onArrowBelowClicked: console.log("Arrow below clicked")
                        onInputValueChanged: console.log("Input value changed to:", inputValue)
                        onSliderValueChanged: backend.set_winch_spd_limit(sliderValue)
                    }
                }
            }
        }

        // teensy status
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                RowLayout {
                    spacing: 10
                    Label {
                        text: "Teensy Status"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    // rectange for spacing
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Label { text: "Enable:"; font.bold: true }
                    
                    RowLayout {
                        TouchSwitch {
                            id: teensyEnableSwitch
                            checked: uiData.teensy_enabled
                            onToggled: backend.setTeensyEnabled(checked)
                        }
                    }

                    Label { text: "Relay:"; font.bold: true }
                    
                    RowLayout {
                        TouchSwitch {
                            id: teensyRelayEnableSwitch
                            checked: uiData.teensy_relay_enabled
                            onToggled: backend.setTeensyRelayEnabled(checked)
                        }
                    }
                }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ColumnLayout {
                        spacing: 20

                        // Board Status Section
                        GroupBox {
                            title: "Board Status"
                            Layout.fillWidth: true

                            GridLayout {
                                columns: 4
                                rowSpacing: 10
                                columnSpacing: 20
                                anchors.fill: parent  

                                Label { text: "Voltage:"; font.bold: true }
                                Label { text: uiData.teensy_voltage + " V" }
                                Label { text: "Current:"; font.bold: true }
                                Label { text: uiData.teensy_current + " A" }

                                Label { text: "Temperature:"; font.bold: true }
                                Label { text: uiData.teensy_temperature + " °C" }
                                Label { text: "Runtime:"; font.bold: true }
                                Label { text: uiData.teensy_run_time  }

                                Label { text: "Loop Time:"; font.bold: true }
                                Label { text: uiData.teensy_loop_time + " µs" }
                                Label { text: "Loop Counter:"; font.bold: true }
                                Label { text: uiData.teensy_loop_time_counter }
                            }
                        }

                        // Rail Status Section
                        GroupBox {
                            title: "Rail Status"
                            Layout.fillWidth: true

                            GridLayout {
                                columns: 6
                                rowSpacing: 10
                                columnSpacing: 20
                                Layout.fillWidth: true

                                Label { text: "Top Rail"; font.bold: true; Layout.columnSpan: 6 }
                                Label { text: "Position:" }
                                Label { text: uiData.top_rail_position+ " m" }
                                Label { text: "Speed:" }
                                Label { text: uiData.top_rail_speed + " m/s" }
                                Label { text: "Current:" }
                                Label { text: uiData.top_rail_current + " A" }

                                Label { text: "Arm Rail"; font.bold: true; Layout.columnSpan: 6 }
                                Label { text: "Position:" }
                                Label { text: uiData.arm_rail_position + " m" }
                                Label { text: "Speed:" }
                                Label { text: uiData.arm_rail_speed + " m/s" }
                                Label { text: "Current:" }
                                Label { text: uiData.arm_rail_current + " A" }
                            }
                        }

                        // Propeller Status Section
                        GroupBox {
                            title: "Propeller Status"
                            Layout.fillWidth: true

                            GridLayout {
                                columns: 4
                                rowSpacing: 10
                                columnSpacing: 20
                                Layout.fillWidth: true

                                Label { text: "Left Propeller"; font.bold: true; Layout.columnSpan: 2 }
                                Label { text: "Right Propeller"; font.bold: true; Layout.columnSpan: 2 }

                                Label { text: "Position:" }
                                Label { text: uiData.left_prop_position + "°" }
                                Label { text: "Position:" }
                                Label { text: uiData.right_prop_position + "°" }

                                Label { text: "PWM:" }
                                Label { text: uiData.left_prop_pwm }
                                Label { text: "PWM:" }
                                Label { text: uiData.right_prop_pwm }
                            }
                        }

                        // IMU Status Section
                        GroupBox {
                            title: "IMU Status"
                            Layout.fillWidth: true

                            GridLayout {
                                columns: 6
                                rowSpacing: 10
                                columnSpacing: 20
                                Layout.fillWidth: true

                                Label { text: "Linear Acceleration"; font.bold: true; Layout.columnSpan: 6 }
                                Label { text: "X:" }
                                Label { text: uiData.teensy_imu_acc_x+ " m/s²" }
                                Label { text: "Y:" }
                                Label { text: uiData.teensy_imu_acc_y + " m/s²" }
                                Label { text: "Z:" }
                                Label { text: uiData.teensy_imu_acc_z + " m/s²" }

                                Label { text: "Angular Velocity"; font.bold: true; Layout.columnSpan: 6 }
                                Label { text: "X:" }
                                Label { text: uiData.teensy_imu_angular_acc_x + " rad/s" }
                                Label { text: "Y:" }
                                Label { text: uiData.teensy_imu_angular_acc_y + " rad/s" }
                                Label { text: "Z:" }
                                Label { text: uiData.teensy_imu_angular_acc_z + " rad/s" }

                                Label { text: "Orientation"; font.bold: true; Layout.columnSpan: 6 }
                                Label { text: "Pitch:" }
                                Label { text: uiData.teensy_imu_pitch }
                                Label { text: "Roll:" }
                                Label { text: uiData.teensy_imu_roll }
                                Label { text: "Yaw:" }
                                Label { text: uiData.teensy_imu_yaw }
                            }
                        }
                    }
                }
            }
        }

        // Right Side: Steam Deck Input Status
        Rectangle {
            Layout.preferredWidth: parent.width / 4
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

                    ColumnLayout {
                        height: 80
                        anchors.fill: parent
                        spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Label {
                                text: "Left:"
                                font.bold: true
                            }

                            ComboBox {
                                id: leftJoystickMapping
                                model: getAvailableOptions(true)
                                currentIndex: model.indexOf(leftCurrentControl)
                                Layout.preferredHeight: 40
                                
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
                                text: "Right:"
                                font.bold: true
                            }

                            ComboBox {
                                id: rightJoystickMapping
                                model: getAvailableOptions(false)
                                currentIndex: model.indexOf(rightCurrentControl)
                                Layout.preferredHeight: 40
                                
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

                }
            }
        }
    }
}