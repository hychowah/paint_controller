import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import QtMultimedia 6.7
import Qt5Compat.GraphicalEffects

Rectangle {
    id: page1Rect
    objectName: "page1Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    property int timeStep: 0
    color: "#9F9F9F"

    property int dataRectHeight: 150

    property string camSource: "image://base_front_live/frame"

    RowLayout {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: 20
        height: 50

        Rectangle {
            width: 100
            height: parent.height
            color: camSource == "image://base_front_live/frame" ? "#007bff" : "#e0e0e0"
            radius: 20

            Text {
                text: "Front"
                anchors.centerIn: parent
                anchors.horizontalCenter: parent.horizontalCenter
                color: camSource == "image://base_front_live/frame" ? "#ffffff" : "#6c757d"
                font.pixelSize: 15
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    camSource = "image://base_front_live/frame"
                }
            }
        }

        Rectangle {
            width: 100
            height: parent.height
            color: camSource == "image://base_rear_live/frame" ? "#007bff" : "#e0e0e0"
            radius: 20

            Text {
                text: "Rear"
                anchors.centerIn: parent
                anchors.horizontalCenter: parent.horizontalCenter
                color: camSource == "image://base_rear_live/frame" ? "#ffffff" : "#6c757d"
                font.pixelSize: 15
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    camSource = "image://base_rear_live/frame"
                }
            }
        }
    }

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
            spacing: 20

            RowLayout {
                Layout.preferredWidth: 800
                Layout.fillHeight: true
                spacing: 20

                Rectangle {
                    id: baseView
                    objectName: "baseView"
                    //anchors.fill: parent
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"
                    
                    Image {
                        id: baseFrame
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectCrop
                        cache: false
                        source: camSource
                    }
                }

                /*Rectangle {
                    id: cameraView
                    objectName: "cameraView"
                    color: "#ff0000"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                    layer.enabled: true
                    layer.effect: OpacityMask {
                        maskSource: Item {
                            width: cameraView.width
                            height: cameraView.height
                            Rectangle {
                                anchors.centerIn: parent
                                width: parent.width
                                height: parent.height
                                radius: 20 // Adjust this value to change the corner roundness
                            }
                        }
                    }

                    Image {
                        id: videoFrame
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectCrop
                        cache: false
                        source: "image://base_live/frame"

                    }
                }*/
            }

            ColumnLayout {
                Layout.preferredWidth: 300
                Layout.fillHeight: true
                spacing: 20

                TouchSwitch {
                        id: wheelEnableSwitch
                        checked: uiData.wheel_enabled
                        onToggled: backend.setWheelEnabled(checked)
                }

                DataDisplay {
                    title: "LEFT SPEED"
                    value: uiData.left_wheel_speed
                    unit: "RPM"
                    backgroundColor: "#F0F0F0"
                    lineColor: "blue"
                    maxAbsValue: 40
                    Layout.preferredHeight: 120
                    titleFontSize: 22
                    valueFontSize: 44
                    unitFontSize: 18
                }

                DataDisplay {
                    title: "RIGHT SPEED"
                    value: uiData.right_wheel_speed
                    unit: "RPM"
                    backgroundColor: "#F0F0F0"
                    lineColor: "blue"
                    maxAbsValue: 40
                    Layout.preferredHeight: 120
                    titleFontSize: 22
                    valueFontSize: 44
                    unitFontSize: 18
                }

                DataDisplay {
                    title: "LEFT CURRENT"
                    value: uiData.left_wheel_current
                    unit: "A"
                    backgroundColor: "#F0F0F0"
                    lineColor: "blue"
                    maxAbsValue: 5
                    Layout.preferredHeight: 120
                    titleFontSize: 22
                    valueFontSize: 44
                    unitFontSize: 18
                }

                DataDisplay {
                    title: "RIGHT CURRENT"
                    value: uiData.right_wheel_current
                    unit: "A"
                    backgroundColor: "#F0F0F0"
                    lineColor: "blue"
                    maxAbsValue: 5
                    Layout.preferredHeight: 120
                    titleFontSize: 22
                    valueFontSize: 44
                    unitFontSize: 18
                }

                
            }
        }

        Timer {
            interval: 100
            repeat: true
            running: true
            onTriggered: {
                timeStep++;
                var y = (1+Math.cos(timeStep/10.0))/2.0;
            }
        }

        Connections {
            target: baseStreamHandler
            function onBaseFrontFrameReady() {
                if (camSource == "image://base_front_live/frame"){
                    baseFrame.source = ""
                    baseFrame.source = "image://base_front_live/frame"
                }
            }

            function onBaseRearFrameReady() {
                if (camSource == "image://base_rear_live/frame"){
                    baseFrame.source = ""
                    baseFrame.source = "image://base_rear_live/frame"
                }
            }
        }
    }
}