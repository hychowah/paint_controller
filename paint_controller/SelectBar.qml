import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: selectBar
    width: 101
    Layout.fillHeight: true
    color: "#191d21"

    property var stackView

    Column {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 20

        // Spacer to reserve space at the top
        Rectangle {
            width: parent.width
            height: 20 // Adjust this height to reserve the desired space
            color: "transparent"
        }

        Rectangle {
            id: buttonPage1
            width: 80
            height: 80
            radius: 20
            color: "#56606e"
            Layout.alignment: Qt.AlignHCenter

            Image {
                id: imagePage1
                source: "../paint_controller/resource/base.png"
                anchors.centerIn: parent
                width: parent.width * 0.8
                height: parent.height * 0.8
                fillMode: Image.PreserveAspectFit
            }

            MouseArea {
                anchors.fill: parent
                onClicked: stackView.replace(page1Component)
            }
        }

        Rectangle {
            id: buttonPage2
            width: 80
            height: 80
            radius: 20
            color: "#56606e"
            Layout.alignment: Qt.AlignHCenter

            Image {
                id: imagePage2
                source: "../paint_controller/resource/winch.png"
                anchors.centerIn: parent
                width: parent.width * 0.8
                height: parent.height * 0.8
                fillMode: Image.PreserveAspectFit
            }

            MouseArea {
                anchors.fill: parent
                onClicked: stackView.replace(page2Component)
            }
        }
    }
}
