import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    
    property bool active: false
    
    visible: active
    anchors.fill: parent
    color: "#AA000000"  // Semi-transparent black background
    z: 600  // Above video overlay
    
    // 3D View parameters
    property real rotationX: 30
    property real rotationZ: 0
    property real zoom: 200
    property real scale: 500  // Scale factor for meter to pixel conversion (1 meter = 500 pixels)
    property var pointsData: []
    
    Column {
        anchors.fill: parent
        spacing: 10
        
        // Header
        Rectangle {
            width: parent.width
            height: 60
            color: "#222222"
            
            Row {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 20
                
                Text {
                    text: "LiDAR Point Cloud"
                    font.pixelSize: 24
                    font.bold: true
                    color: "white"
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "Points: " + (lidarController.point_count || 0)
                    font.pixelSize: 18
                    color: "#00FF00"
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "Messages: " + (lidarController.messages_received || 0)
                    font.pixelSize: 18
                    color: "#00FF00"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
        
        // Efficient Canvas-based 3D view
        Rectangle {
            width: parent.width
            height: parent.height - 140
            color: "#000000"
            border.color: "#00FF00"
            border.width: 2
            
            Canvas {
                id: canvas3d
                anchors.fill: parent
                anchors.margins: 5
                
                property real centerX: width / 2
                property real centerY: height / 2
                
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.reset();
                    
                    // Clear background
                    ctx.fillStyle = "#000000";
                    ctx.fillRect(0, 0, width, height);
                    
                    if (pointsData.length === 0) {
                        ctx.fillStyle = "#888888";
                        ctx.font = "20px Arial";
                        ctx.textAlign = "center";
                        ctx.fillText("Waiting for LiDAR data...", centerX, centerY);
                        return;
                    }
                    
                    // Draw coordinate axes
                    ctx.strokeStyle = "#FF0000";
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(centerX, centerY);
                    ctx.lineTo(centerX + 80, centerY);
                    ctx.stroke();
                    
                    ctx.strokeStyle = "#00FF00";
                    ctx.beginPath();
                    ctx.moveTo(centerX, centerY);
                    ctx.lineTo(centerX, centerY - 80);
                    ctx.stroke();
                    
                    // Convert angles to radians
                    var rotXRad = rotationX * Math.PI / 180;
                    var rotZRad = rotationZ * Math.PI / 180;
                    
                    // Debug: Draw first few points without any transformations
                    ctx.fillStyle = "#FF00FF";  // Magenta for debug points
                    for (var d = 0; d < Math.min(5, pointsData.length); d++) {
                        var dp = pointsData[d];
                        var dx = centerX + dp.x * 50;  // Simple scale
                        var dy = centerY - dp.y * 50;
                        ctx.fillRect(dx - 3, dy - 3, 6, 6);
                        
                        // Draw point coordinates
                        ctx.fillStyle = "#FFFFFF";
                        ctx.font = "10px Arial";
                        ctx.textAlign = "left";
                        ctx.fillText("(" + dp.x.toFixed(2) + "," + dp.y.toFixed(2) + "," + dp.z.toFixed(2) + ")", 
                                   dx + 5, dy);
                        ctx.fillStyle = "#FF00FF";
                    }
                    
                                        // Draw points with simplified 3D transformation
                    ctx.fillStyle = "#00FF00";
                    
                    // Use much less aggressive sampling - show more points
                    var step = Math.max(1, Math.floor(pointsData.length / 5000));  // Show up to 5000 points
                    var drawnPoints = 0;
                    var skippedPoints = 0;
                    
                    for (var i = 0; i < pointsData.length; i += step) {
                        var p = pointsData[i];
                        
                        // Start with original coordinates
                        var x = p.x;
                        var y = p.y;
                        var z = p.z;
                        
                        // Apply simple rotations (simplified - no perspective yet)
                        var rotXRad = rotationX * Math.PI / 180;
                        var rotZRad = rotationZ * Math.PI / 180;
                        
                        // Rotate around X axis (pitch)
                        var y1 = y * Math.cos(rotXRad) - z * Math.sin(rotXRad);
                        var z1 = y * Math.sin(rotXRad) + z * Math.cos(rotXRad);
                        
                        // Rotate around Z axis (yaw)
                        var x2 = x * Math.cos(rotZRad) - y1 * Math.sin(rotZRad);
                        var y2 = x * Math.sin(rotZRad) + y1 * Math.cos(rotZRad);
                        
                        // Simple scaling and projection to screen
                        var screenX = centerX + x2 * scale;
                        var screenY = centerY - y2 * scale;  // Flip Y for screen coordinates
                        
                        // Check bounds with some margin for debugging
                        if (screenX >= -50 && screenX < width + 50 && 
                            screenY >= -50 && screenY < height + 50) {
                            
                            // Draw larger points for better visibility
                            ctx.fillRect(screenX - 3, screenY - 3, 6, 6);
                            drawnPoints++;
                        } else {
                            skippedPoints++;
                        }
                    }
                    
                    // Draw debug info
                    ctx.fillStyle = "#AAAAAA";
                    ctx.font = "12px Arial";
                    ctx.textAlign = "left";
                    ctx.fillText("Total Points: " + pointsData.length, 10, 20);
                    ctx.fillText("Sampling: every " + step + " points", 10, 35);
                    ctx.fillText("Points drawn: " + drawnPoints, 10, 50);
                    ctx.fillText("Scale: " + scale + "x", 10, 65);
                    ctx.fillText("Zoom: " + zoom.toFixed(0), 10, 80);
                    ctx.fillText("Rotation: X=" + rotationX.toFixed(0) + "° Z=" + rotationZ.toFixed(0) + "°", 10, 95);
                    
                    if (pointsData.length > 0) {
                        var firstPoint = pointsData[0];
                        ctx.fillText("First point: x=" + firstPoint.x.toFixed(3) + 
                                   " y=" + firstPoint.y.toFixed(3) + 
                                   " z=" + firstPoint.z.toFixed(3), 10, 110);
                    }
                    
                    // Draw center marker
                    ctx.fillStyle = "#FFFF00";
                    ctx.fillRect(centerX - 2, centerY - 2, 4, 4);
                }
                
                MouseArea {
                    anchors.fill: parent
                    property real lastX: 0
                    property real lastY: 0
                    
                    onPressed: {
                        lastX = mouseX;
                        lastY = mouseY;
                    }
                    
                    onPositionChanged: {
                        if (pressed) {
                            var dx = mouseX - lastX;
                            var dy = mouseY - lastY;
                            
                            rotationZ += dx * 0.3;
                            rotationX += dy * 0.3;
                            
                            // Clamp rotation
                            rotationX = Math.max(-90, Math.min(90, rotationX));
                            
                            lastX = mouseX;
                            lastY = mouseY;
                            
                            canvas3d.requestPaint();
                        }
                    }
                    
                    onWheel: {
                        zoom += wheel.angleDelta.y * 0.2;
                        zoom = Math.max(50, Math.min(1000, zoom));
                        canvas3d.requestPaint();
                    }
                }
            }
            
            // Debug info overlay
            Column {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.margins: 10
                
                Text {
                    text: "Total Points: " + pointsData.length
                    color: "#00FF00"
                    font.pixelSize: 12
                }
                
                Text {
                    text: "Drag: rotate | Wheel: zoom"
                    color: "#AAAAAA"
                    font.pixelSize: 10
                }
            }
        }
        
        // Controls
        Rectangle {
            width: parent.width
            height: 70
            color: "#222222"
            
            Column {
                anchors.centerIn: parent
                spacing: 10
                
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 20
                    
                    Text {
                        text: "Drag to rotate | Scroll to zoom"
                        font.pixelSize: 16
                        color: "#AAAAAA"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Button {
                        text: "Reset View"
                        onClicked: {
                            rotationX = 30;
                            rotationZ = 0;
                            zoom = 200;
                            canvas3d.requestPaint();
                        }
                    }
                    
                    Button {
                        text: "Refresh"
                        onClicked: {
                            canvas3d.requestPaint();
                        }
                    }
                    
                    Text {
                        text: "Press 'A' to close"
                        font.pixelSize: 16
                        color: "#00FF00"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10
                    
                    Text {
                        text: "Scale:"
                        font.pixelSize: 14
                        color: "#AAAAAA"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Button {
                        text: "-"
                        width: 40
                        onClicked: {
                            scale = Math.max(50, scale - 50);
                            canvas3d.requestPaint();
                        }
                    }
                    
                    Text {
                        text: scale.toFixed(0) + "x"
                        font.pixelSize: 14
                        color: "#00FF00"
                        anchors.verticalCenter: parent.verticalCenter
                        width: 50
                        horizontalAlignment: Text.AlignHCenter
                    }
                    
                    Button {
                        text: "+"
                        width: 40
                        onClicked: {
                            scale = Math.min(2000, scale + 50);
                            canvas3d.requestPaint();
                        }
                    }
                }
            }
        }
    }
    
    // Connections to update when LiDAR data changes
    Connections {
        target: lidarController
        
        function onPoints_ready(points) {
            console.log("Received", points.length, "points for rendering");
            pointsData = points;
        }
        
        function onPointcloud_updated(data) {
            console.log("LiDAR data updated:", JSON.stringify(data));
        }
    }
    
    // Smooth fade in/out animation
    Behavior on opacity {
        NumberAnimation { duration: 300 }
    }
    
    opacity: active ? 1.0 : 0.0
}
