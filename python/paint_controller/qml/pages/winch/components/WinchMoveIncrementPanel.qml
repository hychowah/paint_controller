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
    required property var winchActions
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
            text: "Move Increment"
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
                text: "Length (mm)"
                font.pixelSize: 14
                color: "#212121"
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 0

                TextField {
                    id: incrementLengthField
                    Layout.fillWidth: true
                    selectByMouse: true
                    placeholderText: "Enter length"
                    enabled: root.winchStatus.enabled
                    validator: IntValidator { bottom: -10000; top: 10000 }

                    background: Rectangle {
                        radius: 6
                        border.color: incrementLengthField.acceptableInput ? "#BDBDBD" : root.dangerColor
                        border.width: 1
                    }

                    onTextChanged: {
                        if (text && !acceptableInput) {
                            errorToolTip.text = "Enter a value between -10000 and 10000"
                            errorToolTip.visible = true
                        } else {
                            errorToolTip.visible = false
                        }
                    }

                    ToolTip {
                        id: errorToolTip
                        visible: false
                        delay: 500
                        timeout: 5000
                        contentItem: Text {
                            color: "white"
                            text: errorToolTip.text
                        }
                        background: Rectangle {
                            color: root.dangerColor
                            radius: 4
                        }
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
                    id: incrementSpeedField
                    Layout.fillWidth: true
                    selectByMouse: true
                    text: "500"
                    enabled: root.winchStatus.enabled
                    validator: IntValidator { bottom: 1; top: 1000 }

                    background: Rectangle {
                        radius: 6
                        border.color: incrementSpeedField.acceptableInput ? "#BDBDBD" : root.dangerColor
                        border.width: 1
                    }

                    onTextChanged: {
                        if (text && parseInt(text) > 0 && parseInt(text) <= 1000) {
                            incrementSpeedSlider.value = parseInt(text)
                        }
                    }
                }

                Slider {
                    id: incrementSpeedSlider
                    Layout.fillWidth: true
                    from: 1
                    to: 1000
                    stepSize: 10
                    value: 500
                    enabled: root.winchStatus.enabled
                    onValueChanged: incrementSpeedField.text = Math.round(value).toString()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 5

            Repeater {
                model: [
                    { label: "10mm", value: "10" },
                    { label: "100mm", value: "100" },
                    { label: "500mm", value: "500" }
                ]
                delegate: Button {
                    text: modelData.label
                    enabled: root.winchStatus.enabled
                    onClicked: incrementLengthField.text = modelData.value

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
            text: "MOVE INCREMENT"
            enabled: root.winchStatus.enabled
                     && incrementLengthField.text.length > 0
                     && incrementSpeedField.text.length > 0
                     && incrementLengthField.acceptableInput
                     && incrementSpeedField.acceptableInput
            onClicked: {
                if (root.winchActions.moveIncrement(
                        parseInt(incrementLengthField.text),
                        parseInt(incrementSpeedField.text))) {
                    root.notifyRequested("Moving increment: " + incrementLengthField.text + "mm", 2000)
                    root.activityLogged("Increment move: " + incrementLengthField.text + "mm")
                } else {
                    root.notifyRequested("Increment move rejected", 2000)
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
