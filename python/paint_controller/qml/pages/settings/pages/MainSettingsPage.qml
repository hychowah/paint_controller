import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
    
    signal pageRequested(string page)
    
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
            subtitle: settingsManager
                ? "Max speed: " + settingsManager.winch_max_speed_mmps.toFixed(1) + " mm/s"
                : "Max speed settings"
            
            onClicked: root.pageRequested("winch")
        }
        
        SettingsItem {
            title: "Wheels"
            subtitle: settingsManager
                ? "Track max: " + settingsManager.track_max_speed.toFixed(1)
                    + ", travel max: " + settingsManager.wheel_travel_max.toFixed(0) + " mm"
                : "Wheel speed and travel settings"
            
            onClicked: root.pageRequested("wheels")
        }
        
        SettingsItem {
            title: "Camera"
            subtitle: settingsManager
                ? "Base-top zoom: " + settingsManager.base_top_view_zoom.toFixed(2)
                    + "; full calibration remains overlay-primary"
                : "Base-top calibration and camera settings"
            
            onClicked: root.pageRequested("camera")
        }
        
        SettingsCategory {
            title: "End Effector Settings"
        }
        
        SettingsItem {
            title: "Arm"
            subtitle: settingsManager
                ? "Retract: " + settingsManager.arm_retract_length + " mm, extend: "
                    + settingsManager.arm_extend_length + " mm"
                : "Arm presets and end-effector settings"
            
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
}