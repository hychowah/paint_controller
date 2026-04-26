import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
    
    signal pageRequested(string page)

    property string winchSubtitle: "Max speed settings"
    property string wheelsSubtitle: "Wheel speed and travel settings"
    property string cameraSubtitle: "Base-top calibration and camera settings"
    property string armSubtitle: "Arm presets and end-effector settings"

    function refreshSummaries() {
        if (!settingsManager) {
            winchSubtitle = "Max speed settings"
            wheelsSubtitle = "Wheel speed and travel settings"
            cameraSubtitle = "Base-top calibration and camera settings"
            armSubtitle = "Arm presets and end-effector settings"
            return
        }

        winchSubtitle = settingsManager.getRouteSummary("winch")
        wheelsSubtitle = settingsManager.getRouteSummary("wheels")
        cameraSubtitle = settingsManager.getRouteSummary("camera")
        armSubtitle = settingsManager.getRouteSummary("arm")
    }
    
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Settings"
            showBack: false
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }
        
        SettingsCategory {
            title: "Base Settings"
        }
        
        SettingsItem {
            title: "Winch"
            subtitle: root.winchSubtitle
            
            onClicked: root.pageRequested("winch")
        }
        
        SettingsItem {
            title: "Wheels"
            subtitle: root.wheelsSubtitle
            
            onClicked: root.pageRequested("wheels")
        }
        
        SettingsItem {
            title: "Camera"
            subtitle: root.cameraSubtitle
            
            onClicked: root.pageRequested("camera")
        }
        
        SettingsCategory {
            title: "End Effector Settings"
        }
        
        SettingsItem {
            title: "Arm"
            subtitle: root.armSubtitle
            
            onClicked: root.pageRequested("arm")
        }
        
        SettingsCategory {
            title: "Display Settings"
        }
        
        SettingsItem {
            title: "Multi-Screen Test"
            subtitle: "Test multi-screen display support"
            
            onClicked: {
                if (backend) {
                    backend.toggle_multiscreen_window()
                }
            }
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 20
            color: "transparent"
        }
    }

    Connections {
        target: settingsManager

        function onSetting_changed(key, value) {
            root.refreshSummaries()
        }
    }

    Component.onCompleted: root.refreshSummaries()
}