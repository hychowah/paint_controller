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
            Layout.alignment: Qt.AlignHCenter | Qt.AlignHCenter

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

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
                        implicitWidth: 120
                        implicitHeight: 50
                        x: toggleSwitch.leftPadding
                        y: parent.height / 2 - height / 2
                        radius: 25
                        color: toggleSwitch.checked ? "#4CAF50" : "#F44336"
                        border.color: toggleSwitch.checked ? "#45a049" : "#d32f2f"

                        Rectangle {
                            x: toggleSwitch.checked ? parent.width - width - 3 : 3
                            width: toggleSwitch.checked ? parent.width * 0.4 : parent.width * 0.4
                            height: 44
                            y: 3
                            radius: 22
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
                            font.pixelSize: 18
                            color: toggleSwitch.checked ? "#FFFFFF" : "#FFFFFF"
                            anchors.verticalCenter: parent.verticalCenter
                            x: toggleSwitch.checked ? 10 : 50
                        }
                    }

                    onCheckedChanged: backend.toggleSwitchChanged(checked)
                }

                // Representation of Winch, Cable, and Payload
                Rectangle {
                    width: 422
                    height: 600
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
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
                        anchors.leftMargin: 10
                        anchors.topMargin: 250
                        color : "white"
                        border.color: "black"
                        border.width: 2
                        radius: 10
                        Text {
                            text: "Length:"
                            font.bold: true
                            font.pixelSize: 20
                            color: "#000000"
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.leftMargin: 5
                            anchors.topMargin: 5
                            
                        }
                        Text {
                            text : "mm"
                            font.pixelSize: 10
                            anchors.bottom: parent.bottom
                            anchors.right: parent.right
                            anchors.bottomMargin: 5
                            anchors.rightMargin: 5

                        }
                    }
                    
                }

                MoveLengthButton {
                    id: moveLengthButton
                    anchors.centerIn: parent
                    applicationRoot: page2Rect  // Set the application root
                    onArrowAboveClicked: console.log("Arrow above clicked")
                    onArrowBelowClicked: console.log("Arrow below clicked")
                    onInputValueChanged: console.log("Input value changed to:", inputValue)
                    onSliderValueChanged: console.log("Slider value changed to:", sliderValue)
                }
            }
        }
    }
}
