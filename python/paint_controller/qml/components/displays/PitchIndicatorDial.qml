import QtQuick 2.15
import QtQuick.Shapes 1.15

Item {
    id: root
    width: 180
    height: 85
    
    // --- ADJUSTABLE DIAL PROPERTIES ---
    // The measurement range (e.g., 10.0 = ±10°)
    property real dialRange: 10.0
    // The visual angle of the arc (e.g., 60.0 = ±60° on screen)
    property real dialVisualAngle: 60.0
    // ------------------------------------

    // Property for pitch data binding
    property real currentPitch: 0.0
    
    // Opacity for the background, 0.0 (fully transparent) to 1.0 (fully opaque)
    property real backgroundOpacity: 0.6
    
    // Calculate needle angle - pitch centered at 0°
    property real clampedPitch: Math.max(-dialRange, Math.min(dialRange, currentPitch))
    property real needleAngle: (clampedPitch / dialRange) * -dialVisualAngle
    
    Rectangle {
        id: dialBackground
        anchors.fill: parent
        color: "#000000"
        opacity: root.backgroundOpacity
        radius: 8
        border.width: 0
        
        property real centerX: width / 2
        property real centerY: height - 10
        property real dialRadius: 55
        
        // Background dial arc
        Shape {
            anchors.fill: parent
            
            ShapePath {
                strokeWidth: 3
                strokeColor: "#555555"
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                
                PathAngleArc {
                    centerX: dialBackground.centerX
                    centerY: dialBackground.centerY
                    radiusX: dialBackground.dialRadius
                    radiusY: dialBackground.dialRadius
                    startAngle: 270 - root.dialVisualAngle
                    sweepAngle: root.dialVisualAngle * 2
                }
            }
        }
        
        // Tick marks and labels
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                var centerX = dialBackground.centerX
                var centerY = dialBackground.centerY
                var radius = dialBackground.dialRadius
                
                ctx.strokeStyle = "#CCCCCC"
                ctx.fillStyle = "#FFFFFF"
                ctx.font = "10px Arial"
                ctx.textAlign = "center"
                ctx.textBaseline = "middle"
                
                // Tick marks: [-10, -5, 0, 5, 10]
                var marks = [
                    -root.dialRange, 
                    -root.dialRange / 2.0, 
                    0, 
                    root.dialRange / 2.0, 
                    root.dialRange
                ]
                
                marks.forEach(function(deg) {
                    var visualAngleDegrees = (deg / root.dialRange) * -root.dialVisualAngle
                    var angle = (270 + visualAngleDegrees) * Math.PI / 180
                    
                    var outerX = centerX + Math.cos(angle) * (radius + 8)
                    var outerY = centerY + Math.sin(angle) * (radius + 8)
                    var innerX = centerX + Math.cos(angle) * radius
                    var innerY = centerY + Math.sin(angle) * radius
                    
                    ctx.beginPath()
                    ctx.moveTo(innerX, innerY)
                    ctx.lineTo(outerX, outerY)
                    ctx.lineWidth = 1
                    ctx.stroke()
                    
                    // Label only the extreme values and center
                    if (deg === -root.dialRange || deg === 0 || deg === root.dialRange) {
                        var labelX = centerX + Math.cos(angle) * (radius + 18)
                        var labelY = centerY + Math.sin(angle) * (radius + 18)
                        
                        var label = deg.toFixed(0) + "°"
                        if (deg > 0) {
                            label = "+" + label
                        }
                        ctx.fillText(label, labelX, labelY)
                    }
                })
            }
        }
        
        // Center hub
        Rectangle {
            x: dialBackground.centerX - 6
            y: dialBackground.centerY - 6
            width: 12
            height: 12
            radius: 6
            color: "#CCCCCC"
            border.color: "#999999"
            border.width: 1
            z: 2
        }
        
        // Needle indicator (red)
        Item {
            x: dialBackground.centerX
            y: dialBackground.centerY
            z: 1
            
            transform: Rotation {
                origin.x: 0
                origin.y: 0
                angle: root.needleAngle
                
                Behavior on angle {
                    NumberAnimation { duration: 200 }
                }
            }
            
            Rectangle {
                x: -1.5
                y: - (dialBackground.dialRadius - 10)
                width: 3
                height: (dialBackground.dialRadius - 10) + 5
                radius: 1.5
                color: "#FF3333"
            }
        }
        
        // PITCH label
        Text {
            id: pitchLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 5
            text: "PITCH"
            color: "#CCCCCC"
            font.pixelSize: 9
            font.bold: true
        }
        
        // Current pitch display
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: pitchLabel.bottom
            anchors.topMargin: 30
            text: root.currentPitch.toFixed(1) + "°"
            color: "#FFFFFF"
            font.pixelSize: 11
            font.bold: true
            z: 2
        }
    }
}
