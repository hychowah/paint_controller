import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page3Rect
    objectName: "page3Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                Label {
                    text: "Winch Status"
                    font.pixelSize: 24
                    font.bold: true
                    Layout.alignment: Qt.AlignTop
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    Label { text: "Status:"; font.bold: true }
                    Label { 
                        text: backend.winch_available ? "Connected" : "Disconnected"
                        color: backend.winch_available ? "green" : "red"
                    }

                    Label { text: "Cable Length:"; font.bold: true }
                    Label { text: backend.winch_length + " m" }

                    Label { text: "Cable Speed:"; font.bold: true }
                    Label { text: backend.winch_speed + " m/s" }

                    Label { text: "Torque:"; font.bold: true }
                    Label { text: backend.winch_torque + " Nm" }

                    Label { text: "Temperature:"; font.bold: true }
                    Label { text: backend.winch_temperature + " °C" }

                    Label { text: "Voltage:"; font.bold: true }
                    Label { text: backend.winch_voltage + " V" }

                    Label { text: "Brake:"; font.bold: true }
                    Label { 
                        text: backend.winch_brake ? "Engaged" : "Released"
                        color: backend.winch_brake ? "red" : "green"
                    }
                }
            }
        }
    }
}