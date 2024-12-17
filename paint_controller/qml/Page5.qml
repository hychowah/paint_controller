import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page5Rect
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20


        Rectangle {
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            GridLayout {
                    columns: 2
                    rowSpacing: 2
                    columnSpacing: 20
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    Label { text: "Wind Speed:"; font.bold: true }
                    Label { text: uiData.wind_speed + " m/s" }

                    Label { text: "Wind Direction:"; font.bold: true }
                    Label { text: uiData.wind_direction + " o" }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10
        }
    }

}