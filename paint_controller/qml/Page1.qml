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

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        ColumnLayout {
            Layout.preferredWidth: 800
            Layout.fillHeight: true
            spacing: 20

            Rectangle {
                id: cameraView
                objectName: "cameraView"
                color: "transparent"
                width: 760
                height: 576
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
                    source: "image://live/frame"

                }
            }

            // Item {
            //     width: 800
            //     height: 300

            //     ChartView {
            //         id: chartView
            //         anchors.fill: parent
            //         backgroundColor: "transparent"
            //         backgroundRoundness : 20

            //         ValueAxis {
            //             id: axisX
            //             min: 0
            //             max: 400
            //         }

            //         LineSeries {
            //             id: series1
            //             axisX: axisX
            //             name: "data"
            //         }
            //     }
            // }
        }

        ColumnLayout {
            Layout.preferredWidth: 300
            Layout.fillHeight: true
            spacing: 20

            Rectangle {
                id: leftWheelSpeedRect
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                property var speedDataPoints: []

                Text {
                    id: titleText
                    text: "LEFT WHEEL SPEED"
                    font.pixelSize: 20
                    font.bold: true
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }

                LineGraph {
                    id: speedGraph
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: titleText.bottom
                    anchors.bottom: speedText.top
                    anchors.margins: 0
                    
                }

                Text {
                    id: speedText
                    text: backend.left_wheel_speed
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: unitText.left
                    anchors.rightMargin: 10
                }

                Text {
                    id: unitText
                    text: "RPM"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 5
                }

                Timer {
                    interval: 100  // Update every 100ms
                    running: true
                    repeat: true
                    onTriggered: {
                        speedGraph.addDataPoint(backend.left_wheel_speed);
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                Text {
                    id: rightWheelSpeedTitle
                    text: "RIGHT WHEEL SPEED"
                    font.bold: true
                    font.pixelSize: 20
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }

                LineGraph {
                    id: rightSpeedGraph
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: rightWheelSpeedTitle.bottom
                    anchors.bottom: rightSpeedText.top
                    anchors.margins: 0
                }

                Text {
                    id: rightSpeedText
                    text: backend.right_wheel_speed
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: rightSpeedUnitText.left
                    anchors.rightMargin: 10
                }

                Text {
                    id: rightSpeedUnitText
                    text: "RPM"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 5
                }

                Timer {
                    interval: 100  // Update every 100ms
                    running: true
                    repeat: true
                    onTriggered: {
                        rightSpeedGraph.addDataPoint(backend.right_wheel_speed);
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                Text {
                    id: leftWheelCurrentTitle
                    text: "LEFT WHEEL CURRENT"
                    font.bold: true
                    font.pixelSize: 20
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }

                LineGraph {
                    id: leftCurrentGraph
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: leftWheelCurrentTitle.bottom
                    anchors.bottom: leftCurrentText.top
                    anchors.margins: 0
                }

                Text {
                    id: leftCurrentText
                    text: backend.left_wheel_current
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: leftCurrentUnitText.left
                    anchors.rightMargin: 10
                }

                Text {
                    id: leftCurrentUnitText
                    text: "A"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 5
                }

                Timer {
                    interval: 100  // Update every 100ms
                    running: true
                    repeat: true
                    onTriggered: {
                        leftCurrentGraph.addDataPoint(backend.left_wheel_current);
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                Text {
                    id: rightWheelCurrentTitle
                    text: "RIGHT WHEEL CURRENT"
                    font.pixelSize: 20
                    font.bold: true
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }

                LineGraph {
                    id: rightCurrentGraph
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: rightWheelCurrentTitle.bottom
                    anchors.bottom: rightCurrentText.top
                    anchors.margins: 0
                }

                Text {
                    id: rightCurrentText
                    text: backend.right_wheel_current
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: rightCurrentUnitText.left
                    anchors.rightMargin: 10
                }

                Text {
                    id: rightCurrentUnitText
                    text: "A"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 5
                }

                Timer {
                    interval: 100  // Update every 100ms
                    running: true
                    repeat: true
                    onTriggered: {
                        rightCurrentGraph.addDataPoint(backend.right_wheel_current);
                    }
                }
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
            // series1.append(timeStep, y);
            // imageView.source = "image://frameProvider/frame?" + Math.random()
        
        }
    }

    Connections {
                    target: videoStreamer
                    function onFrame_ready() {
                        videoFrame.source = ""
                        videoFrame.source = "image://live/frame"
                    }
    }
}
