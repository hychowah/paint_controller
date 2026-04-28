import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: overlay
    required property var lidarStatus
    
    // *** You can now change width and height here to scale the whole UI ***
    width: 250
    height: 120
    
    // This scaleFactor drives all internal sizing
    property real scaleFactor: height / 160.0 
    
    // Background opacity as percentage (0-100)
    property real backgroundOpacity: 40
    
    // Track last LIDAR message timestamp
    property var lastLidarUpdateTime: new Date()
    property real messageTimeoutMs: 1000  // 1 second timeout
    property bool isLidarActive: false
    readonly property real lidarDistance: (lidarStatus && typeof lidarStatus.distance === "number") ? lidarStatus.distance : 0.0
    readonly property real lidarAngle: (lidarStatus && typeof lidarStatus.angle === "number") ? lidarStatus.angle : 0.0
    
    // Update timestamp when distance changes
    Connections {
        target: overlay.lidarStatus

        function onChanged() {
            overlay.lastLidarUpdateTime = new Date()
            overlay.isLidarActive = true
        }
    }
    
    // Timer to check if message timeout has occurred
    Timer {
        id: lidarTimeoutTimer
        interval: 500  // Check every 500ms
        running: true
        repeat: true
        
        onTriggered: {
            var now = new Date()
            overlay.isLidarActive = (now.getTime() - overlay.lastLidarUpdateTime.getTime()) < overlay.messageTimeoutMs
        }
    }
    
    anchors.bottom: parent.bottom
    anchors.bottomMargin: 5
    anchors.horizontalCenter: parent.horizontalCenter
    
    color: Qt.rgba(0, 0, 0, backgroundOpacity / 100)
    radius: 8 * scaleFactor
    // border.width: 2
    // border.color: "#00FF00"
    
    // Using RowLayout for better proportional scaling
    RowLayout {
        anchors.fill: parent
        anchors.margins: 10 * scaleFactor
        spacing: 10 * scaleFactor
        
        // LEFT SIDE - Visual Diagram
        Rectangle {
            // Use Layout properties for sizing
            Layout.fillWidth: true
            Layout.preferredWidth: 120 * scaleFactor
            Layout.fillHeight: true
            color: "transparent"
            
            // Title at top
            Text {
                text: "WALL DETECTION"
                color: "#00FF00"
                font.pixelSize: 11 * scaleFactor // Scaled
                font.bold: true
                font.letterSpacing: 1.0
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
            }
            
            // Visual representation area
            Canvas {
                id: wallCanvas
                anchors.top: parent.top
                anchors.topMargin: 22 * scaleFactor // Scaled
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                
                property real distance: Math.min(overlay.lidarDistance, 2.0)
                property real angle: overlay.lidarAngle
                
                onDistanceChanged: requestPaint()
                onAngleChanged: requestPaint()
                
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    
                    // --- Setup ---
                    var sF = overlay.scaleFactor 
                    var centerX = width * 0.5
                    var centerY = height * 0.75 // Fixed position for the end effector
                    var scale = 40 * sF
                    var angleRad = (angle * Math.PI) / 180

                    // --- 1. Draw End Effector (Static) ---
                    // Green dot
                    ctx.fillStyle = "#00FF00"
                    ctx.beginPath()
                    ctx.arc(centerX, centerY, 6 * sF, 0, 2 * Math.PI) 
                    ctx.fill()
                    
                    // Horizontal reference line
                    ctx.strokeStyle = "#666666"
                    ctx.lineWidth = Math.max(1, 1 * sF) 
                    ctx.setLineDash([3, 3])
                    ctx.beginPath()
                    ctx.moveTo(centerX - (30 * sF), centerY) 
                    ctx.lineTo(centerX + (30 * sF), centerY) 
                    ctx.stroke()
                    ctx.setLineDash([])

                    // --- 2. Draw "Forward" Perpendicular Vector (Green Line) ---
                    // This line represents the "DISTANCE" value (1.07 m)
                    var perpY = centerY - (distance * scale)
                    ctx.strokeStyle = "#00FF00"
                    ctx.lineWidth = 2 * sF 
                    ctx.beginPath()
                    ctx.moveTo(centerX, centerY)
                    ctx.lineTo(centerX, perpY)
                    ctx.stroke()

                    // --- 3. Draw Actual Sensor Vector (Thin Orange Line) ---
                    // This shows the "ANGLE DEVIATION"
                    // Calculate hypotenuse length based on perpendicular distance
                    var actualDistance = distance / Math.cos(angleRad)
                    var endX = centerX + (actualDistance * scale * Math.sin(angleRad))
                    var endY = centerY - (actualDistance * scale * Math.cos(angleRad))
                    
                    ctx.strokeStyle = "#FFAA00"
                    ctx.lineWidth = 2 * sF 
                    ctx.beginPath()
                    ctx.moveTo(centerX, centerY)
                    ctx.lineTo(endX, endY)
                    ctx.stroke()

                    // --- 4. Draw the Wall (Thick Orange Line) ---
                    // The wall is at the end of the *actual* sensor vector (endX, endY)
                    // and rotated by the same angle.
                    ctx.save() // Save the current canvas state
                    ctx.translate(endX, endY) // Move the origin to the wall's center
                    ctx.rotate(angleRad)      // Rotate the canvas to the wall's angle
                    
                    ctx.strokeStyle = "#FF6600"
                    ctx.lineWidth = 3 * sF 
                    ctx.beginPath()
                    // Draw the line centered on the new (0,0) origin
                    ctx.moveTo(-width * 0.4, 0) 
                    ctx.lineTo(width * 0.4, 0)
                    ctx.stroke()
                    
                    ctx.restore() // Restore the canvas to its original state
                }
            }
        }
        
        // Divider
        Rectangle {
            Layout.preferredWidth: 2 // Keep divider thin
            Layout.fillHeight: true
            color: "#333333"
        }
        
        // RIGHT SIDE - Numerical Values & Status
        ColumnLayout {
            Layout.fillWidth: true
            Layout.preferredWidth: 140 * scaleFactor
            Layout.fillHeight: true
            spacing: 8 * scaleFactor // Scaled
            
            // Distance display
            Column {
                Layout.fillWidth: true
                spacing: 4 * scaleFactor // Scaled
                
                Text {
                    text: "DISTANCE"
                    color: "#00FF00"
                    font.pixelSize: 10 * scaleFactor // Scaled
                    font.bold: true
                    font.letterSpacing: 0.5
                }
                
                Rectangle {
                    width: parent.width
                    height: 30 * scaleFactor // Scaled
                    color: "#1A1A1A"
                    radius: 4 * scaleFactor // Scaled
                    border.width: 1
                    border.color: "#00FF00"
                    
                    Text {
                        anchors.centerIn: parent
                        text: overlay.lidarDistance.toFixed(2) + " m"
                        color: "#00FF00"
                        font.pixelSize: 20 * scaleFactor // Scaled
                        font.bold: true
                        font.family: "Courier New"
                    }
                }
            }
            
            // Angle display
            Column {
                Layout.fillWidth: true
                spacing: 4 * scaleFactor // Scaled
                
                Text {
                    text: "ANGLE DEVIATION"
                    color: "#FFAA00"
                    font.pixelSize: 10 * scaleFactor // Scaled
                    font.bold: true
                    font.letterSpacing: 0.5
                }
                
                Rectangle {
                    width: parent.width
                    height: 30 * scaleFactor // Scaled
                    color: "#1A1A1A"
                    radius: 4 * scaleFactor // Scaled
                    border.width: 1
                    border.color: Math.abs(overlay.lidarAngle) > 5 ? "#FF6600" : "#FFAA00"
                    
                    Text {
                        anchors.centerIn: parent
                        text: (overlay.lidarAngle > 0 ? "+" : "") + overlay.lidarAngle.toFixed(1) + "°"
                        color: Math.abs(overlay.lidarAngle) > 5 ? "#FF6600" : "#FFAA00"
                        font.pixelSize: 20 * scaleFactor // Scaled
                        font.bold: true
                        font.family: "Courier New"
                    }
                }
            }
            
            // Status indicator
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 25 * scaleFactor // Scaled
                color: "transparent"
                
                Rectangle {
                    width: 8 * scaleFactor // Scaled
                    height: 8 * scaleFactor // Scaled
                    radius: 4 * scaleFactor // Scaled
                    color: overlay.isLidarActive ? "#00FF00" : "#FF3333"
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    
                    NumberAnimation on opacity {
                        running: overlay.isLidarActive
                        from: 1.0
                        to: 0.4
                        duration: 600
                        loops: Animation.Infinite
                    }
                }
                
                Text {
                    text: overlay.isLidarActive ? "ACTIVE" : "NO SIGNAL"
                    color: overlay.isLidarActive ? "#00FF00" : "#FF3333"
                    font.pixelSize: 10 * scaleFactor // Scaled
                    font.bold: true
                    anchors.left: parent.left
                    anchors.leftMargin: 14 * scaleFactor // Scaled
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}