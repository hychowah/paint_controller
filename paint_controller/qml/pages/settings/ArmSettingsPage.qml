import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
    
    signal backRequested()
    
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Arm Settings"
            showBack: true
            onBackClicked: root.backRequested()
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }
        
        DetailSettingItem {
            title: "Joint Positions"
            subtitle: "Set target angles for arm joints"
            showMultipleInputs: true
            valueLabels: ["Base", "Shoulder", "Elbow", "Wrist"]
            currentValues: [0, 90, -45, 0]
            minValue: -180
            maxValue: 180
            unit: "°"
            applyButtonText: "Move Joints"
            
            onApplyInputValues: function(values) {
                console.log("Joint positions applied:", values)
            }
        }
        
        DetailSettingItem {
            title: "Move to Home Position"
            subtitle: "Return arm to safe home position"
            showActionButton: true
            buttonText: "Go Home"
            buttonColor: "#4CAF50"
            
            onActionButtonClicked: {
                console.log("Moving arm to home position...")
            }
        }
        
        DetailSettingItem {
            title: "Emergency Stop"
            subtitle: "Immediately stop all arm movement"
            showActionButton: true
            buttonText: "EMERGENCY STOP"
            buttonColor: "#F44336"
            
            onActionButtonClicked: {
                console.log("EMERGENCY STOP activated!")
            }
        }
    }
}