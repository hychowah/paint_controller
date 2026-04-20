import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"

Popup {
    id: numpad
    width: 320
    height: 480
    x: 800
    y: 280

    property TextField targetField
    property int buttonFontSize: 18
    property color buttonColor: "#2A3040"
    property color buttonPressedColor: "#3A5A8C"
    property color buttonBorderColor: "#3A5A8C"
    property color buttonTextColor: "#FFFFFF"
    property int buttonRadius: 8

    background: Rectangle {
        color: "transparent"
    }
    
    function toggleNegative() {
        if (targetField && targetField.text !== "") {
            if (targetField.text.startsWith("-")) {
                targetField.text = targetField.text.substring(1)
            } else {
                targetField.text = "-" + targetField.text
            }
        } else if (targetField) {
            targetField.text = "-"
        }
    }
    
    function addDecimal() {
        if (targetField && !targetField.text.includes(".")) {
            if (targetField.text === "" || targetField.text === "-") {
                targetField.text += "0."
            } else {
                targetField.text += "."
            }
        }
    }
    
    function backspace() {
        if (targetField && targetField.text.length > 0) {
            targetField.text = targetField.text.slice(0, -1)
        }
    }

    Rectangle {
        width: parent.width
        height: parent.height
        color: "#252A36"
        radius: 10
        border.color: "#3A5A8C"
        border.width: 2

        GridLayout {
            columns: 4
            anchors.margins: 10
            anchors.fill: parent
            rowSpacing: 8
            columnSpacing: 8

            Rectangle {
                Layout.row: 0
                Layout.column: 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "transparent"

                Button {
                    anchors.fill: parent
                    text: "7"
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    text: "0"
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    text: "Clear"
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
                    font.pixelSize: numpad.buttonFontSize
                    background: Rectangle {
                        color: parent.pressed ? numpad.buttonPressedColor : numpad.buttonColor
                        radius: numpad.buttonRadius
                        border.color: numpad.buttonBorderColor
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
