import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    Layout.fillWidth: true
    height: 60
    color: "#F5F5F5"
    radius: 12

    required property var winchStatus
    required property var winchActions
    property color primaryColor: "#2196F3"
    property color dangerColor: "#F44336"
    property color disabledColor: "#BDBDBD"

    signal notifyRequested(string message, int duration)
    signal activityLogged(string activity)

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        Button {
            Layout.fillWidth: true
            text: "Retract Full"
            enabled: root.winchStatus.enabled
            onClicked: {
                if (root.winchActions.retractFull()) {
                    root.notifyRequested("Retracting cable fully", 2000)
                    root.activityLogged("Full retraction initiated")
                } else {
                    root.notifyRequested("Full retract rejected", 2000)
                }
            }

            background: Rectangle {
                radius: 6
                color: parent.enabled ? root.primaryColor : root.disabledColor
            }

            contentItem: Text {
                text: parent.text
                font.pixelSize: 14
                font.bold: true
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Button {
            Layout.fillWidth: true
            Layout.preferredWidth: parent.width * 1.2
            text: "EMERGENCY STOP"
            enabled: root.winchStatus.enabled
            onClicked: {
                if (root.winchActions.emergencyStop()) {
                    root.notifyRequested("EMERGENCY STOP ACTIVATED", 3000)
                    root.activityLogged("Emergency stop activated")
                } else {
                    root.notifyRequested("Emergency stop rejected", 3000)
                }
            }

            background: Rectangle {
                radius: 6
                color: parent.enabled ? root.dangerColor : root.disabledColor

                SequentialAnimation on opacity {
                    running: root.winchStatus.enabled
                    loops: Animation.Infinite
                    PropertyAnimation { to: 0.8; duration: 800 }
                    PropertyAnimation { to: 1.0; duration: 800 }
                }
            }

            contentItem: Text {
                text: parent.text
                font.pixelSize: 14
                font.bold: true
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Button {
            Layout.fillWidth: true
            text: "Extend 1m"
            enabled: root.winchStatus.enabled
            onClicked: {
                if (root.winchActions.extendOneMeter()) {
                    root.notifyRequested("Extending cable by 1m", 2000)
                } else {
                    root.notifyRequested("Extend 1m rejected", 2000)
                }
                root.activityLogged("1m extension initiated")
            }

            background: Rectangle {
                radius: 6
                color: parent.enabled ? root.primaryColor : root.disabledColor
            }

            contentItem: Text {
                text: parent.text
                font.pixelSize: 14
                font.bold: true
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
