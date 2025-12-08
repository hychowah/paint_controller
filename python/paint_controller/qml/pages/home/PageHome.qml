import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"

Rectangle {
    id: pageHomeRect
    width: parent.width
    height: parent.height
    color: "#1E1E1E"

    property color availableColor: "#7ED957"
    property color unavailableColor: "#FF5E3A"
    property real ledSize: 24

    // Track video stream availability (persists across source changes)
    property bool baseFrontVideoActive: false
    property bool endEffectorVideoActive: false

    // Auto-start video streams on page load
    Component.onCompleted: {
        console.log("PageHome loaded - starting video streams")
        baseStreamHandler.start_all_streams()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        // Modern Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            color: "#2D2D30"
            
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12

                Text {
                    text: "SYSTEM OVERVIEW"
                    font.pixelSize: 36
                    font.weight: Font.Light
                    font.letterSpacing: 2
                    color: "#FFFFFF"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }

                Rectangle {
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 3
                    radius: 1.5
                    color: "#64B5F6"
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }

        // Main Content - Video Streams with Status
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#1E1E1E"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 24

                // Left Panel - BASE FRONT Camera
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#252526"
                    radius: 12
                    border.color: "#3E3E42"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 16

                        // Header with Status LED
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 60
                            color: "#2D2D30"
                            radius: 8

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 16

                                // Device Icon/Label
                                Rectangle {
                                    Layout.preferredWidth: 50
                                    Layout.preferredHeight: 50
                                    radius: 25
                                    color: "#3E3E42"
                                    border.color: sshHandler.deviceAvailability.BASE ? availableColor : unavailableColor
                                    border.width: 3

                                    Text {
                                        anchors.centerIn: parent
                                        text: "B"
                                        font.pixelSize: 24
                                        font.weight: Font.Bold
                                        color: "#FFFFFF"
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Text {
                                        text: "BASE STATION"
                                        font.pixelSize: 20
                                        font.weight: Font.Medium
                                        color: "#FFFFFF"
                                    }

                                    RowLayout {
                                        spacing: 8

                                        Rectangle {
                                            width: ledSize
                                            height: ledSize
                                            radius: ledSize / 2
                                            color: sshHandler.deviceAvailability.BASE ? availableColor : unavailableColor
                                            border.color: "#FFFFFF"
                                            border.width: 2

                                            // Pulsing animation when available
                                            SequentialAnimation on opacity {
                                                running: sshHandler.deviceAvailability.BASE
                                                loops: Animation.Infinite
                                                NumberAnimation { from: 1.0; to: 0.5; duration: 1000; easing.type: Easing.InOutQuad }
                                                NumberAnimation { from: 0.5; to: 1.0; duration: 1000; easing.type: Easing.InOutQuad }
                                            }
                                        }

                                        Text {
                                            text: sshHandler.deviceAvailability.BASE ? "ONLINE" : "OFFLINE"
                                            font.pixelSize: 14
                                            font.weight: Font.Medium
                                            color: sshHandler.deviceAvailability.BASE ? availableColor : unavailableColor
                                        }
                                    }
                                }

                                // Heartbeat indicator
                                Rectangle {
                                    Layout.preferredWidth: 16
                                    Layout.preferredHeight: 16
                                    radius: 8
                                    color: heartbeatHandler.base_online ? "#4CD964" : "#8E8E93"
                                    
                                    // Heartbeat pulse
                                    SequentialAnimation on scale {
                                        running: heartbeatHandler.base_online
                                        loops: Animation.Infinite
                                        NumberAnimation { from: 1.0; to: 1.3; duration: 300; easing.type: Easing.InOutQuad }
                                        NumberAnimation { from: 1.3; to: 1.0; duration: 300; easing.type: Easing.InOutQuad }
                                        PauseAnimation { duration: 800 }
                                    }
                                }
                            }
                        }

                        // Video Display
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#1E1E1E"
                            radius: 8
                            border.color: "#3E3E42"
                            border.width: 1
                            clip: true

                            Image {
                                id: baseFrontVideo
                                anchors.fill: parent
                                anchors.margins: 2
                                source: "image://base_front_live/latest"
                                fillMode: Image.PreserveAspectFit
                                cache: false
                                asynchronous: false

                                // Status overlay when no video
                                Rectangle {
                                    anchors.fill: parent
                                    color: "#2D2D30"
                                    visible: !baseFrontVideoActive

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 16

                                        Text {
                                            text: "📹"
                                            font.pixelSize: 64
                                            color: "#666666"
                                            Layout.alignment: Qt.AlignHCenter
                                        }

                                        Text {
                                            text: "NO VIDEO SIGNAL"
                                            font.pixelSize: 18
                                            font.weight: Font.Medium
                                            color: "#999999"
                                            Layout.alignment: Qt.AlignHCenter
                                        }

                                        Text {
                                            text: "Waiting for BASE FRONT stream..."
                                            font.pixelSize: 12
                                            color: "#666666"
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }
                                }

                                // Video active indicator overlay (top-right corner)
                                Rectangle {
                                    anchors.top: parent.top
                                    anchors.right: parent.right
                                    anchors.margins: 12
                                    width: 80
                                    height: 30
                                    radius: 15
                                    color: "#000000"
                                    opacity: 0.7
                                    visible: baseFrontVideoActive

                                    RowLayout {
                                        anchors.centerIn: parent
                                        spacing: 6

                                        Rectangle {
                                            width: 10
                                            height: 10
                                            radius: 5
                                            color: "#FF4444"

                                            SequentialAnimation on opacity {
                                                loops: Animation.Infinite
                                                NumberAnimation { from: 1.0; to: 0.3; duration: 800 }
                                                NumberAnimation { from: 0.3; to: 1.0; duration: 800 }
                                            }
                                        }

                                        Text {
                                            text: "LIVE"
                                            font.pixelSize: 12
                                            font.weight: Font.Bold
                                            color: "#FFFFFF"
                                        }
                                    }
                                }
                            }

                            Connections {
                                target: baseStreamHandler
                                function onBaseFrontFrameReady() {
                                    baseFrontVideoActive = true
                                    baseFrontVideo.source = ""
                                    baseFrontVideo.source = "image://base_front_live/latest"
                                }
                            }
                        }

                        // Camera Info Footer
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 40
                            color: "#2D2D30"
                            radius: 8

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 16

                                Text {
                                    text: "📍 Front Camera"
                                    font.pixelSize: 12
                                    color: "#CCCCCC"
                                }

                                Item { Layout.fillWidth: true }

                                Text {
                                    text: "Port: 5002"
                                    font.pixelSize: 10
                                    font.family: "monospace"
                                    color: "#888888"
                                }
                            }
                        }
                    }
                }

                // Right Panel - END EFFECTOR Camera
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#252526"
                    radius: 12
                    border.color: "#3E3E42"
                    border.width: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 16

                        // Header with Status LED
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 60
                            color: "#2D2D30"
                            radius: 8

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 16

                                // Device Icon/Label
                                Rectangle {
                                    Layout.preferredWidth: 50
                                    Layout.preferredHeight: 50
                                    radius: 25
                                    color: "#3E3E42"
                                    border.color: sshHandler.deviceAvailability.END_EFFECTOR ? availableColor : unavailableColor
                                    border.width: 3

                                    Text {
                                        anchors.centerIn: parent
                                        text: "E"
                                        font.pixelSize: 24
                                        font.weight: Font.Bold
                                        color: "#FFFFFF"
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4

                                    Text {
                                        text: "END EFFECTOR"
                                        font.pixelSize: 20
                                        font.weight: Font.Medium
                                        color: "#FFFFFF"
                                    }

                                    RowLayout {
                                        spacing: 8

                                        Rectangle {
                                            width: ledSize
                                            height: ledSize
                                            radius: ledSize / 2
                                            color: sshHandler.deviceAvailability.END_EFFECTOR ? availableColor : unavailableColor
                                            border.color: "#FFFFFF"
                                            border.width: 2

                                            // Pulsing animation when available
                                            SequentialAnimation on opacity {
                                                running: sshHandler.deviceAvailability.END_EFFECTOR
                                                loops: Animation.Infinite
                                                NumberAnimation { from: 1.0; to: 0.5; duration: 1000; easing.type: Easing.InOutQuad }
                                                NumberAnimation { from: 0.5; to: 1.0; duration: 1000; easing.type: Easing.InOutQuad }
                                            }
                                        }

                                        Text {
                                            text: sshHandler.deviceAvailability.END_EFFECTOR ? "ONLINE" : "OFFLINE"
                                            font.pixelSize: 14
                                            font.weight: Font.Medium
                                            color: sshHandler.deviceAvailability.END_EFFECTOR ? availableColor : unavailableColor
                                        }
                                    }
                                }

                                // Heartbeat indicator
                                Rectangle {
                                    Layout.preferredWidth: 16
                                    Layout.preferredHeight: 16
                                    radius: 8
                                    color: heartbeatHandler.ef_online ? "#4CD964" : "#8E8E93"
                                    
                                    // Heartbeat pulse
                                    SequentialAnimation on scale {
                                        running: heartbeatHandler.ef_online
                                        loops: Animation.Infinite
                                        NumberAnimation { from: 1.0; to: 1.3; duration: 300; easing.type: Easing.InOutQuad }
                                        NumberAnimation { from: 1.3; to: 1.0; duration: 300; easing.type: Easing.InOutQuad }
                                        PauseAnimation { duration: 800 }
                                    }
                                }
                            }
                        }

                        // Video Display
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#1E1E1E"
                            radius: 8
                            border.color: "#3E3E42"
                            border.width: 1
                            clip: true

                            Image {
                                id: endEffectorVideo
                                anchors.fill: parent
                                anchors.margins: 2
                                source: "image://ef_live/latest"
                                fillMode: Image.PreserveAspectFit
                                cache: false
                                asynchronous: false

                                // Status overlay when no video
                                Rectangle {
                                    anchors.fill: parent
                                    color: "#2D2D30"
                                    visible: !endEffectorVideoActive

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 16

                                        Text {
                                            text: "📹"
                                            font.pixelSize: 64
                                            color: "#666666"
                                            Layout.alignment: Qt.AlignHCenter
                                        }

                                        Text {
                                            text: "NO VIDEO SIGNAL"
                                            font.pixelSize: 18
                                            font.weight: Font.Medium
                                            color: "#999999"
                                            Layout.alignment: Qt.AlignHCenter
                                        }

                                        Text {
                                            text: "Waiting for END EFFECTOR stream..."
                                            font.pixelSize: 12
                                            color: "#666666"
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }
                                }

                                // Video active indicator overlay (top-right corner)
                                Rectangle {
                                    anchors.top: parent.top
                                    anchors.right: parent.right
                                    anchors.margins: 12
                                    width: 80
                                    height: 30
                                    radius: 15
                                    color: "#000000"
                                    opacity: 0.7
                                    visible: endEffectorVideoActive

                                    RowLayout {
                                        anchors.centerIn: parent
                                        spacing: 6

                                        Rectangle {
                                            width: 10
                                            height: 10
                                            radius: 5
                                            color: "#FF4444"

                                            SequentialAnimation on opacity {
                                                loops: Animation.Infinite
                                                NumberAnimation { from: 1.0; to: 0.3; duration: 800 }
                                                NumberAnimation { from: 0.3; to: 1.0; duration: 800 }
                                            }
                                        }

                                        Text {
                                            text: "LIVE"
                                            font.pixelSize: 12
                                            font.weight: Font.Bold
                                            color: "#FFFFFF"
                                        }
                                    }
                                }
                            }

                            Connections {
                                target: baseStreamHandler
                                function onEndEffectorFrameReady() {
                                    endEffectorVideoActive = true
                                    endEffectorVideo.source = ""
                                    endEffectorVideo.source = "image://ef_live/latest"
                                }
                            }
                        }

                        // Camera Info Footer
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 40
                            color: "#2D2D30"
                            radius: 8

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 16

                                Text {
                                    text: "📍 End Effector Camera"
                                    font.pixelSize: 12
                                    color: "#CCCCCC"
                                }

                                Item { Layout.fillWidth: true }

                                Text {
                                    text: "Port: 5001"
                                    font.pixelSize: 10
                                    font.family: "monospace"
                                    color: "#888888"
                                }
                            }
                        }
                    }
                }
            }
        }

        // Bottom Status Bar
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: "#2D2D30"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 24

                Text {
                    text: "🌐 Network Status"
                    font.pixelSize: 12
                    color: "#CCCCCC"
                }

                Rectangle {
                    width: 1
                    height: 20
                    color: "#3E3E42"
                }

                Text {
                    text: "BASE: " + (heartbeatHandler.base_online ? "Connected" : "Disconnected")
                    font.pixelSize: 11
                    color: heartbeatHandler.base_online ? availableColor : unavailableColor
                }

                Text {
                    text: "EF: " + (heartbeatHandler.ef_online ? "Connected" : "Disconnected")
                    font.pixelSize: 11
                    color: heartbeatHandler.ef_online ? availableColor : unavailableColor
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: "📊 Video Streams Active"
                    font.pixelSize: 11
                    color: "#888888"
                }
            }
        }
    }
}
