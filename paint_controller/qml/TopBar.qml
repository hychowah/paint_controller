// TopBar.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: topBar
    height: 50
    color: "#28445E"
    z: 1  // Ensure top bar is above the StackView

    // White bottom border
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: "white"
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10

        Item { Layout.fillWidth: true } // Spacer

        Text {
            text: Qt.formatDateTime(new Date(), "hh:mm:ss")
            color: "white"
            font.family: "Roboto"  // Modern sans-serif font
            font.pixelSize: 24
            font.weight: Font.Medium

            Timer {
                interval: 1000
                running: true
                repeat: true
                onTriggered: parent.text = Qt.formatDateTime(new Date(), "hh:mm:ss")
            }
        }
    }
}