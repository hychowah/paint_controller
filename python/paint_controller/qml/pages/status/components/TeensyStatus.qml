import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"
import "../../../components/buttons"
import "../../../components/displays"

Rectangle {
    id: teensyStatusRect
    required property var teensyStatus
    color: "#FFFFFF"
    radius: 10

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10
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
                checked: teensyStatusRect.teensyStatus.enabled
                onToggled: {
                    // No revert needed: the switch never self-assigns,
                    // so a rejected request leaves the binding intact.
                    deviceActionHandler.requestTeensyEnabled(checked)
                }
            }

            Label { text: "Relay:"; font.bold: true }
            
            TouchSwitch {
                id: teensyRelayEnableSwitch
                checked: teensyStatusRect.teensyStatus.relayOn
                onToggled: {
                    // No revert needed: the switch never self-assigns,
                    // so a rejected request leaves the binding intact.
                    deviceActionHandler.requestTeensyRelayEnabled(checked)
                }
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
                        Label { text: teensyStatusRect.teensyStatus.voltage.toFixed(1) + " V" }
                        Label { text: "Current:"; font.bold: true }
                        Label { text: teensyStatusRect.teensyStatus.current.toFixed(1) + " A" }
                        
                        Label { text: "Temperature:"; font.bold: true }
                        Label { text: teensyStatusRect.teensyStatus.temperature.toFixed(1) + " °C" }
                        Label { text: "Runtime:"; font.bold: true }
                        Label { text: teensyStatusRect.teensyStatus.runTime.toFixed(0) }
                        
                        Label { text: "Loop Time:"; font.bold: true }
                        Label { text: teensyStatusRect.teensyStatus.loopTime.toFixed(0) + " µs" }
                        Label { text: "Loop Counter:"; font.bold: true }
                        Label { text: teensyStatusRect.teensyStatus.loopTimeCounter.toFixed(0) }
                        
                        Label { text: "Battery:"; font.bold: true }
                        Label { text: calculateBatteryPercentage(teensyStatusRect.teensyStatus.voltage) + "%" }
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
                                    Text { text: teensyStatusRect.teensyStatus.topRailPosition.toFixed(0) + " cnt" }
                                    Text { text: "Speed:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.topRailSpeed.toFixed(0) + " m/s" }
                                    
                                    Text { text: "Current:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.topRailCurrent.toFixed(0) + " A" }
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
                                    Text { text: teensyStatusRect.teensyStatus.armRailPosition.toFixed(0) + " m" }
                                    Text { text: "Speed:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.armRailSpeed.toFixed(0) + " m/s" }
                                    
                                    Text { text: "Current:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.armRailCurrent.toFixed(0) + " A" }
                                    Text { text: "Extension:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.armExtensionDist.toFixed(0) + " mm" }

                                    Text { text: "Sensor:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.armSensorDist.toFixed(0) + " mm" }
                                }
                            }
                        }
                        
                        // This Rectangle acts as a spacer that pushes content to the top
                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "transparent"
                            Layout.fillHeight: true
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
                                            text: teensyStatusRect.teensyStatus.leftPropPosition.toFixed(0) + "°"
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
                                            text: teensyStatusRect.teensyStatus.rightPropPosition.toFixed(0) + "°"
                                        }
                                    }
                                }
                            }
                        }
                        
                        // PWM row
                        Rectangle {
                            width: parent.width
                            height: 40
                            color: "#F9F9F9"
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
                                            text: teensyStatusRect.teensyStatus.leftPropPwm.toFixed(0)
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
                                            text: teensyStatusRect.teensyStatus.rightPropPwm.toFixed(0)
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Visual representation of propellers
                        Rectangle {
                            width: parent.width
                            height: 120
                            color: "#F8F8F8"
                            border.color: "#DDDDDD"
                            border.width: 1
                            radius: 4
                            
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
                                                angle: teensyStatusRect.teensyStatus.leftPropPosition + 90
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
                                                angle: teensyStatusRect.teensyStatus.rightPropPosition + 90
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
                    }
                }
                
                // IMU TAB
                Item {
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
                                
                                Text {
                                    text: "Orientation"
                                    font.bold: true
                                    font.pixelSize: 16
                                }
                                
                                Grid {
                                    width: parent.width
                                    columns: 6
                                    spacing: 15
                                    
                                    Text { text: "Pitch:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuPitch }
                                    Text { text: "Roll:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuRoll }
                                    Text { text: "Yaw:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuYaw }
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
                                
                                Text {
                                    text: "Linear Acceleration"
                                    font.bold: true
                                    font.pixelSize: 16
                                }
                                
                                Grid {
                                    width: parent.width
                                    columns: 6
                                    spacing: 15
                                    
                                    Text { text: "X:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuAccX + " m/s²" }
                                    Text { text: "Y:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuAccY + " m/s²" }
                                    Text { text: "Z:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuAccZ + " m/s²" }
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
                                
                                Text {
                                    text: "Angular Velocity"
                                    font.bold: true
                                    font.pixelSize: 16
                                }
                                
                                Grid {
                                    width: parent.width
                                    columns: 6
                                    spacing: 15
                                    
                                    Text { text: "X:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuAngularAccX + " rad/s" }
                                    Text { text: "Y:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuAngularAccY + " rad/s" }
                                    Text { text: "Z:"; font.bold: true }
                                    Text { text: teensyStatusRect.teensyStatus.imuAngularAccZ + " rad/s" }
                                }
                            }
                        }
                    }
                }

                // Spray Gun TAB
                Item {
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
                                text: teensyStatusRect.teensyStatus.sprayGunPitch.toFixed(1) + "°"
                            }

                            Label { text: "Pitch Motor Angle:"; font.bold: true }
                            Label { 
                                text: teensyStatusRect.teensyStatus.gimbalPitchMotorAngle.toFixed(1) + "°"
                            }

                            Label { text: "Pitch Motor Current:"; font.bold: true }
                            Label { 
                                text: teensyStatusRect.teensyStatus.gimbalPitchMotorCurrent.toFixed(1) + " A"
                            }

                            Label { text: "Pitch Motor Temp:"; font.bold: true }
                            Label { 
                                text: teensyStatusRect.teensyStatus.gimbalPitchMotorTemp.toFixed(1) + " °C"
                            }

                            Label { text: "Roll Motor Angle:"; font.bold: true }
                            Label { 
                                text: teensyStatusRect.teensyStatus.gimbalRollMotorAngle.toFixed(1) + "°"
                            }

                            Label { text: "Roll Motor Current:"; font.bold: true }
                            Label { 
                                text: teensyStatusRect.teensyStatus.gimbalRollMotorCurrent.toFixed(1) + " A"
                            }

                            Label { text: "Roll Motor Temp:"; font.bold: true }
                            Label { 
                                text: teensyStatusRect.teensyStatus.gimbalRollMotorTemp.toFixed(1) + " °C"
                            }

                            Label { text: "Trigger:"; font.bold: true }
                            Label { 
                                text: teensyStatusRect.teensyStatus.sprayGunTrigger ? "Pressed" : "Released"
                                color: teensyStatusRect.teensyStatus.sprayGunTrigger ? "green" : "gray"
                            }
                        }
                    }
                }
            }
        }
    }

    function calculateBatteryPercentage(voltage) {
        // Constants for 7S Li-ion battery
        const maxVoltage = 29.4;  // Fully charged voltage
        const minVoltage = 21.0;  // Discharge cutoff voltage
        
        // Clamp the voltage to the valid range
        const clampedVoltage = Math.max(minVoltage, Math.min(maxVoltage, voltage));
        
        // Calculate the percentage
        const percentage = ((clampedVoltage - minVoltage) / (maxVoltage - minVoltage)) * 100;
        
        // Round to nearest integer
        return Math.round(percentage);
    }
}