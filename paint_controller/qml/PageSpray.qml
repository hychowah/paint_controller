import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import QtMultimedia 6.7
import Qt5Compat.GraphicalEffects

Rectangle {
    id: page5Rect
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    Rectangle {
        id: dataRect
        Layout.fillWidth: true  
        width: 1050
        height: 700
        anchors.centerIn: parent
        color: "#E2E2E2"
        radius: 30

        RowLayout {
            anchors.fill: parent
            anchors.margins: 20

            Item {
                id: streamContainer
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                // Original streaming view
                Rectangle {
                    id: efView
                    objectName: "efView"
                    anchors.fill: parent
                    color: "transparent"
                    layer.enabled: true
                    layer.effect: OpacityMask {
                        maskSource: Item {
                            width: efView.width
                            height: efView.height
                            Rectangle {
                                anchors.centerIn: parent
                                width: parent.width
                                height: parent.height
                                radius: 20
                            }
                        }
                    }

                    Image {
                        id: efFrame
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectCrop
                        cache: false
                        source: "image://ef_live/frame"
                    }
                }


                Rectangle {
                    id: bottomOverlay
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: 200
                    color: Qt.rgba(0, 0, 0, 0.5)

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 20

                        Button {
                            text: "Settings"
                            Layout.preferredWidth: 100
                            anchors.bottom: parent.bottom
                        }

                        Label {
                            text: uiData.winch_available ? "Winch Connected" : "Winch Disconnected"
                            color: "white"
                            Layout.fillWidth: true
                            anchors.bottom: parent.bottom
                        }

                        DigitalGauge {
                            width: 150
                            height: 150
                            torque: Math.abs(uiData.winch_torque)  // Current torque value
                            speed: uiData.winch_speed // Current speed value
                            maxTorque: 1000
                            units: "Nm"
                            speedUnits: "RPM"
                            Layout.rightMargin: 20
                        }
                    }
                }

                // Side overlay (example for statistics or controls)
                Rectangle {
                    id: sideOverlay
                    anchors.right: parent.right
                    anchors.top: topOverlay.bottom
                    anchors.bottom: bottomOverlay.top
                    width: 200
                    color: Qt.rgba(0, 0, 0, 0.3)
                    visible: false  // Hidden by default

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Label {
                            text: "Statistics"
                            color: "white"
                            font.bold: true
                        }

                        // Add more statistics or control elements here
                    }
                }
            }
        }
    }

    Connections {
        target: baseStreamer
        function onFrame_ready() {
            efFrame.source = ""
            efFrame.source = "image://ef_live/frame"
        }
    }

    // Toggle button for side overlay
    Button {
        id: toggleSideOverlay
        anchors.right: dataRect.right
        anchors.top: dataRect.top
        anchors.margins: 30
        text: "Toggle Stats"
        onClicked: sideOverlay.visible = !sideOverlay.visible
    }
}