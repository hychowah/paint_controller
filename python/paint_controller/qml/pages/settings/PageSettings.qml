import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "pages"

Rectangle {
    id: settingsMenu
    required property var settingsManager
    required property var qtBridge
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#F5F5F5"
    
    property string currentPage: "main"
    
    StackLayout {
        anchors.fill: parent
        currentIndex: {
            switch(settingsMenu.currentPage) {
                case "main": return 0
                case "winch": return 1
                case "wheels": return 2
                case "camera": return 3
                case "arm": return 4
                default: return 0
            }
        }
        
        MainSettingsPage {
            settingsManager: settingsMenu.settingsManager
            qtBridge: settingsMenu.qtBridge
            id: mainPage
            onPageRequested: function(page) {
                settingsMenu.currentPage = page
            }
        }
        
        WinchSettingsPage {
            settingsManager: settingsMenu.settingsManager
            qtBridge: settingsMenu.qtBridge
            id: winchPage
            onBackRequested: settingsMenu.currentPage = "main"
        }
        
        WheelsSettingsPage {
            settingsManager: settingsMenu.settingsManager
            qtBridge: settingsMenu.qtBridge
            id: wheelsPage
            onBackRequested: settingsMenu.currentPage = "main"
        }
        
        CameraSettingsPage {
            settingsManager: settingsMenu.settingsManager
            qtBridge: settingsMenu.qtBridge
            id: cameraPage
            onBackRequested: settingsMenu.currentPage = "main"
        }
        
        ArmSettingsPage {
            settingsManager: settingsMenu.settingsManager
            qtBridge: settingsMenu.qtBridge
            id: armPage
            onBackRequested: settingsMenu.currentPage = "main"
        }
    }
}