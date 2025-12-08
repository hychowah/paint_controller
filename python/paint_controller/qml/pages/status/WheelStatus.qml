import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"

Rectangle {
    id: wheelStatusRect
    color: "#FFFFFF"
    radius: 10

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
                text: wheelController.available ? "Connected" : "Disconnected"
                color: wheelController.available ? "green" : "red"
            }

            Label { text: "Wheel Enabled:"; font.bold: true }
            Label { 
                text: wheelController.enabled ? "Enabled" : "Disabled"
                color: wheelController.enabled ? "green" : "red"
            }

            Label { text: "Left Wheel Speed:"; font.bold: true }
            Label { 
                text: wheelController.left_wheel_speed.toFixed(1) + " rpm"
                color: wheelController.left_wheel_speed > 0 ? "green" : "grey"
            }

            Label { text: "Right Wheel Speed:"; font.bold: true }
            Label { 
                text: wheelController.right_wheel_speed.toFixed(1) + " rpm"
                color: wheelController.right_wheel_speed > 0 ? "green" : "grey"
            }
            
            Label { text: "Left Wheel Current:"; font.bold: true }
            Label { 
                text: wheelController.left_wheel_current.toFixed(1) + " A"
                color: wheelController.left_wheel_current > 0 ? "green" : "grey"
            }

            Label { text: "Right Wheel Current:"; font.bold: true }
            Label { 
                text: wheelController.right_wheel_current.toFixed(1) + " A"
                color: wheelController.right_wheel_current > 0 ? "green" : "grey"
            }

            Label { text: "Left Wheel Travel:"; font.bold: true }
            Label { 
                text: wheelController.left_wheel_position.toFixed(0) + " mm"
                color: wheelController.left_wheel_position > 0 ? "green" : "grey"
            }

            Label { text: "Right Wheel Travel:"; font.bold: true }
            Label { 
                text: wheelController.right_wheel_position.toFixed(0) + " mm"
                color: wheelController.right_wheel_position > 0 ? "green" : "grey"
            }
        }
    }
}