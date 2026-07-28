import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"
import "./components"

Item {
    id: winchPageRoot
    objectName: "winchPageRoot"
    required property var winchStatus
    // winchActions is the ambient root-context model (same as pre-extract PageWinch).
    Layout.fillWidth: true
    Layout.fillHeight: true

    property color primaryColor: "#2196F3"
    property color dangerColor: "#F44336"
    property color successColor: "#4CAF50"
    property color warningColor: "#FF9800"
    property color disabledColor: "#BDBDBD"

    function logActivity(activity) {
        activityModel.insert(0, {
            timestamp: new Date().toLocaleTimeString(Qt.locale(), "hh:mm:ss"),
            activity: activity
        })
    }

    WinchNotificationPopup {
        id: notificationPopup
        x: (winchPageRoot.width - width) / 2
        y: winchPageRoot.height - height - 20
        parent: winchPageRoot
    }

    Rectangle {
        id: dataRect
        width: Math.min(parent.width * 0.95, 1200)
        height: Math.min(parent.height * 0.9, 680)
        anchors.centerIn: parent
        color: "#E2E2E2"
        radius: 20
        border.width: 1
        border.color: "#CCCCCC"

        RowLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 15

            // Left: controls
            Rectangle {
                Layout.preferredWidth: parent.width * 0.6
                Layout.fillHeight: true
                color: "#FFFFFF"
                radius: 15
                border.width: 1
                border.color: "#E0E0E0"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 15

                    Rectangle {
                        Layout.fillWidth: true
                        height: 50
                        color: winchPageRoot.winchStatus.available ? "#E3F2FD" : "#FFEBEE"
                        radius: 12

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10

                            Rectangle {
                                width: 12
                                height: 12
                                radius: 6
                                color: winchPageRoot.winchStatus.available ? primaryColor : dangerColor

                                SequentialAnimation on opacity {
                                    running: winchPageRoot.winchStatus.available
                                    loops: Animation.Infinite
                                    PropertyAnimation { to: 0.6; duration: 1000 }
                                    PropertyAnimation { to: 1.0; duration: 1000 }
                                }
                            }

                            Text {
                                text: "Winch Control"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }

                            Item { Layout.fillWidth: true }

                            Text {
                                text: winchPageRoot.winchStatus.available ? "Connected" : "Disconnected"
                                color: winchPageRoot.winchStatus.available ? primaryColor : dangerColor
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }
                    }

                    WinchEnableToggle {
                        winchStatus: winchPageRoot.winchStatus
                        winchActions: winchActions
                        mode: "power"
                        primaryColor: winchPageRoot.primaryColor
                        disabledColor: winchPageRoot.disabledColor
                        onNotifyRequested: (message, duration) => notificationPopup.show(message, duration)
                    }

                    WinchEnableToggle {
                        winchStatus: winchPageRoot.winchStatus
                        winchActions: winchActions
                        mode: "load"
                        primaryColor: winchPageRoot.primaryColor
                        disabledColor: winchPageRoot.disabledColor
                        onNotifyRequested: (message, duration) => notificationPopup.show(message, duration)
                    }

                    Rectangle {
                        id: historyLog
                        Layout.fillWidth: true
                        height: 80
                        color: "#F5F5F5"
                        radius: 12
                        visible: winchPageRoot.winchStatus.enabled

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 5

                            Text {
                                text: "Recent Activity"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#212121"
                            }

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: ListModel { id: activityModel }
                                delegate: Text {
                                    text: timestamp + ": " + activity
                                    font.pixelSize: 12
                                    color: "#424242"
                                }

                                Component.onCompleted: {
                                    activityModel.append({ timestamp: "10:42:15", activity: "Cable extended to 1800mm" })
                                    activityModel.append({ timestamp: "10:40:03", activity: "System initialized" })
                                }
                            }
                        }
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        columns: 2
                        rowSpacing: 15
                        columnSpacing: 15

                        WinchMoveIncrementPanel {
                            winchStatus: winchPageRoot.winchStatus
                            winchActions: winchActions
                            primaryColor: winchPageRoot.primaryColor
                            dangerColor: winchPageRoot.dangerColor
                            disabledColor: winchPageRoot.disabledColor
                            onNotifyRequested: (message, duration) => notificationPopup.show(message, duration)
                            onActivityLogged: (activity) => winchPageRoot.logActivity(activity)
                        }

                        WinchMoveAbsolutePanel {
                            winchStatus: winchPageRoot.winchStatus
                            winchActions: winchActions
                            primaryColor: winchPageRoot.primaryColor
                            dangerColor: winchPageRoot.dangerColor
                            disabledColor: winchPageRoot.disabledColor
                            onNotifyRequested: (message, duration) => notificationPopup.show(message, duration)
                            onActivityLogged: (activity) => winchPageRoot.logActivity(activity)
                        }
                    }

                    WinchQuickActionsBar {
                        winchStatus: winchPageRoot.winchStatus
                        winchActions: winchActions
                        primaryColor: winchPageRoot.primaryColor
                        dangerColor: winchPageRoot.dangerColor
                        disabledColor: winchPageRoot.disabledColor
                        onNotifyRequested: (message, duration) => notificationPopup.show(message, duration)
                        onActivityLogged: (activity) => winchPageRoot.logActivity(activity)
                    }
                }
            }

            // Right: telemetry
            WinchTelemetryPanel {
                winchStatus: winchPageRoot.winchStatus
                primaryColor: winchPageRoot.primaryColor
                dangerColor: winchPageRoot.dangerColor
                onNotifyRequested: (message, duration) => notificationPopup.show(message, duration)
            }
        }
    }
}
