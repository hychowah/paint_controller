// WindVisualizer.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: windVisualizer
    color: "#FFFFFF"
    radius: 15
    border.color: "#E0E0E0"
    border.width: 1

    // Properties that can be set from outside
    property real windSpeed: 0
    property real windDirection: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // Title
        Label {
            text: "Wind Conditions"
            font.pixelSize: 24
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }

        // Wind Direction Indicator
        Item {
            Layout.preferredWidth: Math.min(parent.width - 40, 200)
            Layout.preferredHeight: Layout.preferredWidth
            Layout.alignment: Qt.AlignHCenter

            // Compass background
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: "#F8F8F8"
                border.color: "#E0E0E0"
                border.width: 2

                // Cardinal direction markers
                Repeater {
                    model: ["0", "90", "180", "270"]
                    Label {
                        x: parent.width/2 - width/2 + Math.cos((index * 90 - 90) * Math.PI/180) * (parent.width/2 - 20)
                        y: parent.height/2 - height/2 + Math.sin((index * 90 - 90) * Math.PI/180) * (parent.height/2 - 20)
                        text: modelData
                        font.bold: true
                        font.pixelSize: 16
                    }
                }
            }

            // Wind direction arrow
            Image {
                id: directionArrow
                source: "../resource/arrow.png"
                width: parent.width * 0.4
                height: width * 1
                anchors.centerIn: parent
                rotation: (windDirection - 180) || 0

                Behavior on rotation {
                    RotationAnimation {
                        duration: 1000
                        direction: RotationAnimation.Shortest
                        easing.type: Easing.OutCubic
                    }
                }
            }
        }

        // Wind Speed Gauge
        Rectangle {
            Layout.preferredWidth: Math.min(parent.width - 40, 200)
            Layout.preferredHeight: Layout.preferredWidth / 2
            Layout.alignment: Qt.AlignHCenter
            color: "#F8F8F8"
            radius: 10
            border.color: "#E0E0E0"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                Label {
                    text: "Wind Speed"
                    font.pixelSize: 16
                    Layout.alignment: Qt.AlignHCenter
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    color: "#E0E0E0"
                    radius: height / 2

                    Rectangle {
                        width: parent.width * Math.min(windSpeed / 30, 1)
                        height: parent.height
                        radius: height / 2
                        color: {
                            if (windSpeed < 10) return "#4CAF50"
                            if (windSpeed < 20) return "#FFC107"
                            return "#F44336"
                        }

                        Behavior on width {
                            NumberAnimation {
                                duration: 500
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                }

                Label {
                    text: windSpeed.toFixed(1) + " m/s"
                    font.pixelSize: 24
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }

        // Additional wind data
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            rowSpacing: 10
            columnSpacing: 20

            Label { 
                text: "Direction:"
                font.bold: true 
            }
            Label { 
                text: windDirection.toFixed(1) + "°" 
            }

            Label { 
                text: "Beaufort Scale:"
                font.bold: true 
            }
            Label { 
                text: {
                    if (windSpeed < 0.5) return "0 - Calm"
                    if (windSpeed < 1.5) return "1 - Light Air"
                    if (windSpeed < 3.3) return "2 - Light Breeze"
                    if (windSpeed < 5.5) return "3 - Gentle Breeze"
                    if (windSpeed < 7.9) return "4 - Moderate Breeze"
                    if (windSpeed < 10.7) return "5 - Fresh Breeze"
                    if (windSpeed < 13.8) return "6 - Strong Breeze"
                    if (windSpeed < 17.1) return "7 - High Wind"
                    return "8+ - Gale or stronger"
                }
            }
        }
    }
}