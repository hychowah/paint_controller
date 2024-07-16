import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page2Rect
    objectName: "page2Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    property string length: "0"
    property string speed: "0"

    // Toggle Switch at the top right corner
    Switch {
        id: toggleSwitch
        width: 120
        height: 50
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 20
        anchors.rightMargin: 20

        indicator: Rectangle {
            implicitWidth: 120  // Increased from 80
            implicitHeight: 50  // Increased from 34
            x: toggleSwitch.leftPadding
            y: parent.height / 2 - height / 2
            radius: 25  // Increased from 17
            color: toggleSwitch.checked ? "#4CAF50" : "#F44336"
            border.color: toggleSwitch.checked ? "#45a049" : "#d32f2f"

            Rectangle {
                x: toggleSwitch.checked ? parent.width - width - 3 : 3
                width: toggleSwitch.checked ? parent.width * 0.4 : parent.width * 0.4
                height: 44  // Increased from 30
                y: 3
                radius: 22  // Increased from 15
                color: "white"
                border.color: "#D5D5D5"

                Behavior on x {
                    NumberAnimation { duration: 200 }
                }
                Behavior on width {
                    NumberAnimation { duration: 200 }
                }
            }

            Text {
                text: toggleSwitch.checked ? "Enable" : "Disable"
                font.pixelSize: 18  // Increased from 14
                color: toggleSwitch.checked ? "#FFFFFF" : "#FFFFFF"
                anchors.verticalCenter: parent.verticalCenter
                x: toggleSwitch.checked ? 10 : 50  // Adjust as necessary
            }
        }

        onCheckedChanged: backend.toggleSwitchChanged(checked)
    }

    // Representation of Winch, Cable, and Payload
    Rectangle {
        id: winch
        width: 100
        height: 30
        color: "#606060"
        anchors.left: parent.left
        anchors.leftMargin: 50
        anchors.top: parent.top
        anchors.topMargin: 100
    }

    Rectangle {
        id: cable
        width: 5
        height: 300  // Adjust the height to represent the cable length
        color: "#000000"
        anchors.horizontalCenter: winch.horizontalCenter
        anchors.top: winch.bottom

        // Box in the middle of the cable
        Rectangle {
            id: infoBox
            width: 120
            height: 60
            color: "#FFFFFF"
            border.color: "#000000"
            radius: 10
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                RowLayout {
                    Layout.alignment: Qt.AlignLeft
                    Text {
                        text: "Length: "
                        font.pixelSize: 16
                    }
                    Text {
                        text: page2Rect.length
                        font.pixelSize: 16
                        Layout.alignment: Qt.AlignRight
                        width: 50
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignLeft
                    Text {
                        text: "Speed: "
                        font.pixelSize: 16
                    }
                    Text {
                        text: page2Rect.speed
                        font.pixelSize: 16
                        Layout.alignment: Qt.AlignRight
                        width: 50
                    }
                }
            }
        }
    }

    Rectangle {
        id: payload
        width: 150
        height: 150
        radius: 20
        color: "#000000"
        anchors.horizontalCenter: cable.horizontalCenter
        anchors.top: cable.bottom
    }

    // Input Field
    TextField {
        id: inputField
        placeholderText: "Enter number"
        font.pixelSize: 20
        width: 200
        height: 40
        background: Rectangle {
            color: "white"
            radius: 10  // Adjust the radius value for more or less rounding
            border.color: "gray"
            border.width: 1
        }
        padding: 10  // Optional: adjust padding for better appearance
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        onFocusChanged: {
            if (focus && numpadLoader.status === Loader.Ready) {
                numpadLoader.item.targetField = inputField
                numpadLoader.item.open()
            } else if (numpadLoader.status === Loader.Ready) {
                numpadLoader.item.close()
            }
        }
    }

    // Text components with absolute positioning
    Text {
        text: "Page 2"
        font.pixelSize: 40
        color: "#E2E2E2"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 20
    }

    Text {
        text: "This is the second page."
        font.pixelSize: 20
        color: "#FFFFFF"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: inputField.bottom
        anchors.topMargin: 20
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
