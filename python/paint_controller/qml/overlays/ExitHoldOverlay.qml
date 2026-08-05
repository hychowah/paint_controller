import QtQuick
import QtQuick.Layouts
import "../theme"

/**
 * Hold-to-exit progress chrome for the Steam Deck Switch button.
 * Policy (3s threshold, quit) lives in Python ExitHoldHandler; this is display only.
 */
Item {
    id: root
    required property var qtBridge
    anchors.fill: parent
    z: 1900

    property real progress: 0.0
    property real currentDuration: 0.0
    property real targetDuration: 1.0

    property bool shouldBeVisible: false
    property bool isAnimating: false

    readonly property color backgroundColor: CommonStyle.cardBackground
    readonly property color accentColor: CommonStyle.statusWarning
    readonly property color primaryText: CommonStyle.textPrimary
    readonly property color secondaryText: CommonStyle.textSecondary
    readonly property color borderColor: CommonStyle.statusWarning
    readonly property color progressBackground: CommonStyle.backgroundL2

    Connections {
        target: root.qtBridge
        function onExit_overlay_changed(visible, currentDuration, targetDuration) {
            if (visible !== root.shouldBeVisible) {
                root.shouldBeVisible = visible

                if (visible) {
                    overlay.visible = true
                    dimmer.visible = true
                    root.progress = 0
                    showAnimation.start()
                } else {
                    root.progress = 0
                    root.currentDuration = 0
                    hideAnimation.start()
                }
            }

            if (visible) {
                root.progress = targetDuration > 0 ? currentDuration / targetDuration : 0
                root.currentDuration = currentDuration
                root.targetDuration = targetDuration
            }
        }
    }

    Rectangle {
        id: dimmer
        anchors.fill: parent
        color: CommonStyle.overlayScrim
        opacity: 0
        visible: false

        MouseArea {
            anchors.fill: parent
            enabled: dimmer.visible
        }
    }

    Rectangle {
        id: overlay
        anchors.centerIn: parent
        width: Math.round(480 * CommonStyle.scaleFactor)
        height: Math.round(240 * CommonStyle.scaleFactor)
        color: backgroundColor
        radius: CommonStyle.radiusLg
        border.color: borderColor
        border.width: CommonStyle.borderWidthThick
        visible: false
        opacity: 0
        scale: 0.9

        ColumnLayout {
            anchors.centerIn: parent
            anchors.margins: CommonStyle.spacingXxl + CommonStyle.spacingSm
            spacing: CommonStyle.spacingXxl

            ColumnLayout {
                spacing: CommonStyle.spacingMd
                Layout.alignment: Qt.AlignHCenter

                Rectangle {
                    width: Math.round(48 * CommonStyle.scaleFactor)
                    height: Math.round(48 * CommonStyle.scaleFactor)
                    radius: 24
                    color: accentColor
                    Layout.alignment: Qt.AlignHCenter

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: CommonStyle.textPrimary
                        font.pixelSize: Math.round(24 * CommonStyle.scaleFactor)
                        font.bold: true
                    }
                }

                Text {
                    text: "EXIT APP"
                    color: primaryText
                    font.pixelSize: CommonStyle.fontDisplay
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "Hold Switch to quit"
                    color: secondaryText
                    font.pixelSize: CommonStyle.fontCaption
                    Layout.alignment: Qt.AlignHCenter
                }
            }

            ColumnLayout {
                spacing: CommonStyle.spacingMd
                Layout.fillWidth: true

                Rectangle {
                    Layout.fillWidth: true
                    height: CommonStyle.spacingSm
                    color: progressBackground
                    radius: 4

                    Rectangle {
                        id: progressBar
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: parent.width * progress
                        color: accentColor
                        radius: 4

                        Behavior on width {
                            enabled: root.shouldBeVisible && progress > 0
                            NumberAnimation {
                                duration: 50
                                easing.type: Easing.OutQuart
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: `${Math.round(progress * 100)}%`
                        color: accentColor
                        font.pixelSize: CommonStyle.fontBody + 2
                        font.bold: true
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: `${currentDuration.toFixed(1)} / ${targetDuration.toFixed(1)} s`
                        color: secondaryText
                        font.pixelSize: CommonStyle.fontCaption
                    }
                }
            }
        }

        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            border.color: accentColor
            border.width: progress > 0.8 ? 3 : 2
            color: "transparent"
            visible: progress > 0.8

            Behavior on border.width {
                NumberAnimation {
                    duration: 150
                    easing.type: Easing.InOutQuad
                }
            }
        }
    }

    ParallelAnimation {
        id: showAnimation

        onStarted: root.isAnimating = true
        onStopped: root.isAnimating = false

        PropertyAnimation {
            target: overlay
            property: "opacity"
            from: 0
            to: 1
            duration: 250
            easing.type: Easing.OutQuart
        }

        PropertyAnimation {
            target: overlay
            property: "scale"
            from: 0.9
            to: 1.0
            duration: 250
            easing.type: Easing.OutQuart
        }

        PropertyAnimation {
            target: dimmer
            property: "opacity"
            from: 0
            to: 0.85
            duration: 250
            easing.type: Easing.OutQuart
        }
    }

    ParallelAnimation {
        id: hideAnimation

        onStarted: {
            root.isAnimating = true
            root.progress = 0
            root.currentDuration = 0
        }

        onStopped: {
            root.isAnimating = false
            overlay.visible = false
            dimmer.visible = false
        }

        PropertyAnimation {
            target: overlay
            property: "opacity"
            from: 1
            to: 0
            duration: 200
            easing.type: Easing.InQuart
        }

        PropertyAnimation {
            target: overlay
            property: "scale"
            from: 1.0
            to: 0.9
            duration: 200
            easing.type: Easing.InQuart
        }

        PropertyAnimation {
            target: dimmer
            property: "opacity"
            from: 0.85
            to: 0
            duration: 200
            easing.type: Easing.InQuart
        }

        PropertyAnimation {
            target: progressBar
            property: "width"
            to: 0
            duration: 200
            easing.type: Easing.InQuart
        }
    }
}
