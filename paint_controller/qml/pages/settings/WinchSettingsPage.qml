import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
    
    property real winchMaxSpeed: 50.0
    property bool winchTorqueLimitEnabled: true
    property real winchTorqueLimit: 75.0
    property var pidValues: [1.0, 0.5, 0.1, 0.0]

    
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Winch Settings"
            showBack: true
            
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }
        
        DetailSettingItem {
            title: "Maximum Speed"
            subtitle: "Set the maximum winch speed"
            showSlider: true
            minValue: 10
            maxValue: 100
            currentValue: root.winchMaxSpeed
            unit: " RPM"
            
            onValueChanged: function(value) {
            }
        }
        
        DetailSettingItem {
            title: "Torque Limit"
            subtitle: "Enable automatic torque limiting"
            showToggle: true
            toggleValue: root.winchTorqueLimitEnabled
            
            onToggled: function(value) {
            }
        }
        
        DetailSettingItem {
            title: "Torque Threshold"
            subtitle: "Maximum torque before limiting"
            showSpinBox: true
            minValue: 25
            maxValue: 100
            currentValue: root.winchTorqueLimit
            unit: "%"
            
            onValueChanged: function(value) {
            }
        }
        
        DetailSettingItem {
            title: "Emergency Stop"
            subtitle: "Enable emergency stop functionality"
            showToggle: true
            toggleValue: true
            
            onToggled: function(value) {
                console.log("Emergency stop:", value)
            }
        }
        
        DetailSettingItem {
            title: "PID Controller"
            subtitle: "Set P, I, D, and Feedforward values"
            showMultipleValues: true
            valueLabels: ["P", "I", "D", "FF"]
            currentValues: root.pidValues
            minValue: -10
            maxValue: 10
            unit: ""
            
            onMultipleValuesChanged: function(values) {
                console.log("PID values updated:", values)
            }
        }
        
        DetailSettingItem {
            title: "Calibrate Winch"
            subtitle: "Run winch calibration procedure"
            showActionButton: true
            buttonText: "Start Calibration"
            buttonColor: "#FF9800"
            
            onActionButtonClicked: {
                console.log("Starting winch calibration...")
            }
        }
        
        DetailSettingItem {
            title: "Reset to Factory Defaults"
            subtitle: "Warning: This will reset all winch settings"
            showActionButton: true
            buttonText: "Reset Settings"
            buttonColor: "#F44336"
            
            onActionButtonClicked: {
                console.log("Resetting winch to factory defaults...")

            }
        }
    }
}