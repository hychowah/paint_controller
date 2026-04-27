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
import "../features/systemcontrol"
import "../features/video"
import "../overlays/lidar"

ApplicationWindow {
    id: mainWindow
    visible: true
    visibility: Window.FullScreen
    
    // Shell policy is owned by shellState; QML consumes it and keeps window composition declarative.
    property int screenCount: shellState ? shellState.screen_count : 1
    property int mainScreenIndex: shellState ? shellState.main_surface_screen_index : 0
    property int secondaryScreenIndex: shellState ? shellState.secondary_surface_screen_index : 0
    property bool secondarySurfaceActive: shellState ? shellState.secondary_surface_active : false
    property bool secondarySurfaceFullscreen: shellState ? shellState.secondary_surface_fullscreen : false
    property bool showSystemControlOnMainSurface: overlayHost ? overlayHost.system_control_on_main_surface : (shellState ? shellState.show_system_control_on_main_surface : true)
    property bool showJoystickOverlayOnMainSurface: overlayHost ? overlayHost.joystick_overlay_on_main_surface : true
    property bool showEmergencyOverlayOnMainSurface: overlayHost ? overlayHost.emergency_overlay_on_main_surface : true
    property bool videoFullscreenOnMainSurface: overlayHost ? overlayHost.video_fullscreen_on_main_surface : (shellState ? shellState.video_fullscreen_on_main_surface : true)
    property var systemControlServicesModel: systemControlServices
    property var videoRuntimeModel: videoRuntime
    property var recordingStatusModel: recordingStatus
    property var wheelStatusModel: wheelStatus
    property var winchStatusModel: winchStatus
    property var teensyStatusModel: teensyStatus
    property var shellConnectivityStatusModel: shellConnectivityStatus
    property var launcherAdminModel: launcherAdmin
    
    // Use Qt's Screen type for positioning - access via Screen attached property
    screen: Qt.application.screens[mainScreenIndex] || Qt.application.screens[0]

    property int sidebarWidth: CommonStyle.shellSidebarExpandedWidth
    property string selectedPageKey: "home"
    
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
                    pageRegistry: mainWindow.pageRegistry
                    selectedPageKey: mainWindow.selectedPageKey
                    shellConnectivityStatus: mainWindow.shellConnectivityStatusModel
                    height: parent.height
                    onNavigateRequested: function(pageKey) {
                        mainWindow.navigateToPage(pageKey)
                    }
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
        PageHome {
            shellConnectivityStatus: mainWindow.shellConnectivityStatusModel
        }
    }

    Component {
        id: wheelPageComponent
        PageWheel {}
    }
    
    Component {
        id: winchPageComponent
        PageWinch {
            winchStatus: mainWindow.winchStatusModel
        }
    }
    
    Component {
        id: statusPageComponent
        PageStatus {
            wheelStatus: mainWindow.wheelStatusModel
            winchStatus: mainWindow.winchStatusModel
            teensyStatus: mainWindow.teensyStatusModel
        }
    }

    Component {
        id: tuningPageComponent
        PageTuning {}
    }

    Component {
        id: launcherPageComponent
        PageLauncher {
            shellConnectivityStatus: mainWindow.shellConnectivityStatusModel
            launcherAdmin: mainWindow.launcherAdminModel
        }
    }

    Component {
        id: settingsPageComponent
        PageSettings {}
    }

    readonly property var pageRegistry: [
        { routeOrder: 0, buttonKey: "home", buttonText: "Home", iconSource: "../../resource/homepage.svg", iconScale: 0.7, component: homeComponent },
        { routeOrder: 1, buttonKey: "base", buttonText: "Base", iconSource: "../../resource/base.png", iconScale: 0.7, component: wheelPageComponent },
        { routeOrder: 2, buttonKey: "winch", buttonText: "Winch", iconSource: "../../resource/winch.png", iconScale: 0.6, component: winchPageComponent },
        { routeOrder: 3, buttonKey: "monitor", buttonText: "Monitor", iconSource: "../../resource/monitor.svg", iconScale: 0.6, component: statusPageComponent },
        { routeOrder: 4, buttonKey: "tuning", buttonText: "Tuning", iconSource: "../../resource/icon-pid.png", iconScale: 0.6, component: tuningPageComponent },
        { routeOrder: 5, buttonKey: "launcher", buttonText: "Launcher", iconSource: "../../resource/launcher.svg", iconScale: 0.7, component: launcherPageComponent },
        { routeOrder: 6, buttonKey: "settings", buttonText: "Settings", iconSource: "../../resource/setting.svg", iconScale: 0.6, component: settingsPageComponent }
    ]

    function getPageConfig(pageKey) {
        for (var i = 0; i < pageRegistry.length; i++) {
            if (pageRegistry[i].buttonKey === pageKey) {
                return pageRegistry[i]
            }
        }
        return null
    }

    function getRouteOrder(pageKey) {
        var targetPage = getPageConfig(pageKey)
        if (!targetPage) {
            return -1
        }
        return targetPage.routeOrder
    }

    function navigateToPage(pageKey) {
        var targetPage = getPageConfig(pageKey)
        if (!targetPage || !targetPage.component) {
            console.warn("MainWindow: unknown page key", pageKey)
            return
        }

        selectedPageKey = targetPage.buttonKey

        var targetOrder = targetPage.routeOrder

        if (targetOrder === stackView.currentIndex) {
            return
        }

        stackView.targetIndex = targetOrder
        stackView.replace(stackView.currentItem, targetPage.component)
        stackView.currentIndex = targetOrder
    }

    SystemControlWorkspace {
        anchors.fill: parent
        id: systemControlMenu
        objectName: "systemControlMenuMain"
        z: overlayHost ? overlayHost.system_control_layer : 1001
        showOverlay: overlayController.show_overlay
        activeMenu: overlayController.active_menu
        systemControlServices: mainWindow.systemControlServicesModel
        recordingStatus: mainWindow.recordingStatusModel
        wheelStatus: mainWindow.wheelStatusModel
        winchStatus: mainWindow.winchStatusModel
        teensyStatus: mainWindow.teensyStatusModel
        visible: showSystemControlOnMainSurface
    }

    CustomPopup {
        id: messagePopup
    }

    JoystickOverlay {
        anchors.fill: parent
        id: joystickOverlayMain
        objectName: "joystickOverlayMain"
        z: overlayHost ? overlayHost.joystick_overlay_layer : 1000
        showOverlay: overlayController.show_overlay
        leftSelectedIndex: overlayController.left_selected_index
        rightSelectedIndex: overlayController.right_selected_index
        activeMenu: overlayController.active_menu
        controlOptions: overlayController.control_options
        visible: showJoystickOverlayOnMainSurface
    }

    // Emergency Overlay - highest z-index to appear on top
    EmergencyOverlay {
        id: emergencyOverlay
        objectName: "emergencyOverlayMain"
        anchors.fill: parent
        z: overlayHost ? overlayHost.emergency_overlay_layer : 3000
        visible: showEmergencyOverlayOnMainSurface
    }

    // Video Fullscreen Overlay - for fullscreen video with DJI-style overlay
    VideoFullscreenWorkspace {
        id: videoFullscreenOverlay
        objectName: "videoFullscreenOverlayMain"
        anchors.fill: parent
        z: overlayHost ? overlayHost.video_fullscreen_layer : 500
        active: overlayHost ? (overlayHost.video_fullscreen_active && overlayHost.video_fullscreen_on_main_surface) : false
        videoSource: overlayHost ? overlayHost.video_fullscreen_source : ""
        workflowServices: mainWindow.systemControlServicesModel
        videoRuntime: mainWindow.videoRuntimeModel
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
            if (secondarySurfaceActive && appScreens.length > secondaryScreenIndex) {
                ensureSecondaryScreenWindow(appScreens)
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
            closeSecondaryScreenWindow()
            console.log("Multi-screen test window closed")
        }
    }

    function closeSecondaryScreenWindow() {
        if (multiScreenWindow !== null) {
            multiScreenWindow.hideWindow()
            multiScreenWindow.destroy()
            multiScreenWindow = null
        }
    }

    function ensureSecondaryScreenWindow(appScreens) {
        if (!secondarySurfaceActive || appScreens.length <= secondaryScreenIndex) {
            closeSecondaryScreenWindow()
            return
        }

        if (multiScreenWindow === null) {
            multiScreenWindow = multiScreenComponent.createObject(mainWindow)
            if (!multiScreenWindow) {
                return
            }
        }

        var secondaryScreen = appScreens[secondaryScreenIndex]
        multiScreenWindow.screen = secondaryScreen
        multiScreenWindow.x = secondaryScreen.virtualX
        multiScreenWindow.y = secondaryScreen.virtualY
        multiScreenWindow.width = secondaryScreen.width
        multiScreenWindow.height = secondaryScreen.height
        multiScreenWindow.targetScreenIndex = secondaryScreenIndex
        multiScreenWindow.fullscreenMode = secondarySurfaceFullscreen
        multiScreenWindow.showWindow()
    }

    function applyShellSurfacePolicy() {
        var appScreens = Qt.application.screens
        console.log("Applying shell surface policy, Qt screens: " + appScreens.length)

        var mainSurfaceScreen = appScreens[mainScreenIndex] || appScreens[0]
        if (mainSurfaceScreen) {
            mainWindow.screen = mainSurfaceScreen
            mainWindow.x = mainSurfaceScreen.virtualX
            mainWindow.y = mainSurfaceScreen.virtualY
            mainWindow.width = mainSurfaceScreen.width
            mainWindow.height = mainSurfaceScreen.height
        }

        if (secondarySurfaceActive && appScreens.length > secondaryScreenIndex) {
            ensureSecondaryScreenWindow(appScreens)
        } else {
            closeSecondaryScreenWindow()
        }
    }
    
    // Monitor screen changes and update
    Connections {
        target: screenManager
        
        function onScreens_changed() {
            console.log("MainWindow: Screen configuration changed, shell policy count: " + screenCount)
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
            if (!videoFullscreenOnMainSurface) {
                return
            }

            if (overlayHost) {
                overlayHost.toggle_video_fullscreen(videoSource)
                return
            }

            if (videoFullscreenOverlay.active) {
                videoFullscreenOverlay.active = false
            } else {
                videoFullscreenOverlay.videoSource = videoSource
                videoFullscreenOverlay.active = true
            }
        }

        function onUpdateVideoSourceRequested(videoSource) {
            if (overlayHost) {
                overlayHost.set_video_fullscreen_source(videoSource)
                return
            }

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
            applyShellSurfacePolicy()
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
        
        applyShellSurfacePolicy()
    }
}

