import QtQuick 2.15

Canvas {
    id: canvas
    anchors.fill: parent

    property var points: []
    property real scale: 1.0
    property color pointColor: "red"

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()

        // Clear the canvas
        ctx.clearRect(0, 0, width, height)

        // Set up the coordinate system
        ctx.save()
        ctx.translate(width / 2, height / 2)
        ctx.scale(scale, -scale)  // Flip Y-axis to make positive Y go up

        // Draw points
        ctx.fillStyle = pointColor
        for (var i = 0; i < points.length; i++) {
            var point = points[i]
            ctx.beginPath()
            ctx.arc(point.x, point.y, 2 / scale, 0, 2 * Math.PI)
            ctx.fill()
        }

        ctx.restore()
    }

    function updatePoints(newPoints) {
        points = newPoints
        requestPaint()
    }

    function updateScale(newScale) {
        scale = newScale
        requestPaint()
    }
}