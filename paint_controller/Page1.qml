import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CustomComponents 1.0  // Import the module where PlotItem is registered

Rectangle {
    id: page1Rect
    objectName: "page1Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

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
                Layout.preferredHeight: 500  // Adjust height as needed
                color: "#E2E2E2"
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
            Layout.preferredWidth: 300
            spacing: 0

            Item {
                id: plotContainer
                objectName: "plotContainer"
                width: 300
                height: 300
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
                color: "#E2E2E2"
                width: 300
                height: 300
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
