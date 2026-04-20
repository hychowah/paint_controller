import QtQuick
import QtQuick.Controls
import "../core"

Item {
    id: overlayLayer
    
    // Helper function to calculate item Y position considering scroll offset
    function getItemYPosition(listView, index) {
        return listView.contentY + (index * 50)
    }
    
    // Properties to be bound from parent
    property bool showOverlay: false
    property int leftSelectedIndex: 0
    property int rightSelectedIndex: 0
    property string activeMenu: ""
    property var controlOptions: []
    property bool showLeftMenu: showOverlay && activeMenu === "left"
    property bool showRightMenu: showOverlay && activeMenu === "right"

    // Left menu overlay background
    Rectangle {
        id: leftOverlayBackground
        anchors.fill: parent
        color: CommonStyle.overlayScrim
        opacity: 0.7
        visible: showLeftMenu

        MouseArea {
            anchors.fill: parent
            enabled: showLeftMenu
        }
    }

    // Right menu overlay background
    Rectangle {
        id: rightOverlayBackground
        anchors.fill: parent
        color: CommonStyle.overlayScrim
        opacity: 0.7
        visible: showRightMenu

        MouseArea {
            anchors.fill: parent
            enabled: showRightMenu
        }
    }

    // Left menu container
    Rectangle {
        id: leftMenuContainer
        width: Math.round(400 * CommonStyle.scaleFactor)
        height: Math.min(parent.height * 0.8, Math.round(150 * CommonStyle.scaleFactor) + CommonStyle.listRowHeight * controlOptions.length)
        anchors.centerIn: parent
        color: CommonStyle.backgroundL0
        opacity: 0.9
        radius: CommonStyle.radiusMd
        visible: showLeftMenu

        Rectangle {
            visible: activeMenu === "left"
            anchors.fill: parent
            color: CommonStyle.accentPrimary
            opacity: 0.1
            radius: CommonStyle.radiusMd
        }

        Text {
            id: leftMenuTitle
            text: "Left Joystick Control"
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
            id: leftScrollView
            width: parent.width - CommonStyle.spacingXxl - CommonStyle.spacingSm
            anchors {
                top: leftMenuTitle.bottom
                bottom: parent.bottom
                topMargin: CommonStyle.spacingXl
                horizontalCenter: parent.horizontalCenter
                bottomMargin: CommonStyle.spacingXl
            }
            clip: true

            ListView {
                id: leftOptionsList
                width: leftScrollView.width
                model: controlOptions
                delegate: Rectangle {
                    width: leftOptionsList.width
                    height: CommonStyle.listRowHeight
                    color: "transparent"

                    Rectangle {
                        visible: index === leftSelectedIndex
                        anchors.fill: parent
                        color: CommonStyle.accentPrimary
                        opacity: 0.5
                        radius: CommonStyle.radiusSm
                    }

                    Text {
                        text: modelData
                        color: {
                            if (index === rightSelectedIndex) return CommonStyle.statusError
                            else if (index === leftSelectedIndex) return CommonStyle.textPrimary
                            else return CommonStyle.textSecondary
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
        
        // Auto-scroll to keep selected item visible
        Connections {
            target: overlayLayer
            function onLeftSelectedIndexChanged() {
                leftOptionsList.positionViewAtIndex(overlayLayer.leftSelectedIndex, ListView.Contain)
            }
        }

        Rectangle {
            id: leftSelectionIndicator
            width: 8
            height: CommonStyle.listRowHeight
            color: CommonStyle.accentPrimary
            radius: 4
            anchors {
                right: parent.left
                rightMargin: -4
            }
            y: leftMenuTitle.height + CommonStyle.spacingXl + (leftSelectedIndex * CommonStyle.listRowHeight) - leftOptionsList.contentY

            Behavior on y {
                NumberAnimation {
                    duration: 150
                    easing.type: Easing.OutQuad
                }
            }
        }
    }

    // Right menu container
    Rectangle {
        id: rightMenuContainer
        z: 1001
        width: Math.round(400 * CommonStyle.scaleFactor)
        height: Math.min(parent.height * 0.8, Math.round(150 * CommonStyle.scaleFactor) + CommonStyle.listRowHeight * controlOptions.length)
        anchors.centerIn: parent
        color: CommonStyle.backgroundL0
        opacity: 0.9
        radius: CommonStyle.radiusMd
        visible: showRightMenu

        Rectangle {
            visible: showRightMenu
            anchors.fill: parent
            color: CommonStyle.accentPrimary
            opacity: 0.1
            radius: CommonStyle.radiusMd
        }

        Text {
            id: rightMenuTitle
            text: "Right Joystick Control"
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
            id: rightScrollView
            width: parent.width - CommonStyle.spacingXxl - CommonStyle.spacingSm
            anchors {
                top: rightMenuTitle.bottom
                bottom: parent.bottom
                topMargin: CommonStyle.spacingXl
                horizontalCenter: parent.horizontalCenter
                bottomMargin: CommonStyle.spacingXl
            }
            clip: true

            ListView {
                id: rightOptionsList
                width: rightScrollView.width
                model: controlOptions
                delegate: Rectangle {
                    width: rightOptionsList.width
                    height: CommonStyle.listRowHeight
                    color: "transparent"

                    Rectangle {
                        visible: index === rightSelectedIndex
                        anchors.fill: parent
                        color: CommonStyle.accentPrimary
                        opacity: 0.5
                        radius: CommonStyle.radiusSm
                    }

                    Text {
                        text: modelData
                        color: {
                            if (index === leftSelectedIndex) return CommonStyle.statusError
                            else if (index === rightSelectedIndex) return CommonStyle.textPrimary
                            else return CommonStyle.textSecondary
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
        
        // Auto-scroll to keep selected item visible
        Connections {
            target: overlayLayer
            function onRightSelectedIndexChanged() {
                rightOptionsList.positionViewAtIndex(overlayLayer.rightSelectedIndex, ListView.Contain)
            }
        }

        Rectangle {
            id: rightSelectionIndicator
            width: 8
            height: CommonStyle.listRowHeight
            color: CommonStyle.accentPrimary
            radius: 4
            anchors {
                right: parent.left
                rightMargin: -4
            }
            y: rightMenuTitle.height + CommonStyle.spacingXl + (rightSelectedIndex * CommonStyle.listRowHeight) - rightOptionsList.contentY

            Behavior on y {
                NumberAnimation {
                    duration: 150
                    easing.type: Easing.OutQuad
                }
            }
        }
    }
}