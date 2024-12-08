import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import QtMultimedia 6.7

Rectangle{
    id: page4Rect
    objectName: "page4Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    Rectangle{
        id: dataRect
        Layout.fillWidth: true
        width: 1050
        height: 700
        anchors.centerIn: parent
        color: "#E2E2E2"
        radius: 30
    }

    RowLayout{
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        RowLayout{
            Layout.preferredWidth: 800
            Layout.fillHeight: true
            spacing: 20

            Rectangle{
                Layout.fillWidth: true
                Layout.preferredHeight: 300
                color: "white"
                radius: 20
                Layout.alignment: Qt.AlignHCenter | Qt.AlignHCenter

                Image{
                    id: backgroundImage
                    anchors.fill: parent
                    source: "../resource/top_base.png"
                    fillMode: Image.PreserveAspectFit
                    scale: 0.7
                    transform: Translate{
                        x: 5
                        y: 35
                    }
                }
            }
        }
    }
}