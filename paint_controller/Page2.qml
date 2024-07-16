import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page2Rect
    objectName: "page2Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    ColumnLayout {
        spacing: 20
        Layout.fillWidth: true
        Layout.fillHeight: true

        Text {
            text: "Page 2"
            font.pixelSize: 40
            color: "#E2E2E2"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.topMargin: 20
        }

        Rectangle {
            width: 200
            height: 200
            color: "#FFDD00"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
        }

        Text {
            text: "This is the second page."
            font.pixelSize: 20
            color: "#FFFFFF"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
        }

        // Input Field
        TextField {
            id: inputField
            placeholderText: "Enter number"
            font.pixelSize: 20
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            onFocusChanged: {
                if (focus && numpadLoader.status === Loader.Ready) {
                    numpadLoader.item.targetField = inputField
                    numpadLoader.item.open()
                } else if (numpadLoader.status === Loader.Ready) {
                    numpadLoader.item.close()
                }
            }
        }

        Switch {
            id: programSwitch
            text: "Toggle Program"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            onToggled: {
                backend.toggleProgram(checked)
            }
        }
    }

    // Add the Numpad component
    Loader {
        id: numpadLoader
        source: "Numpad.qml"
        onLoaded: {
            if (numpadLoader.item !== null) {
                numpadLoader.item.targetField = inputField
            }
        }
    }
}
