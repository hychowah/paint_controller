import QtQuick
import QtQuick.Shapes
import "../../core"

Item {
    id: root
    width: 180
    height: 85
    
    // --- ADJUSTABLE DIAL PROPERTIES ---
    // The measurement range (e.g., 5.0 = ±5°)
    property real dialRange: 10.0
    // The visual angle of the arc (e.g., 75.0 = ±75° on screen)
    property real dialVisualAngle: 60.0
    // ------------------------------------

    // Properties for yaw data binding
    property real currentYaw: 94.7
    property real targetYaw: 103.0
    
    // Opacity for the background, 0.0 (fully transparent) to 1.0 (fully opaque)
    property real backgroundOpacity: 0.6
    
    // Calculate the yaw offset from target (in degrees)
    property real yawOffset: {
        var offset = currentYaw - targetYaw
        while (offset > 180) offset -= 360
        while (offset < -180) offset += 360
        return offset
    }
    
    // Calculate needle angle
    // Updated to use properties
    property real clampedOffset: Math.max(-dialRange, Math.min(dialRange, yawOffset))
    property real needleAngle: (clampedOffset / dialRange) * -dialVisualAngle
    
    Rectangle {
        id: dialBackground
        anchors.fill: parent
        color: CommonStyle.backgroundL0
        opacity: root.backgroundOpacity
        radius: CommonStyle.radiusSm
        border.width: 0
        
        property real centerX: width / 2
        property real centerY: height - 10
        property real dialRadius: 55
        
        // Background dial arc
        Shape {
            anchors.fill: parent
            
            ShapePath {
                strokeWidth: 3
                strokeColor: CommonStyle.cardBorder
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                
                PathAngleArc {
                    centerX: dialBackground.centerX
                    centerY: dialBackground.centerY
                    radiusX: dialBackground.dialRadius
                    radiusY: dialBackground.dialRadius
                    // Updated to use properties
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
                
                ctx.strokeStyle = CommonStyle.textSecondary
                ctx.fillStyle = CommonStyle.textPrimary
                ctx.font = "10px Arial"
                ctx.textAlign = "center"
                ctx.textBaseline = "middle"
                
                // Updated to use properties: [-5, -2.5, 0, 2.5, 5]
                var marks = [
                    -root.dialRange, 
                    -root.dialRange / 2.0, 
                    0, 
                    root.dialRange / 2.0, 
                    root.dialRange
                ]
                
                marks.forEach(function(deg) {
                    // Updated to use properties
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
                    
                    // Updated to use properties
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
            color: CommonStyle.textSecondary
            border.color: CommonStyle.textDisabled
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
                color: CommonStyle.statusError
            }
        }
        
        // YAW label
        Text {
            id: yawLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 5
            text: "YAW"
            color: CommonStyle.textSecondary
            font.pixelSize: CommonStyle.fontLabel - 2
            font.bold: true
        }
        
        // Current/Target yaw display
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: yawLabel.bottom
            anchors.topMargin: 30
            text: root.currentYaw.toFixed(1) + "° / " + root.targetYaw.toFixed(1) + "°"
            color: CommonStyle.textPrimary
            font.pixelSize: CommonStyle.fontLabel
            font.family: CommonStyle.fontMono
            font.bold: true
            z: 2
        }
    }
}