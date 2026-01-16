import QtQuick 2.15
import QtQuick.Shapes 1.15

Item {
    id: root
    width: 180
    height: 120
    
    // Property for pitch data binding
    property real currentPitch: 0.0
    
    // Opacity for the background, 0.0 (fully transparent) to 1.0 (fully opaque)
    property real backgroundOpacity: 0.6
    
    // Pitch range (±10 degrees)
    property real pitchRange: 10.0
    
    // Pitch scale factor (pixels per degree)
    property real pitchScale: 4.5
    
    Rectangle {
        id: container
        anchors.fill: parent
        color: "#000000"
        opacity: root.backgroundOpacity
        radius: 8
        border.width: 0
        clip: true
        
        // Moving pitch ladder (moves opposite to pitch)
        Item {
            id: pitchLadder
            x: parent.width / 2 - width / 2
            width: parent.width
            height: parent.height * 3
            
            // Vertical offset based on pitch (inverted - positive pitch moves horizon down)
            // Position vertically so that center of ladder aligns with center of container at pitch=0
            y: parent.height / 2 - height / 2 - root.currentPitch * root.pitchScale
            
            Behavior on y {
                NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
            }
            
            // Center horizon line
            Rectangle {
                id: horizonLine
                anchors.horizontalCenter: parent.horizontalCenter
                y: parent.height / 2 - 1.5
                width: parent.width * 0.5
                height: 3
                color: "#FFFFFF"
                radius: 1.5
            }
            
            // Pitch ladder marks
            Canvas {
                id: pitchMarks
                anchors.fill: parent
                
                Component.onCompleted: requestPaint()
                
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    
                    var centerX = width / 2
                    var centerY = height / 2
                    
                    ctx.strokeStyle = "#CCCCCC"
                    ctx.fillStyle = "#FFFFFF"
                    ctx.font = "11px Arial"
                    ctx.textAlign = "center"
                    ctx.textBaseline = "middle"
                    ctx.lineWidth = 2
                    
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
                color: "#FFAA00"
                radius: 1.5
            }
            
            // Right reference line
            Rectangle {
                x: parent.width / 2 + 10
                y: parent.height / 2 - 1.5
                width: 40
                height: 3
                color: "#FFAA00"
                radius: 1.5
            }
            
            // Center dot
            Rectangle {
                anchors.centerIn: parent
                width: 6
                height: 6
                radius: 3
                color: "#FFAA00"
                border.color: "#000000"
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
            color: "#CCCCCC"
            font.pixelSize: 9
            font.bold: true
            z: 11
        }
        
        // Digital pitch readout
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: pitchLabel.bottom
            anchors.topMargin: 25
            text: (root.currentPitch >= 0 ? "+" : "") + root.currentPitch.toFixed(1) + "°"
            color: "#FFFFFF"
            font.pixelSize: 11
            font.bold: true
            font.family: "Courier New"
            z: 11
        }
    }
}
