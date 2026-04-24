import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "../pages/status"
import "../features/systemcontrol"

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
    }
    
    // SystemControlMenu appears on this screen when in dual-monitor mode
    SystemControlWorkspace {
        anchors.fill: parent
        id: systemControlMenuSecondary
        z: 1001
        showOverlay: overlayController.show_overlay
        activeMenu: overlayController.active_menu
    }
    
    Component.onCompleted: {
        console.log("Industrial Monitor initialized on secondary screen")
        console.log("Target screen index:", targetScreenIndex)
    }
}
