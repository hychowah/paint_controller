import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: executorPageStatus
    color: Qt.rgba(255, 255, 255, 0.9)

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true // Enable hover detection
        onEntered: {
            executorPageStatus.color = Qt.rgba(255, 255, 255, 0)
            executorPageStatusGrid.visible = false
        }
        onExited: {
            executorPageStatus.color = Qt.rgba(255, 255, 255, 0.9)
            executorPageStatusGrid.visible = true
        }
    }

    GridLayout {
        id: executorPageStatusGrid
        columns: 4
        rowSpacing: 10
        columnSpacing: 20
        anchors.fill: parent
        anchors.margins: 10
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignTop

        Label {
            text: "Winch Torque"
            font.bold: true
        }
        Label {
            text: winchController.winch_torque.toFixed(1)
        }

        Label {
            text: "Cable Length"
            font.bold: true
        }
        Label {
            text: Math.round(winchController.cable_length)
        }

        Label {
            text: "Cable Speed" 
            font.bold: true
        }
        Label {
            text: Math.abs(winchController.cable_speed)
        }

        Label {
            text: "Arm Extension"
            font.bold: true
        }
        Label {
            text: teensyController.all_status.arm_extension_dist.toFixed(0)
        }

        Label {
            text: "Status5"
            font.bold: true
        }
        Label {
            text: "Value5"
        }
    }
}