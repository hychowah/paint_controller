import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page3Rect
    objectName: "page3Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

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
                        text: backend.winch_available ? "Connected" : "Disconnected"
                        color: backend.winch_available ? "green" : "red"
                    }

                    Label { text: "Cable Length:"; font.bold: true }
                    Label { text: backend.winch_length + " m" }

                    Label { text: "Cable Speed:"; font.bold: true }
                    Label { text: backend.winch_speed + " m/s" }

                    Label { text: "Torque:"; font.bold: true }
                    Label { text: backend.winch_torque + " Nm" }

                    Label { text: "Temperature:"; font.bold: true }
                    Label { text: backend.winch_temperature + " °C" }

                    Label { text: "Voltage:"; font.bold: true }
                    Label { text: backend.winch_voltage + " V" }

                    Label { text: "Brake:"; font.bold: true }
                    Label { 
                        text: backend.winch_brake ? "Engaged" : "Released"
                        color: backend.winch_brake ? "red" : "green"
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
                                model: ["None", "Winch Speed", "Wheel Speed", "Camera Pan/Tilt"]
                                onCurrentTextChanged: {
                                    backend.setLeftJoystickControl(currentText)
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
                                model: ["None", "Winch Speed", "Wheel Speed", "Camera Pan/Tilt"]
                                onCurrentTextChanged: {
                                    backend.setRightJoystickControl(currentText)
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
                    Label { text: "X: " + backend.left_stick_x + ", Y: " + backend.left_stick_y }

                    Label { text: "Right Stick:"; font.bold: true }
                    Label { text: "X: " + backend.right_stick_x + ", Y: " + backend.right_stick_y }

                    // Triggers
                    Label { text: "Left Trigger:"; font.bold: true }
                    Label { text: backend.left_trigger }

                    Label { text: "Right Trigger:"; font.bold: true }
                    Label { text: backend.right_trigger }

                    // Face Buttons
                    Label { text: "A Button:"; font.bold: true }
                    Label { 
                        text: backend.a_pressed ? "Pressed" : "Released"
                        color: backend.a_pressed ? "green" : "gray"
                    }

                    Label { text: "B Button:"; font.bold: true }
                    Label { 
                        text: backend.b_pressed ? "Pressed" : "Released"
                        color: backend.b_pressed ? "green" : "gray"
                    }

                    Label { text: "X Button:"; font.bold: true }
                    Label { 
                        text: backend.x_pressed ? "Pressed" : "Released"
                        color: backend.x_pressed ? "green" : "gray"
                    }

                    Label { text: "Y Button:"; font.bold: true }
                    Label { 
                        text: backend.y_pressed ? "Pressed" : "Released"
                        color: backend.y_pressed ? "green" : "gray"
                    }

                    // Shoulder Buttons
                    Label { text: "L1 Button:"; font.bold: true }
                    Label { 
                        text: backend.l1_pressed ? "Pressed" : "Released"
                        color: backend.l1_pressed ? "green" : "gray"
                    }

                    Label { text: "R1 Button:"; font.bold: true }
                    Label { 
                        text: backend.r1_pressed ? "Pressed" : "Released"
                        color: backend.r1_pressed ? "green" : "gray"
                    }

                    // D-Pad
                    Label { text: "D-Pad:"; font.bold: true }
                    RowLayout {
                        spacing: 5
                        Label { 
                            text: "↑"
                            color: backend.dpad_up_pressed ? "green" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "↓"
                            color: backend.dpad_down_pressed ? "green" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "←"
                            color: backend.dpad_left_pressed ? "green" : "gray"
                            font.bold: true
                        }
                        Label { 
                            text: "→"
                            color: backend.dpad_right_pressed ? "green" : "gray"
                            font.bold: true
                        }
                    }

                    // Menu Button
                    Label { text: "Menu:"; font.bold: true }
                    Label { 
                        text: backend.menu_pressed ? "Pressed" : "Released"
                        color: backend.menu_pressed ? "green" : "gray"
                    }

                    // IMU Data
                    Label { text: "IMU:"; font.bold: true }
                    Label { text: "Pitch: " + backend.imu_pitch + "°, Roll: " + backend.imu_roll + "°, Yaw: " + backend.imu_yaw + "°" }
                }
            }
        }
    }
}