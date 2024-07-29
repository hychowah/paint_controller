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
            id: mainContainer
            Layout.fillWidth: true
            Layout.preferredHeight: 700
            color: "white"
            radius: 20
            Layout.alignment: Qt.AlignHCenter | Qt.AlignHCenter

            LidarPlot {
                id: lidarPlot
                anchors.fill: parent
                anchors.margins: 10 // This gives some padding inside the rectangle
            }
        }
    }
}
