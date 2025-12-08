import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"
import "../../components/buttons"
import "../../components/inputs"
import "../../components/displays"
import "../../components/panels"
import "."

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

        ColumnLayout {
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
            spacing: 20

            // Left Side: Winch Status
            Rectangle {
                Layout.fillWidth: true                   
                Layout.fillHeight: true
                Layout.preferredHeight: parent.height * 0.7
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

                        Label { text: "Cable Length:"; font.bold: true }
                        Label { text: String((winchController.cable_length).toFixed(0)) + " mm" }

                        Label {text: "Cable Speed:"; font.bold: true}
                        Label {text: String(winchController.cable_speed.toFixed(0)) + " m/s"}

                        Label { text: "Torque:"; font.bold: true }
                        Label { text: String(winchController.winch_torque.toFixed(1)) + " Nm" }

                        Label { text: "Temperature:"; font.bold: true }
                        Label { text: winchController.motor_temperature.toFixed(1) + " °C" }

                        Label { text: "Voltage:"; font.bold: true }
                        Label { text: winchController.motor_voltage.toFixed(1) + " V" }

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

            // Wind Visualizer
            WindVisualizer {
                Layout.fillWidth: true
                Layout.preferredHeight: parent.height * 0.3 
                windSpeed: 2.7  // Replace with actual wind speed data
                windDirection: 45  // Replace with actual wind direction data
            }
        }

        // Teensy Status - now using the separate component
        TeensyStatus {
            Layout.preferredWidth: parent.width / 2
            Layout.fillHeight: true
        }

        // Wheel Status - now using the separate component  
        WheelStatus {
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
        }
    }
}