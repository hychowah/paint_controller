import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: powerControlMenu

    // These properties can now be directly bound to the overlayController
    property bool showOverlay: overlayController.show_overlay
    property string activeMenu: overlayController.active_menu
    property bool showPowerMenu: showOverlay && activeMenu === "power"

    // Ensure the menu is visible
    visible: true

    Rectangle {
        id: powerOverlayBackground
        anchors.fill: parent
        color: "#000000"
        opacity: showPowerMenu ? 0.5 : 0
        visible: opacity > 0
        
        Behavior on opacity {
            NumberAnimation { 
                duration: 250
                easing.type: Easing.InOutQuad 
            }
        }
        
        // Direct access to overlayController methods
        MouseArea {
            anchors.fill: parent
            onClicked: {
                overlayController.hide_menu()
            }
        }
    }

    Rectangle {
        id: powerMenuContainer
        width: 750 // Wider to accommodate two columns
        height: 650  // Increased height to accommodate the new button
        radius: 12
        color: "#1A1A1A"  // Darker background for modern look
        opacity: showPowerMenu ? 1 : 0
        visible: opacity > 0
        
        // Modern subtle border
        border.color: "#333333"
        border.width: 1
        
        // Centered positioning with animation
        anchors {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: showPowerMenu ? 0 : -parent.height
        }

        Behavior on anchors.verticalCenterOffset {
            NumberAnimation {
                duration: 300
                easing.type: Easing.OutBack
                easing.overshoot: 0.7
            }
        }

        Behavior on opacity {
            NumberAnimation {
                duration: 250
                easing.type: Easing.InOutQuad
            }
        }

        ColumnLayout {
            anchors {
                fill: parent
                margins: 20
            }
            spacing: 10

            // Header with close button
            RowLayout {
                Layout.fillWidth: true
                
                Text {
                    text: "Power Control"
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 26
                    font.bold: true
                    Layout.fillWidth: true
                }
                
                // Close button
                Rectangle {
                    width: 32
                    height: 32
                    radius: 16
                    color: closeMouseArea.containsMouse ? "#333333" : "transparent"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "×"
                        color: "#CCCCCC"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    
                    MouseArea {
                        id: closeMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: overlayController.hide_menu()
                    }
                }
            }
            
            // Divider
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#333333"
                Layout.topMargin: 4
                Layout.bottomMargin: 10
            }

            // Two-column layout
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 20
                
                // Left column - Base Controls
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10
                    
                    // Base Controls Category
                    Item {
                        Layout.fillWidth: true
                        height: 32
                        
                        Text {
                            text: "Base Controls"
                            color: "#FFFFFF"
                            font.family: "Helvetica"
                            font.pixelSize: 18
                            font.bold: true
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        
                        Rectangle {
                            height: 1
                            width: parent.width - 120
                            color: "#333333"
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }

                    // Winch Enable Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Winch Enable"
                        controlStatus: winchController.enabled ? "Enabled" : "Disabled"
                        enabledState: winchController.enabled
                        iconText: "W"
                        
                        onClicked: winchController.setEnabled(!winchController.enabled)
                    }
                    
                    // Winch Load Detection Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Load Detection"
                        controlStatus: winchController.load_detection_enabled ? "Active" : "Inactive"
                        enabledState: winchController.load_detection_enabled
                        iconText: "LD"
                        
                        onClicked: winchController.setLoadDetectionEnabled(!winchController.load_detection_enabled)
                    }
                    
                    // Wheel Enable Control (new)
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Wheel Enable"
                        // Assuming wheelController.enabled property exists
                        controlStatus: wheelController ? (wheelController.enabled ? "Motors active" : "Motors inactive") : "Unavailable"
                        enabledState: wheelController ? wheelController.enabled : false
                        iconText: "🛞"
                        
                        onClicked: {
                            if (wheelController) {
                                wheelController.setEnabled(!wheelController.enabled)
                            } else {
                                console.log("Wheel controller not available")
                            }
                        }
                    }
                    
                    // Spacer
                    Item { 
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                    }
                }
                
                // Vertical Separator
                Rectangle {
                    width: 1
                    Layout.fillHeight: true
                    color: "#333333"
                }
                
                // Right column - End Effector Controls
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10
                    
                    // End Effector Category
                    Item {
                        Layout.fillWidth: true
                        height: 32
                        
                        Text {
                            text: "End Effector Controls"
                            color: "#FFFFFF"
                            font.family: "Helvetica"
                            font.pixelSize: 18
                            font.bold: true
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        
                        Rectangle {
                            height: 1
                            width: parent.width - 180
                            color: "#333333"
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }

                    // Teensy Relay Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Teensy Relay"
                        controlStatus: teensyController.all_status.relay_on ? "Connected" : "Disconnected"
                        enabledState: teensyController.all_status.relay_on
                        iconText: "TR"
                        
                        onClicked: teensyController.setRelayEnabled(!teensyController.all_status.relay_on)
                    }
                    
                    // Teensy Enable Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Teensy Enable"
                        controlStatus: teensyController.all_status.enabled ? "Powered" : "Unpowered"
                        enabledState: teensyController.all_status.enabled
                        iconText: "T"
                        
                        onClicked: teensyController.setEnabled(!teensyController.all_status.enabled)
                    }
                    
                    // Yaw Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Yaw Control"
                        controlStatus: teensyController.all_status.yaw_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.all_status.yaw_enabled
                        iconText: "Y"
                        
                        onClicked: teensyController.setYawEnabled(!teensyController.all_status.yaw_enabled)
                    }

                    // SprayGun Levelling
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "SprayGun Levelling"
                        controlStatus: teensyController.spray_gun_leveling_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.spray_gun_leveling_enabled
                        iconText: "SL"

                        onClicked: teensyController.setSprayGunLevelingEnabled(!teensyController.spray_gun_leveling_enabled)
                    }

                    // SprayGun Led Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "SprayGun LED"
                        controlStatus: teensyController.spray_gun_led_on ? "On" : "Off"
                        enabledState: teensyController.spray_gun_led_on
                        iconText: "LED"
                        
                        onClicked: teensyController.setSprayGunLED(!teensyController.spray_gun_led_on)
                    }
                    
                    // Spacer
                    Item { 
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                    }
                }
            }
            
            // Error Cleaning Button Section - Added below the two columns
            Item {
                Layout.fillWidth: true
                Layout.topMargin: 10
                height: 32
                
                Text {
                    text: "System Errors"
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 18
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Rectangle {
                    height: 1
                    width: parent.width - 120
                    color: "#333333"
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Error Clear Button
            Rectangle {
                id: errorClearButton
                Layout.fillWidth: true
                height: 60
                radius: 10
                color: errorClearMouseArea.containsMouse ? "#4A2C2C" : "#3A2222"
                border.color: "#8C3A3A"
                border.width: 1
                
                Behavior on color {
                    ColorAnimation { duration: 200 }
                }
                
                MouseArea {
                    id: errorClearMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        // Call the clear_error_state method from heartbeatHandler
                        heartbeatHandler.clear_error_state()
                    }
                }
                
                RowLayout {
                    anchors {
                        fill: parent
                        margins: 10
                    }
                    spacing: 15
                    
                    // Icon
                    Rectangle {
                        width: 36
                        height: 36
                        radius: 18
                        color: "#8C3A3A"
                        
                        Text {
                            anchors.centerIn: parent
                            text: "⚠"
                            font.pixelSize: 16
                            color: "white"
                            font.bold: true
                        }
                    }
                    
                    // Text
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: "Clear Error States"
                            font.pixelSize: 16
                            font.bold: true
                            color: "#FFFFFF"
                        }
                        
                        Text {
                            text: "Reset all error flags in system components"
                            font.pixelSize: 13
                            color: "#F99090"
                        }
                    }
                    
                    // Reset icon
                    Rectangle {
                        width: 36
                        height: 36
                        radius: 18
                        color: "#8C3A3A"
                        
                        Text {
                            anchors.centerIn: parent
                            text: "↺"
                            font.pixelSize: 20
                            color: "white"
                            font.bold: true
                        }
                    }
                }
            }
        }
    }

    // Backend-driven control panel component with fixed alignment
    component ControlPanel: Rectangle {
        id: controlPanel
        property string controlName: "Control"
        property string controlStatus: "Unknown"
        property bool enabledState: false
        property string iconText: "X"
        
        signal clicked()
        
        height: 60
        radius: 10
        color: enabledState ? "#252A36" : "#222222"
        border.color: enabledState ? "#3A5A8C" : "#333333"
        border.width: 1
        
        // This ensures consistent layout across all control panels
        Layout.fillWidth: true
        
        // Subtle transition animations
        Behavior on color {
            ColorAnimation { duration: 200 }
        }
        
        Behavior on border.color {
            ColorAnimation { duration: 200 }
        }
        
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: controlPanel.clicked()
            
            // Hover effect
            onEntered: {
                parent.color = enabledState ? "#2A3040" : "#2A2A2A"
            }
            
            onExited: {
                parent.color = enabledState ? "#252A36" : "#222222"
            }
        }
        
        // Use Row instead of RowLayout for more consistent sizing
        Row {
            anchors {
                fill: parent
                margins: 10
                // Add right margin to create space between toggle and right edge
                rightMargin: 15
            }
            spacing: 10
            
            // Icon
            Rectangle {
                width: 36
                height: 36
                radius: 18
                color: enabledState ? "#3A5A8C" : "#444444"
                anchors.verticalCenter: parent.verticalCenter
                
                Text {
                    anchors.centerIn: parent
                    text: controlPanel.iconText
                    font.pixelSize: 16
                    color: "white"
                    font.bold: true
                }
                
                // Color transition
                Behavior on color {
                    ColorAnimation { duration: 200 }
                }
            }
            
            // Text with status - using a Rectangle with Column inside to fill available space
            Rectangle {
                width: parent.width - 36 - 10 - 48 - 5 // parent width minus icon width, spacing, switch width, and extra margin
                height: parent.height - 20
                color: "transparent" // Make this visible for debugging: "#550000"
                anchors.verticalCenter: parent.verticalCenter
                
                Column {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2
                    
                    Text {
                        text: controlPanel.controlName
                        font.pixelSize: 16
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    
                    Text {
                        text: controlPanel.controlStatus
                        font.pixelSize: 13
                        color: enabledState ? "#90CAF9" : "#999999"
                        
                        // Color transition
                        Behavior on color {
                            ColorAnimation { duration: 200 }
                        }
                    }
                }
            }
            
            // Toggle switch - simple Rectangle with fixed width
            Rectangle {
                width: 48
                height: 24
                radius: 12
                color: enabledState ? "#3A5A8C" : "#444444"
                anchors.verticalCenter: parent.verticalCenter
                
                Rectangle {
                    width: 18
                    height: 18
                    radius: 9
                    color: "#FFFFFF"
                    anchors.verticalCenter: parent.verticalCenter
                    x: enabledState ? parent.width - width - 3 : 3
                    
                    Behavior on x {
                        NumberAnimation { 
                            duration: 200
                            easing.type: Easing.OutCubic
                        }
                    }
                }
                
                // Color transition
                Behavior on color {
                    ColorAnimation { duration: 200 }
                }
            }
        }
    }
}