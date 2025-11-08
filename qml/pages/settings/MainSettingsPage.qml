import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
    
    property real winchMaxSpeed: 50.0
    
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
            subtitle: "Max speed: " + root.winchMaxSpeed.toFixed(1) + " RPM"
            
            onClicked: root.pageRequested("winch")
        }
        
        SettingsItem {
            title: "Wheels"
            subtitle: "Wheel configuration and speed limits"
            
            onClicked: root.pageRequested("wheels")
        }
        
        SettingsItem {
            title: "Camera"
            subtitle: "Camera settings and calibration"
            
            onClicked: root.pageRequested("camera")
        }
        
        SettingsCategory {
            title: "End Effector Settings"
        }
        
        SettingsItem {
            title: "Arm"
            subtitle: "Retractable Arm configuration"
            
            onClicked: root.pageRequested("arm")
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 20
            color: "transparent"
        }
    }
}