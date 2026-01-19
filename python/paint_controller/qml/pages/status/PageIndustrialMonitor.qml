// Industrial Monitor UI - 1280x720 optimized for external industrial display
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"
import "../../components/buttons"
import "../../components/displays"

Rectangle {
    id: industrialMonitorPage
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
        
        // ====================================================================
        // TOP HEADER BAR (80px) - Global Status & E-Stop
        // ====================================================================
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "#252a35"
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 20
                
                // LEFT SECTION: Telemetry
                RowLayout {
                    Layout.preferredWidth: 350
                    spacing: 15
                    
                    // Voltage indicator
                    Rectangle {
                        Layout.preferredWidth: 110
                        Layout.fillHeight: true
                        color: "#29303b"
                        radius: 6
                        
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4
                            
                            Text {
                                text: "⚡"
                                font.pixelSize: 20
                                color: "#3498db"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: (teensyController.all_status.voltage || 0).toFixed(1) + "V"
                                font.pixelSize: 18
                                font.family: "Monospace"
                                font.bold: true
                                color: "#FFFFFF"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }
                    
                    // Temperature indicator
                    Rectangle {
                        Layout.preferredWidth: 110
                        Layout.fillHeight: true
                        color: "#29303b"
                        radius: 6
                        
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4
                            
                            Text {
                                text: "🌡️"
                                font.pixelSize: 20
                                color: "#f39c12"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: (teensyController.all_status.temperature || 0).toFixed(0) + "°C"
                                font.pixelSize: 18
                                font.family: "Monospace"
                                font.bold: true
                                color: "#FFFFFF"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }
                    
                    // Loop time indicator
                    Rectangle {
                        Layout.preferredWidth: 110
                        Layout.fillHeight: true
                        color: "#29303b"
                        radius: 6
                        
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4
                            
                            Text {
                                text: "⏱️"
                                font.pixelSize: 20
                                color: "#2ecc71"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: "Loop: " + (teensyController.all_status.loop_time || 0).toFixed(0) + "ms"
                                font.pixelSize: 14
                                font.family: "Monospace"
                                font.bold: true
                                color: "#FFFFFF"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }
                }
                
                // MIDDLE SECTION: Status Badges (PASSIVE - Labels, not buttons)
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 12
                        
                        // Relay Status Badge (small)
                        Rectangle {
                            Layout.preferredWidth: 100
                            Layout.preferredHeight: 35
                            color: "transparent"
                            border.color: teensyController.all_status.relay_on ? "#2ecc71" : "#7f8c8d"
                            border.width: 2
                            radius: 6
                            
                            Text {
                                anchors.centerIn: parent
                                text: "RELAY: " + (teensyController.all_status.relay_on ? "ON" : "OFF")
                                font.pixelSize: 11
                                font.family: "Roboto"
                                font.bold: true
                                color: teensyController.all_status.relay_on ? "#2ecc71" : "#7f8c8d"
                            }
                        }
                        
                        // Enable Status Badge (larger)
                        Rectangle {
                            Layout.preferredWidth: 180
                            Layout.preferredHeight: 50
                            color: teensyController.all_status.enabled ? "#2ecc71" : "#7f8c8d"
                            radius: 8
                            
                            Text {
                                anchors.centerIn: parent
                                text: teensyController.all_status.enabled ? "SYSTEM ENABLED" : "SYSTEM DISABLED"
                                font.pixelSize: 14
                                font.family: "Roboto"
                                font.bold: true
                                color: "#FFFFFF"
                            }
                        }
                    }
                }
                
                // RIGHT SECTION: Emergency Action (ACTIVE)
                Button {
                    id: emergencyStopButton
                    Layout.preferredWidth: 200
                    Layout.preferredHeight: 60
                    
                    background: Rectangle {
                        color: emergencyStopButton.pressed ? "#c0392b" : "#e74c3c"
                        radius: 8
                        border.color: "#a93226"
                        border.width: 3
                        
                        // Subtle pulse animation
                        SequentialAnimation on opacity {
                            running: true
                            loops: Animation.Infinite
                            NumberAnimation { to: 0.85; duration: 1000 }
                            NumberAnimation { to: 1.0; duration: 1000 }
                        }
                        
                        // Drop shadow effect (simulated with offset rectangle)
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: -2
                            color: "transparent"
                            border.color: "#00000040"
                            border.width: 2
                            radius: 10
                            z: -1
                        }
                    }
                    
                    contentItem: Text {
                        text: "EMERGENCY STOP"
                        font.pixelSize: 16
                        font.family: "Roboto"
                        font.bold: true
                        font.letterSpacing: 1.5
                        color: "#FFFFFF"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: {
                        // TODO: Wire to actual emergency stop handler when available
                        // For now, try to disable all systems
                        console.log("EMERGENCY STOP ACTIVATED")
                        if (typeof teensyController !== 'undefined') {
                            teensyController.setEnabled(false)
                        }
                        if (typeof wheelController !== 'undefined') {
                            wheelController.setEnabled(false)
                        }
                        if (typeof winchController !== 'undefined') {
                            winchController.setEnabled(false)
                        }
                    }
                }
            }
        }
        
        // ====================================================================
        // MAIN BODY (3-Column Layout) - remaining 640px height
        // ====================================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10
            
            // LEFT COLUMN (30%): Mobility & Fluids
            ColumnLayout {
                Layout.preferredWidth: parent.width * 0.30
                Layout.fillHeight: true
                Layout.margins: 10
                spacing: 10
                
                // WHEELS CARD
                IndustrialCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height * 0.5
                    title: "Wheels"
                    
                    RowLayout {
                        anchors.fill: parent
                        spacing: 8
                        
                        // Left Wheel
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 8
                            
                            Text {
                                text: "L"
                                font.pixelSize: 16
                                font.bold: true
                                font.family: "Roboto"
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: Math.abs(wheelController.left_wheel_speed || 0).toFixed(2)
                                font.pixelSize: 28
                                font.family: "Monospace"
                                font.bold: true
                                color: "#3498db"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: "m/s"
                                font.pixelSize: 12
                                font.family: "Roboto"
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: Math.abs(wheelController.left_wheel_current || 0).toFixed(1) + " A"
                                font.pixelSize: 14
                                font.family: "Monospace"
                                color: "#FFFFFF"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            ProgressBarIndicator {
                                Layout.fillWidth: true
                                Layout.margins: 4
                                value: Math.abs(wheelController.left_wheel_current || 0)
                                maxValue: maxWheelCurrent
                                barColor: "#2ecc71"
                            }
                        }
                        
                        // Right Wheel
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 8
                            
                            Text {
                                text: "R"
                                font.pixelSize: 16
                                font.bold: true
                                font.family: "Roboto"
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: Math.abs(wheelController.right_wheel_speed || 0).toFixed(2)
                                font.pixelSize: 28
                                font.family: "Monospace"
                                font.bold: true
                                color: "#3498db"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: "m/s"
                                font.pixelSize: 12
                                font.family: "Roboto"
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: Math.abs(wheelController.right_wheel_current || 0).toFixed(1) + " A"
                                font.pixelSize: 14
                                font.family: "Monospace"
                                color: "#FFFFFF"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            ProgressBarIndicator {
                                Layout.fillWidth: true
                                Layout.margins: 4
                                value: Math.abs(wheelController.right_wheel_current || 0)
                                maxValue: maxWheelCurrent
                                barColor: "#2ecc71"
                            }
                        }
                    }
                }
                
                // VALVES CARD
                IndustrialCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height * 0.5
                    title: "Valves"
                    
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        
                        // Flow Rate
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                text: "Flow Rate"
                                font.pixelSize: 12
                                font.family: "Roboto"
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: (teensyController.all_status.valve_rate || 0).toFixed(1)
                                font.pixelSize: 32
                                font.family: "Monospace"
                                font.bold: true
                                color: "#3498db"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Text {
                                text: "L/min"
                                font.pixelSize: 12
                                font.family: "Roboto"
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                        
                        Item { Layout.preferredHeight: 10 }
                        
                        // Valve Position
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            
                            // Calculate valve position percentage once
                            property real valvePositionPercent: (teensyController.all_status.valve_position || 0)
                            
                            Text {
                                text: "Valve Position: " + parent.valvePositionPercent.toFixed(0) + "%"
                                font.pixelSize: 12
                                font.family: "Roboto"
                                color: "#AAAAAA"
                            }
                            
                            // Position bar with thumb indicator
                            Item {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 20
                                
                                property real valvePositionPercent: parent.valvePositionPercent
                                property real normalizedPosition: valvePositionPercent / 100.0
                                
                                // Background bar
                                Rectangle {
                                    anchors.fill: parent
                                    color: "#1e222b"
                                    radius: 10
                                }
                                
                                // Progress bar (cyan)
                                Rectangle {
                                    width: Math.max(0, Math.min(parent.width * parent.normalizedPosition, parent.width))
                                    height: parent.height
                                    color: "#3498db"
                                    radius: 10
                                    
                                    Behavior on width {
                                        NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                                    }
                                }
                                
                                // White thumb indicator
                                Rectangle {
                                    x: Math.max(5, Math.min(parent.width * parent.normalizedPosition - 5, parent.width - 15))
                                    y: parent.height / 2 - 7
                                    width: 14
                                    height: 14
                                    color: "#FFFFFF"
                                    radius: 7
                                    border.color: "#3498db"
                                    border.width: 2
                                    
                                    Behavior on x {
                                        NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // CENTER COLUMN (40%): Core Operations (HERO)
            ColumnLayout {
                Layout.preferredWidth: parent.width * 0.40
                Layout.fillHeight: true
                Layout.margins: 10
                spacing: 10
                
                // TEENSY ARM CARD
                IndustrialCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height * 0.5
                    title: "Teensy Arm"
                    
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12
                        
                        // Extension
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                text: "Extension"
                                font.pixelSize: 12
                                font.family: "Roboto"
                                color: "#AAAAAA"
                            }
                            
                            Text {
                                text: ((teensyController.all_status.arm_extension_dist || 0) / 1000).toFixed(2) + " m"
                                font.pixelSize: 28
                                font.family: "Monospace"
                                font.bold: true
                                color: "#2ecc71"
                            }
                            
                            ProgressBarIndicator {
                                Layout.fillWidth: true
                                value: teensyController.all_status.arm_extension_dist || 0
                                maxValue: maxArmExtension
                                barColor: "#2ecc71"
                                barHeight: 8
                            }
                        }
                        
                        Item { Layout.preferredHeight: 10 }
                        
                        // Current comparison: Arm vs Spray Gun
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 20
                            
                            // Arm Current
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                
                                Text {
                                    text: "Arm Current"
                                    font.pixelSize: 11
                                    font.family: "Roboto"
                                    color: "#AAAAAA"
                                    horizontalAlignment: Text.AlignHCenter
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                
                                // Vertical bar chart
                                Item {
                                    Layout.preferredWidth: 40
                                    Layout.preferredHeight: 100
                                    Layout.alignment: Qt.AlignHCenter
                                    
                                    property real heightRatio: maxArmCurrent > 0 ? Math.abs(teensyController.all_status.arm_rail_current || 0) / maxArmCurrent : 0
                                    
                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        width: parent.width
                                        height: Math.max(10, parent.height * parent.heightRatio)
                                        color: "#3498db"
                                        radius: 4
                                        
                                        Behavior on height {
                                            NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                                        }
                                    }
                                }
                                
                                Text {
                                    text: Math.abs(teensyController.all_status.arm_rail_current || 0).toFixed(2) + " A"
                                    font.pixelSize: 12
                                    font.family: "Monospace"
                                    color: "#FFFFFF"
                                    horizontalAlignment: Text.AlignHCenter
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                            
                            // Spray Gun Motor Current
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                
                                Text {
                                    text: "Spray Gun Current"
                                    font.pixelSize: 11
                                    font.family: "Roboto"
                                    color: "#AAAAAA"
                                    horizontalAlignment: Text.AlignHCenter
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                
                                // Vertical bar chart
                                Item {
                                    Layout.preferredWidth: 40
                                    Layout.preferredHeight: 100
                                    Layout.alignment: Qt.AlignHCenter
                                    
                                    property real heightRatio: maxArmCurrent > 0 ? Math.abs(teensyController.all_status.spray_gun_motor_current || 0) / maxArmCurrent : 0
                                    
                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        width: parent.width
                                        height: Math.max(10, parent.height * parent.heightRatio)
                                        color: "#e74c3c"
                                        radius: 4
                                        
                                        Behavior on height {
                                            NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                                        }
                                    }
                                }
                                
                                Text {
                                    text: Math.abs(teensyController.all_status.spray_gun_motor_current || 0).toFixed(2) + " A"
                                    font.pixelSize: 12
                                    font.family: "Monospace"
                                    color: "#FFFFFF"
                                    horizontalAlignment: Text.AlignHCenter
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }
                    }
                }
                
                // WINCH DATA CARD
                IndustrialCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: parent.height * 0.5
                    title: "Winch Data"
                    
                    GridLayout {
                        anchors.fill: parent
                        columns: 2
                        rowSpacing: 12
                        columnSpacing: 20
                        
                        // Cable Length
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                text: "📏 Cable Length"
                                font.pixelSize: 12
                                font.family: "Roboto"
                                color: "#AAAAAA"
                            }
                            
                            Text {
                                text: ((winchController.cable_length || 0) / 1000).toFixed(2) + " m"
                                font.pixelSize: 24
                                font.family: "Monospace"
                                font.bold: true
                                color: "#3498db"
                            }
                        }
                        
                        // Cable Speed
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Row {
                                spacing: 4
                                
                                Text {
                                    text: (winchController.cable_speed || 0) >= 0 ? "↑" : "↓"
                                    font.pixelSize: 16
                                    color: "#f39c12"
                                }
                                
                                Text {
                                    text: "Cable Speed"
                                    font.pixelSize: 12
                                    font.family: "Roboto"
                                    color: "#AAAAAA"
                                }
                            }
                            
                            Text {
                                text: Math.abs(winchController.cable_speed || 0).toFixed(1) + " m/s"
                                font.pixelSize: 24
                                font.family: "Monospace"
                                font.bold: true
                                color: "#f39c12"
                            }
                        }
                        
                        // Winch Voltage
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                text: "Winch Voltage"
                                font.pixelSize: 11
                                font.family: "Roboto"
                                color: "#AAAAAA"
                            }
                            
                            Text {
                                text: (winchController.motor_voltage || 0).toFixed(1) + " V"
                                font.pixelSize: 16
                                font.family: "Monospace"
                                color: "#2ecc71"
                            }
                        }
                        
                        // Torque (Amber if > 80% of max)
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                text: "Torque"
                                font.pixelSize: 11
                                font.family: "Roboto"
                                color: "#AAAAAA"
                            }
                            
                            Text {
                                property real torquePercent: maxWinchTorque > 0 ? (winchController.winch_torque || 0) / maxWinchTorque * 100 : 0
                                text: (winchController.winch_torque || 0).toFixed(1) + " Nm"
                                font.pixelSize: 16
                                font.family: "Monospace"
                                color: torquePercent > 80 ? "#f39c12" : "#2ecc71"  // Amber if high
                            }
                        }
                    }
                }
            }
            
            // RIGHT COLUMN (30%): Sensor Density (IMU)
            ColumnLayout {
                Layout.preferredWidth: parent.width * 0.30
                Layout.fillHeight: true
                Layout.margins: 10
                spacing: 10
                
                // IMU CARD
                IndustrialCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    title: "IMU"
                    
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 4
                        
                        // Header row
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                Layout.preferredWidth: 80
                                text: "Data Type"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                font.bold: true
                                color: "#AAAAAA"
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: "X"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                font.bold: true
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: "Y"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                font.bold: true
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: "Z"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                font.bold: true
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: "Trend"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                font.bold: true
                                color: "#AAAAAA"
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                        
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
                        
                        // Angle row
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                Layout.preferredWidth: 80
                                text: "Angle (°)"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                color: "#FFFFFF"
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_pitch || 0).toFixed(1)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#3498db"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_roll || 0).toFixed(1)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#3498db"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_yaw || 0).toFixed(1)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#3498db"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Sparkline {
                                Layout.preferredWidth: 50
                                Layout.preferredHeight: 20
                                dataPoints: imuRollHistory
                                lineColor: "#3498db"
                            }
                        }
                        
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
                        
                        // Acceleration row
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                Layout.preferredWidth: 80
                                text: "Accel (g)"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                color: "#FFFFFF"
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_acc_x || 0).toFixed(2)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#2ecc71"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_acc_y || 0).toFixed(2)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#2ecc71"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_acc_z || 0).toFixed(2)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#2ecc71"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Sparkline {
                                Layout.preferredWidth: 50
                                Layout.preferredHeight: 20
                                dataPoints: imuAccZHistory
                                lineColor: "#2ecc71"
                            }
                        }
                        
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
                        
                        // Angular Acceleration row
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            
                            Text {
                                Layout.preferredWidth: 80
                                text: "Ang Accel"
                                font.pixelSize: 10
                                font.family: "Roboto"
                                color: "#FFFFFF"
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_angular_acc_x || 0).toFixed(2)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#f39c12"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_angular_acc_y || 0).toFixed(2)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#f39c12"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Text {
                                Layout.preferredWidth: 50
                                text: (teensyController.all_status.imu_angular_acc_z || 0).toFixed(2)
                                font.pixelSize: 11
                                font.family: "Monospace"
                                color: "#f39c12"
                                horizontalAlignment: Text.AlignRight
                            }
                            
                            Sparkline {
                                Layout.preferredWidth: 50
                                Layout.preferredHeight: 20
                                dataPoints: imuAngularAccZHistory
                                lineColor: "#f39c12"
                            }
                        }
                    }
                }
            }
        }
    }
}
