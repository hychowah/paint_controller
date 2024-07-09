import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page2Rect
    objectName: "page2Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#3D3846"

    ColumnLayout {
        spacing: 20
        Layout.fillWidth: true
        Layout.fillHeight: true

        Text {
            text: "Page 2"
            font.pixelSize: 40
            color: "#FFFFFF"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
            Layout.topMargin: 20
        }

        Rectangle {
            width: 200
            height: 200
            color: "#FFDD00"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
        }

        Text {
            text: "This is the second page."
            font.pixelSize: 20
            color: "#FFFFFF"
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
        }
    }
}
