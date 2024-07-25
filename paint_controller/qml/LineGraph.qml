import QtQuick 2.15

Canvas {
    id: canvas
    property var dataPoints: []
    property int maxDataPoints: 50
    property real minValue: 0
    property real maxValue: 0
    property real midLine: 0

    function updateMinMaxValues() {
        if (dataPoints.length > 0) {
            minValue = Math.min(...dataPoints)
            maxValue = Math.max(...dataPoints)
            // Add a small buffer to min and max for better visualization
            var range = maxValue - minValue
            minValue -= range * 0.1
            maxValue += range * 0.1
        } else {
            minValue = -40
            maxValue = 40
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
        ctx.strokeStyle = "#888888";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, h/2);
        ctx.lineTo(w, h/2);
        ctx.stroke();

        if (dataPoints.length < 2) return;

        // Draw the data line
        ctx.strokeStyle = "#4374A2";
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
        dataPoints.push(value);
        if (dataPoints.length > maxDataPoints) {
            dataPoints.shift();
        }
        updateMinMaxValues();
    }
}