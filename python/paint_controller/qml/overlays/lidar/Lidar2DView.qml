import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    
    property bool active: false
    property var pointsData: []
    property string viewPlane: "XY"  // "XY", "XZ", "YZ"
    property real pointSize: 2.0
    property real zoomLevel: 1.0
    property real panX: 0
    property real panY: 0
    
    visible: active
    anchors.fill: parent
    color: "#1a1a1a"
    z: 600
    
    // Main canvas for drawing points
    Canvas {
        id: canvas
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            // Draw background grid
            drawGrid(ctx)
            
            // Draw axes
            drawAxes(ctx)
            
            // Draw points
            drawPoints(ctx)
            
            // Draw info
            drawInfo(ctx)
        }
        
        function drawGrid(ctx) {
            var centerX = width / 2 + panX
            var centerY = height / 2 + panY
            var gridSize = 100 * zoomLevel  // 1 meter = 100 pixels base
            
            ctx.strokeStyle = "#2a2a2a"
            ctx.lineWidth = 1
            
            // Vertical lines
            for (var x = centerX % gridSize; x < width; x += gridSize) {
                ctx.beginPath()
                ctx.moveTo(x, 0)
                ctx.lineTo(x, height)
                ctx.stroke()
            }
            
            // Horizontal lines
            for (var y = centerY % gridSize; y < height; y += gridSize) {
                ctx.beginPath()
                ctx.moveTo(0, y)
                ctx.lineTo(width, y)
                ctx.stroke()
            }
            
            // Center lines (thicker)
            ctx.strokeStyle = "#404040"
            ctx.lineWidth = 2
            
            // Vertical center
            ctx.beginPath()
            ctx.moveTo(centerX, 0)
            ctx.lineTo(centerX, height)
            ctx.stroke()
            
            // Horizontal center
            ctx.beginPath()
            ctx.moveTo(0, centerY)
            ctx.lineTo(width, centerY)
            ctx.stroke()
        }
        
        function drawAxes(ctx) {
            var centerX = width / 2 + panX
            var centerY = height / 2 + panY
            var axisLength = 50
            
            ctx.lineWidth = 3
            
            if (viewPlane === "XY") {
                // X axis (red) - right
                ctx.strokeStyle = "#ff0000"
                ctx.beginPath()
                ctx.moveTo(centerX, centerY)
                ctx.lineTo(centerX + axisLength, centerY)
                ctx.stroke()
                
                // Y axis (green) - up
                ctx.strokeStyle = "#00ff00"
                ctx.beginPath()
                ctx.moveTo(centerX, centerY)
                ctx.lineTo(centerX, centerY - axisLength)
                ctx.stroke()
                
                // Labels
                ctx.fillStyle = "#ff0000"
                ctx.font = "bold 14px monospace"
                ctx.fillText("X", centerX + axisLength + 5, centerY + 5)
                
                ctx.fillStyle = "#00ff00"
                ctx.fillText("Y", centerX + 5, centerY - axisLength - 5)
                
            } else if (viewPlane === "XZ") {
                // X axis (red) - right
                ctx.strokeStyle = "#ff0000"
                ctx.beginPath()
                ctx.moveTo(centerX, centerY)
                ctx.lineTo(centerX + axisLength, centerY)
                ctx.stroke()
                
                // Z axis (blue) - up
                ctx.strokeStyle = "#0000ff"
                ctx.beginPath()
                ctx.moveTo(centerX, centerY)
                ctx.lineTo(centerX, centerY - axisLength)
                ctx.stroke()
                
                // Labels
                ctx.fillStyle = "#ff0000"
                ctx.font = "bold 14px monospace"
                ctx.fillText("X", centerX + axisLength + 5, centerY + 5)
                
                ctx.fillStyle = "#0000ff"
                ctx.fillText("Z", centerX + 5, centerY - axisLength - 5)
                
            } else if (viewPlane === "YZ") {
                // Y axis (green) - right
                ctx.strokeStyle = "#00ff00"
                ctx.beginPath()
                ctx.moveTo(centerX, centerY)
                ctx.lineTo(centerX + axisLength, centerY)
                ctx.stroke()
                
                // Z axis (blue) - up
                ctx.strokeStyle = "#0000ff"
                ctx.beginPath()
                ctx.moveTo(centerX, centerY)
                ctx.lineTo(centerX, centerY - axisLength)
                ctx.stroke()
                
                // Labels
                ctx.fillStyle = "#00ff00"
                ctx.font = "bold 14px monospace"
                ctx.fillText("Y", centerX + axisLength + 5, centerY + 5)
                
                ctx.fillStyle = "#0000ff"
                ctx.fillText("Z", centerX + 5, centerY - axisLength - 5)
            }
        }
        
        function drawPoints(ctx) {
            if (!pointsData || pointsData.length === 0) return
            
            var centerX = width / 2 + panX
            var centerY = height / 2 + panY
            var scale = 100 * zoomLevel  // 1 meter = 100 pixels
            
            var pointCount = 0
            var maxPoints = 10000  // Draw more points in 2D
            
            for (var i = 0; i < pointsData.length && pointCount < maxPoints; i++) {
                var point = pointsData[i]
                var x, y
                
                // Select coordinates based on view plane
                if (viewPlane === "XY") {
                    x = centerX + point.x * scale
                    y = centerY - point.y * scale
                } else if (viewPlane === "XZ") {
                    x = centerX + point.x * scale
                    y = centerY - point.z * scale
                } else if (viewPlane === "YZ") {
                    x = centerX + point.y * scale
                    y = centerY - point.z * scale
                }
                
                // Only draw points within view
                if (x >= -10 && x < width + 10 && y >= -10 && y < height + 10) {
                    // Color based on distance
                    var dist = Math.sqrt(point.x * point.x + point.y * point.y + point.z * point.z)
                    ctx.fillStyle = getPointColor(dist)
                    ctx.fillRect(x - pointSize/2, y - pointSize/2, pointSize, pointSize)
                    pointCount++
                }
            }
        }
        
        function drawInfo(ctx) {
            // Draw scale indicator
            var scaleLength = 100 * zoomLevel
            var scaleX = 20
            var scaleY = height - 40
            
            ctx.strokeStyle = "#ffffff"
            ctx.fillStyle = "#ffffff"
            ctx.lineWidth = 2
            ctx.font = "12px monospace"
            
            ctx.beginPath()
            ctx.moveTo(scaleX, scaleY)
            ctx.lineTo(scaleX + scaleLength, scaleY)
            ctx.stroke()
            
            // Ticks
            ctx.beginPath()
            ctx.moveTo(scaleX, scaleY - 5)
            ctx.lineTo(scaleX, scaleY + 5)
            ctx.moveTo(scaleX + scaleLength, scaleY - 5)
            ctx.lineTo(scaleX + scaleLength, scaleY + 5)
            ctx.stroke()
            
            ctx.fillText("1m", scaleX + scaleLength/2 - 10, scaleY + 20)
        }
        
        function getPointColor(distance) {
            var maxDist = 10.0
            var ratio = Math.min(distance / maxDist, 1.0)
            
            // Rainbow gradient
            if (ratio < 0.2) {
                var t = ratio / 0.2
                var r = Math.floor((0.5 - t * 0.5) * 255)
                var g = 0
                var b = 255
                return "rgb(" + r + "," + g + "," + b + ")"
            } else if (ratio < 0.4) {
                var t = (ratio - 0.2) / 0.2
                var r = 0
                var g = Math.floor(t * 255)
                var b = 255
                return "rgb(" + r + "," + g + "," + b + ")"
            } else if (ratio < 0.6) {
                var t = (ratio - 0.4) / 0.2
                var r = 0
                var g = 255
                var b = Math.floor((1 - t) * 255)
                return "rgb(" + r + "," + g + "," + b + ")"
            } else if (ratio < 0.8) {
                var t = (ratio - 0.6) / 0.2
                var r = Math.floor(t * 255)
                var g = 255
                var b = 0
                return "rgb(" + r + "," + g + "," + b + ")"
            } else {
                var t = (ratio - 0.8) / 0.2
                var r = 255
                var g = Math.floor((1 - t) * 255)
                var b = 0
                return "rgb(" + r + "," + g + "," + b + ")"
            }
        }
    }
    
    // Mouse interaction for pan
    MouseArea {
        anchors.fill: parent
        
        property real lastX: 0
        property real lastY: 0
        property bool dragging: false
        
        onPressed: {
            lastX = mouseX
            lastY = mouseY
            dragging = true
        }
        
        onReleased: {
            dragging = false
        }
        
        onPositionChanged: {
            if (dragging) {
                var dx = mouseX - lastX
                var dy = mouseY - lastY
                
                panX += dx
                panY += dy
                
                lastX = mouseX
                lastY = mouseY
                
                canvas.requestPaint()
            }
        }
        
        onWheel: {
            var delta = wheel.angleDelta.y
            var oldZoom = zoomLevel
            
            if (delta > 0) {
                zoomLevel *= 1.1
            } else {
                zoomLevel *= 0.9
            }
            
            zoomLevel = Math.max(0.1, Math.min(10, zoomLevel))
            canvas.requestPaint()
        }
    }
    
    // Top right controls
    Column {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 10
        spacing: 10
        
        // Info panel
        Rectangle {
            width: 250
            height: infoColumn.height + 20
            color: "#CC1a1a1a"
            border.color: "#404040"
            border.width: 1
            radius: 5
            
            Column {
                id: infoColumn
                anchors.centerIn: parent
                spacing: 5
                
                Text {
                    text: "LiDAR 2D View"
                    color: "#00FF00"
                    font.pixelSize: 16
                    font.bold: true
                }
                
                Text {
                    text: "Points: " + pointsData.length
                    color: "#CCCCCC"
                    font.pixelSize: 13
                }
                
                Text {
                    text: "Plane: " + viewPlane
                    color: "#CCCCCC"
                    font.pixelSize: 13
                }
                
                Text {
                    text: "Zoom: " + zoomLevel.toFixed(1) + "x"
                    color: "#CCCCCC"
                    font.pixelSize: 13
                }
            }
        }
        
        // View plane selector
        Rectangle {
            width: 250
            height: planeColumn.height + 20
            color: "#CC1a1a1a"
            border.color: "#404040"
            border.width: 1
            radius: 5
            
            Column {
                id: planeColumn
                anchors.centerIn: parent
                spacing: 8
                
                Text {
                    text: "View Plane"
                    color: "#888888"
                    font.pixelSize: 12
                    font.bold: true
                }
                
                Row {
                    spacing: 5
                    
                    Button {
                        text: "XY (Top)"
                        width: 80
                        highlighted: viewPlane === "XY"
                        onClicked: {
                            viewPlane = "XY"
                            canvas.requestPaint()
                        }
                    }
                    
                    Button {
                        text: "XZ (Front)"
                        width: 80
                        highlighted: viewPlane === "XZ"
                        onClicked: {
                            viewPlane = "XZ"
                            canvas.requestPaint()
                        }
                    }
                    
                    Button {
                        text: "YZ (Side)"
                        width: 80
                        highlighted: viewPlane === "YZ"
                        onClicked: {
                            viewPlane = "YZ"
                            canvas.requestPaint()
                        }
                    }
                }
            }
        }
        
        // Point size control
        Rectangle {
            width: 250
            height: sizeColumn.height + 20
            color: "#CC1a1a1a"
            border.color: "#404040"
            border.width: 1
            radius: 5
            
            Column {
                id: sizeColumn
                anchors.centerIn: parent
                spacing: 8
                
                Text {
                    text: "Point Size"
                    color: "#888888"
                    font.pixelSize: 12
                    font.bold: true
                }
                
                Row {
                    spacing: 5
                    
                    Button {
                        text: "-"
                        width: 40
                        onClicked: {
                            pointSize = Math.max(1, pointSize - 0.5)
                            canvas.requestPaint()
                        }
                    }
                    
                    Text {
                        text: pointSize.toFixed(1) + "px"
                        color: "#CCCCCC"
                        font.pixelSize: 13
                        width: 50
                        horizontalAlignment: Text.AlignHCenter
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Button {
                        text: "+"
                        width: 40
                        onClicked: {
                            pointSize = Math.min(10, pointSize + 0.5)
                            canvas.requestPaint()
                        }
                    }
                }
            }
        }
    }
    
    // Bottom controls
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: 20
        width: controlRow.width + 20
        height: controlRow.height + 20
        color: "#CC1a1a1a"
        border.color: "#404040"
        border.width: 1
        radius: 5
        
        Row {
            id: controlRow
            anchors.centerIn: parent
            spacing: 10
            
            Button {
                text: "Reset View"
                width: 100
                onClicked: {
                    zoomLevel = 1.0
                    panX = 0
                    panY = 0
                    canvas.requestPaint()
                }
            }
            
            Rectangle {
                width: 2
                height: 30
                color: "#404040"
            }
            
            Button {
                text: "Close [A]"
                width: 100
                onClicked: {
                    root.active = false
                }
            }
        }
    }
    
    // Redraw when visibility changes
    onActiveChanged: {
        if (active) {
            canvas.requestPaint()
        }
    }
    
    // Instructions overlay
    Text {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.margins: 20
        text: "Drag to Pan | Wheel to Zoom"
        color: "#888888"
        font.pixelSize: 12
    }
    
    // Smooth fade in/out
    Behavior on opacity {
        NumberAnimation { duration: 300 }
    }
    
    opacity: active ? 1.0 : 0.0
}
