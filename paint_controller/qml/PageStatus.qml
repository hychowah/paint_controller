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
                spacing: 10 // Reduced spacing for more content

                RowLayout {
                    spacing: 10
                    Label {
                        text: "Teensy Status"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    // rectangle for spacing
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

                // TabBar to organize content in categories
                TabBar {
                    id: teensynStatusTabs
                    Layout.fillWidth: true
                    
                    TabButton {
                        text: "Main"
                        width: implicitWidth
                    }
                    TabButton {
                        text: "Rails"
                        width: implicitWidth
                    }
                    TabButton {
                        text: "Propellers"
                        width: implicitWidth
                    }
                    TabButton {
                        text: "IMU"
                        width: implicitWidth
                    }
                }

                // StackLayout to show different pages based on selected tab
                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: teensynStatusTabs.currentIndex

                    // Main Tab - Board Status and Warnings
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: parent.width
                            spacing: 10
                            
                            // Board Status Section
                            GroupBox {
                                title: "Board Status"
                                Layout.fillWidth: true

                                GridLayout {
                                    columns: 4
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    anchors.fill: parent  

                                    Label { text: "Voltage:"; font.bold: true }
                                    Label { text: teensyController.all_status.voltage.toFixed(1) + " V" }
                                    Label { text: "Current:"; font.bold: true }
                                    Label { text: teensyController.all_status.current.toFixed(1) + " A" }

                                    Label { text: "Temperature:"; font.bold: true }
                                    Label { text: teensyController.all_status.temperature.toFixed(1) + " °C" }
                                    Label { text: "Runtime:"; font.bold: true }
                                    Label { text: teensyController.all_status.voltage.toFixed(1)  }

                                    Label { text: "Loop Time:"; font.bold: true }
                                    Label { text: teensyController.all_status.loop_time.toFixed(0) + " µs" }
                                    Label { text: "Loop Counter:"; font.bold: true }
                                    Label { text: teensyController.all_status.loop_time_counter.toFixed(0) }
                                    
                                    // New fields can be added here
                                    Label { text: "Battery:"; font.bold: true }
                                    Label { text: "87%" }
                                    Label { text: "Status:"; font.bold: true }
                                    Label { text: "Operating" }
                                }
                            }
                            
                            // System Alerts/Warnings section (new)
                            GroupBox {
                                title: "System Alerts"
                                Layout.fillWidth: true
                                
                                ListView {
                                    implicitHeight: 80
                                    Layout.fillWidth: true
                                    model: ListModel {
                                        ListElement { message: "Temperature Warning"; severity: "warning" }
                                        ListElement { message: "Voltage Level Low"; severity: "warning" }
                                    }
                                    delegate: Rectangle {
                                        width: parent.width
                                        height: 24
                                        color: index % 2 ? "#F0F0F0" : "transparent"
                                        
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 5
                                            spacing: 10
                                            
                                            Rectangle {
                                                width: 12
                                                height: 12
                                                radius: 6
                                                color: model.severity === "error" ? "red" : 
                                                    model.severity === "warning" ? "orange" : "green"
                                            }
                                            
                                            Label { text: model.message }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // Rails Tab
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: parent.width
                            spacing: 10
                            
                            // Top Rail Status - More detailed
                            GroupBox {
                                title: "Top Rail"
                                Layout.fillWidth: true

                                GridLayout {
                                    columns: 4
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    Layout.fillWidth: true

                                    Label { text: "Position:" }
                                    Label { text: teensyController.all_status.top_rail_position.toFixed(0) + " cnt" }
                                    Label { text: "Speed:" }
                                    Label { text: teensyController.all_status.top_rail_speed.toFixed(0) + " m/s" }

                                    Label { text: "Current:" }
                                    Label { text: teensyController.all_status.top_rail_current.toFixed(0) + " A" }
                                    Label { text: "Target:" }
                                    Label { text: "18000 cnt" }
                                    
                                    Label { text: "Limit Switch:" }
                                    Label { text: "Not Triggered" }
                                    Label { text: "Home:" }
                                    Label { text: "Yes" }
                                    
                                    Label { text: "Error:" }
                                    Label { text: "± 5 cnt" }
                                    Label { text: "Status:" }
                                    Label { text: "Moving" }
                                }
                            }

                            // Arm Rail Status - More detailed
                            GroupBox {
                                title: "Arm Rail"
                                Layout.fillWidth: true

                                GridLayout {
                                    columns: 4
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    Layout.fillWidth: true

                                    Label { text: "Position:" }
                                    Label { text: teensyController.all_status.arm_rail_position.toFixed(0) + " m" }
                                    Label { text: "Speed:" }
                                    Label { text: teensyController.all_status.arm_rail_speed.toFixed(0) + " m/s" }

                                    Label { text: "Current:" }
                                    Label { text: teensyController.all_status.arm_rail_current.toFixed(0) + " A" }
                                    Label { text: "Target:" }
                                    Label { text: "8000 m" }
                                    
                                    Label { text: "Limit Switch:" }
                                    Label { text: "Not Triggered" }
                                    Label { text: "Home:" }
                                    Label { text: "No" }
                                    
                                    Label { text: "Error:" }
                                    Label { text: "± 0.5 m" }
                                    Label { text: "Status:" }
                                    Label { text: "Idle" }
                                }
                            }
                        }
                    }
                    
                    // Propellers Tab
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: parent.width
                            spacing: 10
                            
                            // Enhanced Propeller Status
                            GroupBox {
                                title: "Propeller Status"
                                Layout.fillWidth: true

                                GridLayout {
                                    columns: 4
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    Layout.fillWidth: true

                                    Label { text: "Left Propeller"; font.bold: true; Layout.columnSpan: 2 }
                                    Label { text: "Right Propeller"; font.bold: true; Layout.columnSpan: 2 }

                                    Label { text: "Position:" }
                                    Label { text: teensyController.all_status.left_prop_position.toFixed(0) + "°" }
                                    Label { text: "Position:" }
                                    Label { text: teensyController.all_status.right_prop_position.toFixed(0) + "°" }

                                    Label { text: "PWM:" }
                                    Label { text: teensyController.all_status.left_prop_pwm.toFixed(0) }
                                    Label { text: "PWM:" }
                                    Label { text: teensyController.all_status.right_prop_pwm.toFixed(0) }
                                    
                                    Label { text: "Current:" }
                                    Label { text: "2.4 A" }
                                    Label { text: "Current:" }
                                    Label { text: "2.6 A" }
                                    
                                    Label { text: "Target:" }
                                    Label { text: "-300°" }
                                    Label { text: "Target:" }
                                    Label { text: "-450°" }
                                    
                                    Label { text: "Status:" }
                                    Label { text: "Running" }
                                    Label { text: "Status:" }
                                    Label { text: "Running" }
                                    
                                    Label { text: "Temp:" }
                                    Label { text: "34°C" }
                                    Label { text: "Temp:" }
                                    Label { text: "36°C" }
                                }
                            }
                            
                            // Propeller Performance
                            GroupBox {
                                title: "Propeller Performance"
                                Layout.fillWidth: true
                                
                                GridLayout {
                                    columns: 4
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    Layout.fillWidth: true
                                    
                                    Label { text: "Left Efficiency:" }
                                    Label { text: "86%" }
                                    Label { text: "Right Efficiency:" }
                                    Label { text: "83%" }
                                    
                                    Label { text: "Left RPM:" }
                                    Label { text: "1200" }
                                    Label { text: "Right RPM:" }
                                    Label { text: "1180" }
                                }
                            }
                        }
                    }
                    
                    // IMU Tab
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: parent.width
                            spacing: 10
                            
                            // Enhanced IMU Status
                            GroupBox {
                                title: "Linear Acceleration"
                                Layout.fillWidth: true

                                GridLayout {
                                    columns: 6
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    Layout.fillWidth: true

                                    Label { text: "X:" }
                                    Label { text: teensyController.all_status.imu_acc_x + " m/s²" }
                                    Label { text: "Y:" }
                                    Label { text: teensyController.all_status.imu_acc_y + " m/s²" }
                                    Label { text: "Z:" }
                                    Label { text: teensyController.all_status.imu_acc_z + " m/s²" }
                                    
                                    Label { text: "Max X:" }
                                    Label { text: "±12 m/s²" }
                                    Label { text: "Max Y:" }
                                    Label { text: "±12 m/s²" }
                                    Label { text: "Max Z:" }
                                    Label { text: "±12 m/s²" }
                                }
                            }

                            GroupBox {
                                title: "Angular Velocity"
                                Layout.fillWidth: true

                                GridLayout {
                                    columns: 6
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    Layout.fillWidth: true

                                    Label { text: "X:" }
                                    Label { text: teensyController.all_status.imu_angular_acc_x + " rad/s" }
                                    Label { text: "Y:" }
                                    Label { text: teensyController.all_status.imu_angular_acc_y + " rad/s" }
                                    Label { text: "Z:" }
                                    Label { text: teensyController.all_status.imu_angular_acc_z + " rad/s" }
                                    
                                    Label { text: "Rate X:" }
                                    Label { text: "Low" }
                                    Label { text: "Rate Y:" }
                                    Label { text: "Low" }
                                    Label { text: "Rate Z:" }
                                    Label { text: "Medium" }
                                }
                            }

                            GroupBox {
                                title: "Orientation"
                                Layout.fillWidth: true

                                GridLayout {
                                    columns: 6
                                    rowSpacing: 8
                                    columnSpacing: 15
                                    Layout.fillWidth: true

                                    Label { text: "Pitch:" }
                                    Label { text: teensyController.all_status.imu_pitch }
                                    Label { text: "Roll:" }
                                    Label { text: teensyController.all_status.imu_roll }
                                    Label { text: "Yaw:" }
                                    Label { text: teensyController.all_status.imu_yaw }
                                    
                                    Label { text: "Stability:" }
                                    Label { text: "Good" }
                                    Label { text: "Calibration:" }
                                    Label { text: "Active" }
                                    Label { text: "Sensor:" }
                                    Label { text: "BNO055" }
                                }
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
                    Label { text: "X: " + steamDeckHandler.left_stick.x.toFixed(0) + ", Y: " + steamDeckHandler.left_stick.y.toFixed(0) }

                    Label { text: "Right Stick:"; font.bold: true }
                    Label { text: "X: " + steamDeckHandler.right_stick.x.toFixed(0) + ", Y: " + steamDeckHandler.right_stick.y.toFixed(0) }

                    // Triggers
                    Label { text: "Left Trigger:"; font.bold: true }
                    Label { text: steamDeckHandler.triggers.left }

                    Label { text: "Right Trigger:"; font.bold: true }
                    Label { text: steamDeckHandler.triggers.right }

                    // Face Buttons
                    Label { text: "A Button:"; font.bold: true }
                    Label { 
                        text: steamDeckHandler.buttons.a ? "Pressed" : "Released"
                        color: steamDeckHandler.buttons.a ? "green" : "gray"
                    }

                    Label { text: "B Button:"; font.bold: true }
                    Label { 
                        text: steamDeckHandler.buttons.b ? "Pressed" : "Released"
                        color: steamDeckHandler.buttons.b ? "green" : "gray"
                    }

                    Label { text: "X Button:"; font.bold: true }
                    Label { 
                        text: steamDeckHandler.buttons.x ? "Pressed" : "Released"
                        color: steamDeckHandler.buttons.x ? "green" : "gray"
                    }

                    Label { text: "Y Button:"; font.bold: true }
                    Label { 
                        text: steamDeckHandler.buttons.y ? "Pressed" : "Released"
                        color: steamDeckHandler.buttons.y ? "green" : "gray"
                    }

                    // Shoulder Buttons
                    Label { text: "L1 Button:"; font.bold: true }
                    Label { 
                        text: steamDeckHandler.buttons.l1 ? "Pressed" : "Released"
                        color: steamDeckHandler.buttons.l1 ? "green" : "gray"
                    }

                    Label { text: "R1 Button:"; font.bold: true }
                    Label { 
                        text: steamDeckHandler.buttons.r1 ? "Pressed" : "Released"
                        color: steamDeckHandler.buttons.r1 ? "green" : "gray"
                    }

                    // D-Pad
                    Label { text: "D-Pad:"; font.bold: true }
                    RowLayout {
                        spacing: 5
                        Label { 
                            text: "↑"
                            color: steamDeckHandler.buttons.up ? "red" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "↓"
                            color: steamDeckHandler.buttons.down ? "red" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "←"
                            color: steamDeckHandler.buttons.left ? "red" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "→"
                            color: steamDeckHandler.buttons.right ? "red" : "gray"
                            font.bold: true
                        }
                    }

                    // Menu Button
                    Label { text: "Menu:"; font.bold: true }
                    Label { 
                        text: steamDeckHandler.buttons.menu ? "Pressed" : "Released"
                        color: steamDeckHandler.buttons.menu ? "green" : "gray"
                    }

                }
            }
        }
    }
}