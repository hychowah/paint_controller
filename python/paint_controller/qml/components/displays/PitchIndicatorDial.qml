import QtQuick
import QtQuick.Shapes
import "../../theme"

Item {
    id: root
    width: 180
    height: 120
    
    required property real currentPitch
    
    // Opacity for sky/ground fill only (labels & aircraft ref stay solid)
    property real backgroundOpacity: 0.45
    
    // Pitch range (±10 degrees)
    property real pitchRange: 10.0
    
    // Pitch scale factor (pixels per degree)
    property real pitchScale: 4.5
    readonly property string pitchText: (root.currentPitch >= 0 ? "+" : "") + root.currentPitch.toFixed(1) + "°"

    // ADI-style sky / ground (above / below 0°) — solid base; alpha via opacity
    readonly property color skyColor: "#3a7ebd"
    readonly property color groundColor: "#8b5a2b"
    
    Rectangle {
        id: container
        anchors.fill: parent
        color: "transparent"
        radius: CommonStyle.radiusSm
        border.width: 0
        clip: true
        
        // Moving pitch ladder (moves opposite to pitch)
        Item {
            id: pitchLadder
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            height: parent.height * 3
            
            // Center ladder vertically, offset by pitch angle
            y: parent.height / 2 - height / 2 - root.currentPitch * root.pitchScale
            
            Behavior on y {
                NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
            }

            // Sky band — above 0° horizon (top half of ladder)
            Rectangle {
                id: skyBand
                anchors.left: parent.left
                anchors.right: parent.right
                y: 0
                height: parent.height / 2
                color: root.skyColor
                opacity: root.backgroundOpacity
            }

            // Ground band — below 0° horizon (bottom half of ladder)
            Rectangle {
                id: groundBand
                anchors.left: parent.left
                anchors.right: parent.right
                y: parent.height / 2
                height: parent.height / 2
                color: root.groundColor
                opacity: root.backgroundOpacity
            }
            
            // Center horizon line
            Rectangle {
                id: horizonLine
                anchors.horizontalCenter: parent.horizontalCenter
                y: parent.height / 2 - 1.5
                width: parent.width * 0.85
                height: 3
                color: CommonStyle.textPrimary
                radius: 1.5
                z: 2
            }
            
            // Pitch ladder marks
            Canvas {
                id: pitchMarks
                anchors.fill: parent
                z: 2
                
                Component.onCompleted: requestPaint()
                
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    
                    var centerX = width / 2
                    var centerY = height / 2
                    
                    // Light ticks/labels for contrast on both sky and ground
                    ctx.strokeStyle = "#f4f7fb"
                    ctx.fillStyle = "#f4f7fb"
                    ctx.font = "11px Arial"
                    ctx.textAlign = "center"
                    ctx.textBaseline = "middle"
                    ctx.lineWidth = 2
                    ctx.globalAlpha = 0.9
                    
                    // Draw pitch lines every 2.5 degrees from -pitchRange to +pitchRange
                    for (var pitch = -root.pitchRange; pitch <= root.pitchRange; pitch += 2.5) {
                        if (pitch === 0) continue // Skip horizon line
                        
                        var y = centerY + pitch * root.pitchScale
                        var lineWidth = (pitch % 5 === 0) ? 50 : 30
                        
                        // Pitch line
                        ctx.beginPath()
                        ctx.moveTo(centerX - lineWidth / 2, y)
                        ctx.lineTo(centerX + lineWidth / 2, y)
                        ctx.stroke()
                        
                        // Labels for 5-degree intervals
                        if (pitch % 5 === 0) {
                            var label = Math.abs(pitch).toString()
                            ctx.fillText(label, centerX - lineWidth / 2 - 12, y)
                            ctx.fillText(label, centerX + lineWidth / 2 + 12, y)
                        }
                    }
                }
            }
        }
        
        // Fixed center reference indicator
        Item {
            id: centerReference
            anchors.centerIn: parent
            width: parent.width
            height: 30
            z: 10
            
            // Left reference line
            Rectangle {
                x: parent.width / 2 - 50
                y: parent.height / 2 - 1.5
                width: 40
                height: 3
                color: CommonStyle.statusWarning
                radius: 1.5
            }
            
            // Right reference line
            Rectangle {
                x: parent.width / 2 + 10
                y: parent.height / 2 - 1.5
                width: 40
                height: 3
                color: CommonStyle.statusWarning
                radius: 1.5
            }
            
            // Center dot
            Rectangle {
                anchors.centerIn: parent
                width: 6
                height: 6
                radius: 3
                color: CommonStyle.statusWarning
                border.color: CommonStyle.backgroundL0
                border.width: 1
            }
        }
        
        // PITCH label at top
        Text {
            id: pitchLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 5
            text: "PITCH"
            color: CommonStyle.textSecondary
            font.pixelSize: CommonStyle.fontLabel - 2
            font.bold: true
            z: 11
        }
        
        // Digital pitch readout
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: pitchLabel.bottom
            anchors.topMargin: 25
            text: root.pitchText
            color: CommonStyle.textPrimary
            font.pixelSize: CommonStyle.fontLabel
            font.bold: true
            font.family: CommonStyle.fontMono
            z: 11
        }
    }
}
