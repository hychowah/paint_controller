import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Popup {
    id: keyboardPopup
    width: 600
    height: 400
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
            font.pixelSize: 20
            text: currentText
            //readOnly: true
            onTextChanged: textUpdated(text)
        }

        // Letter rows
        GridLayout {
            Layout.fillWidth: true
            rows: 3
            columns: 10
            rowSpacing: 5
            columnSpacing: 5

            Button {
                text: "1"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "2"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "3"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "4"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "5"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "6"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "7"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "8"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "9"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Button {
                text: "0"
                Layout.fillWidth: true
                onClicked: currentText += text
                background: Rectangle {
                    color: "#ffffff"
                    radius: 3
                }
            }

            Repeater {
                model: "QWERTYUIOP"
                Button {
                    text: modelData
                    Layout.fillWidth: true
                    onClicked: currentText += shiftPressed ? text : text.toLowerCase()
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 3
                    }
                }
            }

            Repeater {
                model: "ASDFGHJKL"
                Button {
                    text: modelData
                    Layout.fillWidth: true
                    onClicked: currentText += shiftPressed ? text : text.toLowerCase()
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 3
                    }
                }
            }

            Repeater {
                model: "ZXCVBNM"
                Button {
                    text: modelData
                    Layout.fillWidth: true
                    onClicked: currentText += shiftPressed ? text : text.toLowerCase()
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 3
                    }
                }
            }
        }

        // Number row and controls
        RowLayout {
            Layout.fillWidth: true
            spacing: 5

            /*Repeater {
                model: "1234567890"
                Button {
                    text: modelData
                    Layout.fillWidth: true
                    onClicked: currentText += text
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 3
                    }
                }
            }*/

            // Control buttons
            Button {
                text: "⌫"
                Layout.fillWidth: true
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
                onClicked: shiftPressed = !shiftPressed
                background: Rectangle {
                    color: shiftPressed ? "#99ccff" : "#cccccc"
                    radius: 3
                }
            }

            Button {
                text: "Clear"
                Layout.fillWidth: true
                onClicked: currentText = ""
                background: Rectangle {
                    color: "#99ff99"
                    radius: 3
                }
            }

            Button {
                text: "Close"
                Layout.fillWidth: true
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