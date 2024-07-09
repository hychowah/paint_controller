import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    width: 101
    Layout.fillHeight: true
    color: "#3D3846"

    signal selectPage1()
    signal selectPage2()

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Button {
            text: "Page 1"
            onClicked: selectPage1()
        }

        Button {
            text: "Page 2"
            onClicked: selectPage2()
        }
    }
}
