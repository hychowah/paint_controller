import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"
import "../../../components/buttons"
import "./teensy"

Rectangle {
    id: teensyStatusRect
    objectName: "teensyStatus"
    required property var teensyStatus
    color: "#FFFFFF"
    radius: 10

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10
        Layout.alignment: Qt.AlignTop

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Label {
                text: "Teensy Status"
                font.pixelSize: 24
                font.bold: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
            }

            Label { text: "Enable:"; font.bold: true }

            TouchSwitch {
                checked: teensyStatusRect.teensyStatus.enabled
                onToggled: teensyActions.requestTeensyEnabled(checked)
            }

            Label { text: "Relay:"; font.bold: true }

            TouchSwitch {
                checked: teensyStatusRect.teensyStatus.relayOn
                onToggled: teensyActions.requestTeensyRelayEnabled(checked)
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 50
            color: "transparent"

            RowLayout {
                id: tabButtons
                anchors.fill: parent
                spacing: 1
                property int currentIndex: 0

                Repeater {
                    model: ["Main", "Rails", "Propellers", "IMU", "Spray Gun"]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: tabButtons.currentIndex === index ? "#E0E0E0" : "transparent"
                        border.color: "#CCCCCC"
                        border.width: 1

                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            font.pixelSize: 16
                            font.bold: tabButtons.currentIndex === index
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: tabButtons.currentIndex = index
                        }
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            StackLayout {
                anchors.fill: parent
                currentIndex: tabButtons.currentIndex

                TeensyMainTab { teensyStatus: teensyStatusRect.teensyStatus }
                TeensyRailsTab { teensyStatus: teensyStatusRect.teensyStatus }
                TeensyPropellersTab { teensyStatus: teensyStatusRect.teensyStatus }
                TeensyImuTab { teensyStatus: teensyStatusRect.teensyStatus }
                TeensySprayGunTab { teensyStatus: teensyStatusRect.teensyStatus }
            }
        }
    }
}
