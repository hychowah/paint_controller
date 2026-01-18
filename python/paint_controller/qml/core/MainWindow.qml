import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "../pages/home"
import "../pages/spray"
import "../pages/workflow"
import "../pages/wheel"
import "../pages/winch"
import "../pages/tuning"
import "../pages/settings"
import "../pages/status"
import "../pages/misc"
import "../navigation"
import "../components/buttons"
import "../components/inputs"
import "../components/displays"
import "../components/panels"
import "../components/popups"
import "../components/specialized/pointcloud"
import "../overlays"
import "../overlays/systemcontrol"
import "../overlays/video"
import "../overlays/lidar"

ApplicationWindow {
    id: mainWindow
    visible: true
    visibility: Window.FullScreen
    
    // Multi-screen support
    property var screens: Qt.application.screens
    property int primaryScreenIndex: 0
    property var targetScreen: screens.length > primaryScreenIndex ? screens[primaryScreenIndex] : screens[0]

    property int sidebarWidth: 150 // Initial value (expanded width)
    
    // Expose the video fullscreen overlay as a property
    property alias videoFullscreenOverlay: videoFullscreenOverlay
    
    // Multi-screen test window
    property var multiScreenWindow: null
    
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
                                    initialItem: homeComponent
                                    
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
        id: homeComponent
        PageHome {}
    }

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
        id: page5Component
        PageLauncher {}
    }

    Component {
        id: page7Component
        PageWorkFlow {}
    }

    Component {
        id: settingPageComponent
        PageSettings {}
    }

    SystemControlMenu {
        anchors.fill: parent
        id: systemControlMenu
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

    // Video Fullscreen Overlay - for fullscreen video with DJI-style overlay
    VideoFullscreenOverlay {
        id: videoFullscreenOverlay
        objectName: "videoFullscreenOverlay"
        anchors.fill: parent
        z: 500  // Below emergency overlay but above main content
    }

    // LiDAR 3D View
    Lidar3DView {
        id: lidar3DView
        objectName: "lidarOverlay"
    }
    
    // Multi-screen test window component
    Component {
        id: multiScreenComponent
        MultiScreenListUI {
            id: multiScreenTestWindow
        }
    }
    
    // Function to open/close multi-screen test window
    function toggleMultiScreenWindow() {
        if (multiScreenWindow === null) {
            // Create and show the window
            multiScreenWindow = multiScreenComponent.createObject(mainWindow)
            if (multiScreenWindow) {
                // Position on second screen if available
                if (screens.length > 1) {
                    multiScreenWindow.x = screens[1].virtualX
                    multiScreenWindow.y = screens[1].virtualY
                    multiScreenWindow.width = screens[1].width
                    multiScreenWindow.height = screens[1].height
                    multiScreenWindow.targetScreenIndex = 1
                }
                multiScreenWindow.visible = true
                console.log("Multi-screen test window opened")
            }
        } else {
            // Close and destroy the window
            multiScreenWindow.visible = false
            multiScreenWindow.destroy()
            multiScreenWindow = null
            console.log("Multi-screen test window closed")
        }
    }
    
    // Monitor screen changes and update
    Connections {
        target: screenManager
        
        function onScreens_changed() {
            console.log("MainWindow: Screen configuration changed")
            screens = Qt.application.screens
            
            // Update target screen if needed
            if (screens.length > primaryScreenIndex) {
                targetScreen = screens[primaryScreenIndex]
            } else {
                targetScreen = screens[0]
            }
            
            // Reposition multi-screen window if it exists and there's a second screen
            if (multiScreenWindow !== null && screens.length > 1) {
                multiScreenWindow.x = screens[1].virtualX
                multiScreenWindow.y = screens[1].virtualY
                multiScreenWindow.width = screens[1].width
                multiScreenWindow.height = screens[1].height
            }
        }
    }
}




