import QtQuick
import QtQuick.Controls
import "../theme"

Item {
    id: overlayLayer

    component JoystickMenuOverlay: Rectangle {
        id: menuOverlay

        required property bool menuVisible
        required property string menuTitle
        required property int selectedIndex
        required property int otherSelectedIndex

        width: Math.round(400 * CommonStyle.scaleFactor)
        height: Math.min(parent.height * 0.8, Math.round(150 * CommonStyle.scaleFactor) + CommonStyle.listRowHeight * overlayLayer.controlOptions.length)
        anchors.centerIn: parent
        color: CommonStyle.backgroundL0
        opacity: 0.9
        radius: CommonStyle.radiusMd
        visible: menuVisible

        // Block touches on the menu background from falling through to the scrim.
        MouseArea {
            anchors.fill: parent
            onPressed: mouse => mouse.accepted = true
            onClicked: mouse => mouse.accepted = true
        }

        onSelectedIndexChanged: {
            if (selectedIndex >= 0) {
                optionsList.positionViewAtIndex(selectedIndex, ListView.Contain)
            }
        }

        Rectangle {
            visible: menuOverlay.menuVisible
            anchors.fill: parent
            color: CommonStyle.accentPrimary
            opacity: 0.1
            radius: CommonStyle.radiusMd
        }

        Text {
            id: menuTitleLabel
            text: menuOverlay.menuTitle
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontDisplay
            font.bold: true
            anchors {
                top: parent.top
                topMargin: CommonStyle.spacingXl
                horizontalCenter: parent.horizontalCenter
            }
        }

        ListView {
            id: optionsList
            objectName: "joystickOptionsList"
            width: parent.width - CommonStyle.spacingXxl - CommonStyle.spacingSm
            anchors {
                top: menuTitleLabel.bottom
                bottom: parent.bottom
                topMargin: CommonStyle.spacingXl
                horizontalCenter: parent.horizontalCenter
                bottomMargin: CommonStyle.spacingXl
            }
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: overlayLayer.controlOptions

            delegate: Rectangle {
                id: delegateRoot
                width: optionsList.width
                height: CommonStyle.listRowHeight
                color: "transparent"
                objectName: "joystickMenuDelegate"
                property bool visuallyPressed: false

                Rectangle {
                    visible: index === menuOverlay.selectedIndex
                    anchors.fill: parent
                    color: CommonStyle.accentPrimary
                    opacity: 0.5
                    radius: CommonStyle.radiusSm
                }

                Text {
                    text: modelData
                    color: {
                        if (index === menuOverlay.otherSelectedIndex) return CommonStyle.statusError
                        if (index === menuOverlay.selectedIndex) return CommonStyle.textPrimary
                        return CommonStyle.textSecondary
                    }
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody + 2
                    anchors {
                        left: parent.left
                        leftMargin: CommonStyle.spacingXl
                        verticalCenter: parent.verticalCenter
                    }
                }

                MouseArea {
                    id: delegateMouse
                    anchors.fill: parent
                    onPressed: delegateRoot.visuallyPressed = true
                    onClicked: commitTimer.start()
                    onCanceled: delegateRoot.visuallyPressed = false
                    onExited: {
                        if (!commitTimer.running) delegateRoot.visuallyPressed = false
                    }

                    Timer {
                        id: commitTimer
                        objectName: "joystickCommitTimer"
                        interval: 150
                        repeat: false
                        onTriggered: {
                            delegateRoot.visuallyPressed = false
                            overlayLayer.overlayController.select_index(index)
                        }
                    }
                }

                // Touch-down feedback: high-contrast highlight that lingers
                // briefly after release so the operator sees what was tapped.
                Rectangle {
                    id: pressedFeedback
                    objectName: "joystickPressedFeedback"
                    visible: delegateRoot.visuallyPressed && menuOverlay.menuVisible
                    anchors.fill: parent
                    color: CommonStyle.accentPrimary
                    opacity: 0.5
                    border.color: CommonStyle.borderFocused
                    border.width: CommonStyle.borderWidthThick
                    radius: CommonStyle.radiusSm
                }
            }
        }

        // Proportional scrollbar thumb aligned to the ListView viewport.
        Rectangle {
            width: 8
            radius: 4
            color: CommonStyle.accentPrimary
            anchors {
                right: parent.left
                rightMargin: -4
            }
            visible: optionsList.contentHeight > optionsList.height

            readonly property real listViewTopY: menuTitleLabel.height + 2 * CommonStyle.spacingXl
            readonly property real viewportHeight: optionsList.height
            readonly property real maxContentY: Math.max(0, optionsList.contentHeight - viewportHeight)

            height: Math.max(
                20,
                viewportHeight * Math.min(1, viewportHeight / Math.max(optionsList.contentHeight, 1))
            )
            y: listViewTopY + (maxContentY > 0
                ? (optionsList.contentY / maxContentY) * (viewportHeight - height)
                : 0)

            Behavior on y {
                NumberAnimation {
                    duration: 150
                    easing.type: Easing.OutQuad
                }
            }
        }
    }

    // Properties to be bound from parent
    required property bool showOverlay
    required property int leftSelectedIndex
    required property int rightSelectedIndex
    required property string activeMenu
    required property var controlOptions
    required property var overlayController
    property bool showLeftMenu: showOverlay && activeMenu === "left"
    property bool showRightMenu: showOverlay && activeMenu === "right"

    Rectangle {
        anchors.fill: parent
        color: CommonStyle.overlayScrim
        opacity: 0.7
        visible: showLeftMenu || showRightMenu

        MouseArea {
            anchors.fill: parent
            enabled: parent.visible
            onClicked: overlayLayer.overlayController.hide_menu()
        }
    }

    JoystickMenuOverlay {
        id: leftMenuContainer
        objectName: "leftMenuContainer"
        z: 1000
        menuVisible: showLeftMenu
        menuTitle: "Left Joystick Control"
        selectedIndex: leftSelectedIndex
        otherSelectedIndex: rightSelectedIndex
    }

    JoystickMenuOverlay {
        id: rightMenuContainer
        objectName: "rightMenuContainer"
        z: 1001
        menuVisible: showRightMenu
        menuTitle: "Right Joystick Control"
        selectedIndex: rightSelectedIndex
        otherSelectedIndex: leftSelectedIndex
    }
}
