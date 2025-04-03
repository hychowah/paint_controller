import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: page3Rect
    objectName: "page3Rect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Helper function to update available options
    // Store the complete list of options
    property var allControlOptions: ["None", "Winch Speed", "Wheel Speed", "EF arm", "EF top rail", "EF prop pwm", "EF prop joint", "EF spray trigger", "EF spray gimbal"]
    
    // Properties to store current selections
    property string leftCurrentControl: "None"
    property string rightCurrentControl: "None"

    // Helper function to get available options for a combo box
    function getAvailableOptions(isLeftComboBox) {
        let otherSelection = isLeftComboBox ? rightCurrentControl : leftCurrentControl
        return allControlOptions.filter(option => 
            option === "None" || option !== otherSelection
        )
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Left Side: Winch Status
        Rectangle {
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                RowLayout {
                    spacing: 10
                    Label {
                        text: "Winch Status"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    // rectange for spacing
                    Rectangle {
                        Layout.fillWidth: true
                    }
                    TouchSwitch {
                            id: winchEnableSwitch
                            checked: winchController.enabled
                            onToggled: winchController.setEnabled(checked)
                    }
                }

                GridLayout {
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    Label { text: "Status:"; font.bold: true }
                    Label { 
                        text: winchController.available ? "Connected" : "Disconnected"
                        color: winchController.available ? "green" : "red"
                    }


                    Label { text: "Cable Length:"; font.bold: true }
                    Label { text: String((winchController.cable_length).toFixed(0)) + " mm" }

                    Label {text: "Cable Speed:"; font.bold: true}
                    Label {text: String(winchController.cable_speed.toFixed(0)) + " m/s"}

                    Label { text: "Torque:"; font.bold: true }
                    Label { text: String(winchController.winch_torque.toFixed(1)) + " Nm" }

                    Label { text: "Temperature:"; font.bold: true }
                    Label { text: winchController.motor_temperature.toFixed(1) + " °C" }

                    Label { text: "Voltage:"; font.bold: true }
                    Label { text: winchController.motor_voltage.toFixed(1) + " V" }

                    Label { text: "Brake:"; font.bold: true }
                    Label { 
                        text: winchController.motor_brake ? "Engaged" : "Released"
                        color: winchController.motor_brake ? "red" : "green"
                    }

                    Label { text: "Load Detection:"; font.bold: true }
                    Label { 
                        text: winchController.load_detection_enabled ? "True" : "False"
                        color: winchController.load_detection_enabled ? "green" : "red"
                    }

                    Label { text: "Unusual Load:"; font.bold: true }
                    Label { 
                        text: winchController.unusual_load_detected ? "True" : "False"
                        color: winchController.unusual_load_detected ? "green" : "red"
                    }

                }
            }
        }

        // teensy status
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10
                // Ensure layout is top-to-bottom with no stretching
                Layout.alignment: Qt.AlignTop

                // Header with title and switches
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    Label {
                        text: "Teensy Status"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    // rectangle for spacing
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                    }
                    Label { text: "Enable:"; font.bold: true }
                    
                    TouchSwitch {
                        id: teensyEnableSwitch
                        checked: teensyController.all_status.enabled
                        onToggled: teensyController.setEnabled(checked)
                    }

                    Label { text: "Relay:"; font.bold: true }
                    
                    TouchSwitch {
                        id: teensyRelayEnableSwitch
                        checked: teensyController.all_status.relay_on
                        onToggled: teensyController.setRelayEnabled(checked)
                    }
                }

                // Tab buttons - using Row for better touch control
                Rectangle {
                    Layout.fillWidth: true
                    height: 50
                    color: "transparent"
                    
                    RowLayout {
                        id: tabButtons
                        anchors.fill: parent
                        spacing: 1
                        
                        property int currentIndex: 0
                        
                        // Main Tab Button
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: tabButtons.currentIndex === 0 ? "#E0E0E0" : "transparent"
                            border.color: "#CCCCCC"
                            border.width: 1
                            
                            Text {
                                anchors.centerIn: parent
                                text: "Main"
                                font.pixelSize: 16
                                font.bold: tabButtons.currentIndex === 0
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: tabButtons.currentIndex = 0
                            }
                        }
                        
                        // Rails Tab Button
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: tabButtons.currentIndex === 1 ? "#E0E0E0" : "transparent"
                            border.color: "#CCCCCC"
                            border.width: 1
                            
                            Text {
                                anchors.centerIn: parent
                                text: "Rails"
                                font.pixelSize: 16
                                font.bold: tabButtons.currentIndex === 1
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: tabButtons.currentIndex = 1
                            }
                        }
                        
                        // Propellers Tab Button
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: tabButtons.currentIndex === 2 ? "#E0E0E0" : "transparent"
                            border.color: "#CCCCCC"
                            border.width: 1
                            
                            Text {
                                anchors.centerIn: parent
                                text: "Propellers"
                                font.pixelSize: 16
                                font.bold: tabButtons.currentIndex === 2
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: tabButtons.currentIndex = 2
                            }
                        }
                        
                        // IMU Tab Button
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: tabButtons.currentIndex === 3 ? "#E0E0E0" : "transparent"
                            border.color: "#CCCCCC"
                            border.width: 1
                            
                            Text {
                                anchors.centerIn: parent
                                text: "IMU"
                                font.pixelSize: 16
                                font.bold: tabButtons.currentIndex === 3
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: tabButtons.currentIndex = 3
                            }
                        }

                        // Spray Gun Tab Button
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: tabButtons.currentIndex === 4 ? "#E0E0E0" : "transparent"
                            border.color: "#CCCCCC"
                            border.width: 1
                            
                            Text {
                                anchors.centerIn: parent
                                text: "Spray Gun"
                                font.pixelSize: 16
                                font.bold: tabButtons.currentIndex === 4
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: tabButtons.currentIndex = 4
                            }
                        }
                    }
                }
                
                // Tab Content Area
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    // Stack of content pages
                    StackLayout {
                        id: contentStack
                        anchors.fill: parent
                        currentIndex: tabButtons.currentIndex
                        
                        // MAIN TAB
                        Item {
                            // Board Status Section
                            GridLayout {
                                anchors.fill: parent
                                columns: 4
                                rowSpacing: 10
                                columnSpacing: 20
                                
                                // Section title
                                Label { 
                                    text: "Board Status" 
                                    font.bold: true 
                                    font.pixelSize: 16
                                    Layout.columnSpan: 4
                                }
                                
                                // Board status values
                                Label { text: "Voltage:"; font.bold: true }
                                Label { text: teensyController.all_status.voltage.toFixed(1) + " V" }
                                Label { text: "Current:"; font.bold: true }
                                Label { text: teensyController.all_status.current.toFixed(1) + " A" }
                                
                                Label { text: "Temperature:"; font.bold: true }
                                Label { text: teensyController.all_status.temperature.toFixed(1) + " °C" }
                                Label { text: "Runtime:"; font.bold: true }
                                Label { text: teensyController.all_status.voltage.toFixed(1) }
                                
                                Label { text: "Loop Time:"; font.bold: true }
                                Label { text: teensyController.all_status.loop_time.toFixed(0) + " µs" }
                                Label { text: "Loop Counter:"; font.bold: true }
                                Label { text: teensyController.all_status.loop_time_counter.toFixed(0) }
                                
                                Label { text: "Battery:"; font.bold: true }
                                Label { text: "87%" }
                                Label { text: "Status:"; font.bold: true }
                                Label { text: "Operating" }
                                
                                // System Alerts section
                                Label { 
                                    text: "System Alerts" 
                                    font.bold: true 
                                    font.pixelSize: 16
                                    Layout.columnSpan: 4
                                    Layout.topMargin: 10
                                }
                                
                                // Alerts display area
                                Rectangle {
                                    Layout.columnSpan: 4
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    Layout.minimumHeight: 100
                                    color: "#F5F5F5"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    
                                    Column {
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        spacing: 10
                                        
                                        // Temperature warning
                                        Row {
                                            spacing: 10
                                            Rectangle {
                                                width: 12
                                                height: 12
                                                radius: 6
                                                color: "#FFA500" // Orange for warning
                                            }
                                            Text { text: "Temperature Warning" }
                                        }
                                        
                                        // Voltage warning
                                        Row {
                                            spacing: 10
                                            Rectangle {
                                                width: 12
                                                height: 12
                                                radius: 6
                                                color: "#FFA500" // Orange for warning
                                            }
                                            Text { text: "Voltage Level Low" }
                                        }
                                    }
                                }
                            }
                        }
                        
                        // RAILS TAB
                        Item {
                            // Use Column instead of ColumnLayout to have better control over positioning
                            Column {
                                anchors.fill: parent
                                anchors.topMargin: 10
                                spacing: 20
                                
                                // Top Rail section
                                Rectangle {
                                    width: parent.width
                                    height: childrenRect.height + 20 // Adjust height based on content
                                    color: "#F8F8F8"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    radius: 4
                                    
                                    Column {
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 10
                                        spacing: 10
                                        
                                        // Section Title
                                        Text {
                                            text: "Top Rail"
                                            font.bold: true
                                            font.pixelSize: 16
                                        }
                                        
                                        // Top Rail Data
                                        Grid {
                                            width: parent.width
                                            columns: 4
                                            spacing: 15
                                            
                                            Text { text: "Position:"; font.bold: true }
                                            Text { text: teensyController.all_status.top_rail_position.toFixed(0) + " cnt" }
                                            Text { text: "Speed:"; font.bold: true }
                                            Text { text: teensyController.all_status.top_rail_speed.toFixed(0) + " m/s" }
                                            
                                            Text { text: "Current:"; font.bold: true }
                                            Text { text: teensyController.all_status.top_rail_current.toFixed(0) + " A" }

                                        }
                                    }
                                }
        
                                // Arm Rail section - same structure as Top Rail
                                Rectangle {
                                    width: parent.width
                                    height: childrenRect.height + 20
                                    color: "#F8F8F8"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    radius: 4
                                    
                                    Column {
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 10
                                        spacing: 10
                                        
                                        Text {
                                            text: "Arm Rail"
                                            font.bold: true
                                            font.pixelSize: 16
                                        }
                                        
                                        Grid {
                                            width: parent.width
                                            columns: 4
                                            spacing: 15
                                            
                                            Text { text: "Position:"; font.bold: true }
                                            Text { text: teensyController.all_status.arm_rail_position.toFixed(0) + " m" }
                                            Text { text: "Speed:"; font.bold: true }
                                            Text { text: teensyController.all_status.arm_rail_speed.toFixed(0) + " m/s" }
                                            
                                            Text { text: "Current:"; font.bold: true }
                                            Text { text: teensyController.all_status.arm_rail_current.toFixed(0) + " A" }
                                            Text { text: "Extension:"; font.bold: true }
                                            Text { text: teensyController.all_status.arm_extension_dist.toFixed(0) + " mm" }

                                            Text { text: "Sensor:"; font.bold: true }
                                            Text { text: teensyController.all_status.arm_sensor_dist.toFixed(0) + " mm" }
                                        }
                                    }
                                }
                                
                                // You can add more rail-related information sections here
                                // Each would follow the same pattern as above
                                
                                // This Rectangle acts as a spacer that pushes content to the top
                                // It takes up any remaining space at the bottom
                                Rectangle {
                                    width: parent.width
                                    height: 1 // Minimal height
                                    color: "transparent" // Invisible
                                    Layout.fillHeight: true // Takes up remaining space
                                }
                            }
                        }
                        
                        // PROPELLERS TAB
                        Item {
                            // Use Column for better vertical control
                            Column {
                                anchors.fill: parent
                                anchors.topMargin: 10
                                spacing: 15
                                
                                // Propeller headers
                                Rectangle {
                                    width: parent.width
                                    height: 40
                                    color: "#F8F8F8"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    radius: 4
                                    
                                    Row {
                                        anchors.fill: parent
                                        
                                        // Left propeller header
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Text {
                                                anchors.centerIn: parent
                                                text: "Left Propeller"
                                                font.bold: true
                                                font.pixelSize: 16
                                            }
                                            
                                            // Vertical divider
                                            Rectangle {
                                                anchors.right: parent.right
                                                width: 1
                                                height: parent.height
                                                color: "#DDDDDD"
                                            }
                                        }
                                        
                                        // Right propeller header
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Text {
                                                anchors.centerIn: parent
                                                text: "Right Propeller"
                                                font.bold: true
                                                font.pixelSize: 16
                                            }
                                        }
                                    }
                                }
                                
                                // Position row
                                Rectangle {
                                    width: parent.width
                                    height: 40
                                    color: "white"
                                    border.color: "#EEEEEE"
                                    border.width: 1
                                    
                                    Row {
                                        anchors.fill: parent
                                        
                                        // Left position
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "Position:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: teensyController.all_status.left_prop_position.toFixed(0) + "°"
                                                }
                                            }
                                            
                                            // Vertical divider
                                            Rectangle {
                                                anchors.right: parent.right
                                                width: 1
                                                height: parent.height
                                                color: "#EEEEEE"
                                            }
                                        }
                                        
                                        // Right position
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "Position:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: teensyController.all_status.right_prop_position.toFixed(0) + "°"
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // PWM row
                                Rectangle {
                                    width: parent.width
                                    height: 40
                                    color: index % 2 ? "#F9F9F9" : "white"
                                    border.color: "#EEEEEE"
                                    border.width: 1
                                    
                                    Row {
                                        anchors.fill: parent
                                        
                                        // Left PWM
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "PWM:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: teensyController.all_status.left_prop_pwm.toFixed(0)
                                                }
                                            }
                                            
                                            // Vertical divider
                                            Rectangle {
                                                anchors.right: parent.right
                                                width: 1
                                                height: parent.height
                                                color: "#EEEEEE"
                                            }
                                        }
                                        
                                        // Right PWM
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "PWM:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: teensyController.all_status.right_prop_pwm.toFixed(0)
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Current row
                                Rectangle {
                                    width: parent.width
                                    height: 40
                                    color: "white"
                                    border.color: "#EEEEEE"
                                    border.width: 1
                                    
                                    Row {
                                        anchors.fill: parent
                                        
                                        // Left Current
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "Current:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: "2.5 A"
                                                }
                                            }
                                            
                                            // Vertical divider
                                            Rectangle {
                                                anchors.right: parent.right
                                                width: 1
                                                height: parent.height
                                                color: "#EEEEEE"
                                            }
                                        }
                                        
                                        // Right Current
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "Current:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: "2.3 A"
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Temperature row
                                Rectangle {
                                    width: parent.width
                                    height: 40
                                    color: index % 2 ? "#F9F9F9" : "white"
                                    border.color: "#EEEEEE"
                                    border.width: 1
                                    
                                    Row {
                                        anchors.fill: parent
                                        
                                        // Left Temperature
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "Temperature:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: "34 °C"
                                                }
                                            }
                                            
                                            // Vertical divider
                                            Rectangle {
                                                anchors.right: parent.right
                                                width: 1
                                                height: parent.height
                                                color: "#EEEEEE"
                                            }
                                        }
                                        
                                        // Right Temperature
                                        Rectangle {
                                            width: parent.width / 2
                                            height: parent.height
                                            color: "transparent"
                                            
                                            Row {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text {
                                                    text: "Temperature:"
                                                    font.bold: true
                                                }
                                                
                                                Text {
                                                    text: "35 °C"
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Visual representation of propellers (optional enhancement)
                                Rectangle {
                                    width: parent.width
                                    height: 120
                                    color: "#F8F8F8"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    radius: 4
                                    visible: true // Set to false if you don't want this visualization
                                    
                                    Row {
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        spacing: 10
                                        
                                        // Left propeller visualization
                                        Rectangle {
                                            width: parent.width / 2 - 5
                                            height: parent.height
                                            color: "white"
                                            radius: 4
                                            
                                            Rectangle {
                                                anchors.centerIn: parent
                                                width: 80
                                                height: 80
                                                radius: 40
                                                color: "#EEEEEE"
                                                border.color: "#DDDDDD"
                                                border.width: 1
                                                
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 70
                                                    height: 6
                                                    color: "#666666"
                                                    transform: Rotation {
                                                        origin.x: 35
                                                        origin.y: 3
                                                        angle: teensyController.all_status.left_prop_position + 90
                                                    }
                                                }
                                                
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 10
                                                    height: 10
                                                    radius: 5
                                                    color: "#999999"
                                                }
                                            }
                                        }
                                        
                                        // Right propeller visualization
                                        Rectangle {
                                            width: parent.width / 2 - 5
                                            height: parent.height
                                            color: "white"
                                            radius: 4
                                            
                                            Rectangle {
                                                anchors.centerIn: parent
                                                width: 80
                                                height: 80
                                                radius: 40
                                                color: "#EEEEEE"
                                                border.color: "#DDDDDD"
                                                border.width: 1
                                                
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 70
                                                    height: 6
                                                    color: "#666666"
                                                    transform: Rotation {
                                                        origin.x: 35
                                                        origin.y: 3
                                                        angle: teensyController.all_status.right_prop_position + 90
                                                    }
                                                }
                                                
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 10
                                                    height: 10
                                                    radius: 5
                                                    color: "#999999"
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Spacer to push all content to the top
                                Item {
                                    width: parent.width
                                    height: 1
                                    Layout.fillHeight: true
                                }
                            }
                        }
                        
                        // IMU TAB
                        Item {
                            // Use Column for better vertical control
                            Column {
                                anchors.fill: parent
                                anchors.topMargin: 10
                                spacing: 15
                                
                                // Orientation section
                                Rectangle {
                                    width: parent.width
                                    height: childrenRect.height + 20
                                    color: "#F8F8F8"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    radius: 4
                                    
                                    Column {
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 10
                                        spacing: 10
                                        
                                        // Section title
                                        Text {
                                            text: "Orientation"
                                            font.bold: true
                                            font.pixelSize: 16
                                        }
                                        
                                        // Data grid
                                        Grid {
                                            width: parent.width
                                            columns: 6
                                            spacing: 15
                                            
                                            Text { text: "Pitch:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_pitch }
                                            Text { text: "Roll:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_roll }
                                            Text { text: "Yaw:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_yaw }
                                        }
                                    }
                                }
                                
                                // Linear Acceleration section
                                Rectangle {
                                    width: parent.width
                                    height: childrenRect.height + 20
                                    color: "#F8F8F8"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    radius: 4
                                    
                                    Column {
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 10
                                        spacing: 10
                                        
                                        // Section title
                                        Text {
                                            text: "Linear Acceleration"
                                            font.bold: true
                                            font.pixelSize: 16
                                        }
                                        
                                        // Data grid
                                        Grid {
                                            width: parent.width
                                            columns: 6
                                            spacing: 15
                                            
                                            Text { text: "X:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_acc_x + " m/s²" }
                                            Text { text: "Y:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_acc_y + " m/s²" }
                                            Text { text: "Z:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_acc_z + " m/s²" }
                                        }
                                        
                                        // Optional: visualization of acceleration
                                        Rectangle {
                                            width: parent.width
                                            height: 60
                                            color: "#FFFFFF"
                                            border.color: "#EEEEEE"
                                            border.width: 1
                                            radius: 3
                                            visible: true // Set to false if not needed
                                            
                                            Row {
                                                anchors.fill: parent
                                                anchors.margins: 5
                                                spacing: 5
                                                
                                                // X-axis
                                                Column {
                                                    width: parent.width / 3 - 4
                                                    height: parent.height
                                                    spacing: 3
                                                    
                                                    Text { 
                                                        text: "X-axis" 
                                                        font.pixelSize: 12
                                                        anchors.horizontalCenter: parent.horizontalCenter
                                                    }
                                                    
                                                    Rectangle {
                                                        width: parent.width
                                                        height: 20
                                                        color: "#F0F0F0"
                                                        radius: 2
                                                        
                                                        Rectangle {
                                                            property real normalizedValue: (parseFloat(teensyController.all_status.imu_acc_x) + 10) / 20
                                                            width: 6
                                                            height: parent.height
                                                            x: Math.max(0, Math.min(parent.width - width, parent.width * normalizedValue - width/2))
                                                            color: "#4285F4"
                                                        }
                                                    }
                                                }
                                                
                                                // Y-axis
                                                Column {
                                                    width: parent.width / 3 - 4
                                                    height: parent.height
                                                    spacing: 3
                                                    
                                                    Text { 
                                                        text: "Y-axis" 
                                                        font.pixelSize: 12
                                                        anchors.horizontalCenter: parent.horizontalCenter
                                                    }
                                                    
                                                    Rectangle {
                                                        width: parent.width
                                                        height: 20
                                                        color: "#F0F0F0"
                                                        radius: 2
                                                        
                                                        Rectangle {
                                                            property real normalizedValue: (parseFloat(teensyController.all_status.imu_acc_y) + 10) / 20
                                                            width: 6
                                                            height: parent.height
                                                            x: Math.max(0, Math.min(parent.width - width, parent.width * normalizedValue - width/2))
                                                            color: "#0F9D58"
                                                        }
                                                    }
                                                }
                                                
                                                // Z-axis
                                                Column {
                                                    width: parent.width / 3 - 4
                                                    height: parent.height
                                                    spacing: 3
                                                    
                                                    Text { 
                                                        text: "Z-axis" 
                                                        font.pixelSize: 12
                                                        anchors.horizontalCenter: parent.horizontalCenter
                                                    }
                                                    
                                                    Rectangle {
                                                        width: parent.width
                                                        height: 20
                                                        color: "#F0F0F0"
                                                        radius: 2
                                                        
                                                        Rectangle {
                                                            property real normalizedValue: (parseFloat(teensyController.all_status.imu_acc_z) + 10) / 20
                                                            width: 6
                                                            height: parent.height
                                                            x: Math.max(0, Math.min(parent.width - width, parent.width * normalizedValue - width/2))
                                                            color: "#DB4437"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Angular Velocity section
                                Rectangle {
                                    width: parent.width
                                    height: childrenRect.height + 20
                                    color: "#F8F8F8"
                                    border.color: "#DDDDDD"
                                    border.width: 1
                                    radius: 4
                                    
                                    Column {
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.top: parent.top
                                        anchors.margins: 10
                                        spacing: 10
                                        
                                        // Section title
                                        Text {
                                            text: "Angular Velocity"
                                            font.bold: true
                                            font.pixelSize: 16
                                        }
                                        
                                        // Data grid
                                        Grid {
                                            width: parent.width
                                            columns: 6
                                            spacing: 15
                                            
                                            Text { text: "X:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_angular_acc_x + " rad/s" }
                                            Text { text: "Y:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_angular_acc_y + " rad/s" }
                                            Text { text: "Z:"; font.bold: true }
                                            Text { text: teensyController.all_status.imu_angular_acc_z + " rad/s" }
                                        }
                                        
                                        // Optional: 3D orientation visualization placeholder
                                        Rectangle {
                                            width: parent.width
                                            height: 120
                                            color: "#FFFFFF"
                                            border.color: "#EEEEEE"
                                            border.width: 1
                                            radius: 3
                                            visible: true // Set to false if not needed
                                            
                                            Column {
                                                anchors.centerIn: parent
                                                spacing: 10
                                                
                                                Text { 
                                                    text: "3D Orientation" 
                                                    font.pixelSize: 14
                                                    font.bold: true
                                                    anchors.horizontalCenter: parent.horizontalCenter
                                                }
                                                
                                                Row {
                                                    spacing: 20
                                                    
                                                    // Simple cube representation
                                                    Rectangle {
                                                        width: 80
                                                        height: 80
                                                        color: "#EEEEEE"
                                                        border.color: "#CCCCCC"
                                                        border.width: 1
                                                        
                                                        Rectangle {
                                                            anchors.centerIn: parent
                                                            width: 50
                                                            height: 50
                                                            color: "#DDDDDD"
                                                            transform: [
                                                                Rotation {
                                                                    origin.x: 25; origin.y: 25
                                                                    angle: teensyController.all_status.imu_roll
                                                                    axis { x: 1; y: 0; z: 0 }
                                                                },
                                                                Rotation {
                                                                    origin.x: 25; origin.y: 25
                                                                    angle: teensyController.all_status.imu_pitch
                                                                    axis { x: 0; y: 1; z: 0 }
                                                                },
                                                                Rotation {
                                                                    origin.x: 25; origin.y: 25
                                                                    angle: teensyController.all_status.imu_yaw
                                                                    axis { x: 0; y: 0; z: 1 }
                                                                }
                                                            ]
                                                            
                                                            // X-axis indicator (red)
                                                            Rectangle {
                                                                anchors.centerIn: parent
                                                                height: 2
                                                                width: 30
                                                                color: "#DB4437" // Red
                                                            }
                                                            
                                                            // Y-axis indicator (green)
                                                            Rectangle {
                                                                anchors.centerIn: parent
                                                                width: 2
                                                                height: 30
                                                                color: "#0F9D58" // Green
                                                            }
                                                        }
                                                    }
                                                    
                                                    // Values display
                                                    Column {
                                                        spacing: 5
                                                        
                                                        Text { text: "Pitch: " + teensyController.all_status.imu_pitch + "°" }
                                                        Text { text: "Roll: " + teensyController.all_status.imu_roll + "°" }
                                                        Text { text: "Yaw: " + teensyController.all_status.imu_yaw + "°" }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Spacer to push content to top
                                Item {
                                    width: parent.width
                                    height: 1
                                    Layout.fillHeight: true
                                }
                            }
                        }

                        // Spray Gun TAB
                        Item {
                            // Use Column instead of ColumnLayout to have better control over positioning
                            Column {
                                anchors.fill: parent
                                anchors.topMargin: 10
                                spacing: 20
                                
                                GridLayout {
                                    columns: 2
                                    rowSpacing: 10
                                    columnSpacing: 20
                                    Layout.fillHeight: true
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignTop

                                    Label { text: "Pitch:"; font.bold: true }
                                    Label { 
                                        text: teensyController.all_status.spray_gun_pitch.toFixed(1) + "°"
                                    }

                                    Label { text: "Motor Angle:"; font.bold: true }
                                    Label { 
                                        text: teensyController.all_status.spray_gun_motor_angle.toFixed(1) + "°"
                                    }

                                    Label { text: "Motor Current:"; font.bold: true }
                                    Label { 
                                        text: teensyController.all_status.spray_gun_motor_current.toFixed(1) + "°"
                                    }

                                    Label { text: "Motor Temperature:"; font.bold: true }
                                    Label { 
                                        text: teensyController.all_status.spray_gun_motor_temp.toFixed(1) + "°"
                                    }

                                    Label { text: "Pitch:"; font.bold: true }
                                    Label { 
                                        text: teensyController.all_status.spray_gun_spray_gun_trigger? "Pressed" : "Released"
                                        color: teensyController.all_status.spray_gun_spray_gun_trigger ? "green" : "gray"
                                    }
                                }
                                
                                // You can add more rail-related information sections here
                                // Each would follow the same pattern as above
                                
                                // This Rectangle acts as a spacer that pushes content to the top
                                // It takes up any remaining space at the bottom
                                Rectangle {
                                    width: parent.width
                                    height: 1 // Minimal height
                                    color: "transparent" // Invisible
                                    Layout.fillHeight: true // Takes up remaining space
                                }
                            }
                        }
                    }
                }
            }
        }

        // Right Side: Wheel Status
        Rectangle {
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                Label {
                    text: "Wheel Status"
                    font.pixelSize: 24
                    font.bold: true
                }

                // Input Status Display
                GridLayout {
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 20
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    Label { text: "Wheel Connected:"; font.bold: true }
                    Label { 
                        text: wheelController.available ? "Connected" : "Disconnected"
                        color: wheelController.available ? "green" : "red"
                    }

                    Label { text: "Wheel Enabled:"; font.bold: true }
                    Label { 
                        text: wheelController.enabled ? "Enabled" : "Disabled"
                        color: wheelController.enabled ? "green" : "red"
                    }

                    Label { text: "Left Wheel Speed:"; font.bold: true }
                    Label { 
                        text: wheelController.left_wheel_speed.toFixed(1) + " rpm"
                        color: wheelController.left_wheel_speed > 0 ? "green" : "grey"
                    }

                    Label { text: "Right Wheel Speed:"; font.bold: true }
                    Label { 
                        text: wheelController.right_wheel_speed.toFixed(1) + " rpm"
                        color: wheelController.right_wheel_speed > 0 ? "green" : "grey"
                    }
                    Label { text: "Left Wheel Current:"; font.bold: true }
                    Label { 
                        text: wheelController.left_wheel_current.toFixed(1) + " A"
                        color: wheelController.left_wheel_current > 0 ? "green" : "grey"
                    }

                    Label { text: "Right Wheel Current:"; font.bold: true }
                    Label { 
                        text: wheelController.right_wheel_current.toFixed(1) + " A"
                        color: wheelController.right_wheel_current > 0 ? "green" : "grey"
                    }

                    Label { text: "Left Wheel Travel:"; font.bold: true }
                    Label { 
                        text: wheelController.left_wheel_position.toFixed(0) + " mm"
                        color: wheelController.left_wheel_position > 0 ? "green" : "grey"
                    }

                    Label { text: "Right Wheel Travel:"; font.bold: true }
                    Label { 
                        text: wheelController.right_wheel_position.toFixed(0) + " mm"
                        color: wheelController.right_wheel_position > 0 ? "green" : "grey"
                    }


                }
            }
        }
    }
}