import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"

Rectangle {
    id: pageHomeRect
    width: parent.width
    height: parent.height
    color: "#1E1E1E"
    required property var shellConnectivityStatus
    required property var videoRuntime

    property color availableColor: "#7ED957"
    property color unavailableColor: "#FF5E3A"
    property real ledSize: 24
    property int baseFrontFrameRevision: 0
    property int endEffectorFrameRevision: 0
    readonly property bool baseFrontVideoActive: baseFrontFrameRevision > 0
    readonly property bool endEffectorVideoActive: endEffectorFrameRevision > 0

    Connections {
        target: videoRuntime ? videoRuntime.feeds : null

        function onBaseFrontFrameReady() {
            baseFrontFrameRevision += 1
        }

        function onEndEffectorFrameReady() {
            endEffectorFrameRevision += 1
        }
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

                HomeVideoPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    badgeText: "B"
                    titleText: "BASE STATION"
                    reachable: shellConnectivityStatus.baseReachable
                    online: shellConnectivityStatus.baseOnline
                    videoActive: pageHomeRect.baseFrontVideoActive
                    waitingText: "Waiting for BASE FRONT stream..."
                    locationText: "📍 Front Camera"
                    portText: "Port: 5002"
                    imageSource: "image://base_front_live/latest"
                    frameRevision: pageHomeRect.baseFrontFrameRevision
                    availableColor: pageHomeRect.availableColor
                    unavailableColor: pageHomeRect.unavailableColor
                    ledSize: pageHomeRect.ledSize
                }

                HomeVideoPanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    badgeText: "E"
                    titleText: "END EFFECTOR"
                    reachable: shellConnectivityStatus.endEffectorReachable
                    online: shellConnectivityStatus.endEffectorOnline
                    videoActive: pageHomeRect.endEffectorVideoActive
                    waitingText: "Waiting for END EFFECTOR stream..."
                    locationText: "📍 End Effector Camera"
                    portText: "Port: 5001"
                    imageSource: "image://ef_live/latest"
                    frameRevision: pageHomeRect.endEffectorFrameRevision
                    availableColor: pageHomeRect.availableColor
                    unavailableColor: pageHomeRect.unavailableColor
                    ledSize: pageHomeRect.ledSize
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
                    text: "BASE: " + (shellConnectivityStatus.baseOnline ? "Connected" : "Disconnected")
                    font.pixelSize: 11
                    color: shellConnectivityStatus.baseOnline ? availableColor : unavailableColor
                }

                Text {
                    text: "EF: " + (shellConnectivityStatus.endEffectorOnline ? "Connected" : "Disconnected")
                    font.pixelSize: 11
                    color: shellConnectivityStatus.endEffectorOnline ? availableColor : unavailableColor
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
