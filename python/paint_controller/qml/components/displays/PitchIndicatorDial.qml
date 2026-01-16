import QtQuick 2.15
import QtQuick.Shapes 1.15

Item {
    id: root
    width: 180
    height: 180
    
    // Property for pitch data binding
    property real currentPitch: 0.0
    
    // Opacity for the background, 0.0 (fully transparent) to 1.0 (fully opaque)
    property real backgroundOpacity: 0.8
    
    // Pitch scale factor (pixels per degree)
    property real pitchScale: 3.5
    
    Rectangle {
        id: container
        anchors.fill: parent
        color: "#000000"
        opacity: root.backgroundOpacity
        radius: 8
        border.width: 2
        border.color: "#333333"
        clip: true
        
        // Circular mask for the attitude indicator
        Rectangle {
            id: attitudeCircle
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height) - 20
            height: width
            radius: width / 2
            clip: true
            color: "transparent"
            
            // Moving pitch ladder (moves opposite to pitch)
            Item {
                id: pitchLadder
                anchors.centerIn: parent
                width: parent.width
                height: parent.height * 4
                
                // Vertical offset based on pitch
                y: root.currentPitch * root.pitchScale
                
                Behavior on y {
                    NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                }
                
                // Sky (blue background)
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 0
                    width: parent.width
                    height: parent.height / 2
                    color: "#4A90E2"
                }
                
                // Ground (brown background)
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: parent.height / 2
                    width: parent.width
                    height: parent.height / 2
                    color: "#8B6F47"
                }
                
                // Horizon line
                Rectangle {
                    id: horizonLine
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: parent.height / 2 - 2
                    width: parent.width
                    height: 4
                    color: "#FFFFFF"
                }
                
                // Pitch ladder marks
                Canvas {
                    id: pitchMarks
                    anchors.fill: parent
                    
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        
                        var centerX = width / 2
                        var centerY = height / 2
                        
                        ctx.strokeStyle = "#FFFFFF"
                        ctx.fillStyle = "#FFFFFF"
                        ctx.font = "bold 11px Arial"
                        ctx.textAlign = "center"
                        ctx.textBaseline = "middle"
                        ctx.lineWidth = 2
                        
                        // Draw pitch lines every 5 degrees from -30 to +30
                        for (var pitch = -30; pitch <= 30; pitch += 5) {
                            if (pitch === 0) continue // Skip horizon line
                            
                            var y = centerY - pitch * root.pitchScale
                            var lineWidth = (pitch % 10 === 0) ? 60 : 40
                            
                            // Pitch line
                            ctx.beginPath()
                            ctx.moveTo(centerX - lineWidth / 2, y)
                            ctx.lineTo(centerX + lineWidth / 2, y)
                            ctx.stroke()
                            
                            // Labels for 10-degree intervals
                            if (pitch % 10 === 0) {
                                var label = Math.abs(pitch).toString()
                                ctx.fillText(label, centerX - lineWidth / 2 - 15, y)
                                ctx.fillText(label, centerX + lineWidth / 2 + 15, y)
                            }
                        }
                    }
                }
            }
            
            // Fixed aircraft symbol (center reference)
            Item {
                id: aircraftSymbol
                anchors.centerIn: parent
                width: parent.width
                height: 40
                z: 10
                
                // Left wing
                Rectangle {
                    x: parent.width / 2 - 60
                    y: parent.height / 2 - 2
                    width: 50
                    height: 4
                    color: "#FFAA00"
                    radius: 2
                }
                
                // Right wing
                Rectangle {
                    x: parent.width / 2 + 10
                    y: parent.height / 2 - 2
                    width: 50
                    height: 4
                    color: "#FFAA00"
                    radius: 2
                }
                
                // Center fuselage
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: parent.height / 2 - 2
                    width: 8
                    height: 4
                    color: "#FFAA00"
                }
                
                // Center dot
                Rectangle {
                    anchors.centerIn: parent
                    width: 8
                    height: 8
                    radius: 4
                    color: "#FFAA00"
                    border.color: "#000000"
                    border.width: 1
                }
            }
        }
        
        // PITCH label at top
        Text {
            id: pitchLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 5
            text: "PITCH"
            color: "#FFFFFF"
            font.pixelSize: 10
            font.bold: true
            z: 11
        }
        
        // Digital pitch readout at bottom
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 5
            width: 60
            height: 20
            color: "#000000"
            border.color: "#666666"
            border.width: 1
            radius: 3
            z: 11
            
            Text {
                anchors.centerIn: parent
                text: (root.currentPitch >= 0 ? "+" : "") + root.currentPitch.toFixed(1) + "°"
                color: "#00FF00"
                font.pixelSize: 11
                font.bold: true
                font.family: "Courier New"
            }
        }
    }
}
