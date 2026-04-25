import QtQuick
import QtQuick.Controls
import "../core"

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

        ScrollView {
            id: menuScrollView
            width: parent.width - CommonStyle.spacingXxl - CommonStyle.spacingSm
            anchors {
                top: menuTitleLabel.bottom
                bottom: parent.bottom
                topMargin: CommonStyle.spacingXl
                horizontalCenter: parent.horizontalCenter
                bottomMargin: CommonStyle.spacingXl
            }
            clip: true

            ListView {
                id: optionsList
                width: menuScrollView.width
                model: overlayLayer.controlOptions

                delegate: Rectangle {
                    width: optionsList.width
                    height: CommonStyle.listRowHeight
                    color: "transparent"

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
                }
            }
        }

        Rectangle {
            width: 8
            height: CommonStyle.listRowHeight
            color: CommonStyle.accentPrimary
            radius: 4
            anchors {
                right: parent.left
                rightMargin: -4
            }
            y: menuTitleLabel.height + CommonStyle.spacingXl + (menuOverlay.selectedIndex * CommonStyle.listRowHeight) - optionsList.contentY

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
        }
    }

    JoystickMenuOverlay {
        id: leftMenuContainer
        menuVisible: showLeftMenu
        menuTitle: "Left Joystick Control"
        selectedIndex: leftSelectedIndex
        otherSelectedIndex: rightSelectedIndex
    }

    JoystickMenuOverlay {
        id: rightMenuContainer
        z: 1001
        menuVisible: showRightMenu
        menuTitle: "Right Joystick Control"
        selectedIndex: rightSelectedIndex
        otherSelectedIndex: leftSelectedIndex
    }
}