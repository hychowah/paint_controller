import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

/**
 * MultiScreenListUI - Test/Demo UI for multi-screen display
 * 
 * This component provides a simple list view showing:
 * - Number of detected screens
 * - Screen information (resolution, position, refresh rate)
 * - Real-time updates when screens are added/removed
 * 
 * This serves as a testing interface for the multi-screen support.
 */
Window {
    id: multiScreenWindow
    title: "Multi-Screen Display - Paint Controller"
    width: 800
    height: 600
    
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
    
    // Background
    Rectangle {
        anchors.fill: parent
        color: "#2E3436"
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 20
            
            // Header
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 80
                color: "#1E2021"
                radius: 8
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 5
                    
                    Text {
                        text: "Multi-Screen Display Manager"
                        font.pixelSize: 28
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    
                    Text {
                        id: screenCountText
                        text: "Detected Screens: " + (screenManager ? screenManager.get_screen_count() : 0)
                        font.pixelSize: 18
                        color: "#B0B0B0"
                    }
                }
            }
            
            // Instructions
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                color: "#3584E4"
                radius: 8
                
                Text {
                    anchors.fill: parent
                    anchors.margins: 15
                    text: "Connect or disconnect external monitors to test real-time detection"
                    font.pixelSize: 16
                    color: "#FFFFFF"
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                }
            }
            
            // Screen List
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#1E2021"
                radius: 8
                
                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 10
                    clip: true
                    
                    ListView {
                        id: screenListView
                        anchors.fill: parent
                        spacing: 10
                        
                        model: screenManager ? screenManager.get_screen_count() : 0
                        
                        delegate: Rectangle {
                            width: screenListView.width
                            height: 150
                            color: "#2E3436"
                            radius: 6
                            border.color: "#555555"
                            border.width: 1
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 15
                                spacing: 8
                                
                                // Screen title
                                Text {
                                    text: "Screen " + index
                                    font.pixelSize: 22
                                    font.bold: true
                                    color: "#3584E4"
                                    Layout.fillWidth: true
                                }
                                
                                // Screen info
                                Text {
                                    id: screenInfoText
                                    text: screenManager ? screenManager.get_screen_info_string(index) : "Loading..."
                                    font.pixelSize: 14
                                    color: "#E0E0E0"
                                    Layout.fillWidth: true
                                    wrapMode: Text.WordWrap
                                }
                                
                                // Status indicator
                                Rectangle {
                                    Layout.preferredWidth: 120
                                    Layout.preferredHeight: 30
                                    color: "#26A269"
                                    radius: 4
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "● Connected"
                                        font.pixelSize: 14
                                        color: "#FFFFFF"
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Footer with controls
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                color: "#1E2021"
                radius: 8
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 15
                    
                    Button {
                        text: "Refresh"
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 40
                        
                        background: Rectangle {
                            color: parent.pressed ? "#2A6FC9" : (parent.hovered ? "#3584E4" : "#1C71D8")
                            radius: 6
                        }
                        
                        contentItem: Text {
                            text: parent.text
                            font.pixelSize: 16
                            color: "#FFFFFF"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        onClicked: {
                            // Force refresh of screen list
                            refreshScreenList()
                        }
                    }
                    
                    Item {
                        Layout.fillWidth: true
                    }
                    
                    Text {
                        text: "Status: Monitoring"
                        font.pixelSize: 14
                        color: "#26A269"
                    }
                    
                    Rectangle {
                        width: 12
                        height: 12
                        radius: 6
                        color: "#26A269"
                        
                        SequentialAnimation on opacity {
                            running: true
                            loops: Animation.Infinite
                            NumberAnimation { from: 1.0; to: 0.3; duration: 800 }
                            NumberAnimation { from: 0.3; to: 1.0; duration: 800 }
                        }
                    }
                }
            }
        }
    }
    
    // Helper function to refresh screen list
    function refreshScreenList() {
        // Update model to trigger ListView refresh
        var count = screenManager.get_screen_count()
        screenListView.model = count
        screenCountText.text = "Detected Screens: " + count
    }
    
    // Connections to screen manager signals
    Connections {
        target: screenManager
        
        function onScreens_changed() {
            console.log("Screens changed detected in QML")
            refreshScreenList()
        }
        
        function onScreen_added(index) {
            console.log("Screen added at index:", index)
            refreshScreenList()
        }
        
        function onScreen_removed(index) {
            console.log("Screen removed at index:", index)
            refreshScreenList()
        }
        
        function onPrimary_screen_changed(screenName) {
            console.log("Primary screen changed to:", screenName)
            refreshScreenList()
        }
    }
    
    Component.onCompleted: {
        console.log("MultiScreenListUI initialized")
        console.log("Initial screen count:", screenManager.get_screen_count())
    }
}
