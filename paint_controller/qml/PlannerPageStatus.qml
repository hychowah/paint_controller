import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: plannerPageStatus
    color: "#ffffff"
    radius: 15
    border.color: "#e0e0e0"
    border.width: 1

    GridLayout {
        columns: 2
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