import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    visibility: Window.FullScreen
    property var screens: Qt.application.screens
    property var targetScreen: screens.length > 1 ? screens[0] : screens[0]

    property int sidebarWidth: 150 // Initial value (expanded width)
    
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
    property bool showPowerMenu: showOverlay && activeMenu === "power"
    
    // Main content
    Rectangle {
        id: background
        anchors.fill: parent
        color: "#5E5C64"
        
        RowLayout {
            anchors.fill: parent
            spacing: 10
            
            Item {
                id: contentContainer
                anchors.fill: parent
                
                SelectBar {
                    id: selectBar
                    objectName: "selectBar"
                    stackView: stackView
                    height: parent.height
                    // Connect to the signal
                    onExpandedStateChanged: {
                        sidebarWidth = newWidth
                        // Force layout update - the key part!
                        contentLayout.anchors.leftMargin = sidebarWidth
                    }
                }
                
                // Main content with dynamic margin
                Item {
                    id: contentLayout
                    anchors.left: parent.left
                    anchors.leftMargin: sidebarWidth // Bind to the sidebar width
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    
                    // Animation for smooth transition
                    Behavior on anchors.leftMargin {
                        NumberAnimation { 
                            duration: 250
                            easing.type: Easing.InOutQuad
                        }
                    }
                    
                    Rectangle {
                        id: contentRect
                        anchors.fill: parent
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
        }
    }

    // Components
    Component {
        id: page1Component
        PageWheel {}
    }
    
    Component {
        id: page2Component
        PageWinch {}
    }
    
    Component {
        id: page3Component
        PageStatus {}
    }

    Component {
        id: page4Component
        PageTuning {}
    }

    Component {
        id: page7Component
        PageTrajectory {}
    }

    PowerControlMenu {
        anchors.fill: parent
        id: powerControlMenu
        z: 1001
        showOverlay: overlayController.show_overlay
        activeMenu: overlayController.active_menu
    }

    CustomPopup {
        id: messagePopup
        // This is referenced from Python code
        objectName: "messagePopup"
    }

    OverlayLayer {
        anchors.fill: parent
        z: 1000
        showOverlay: overlayController.show_overlay
        leftSelectedIndex: overlayController.left_selected_index
        rightSelectedIndex: overlayController.right_selected_index
        activeMenu: overlayController.active_menu
        controlOptions: overlayController.control_options
    }

    // Emergency Overlay - highest z-index to appear on top
    EmergencyOverlay {
        id: emergencyOverlay
        anchors.fill: parent
        z: 3000  // Highest z-index to ensure it's on top
    }
}

