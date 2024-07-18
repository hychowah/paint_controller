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
            Layout.preferredHeight: 600
            color: "#E2E2E2"
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
                    id: winch
                    width: 100
                    height: 30
                    color: "#606060"
                    anchors.left: parent.left
                    anchors.leftMargin: 150
                    anchors.top: parent.top
                    anchors.topMargin: 30
                }

                Rectangle {
                    id: cable
                    width: 5
                    height: 330
                    color: "#000000"
                    anchors.horizontalCenter: winch.horizontalCenter
                    anchors.top: winch.bottom

                    // Box to the right of the cable
                    Rectangle {
                        id: infoBox
                        width: 110
                        height: 80
                        color: "transparent"
                        radius: 10
                        anchors.left: cable.right
                        anchors.leftMargin: 20
                        anchors.verticalCenter: parent.verticalCenter

                        GridLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            columns: 2
                            rowSpacing: 5

                            Text {
                                text: "Length: "
                                font.pixelSize: 16
                                Layout.row: 0
                                Layout.column: 0
                                Layout.alignment: Qt.AlignLeft
                            }
                            Text {
                                text: backend.length
                                font.pixelSize: 16
                                Layout.row: 0
                                Layout.column: 1
                                Layout.alignment: Qt.AlignRight
                            }
                            Text {
                                text: "Speed: "
                                font.pixelSize: 16
                                Layout.row: 1
                                Layout.column: 0
                                Layout.alignment: Qt.AlignLeft
                            }
                            Text {
                                text: backend.speed
                                font.pixelSize: 16
                                Layout.row: 1
                                Layout.column: 1
                                Layout.alignment: Qt.AlignRight
                            }
                        }
                    }

                    // Arrow to indicate cable movement
                    Rectangle {
                        id: arrow
                        width: 20
                        height: 20
                        color: "transparent"
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.verticalCenter: infoBox.verticalCenter
                        rotation: backend.speed > 0 ? 0 : 180
                        visible: backend.speed != 0  // Arrow is visible only when speed is non-zero

                        // Left diagonal line of the arrowhead
                        Rectangle {
                            width: 5
                            height: 20
                            color: "black"
                            rotation: 45
                            anchors.bottom: parent.bottom
                            anchors.horizontalCenter: parent.horizontalCenter
                            transformOrigin: Item.Bottom
                        }

                        // Right diagonal line of the arrowhead
                        Rectangle {
                            width: 5
                            height: 20
                            color: "black"
                            rotation: -45
                            anchors.bottom: parent.bottom
                            anchors.horizontalCenter: parent.horizontalCenter
                            transformOrigin: Item.Bottom
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

                // Arrow Image Above the Input Field
                Rectangle {
                    width: 100
                    height: 100
                    anchors.horizontalCenter: inputField.horizontalCenter
                    anchors.bottom: inputField.top
                    anchors.bottomMargin: 20
                    color: "transparent"
                    Image {
                        id: arrowAbove
                        source: "../paint_controller/resource/up_arrow.png"
                        anchors.fill: parent
                    }
                    MouseArea {
                        anchors.fill: parent
                        onPressed: arrowAbove.opacity = 0.5
                        onReleased: {
                            arrowAbove.opacity = 1.0
                            // Define your action here
                            console.log("Arrow above clicked")
                        }
                    }
                }

                // Input Field
                TextField {
                    id: inputField
                    placeholderText: "Enter length"
                    font.pixelSize: 20
                    width: 200
                    height: 40
                    verticalAlignment: Text.AlignBottom
                    bottomPadding: 5
                    rightPadding: 30  // Make room for the "mm" text
                    background: Rectangle {
                        color: "#9F9F9F"
                        border.color: "gray"
                        border.width: 1
                        Rectangle {
                            width: parent.width
                            height: 1
                            anchors.bottom: parent.bottom
                            color: "gray"
                        }
                    }
                    padding: 10
                    x: parent.width / 2 - width / 2 - 90
                    y: parent.height / 2 - height / 2 + 95
                    onFocusChanged: {
                        if (focus && numpadLoader.status === Loader.Ready) {
                            numpadLoader.item.targetField = inputField
                            numpadLoader.item.open()
                        } else if (numpadLoader.status === Loader.Ready) {
                            numpadLoader.item.close()
                        }
                    }

                    Text {
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        anchors.rightMargin: 5
                        anchors.bottomMargin: 5
                        text: "mm"
                        font.pixelSize: 14
                        color: "gray"
                    }
                }

                // Arrow Image Below the Input Field
                Rectangle {
                    width: 100
                    height: 100
                    anchors.horizontalCenter: inputField.horizontalCenter
                    anchors.top: inputField.bottom
                    anchors.topMargin: 20
                    color: "transparent"
                    Image {
                        id: arrowBelow
                        source: "../paint_controller/resource/down_arrow.png"
                        anchors.fill: parent
                    }
                    MouseArea {
                        anchors.fill: parent
                        onPressed: arrowBelow.opacity = 0.5
                        onReleased: {
                            arrowBelow.opacity = 1.0
                            // Define your action here
                            console.log("Arrow below clicked")
                        }
                    }
                }

                // Vertical Slider to the right of the Input Field
                Slider {
                    id: verticalSlider
                    orientation: Qt.Vertical
                    anchors.left: inputField.right
                    anchors.leftMargin: 20
                    anchors.verticalCenter: inputField.verticalCenter
                    width: 60
                    implicitHeight: 300
                    from: 0
                    to: 100
                    stepSize: 1
                    value: 50

                    // Custom handle
                    handle: Rectangle {
                        x: verticalSlider.leftPadding + verticalSlider.availableWidth / 2 - width / 2
                        y: verticalSlider.topPadding + verticalSlider.visualPosition * (verticalSlider.availableHeight - height)
                        implicitWidth: 30
                        height: 30
                        radius: 15  // This makes it circular
                        color: verticalSlider.pressed ? "#cccccc" : "#ffffff"  // Light grey when pressed, white otherwise
                        border.color: "#999999"
                        border.width: 2

                        // Optional: Add an inner circle for a more distinctive look
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width * 0.6
                            height: width
                            radius: width / 2
                            color: "#999999"
                        }
                    }
                }
            }
        }
    }

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
