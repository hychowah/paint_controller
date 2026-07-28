import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var teensyStatus

    function calculateBatteryPercentage(voltage) {
        const maxVoltage = 29.4
        const minVoltage = 21.0
        const clampedVoltage = Math.max(minVoltage, Math.min(maxVoltage, voltage))
        return Math.round(((clampedVoltage - minVoltage) / (maxVoltage - minVoltage)) * 100)
    }

    GridLayout {
        anchors.fill: parent
        columns: 4
        rowSpacing: 10
        columnSpacing: 20

        Label {
            text: "Board Status"
            font.bold: true
            font.pixelSize: 16
            Layout.columnSpan: 4
        }

        Label { text: "Voltage:"; font.bold: true }
        Label { text: root.teensyStatus.voltage.toFixed(1) + " V" }
        Label { text: "Current:"; font.bold: true }
        Label { text: root.teensyStatus.current.toFixed(1) + " A" }

        Label { text: "Temperature:"; font.bold: true }
        Label { text: root.teensyStatus.temperature.toFixed(1) + " °C" }
        Label { text: "Runtime:"; font.bold: true }
        Label { text: root.teensyStatus.runTime.toFixed(0) }

        Label { text: "Loop Time:"; font.bold: true }
        Label { text: root.teensyStatus.loopTime.toFixed(0) + " µs" }
        Label { text: "Loop Counter:"; font.bold: true }
        Label { text: root.teensyStatus.loopTimeCounter.toFixed(0) }

        Label { text: "Battery:"; font.bold: true }
        Label { text: root.calculateBatteryPercentage(root.teensyStatus.voltage) + "%" }
        Label { text: "Status:"; font.bold: true }
        Label { text: "Operating" }

        Label {
            text: "System Alerts"
            font.bold: true
            font.pixelSize: 16
            Layout.columnSpan: 4
            Layout.topMargin: 10
        }

        Rectangle {
            Layout.columnSpan: 4
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 100
            color: "#F5F5F5"
            border.color: "#DDDDDD"
            border.width: 1

            Column {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10
            }
        }
    }
}
