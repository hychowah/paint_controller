import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CustomComponents 1.0  // Import the module where PlotItem is registered

Rectangle {
    id: page1Rect
    objectName: "page1Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#E66100"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20

            Text {
                text: "Page 1"
                font.pixelSize: 40
                color: "#FFFFFF"
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20

            Item {
                id: plotContainer
                objectName: "plotContainer"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                property var plotWidget: null

                PlotItem {
                    id: plotItem
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }
            }

            Rectangle {
                color: "#DDDDDD"
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom
                Text {
                    text: "Bottom Row"
                    anchors.centerIn: parent
                    color: "#000000"
                }
            }
        }
    }
}
