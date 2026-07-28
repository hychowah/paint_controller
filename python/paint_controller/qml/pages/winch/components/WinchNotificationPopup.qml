import QtQuick
import QtQuick.Controls

Popup {
    id: notificationPopup
    width: 300
    height: 60
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    background: Rectangle {
        color: "#323232"
        radius: 8
    }

    contentItem: Text {
        id: notificationText
        color: "white"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 14
    }

    function show(message, duration) {
        notificationText.text = message
        open()
        closeTimer.interval = duration || 3000
        closeTimer.restart()
    }

    Timer {
        id: closeTimer
        onTriggered: notificationPopup.close()
    }
}
