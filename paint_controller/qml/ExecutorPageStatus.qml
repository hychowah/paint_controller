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
            text: "Status1"
            font.bold: true
        }
        Label {
            text: "Value1"
        }

        Label {
            text: "Status2"
            font.bold: true
        }
        Label {
            text: "Value2"
        }

        Label {
            text: "Status3"
            font.bold: true
        }
        Label {
            text: "Value3"
        }

        Label {
            text: "Status4"
            font.bold: true
        }
        Label {
            text: "Value4"
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