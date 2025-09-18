import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
        
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Wheels Settings"
            showBack: true
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }
        
        DetailSettingItem {
            title: "Wheel Position"
            subtitle: "Set target position for all wheels"
            showMultipleInputs: true
            valueLabels: ["Front L", "Front R", "Rear L", "Rear R"]
            currentValues: [0, 0, 0, 0]
            minValue: -180
            maxValue: 180
            unit: "°"
            applyButtonText: "Set Positions"
            
            onApplyInputValues: function(values) {
                console.log("Wheel positions applied:", values)
            }
        }
        
        DetailSettingItem {
            title: "Move to Position"
            subtitle: "Execute wheel movement to set positions"
            showActionButton: true
            buttonText: "Move Wheels"
            buttonColor: "#4CAF50"
            
            onActionButtonClicked: {
                console.log("Moving wheels to position...")
            }
        }
    }
}
