import QtQuick
import "../../core"

Canvas {
    id: canvas
    property var dataPoints: []
    property int maxDataPoints: 50  // Adjust this to change the number of points shown
    property real minValue: -40  // Set to the minimum expected RPM
    property real maxValue: 40   // Set to the maximum expected RPM
    property real midLine: 0     // The middle line (0 RPM in this case)
    property real maxAbsValue: 40 // Default max absolute value
    property color lineColor: CommonStyle.accentPrimary
    
    function updateMinMaxValues() {
        if (dataPoints.length > 0) {
            minValue = -maxAbsValue
            maxValue = maxAbsValue
        } else {
            minValue = -maxAbsValue
            maxValue = maxAbsValue
        }
        requestPaint()
    }

    onPaint: {
        var ctx = getContext("2d");
        ctx.reset();

        var w = width;
        var h = height;
        var step = w / (maxDataPoints - 1);

        // Draw the middle line
        ctx.strokeStyle = CommonStyle.textDisabled;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, h/2);
        ctx.lineTo(w, h/2);
        ctx.stroke();

        if (dataPoints.length < 2) return;

        // Draw the data line
        ctx.strokeStyle = lineColor;  // Blue color for the line
        ctx.lineWidth = 2;

        ctx.beginPath();
        for (var i = 0; i < dataPoints.length; i++) {
            var x = i * step;
            var y = h - (dataPoints[i] - minValue) / (maxValue - minValue) * h;
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    }

    function addDataPoint(value) {
        value = Math.max(-maxAbsValue * 0.95, Math.min(maxAbsValue * 0.95, value));
        dataPoints.push(value);
        if (dataPoints.length > maxDataPoints) {
            dataPoints.shift();
        }
        updateMinMaxValues();
    }
}