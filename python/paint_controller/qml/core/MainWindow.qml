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
    
    // Screen management - use ScreenManager for adaptive multi-screen support
    property int targetScreenIndex: 0  // Default to primary screen
    property var allScreens: Qt.application.screens
    property var targetScreen: {
        // Use screenManager if available and target index is valid
        if (typeof screenManager !== 'undefined' && screenManager) {
            var idx = targetScreenIndex
            if (idx >= 0 && idx < allScreens.length) {
                return allScreens[idx]
            }
        }
        // Fallback to primary screen
        return allScreens.length > 0 ? allScreens[0] : null
    }

    property int sidebarWidth: 150 // Initial value (expanded width)
    
    // Expose the video fullscreen overlay as a property
    property alias videoFullscreenOverlay: videoFullscreenOverlay
    
    // Update window position and size when target screen changes or screens are added/removed
    Component.onCompleted: {
        updateWindowGeometry()
        
        // Connect to screenManager signals if available
        if (typeof screenManager !== 'undefined' && screenManager) {
            screenManager.screens_changed.connect(updateWindowGeometry)
            screenManager.screen_added.connect(handleScreenAdded)
            screenManager.screen_removed.connect(handleScreenRemoved)
            
            console.log("MainWindow: Connected to ScreenManager - " + screenManager.screen_count + " screen(s) detected")
            logScreenInfo()
        }
    }
    
    // Function to update window geometry based on target screen
    function updateWindowGeometry() {
        if (targetScreen) {
            mainWindow.x = targetScreen.virtualX
            mainWindow.y = targetScreen.virtualY
            mainWindow.width = targetScreen.width
            mainWindow.height = targetScreen.height
            console.log("Window geometry updated to screen: " + targetScreen.name + 
                       " (" + targetScreen.width + "x" + targetScreen.height + ")")
        }
    }
    
    // Handle screen addition
    function handleScreenAdded(index, name) {
        console.log("Screen added: " + name + " at index " + index)
        allScreens = Qt.application.screens  // Refresh screen list
        logScreenInfo()
    }
    
    // Handle screen removal
    function handleScreenRemoved(index, name) {
        console.log("Screen removed: " + name + " (was at index " + index + ")")
        allScreens = Qt.application.screens  // Refresh screen list
        
        // If we're on the removed screen, switch to primary
        if (targetScreenIndex === index) {
            console.log("Target screen removed, switching to primary screen")
            targetScreenIndex = 0
            updateWindowGeometry()
        } else if (targetScreenIndex > index) {
            // Adjust index if a screen before our target was removed
            targetScreenIndex--
        }
        
        logScreenInfo()
    }
    
    // Log information about all connected screens
    function logScreenInfo() {
        if (typeof screenManager !== 'undefined' && screenManager) {
            var screenCount = screenManager.screen_count
            console.log("=== Screen Information ===")
            console.log("Total screens: " + screenCount)
            console.log("Multiple screens: " + screenManager.has_multiple_screens)
            console.log("Primary screen: " + screenManager.primary_screen_name)
            
            for (var i = 0; i < screenCount; i++) {
                var info = screenManager.get_screen_info(i)
                console.log("Screen " + i + ": " + info.name + 
                           (info.isPrimary ? " (PRIMARY)" : "") +
                           " - " + info.width + "x" + info.height +
                           " @ " + info.refreshRate + "Hz")
            }
            console.log("=========================")
        }
    }
    
    // Function to switch to a specific screen
    function switchToScreen(screenIndex) {
        if (screenIndex >= 0 && screenIndex < allScreens.length) {
            targetScreenIndex = screenIndex
            updateWindowGeometry()
            console.log("Switched to screen " + screenIndex)
        } else {
            console.log("Invalid screen index: " + screenIndex)
        }
    }
    
    x: targetScreen ? targetScreen.virtualX : 0
    y: targetScreen ? targetScreen.virtualY : 0
    width: targetScreen ? targetScreen.width : 800
    height: targetScreen ? targetScreen.height : 600

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

        // Video Fullscreen Overlay - above everything for fullscreen video with DJI-style overlay
    VideoFullscreenOverlay {
        id: videoFullscreenOverlay
        objectName: "videoFullscreenOverlay"
        anchors.fill: parent
        z: 500  // Above everything including emergency overlay
    }

    // LiDAR 3D View
    Lidar3DView {
        id: lidar3DView
        objectName: "lidarOverlay"
    }
}




