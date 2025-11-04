import QtQuick 2.15
import QtQuick.Controls 2.15

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
        color: "#000000"
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
        color: "#000000"
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
        width: 400
        height: Math.min(parent.height * 0.8, 150 + 50 * controlOptions.length)
        anchors.centerIn: parent
        color: "#2c2c2c"
        opacity: 0.9
        radius: 10
        visible: showLeftMenu

        Rectangle {
            visible: activeMenu === "left"
            anchors.fill: parent
            color: "#3498db"
            opacity: 0.1
            radius: 10
        }

        Text {
            id: leftMenuTitle
            text: "Left Joystick Control"
            color: "white"
            font.pixelSize: 24
            font.bold: true
            anchors {
                top: parent.top
                topMargin: 20
                horizontalCenter: parent.horizontalCenter
            }
        }

        ScrollView {
            id: leftScrollView
            width: parent.width - 40
            anchors {
                top: leftMenuTitle.bottom
                bottom: parent.bottom
                topMargin: 20
                horizontalCenter: parent.horizontalCenter
                bottomMargin: 20
            }
            clip: true

            ListView {
                id: leftOptionsList
                width: leftScrollView.width
                model: controlOptions
                delegate: Rectangle {
                    width: leftOptionsList.width
                    height: 50
                    color: "transparent"

                    Rectangle {
                        visible: index === leftSelectedIndex
                        anchors.fill: parent
                        color: "#3498db"
                        opacity: 0.5
                        radius: 5
                    }

                    Text {
                        text: modelData
                        color: {
                            if (index === rightSelectedIndex) return "#ff6b6b"
                            else if (index === leftSelectedIndex) return "white"
                            else return "#cccccc"
                        }
                        font.pixelSize: 18
                        anchors {
                            left: parent.left
                            leftMargin: 20
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
            height: 50
            color: "#3498db"
            radius: 4
            anchors {
                right: parent.left
                rightMargin: -4
            }
            y: leftMenuTitle.height + 20 + (leftSelectedIndex * 50) - leftOptionsList.contentY

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
        width: 400
        height: Math.min(parent.height * 0.8, 150 + 50 * controlOptions.length)
        anchors.centerIn: parent
        color: "#2c2c2c"
        opacity: 0.9
        radius: 10
        visible: showRightMenu

        Rectangle {
            visible: showRightMenu
            anchors.fill: parent
            color: "#3498db"
            opacity: 0.1
            radius: 10
        }

        Text {
            id: rightMenuTitle
            text: "Right Joystick Control"
            color: "white"
            font.pixelSize: 24
            font.bold: true
            anchors {
                top: parent.top
                topMargin: 20
                horizontalCenter: parent.horizontalCenter
            }
        }

        ScrollView {
            id: rightScrollView
            width: parent.width - 40
            anchors {
                top: rightMenuTitle.bottom
                bottom: parent.bottom
                topMargin: 20
                horizontalCenter: parent.horizontalCenter
                bottomMargin: 20
            }
            clip: true

            ListView {
                id: rightOptionsList
                width: rightScrollView.width
                model: controlOptions
                delegate: Rectangle {
                    width: rightOptionsList.width
                    height: 50
                    color: "transparent"

                    Rectangle {
                        visible: index === rightSelectedIndex
                        anchors.fill: parent
                        color: "#3498db"
                        opacity: 0.5
                        radius: 5
                    }

                    Text {
                        text: modelData
                        color: {
                            if (index === leftSelectedIndex) return "#ff6b6b"
                            else if (index === rightSelectedIndex) return "white"
                            else return "#cccccc"
                        }
                        font.pixelSize: 18
                        anchors {
                            left: parent.left
                            leftMargin: 20
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
            height: 50
            color: "#3498db"
            radius: 4
            anchors {
                right: parent.left
                rightMargin: -4
            }
            y: rightMenuTitle.height + 20 + (rightSelectedIndex * 50) - rightOptionsList.contentY

            Behavior on y {
                NumberAnimation {
                    duration: 150
                    easing.type: Easing.OutQuad
                }
            }
        }
    }
}