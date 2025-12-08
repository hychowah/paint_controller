import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
    
    property var coordinateValues: [10.5, 25.3, -5.2, 45.0, 90.0]
    
    
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Camera Settings"
            showBack: true
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }
        
        DetailSettingItem {
            title: "Camera Position"
            subtitle: "Set camera coordinates and orientation"
            showMultipleInputs: true
            valueLabels: ["X", "Y", "Z", "Pitch", "Yaw"]
            currentValues: root.coordinateValues
            minValue: -100
            maxValue: 100
            unit: "mm"
            applyButtonText: "Update Position"
            
            onApplyInputValues: function(values) {
                console.log("Camera position applied:", values)
            }
        }
        
        DetailSettingItem {
            title: "Auto Focus"
            subtitle: "Run automatic camera focus routine"
            showActionButton: true
            buttonText: "Start Auto Focus"
            buttonColor: "#2196F3"
            
            onActionButtonClicked: {
                console.log("Starting camera auto focus...")
            }
        }
        
        DetailSettingItem {
            title: "Capture Test Image"
            subtitle: "Take a test photo with current settings"
            showActionButton: true
            buttonText: "Capture Image"
            buttonColor: "#9C27B0"
            
            onActionButtonClicked: {
                console.log("Capturing test image...")
            }
        }
    }
}
