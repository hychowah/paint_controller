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
    
    // Cached min/max values for performance
    property real cachedMin: minValue
    property real cachedMax: maxValue
    
    // Update cached min/max when dataPoints change
    onDataPointsChanged: {
        if (dataPoints.length > 0) {
            cachedMin = dataPoints[0]
            cachedMax = dataPoints[0]
            for (var i = 1; i < dataPoints.length; i++) {
                if (dataPoints[i] < cachedMin) cachedMin = dataPoints[i]
                if (dataPoints[i] > cachedMax) cachedMax = dataPoints[i]
            }
        } else {
            cachedMin = minValue
            cachedMax = maxValue
        }
        requestPaint()
    }
    
    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)
        
        if (dataPoints.length < 2) return
        
        var range = cachedMax - cachedMin
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
            var y = height - ((value - cachedMin) / range) * height
            
            if (i === 0) {
                ctx.moveTo(x, y)
            } else {
                ctx.lineTo(x, y)
            }
        }
        
        ctx.stroke()
    }
}
