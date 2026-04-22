import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtCharts
import Qt5Compat.GraphicalEffects
import "../pages/home"
import "../pages/wheel"
import "../pages/winch"
import "../pages/tuning"
import "../pages/settings"
import "../pages/status"
import "../navigation"
import "../components/displays"
import "../components/popups"
import "../overlays"
import "../overlays/systemcontrol"
import "../overlays/video"
import "../overlays/lidar"

ApplicationWindow {
    id: mainWindow
    visible: true
    visibility: Window.FullScreen
    
    // Multi-screen support - use screenManager from Python for reliable detection
    property int screenCount: screenManager ? screenManager.get_screen_count() : 1
    
    // Main UI goes on second monitor (index 1) when available, otherwise primary (index 0)
    property int mainScreenIndex: Qt.application.screens.length > 1 ? 1 : 0
    
    // Use Qt's Screen type for positioning - access via Screen attached property
    screen: Qt.application.screens[mainScreenIndex] || Qt.application.screens[0]

    property int sidebarWidth: CommonStyle.shellSidebarExpandedWidth
    
    // Expose the video fullscreen overlay as a property
    property alias videoFullscreenOverlay: videoFullscreenOverlay
    
    // Multi-screen test window
    property var multiScreenWindow: null
    
    // Position and size are now derived from the assigned screen
    x: screen ? screen.virtualX : 0
    y: screen ? screen.virtualY : 0
    width: screen ? screen.width : 1280
    height: screen ? screen.height : 800
    color: CommonStyle.windowBackground

    // Warm up heavy QML modules during startup so the first page navigation stays responsive.
    Loader {
        id: chartModuleWarmup
        active: true
        visible: false
        sourceComponent: Component {
            Item {
                width: 1
                height: 1
                opacity: 0.0

                ChartView {
                    anchors.fill: parent
                    antialiasing: false
                    legend.visible: false
                }
            }
        }
    }

    Loader {
        id: graphicalEffectsWarmup
        active: true
        visible: false
        sourceComponent: Component {
            Item {
                width: 1
                height: 1
                opacity: 0.0

                Rectangle {
                    anchors.fill: parent
                    color: "white"
                    layer.enabled: true
                    layer.effect: DropShadow {
                        horizontalOffset: 0
                        verticalOffset: 0
                        radius: 1
                        samples: 3
                        color: "#00000000"
                    }
                }
            }
        }
    }

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
        color: CommonStyle.windowBackground
        
        RowLayout {
            anchors.fill: parent
            spacing: CommonStyle.spacingSm
            
            Item {
                id: contentContainer
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                SelectBar {
                    id: selectBar
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
                        color: CommonStyle.windowBackground
                        
                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0
                            
                            TopBar {
                                Layout.fillWidth: true
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
        id: wheelPageComponent
        PageWheel {}
    }
    
    Component {
        id: winchPageComponent
        PageWinch {}
    }
    
    Component {
        id: statusPageComponent
        PageStatus {}
    }

    Component {
        id: tuningPageComponent
        PageTuning {}
    }

    Component {
        id: launcherPageComponent
        PageLauncher {}
    }

    Component {
        id: settingsPageComponent
        PageSettings {}
    }

    SystemControlMenu {
        anchors.fill: parent
        id: systemControlMenu
        z: 1001
        showOverlay: overlayController.show_overlay
        activeMenu: overlayController.active_menu
        // Hide the system control menu on main window when in dual-monitor mode
        // It will appear on the secondary screen (touchscreen) instead
        visible: screenCount <= 1
    }

    CustomPopup {
        id: messagePopup
    }

    JoystickOverlay {
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
    
    // Function to open/close multi-screen test window (manual toggle)
    function toggleMultiScreenWindow() {
        var appScreens = Qt.application.screens
        console.log("toggleMultiScreenWindow: Found " + appScreens.length + " screens")
        
        if (multiScreenWindow === null) {
            // Use the fullscreen function if we have 2 screens
            if (appScreens.length > 1) {
                openSecondaryScreenFullscreen()
            } else {
                // Create windowed on primary if only one screen
                multiScreenWindow = multiScreenComponent.createObject(mainWindow)
                if (multiScreenWindow) {
                    multiScreenWindow.showWindow()
                    console.log("Multi-screen test window opened (windowed on primary)")
                }
            }
        } else {
            // Close and destroy the window
            multiScreenWindow.hideWindow()
            multiScreenWindow.destroy()
            multiScreenWindow = null
            console.log("Multi-screen test window closed")
        }
    }
    
    // Monitor screen changes and update
    Connections {
        target: screenManager
        
        function onScreens_changed() {
            // Use screenManager count - it's more reliable than Qt.application.screens
            // which may not have updated yet when this signal fires
            var newScreenCount = screenManager.get_screen_count()
            console.log("MainWindow: Screen configuration changed, count: " + newScreenCount)
            
            // Update screen count property
            screenCount = newScreenCount
            
            // Use a small delay to let Qt.application.screens update
            screenUpdateTimer.restart()
        }
    }

    // Bridge signals from Python backend to QML UI elements
    Connections {
        target: backend

        function onShowPopupRequested(title, message, popupType, delay) {
            messagePopup.messageTitle = title
            messagePopup.messageText = message
            messagePopup.messageType = popupType
            messagePopup.dismissDelay = delay
            messagePopup.open()
        }

        function onClosePopupRequested() {
            messagePopup.close()
        }

        function onToggleSidebarRequested() {
            selectBar.toggleSidebar()
        }

        function onToggleVideoOverlayRequested(active, videoSource) {
            if (videoFullscreenOverlay.active) {
                videoFullscreenOverlay.active = false
            } else {
                videoFullscreenOverlay.videoSource = videoSource
                videoFullscreenOverlay.active = true
            }
        }

        function onUpdateVideoSourceRequested(videoSource) {
            if (videoFullscreenOverlay.active) {
                videoFullscreenOverlay.videoSource = videoSource
            }
        }
    }
    
    // Timer to handle screen updates after Qt.application.screens has updated
    Timer {
        id: screenUpdateTimer
        interval: 100  // 100ms delay for Qt to update screen list
        repeat: false
        onTriggered: {
            var appScreens = Qt.application.screens
            var count = appScreens.length
            console.log("Screen update timer triggered, Qt screens: " + count)
            
            if (count > 1) {
                // Two monitors: Main UI on external (index 1), secondary on built-in (index 0)
                console.log("Two screens - repositioning: Main UI -> external, Secondary -> built-in")
                
                // Move main window to external monitor
                mainScreenIndex = 1
                mainWindow.screen = appScreens[1]
                mainWindow.x = appScreens[1].virtualX
                mainWindow.y = appScreens[1].virtualY
                
                // Open/reposition secondary window on built-in screen
                if (multiScreenWindow === null) {
                    openSecondaryScreenFullscreen()
                } else {
                    var builtInScreen = appScreens[0]
                    multiScreenWindow.screen = builtInScreen
                    multiScreenWindow.x = builtInScreen.virtualX
                    multiScreenWindow.y = builtInScreen.virtualY
                    multiScreenWindow.width = builtInScreen.width
                    multiScreenWindow.height = builtInScreen.height
                }
            } else {
                // Only one monitor: Main UI on primary, close secondary window
                console.log("Single screen - Main UI on built-in only")
                mainScreenIndex = 0
                mainWindow.screen = appScreens[0]
                mainWindow.x = appScreens[0].virtualX
                mainWindow.y = appScreens[0].virtualY
                
                if (multiScreenWindow !== null) {
                    console.log("Closing secondary display")
                    multiScreenWindow.hideWindow()
                    multiScreenWindow.destroy()
                    multiScreenWindow = null
                }
            }
        }
    }
    
    // Debug: Log screen info on startup
    Component.onCompleted: {
        var appScreens = Qt.application.screens
        console.log("MainWindow initialized")
        console.log("Number of screens detected: " + appScreens.length)
        for (var i = 0; i < appScreens.length; i++) {
            var s = appScreens[i]
            console.log("  Screen " + i + ": " + s.name + 
                       " - " + s.width + "x" + s.height +
                       " @ (" + s.virtualX + ", " + s.virtualY + ")")
        }
        console.log("ScreenManager count: " + (screenManager ? screenManager.get_screen_count() : "N/A"))
        
        // When two monitors detected:
        // - Main UI shows on second monitor (external display, index 1)
        // - Secondary window shows on first monitor (built-in Steam Deck, index 0)
        if (appScreens.length > 1) {
            console.log("Two screens detected:")
            console.log("  Main UI -> Screen 1 (" + appScreens[1].name + ")")
            console.log("  Secondary window -> Screen 0 (" + appScreens[0].name + ")")
            
            // Move main window to second screen
            mainScreenIndex = 1
            mainWindow.screen = appScreens[1]
            mainWindow.x = appScreens[1].virtualX
            mainWindow.y = appScreens[1].virtualY
            
            // Open secondary window on first screen (built-in)
            openSecondaryScreenFullscreen()
        }
    }
    
    // Function to open secondary screen window on the built-in display (screen 0)
    function openSecondaryScreenFullscreen() {
        var appScreens = Qt.application.screens
        if (appScreens.length < 2) {
            console.log("Cannot open secondary screen - only one monitor detected")
            return
        }
        
        if (multiScreenWindow === null) {
            multiScreenWindow = multiScreenComponent.createObject(mainWindow)
            if (multiScreenWindow) {
                // Secondary window goes on first screen (built-in Steam Deck display)
                var builtInScreen = appScreens[0]
                console.log("Opening fullscreen on built-in screen: " + builtInScreen.name)
                multiScreenWindow.screen = builtInScreen
                multiScreenWindow.x = builtInScreen.virtualX
                multiScreenWindow.y = builtInScreen.virtualY
                multiScreenWindow.width = builtInScreen.width
                multiScreenWindow.height = builtInScreen.height
                multiScreenWindow.targetScreenIndex = 0
                multiScreenWindow.fullscreenMode = true
                multiScreenWindow.showWindow()  // Use showWindow() to avoid visible/visibility conflict
                console.log("Secondary screen window opened in fullscreen on built-in display")
            }
        }
    }
}

