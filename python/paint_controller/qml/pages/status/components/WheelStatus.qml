import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

Rectangle {
    id: wheelStatusRect
    color: "#FFFFFF"
    radius: 10
    required property var wheelStatus

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        Label {
            text: "Wheel Status"
            font.pixelSize: 24
            font.bold: true
        }

        // Input Status Display
        GridLayout {
            columns: 2
            rowSpacing: 10
            columnSpacing: 20
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop

            Label { text: "Wheel Connected:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.available ? "Connected" : "Disconnected"
                color: wheelStatusRect.wheelStatus.available ? "green" : "red"
            }

            Label { text: "Wheel Enabled:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.enabled ? "Enabled" : "Disabled"
                color: wheelStatusRect.wheelStatus.enabled ? "green" : "red"
            }

            Label { text: "Left Wheel Speed:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.leftWheelSpeed.toFixed(1) + " rpm"
                color: wheelStatusRect.wheelStatus.leftWheelSpeed > 0 ? "green" : "grey"
            }

            Label { text: "Right Wheel Speed:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.rightWheelSpeed.toFixed(1) + " rpm"
                color: wheelStatusRect.wheelStatus.rightWheelSpeed > 0 ? "green" : "grey"
            }
            
            Label { text: "Left Wheel Current:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.leftWheelCurrent.toFixed(1) + " A"
                color: wheelStatusRect.wheelStatus.leftWheelCurrent > 0 ? "green" : "grey"
            }

            Label { text: "Right Wheel Current:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.rightWheelCurrent.toFixed(1) + " A"
                color: wheelStatusRect.wheelStatus.rightWheelCurrent > 0 ? "green" : "grey"
            }

            Label { text: "Left Wheel Travel:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.leftWheelPosition.toFixed(0) + " mm"
                color: wheelStatusRect.wheelStatus.leftWheelPosition > 0 ? "green" : "grey"
            }

            Label { text: "Right Wheel Travel:"; font.bold: true }
            Label { 
                text: wheelStatusRect.wheelStatus.rightWheelPosition.toFixed(0) + " mm"
                color: wheelStatusRect.wheelStatus.rightWheelPosition > 0 ? "green" : "grey"
            }
        }
    }
}