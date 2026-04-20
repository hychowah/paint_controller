import QtQuick
import QtQuick.Controls

Item {
    id: root
    anchors.fill: parent
    visible: birdViewController.editMode
    
    // Source image dimensions (before transformation)
    readonly property int sourceWidth: 640
    readonly property int sourceHeight: 480
    
    // Points from transformer (normalized 0.0-1.0)
    property var points: birdViewController.sourcePoints
    
    // Visual feedback
    property int activePoint: -1
    
    // Semi-transparent background
    Rectangle {
        anchors.fill: parent
        color: "#80000000"
        opacity: 0.3
    }
    
    // Instructions text
    Rectangle {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 10
        width: instructionText.width + 20
        height: 30
        color: "#E0000000"
        radius: 5
        border.color: "#4CAF50"
        border.width: 2
        
        Text {
            id: instructionText
            text: "Drag corners to adjust perspective • ESC to exit"
            color: "#4CAF50"
            font.pixelSize: 12
            font.bold: true
            anchors.centerIn: parent
        }
    }
    
    // Trapezoid outline connecting the four points
    Canvas {
        id: canvas
        anchors.fill: parent
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            if (points && points.length === 4) {
                // Draw trapezoid
                ctx.strokeStyle = "#4CAF50"
                ctx.lineWidth = 2
                ctx.setLineDash([5, 3])
                
                ctx.beginPath()
                for (var i = 0; i < 4; i++) {
                    var x = points[i][0] * width
                    var y = points[i][1] * height
                    if (i === 0) {
                        ctx.moveTo(x, y)
                    } else {
                        ctx.lineTo(x, y)
                    }
                }
                ctx.closePath()
                ctx.stroke()
                
                // Draw coordinate labels
                ctx.font = "11px monospace"
                ctx.fillStyle = "#4CAF50"
                var labels = ["BL", "BR", "TR", "TL"]
                for (var j = 0; j < 4; j++) {
                    var px = points[j][0] * width
                    var py = points[j][1] * height
                    ctx.fillText(labels[j] + " (" + points[j][0].toFixed(3) + ", " + points[j][1].toFixed(3) + ")", 
                                px + 15, py - 5)
                }
            }
        }
        
        Connections {
            target: birdViewController
            function onSourcePointsChanged() {
                canvas.requestPaint()
            }
        }
    }
    
    // Four draggable corner points
    Repeater {
        model: 4
        
        Rectangle {
            id: dragHandle
            width: 20
            height: 20
            radius: 10
            color: activePoint === index ? "#FF5722" : "#4CAF50"
            border.color: "white"
            border.width: 2
            
            x: (points && points[index] ? points[index][0] * root.width : 0) - width / 2
            y: (points && points[index] ? points[index][1] * root.height : 0) - height / 2
            
            z: activePoint === index ? 10 : 5
            
            // Label
            Text {
                text: index
                color: "white"
                font.pixelSize: 11
                font.bold: true
                anchors.centerIn: parent
            }
            
            // Drag behavior
            MouseArea {
                id: mouseArea
                anchors.fill: parent
                anchors.margins: -10  // Larger touch target
                cursorShape: Qt.OpenHandCursor
                drag.target: parent
                
                property real startX: 0
                property real startY: 0
                
                onPressed: {
                    root.activePoint = index
                    cursorShape = Qt.ClosedHandCursor
                    startX = dragHandle.x
                    startY = dragHandle.y
                }
                
                onReleased: {
                    root.activePoint = -1
                    cursorShape = Qt.OpenHandCursor
                }
                
                onPositionChanged: {
                    if (drag.active) {
                        // Constrain to bounds
                        var newX = Math.max(0, Math.min(root.width, dragHandle.x + dragHandle.width / 2))
                        var newY = Math.max(0, Math.min(root.height, dragHandle.y + dragHandle.height / 2))
                        
                        // Convert to normalized coordinates
                        var normalizedX = newX / root.width
                        var normalizedY = newY / root.height
                        
                        // Update the transformer
                        birdViewController.updateSourcePoint(index, normalizedX, normalizedY)
                        
                        // Redraw canvas
                        canvas.requestPaint()
                    }
                }
            }
            
            // Hover effect
            scale: mouseArea.containsMouse ? 1.2 : 1.0
            Behavior on scale {
                NumberAnimation { duration: 100 }
            }
            
            Behavior on color {
                ColorAnimation { duration: 150 }
            }
        }
    }
    
    // Close button
    Button {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 20
        width: 150
        height: 40
        
        background: Rectangle {
            color: parent.pressed ? "#388E3C" : (parent.hovered ? "#43A047" : "#4CAF50")
            radius: 6
            border.color: "white"
            border.width: 2
        }
        
        contentItem: Text {
            text: "Done Editing"
            color: "white"
            font.pixelSize: 14
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        
        onClicked: birdViewController.editMode = false
    }
    
    // ESC key to exit
    Keys.onEscapePressed: {
        birdViewController.editMode = false
    }
    
    Component.onCompleted: {
        if (visible) {
            forceActiveFocus()
        }
    }
    
    onVisibleChanged: {
        if (visible) {
            forceActiveFocus()
            canvas.requestPaint()
        }
    }
}
