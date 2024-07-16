import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CustomComponents 1.0  // Import the module where PlotItem is registered

Rectangle {
    id: page1Rect
    objectName: "page1Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#FFFFFF"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        ColumnLayout {
            Layout.preferredWidth: 700
            spacing: 20

            Rectangle {
                id: titleContainer
                Layout.fillWidth: true
                Layout.preferredHeight: 680  // Adjust height as needed
                color: "#DDDDDD"
                radius: 10
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                Text {
                    text: "Page 1"
                    font.pixelSize: 40
                    color: "#000000"  // Adjusted color for visibility
                    anchors.centerIn: parent
                }
            }
        }

        ColumnLayout {
            Layout.preferredWidth: 500
            spacing: 20

            Item {
                id: plotContainer
                objectName: "plotContainer"
                width: 500
                height: 500
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                property var plotWidget: null

                PlotItem {
                    id: plotItem
                    width: parent.width
                    height: parent.height
                }
            }

            Rectangle {
                id: cameraView
                color: "#DDDDDD"
                width: 500
                height: 500
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom
                Text {
                    text: "Camera View"
                    anchors.centerIn: parent
                    color: "#000000"
                }
            }
        }
    }
}
