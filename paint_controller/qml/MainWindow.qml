import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    visibility: Window.FullScreen
    property var screens: Qt.application.screens
    property var targetScreen: screens.length > 1 ? screens[0] : screens[0]
    
    x: targetScreen.virtualX
    y: targetScreen.virtualY
    width: targetScreen.width
    height: targetScreen.height

    // Controller bindings
    property bool showOverlay: overlayController.show_overlay
    property int leftSelectedIndex: overlayController.left_selected_index
    property int rightSelectedIndex: overlayController.right_selected_index
    property string activeMenu: overlayController.active_menu
    property var controlOptions: overlayController.control_options
    property bool showLeftMenu: showOverlay && activeMenu === "left"
    property bool showRightMenu: showOverlay && activeMenu === "right"
    
    // Main content
    Rectangle {
        id: background
        anchors.fill: parent
        color: "#5E5C64"
        
        RowLayout {
            anchors.fill: parent
            spacing: 10
            
            SelectBar {
                id: selectBar
                stackView: stackView
                Layout.fillHeight: true
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#5E5C64"
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0
                    
                    TopBar {
                        Layout.fillWidth: true
                        Component.onCompleted: {
                            for(var i = 0; i < children.length; i++) {
                                var child = children[i];
                                if (child.objectName === "topBar") {
                                    child.uiData = uiData;
                                }
                            }
                        }
                    }
                    
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        
                        StackView {
                            id: stackView
                            objectName: "stackView"
                            anchors.fill: parent
                            initialItem: page1Component
                            
                            property int currentIndex: 0
                            property int targetIndex: 0
                            
                            replaceEnter: Transition {
                                NumberAnimation {
                                    property: "y"
                                    from: stackView.currentIndex > stackView.targetIndex ? -stackView.height : stackView.height
                                    to: 0
                                    duration: 400
                                    easing.type: Easing.InOutQuad
                                }
                            }
                            
                            replaceExit: Transition {
                                NumberAnimation {
                                    property: "y"
                                    from: 0
                                    to: stackView.currentIndex > stackView.targetIndex ? stackView.height : -stackView.height
                                    duration: 400
                                    easing.type: Easing.InOutQuad
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Components
    Component {
        id: page1Component
        Page1 {}
    }
    
    Component {
        id: page2Component
        Page2 {}
    }
    
    Component {
        id: page3Component
        Page3 {}
    }

    Component {
        id: page4Component
        Page4 {}
    }

    // Overlay layer
    Item {
        id: overlayLayer
        anchors.fill: parent
        z: 1000  // Ensure it's above everything else

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
            height: parent.height * 0.8
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

            ListView {
                id: leftOptionsList
                width: parent.width - 40
                anchors {
                    top: leftMenuTitle.bottom
                    bottom: parent.bottom
                    topMargin: 20
                    horizontalCenter: parent.horizontalCenter
                }
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
                y: leftMenuTitle.height + 20 + (leftSelectedIndex * 50)

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
            height: parent.height * 0.8
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

            ListView {
                id: rightOptionsList
                width: parent.width - 40
                anchors {
                    top: rightMenuTitle.bottom
                    bottom: parent.bottom
                    topMargin: 20
                    horizontalCenter: parent.horizontalCenter
                }
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
                y: rightMenuTitle.height + 20 + (rightSelectedIndex * 50)

                Behavior on y {
                    NumberAnimation {
                        duration: 150
                        easing.type: Easing.OutQuad
                    }
                }
            }
        }
    }
}

