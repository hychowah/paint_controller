import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"
import "../buttons"

Popup {
    id: numpad
    width: 300
    height: 500
    modal: true
    clip: true
    
    property var targetField
    property int buttonFontSize: 16
    property color buttonColor: "#2A3040"
    property color buttonPressedColor: "#3A5A8C"
    property color buttonBorderColor: "#3A5A8C"
    property color buttonTextColor: "#FFFFFF"
    property color specialButtonColor: "#1E3A5F"
    property int buttonRadius: 6

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
        radius: 12
        border.color: "#3A5A8C"
        border.width: 2

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            // Display area
            Rectangle {
                Layout.fillWidth: true
                height: 50
                color: "#1A1A1A"
                radius: 6
                border.color: "#3A5A8C"
                border.width: 1

                Text {
                    anchors.fill: parent
                    anchors.margins: 10
                    text: targetField ? targetField.text : "0"
                    color: "#FFFFFF"
                    font.pixelSize: 20
                    font.bold: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideLeft
                }
            }

            // Buttons grid
            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 4
                rowSpacing: 8
                columnSpacing: 8

                // Row 1: 7, 8, 9, Backspace
                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "7"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "8"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "9"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "←"
                    isSpecial: true
                    onClicked: numpad.backspace()
                }

                // Row 2: 4, 5, 6, Minus
                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "4"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "5"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "6"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "−"
                    isSpecial: true
                    onClicked: numpad.toggleNegative()
                }

                // Row 3: 1, 2, 3, Period
                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "1"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "2"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "3"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "."
                    isSpecial: true
                    onClicked: numpad.addDecimal()
                }

                // Row 4: 0, Clear, Enter
                NumpadButton {
                    Layout.column: 0
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "0"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                NumpadButton {
                    Layout.column: 1
                    Layout.columnSpan: 2
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "Clear"
                    isSpecial: true
                    onClicked: if (numpad.targetField) numpad.targetField.text = ""
                }

                NumpadButton {
                    Layout.column: 3
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "✓"
                    isSpecial: true
                    onClicked: {
                        numpad.close()
                        if (numpad.targetField) {
                            numpad.targetField.focus = false
                        }
                    }
                }
            }
        }
    }
}
