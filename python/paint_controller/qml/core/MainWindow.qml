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
import "../theme"

ApplicationWindow {
    id: mainWindow
    visibility: Window.FullScreen

    // Shell policy is owned by shellState; QML consumes it and keeps window composition declarative.
    property int screenCount: shellState ? shellState.screen_count : 1
    property int mainScreenIndex: shellState ? shellState.main_surface_screen_index : 0
    property bool showSystemControlOnMainSurface: overlayHost ? overlayHost.system_control_on_main_surface : (shellState ? shellState.show_system_control_on_main_surface : true)
    property bool showJoystickOverlayOnMainSurface: overlayHost ? overlayHost.joystick_overlay_on_main_surface : true
    property bool showEmergencyOverlayOnMainSurface: overlayHost ? overlayHost.emergency_overlay_on_main_surface : true
    property bool videoFullscreenOnMainSurface: overlayHost ? overlayHost.video_fullscreen_on_main_surface : (shellState ? shellState.video_fullscreen_on_main_surface : true)
    property var systemControlServicesModel: systemControlServices
    property var shellRouterModel: shellRouter
    property var shellStateModel: shellState
    property var videoRuntimeModel: videoRuntime
    property var recordingStatusModel: recordingStatus
    property var wheelStatusModel: wheelStatus
    property var wheelActionsModel: wheelActions
    property var winchStatusModel: winchStatus
    property var winchActionsModel: winchActions
    property var teensyStatusModel: teensyStatus
    property var teensyActionsModel: teensyActions
    property var recordingActionsModel: recordingActions
    property var systemActionsModel: systemActions
    property var actionLegalityModel: actionLegality
    property var tuningActionsModel: tuningActions
    property var settingsManagerModel: settingsManager
    property var baseTopViewStatusModel: baseTopViewStatus
    property var baseTopViewActionsModel: baseTopViewActions
    property var overlayControllerModel: overlayController
    property var qtBridgeModel: qtBridge
    property var warningHandlerModel: warningHandler
    property var valveStatusModel: valveStatus
    property var lidarStatusModel: lidarStatus
    property var shellConnectivityStatusModel: shellConnectivityStatus
    property var launcherAdminModel: launcherAdmin

    // Use Qt's Screen type for positioning - access via Screen attached property
    screen: Qt.application.screens[mainScreenIndex] || Qt.application.screens[0]

    property int sidebarWidth: CommonStyle.shellSidebarExpandedWidth

    // Expose the video fullscreen overlay as a property
    property alias videoFullscreenOverlay: videoFullscreenOverlay

    // Minimal QML-side mapping from route key to page component. The route
    // registry (order, titles, icons) lives in Python-owned shellRouter.
    readonly property var routeComponentMap: ({
        "home": homeComponent,
        "base": wheelPageComponent,
        "winch": winchPageComponent,
        "monitor": statusPageComponent,
        "tuning": tuningPageComponent,
        "launcher": launcherPageComponent,
        "settings": settingsPageComponent
    })
    
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
    property bool showOverlay: overlayControllerModel ? overlayControllerModel.show_overlay : false
    property int leftSelectedIndex: overlayControllerModel ? overlayControllerModel.left_selected_index : 0
    property int rightSelectedIndex: overlayControllerModel ? overlayControllerModel.right_selected_index : 0
    property string activeMenu: overlayControllerModel ? overlayControllerModel.active_menu : ""
    property var controlOptions: overlayControllerModel ? overlayControllerModel.control_options : []
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
                    shellRouter: mainWindow.shellRouterModel
                    shellConnectivityStatus: mainWindow.shellConnectivityStatusModel
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
                                qtBridge: mainWindow.qtBridgeModel
                                warningHandler: mainWindow.warningHandlerModel
                            }
                            
                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                
                                StackView {
                                    id: stackView
                                    objectName: "stackView"
                                    anchors.fill: parent
                                    initialItem: homeComponent

                                    property int currentIndex: shellRouter ? shellRouter.currentRouteOrder : 0
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

                                    Connections {
                                        target: shellRouter

                                        function onCurrentRouteChanged(route) {
                                            var component = mainWindow.routeComponentMap[route]
                                            if (!component) {
                                                console.warn("MainWindow: unknown route", route)
                                                return
                                            }

                                            var targetOrder = shellRouter.routeOrder(route)
                                            if (targetOrder === stackView.currentIndex) {
                                                return
                                            }

                                            stackView.targetIndex = targetOrder
                                            stackView.replace(stackView.currentItem, component)
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
            videoRuntime: mainWindow.videoRuntimeModel
        }
    }

    Component {
        id: wheelPageComponent
        PageWheel {
            wheelStatus: mainWindow.wheelStatusModel
            wheelActions: mainWindow.wheelActionsModel
            videoRuntime: mainWindow.videoRuntimeModel
        }
    }
    
    Component {
        id: winchPageComponent
        PageWinch {
            winchStatus: mainWindow.winchStatusModel
            winchActions: mainWindow.winchActionsModel
        }
    }
    
    Component {
        id: statusPageComponent
        PageStatus {
            wheelStatus: mainWindow.wheelStatusModel
            winchStatus: mainWindow.winchStatusModel
            teensyStatus: mainWindow.teensyStatusModel
            winchActions: mainWindow.winchActionsModel
            teensyActions: mainWindow.teensyActionsModel
        }
    }

    Component {
        id: tuningPageComponent
        PageTuning {
            teensyStatus: mainWindow.teensyStatusModel
            tuningActions: mainWindow.tuningActionsModel
            qtBridge: mainWindow.qtBridgeModel
        }
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
        PageSettings {
            settingsManager: mainWindow.settingsManagerModel
            qtBridge: mainWindow.qtBridgeModel
        }
    }

    SystemControlWorkspace {
        anchors.fill: parent
        id: systemControlMenu
        objectName: "systemControlMenuMain"
        z: overlayHost ? overlayHost.system_control_layer : 1001
        showOverlay: mainWindow.overlayControllerModel.show_overlay
        activeMenu: mainWindow.overlayControllerModel.active_menu
        systemControlServices: mainWindow.systemControlServicesModel
        recordingStatus: mainWindow.recordingStatusModel
        wheelStatus: mainWindow.wheelStatusModel
        winchStatus: mainWindow.winchStatusModel
        teensyStatus: mainWindow.teensyStatusModel
        wheelActions: mainWindow.wheelActionsModel
        winchActions: mainWindow.winchActionsModel
        teensyActions: mainWindow.teensyActionsModel
        recordingActions: mainWindow.recordingActionsModel
        systemActions: mainWindow.systemActionsModel
        actionLegality: mainWindow.actionLegalityModel
        settingsManager: mainWindow.settingsManagerModel
        overlayController: mainWindow.overlayControllerModel
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
        showOverlay: mainWindow.overlayControllerModel.show_overlay
        leftSelectedIndex: mainWindow.overlayControllerModel.left_selected_index
        rightSelectedIndex: mainWindow.overlayControllerModel.right_selected_index
        activeMenu: mainWindow.overlayControllerModel.active_menu
        controlOptions: mainWindow.overlayControllerModel.control_options
        overlayController: mainWindow.overlayControllerModel
        visible: showJoystickOverlayOnMainSurface
    }

    // Emergency Overlay - highest z-index to appear on top
    EmergencyOverlay {
        id: emergencyOverlay
        objectName: "emergencyOverlayMain"
        anchors.fill: parent
        z: overlayHost ? overlayHost.emergency_overlay_layer : 3000
        qtBridge: mainWindow.qtBridgeModel
        visible: showEmergencyOverlayOnMainSurface
    }

    // Video Fullscreen Overlay - for fullscreen video with DJI-style overlay
    VideoFullscreenWorkspace {
        id: videoFullscreenOverlay
        objectName: "videoFullscreenOverlayMain"
        anchors.fill: parent
        z: overlayHost ? overlayHost.video_fullscreen_layer : 500
        active: overlayHost ? (overlayHost.video_fullscreen_active && overlayHost.video_fullscreen_on_main_surface && shellRouter && shellRouter.currentRoute === "home") : false
        videoSource: overlayHost ? overlayHost.video_fullscreen_source : ""
        workflowServices: mainWindow.systemControlServicesModel
        videoRuntime: mainWindow.videoRuntimeModel
        wheelStatus: mainWindow.wheelStatusModel
        winchStatus: mainWindow.winchStatusModel
        teensyStatus: mainWindow.teensyStatusModel
        valveStatus: mainWindow.valveStatusModel
        lidarStatus: mainWindow.lidarStatusModel
        overlayController: mainWindow.overlayControllerModel
        baseTopViewStatus: mainWindow.baseTopViewStatusModel
        baseTopViewActions: mainWindow.baseTopViewActionsModel
        actionLegality: mainWindow.actionLegalityModel
    }

    // LiDAR 3D View
    Lidar3DView {
        id: lidar3DView
        objectName: "lidarOverlay"
    }

    // Secondary screen lifecycle is owned by MultiScreenHost
    MultiScreenHost {
        id: multiScreenHost
        shellState: mainWindow.shellStateModel
        mainWindow: mainWindow
    }

    // Bridge signals from Python backend to QML UI elements
    Connections {
        target: mainWindow.qtBridgeModel

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
        console.log("ShellState screen count: " + (shellState ? shellState.screen_count : "N/A"))

        multiScreenHost.applyShellSurfacePolicy()
    }
}

