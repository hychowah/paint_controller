// Monitor UI - 1280x720 optimized for 7-inch industrial display
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCharts
import "../../theme"
import "./components"

Rectangle {
    id: monitorPage
    anchors.fill: parent
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus
    required property var valveStatus
    required property var lidarStatus
    color: "#1e222b"  // Industrial dark background
    
    // Lidar angle chart timing
    property var lidarStartTime: new Date().getTime()
    property int lidarTimeWindow: 30000  // 30 seconds window
    
    // Constants for max values (adjust based on actual hardware specs)
    // Note: These must be > 0 to avoid division by zero
    property real maxWinchCurrent: 10.0      // A
    property real maxWheelCurrent: 10.0      // A
    property real maxArmCurrent: 200        // mA
    property real maxArmExtension: 1500.0    // mm
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Top Header Bar
        MonitorHeader {
            Layout.fillWidth: true
            teensyStatus: monitorPage.teensyStatus
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
                    wheelStatus: monitorPage.wheelStatus
                    maxWheelCurrent: monitorPage.maxWheelCurrent
                }
                
                ValvesCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 1  // Equal weight with WheelsCard
                    valveStatus: monitorPage.valveStatus
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
                    teensyStatus: monitorPage.teensyStatus
                    maxArmCurrent: monitorPage.maxArmCurrent
                    maxArmExtension: monitorPage.maxArmExtension
                }
                
                WinchCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 1  // Equal weight
                    winchStatus: monitorPage.winchStatus
                    maxWinchCurrent: monitorPage.maxWinchCurrent
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
                    Layout.preferredHeight: 1  // Equal weight with LidarAngleCard
                    teensyStatus: monitorPage.teensyStatus
                }
                
                // Lidar Angle Chart Card
                Rectangle {
                    id: lidarAngleCard
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: 1  // Equal weight with IMUCard
                    color: "#29303b"
                    radius: 8
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 4
                        
                        // Card header
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            
                            Text {
                                text: "Wall Angle"
                                font.pixelSize: 16
                                font.family: "Roboto"
                                font.bold: true
                                color: "#FFFFFF"
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Text {
                                text: monitorPage.lidarStatus.angle.toFixed(1) + "°"
                                font.pixelSize: 18
                                font.family: "Monospace"
                                color: "#3498db"
                            }
                        }
                        
                        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
                        
                        // QtCharts LineSeries for lidar angle vs time
                        ChartView {
                            id: lidarChartView
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            antialiasing: true
                            legend.visible: false
                            backgroundColor: "#29303b"
                            plotAreaColor: "#1e222b"
                            margins.top: 0
                            margins.bottom: 0
                            margins.left: 0
                            margins.right: 0
                            
                            ValueAxis {
                                id: lidarAxisX
                                min: 0
                                max: monitorPage.lidarTimeWindow
                                labelsVisible: false
                                gridVisible: false
                                lineVisible: false
                                tickCount: 2
                            }
                            
                            ValueAxis {
                                id: lidarAxisY
                                min: -10
                                max: 10
                                tickCount: 5
                                labelsColor: "#AAAAAA"
                                labelsFont.pixelSize: 10
                                gridLineColor: "#3a4150"
                                color: "#3a4150"
                            }
                            
                            LineSeries {
                                id: lidarAngleSeries
                                name: "Angle"
                                axisX: lidarAxisX
                                axisY: lidarAxisY
                                color: "#4a9eff"
                                width: 2
                            }
                        }
                    }
                    
                    // Update chart on lidar angle change (per-property NOTIFY after TD-037)
                    Connections {
                        target: monitorPage.lidarStatus
                        function onAngleChanged() {
                            var currentTime = new Date().getTime()
                            var elapsed = currentTime - monitorPage.lidarStartTime
                            
                            lidarAngleSeries.append(elapsed, monitorPage.lidarStatus.angle)
                            
                            // Remove old points outside time window
                            while (lidarAngleSeries.count > 0 && 
                                   lidarAngleSeries.at(0).x < elapsed - monitorPage.lidarTimeWindow) {
                                lidarAngleSeries.remove(0)
                            }
                            
                            // Update X axis to scroll with time
                            lidarAxisX.min = elapsed - monitorPage.lidarTimeWindow
                            lidarAxisX.max = elapsed
                        }
                    }
                }
            }
        }
    }
}
