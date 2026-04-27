import QtQuick
import QtQuick.Controls
import "."
import "../../../core"
import "../../../components/displays"



Rectangle {
    id: topBar
    required property var topBarModel
    width: root.width
    height: 50
    color: "transparent"
    
    anchors.top: parent.top
    // anchors.left: parent.left
    // anchors.right: parent.right
    
    readonly property color dividerColor: CommonStyle.videoDivider
    readonly property color topBarTextColor: CommonStyle.textPrimary
    readonly property color batteryGoodColor: CommonStyle.statusSuccess
    readonly property color batteryMediumColor: CommonStyle.statusWarning
    readonly property color batteryLowColor: CommonStyle.statusError
    readonly property color signalExcellentColor: CommonStyle.statusSuccess
    readonly property color signalGoodColor: CommonStyle.statusWarning
    readonly property color signalFairColor: CommonStyle.accentMuted
    readonly property color signalPoorColor: CommonStyle.statusError
    readonly property color tempNormalColor: CommonStyle.statusSuccess
    readonly property color tempWarningColor: CommonStyle.statusWarning
    readonly property color tempCriticalColor: CommonStyle.statusError
    readonly property color timeColor: CommonStyle.accentMuted
    readonly property color recordingColor: CommonStyle.videoRecording
    readonly property int topBarLabelFontSize: CommonStyle.fontCaption + 1
    readonly property int topBarValueFontSize: CommonStyle.fontLabel
    readonly property int topBarIconFontSize: CommonStyle.fontCaption - 1
    readonly property string topBarFontFamily: CommonStyle.fontMono
    
    // EF Battery: 7S Li-ion (21V min, 29.4V max)
    readonly property real efBatteryMin: 21.0
    readonly property real efBatteryMax: 29.4
    
    // Base Battery: 13S Li-ion (39V min, 54.6V max)
    readonly property real baseBatteryMin: 39.0
    readonly property real baseBatteryMax: 54.6
    
    property real efPingMs: topBarModel.endEffectorPingMs
    property real basePingMs: topBarModel.basePingMs
    
    /**
     * Calculate battery percentage from voltage using Li-ion discharge curve
     * Uses a piecewise approximation of the actual Li-ion voltage curve
     * for more accurate remaining capacity estimation
     */
    function calculateBatteryPercent(voltage, minVolt, maxVolt) {
        const clamped = Math.max(minVolt, Math.min(maxVolt, voltage))
        const normalized = (clamped - minVolt) / (maxVolt - minVolt)
        
        // Li-ion discharge curve approximation
        // Battery capacity doesn't decrease linearly with voltage
        // Using a piecewise cubic approximation for realistic curve
        let percent
        
        if (normalized < 0.1) {
            // Below 10% - rapid drop-off (exponential decline)
            percent = normalized * 100 / 0.1 * 0.2  // 0-10% voltage maps to 0-2% capacity
        } else if (normalized < 0.5) {
            // 10-50% voltage - steeper decline
            percent = 2 + (normalized - 0.1) * 100 / 0.4 * 0.3  // Maps to 2-32% capacity
        } else if (normalized < 0.8) {
            // 50-80% voltage - moderate decline (most capacity here)
            percent = 32 + (normalized - 0.5) * 100 / 0.3 * 0.48  // Maps to 32-80% capacity
        } else {
            // 80-100% voltage - slower decline at top
            percent = 80 + (normalized - 0.8) * 100 / 0.2 * 0.2  // Maps to 80-100% capacity
        }
        
        return Math.round(Math.max(0, Math.min(100, percent)))
    }
    
    /**
     * Get battery color based on percentage
     */
    function getBatteryColor(percent) {
        if (percent > 50) return batteryGoodColor
        if (percent > 25) return batteryMediumColor
        return batteryLowColor
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
        if (bars === 3) return signalExcellentColor
        if (bars === 2) return signalGoodColor
        if (bars === 1) return signalFairColor
        return signalPoorColor
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
                color: topBarTextColor
                font.pixelSize: topBarLabelFontSize
                font.bold: true
                font.family: topBarFontFamily
                anchors.verticalCenter: parent.verticalCenter
                width: 25
            }
            
            // EF Battery Info
            BatteryDisplay {
                width: 100
                height: parent.height
                batteryPercent: calculateBatteryPercent(topBarModel.endEffectorBatteryVoltage, efBatteryMin, efBatteryMax)
                borderColor: dividerColor
            }
            
            // Divider
            Rectangle {
                width: 1
                height: parent.height * 0.6
                color: dividerColor
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
                            color: calculateSignalBars(efPingMs) >= 1 ? getSignalColor(efPingMs) : dividerColor
                            radius: 1.5
                            opacity: calculateSignalBars(efPingMs) >= 1 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 5
                            color: calculateSignalBars(efPingMs) >= 2 ? getSignalColor(efPingMs) : dividerColor
                            radius: 1
                            opacity: calculateSignalBars(efPingMs) >= 2 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 7
                            color: calculateSignalBars(efPingMs) >= 3 ? getSignalColor(efPingMs) : dividerColor
                            radius: 1
                            opacity: calculateSignalBars(efPingMs) >= 3 ? 1 : 0.3
                        }
                    }
                    
                    // Network ping time
                    Text {
                        text: efPingMs > 0 ? efPingMs.toFixed(0) + "ms" : "Net OK"
                        color: getSignalColor(efPingMs)
                        font.pixelSize: topBarValueFontSize
                        font.bold: true
                        font.family: topBarFontFamily
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }
    }
    
    // CENTER - System Monitor Info (Battery, Temp, Time)
    // NEW APPROACH: This container fills the space between the side panels
    Rectangle {
        id: topCenterPanel
        height: parent.height
        color: "transparent"
        
        // Anchors now define the space, they don't fight for position
        anchors.left: leftPanel.right
        anchors.right: rightPanel.left
        anchors.leftMargin: 10   // Give it 10px breathing room from the left panel
        anchors.rightMargin: 10  // Give it 10px breathing room from the right panel

        // This single Row holds all the content
        Row {
            anchors.centerIn: parent // Center this Row inside the new centerPanel
            spacing: 20
            
            // Screen Recording Indicator (only visible when recording)
            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6
                visible: topBarModel.isRecording
                
                // Pulsing red dot
                Rectangle {
                    width: 10
                    height: 10
                    radius: 5
                    color: recordingColor
                    anchors.verticalCenter: parent.verticalCenter
                    
                    SequentialAnimation on opacity {
                        running: topBarModel.isRecording
                        loops: Animation.Infinite
                        NumberAnimation { from: 1.0; to: 0.3; duration: 500 }
                        NumberAnimation { from: 0.3; to: 1.0; duration: 500 }
                    }
                }
                
                Text {
                    text: {
                        var mins = Math.floor(topBarModel.recordingDuration / 60)
                        var secs = topBarModel.recordingDuration % 60
                        return "REC " + mins + ":" + (secs < 10 ? "0" : "") + secs
                    }
                    color: recordingColor
                    font.pixelSize: topBarValueFontSize
                    font.bold: true
                    font.family: topBarFontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Divider (only visible when recording)
            Rectangle {
                width: 1
                height: parent.height * 0.6
                color: dividerColor
                anchors.verticalCenter: parent.verticalCenter
                visible: topBarModel.isRecording
            }
            
            // System Battery Info
            BatteryDisplay {
                anchors.verticalCenter: parent.verticalCenter
                batteryPercent: topBarModel.systemBatteryPercent
                borderColor: dividerColor
            }
            
            // Divider
            Rectangle {
                width: 1
                height: parent.height * 0.6
                color: dividerColor
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // CPU Temperature Info (No 'Item' wrapper needed)
            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6
                
                Text {
                    text: "🌡"
                    font.pixelSize: topBarIconFontSize
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: topBarModel.cpuTemperature.toFixed(1) + "°C"
                    color: topBarModel.cpuTemperature > 80 ? tempCriticalColor : 
                        topBarModel.cpuTemperature > 60 ? tempWarningColor : tempNormalColor
                    font.pixelSize: topBarValueFontSize
                    font.bold: true
                    font.family: topBarFontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Divider
            Rectangle {
                width: 1
                height: parent.height * 0.6
                color: dividerColor
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // Remaining Time Info (No 'Item' wrapper needed)
            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6
                
                Text {
                    text: "⏱"
                    font.pixelSize: 11
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: topBarModel.batteryRemainingTime !== "N/A" ? topBarModel.batteryRemainingTime : "---"
                    color: timeColor
                    font.pixelSize: topBarValueFontSize
                    font.bold: true
                    font.family: topBarFontFamily
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }    // RIGHT SIDE - Base Info (Battery left, Network right)
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
            BatteryDisplay {
                width: 100
                height: parent.height
                anchors.right: dividerRight.left
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                batteryPercent: calculateBatteryPercent(topBarModel.baseBatteryVoltage, baseBatteryMin, baseBatteryMax)
                borderColor: dividerColor
            }
            
            // Divider
            Rectangle {
                id: dividerRight
                width: 1
                height: parent.height * 0.6
                color: dividerColor
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
                        font.pixelSize: topBarValueFontSize
                        font.bold: true
                        font.family: topBarFontFamily
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    // Network icon (signal bars simulation)
                    Column {
                        spacing: 2
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Rectangle {
                            width: 3
                            height: 3
                            color: calculateSignalBars(basePingMs) >= 1 ? getSignalColor(basePingMs) : dividerColor
                            radius: 1.5
                            opacity: calculateSignalBars(basePingMs) >= 1 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 5
                            color: calculateSignalBars(basePingMs) >= 2 ? getSignalColor(basePingMs) : dividerColor
                            radius: 1
                            opacity: calculateSignalBars(basePingMs) >= 2 ? 1 : 0.3
                        }
                        Rectangle {
                            width: 3
                            height: 7
                            color: calculateSignalBars(basePingMs) >= 3 ? getSignalColor(basePingMs) : dividerColor
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
                color: topBarTextColor
                font.pixelSize: topBarLabelFontSize
                font.bold: true
                font.family: topBarFontFamily
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: 25
            }
        }
    }
}
