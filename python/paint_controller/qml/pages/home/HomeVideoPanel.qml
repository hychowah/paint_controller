import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    required property string badgeText
    required property string titleText
    required property bool reachable
    required property bool online
    required property bool videoActive
    required property string waitingText
    required property string locationText
    required property string portText
    required property string imageSource
    required property int frameRevision
    required property color availableColor
    required property color unavailableColor
    property real ledSize: 24

    color: "#252526"
    radius: 12
    border.color: "#3E3E42"
    border.width: 2

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#2D2D30"
            radius: 8

            RowLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 16

                Rectangle {
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 50
                    radius: 25
                    color: "#3E3E42"
                    border.color: root.reachable ? root.availableColor : root.unavailableColor
                    border.width: 3

                    Text {
                        anchors.centerIn: parent
                        text: root.badgeText
                        font.pixelSize: 24
                        font.weight: Font.Bold
                        color: "#FFFFFF"
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Text {
                        text: root.titleText
                        font.pixelSize: 20
                        font.weight: Font.Medium
                        color: "#FFFFFF"
                    }

                    RowLayout {
                        spacing: 8

                        Rectangle {
                            width: root.ledSize
                            height: root.ledSize
                            radius: root.ledSize / 2
                            color: root.reachable ? root.availableColor : root.unavailableColor
                            border.color: "#FFFFFF"
                            border.width: 2

                            SequentialAnimation on opacity {
                                running: root.reachable
                                loops: Animation.Infinite
                                NumberAnimation { from: 1.0; to: 0.5; duration: 1000; easing.type: Easing.InOutQuad }
                                NumberAnimation { from: 0.5; to: 1.0; duration: 1000; easing.type: Easing.InOutQuad }
                            }
                        }

                        Text {
                            text: root.reachable ? "ONLINE" : "OFFLINE"
                            font.pixelSize: 14
                            font.weight: Font.Medium
                            color: root.reachable ? root.availableColor : root.unavailableColor
                        }
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    radius: 8
                    color: root.online ? "#4CD964" : "#8E8E93"

                    SequentialAnimation on scale {
                        running: root.online
                        loops: Animation.Infinite
                        NumberAnimation { from: 1.0; to: 1.3; duration: 300; easing.type: Easing.InOutQuad }
                        NumberAnimation { from: 1.3; to: 1.0; duration: 300; easing.type: Easing.InOutQuad }
                        PauseAnimation { duration: 800 }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#1E1E1E"
            radius: 8
            border.color: "#3E3E42"
            border.width: 1
            clip: true

            Image {
                anchors.fill: parent
                anchors.margins: 2
                source: root.imageSource + "?rev=" + root.frameRevision
                fillMode: Image.PreserveAspectFit
                cache: false
                asynchronous: false

                Rectangle {
                    anchors.fill: parent
                    color: "#2D2D30"
                    visible: !root.videoActive

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
                            text: root.waitingText
                            font.pixelSize: 12
                            color: "#666666"
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                Rectangle {
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.margins: 12
                    width: 80
                    height: 30
                    radius: 15
                    color: "#000000"
                    opacity: 0.7
                    visible: root.videoActive

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
        }

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
                    text: root.locationText
                    font.pixelSize: 12
                    color: "#CCCCCC"
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: root.portText
                    font.pixelSize: 10
                    font.family: "monospace"
                    color: "#888888"
                }
            }
        }
    }
}