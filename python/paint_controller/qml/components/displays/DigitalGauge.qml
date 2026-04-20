import QtQuick
import QtQuick.Shapes
import "../../core"

Item {
    id: root
    width: 400
    height: 400

    // Properties for data binding
    property real torque: 0
    property real speed: 0
    property real maxTorque: 100
    property string units: "Nm"  // For torque
    property string speedUnits: "RPM"
    
    // Max value tracking properties
    property real maxTorqueInWindow: 0
    property var torqueHistory: []
    property int historyWindowMs: 1500  // 5 seconds window
    
    // Calculate angles based on values
    property real currentAngle: (torque / maxTorque) * 270
    property real maxAngle: (maxTorqueInWindow / maxTorque) * 270

    // Timer to update max value window
    Timer {
        id: historyTimer
        interval: 100  // Update every 100ms
        running: true
        repeat: true
        onTriggered: {
            // Add current value with timestamp
            var now = Date.now()
            torqueHistory.push({ value: torque, timestamp: now })
            
            // Remove values older than 5 seconds
            var cutoff = now - historyWindowMs
            torqueHistory = torqueHistory.filter(function(item) {
                return item.timestamp >= cutoff
            })
            
            // Update max value in window
            maxTorqueInWindow = Math.max(...torqueHistory.map(function(item) {
                return item.value
            }))
        }
    }

    // Background circle
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: 32
            strokeColor: CommonStyle.inputBackground
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            
            PathAngleArc {
                centerX: root.width / 2
                centerY: root.height / 2
                radiusX: Math.min(root.width, root.height) / 2 - 10
                radiusY: Math.min(root.width, root.height) / 2 - 10
                startAngle: 0
                sweepAngle: 360
            }
        }
    }

    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: 2
            strokeColor: CommonStyle.cardBorder
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            
            PathAngleArc {
                centerX: root.width / 2 
                centerY: root.height / 2
                radiusX: Math.min(root.width, root.height) / 2 * 1.3
                radiusY: Math.min(root.width, root.height) / 2 * 1.3
                startAngle: 45
                sweepAngle: -270
            }
        }
    }

    // Max value indicator
    Rectangle {
        id: maxIndicator
        width: Math.min(root.width, root.height) / 2
        height: 4
        color: CommonStyle.statusError
        opacity: 0.6
        antialiasing: true
        
        x: root.width / 2
        y: root.height / 2 - height / 2
        
        transformOrigin: Item.Left
        rotation: 135 + maxAngle
    }

    // Current value indicator
    Rectangle {
        id: dialIndicator
        width: Math.min(root.width, root.height) / 2
        height: 4
        color: CommonStyle.buttonDanger
        antialiasing: true
        
        x: root.width / 2
        y: root.height / 2 - height / 2
        
        transformOrigin: Item.Left
        rotation: 135 + currentAngle
    }

    // Tick marks
    Repeater {
        model: 11

        Rectangle {
            x: root.width / 2 - width / 2
            y: 5
            width: index % 5 === 0 ? 3 : 2
            height: index % 5 === 0 ? 15 : 10
            color: CommonStyle.textPrimary
            
            transform: [
                Translate {
                    y: -20
                },
                Rotation {
                    angle: -135 + (index * 27)
                    origin.x: width / 2
                    origin.y: root.height / 2
                }
            ]
        }
    }

    // Tick labels
    Repeater {
        model: 6
        
        Text {
            x: root.width / 2 - width / 2
            y: 40
            text: (index * 2).toString()
            color: CommonStyle.textPrimary
            font.pixelSize: CommonStyle.fontBody
            
            transform: [
                Translate {
                    y: -40
                },
                Rotation {
                    angle: -135 + (index * 54)
                    origin.x: width / 2
                    origin.y: root.height / 2 - 40
                }
            ]
        }
    }

    // Center display for speed
    Rectangle {
        id: centerDisplay
        width: root.width * 0.45
        height: root.height * 0.2
        radius: Math.min(width, height) * 0.2
        color: Qt.rgba(0, 0, 0, 0.2)
        anchors.centerIn: parent

        Column {
            anchors.centerIn: parent
            spacing: 5

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Math.round(speed).toString() 
                color: CommonStyle.textPrimary
                font.family: CommonStyle.fontMono
                font.pixelSize: Math.min(centerDisplay.width * 1, centerDisplay.height * 1)
                font.bold: true
            }
        }
    }

    // Current torque value display
    Text {
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: 40
        }
        text: "mmps"
        color: CommonStyle.textPrimary
        font.family: CommonStyle.fontSans
        font.pixelSize: Math.min(centerDisplay.width * 0.3, centerDisplay.height * 0.45)
    }

}