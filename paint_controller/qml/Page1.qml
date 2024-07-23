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
            Layout.maximumHeight: 400

            spacing: 20

            GridLayout {
                id: grid
                columns: 2
                rows: 2
                columnSpacing: 10
                rowSpacing: 10
                anchors.fill: parent
                anchors.margins: 10
                Layout.preferredHeight: 200

                Rectangle {
                    Layout.column: 0
                    Layout.row: 0
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#E2E2E2"
                    radius: 10

                    Text {
                        text: "LEFT WHEEL SPEED"
                        font.pixelSize: 20
                        font.bold: true
                        color: "#000000"
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: 10
                    }
                    Text {
                        text: "1"
                        font.pixelSize: 40
                        color: "#000000"
                        anchors.centerIn: parent
                    }
                    Text {
                        text: "RPM"
                        font.pixelSize: 16
                        color: "#000000"
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 30
                    }
                }

                Rectangle {
                    Layout.column: 1
                    Layout.row: 0
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#E2E2E2"
                    radius: 10

                    Text {
                        text: "RIGHT WHEEL SPEED:"
                        font.bold: true
                        font.pixelSize: 20
                        color: "#000000"
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: 10
                    }
                    Text {
                        text: "2"
                        font.pixelSize: 40
                        color: "#000000"
                        anchors.centerIn: parent
                    }
                    Text {
                        text: "RPM"
                        font.pixelSize: 16
                        color: "#000000"
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 30
                    }
                }

                Rectangle {
                    Layout.column: 0
                    Layout.row: 1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#E2E2E2"
                    radius: 10

                    Text {
                        text: "LEFT WHEEL CURRENT"
                        font.bold: true
                        font.pixelSize: 20
                        color: "#000000"
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: 10
                    }
                    Text {
                        text: "3"
                        font.pixelSize: 40
                        color: "#000000"
                        anchors.centerIn: parent
                    }
                    Text {
                        text: "A"
                        font.pixelSize: 16
                        color: "#000000"
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 30
                    }
                }

                Rectangle {
                    Layout.column: 1
                    Layout.row: 1
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#E2E2E2"
                    radius: 10

                    Text {
                        text: "RIGHT WHEEL CURRENT"
                        font.pixelSize: 20
                        font.bold: true
                        color: "#000000"
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.margins: 10
                    }
                    Text {
                        text: "4"
                        font.pixelSize: 40
                        color: "#000000"
                        anchors.centerIn: parent
                    }
                    Text {
                        text: "A"
                        font.pixelSize: 16
                        color: "#000000"
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 30
                    }
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
