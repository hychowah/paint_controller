import QtQuick
import QtQuick.Layouts

// As-is dual-button style enable toggle used for winch power and load detection.
// Preserves toast-via-signal and ambient winchActions call sites from PageWinch.
Rectangle {
    id: root
    Layout.fillWidth: true
    height: 50
    radius: 12
    border.width: 1

    required property var winchStatus
    required property var winchActions
    property string mode: "power"  // "power" | "load"
    property color primaryColor: "#2196F3"
    property color disabledColor: "#BDBDBD"

    readonly property bool isPower: mode === "power"
    readonly property bool checked: isPower ? winchStatus.enabled : winchStatus.loadDetectionEnabled
    readonly property bool interactive: isPower ? winchStatus.available : winchStatus.enabled

    color: checked ? "#E3F2FD" : "#F5F5F5"
    border.color: checked ? "#90CAF9" : "#E0E0E0"

    signal notifyRequested(string message, int duration)

    Row {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        Rectangle {
            id: indicator
            width: parent.height
            height: parent.height
            anchors.verticalCenter: parent.verticalCenter
            radius: width / 2
            color: root.checked ? root.primaryColor : root.disabledColor

            Text {
                anchors.centerIn: parent
                text: root.isPower ? "⚡" : "⚖"
                color: "white"
                font.pixelSize: 24
                font.bold: true
            }
        }

        Column {
            id: textColumn
            width: parent.width - indicator.width - toggleContainer.width - parent.spacing * 2
            height: parent.height
            spacing: 4
            anchors.verticalCenter: parent.verticalCenter

            Text {
                width: parent.width
                text: root.isPower ? "Winch Power" : "Load Detection"
                font.pixelSize: parent.height * 0.6
                font.bold: true
                color: "#212121"
                elide: Text.ElideRight
            }

            Text {
                width: parent.width
                text: root.isPower
                      ? (root.checked ? "Enabled - Motor active" : "Disabled - Motor inactive")
                      : (root.checked ? "Enabled - Safety active" : "Disabled - No load protection")
                font.pixelSize: parent.height * 0.4
                color: root.checked ? root.primaryColor : "#757575"
                elide: Text.ElideRight
                wrapMode: Text.Wrap
                maximumLineCount: 2
            }
        }

        Item {
            id: toggleContainer
            width: 88
            height: parent.height

            Rectangle {
                id: switchTrack
                width: parent.height * 2
                height: parent.height
                radius: height / 2
                anchors.centerIn: parent
                color: root.checked ? root.primaryColor : "#E0E0E0"

                Behavior on color {
                    ColorAnimation { duration: 200 }
                }
            }

            Rectangle {
                id: switchHandle
                width: parent.height
                height: parent.height
                radius: width / 2
                color: "white"
                border.width: 2
                border.color: root.checked ? root.primaryColor : "#BDBDBD"
                anchors.verticalCenter: switchTrack.verticalCenter
                x: toggleContainer.width / 2 - width / 2 + (root.checked ? 15 : -15)

                Behavior on x {
                    NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
                }
            }

            MouseArea {
                anchors.fill: parent
                enabled: root.interactive
                onClicked: {
                    var requested = !root.checked
                    var ok = false
                    if (root.isPower) {
                        ok = root.winchActions.toggleWinchEnable()
                        if (ok) {
                            root.notifyRequested(requested ? "Winch power enabled" : "Winch power disabled", 2000)
                        } else {
                            root.notifyRequested("Winch power change rejected", 2000)
                        }
                    } else {
                        ok = root.winchActions.toggleLoadDetection()
                        if (ok) {
                            root.notifyRequested(
                                requested ? "Load detection enabled" : "Load detection disabled",
                                2000
                            )
                        } else {
                            root.notifyRequested("Load detection change rejected", 2000)
                        }
                    }
                }
                onPressed: switchHandle.opacity = 0.8
                onReleased: switchHandle.opacity = 1.0
            }
        }
    }
}
