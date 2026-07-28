import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var teensyStatus

    Column {
        anchors.fill: parent
        anchors.topMargin: 10
        spacing: 20

        GridLayout {
            columns: 2
            rowSpacing: 10
            columnSpacing: 20

            Label { text: "Pitch:"; font.bold: true }
            Label { text: root.teensyStatus.sprayGunPitch.toFixed(1) + "°" }

            Label { text: "Pitch Motor Angle:"; font.bold: true }
            Label { text: root.teensyStatus.gimbalPitchMotorAngle.toFixed(1) + "°" }

            Label { text: "Pitch Motor Current:"; font.bold: true }
            Label { text: root.teensyStatus.gimbalPitchMotorCurrent.toFixed(1) + " A" }

            Label { text: "Pitch Motor Temp:"; font.bold: true }
            Label { text: root.teensyStatus.gimbalPitchMotorTemp.toFixed(1) + " °C" }

            Label { text: "Roll Motor Angle:"; font.bold: true }
            Label { text: root.teensyStatus.gimbalRollMotorAngle.toFixed(1) + "°" }

            Label { text: "Roll Motor Current:"; font.bold: true }
            Label { text: root.teensyStatus.gimbalRollMotorCurrent.toFixed(1) + " A" }

            Label { text: "Roll Motor Temp:"; font.bold: true }
            Label { text: root.teensyStatus.gimbalRollMotorTemp.toFixed(1) + " °C" }

            Label { text: "Trigger:"; font.bold: true }
            Label {
                text: root.teensyStatus.sprayGunTrigger ? "Pressed" : "Released"
                color: root.teensyStatus.sprayGunTrigger ? "green" : "gray"
            }
        }
    }
}
