// ActionItem.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: actionItem
    color: "#FFFFFF"
    radius: 15
    border.color: "#E0E0E0"
    border.width: 1

    signal addAscend // signal to add ascend action
    signal addDescend // signal to add descend action
    signal addAscendNSpray // signal to add ascend & spray action
    signal addDescendNSpray // signal to add descend & spray action
    signal addSpray // signal to add spray action
    signal addStopSpray // signal to add stop spray action

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // action item title
        Text {
            text: "Actions"
            font.pixelSize: 20
            font.bold: true
        }

        // action item content
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#E0E0E0"


            // action: ascend
            Rectangle {
                width: parent.width - 20
                height: 70
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: 10
                color: Qt.rgba(255, 255, 255, 0.5)
                border.color: "#E0E0E0"
                border.width: 1
                radius: 15

                Text {
                    anchors.left: parent.left
                    anchors.margins: 10
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Ascend"
                    font.pixelSize: 20
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        actionItem.addAscend()
                    }
                }
            }

            // action: descend
            Rectangle {
                width: parent.width - 20
                height: 70
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.children[0].bottom
                anchors.topMargin: 10
                color: Qt.rgba(255, 255, 255, 0.5)
                border.color: "#E0E0E0"
                border.width: 1
                radius: 15

                Text {
                    anchors.left: parent.left
                    anchors.margins: 10
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Descend"
                    font.pixelSize: 20
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        actionItem.addDescend()
                    }
                }
            }

            // action: ascend & spray
            Rectangle {
                width: parent.width - 20
                height: 70
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.children[1].bottom
                anchors.topMargin: 10
                color: Qt.rgba(255, 255, 255, 0.5)
                border.color: "#E0E0E0"
                border.width: 1
                radius: 15

                Text {
                    anchors.left: parent.left
                    anchors.margins: 10
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Ascend & Spray"
                    font.pixelSize: 20
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        actionItem.addAscendNSpray()
                    }
                }
            }

            // action: descend & spray
            Rectangle {
                width: parent.width - 20
                height: 70
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.children[2].bottom
                anchors.topMargin: 10
                color: Qt.rgba(255, 255, 255, 0.5)
                border.color: "#E0E0E0"
                border.width: 1
                radius: 15

                Text {
                    anchors.left: parent.left
                    anchors.margins: 10
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Descend & Spray"
                    font.pixelSize: 20
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        actionItem.addDescendNSpray()
                    }
                }
            }

            // action: spray
            Rectangle {
                width: parent.width - 20
                height: 70
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.children[3].bottom
                anchors.topMargin: 10
                color: Qt.rgba(255, 255, 255, 0.5)
                border.color: "#E0E0E0"
                border.width: 1
                radius: 15

                Text {
                    anchors.left: parent.left
                    anchors.margins: 10
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Spray"
                    font.pixelSize: 20
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        actionItem.addSpray()
                    }
                }
            }

            // action: stop spray
            Rectangle {
                width: parent.width - 20
                height: 70
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.children[4].bottom
                anchors.topMargin: 10
                color: Qt.rgba(255, 255, 255, 0.5)
                border.color: "#E0E0E0"
                border.width: 1
                radius: 15

                Text {
                    anchors.left: parent.left
                    anchors.margins: 10
                    anchors.leftMargin: 20
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Stop Spray"
                    font.pixelSize: 20
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        actionItem.addStopSpray()
                    }
                }
            }
        }
    }
}