import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import QtMultimedia 6.7
import Qt5Compat.GraphicalEffects

Rectangle {
    id: page1Rect
    objectName: "page1Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    property int timeStep: 0
    color: "#9F9F9F"

    property string camSource: "image://base_front_live/frame"
    
    // Main container optimized for 1280x720 but scales responsively
    Rectangle {
        id: dataRect
        width: Math.min(parent.width * 0.95, 1200)
        height: Math.min(parent.height * 0.9, 680)
        anchors.centerIn: parent
        color: "#E2E2E2"
        radius: 20
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 15

            // Camera view area (left side)
            Rectangle {
                id: cameraContainer
                Layout.preferredWidth: parent.width * 0.65
                Layout.fillHeight: true
                color: "#1E1E1E"
                radius: 15
                
                Rectangle {
                    id: baseView
                    objectName: "baseView"
                    anchors.fill: parent
                    anchors.margins: 2
                    radius: 15
                    color: "black"
                    clip: true
                    
                    Image {
                        id: baseFrame
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectFit
                        cache: false
                        source: camSource
                    }

                    // Camera selection buttons - modernized
                    Rectangle {
                        anchors.top: parent.top
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.topMargin: 15
                        height: 40
                        width: 206  // Adjusted for the two buttons to be adjacent
                        radius: 20
                        color: "#22FFFFFF"  // Semi-transparent white for a modern glass effect
                        z: 1
                        
                        Rectangle {
                            anchors.fill: parent
                            radius: 20
                            color: "transparent"
                            border.color: "#33FFFFFF"
                            border.width: 1
                        }
                        
                        Row {
                            anchors.fill: parent
                            spacing: 0  // Buttons will be adjacent with no gap
                            
                            // Front camera button
                            Rectangle {
                                id: frontButton
                                width: parent.width / 2
                                height: parent.height
                                color: camSource == "image://base_front_live/frame" ? "#407FFF" : "transparent"
                                radius: 20
                                
                                // Only round the left corners
                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: parent.width / 2
                                    color: parent.color
                                }
                                
                                // Left glow effect for active button
                                Rectangle {
                                    visible: camSource == "image://base_front_live/frame"
                                    anchors.fill: parent
                                    radius: 20
                                    color: "transparent"
                                    border.color: "#80AFFFFF"
                                    border.width: 1
                                }
                                
                                Label {
                                    anchors.centerIn: parent
                                    text: "FRONT"
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: camSource == "image://base_front_live/frame" ? "white" : "#CCFFFFFF"
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: camSource = "image://base_front_live/frame"
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }
                            
                            // Rear camera button
                            Rectangle {
                                id: rearButton
                                width: parent.width / 2
                                height: parent.height
                                color: camSource == "image://base_rear_live/frame" ? "#407FFF" : "transparent"
                                radius: 20
                                
                                // Only round the right corners
                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: parent.width / 2
                                    color: parent.color
                                }
                                
                                // Right glow effect for active button
                                Rectangle {
                                    visible: camSource == "image://base_rear_live/frame"
                                    anchors.fill: parent
                                    radius: 20
                                    color: "transparent"
                                    border.color: "#80AFFFFF"
                                    border.width: 1
                                }
                                
                                Label {
                                    anchors.centerIn: parent
                                    text: "REAR"
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: camSource == "image://base_rear_live/frame" ? "white" : "#CCFFFFFF"
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: camSource = "image://base_rear_live/frame"
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }
                        }
                    }
                }
            }

            // Data display area (right side)
            Rectangle {
                id: dataPanelContainer
                Layout.preferredWidth: parent.width * 0.35
                Layout.fillHeight: true
                color: "#FFFFFF"
                radius: 15
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 12
                    
                    // Switch for enabling/disabling wheels - full-width modern design
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56
                        color: uiData.wheel_enabled ? "#E3F2FD" : "#F5F5F5"
                        radius: 12
                        border.width: 1
                        border.color: uiData.wheel_enabled ? "#90CAF9" : "#E0E0E0"
                        
                        // Subtle transition animations
                        Behavior on color {
                            ColorAnimation { duration: 200 }
                        }
                        Behavior on border.color {
                            ColorAnimation { duration: 200 }
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                backend.setWheelEnabled(!uiData.wheel_enabled)
                            }
                        }
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12
                            
                            // Icon placeholder - wheel icon
                            Rectangle {
                                width: 32
                                height: 32
                                radius: 16
                                color: uiData.wheel_enabled ? "#2196F3" : "#9E9E9E"
                                
                                // Simple wheel icon using rectangles
                                Rectangle {
                                    width: 14
                                    height: 14
                                    radius: 7
                                    color: "white"
                                    anchors.centerIn: parent
                                }
                                
                                Rectangle {
                                    width: 26
                                    height: 26
                                    radius: 13
                                    color: "transparent"
                                    border.width: 3
                                    border.color: "white"
                                    anchors.centerIn: parent
                                }
                                
                                // Color transition
                                Behavior on color {
                                    ColorAnimation { duration: 200 }
                                }
                            }
                            
                            // Text with status
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                
                                Label {
                                    text: "Wheel Control"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "#212121"
                                }
                                
                                Label {
                                    text: uiData.wheel_enabled ? "Enabled - Motors active" : "Disabled - Motors inactive"
                                    font.pixelSize: 13
                                    color: uiData.wheel_enabled ? "#2196F3" : "#757575"
                                    
                                    // Color transition
                                    Behavior on color {
                                        ColorAnimation { duration: 200 }
                                    }
                                }
                            }
                            
                            // Toggle switch (visual element)
                            Rectangle {
                                width: 48
                                height: 24
                                radius: 12
                                color: uiData.wheel_enabled ? "#2196F3" : "#9E9E9E"
                                
                                Rectangle {
                                    id: toggleHandle
                                    width: 20
                                    height: 20
                                    radius: 10
                                    color: "white"
                                    anchors.verticalCenter: parent.verticalCenter
                                    x: uiData.wheel_enabled ? parent.width - width - 2 : 2
                                    
                                    // Add subtle drop shadow
                                    layer.enabled: true
                                    layer.effect: DropShadow {
                                        transparentBorder: true
                                        horizontalOffset: 0
                                        verticalOffset: 1
                                        radius: 3.0
                                        samples: 7
                                        color: "#30000000"
                                    }
                                    
                                    Behavior on x {
                                        NumberAnimation { 
                                            duration: 200
                                            easing.type: Easing.OutCubic
                                        }
                                    }
                                }
                                
                                // Color transition animation
                                Behavior on color {
                                    ColorAnimation { duration: 200 }
                                }
                            }
                        }
                    }
                    
                    // Metrics cards using built-in components
                    // Left Speed
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 75
                        color: "#F5F5F5"
                        radius: 10
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            
                            Label {
                                text: "LEFT SPEED"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#555555"
                            }
                            
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                
                                Label {
                                    text: Number(uiData.left_wheel_speed || 0).toFixed(3)
                                    font.pixelSize: 28
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                
                                Label {
                                    text: "RPM"
                                    font.pixelSize: 14
                                    color: "#777777"
                                    Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                                    Layout.bottomMargin: 3
                                }
                                
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 6
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.leftMargin: 10
                                    radius: 3
                                    
                                    Rectangle {
                                        width: parent.width * Math.min(Math.abs(Number(uiData.left_wheel_speed || 0)) / 40, 1)
                                        height: parent.height
                                        color: "#2196F3"
                                        radius: 3
                                    }
                                }
                            }
                        }
                    }
                    
                    // Right Speed
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 75
                        color: "#F5F5F5"
                        radius: 10
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            
                            Label {
                                text: "RIGHT SPEED"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#555555"
                            }
                            
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                
                                Label {
                                    text: Number(uiData.right_wheel_speed || 0).toFixed(3)
                                    font.pixelSize: 28
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                
                                Label {
                                    text: "RPM"
                                    font.pixelSize: 14
                                    color: "#777777"
                                    Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                                    Layout.bottomMargin: 3
                                }
                                
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 6
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.leftMargin: 10
                                    radius: 3
                                    
                                    Rectangle {
                                        width: parent.width * Math.min(Math.abs(Number(uiData.right_wheel_speed || 0)) / 40, 1)
                                        height: parent.height
                                        color: "#2196F3"
                                        radius: 3
                                    }
                                }
                            }
                        }
                    }
                    
                    // Left Current
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 75
                        color: "#F5F5F5"
                        radius: 10
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            
                            Label {
                                text: "LEFT CURRENT"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#555555"
                            }
                            
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                
                                Label {
                                    text: Number(uiData.left_wheel_current || 0).toFixed(3)
                                    font.pixelSize: 28
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                
                                Label {
                                    text: "A"
                                    font.pixelSize: 14
                                    color: "#777777"
                                    Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                                    Layout.bottomMargin: 3
                                }
                                
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 6
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.leftMargin: 10
                                    radius: 3
                                    
                                    Rectangle {
                                        width: parent.width * Math.min(Math.abs(Number(uiData.left_wheel_current || 0)) / 5, 1)
                                        height: parent.height
                                        color: "#FF5722"
                                        radius: 3
                                    }
                                }
                            }
                        }
                    }
                    
                    // Right Current
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 75
                        color: "#F5F5F5"
                        radius: 10
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            
                            Label {
                                text: "RIGHT CURRENT"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#555555"
                            }
                            
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                
                                Label {
                                    text: Number(uiData.right_wheel_current || 0).toFixed(3)
                                    font.pixelSize: 28
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                
                                Label {
                                    text: "A"
                                    font.pixelSize: 14
                                    color: "#777777"
                                    Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                                    Layout.bottomMargin: 3
                                }
                                
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 6
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.leftMargin: 10
                                    radius: 3
                                    
                                    Rectangle {
                                        width: parent.width * Math.min(Math.abs(Number(uiData.right_wheel_current || 0)) / 5, 1)
                                        height: parent.height
                                        color: "#FF5722"
                                        radius: 3
                                    }
                                }
                            }
                        }
                    }
                    
                    // Left Wheel Travel
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 75
                        color: "#F5F5F5"
                        radius: 10
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            
                            Label {
                                text: "LEFT WHEEL TRAVEL"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#555555"
                            }
                            
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                
                                Label {
                                    text: Number(uiData.left_wheel_travel || 0).toFixed(3)
                                    font.pixelSize: 28
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                
                                Label {
                                    text: "m"
                                    font.pixelSize: 14
                                    color: "#777777"
                                    Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                                    Layout.bottomMargin: 3
                                }
                                
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 6
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.leftMargin: 10
                                    radius: 3
                                    
                                    Rectangle {
                                        width: parent.width * Math.min(Math.abs(Number(uiData.left_wheel_travel || 0)) / 100, 1)
                                        height: parent.height
                                        color: "#4CAF50"
                                        radius: 3
                                    }
                                }
                            }
                        }
                    }
                    
                    // Right Wheel Travel
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 75
                        color: "#F5F5F5"
                        radius: 10
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 4
                            
                            Label {
                                text: "RIGHT WHEEL TRAVEL"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#555555"
                            }
                            
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                
                                Label {
                                    text: Number(uiData.right_wheel_travel || 0).toFixed(3)
                                    font.pixelSize: 28
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                                
                                Label {
                                    text: "m"
                                    font.pixelSize: 14
                                    color: "#777777"
                                    Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                                    Layout.bottomMargin: 3
                                }
                                
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 6
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.leftMargin: 10
                                    radius: 3
                                    
                                    Rectangle {
                                        width: parent.width * Math.min(Math.abs(Number(uiData.right_wheel_travel || 0)) / 100, 1)
                                        height: parent.height
                                        color: "#4CAF50"
                                        radius: 3
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Timer {
            interval: 100
            repeat: true
            running: true
            onTriggered: {
                timeStep++;
                var y = (1+Math.cos(timeStep/10.0))/2.0;
            }
        }

        Connections {
            target: baseStreamHandler
            function onBaseFrontFrameReady() {
                if (camSource == "image://base_front_live/frame"){
                    baseFrame.source = ""
                    baseFrame.source = "image://base_front_live/frame"
                }
            }

            function onBaseRearFrameReady() {
                if (camSource == "image://base_rear_live/frame"){
                    baseFrame.source = ""
                    baseFrame.source = "image://base_rear_live/frame"
                }
            }
        }
    }
}