import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page2Rect
    objectName: "page2Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        Rectangle {
            id: mainContainer
            Layout.fillWidth: true
            Layout.preferredHeight: 700
            color: "white"
            radius: 20
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

                // Spacer item
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 20
                }

                // Left column (previously col 1)
                ColumnLayout {
                    Layout.fillHeight: true
                    Layout.preferredWidth: 422

                    Rectangle {
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        color: "transparent"

                        Image {
                            id: hanging
                            source: "../resource/hanging.png"
                            anchors.fill: parent
                            fillMode: Image.PreserveAspectFit 
                        }

                        Rectangle {
                            width: 120
                            height: 60
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.leftMargin: 40
                            anchors.topMargin: 230
                            color: "transparent"
                            radius: 10

                        }
                    }
                }

                // Middle column (previously col 2)
                ColumnLayout {
                    Layout.fillHeight: true
                    Layout.preferredWidth: 200

                    MoveLengthButton {
                        id: moveLengthButton
                        Layout.fillWidth: true
                        Layout.preferredHeight: 300
                        Layout.bottomMargin: 0
                        Layout.rightMargin: 130
                        applicationRoot: page2Rect
                        onArrowAboveClicked: console.log("Arrow above clicked")
                        onArrowBelowClicked: console.log("Arrow below clicked")
                        onInputValueChanged: console.log("Input value changed to:", inputValue)
                        onSliderValueChanged: console.log("Slider value changed to:", sliderValue)
                    }

                }

                // Right column (previously col 3)
                ColumnLayout {
                    Layout.fillHeight: true
                    Layout.preferredWidth: 200
                    spacing: 10

                    DataDisplay {
                        id: winchLengthDisplay
                        backgroundColor: "#F0F0F0"
                        value: backend.winch_length
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        title: "Length"
                        unit: "mm"
                    }

                    DataDisplay {
                        id: winchSpeedDisplay
                        backgroundColor: "#F0F0F0"
                        value: backend.winch_speed
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        title: "Speed"
                        unit: "mm/s"
                    }

                    DataDisplay {
                        id: winchCurrentDisplay
                        backgroundColor: "#F0F0F0"
                        value: backend.winch_current
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        title: "Torque"
                        unit: "%"
                    }
                }

                // Spacer item
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 20
                }
            }
        }
    }
}