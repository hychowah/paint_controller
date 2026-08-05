import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "../pages/status"
import "../overlays"

/**
 * MultiScreenListUI - Industrial Monitor Display for Secondary Screen
 * 
 * This window shows on the built-in Steam Deck display (1280x800) when an external
 * monitor is connected. It provides a dedicated industrial-style monitoring interface
 * for real-time system telemetry and control status.
 * 
 * Note: Optimized for 7-inch display (Steam Deck built-in screen)
 */
Window {
    id: multiScreenWindow
    title: "Industrial Monitor - Paint Controller"
    width: 1280
    height: 720
    property var systemControlServicesModel: systemControlServices
    property var recordingStatusModel: recordingStatus
    property var wheelStatusModel: wheelStatus
    property var winchStatusModel: winchStatus
    property var teensyStatusModel: teensyStatus
    property var valveStatusModel: valveStatus
    property var lidarStatusModel: lidarStatus
    property var videoRuntimeModel: videoRuntime
    property var wheelActionsModel: wheelActions
    property var winchActionsModel: winchActions
    property var teensyActionsModel: teensyActions
    property var recordingActionsModel: recordingActions
    property var systemActionsModel: systemActions
    property var actionLegalityModel: actionLegality
    property var settingsManagerModel: settingsManager
    property var baseTopViewStatusModel: baseTopViewStatus
    property var baseTopViewActionsModel: baseTopViewActions
    property var overlayControllerModel: overlayController
    property var qtBridgeModel: qtBridge
    
    // Properties to control which screen this window appears on
    property int targetScreenIndex: 0
    
    // Property to enable fullscreen mode - use visibility instead of visible
    property bool fullscreenMode: false
    visibility: fullscreenMode ? Window.FullScreen : Window.Hidden
    
    // Prevent keyboard events from leaking to this window
    flags: Qt.Window
    
    // Function to show the window (avoids visible/visibility conflict)
    function showWindow() {
        visibility = fullscreenMode ? Window.FullScreen : Window.Windowed
    }
    
    // Function to hide the window
    function hideWindow() {
        visibility = Window.Hidden
    }
    
    // Industrial Monitor Content
    PageMonitor {
        anchors.fill: parent
        wheelStatus: multiScreenWindow.wheelStatusModel
        winchStatus: multiScreenWindow.winchStatusModel
        teensyStatus: multiScreenWindow.teensyStatusModel
        valveStatus: multiScreenWindow.valveStatusModel
        lidarStatus: multiScreenWindow.lidarStatusModel
    }
    
    // Shared dual-surface overlay composition (TD-053). Host computes secondary flags.
    ShellOverlayStack {
        id: shellOverlayStack
        anchors.fill: parent
        systemControlVisible: overlayHost
            ? overlayHost.system_control_on_secondary_surface
            : (shellState ? shellState.show_system_control_on_secondary_surface : true)
        joystickVisible: overlayHost ? overlayHost.joystick_overlay_on_secondary_surface : false
        emergencyVisible: overlayHost ? overlayHost.emergency_overlay_on_secondary_surface : false
        videoFullscreenActive: overlayHost
            ? (overlayHost.video_fullscreen_active && overlayHost.video_fullscreen_on_secondary_surface)
            : false
        systemControlObjectName: "systemControlMenuSecondary"
        joystickObjectName: "joystickOverlaySecondary"
        videoFullscreenObjectName: "videoFullscreenOverlaySecondary"
        emergencyObjectName: "emergencyOverlaySecondary"
        systemControlLayer: overlayHost ? overlayHost.system_control_layer : 1001
        joystickLayer: overlayHost ? overlayHost.joystick_overlay_layer : 1000
        videoFullscreenLayer: overlayHost ? overlayHost.video_fullscreen_layer : 500
        emergencyLayer: overlayHost ? overlayHost.emergency_overlay_layer : 3000
        overlayController: multiScreenWindow.overlayControllerModel
        systemControlServices: multiScreenWindow.systemControlServicesModel
        recordingStatus: multiScreenWindow.recordingStatusModel
        wheelStatus: multiScreenWindow.wheelStatusModel
        winchStatus: multiScreenWindow.winchStatusModel
        teensyStatus: multiScreenWindow.teensyStatusModel
        valveStatus: multiScreenWindow.valveStatusModel
        lidarStatus: multiScreenWindow.lidarStatusModel
        videoRuntime: multiScreenWindow.videoRuntimeModel
        wheelActions: multiScreenWindow.wheelActionsModel
        winchActions: multiScreenWindow.winchActionsModel
        teensyActions: multiScreenWindow.teensyActionsModel
        recordingActions: multiScreenWindow.recordingActionsModel
        systemActions: multiScreenWindow.systemActionsModel
        actionLegality: multiScreenWindow.actionLegalityModel
        settingsManager: multiScreenWindow.settingsManagerModel
        baseTopViewStatus: multiScreenWindow.baseTopViewStatusModel
        baseTopViewActions: multiScreenWindow.baseTopViewActionsModel
        qtBridge: multiScreenWindow.qtBridgeModel
        videoSource: overlayHost ? overlayHost.video_fullscreen_source : ""
    }
    
    Component.onCompleted: {
        console.log("Industrial Monitor initialized on secondary screen")
        console.log("Target screen index:", targetScreenIndex)
    }
}
