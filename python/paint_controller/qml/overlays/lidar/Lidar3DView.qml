import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick3D 6.0

Rectangle {
    id: root
    
    property bool active: false
    property var pointsData: []
    property bool showGrid: true
    property bool showAxes: true
    property string colorMode: "distance"  // "distance", "height", "uniform"
    
    visible: active
    anchors.fill: parent
    color: "#1a1a1a"
    z: 600
    
    View3D {
        id: view3d
        anchors.fill: parent
        visible: root.active  // Only render when active
        
        environment: SceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: "#1a1a1a"
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }
        
        // Camera
        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 200, 1500)
            eulerRotation.x: -10
            eulerRotation.y: 0
            fieldOfView: 45
            clipNear: 1
            clipFar: 10000
        }
        
        // Directional Light
        DirectionalLight {
            eulerRotation.x: -30
            eulerRotation.y: -70
            brightness: 1.0
        }
        
        // Ambient Light
        DirectionalLight {
            eulerRotation.x: 30
            eulerRotation.y: 110
            brightness: 0.3
        }
        
        // Grid floor
        Model {
            visible: showGrid
            source: "#Rectangle"
            position: Qt.vector3d(0, -500, 0)
            eulerRotation.x: -90
            scale: Qt.vector3d(50, 50, 1)
            materials: DefaultMaterial {
                diffuseColor: "#303030"
                lighting: DefaultMaterial.NoLighting
            }
        }
        
        // Grid lines
        Repeater3D {
            visible: showGrid
            model: 21
            
            Model {
                source: "#Cube"
                position: Qt.vector3d((index - 10) * 100, -500, 0)
                scale: Qt.vector3d(0.5, 0.5, 1000)
                materials: DefaultMaterial {
                    diffuseColor: index === 10 ? "#404040" : "#252525"
                    lighting: DefaultMaterial.NoLighting
                }
            }
        }
        
        Repeater3D {
            visible: showGrid
            model: 21
            
            Model {
                source: "#Cube"
                position: Qt.vector3d(0, -500, (index - 10) * 100)
                scale: Qt.vector3d(1000, 0.5, 0.5)
                materials: DefaultMaterial {
                    diffuseColor: index === 10 ? "#404040" : "#252525"
                    lighting: DefaultMaterial.NoLighting
                }
            }
        }
        
        // Axes
        // X axis (Red)
        Model {
            visible: showAxes
            source: "#Cylinder"
            position: Qt.vector3d(250, 0, 0)
            eulerRotation.z: 90
            scale: Qt.vector3d(2, 500, 2)
            materials: DefaultMaterial {
                diffuseColor: "#ff0000"
                lighting: DefaultMaterial.NoLighting
            }
        }
        
        // Y axis (Green)
        Model {
            visible: showAxes
            source: "#Cylinder"
            position: Qt.vector3d(0, 250, 0)
            scale: Qt.vector3d(2, 500, 2)
            materials: DefaultMaterial {
                diffuseColor: "#00ff00"
                lighting: DefaultMaterial.NoLighting
            }
        }
        
        // Z axis (Blue)
        Model {
            visible: showAxes
            source: "#Cylinder"
            position: Qt.vector3d(0, 0, 250)
            eulerRotation.x: 90
            scale: Qt.vector3d(2, 500, 2)
            materials: DefaultMaterial {
                diffuseColor: "#0000ff"
                lighting: DefaultMaterial.NoLighting
            }
        }
        
                // Node for point cloud model
        Node {
            id: pointCloud
            
            // Use Repeater to create individual point spheres
            // Only render when active to save GPU resources
            Repeater3D {
                model: root.active ? Math.min(pointsData.length, 2000) : 0  // 0 when inactive
                
                Model {
                    property var point: pointsData[index] || {x: 0, y: 0, z: 0}
                    property real distance: Math.sqrt(point.x * point.x + point.y * point.y + point.z * point.z)
                    
                    source: "#Sphere"
                    position: Qt.vector3d(point.x * 100, point.y * 100, point.z * 100)
                    scale: Qt.vector3d(0.1, 0.1, 0.1)
                    
                    materials: DefaultMaterial {
                        diffuseColor: getPointColor(distance, point.y)
                        lighting: DefaultMaterial.NoLighting
                    }
                }
            }
        }
    }
    
    // Helper function to get point color based on mode
    function getPointColor(distance, height) {
        if (colorMode === "uniform") {
            return "#00FF00"
        } else if (colorMode === "height") {
            // Color based on height (y coordinate)
            var h = height / 10.0  // Normalize to roughly -0.5 to 0.5
            h = Math.max(-1.0, Math.min(1.0, h))
            
            if (h < 0) {
                // Blue to cyan for below origin
                var b = Math.abs(h)
                return Qt.rgba(0, 1 - b * 0.5, 1, 1)
            } else {
                // Green to red for above origin
                return Qt.rgba(h, 1 - h, 0, 1)
            }
        } else {  // "distance" mode (default)
            // Color based on distance from origin (like RViz rainbow)
            var maxDist = 10.0  // meters
            var ratio = Math.min(distance / maxDist, 1.0)
            
            // Rainbow gradient: violet -> blue -> cyan -> green -> yellow -> red
            if (ratio < 0.2) {
                // Violet to Blue
                var t = ratio / 0.2
                return Qt.rgba(0.5 - t * 0.5, 0, 1, 1)
            } else if (ratio < 0.4) {
                // Blue to Cyan
                var t = (ratio - 0.2) / 0.2
                return Qt.rgba(0, t, 1, 1)
            } else if (ratio < 0.6) {
                // Cyan to Green
                var t = (ratio - 0.4) / 0.2
                return Qt.rgba(0, 1, 1 - t, 1)
            } else if (ratio < 0.8) {
                // Green to Yellow
                var t = (ratio - 0.6) / 0.2
                return Qt.rgba(t, 1, 0, 1)
            } else {
                // Yellow to Red
                var t = (ratio - 0.8) / 0.2
                return Qt.rgba(1, 1 - t, 0, 1)
            }
        }
    }
    
    // Mouse control for camera - orbit style
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        
        property real lastX: 0
        property real lastY: 0
        property bool rotating: false
        
        // Orbit rotation angles
        property real orbitYaw: 0
        property real orbitPitch: -10
        property real orbitDistance: 1500
        
        onPressed: {
            lastX = mouseX
            lastY = mouseY
            rotating = true
        }
        
        onReleased: {
            rotating = false
        }
        
        onPositionChanged: {
            if (rotating) {
                var dx = mouseX - lastX
                var dy = mouseY - lastY
                
                // Update orbit angles
                orbitYaw -= dx * 0.5
                orbitPitch += dy * 0.5
                
                // Clamp pitch to avoid flipping
                orbitPitch = Math.max(-89, Math.min(89, orbitPitch))
                
                updateCameraPosition()
                
                lastX = mouseX
                lastY = mouseY
            }
        }
        
        onWheel: {
            var delta = wheel.angleDelta.y
            orbitDistance -= delta * 2
            orbitDistance = Math.max(300, Math.min(5000, orbitDistance))
            updateCameraPosition()
        }
        
        function updateCameraPosition() {
            // Convert spherical coordinates to Cartesian
            var pitchRad = orbitPitch * Math.PI / 180
            var yawRad = orbitYaw * Math.PI / 180
            
            var x = orbitDistance * Math.cos(pitchRad) * Math.sin(yawRad)
            var y = orbitDistance * Math.sin(pitchRad) + 200
            var z = orbitDistance * Math.cos(pitchRad) * Math.cos(yawRad)
            
            camera.position = Qt.vector3d(x, y, z)
            
            // Look at center
            camera.eulerRotation.x = -orbitPitch
            camera.eulerRotation.y = -orbitYaw
        }
        
        Component.onCompleted: {
            updateCameraPosition()
        }
    }
    
    // UI Overlay - RViz style controls
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
                    text: "LiDAR 3D View"
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
                    text: "Rendered: " + Math.min(pointsData.length, 2000)
                    color: "#CCCCCC"
                    font.pixelSize: 13
                }
            }
        }
        
        // Display options
        Rectangle {
            width: 250
            height: displayColumn.height + 20
            color: "#CC1a1a1a"
            border.color: "#404040"
            border.width: 1
            radius: 5
            
            Column {
                id: displayColumn
                anchors.centerIn: parent
                spacing: 8
                
                Text {
                    text: "Display Options"
                    color: "#888888"
                    font.pixelSize: 12
                    font.bold: true
                }
                
                Row {
                    spacing: 10
                    Text {
                        text: "Color Mode:"
                        color: "#CCCCCC"
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Button {
                        text: colorMode === "distance" ? "Distance" : colorMode === "height" ? "Height" : "Uniform"
                        width: 100
                        onClicked: {
                            if (colorMode === "distance") colorMode = "height"
                            else if (colorMode === "height") colorMode = "uniform"
                            else colorMode = "distance"
                        }
                    }
                }
                
                Row {
                    spacing: 10
                    CheckBox {
                        id: gridCheckbox
                        checked: showGrid
                        onCheckedChanged: showGrid = checked
                    }
                    Text {
                        text: "Show Grid"
                        color: "#CCCCCC"
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                Row {
                    spacing: 10
                    CheckBox {
                        id: axesCheckbox
                        checked: showAxes
                        onCheckedChanged: showAxes = checked
                    }
                    Text {
                        text: "Show Axes"
                        color: "#CCCCCC"
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
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
                text: "+"
                width: 50
                font.pixelSize: 18
                font.bold: true
                onClicked: {
                    mouseArea.orbitDistance -= 200
                    mouseArea.orbitDistance = Math.max(300, Math.min(5000, mouseArea.orbitDistance))
                    mouseArea.updateCameraPosition()
                }
            }
            
            Button {
                text: "-"
                width: 50
                font.pixelSize: 18
                font.bold: true
                onClicked: {
                    mouseArea.orbitDistance += 200
                    mouseArea.orbitDistance = Math.max(300, Math.min(5000, mouseArea.orbitDistance))
                    mouseArea.updateCameraPosition()
                }
            }
            
            Rectangle {
                width: 2
                height: 30
                color: "#404040"
            }
            
            Button {
                text: "Reset View"
                width: 100
                onClicked: {
                    mouseArea.orbitYaw = 0
                    mouseArea.orbitPitch = -10
                    mouseArea.orbitDistance = 1500
                    mouseArea.updateCameraPosition()
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
    
    // Clear point data when deactivated to free memory
    onActiveChanged: {
        if (!active) {
            pointsData = []
        }
    }
    
    // Smooth fade in/out
    Behavior on opacity {
        NumberAnimation { duration: 300 }
    }
    
    opacity: active ? 1.0 : 0.0
}
