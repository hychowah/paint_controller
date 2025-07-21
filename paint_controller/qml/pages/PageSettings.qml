import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "settings"

Rectangle {
    id: settingsMenu
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#F5F5F5"
    
    property string currentPage: "main"
    property real winchMaxSpeed: 50.0
    property bool winchTorqueLimitEnabled: true
    property real winchTorqueLimit: 75.0
    property var pidValues: [1.0, 0.5, 0.1, 0.0]
    property var coordinateValues: [10.5, 25.3, -5.2, 45.0, 90.0]
    
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
            id: mainPage
            winchMaxSpeed: settingsMenu.winchMaxSpeed
            
            onPageRequested: function(page) {
                settingsMenu.currentPage = page
            }
        }
        
        WinchSettingsPage {
            id: winchPage
            winchMaxSpeed: settingsMenu.winchMaxSpeed
            winchTorqueLimitEnabled: settingsMenu.winchTorqueLimitEnabled
            winchTorqueLimit: settingsMenu.winchTorqueLimit
            pidValues: settingsMenu.pidValues
            
        }
        
        WheelsSettingsPage {
            id: wheelsPage
        }
        
        CameraSettingsPage {
            id: cameraPage
            coordinateValues: settingsMenu.coordinateValues

        }
        
        ArmSettingsPage {
            id: armPage
        }
    }
}