import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "../pages/status"

/**
 * MultiScreenListUI - Industrial Monitor Display for Secondary Screen
 * 
 * This window shows on the built-in Steam Deck display (1280x800) when an external
 * monitor is connected. It provides a dedicated industrial-style monitoring interface
 * for real-time system telemetry and control status.
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
    
    // Function to show the window (avoids visible/visibility conflict)
    function showWindow() {
        visibility = fullscreenMode ? Window.FullScreen : Window.Windowed
    }
    
    // Function to hide the window
    function hideWindow() {
        visibility = Window.Hidden
    }
    
    // Industrial Monitor Content
    PageIndustrialMonitor {
        anchors.fill: parent
    }
    
    Component.onCompleted: {
        console.log("Industrial Monitor initialized on secondary screen")
        console.log("Target screen index:", targetScreenIndex)
    }
}
