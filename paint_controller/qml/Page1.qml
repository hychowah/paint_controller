import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import QtMultimedia 6.7

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
                width: 800
                height: 400
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                Rectangle {
                    id: imageContainer
                    width: 300
                    height: 150
                    radius: 20 // Set the radius to make the corners rounded
                    clip: true // Clip the content to the rounded corners

                    Image {
                        id: imageView
                        objectName: "imageView"
                        anchors.fill: parent
                        fillMode: Image.Stretch
                    }
                }

                Text {
                    text: "Camera View"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 30
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "#000000"
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
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                Text {
                    text: "LEFT WHEEL SPEED"
                    font.pixelSize: 20
                    font.bold: true
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }
                Text {
                    text: backend.left_wheel_speed
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.centerIn: parent
                }
                Text {
                    text: "RPM"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 30
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                Text {
                    text: "RIGHT WHEEL SPEED"
                    font.bold: true
                    font.pixelSize: 20
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }
                Text {
                    text: backend.right_wheel_speed
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.centerIn: parent
                }
                Text {
                    text: "RPM"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 30
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                Text {
                    text: "LEFT WHEEL CURRENT"
                    font.bold: true
                    font.pixelSize: 20
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }
                Text {
                    text: backend.left_wheel_current
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.centerIn: parent
                }
                Text {
                    text: "A"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 30
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: dataRectHeight
                color: "#E2E2E2"
                radius: 10

                Text {
                    text: "RIGHT WHEEL CURRENT"
                    font.pixelSize: 20
                    font.bold: true
                    color: "#000000"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 10
                }
                Text {
                    text: backend.right_wheel_current
                    font.pixelSize: 40
                    color: "#000000"
                    anchors.centerIn: parent
                }
                Text {
                    text: "A"
                    font.pixelSize: 16
                    color: "#000000"
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 30
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
            imageView.source = "image://frameProvider/frame?" + Math.random()
        
        }
    }
}
