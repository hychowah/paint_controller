// Monitor UI - 1280x720 optimized for 7-inch industrial display
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"
import "../../components/buttons"
import "../../components/displays"

Rectangle {
    id: monitorPage
    anchors.fill: parent
    color: "#1e222b"  // Industrial dark background
    
    // Track IMU history for sparklines
    property var imuAccZHistory: []
    property var imuAngularAccZHistory: []
    property var imuRollHistory: []
    
    // Constants for max values (adjust based on actual hardware specs)
    // Note: These must be > 0 to avoid division by zero
    property real maxWinchTorque: 100.0      // Nm
    property real maxWheelCurrent: 10.0      // A
    property real maxArmCurrent: 5.0         // A
    property real maxArmExtension: 2000.0    // mm
    
    // Update IMU history when data changes
    Connections {
        target: teensyController
        
        function onStatus_changed(status) {
            // Add new values and keep last 10
            imuAccZHistory.push(status.imu_acc_z || 0)
            if (imuAccZHistory.length > 10) imuAccZHistory.shift()
            
            imuAngularAccZHistory.push(status.imu_angular_acc_z || 0)
            if (imuAngularAccZHistory.length > 10) imuAngularAccZHistory.shift()
            
            imuRollHistory.push(status.imu_roll || 0)
            if (imuRollHistory.length > 10) imuRollHistory.shift()
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Top Header Bar
        MonitorHeader {
            Layout.fillWidth: true
        }
        
        // Main Body (3-Column Layout)
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10
            
            // LEFT COLUMN (30%): Mobility & Fluids
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 3  // 30% weight (3 of 10)
                Layout.margins: 10
                spacing: 10
                
                WheelsCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 1  // Equal weight with ValvesCard
                    maxWheelCurrent: monitorPage.maxWheelCurrent
                }
                
                ValvesCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 1  // Equal weight with WheelsCard
                }
            }
            
            // CENTER COLUMN (40%): Core Operations
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 4  // 40% weight (4 of 10)
                Layout.margins: 10
                spacing: 10
                
                TeensyArmCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 1  // Equal weight
                    maxArmCurrent: monitorPage.maxArmCurrent
                    maxArmExtension: monitorPage.maxArmExtension
                }
                
                WinchCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 1  // Equal weight
                    maxWinchTorque: monitorPage.maxWinchTorque
                }
            }
            
            // RIGHT COLUMN (30%): Sensor Density
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 3  // 30% weight (3 of 10)
                Layout.margins: 10
                spacing: 10
                
                IMUCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    imuAccZHistory: monitorPage.imuAccZHistory
                    imuAngularAccZHistory: monitorPage.imuAngularAccZHistory
                    imuRollHistory: monitorPage.imuRollHistory
                }
            }
        }
    }
}
