import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    color: "#000000"
    radius: 15
    border.color: "#333333"
    border.width: 1

    // Properties remain the same but update scale defaults
    property var points: []
    property real scale: 20
    property real panX: width / 2
    property real panY: height / 2
    property real rotationX: -45
    property real rotationY: 0
    property real rotationZ: -45
    property bool showGrid: true
    property real gridSpacing: 1.0
    property int gridLines: 20
    property real perspectiveStrength: 0.0015
    property real zoomValue: 20

    function vectorNormalize(v) {
        const len = Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        return { x: v.x / len, y: v.y / len, z: v.z / len }
    }

    function getArcballVector(x, y) {
        const center = { x: canvas.width / 2, y: canvas.height / 2 }
        const radius = Math.min(canvas.width, canvas.height) / 2
        
        // Get point on sphere
        let p = {
            x: (x - center.x) / radius,
            y: (y - center.y) / radius
        }
        
        // Clamp points that are outside the sphere
        const pyth = p.x * p.x + p.y * p.y
        if (pyth > 1) {
            // Point outside sphere, project to sphere
            const scale = 1 / Math.sqrt(pyth)
            p.x *= scale
            p.y *= scale
        }
        
        // Calculate Z coordinate on sphere
        const z = Math.sqrt(1 - Math.min(1, p.x * p.x + p.y * p.y))
        
        return vectorNormalize({ x: p.x, y: p.y, z: z })
    }


    // Transform 3D point to 2D screen coordinates with perspective
    function transform3DPoint(x, y, z) {
        // Convert rotation angles to radians
        const radX = rotationX * Math.PI / 180
        const radY = rotationY * Math.PI / 180
        const radZ = rotationZ * Math.PI / 180

        // Rotation around X axis
        let y1 = y * Math.cos(radX) - z * Math.sin(radX)
        let z1 = y * Math.sin(radX) + z * Math.cos(radX)

        // Rotation around Y axis
        let x2 = x * Math.cos(radY) + z1 * Math.sin(radY)
        let z2 = -x * Math.sin(radY) + z1 * Math.cos(radY)

        // Rotation around Z axis
        let x3 = x2 * Math.cos(radZ) - y1 * Math.sin(radZ)
        let y3 = x2 * Math.sin(radZ) + y1 * Math.cos(radZ)

        // Apply perspective
        const depth = 1 + z2 * perspectiveStrength
        const perspectiveScale = scale / depth

        return {
            x: x3 * perspectiveScale + panX,
            y: y3 * perspectiveScale + panY,
            depth: depth  // Return depth for z-ordering
        }
    }

    // Function to update zoom without triggering the binding loop
    function updateZoom(newValue) {
        zoomValue = newValue
        scale = newValue
        canvas.requestPaint()
    }


    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // Display Region
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#000000"
            radius: 10
            
            // Canvas for drawing
            Canvas {
                id: canvas
                anchors.fill: parent
                antialiasing: true

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.clearRect(0, 0, width, height)

                    // Draw grid
                    if (showGrid) {
                        // Draw ground grid (XY plane)
                        ctx.strokeStyle = "#333333"
                        ctx.lineWidth = 1

                        for (let i = -gridLines/2; i <= gridLines/2; i++) {
                            // X-axis parallel lines
                            let start = transform3DPoint(i * gridSpacing, -gridLines/2 * gridSpacing, 0)
                            let end = transform3DPoint(i * gridSpacing, gridLines/2 * gridSpacing, 0)
                            ctx.beginPath()
                            ctx.moveTo(start.x, start.y)
                            ctx.lineTo(end.x, end.y)
                            ctx.stroke()

                            // Y-axis parallel lines
                            start = transform3DPoint(-gridLines/2 * gridSpacing, i * gridSpacing, 0)
                            end = transform3DPoint(gridLines/2 * gridSpacing, i * gridSpacing, 0)
                            ctx.beginPath()
                            ctx.moveTo(start.x, start.y)
                            ctx.lineTo(end.x, end.y)
                            ctx.stroke()
                        }

                        // Draw coordinate axes
                        const origin = transform3DPoint(0, 0, 0)
                        
                        // X axis (red)
                        ctx.strokeStyle = "#FF0000"
                        ctx.lineWidth = 2
                        const xEnd = transform3DPoint(5, 0, 0)
                        ctx.beginPath()
                        ctx.moveTo(origin.x, origin.y)
                        ctx.lineTo(xEnd.x, xEnd.y)
                        ctx.stroke()

                        // Y axis (green)
                        ctx.strokeStyle = "#00FF00"
                        const yEnd = transform3DPoint(0, 5, 0)
                        ctx.beginPath()
                        ctx.moveTo(origin.x, origin.y)
                        ctx.lineTo(yEnd.x, yEnd.y)
                        ctx.stroke()

                        // Z axis (blue)
                        ctx.strokeStyle = "#0000FF"
                        const zEnd = transform3DPoint(0, 0, 5)
                        ctx.beginPath()
                        ctx.moveTo(origin.x, origin.y)
                        ctx.lineTo(zEnd.x, zEnd.y)
                        ctx.stroke()
                    }

                    // Sort points by depth for proper rendering
                    const transformedPoints = points.map(point => ({
                        point: point,
                        transformed: transform3DPoint(point.x, point.y, point.z || 0)
                    })).sort((a, b) => b.transformed.depth - a.transformed.depth)

                    // Draw points
                    transformedPoints.forEach(({point, transformed}) => {
                        const intensity = point.intensity || 0
                        const height = point.z || 0
                        
                        // Color based on height and intensity
                        const hue = (height * 30) % 360  // Color cycles every 12 meters
                        const lightness = 30 + intensity * 20  // Vary lightness with intensity
                        ctx.fillStyle = `hsl(${hue}, 100%, ${lightness}%)`
                        
                        // Point size varies with depth
                        const pointSize = 3 / transformed.depth
                        
                        ctx.beginPath()
                        ctx.arc(transformed.x, transformed.y, pointSize, 0, 2 * Math.PI)
                        ctx.fill()
                    })
                }
            }

            // Pan control MouseArea
            MouseArea {
                anchors.fill: parent
                property point lastPos
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                onPressed: {
                    lastPos = Qt.point(mouseX, mouseY)
                }

                onPositionChanged: {
                    if (pressed) {
                        if (pressedButtons & Qt.LeftButton) {
                            // Pan with left button
                            panX += (mouseX - lastPos.x)
                            panY += (mouseY - lastPos.y)
                        } else if (pressedButtons & Qt.RightButton) {
                            // Rotate view with right button
                            const dx = mouseX - lastPos.x
                            const dy = mouseY - lastPos.y
                            const sensitivity = 0.5  // Adjust this value to control rotation speed

                            // Direct rotation without limits
                            rotationX += dy * sensitivity
                            rotationZ += dx * sensitivity
                        }
                        lastPos = Qt.point(mouseX, mouseY)
                        canvas.requestPaint()
                    }
                }
            }
        }

        // Control Region
        Rectangle {
            Layout.preferredWidth: 180
            Layout.fillHeight: true
            color: "#333333"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Button {
                    Layout.fillWidth: true
                    height: 40
                    text: "Reset View"
                    onClicked: {
                        panX = root.width / 2
                        panY = root.height / 2
                        updateZoom(20)
                        zoomSlider.value = 20
                        rotationX = -45
                        rotationY = 0
                        rotationZ = -45
                        canvas.requestPaint()
                    }
                }

                Button {
                    Layout.fillWidth: true
                    height: 40
                    text: showGrid ? "Hide Grid" : "Show Grid"
                    onClicked: {
                        showGrid = !showGrid
                        canvas.requestPaint()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#666666"
                }

                // Zoom control
                Label {
                    text: "Zoom: " + zoomSlider.value.toFixed(1)
                    color: "white"
                    font.pixelSize: 14
                    Layout.fillWidth: true
                }

                Slider {
                    id: zoomSlider
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    from: 5
                    to: 100
                    value: zoomValue

                    background: Rectangle {
                        x: zoomSlider.leftPadding
                        y: zoomSlider.topPadding + zoomSlider.availableHeight / 2 - height / 2
                        implicitWidth: zoomSlider.availableWidth
                        implicitHeight: 4
                        width: zoomSlider.availableWidth
                        height: implicitHeight
                        radius: 2
                        color: "#666666"
                        Rectangle {
                            width: zoomSlider.visualPosition * parent.width
                            height: parent.height
                            color: "#4CAF50"
                            radius: 2
                        }
                    }

                    handle: Rectangle {
                        x: zoomSlider.leftPadding + zoomSlider.visualPosition * (zoomSlider.availableWidth - width)
                        y: zoomSlider.topPadding + zoomSlider.availableHeight / 2 - height / 2
                        width: 20
                        height: 20
                        radius: 10
                        color: zoomSlider.pressed ? "#f0f0f0" : "#ffffff"
                        border.color: "#4CAF50"
                    }

                    onMoved: updateZoom(value)
                }

                

                // X Rotation
                Label {
                    text: "X Rotation: " + xRotationSlider.value.toFixed(0) + "°"
                    color: "white"
                    font.pixelSize: 14
                    Layout.fillWidth: true
                }

                Slider {
                    id: xRotationSlider
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    from: -90
                    to: 90
                    value: rotationX
                    
                    background: Rectangle {
                        x: xRotationSlider.leftPadding
                        y: xRotationSlider.topPadding + xRotationSlider.availableHeight / 2 - height / 2
                        implicitWidth: xRotationSlider.availableWidth
                        implicitHeight: 4
                        width: xRotationSlider.availableWidth
                        height: implicitHeight
                        radius: 2
                        color: "#666666"
                        Rectangle {
                            width: xRotationSlider.visualPosition * parent.width
                            height: parent.height
                            color: "#FF4444"
                            radius: 2
                        }
                    }

                    handle: Rectangle {
                        x: xRotationSlider.leftPadding + xRotationSlider.visualPosition * (xRotationSlider.availableWidth - width)
                        y: xRotationSlider.topPadding + xRotationSlider.availableHeight / 2 - height / 2
                        width: 20
                        height: 20
                        radius: 10
                        color: xRotationSlider.pressed ? "#f0f0f0" : "#ffffff"
                        border.color: "#FF4444"
                    }

                    onValueChanged: {
                        rotationX = value
                        canvas.requestPaint()
                    }
                }

                // Y and Z Rotation sliders with same pattern...
                // Keep same styling pattern for Y and Z sliders
                Label {
                    text: "Y Rotation: " + yRotationSlider.value.toFixed(0) + "°"
                    color: "white"
                    font.pixelSize: 14
                    Layout.fillWidth: true
                }

                Slider {
                    id: yRotationSlider
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    from: -180
                    to: 180
                    value: rotationY
                    // Same background and handle pattern with green color
                    onValueChanged: {
                        rotationY = value
                        canvas.requestPaint()
                    }
                }

                Label {
                    text: "Z Rotation: " + zRotationSlider.value.toFixed(0) + "°"
                    color: "white"
                    font.pixelSize: 14
                    Layout.fillWidth: true
                }

                Slider {
                    id: zRotationSlider
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    from: -180
                    to: 180
                    value: rotationZ
                    // Same background and handle pattern with blue color
                    onValueChanged: {
                        rotationZ = value
                        canvas.requestPaint()
                    }
                }

                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }

}