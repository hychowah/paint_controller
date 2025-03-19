import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Popup {
    id: keyboardPopup
    width: 900
    height: 600
    modal: true
    focus: true
    anchors.centerIn: parent

    // Property to bind with external text
    property string currentText: ""

    // Signal to notify text changes
    signal textUpdated(string newText)

    property bool shiftPressed: false

    background: Rectangle {
        color: "#f0f0f0"
        radius: 5
        border.color: "#cccccc"
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 15

        // Text display
        TextField {
            id: textField
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            font.pixelSize: 20
            text: currentText
            //readOnly: true
            onTextChanged: textUpdated(text)
        }

        // Letter rows
        GridLayout {
            Layout.fillWidth: true
            rows: 5
            columns: 8
            rowSpacing: 5
            columnSpacing: 5

            component CustomButton: Button {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            CustomButton {
                text: "1"
                onClicked: currentText += text
            }
            CustomButton {
                text: "2"
                onClicked: currentText += text
            }
            CustomButton {
                text: "3"
                onClicked: currentText += text
            }
            CustomButton {
                text: "4"
                onClicked: currentText += text
            }
            CustomButton {
                text: "5"
                onClicked: currentText += text
            }
            CustomButton {
                text: "6"
                onClicked: currentText += text
            }
            CustomButton {
                text: "7"
                onClicked: currentText += text
            }
            CustomButton {
                text: "8"
                onClicked: currentText += text
            }
            CustomButton {
                text: "9"
                onClicked: currentText += text
            }
            CustomButton {
                text: "0"
                onClicked: currentText += text
            }

            Repeater {
                model: "ABCDEFGHI"

                CustomButton {
                    text: modelData
                    onClicked: currentText += shiftPressed ? text : text.toLowerCase()
                }
            }

            Repeater {
                model: "JKLMNOPQR"

                CustomButton {
                    text: modelData
                    onClicked: currentText += shiftPressed ? text : text.toLowerCase()
                }
            }

            Repeater {
                model: "STUVWXYZ"

                CustomButton {
                    text: modelData
                    onClicked: currentText += shiftPressed ? text : text.toLowerCase()
                }
            }
        }

        // Number row and controls
        RowLayout {
            Layout.fillWidth: true
            spacing: 5

            // Control buttons
            Button {
                text: "⌫"
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                onClicked: currentText = currentText.slice(0, -1)
                background: Rectangle {
                    color: "#ff9999"
                    radius: 3
                }
            }

            Button {
                id: shiftButton
                text: "⇧"
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                onClicked: shiftPressed = !shiftPressed
                background: Rectangle {
                    color: shiftPressed ? "#99ccff" : "#cccccc"
                    radius: 3
                }
            }

            Button {
                text: "Clear"
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                onClicked: currentText = ""
                background: Rectangle {
                    color: "#99ff99"
                    radius: 3
                }
            }

            Button {
                text: "Close"
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                onClicked: keyboardPopup.close()
                background: Rectangle {
                    color: "#cccccc"
                    radius: 3
                }
            }
        }
    }

    // Helper function to update text
    function handleKeyPress(key) {
        root.currentText += key
        textField.text = root.currentText
    }

    function handleBackspace() {
        root.currentText = root.currentText.slice(0, -1)
        textField.text = root.currentText
    }
}