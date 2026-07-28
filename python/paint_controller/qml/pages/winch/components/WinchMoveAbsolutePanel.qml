import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#F5F5F5"
    radius: 12

    required property var winchStatus
    property var winchActions
    property color primaryColor: "#2196F3"
    property color dangerColor: "#F44336"
    property color disabledColor: "#BDBDBD"

    signal notifyRequested(string message, int duration)
    signal activityLogged(string activity)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Text {
            text: "Move Absolute"
            font.pixelSize: 16
            font.bold: true
            color: "#212121"
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2
            rowSpacing: 10
            columnSpacing: 10

            Text {
                text: "Position (mm)"
                font.pixelSize: 14
                color: "#212121"
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 0

                TextField {
                    id: absoluteLengthField
                    Layout.fillWidth: true
                    selectByMouse: true
                    placeholderText: "Enter position"
                    enabled: root.winchStatus.enabled
                    validator: IntValidator { bottom: 0; top: 10000 }

                    background: Rectangle {
                        radius: 6
                        border.color: absoluteLengthField.acceptableInput ? "#BDBDBD" : root.dangerColor
                        border.width: 1
                    }
                }
            }

            Text {
                text: "Speed (mm/s)"
                font.pixelSize: 14
                color: "#212121"
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5

                TextField {
                    id: absoluteSpeedField
                    Layout.fillWidth: true
                    selectByMouse: true
                    text: "500"
                    enabled: root.winchStatus.enabled
                    validator: IntValidator { bottom: 1; top: 1000 }

                    background: Rectangle {
                        radius: 6
                        border.color: absoluteSpeedField.acceptableInput ? "#BDBDBD" : root.dangerColor
                        border.width: 1
                    }

                    onTextChanged: {
                        if (text && parseInt(text) > 0 && parseInt(text) <= 1000) {
                            absoluteSpeedSlider.value = parseInt(text)
                        }
                    }
                }

                Slider {
                    id: absoluteSpeedSlider
                    Layout.fillWidth: true
                    from: 1
                    to: 1000
                    stepSize: 10
                    value: 500
                    enabled: root.winchStatus.enabled
                    onValueChanged: absoluteSpeedField.text = Math.round(value).toString()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 5

            Repeater {
                model: [
                    { label: "Home", value: "0" },
                    { label: "Mid", value: "5000" },
                    { label: "Max", value: "10000" }
                ]
                delegate: Button {
                    text: modelData.label
                    enabled: root.winchStatus.enabled
                    onClicked: absoluteLengthField.text = modelData.value

                    contentItem: Text {
                        text: parent.text
                        font.pixelSize: 12
                        color: root.primaryColor
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        radius: 4
                        color: "#E3F2FD"
                        border.color: root.primaryColor
                        border.width: 1
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        Button {
            Layout.fillWidth: true
            text: "GO TO POSITION"
            enabled: root.winchStatus.enabled
                     && absoluteLengthField.text.length > 0
                     && absoluteSpeedField.text.length > 0
            onClicked: {
                if (root.winchActions.moveAbsolute(
                        parseInt(absoluteLengthField.text),
                        parseInt(absoluteSpeedField.text))) {
                    root.notifyRequested("Moving to position: " + absoluteLengthField.text + "mm", 2000)
                    root.activityLogged("Absolute move to: " + absoluteLengthField.text + "mm")
                } else {
                    root.notifyRequested("Absolute move rejected", 2000)
                }
            }

            background: Rectangle {
                radius: 6
                color: parent.enabled ? root.primaryColor : root.disabledColor
            }

            contentItem: Text {
                text: parent.text
                font.pixelSize: 14
                font.bold: true
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
