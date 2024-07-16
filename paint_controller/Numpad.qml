import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Popup {
    id: numpad
    width: 320
    height: 440
    x: 800
    y: 280

    property TextField targetField

    background: Rectangle {
        color: "transparent"
    }

    Rectangle {
        width: parent.width
        height: parent.height
        color: "#333333"
        radius: 10

        GridLayout {
            columns: 3
            anchors.margins: 10
            anchors.fill: parent

            Rectangle {
                Layout.row: 0
                Layout.column: 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "7"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 0
                Layout.column: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "8"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 0
                Layout.column: 2
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "9"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 1
                Layout.column: 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "4"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 1
                Layout.column: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "5"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 1
                Layout.column: 2
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "6"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 2
                Layout.column: 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "1"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 2
                Layout.column: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "2"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 2
                Layout.column: 2
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "3"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 3
                Layout.column: 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "0"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text += text
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 3
                Layout.column: 1
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "Clear"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                        anchors.fill: parent
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        if (numpad.targetField) {
                            numpad.targetField.text = ""
                        }
                    }
                }
            }

            Rectangle {
                Layout.row: 3
                Layout.column: 2
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "Enter"
                    font.pixelSize: 20
                    background: Rectangle {
                        color: parent.pressed ? "#bbbbbb" : "#dddddd"
                        radius: 20
                        border.color: "#888888"
                        anchors.fill: parent
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    onClicked: {
                        numpad.visible = false
                        if (numpad.targetField) {
                            numpad.targetField.focus = false
                        }
                    }
                }
            }
        }
    }
}
