import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"
import "."

Popup {
    id: numpad
    width: Math.round(400 * CommonStyle.scaleFactor)
    height: Math.round(600 * CommonStyle.scaleFactor)
    modal: true
    clip: true
    
    property var targetField
    property int buttonFontSize: Math.round(60 * CommonStyle.scaleFactor)
    property color buttonColor: CommonStyle.cardBackground
    property color buttonPressedColor: CommonStyle.buttonPressed
    property color buttonBorderColor: CommonStyle.borderFocused
    property color buttonTextColor: CommonStyle.textPrimary
    property color specialButtonColor: CommonStyle.backgroundL1
    property int buttonRadius: CommonStyle.radiusSm

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

    component StyledNumpadButton: NumpadButton {
        normalColor: numpad.buttonColor
        specialColor: numpad.specialButtonColor
        pressedColor: numpad.buttonPressedColor
        borderColorValue: numpad.buttonBorderColor
        textColorValue: numpad.buttonTextColor
        fontSize: numpad.buttonFontSize
        radiusValue: numpad.buttonRadius
    }

    Rectangle {
        width: parent.width
        height: parent.height
        color: CommonStyle.cardBackground
        radius: CommonStyle.radiusLg
        border.color: CommonStyle.borderFocused
        border.width: 2

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: CommonStyle.spacingMd
            spacing: CommonStyle.spacingSm

            // Display area
            Rectangle {
                Layout.fillWidth: true
                height: CommonStyle.controlHeightLg
                color: CommonStyle.inputBackground
                radius: CommonStyle.radiusSm
                border.color: CommonStyle.inputFocusBorder
                border.width: 1

                Text {
                    anchors.fill: parent
                    anchors.margins: CommonStyle.spacingMd
                    text: targetField ? targetField.text : "0"
                    color: CommonStyle.textPrimary
                    font.family: CommonStyle.fontMono
                    font.pixelSize: CommonStyle.fontHeading
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
                rowSpacing: CommonStyle.spacingSm
                columnSpacing: CommonStyle.spacingSm

                // Row 1: 7, 8, 9, Backspace
                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "7"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "8"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "9"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "←"
                    isSpecial: true
                    onClicked: numpad.backspace()
                }

                // Row 2: 4, 5, 6, Minus
                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "4"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "5"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "6"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "−"
                    isSpecial: true
                    onClicked: numpad.toggleNegative()
                }

                // Row 3: 1, 2, 3, Period
                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "1"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "2"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "3"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "."
                    isSpecial: true
                    onClicked: numpad.addDecimal()
                }

                // Row 4: 0, Clear, Enter
                StyledNumpadButton {
                    Layout.column: 0
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "0"
                    onClicked: if (numpad.targetField) numpad.targetField.text += text
                }

                StyledNumpadButton {
                    Layout.column: 1
                    Layout.columnSpan: 2
                    Layout.row: 3
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    text: "Clear"
                    isSpecial: true
                    onClicked: if (numpad.targetField) numpad.targetField.text = ""
                }

                StyledNumpadButton {
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
