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

            //  Rectangle {
            //     id: lidarPlotConatainer
            //     Layout.fillWidth: true
            //     Layout.preferredHeight: 300
            //     color: "white"
            //     radius: 20
            //     Layout.alignment: Qt.AlignHCenter | Qt.AlignHCenter

            //     Image {
            //         id: backgroundImage
            //         anchors.fill: parent
            //         source: "../resource/top_base.png"
            //         fillMode: Image.PreserveAspectFit
            //         // Scale the image (adjust as needed)
            //         scale: 0.7 // You can change this value to scale up or down

            //         // Fine-tune position using transform
            //         transform: Translate {
            //             x: 5 // Adjust horizontal position
            //             y: 35 // Adjust vertical position
            //         }
            //     }

            //     LidarPlot {
            //         id: lidarPlot
            //         anchors.fill: parent
            //         anchors.margins: 10 // This gives some padding inside the rectangle
            //         fixedMaxRange: 1.6
            //     }
            // }

            Rectangle {
                id: cameraView
                objectName: "cameraView"
                color: "transparent"
                width: 480
                height: 320
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
        }

        ColumnLayout {
            Layout.preferredWidth: 300
            Layout.fillHeight: true
            spacing: 20

            DataDisplay {
                title: "LEFT SPEED"
                value: backend.left_wheel_speed
                unit: "RPM"
                backgroundColor: "#F0F0F0"
                lineColor: "blue"
                maxAbsValue: 40
                Layout.preferredHeight: 140
                titleFontSize: 22
                valueFontSize: 44
                unitFontSize: 18
            }

            DataDisplay {
                title: "RIGHT SPEED"
                value: backend.right_wheel_speed
                unit: "RPM"
                backgroundColor: "#F0F0F0"
                lineColor: "blue"
                maxAbsValue: 40
                Layout.preferredHeight: 140
                titleFontSize: 22
                valueFontSize: 44
                unitFontSize: 18
            }

            DataDisplay {
                title: "LEFT CURRENT"
                value: backend.left_wheel_current
                unit: "A"
                backgroundColor: "#F0F0F0"
                lineColor: "blue"
                maxAbsValue: 5
                Layout.preferredHeight: 140
                titleFontSize: 22
                valueFontSize: 44
                unitFontSize: 18
            }

            DataDisplay {
                title: "RIGHT CURRENT"
                value: backend.right_wheel_current
                unit: "A"
                backgroundColor: "#F0F0F0"
                lineColor: "blue"
                maxAbsValue: 5
                Layout.preferredHeight: 140
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
}