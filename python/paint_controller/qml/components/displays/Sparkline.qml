// Mini line graph for showing trends (e.g., IMU data)
import QtQuick 2.15

Canvas {
    id: canvas
    
    // Properties
    property var dataPoints: []
    property int maxDataPoints: 10
    property color lineColor: "#3498db"
    property real lineWidth: 2
    property real minValue: -10
    property real maxValue: 10
    
    width: 40
    height: 20
    
    // Auto-scale based on data if not explicitly set
    property real autoMin: dataPoints.length > 0 ? Math.min(...dataPoints) : minValue
    property real autoMax: dataPoints.length > 0 ? Math.max(...dataPoints) : maxValue
    
    onDataPointsChanged: requestPaint()
    
    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        
        if (dataPoints.length < 2) return
        
        var range = autoMax - autoMin
        if (range === 0) range = 1
        
        ctx.strokeStyle = lineColor
        ctx.lineWidth = lineWidth
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        
        ctx.beginPath()
        
        var step = width / (maxDataPoints - 1)
        var startIndex = Math.max(0, dataPoints.length - maxDataPoints)
        
        for (var i = 0; i < Math.min(dataPoints.length, maxDataPoints); i++) {
            var dataIndex = startIndex + i
            var value = dataPoints[dataIndex]
            var x = i * step
            var y = height - ((value - autoMin) / range) * height
            
            if (i === 0) {
                ctx.moveTo(x, y)
            } else {
                ctx.lineTo(x, y)
            }
        }
        
        ctx.stroke()
    }
}
