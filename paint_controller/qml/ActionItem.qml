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
    signal addMoveWinchTo
    signal addAscendNSpray // signal to add ascend & spray action
    signal addDescendNSpray // signal to add descend & spray action
    signal addSpray // signal to add spray action
    signal addStopSpray // signal to add stop spray action
    signal addResetYaw // signal to add reset yaw action

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
            id: actionContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#E0E0E0"

            // Use a ColumnLayout for reliable vertical stacking
            ColumnLayout {
                id: actionsLayout
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                // action: Move Winch To
                Rectangle {
                    id: moveWinchAction
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
                    color: Qt.rgba(255, 255, 255, 0.5)
                    border.color: "#E0E0E0"
                    border.width: 1
                    radius: 15

                    Text {
                        anchors.left: parent.left
                        anchors.margins: 10
                        anchors.leftMargin: 20
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Move Winch To"
                        font.pixelSize: 20
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            actionItem.addMoveWinchTo()
                        }
                    }
                }

                // action: ascend & spray
                Rectangle {
                    id: ascendSprayAction
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
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
                    id: descendSprayAction
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
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
                    id: sprayAction
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
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
                    id: stopSprayAction
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
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

                // action: reset yaw
                Rectangle {
                    id: resetYawAction
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70
                    color: Qt.rgba(255, 255, 255, 0.5)
                    border.color: "#E0E0E0"
                    border.width: 1
                    radius: 15

                    Text {
                        anchors.left: parent.left
                        anchors.margins: 10
                        anchors.leftMargin: 20
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Reset Yaw"
                        font.pixelSize: 20
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            actionItem.addResetYaw()
                        }
                    }
                }

                // Add spacer item to push everything to the top
                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }
}