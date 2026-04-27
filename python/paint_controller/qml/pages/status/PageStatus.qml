import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"
import "../../components/buttons"
import "../../components/displays"
import "components"

Rectangle {
    id: page3Rect
    objectName: "page3Rect"
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Helper function to update available options
    // Store the complete list of options
    property var allControlOptions: ["None", "Winch Speed", "Wheel Speed", "EF arm", "EF top rail", "EF prop pwm", "EF prop joint", "EF spray trigger", "EF spray pitch"]
    
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
                                checked: page3Rect.winchStatus.enabled
                                onToggled: {
                                    if (!deviceActionHandler.requestWinchEnabled(checked)) {
                                        winchEnableSwitch.checked = !checked
                                    }
                                }
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
                            text: page3Rect.winchStatus.available ? "Connected" : "Disconnected"
                            color: page3Rect.winchStatus.available ? "green" : "red"
                        }

                        Label { text: "Cable Length:"; font.bold: true }
                        Label { text: String((page3Rect.winchStatus.cableLength).toFixed(0)) + " mm" }

                        Label {text: "Cable Speed:"; font.bold: true}
                        Label {text: String(page3Rect.winchStatus.cableSpeed.toFixed(0)) + " m/s"}

                        Label { text: "Torque:"; font.bold: true }
                        Label { text: String(page3Rect.winchStatus.winchTorque.toFixed(1)) + " Nm" }

                        Label { text: "Temperature:"; font.bold: true }
                        Label { text: page3Rect.winchStatus.motorTemperature.toFixed(1) + " °C" }

                        Label { text: "Voltage:"; font.bold: true }
                        Label { text: page3Rect.winchStatus.motorVoltage.toFixed(1) + " V" }

                        Label { text: "Brake:"; font.bold: true }
                        Label { 
                            text: page3Rect.winchStatus.motorBrake ? "Engaged" : "Released"
                            color: page3Rect.winchStatus.motorBrake ? "red" : "green"
                        }

                        Label { text: "Load Detection:"; font.bold: true }
                        Label { 
                            text: page3Rect.winchStatus.loadDetectionEnabled ? "True" : "False"
                            color: page3Rect.winchStatus.loadDetectionEnabled ? "green" : "red"
                        }

                        Label { text: "Unusual Load:"; font.bold: true }
                        Label { 
                            text: page3Rect.winchStatus.unusualLoadDetected ? "True" : "False"
                            color: page3Rect.winchStatus.unusualLoadDetected ? "green" : "red"
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
            teensyStatus: page3Rect.teensyStatus
        }

        // Wheel Status - now using the separate component  
        WheelStatus {
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
            wheelStatus: page3Rect.wheelStatus
        }
    }
}