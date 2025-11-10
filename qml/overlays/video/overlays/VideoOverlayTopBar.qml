import QtQuick 2.15
import QtQuick.Controls 2.15
import "."



Rectangle {
    id: topBar
    width: root.width
    height: 50
    color: "transparent"
    
    anchors.top: parent.top
    // anchors.left: parent.left
    // anchors.right: parent.right
    
    VideoOverlayStyle { id: style }
    
    // EF Battery: 7S Li-ion (21V min, 29.4V max)
    property real efBatteryMin: 21.0
    property real efBatteryMax: 29.4
    
    // Base Battery: 13S Li-ion (39V min, 54.6V max)
    property real baseBatteryMin: 39.0
    property real baseBatteryMax: 54.6
    
        // Network ping times (in milliseconds) - bind to sshHandler's devicePingTimes
    property real efPingMs: {
        if (sshHandler && sshHandler.devicePingTimes) {
            var val = sshHandler.devicePingTimes["END_EFFECTOR"];
            return val ? parseFloat(val) : 0;
        }
        return 0;
    }
    property real basePingMs: {
        if (sshHandler && sshHandler.devicePingTimes) {
            var val = sshHandler.devicePingTimes["BASE"];
            return val ? parseFloat(val) : 0;
        }
        return 0;
    }
    
    /**
     * Calculate battery percentage from voltage
     */
    function calculateBatteryPercent(voltage, minVolt, maxVolt) {
        const clamped = Math.max(minVolt, Math.min(maxVolt, voltage))
        return Math.round(((clamped - minVolt) / (maxVolt - minVolt)) * 100)
    }
    
    /**
     * Get battery color based on percentage
     */
    function getBatteryColor(percent) {
        if (percent > 50) return "#00FF00"      // Green
        if (percent > 25) return "#FFAA00"      // Orange
        return "#FF3333"                         // Red
    }
    
    /**
     * Calculate signal quality based on ping time
     * Returns: 0-3 bars (0=bad, 3=excellent)
     */
    function calculateSignalBars(pingMs) {
        if (pingMs <= 0) return 0               // No signal
        if (pingMs < 50) return 3               // Excellent (< 50ms)
        if (pingMs < 100) return 2              // Good (50-100ms)
        if (pingMs < 200) return 1              // Fair (100-200ms)
        return 0                                 // Poor (> 200ms)
    }
    
    /**
     * Get signal color based on ping time
     */
    function getSignalColor(pingMs) {
        const bars = calculateSignalBars(pingMs)
        if (bars === 3) return "#00FF00"        // Green - Excellent
        if (bars === 2) return "#FFAA00"        // Orange - Good
        if (bars === 1) return "#FF8800"        // Orange-Red - Fair
        return "#FF3333"                         // Red - Poor/No signal
    }
    
    // LEFT SIDE - EF Info (Battery + Network)
    Rectangle {
        id: leftPanel
        width: 300
        height: parent.height
        color: "transparent"
        
        anchors.left: parent.left
        anchors.leftMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        
        Row {
            anchors.fill: parent
            spacing: 8
            
            // EF Label
            Text {
                text: "EF"
                color: "white"
                font.pixelSize: 14
                font.bold: true
                font.family: "Courier New"
                anchors.verticalCenter: parent.verticalCenter
                width: 25
            }
            
            // EF Battery Info
            Item {
                width: 100
                height: parent.height
                
                Row {
                    anchors.centerIn: parent
                    spacing: 8
                    
                    // Battery icon background
                    Rectangle {
                        width: 28
                        height: 14
                        radius: 2
                        color: "transparent"
                        border.color: style.dividerColor
                        border.width: 1
                        
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Battery fill
                        Rectangle {
                            width: parent.width * (calculateBatteryPercent(teensyController.all_status.voltage, efBatteryMin, efBatteryMax) / 100)
                            height: parent.height - 2
                            color: getBatteryColor(calculateBatteryPercent(teensyController.all_status.voltage, efBatteryMin, efBatteryMax))
                            radius: 1
                            anchors.left: parent.left
                            anchors.leftMargin: 1
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                    
                    // EF Battery percentage
                    Text {
                        text: calculateBatteryPercent(teensyController.all_status.voltage, efBatteryMin, efBatteryMax) + "%"
                        color: getBatteryColor(calculateBatteryPercent(teensyController.all_status.voltage, efBatteryMin, efBatteryMax))
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "Courier New"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
            
            // Divider
            Rectangle {
                width: 1
                height: parent.height * 0.6
                color: style.dividerColor
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // EF Network Info
            Item {
                width: 100
                height: parent.height
                
                Row {
                    anchors.centerIn: parent
                    spacing: 8
                    
                    // Network icon (signal bars simulation)
                    Column {
                        spacing: 2
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Rectangle {
                            width: 3
                            height: 3
                            color: calculateSignalBars(efPingMs) >= 1 ? getSignalColor(efPingMs) : style.dividerColor
                            radius: 1.5
                            opacity: calculateSignalBars(efPingMs) >= 1 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 5
                            color: calculateSignalBars(efPingMs) >= 2 ? getSignalColor(efPingMs) : style.dividerColor
                            radius: 1
                            opacity: calculateSignalBars(efPingMs) >= 2 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 7
                            color: calculateSignalBars(efPingMs) >= 3 ? getSignalColor(efPingMs) : style.dividerColor
                            radius: 1
                            opacity: calculateSignalBars(efPingMs) >= 3 ? 1 : 0.3
                        }
                    }
                    
                    // Network ping time
                    Text {
                        text: efPingMs > 0 ? efPingMs.toFixed(0) + "ms" : "Net OK"
                        color: getSignalColor(efPingMs)
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "Courier New"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }
    }

    // empty rectangle to fill width
    Rectangle {
        id: centerFiller
        width: parent.width - leftPanel.width - rightPanel.width - 40  // 40 = 10px margins on each side
        height: parent.height
        color: "transparent"
        anchors.horizontalCenter: parent.horizontalCenter
    }
    
    // RIGHT SIDE - Base Info (Battery left, Network right)
    Rectangle {
        id: rightPanel
        width: 300
        height: parent.height
        color: "transparent"
        
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        
        Row {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.fill: parent
            spacing: 8
            
            // Base Battery Info
            Item {
                width: 100
                height: parent.height
                anchors.right: dividerRight.left
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                
                Row {
                    anchors.centerIn: parent
                    spacing: 8
                    
                    // Base Battery percentage
                    Text {
                        text: calculateBatteryPercent(winchController.motor_voltage, baseBatteryMin, baseBatteryMax) + "%"
                        color: getBatteryColor(calculateBatteryPercent(winchController.motor_voltage, baseBatteryMin, baseBatteryMax))
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "Courier New"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    // Battery icon background
                    Rectangle {
                        width: 28
                        height: 14
                        radius: 2
                        color: "transparent"
                        border.color: style.dividerColor
                        border.width: 1
                        
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Battery fill
                        Rectangle {
                            width: parent.width * (calculateBatteryPercent(winchController.motor_voltage, baseBatteryMin, baseBatteryMax) / 100)
                            height: parent.height - 2
                            color: getBatteryColor(calculateBatteryPercent(winchController.motor_voltage, baseBatteryMin, baseBatteryMax))
                            radius: 1
                            anchors.left: parent.left
                            anchors.leftMargin: 1
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }
            
            // Divider
            Rectangle {
                id: dividerRight
                width: 1
                height: parent.height * 0.6
                color: style.dividerColor
                anchors.right: networkInfoRight.left
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // Base Network Info
            Item {
                id: networkInfoRight
                width: 100
                height: parent.height
                anchors.right: baseLabel.left
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                
                Row {
                    anchors.centerIn: parent
                    spacing: 8
                    
                    // Network ping time
                    Text {
                        text: basePingMs > 0 ? basePingMs.toFixed(0) + "ms" : "Net OK"
                        color: getSignalColor(basePingMs)
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "Courier New"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    // Network icon (signal bars simulation)
                    Column {
                        spacing: 2
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Rectangle {
                            width: 3
                            height: 3
                            color: calculateSignalBars(basePingMs) >= 1 ? getSignalColor(basePingMs) : style.dividerColor
                            radius: 1.5
                            opacity: calculateSignalBars(basePingMs) >= 1 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 5
                            color: calculateSignalBars(basePingMs) >= 2 ? getSignalColor(basePingMs) : style.dividerColor
                            radius: 1
                            opacity: calculateSignalBars(basePingMs) >= 2 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 7
                            color: calculateSignalBars(basePingMs) >= 3 ? getSignalColor(basePingMs) : style.dividerColor
                            radius: 1
                            opacity: calculateSignalBars(basePingMs) >= 3 ? 1 : 0.3
                        }
                    }
                }
            }
            
            // BASE Label
            Text {
                id: baseLabel
                text: "BASE"
                color: "white"
                font.pixelSize: 14
                font.bold: true
                font.family: "Courier New"
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: 25
            }
        }
    }
}
