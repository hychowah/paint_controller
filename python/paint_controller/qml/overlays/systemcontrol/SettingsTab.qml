import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../components/buttons"
import "../../components/panels"
import "../../components/inputs"
import "../../components/popups"

Item {
    id: settingsTab
    
    // Helper function to create setting input field
    function createSettingRow(key, label, currentValue, minVal, maxVal, isFloat) {
        // This is handled inline in the repeater below
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 15
        
        // Header
        Item {
            Layout.fillWidth: true
            height: 32
            
            Text {
                text: "Settings"
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
        
        // Scrollable settings content
        ScrollView {
            id: settingsScrollView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            
            ColumnLayout {
                width: settingsScrollView.width - 20
                spacing: 15
                
                // ==========================================
                // Winch Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "Winch Settings"
                    description: "Configure winch motor parameters"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            // Explicit implicit height for proper sizing
                            implicitHeight: childrenRect.height
                            
                            // Winch Max Speed
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Max Speed (Range: 0 - 100 RPM)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: winchMaxSpeedInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: winchMaxSpeedInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.winch_max_speed_mmps.toFixed(1) : "400.0"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = winchMaxSpeedInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: winchMaxSpeedSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: winchMaxSpeedSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(winchMaxSpeedInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.winch_max_speed_mmps = num
                                                    if (settingsManager.saveSetting("winch_max_speed_mmps")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Winch max speed set to " + num.toFixed(1) + " mm/s"
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                // ==========================================
                // Track Control Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "Track Control"
                    description: "Configure track/wheel speed parameters"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            implicitHeight: childrenRect.height
                            
                            // Track Max Speed
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Max Speed (Range: 5 - 50)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: trackMaxSpeedInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: trackMaxSpeedInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.track_max_speed.toFixed(1) : "25.0"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = trackMaxSpeedInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: trackMaxSpeedSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: trackMaxSpeedSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(trackMaxSpeedInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.track_max_speed = num
                                                    if (settingsManager.saveSetting("track_max_speed")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Track max speed set to " + num.toFixed(1)
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Track Min Speed
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Min Speed (Range: 0 - 30)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: trackMinSpeedInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: trackMinSpeedInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.track_min_speed.toFixed(1) : "15.0"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = trackMinSpeedInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: trackMinSpeedSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: trackMinSpeedSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(trackMinSpeedInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.track_min_speed = num
                                                    if (settingsManager.saveSetting("track_min_speed")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Track min speed set to " + num.toFixed(1)
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Wheel Travel Max Distance
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Wheel Travel Max Distance (Range: 100 - 1000 mm)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: wheelTravelMaxInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: wheelTravelMaxInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.wheel_travel_max.toFixed(0) : "500"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = wheelTravelMaxInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: wheelTravelMaxSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: wheelTravelMaxSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(wheelTravelMaxInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.wheel_travel_max = num
                                                    if (settingsManager.saveSetting("wheel_travel_max")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Wheel travel max set to " + num.toFixed(0) + " mm"
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Wheel Travel Rate
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Wheel Travel Rate (Range: 10 - 500 mm/sec)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: wheelTravelRateInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: wheelTravelRateInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.wheel_travel_rate.toFixed(0) : "100"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = wheelTravelRateInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: wheelTravelRateSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: wheelTravelRateSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(wheelTravelRateInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.wheel_travel_rate = num
                                                    if (settingsManager.saveSetting("wheel_travel_rate")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Wheel travel rate set to " + num.toFixed(0) + " mm/sec"
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Wheel Travel RPM
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Wheel Travel Speed (Range: 50 - 600 RPM)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: wheelTravelRpmInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: wheelTravelRpmInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.wheel_travel_rpm.toString() : "300"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = wheelTravelRpmInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: wheelTravelRpmSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: wheelTravelRpmSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseInt(wheelTravelRpmInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.wheel_travel_rpm = num
                                                    if (settingsManager.saveSetting("wheel_travel_rpm")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Wheel travel speed set to " + num + " RPM"
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                // ==========================================
                // End Effector Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "End Effector"
                    description: "Configure thrust force and valve parameters"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            implicitHeight: childrenRect.height
                            
                            // Thrust Force
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Thrust Force (Range: -1.0 to +1.0)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: thrustForceInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: thrustForceInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.thrust_force.toFixed(2) : "-1.00"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = thrustForceInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: thrustForceSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: thrustForceSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(thrustForceInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.thrust_force = num
                                                    // Also update teensyController for immediate effect
                                                    if (teensyController) {
                                                        teensyController.thrust_force = num
                                                    }
                                                    if (settingsManager.saveSetting("thrust_force")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Thrust force set to " + num.toFixed(2)
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Thrust Ramp Rate
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Thrust Ramp Rate (thrust/second, Range: 0.1 - 10.0)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                Text {
                                    text: "Controls how fast thrust force ramps up/down (1.0 = 0 to max in 1 second)"
                                    color: "#AAAAAA"
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: thrustRampRateInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: thrustRampRateInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.thrust_ramp_rate.toFixed(2) : "1.00"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = thrustRampRateInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: thrustRampRateSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: thrustRampRateSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(thrustRampRateInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    // Clamp to valid range (0.1 - 10.0)
                                                    num = Math.max(0.1, Math.min(10.0, num))
                                                    settingsManager.thrust_ramp_rate = num
                                                    thrustRampRateInput.text = num.toFixed(2)  // Update display with clamped value
                                                    if (settingsManager.saveSetting("thrust_ramp_rate")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Thrust ramp rate set to " + num.toFixed(2)
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Valve Turn Max
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Valve Turn Max (Range: 0 - 10)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: valveTurnMaxInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: valveTurnMaxInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.valve_turn_max.toFixed(1) : "6.0"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = valveTurnMaxInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: valveTurnMaxSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: valveTurnMaxSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseFloat(valveTurnMaxInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.valve_turn_max = num
                                                    if (settingsManager.saveSetting("valve_turn_max")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Valve turn max set to " + num.toFixed(1)
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                // ==========================================
                // Arm Extension Settings Section
                // ==========================================
                SettingsSection {
                    Layout.fillWidth: true
                    title: "Arm Extension Presets"
                    description: "Configure arm retract/extend positions"
                    expanded: true
                    
                    contentItem: Component {
                        ColumnLayout {
                            spacing: 15
                            width: parent ? parent.width : 300
                            implicitHeight: childrenRect.height
                            
                            // Arm Retract Length
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Retract Position (Range: 0 - 1000)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: armRetractInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: armRetractInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.arm_retract_length.toString() : "250"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = armRetractInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: armRetractSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: armRetractSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseInt(armRetractInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.arm_retract_length = num
                                                    if (settingsManager.saveSetting("arm_retract_length")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Arm retract position set to " + num
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Arm Extend Length
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Text {
                                    text: "Extend Position (Range: 0 - 1500)"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 45
                                        color: "#1A1A1A"
                                        border.color: armExtendInput.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        
                                        TextInput {
                                            id: armExtendInput
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            text: settingsManager ? settingsManager.arm_extend_length.toString() : "800"
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            verticalAlignment: TextInput.AlignVCenter
                                            horizontalAlignment: TextInput.AlignRight
                                            selectByMouse: true
                                            
                                            onActiveFocusChanged: {
                                                if (activeFocus) {
                                                    numberPad.targetField = armExtendInput
                                                    numberPad.open()
                                                }
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        width: 70
                                        height: 45
                                        radius: 6
                                        color: armExtendSaveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Save"
                                            color: "#FFFFFF"
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        
                                        MouseArea {
                                            id: armExtendSaveArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                var num = parseInt(armExtendInput.text)
                                                if (!isNaN(num) && settingsManager) {
                                                    settingsManager.arm_extend_length = num
                                                    if (settingsManager.saveSetting("arm_extend_length")) {
                                                        confirmationPopup.messageTitle = "Saved"
                                                        confirmationPopup.messageText = "Arm extend position set to " + num
                                                        confirmationPopup.messageType = "info"
                                                        confirmationPopup.open()
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Bottom spacer
                Item {
                    Layout.fillWidth: true
                    height: 20
                }
            }
        }
    }
    
    // Numpad component for number input
    NumpadNew {
        id: numberPad
    }
    
    // Confirmation popup for settings
    CustomPopup {
        id: confirmationPopup
        width: 400
        height: 180
        dismissDelay: 2000
    }
}
