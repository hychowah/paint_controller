import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import "../"
import "../components"

Rectangle {
    id: pageHomeRect
    width: parent.width
    height: parent.height
    color: "#5E5C64"

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            text: "Welcome to the Paint Controller"
            font.pixelSize: 24
            color: "white"
            horizontalAlignment: Text.AlignHCenter
        }

        Button {
            text: "Start Painting"

        }

        Button {
            text: "Settings"
        }
    }
}