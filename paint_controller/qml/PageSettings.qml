import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: settingsMenu
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#F5F5F5"
    
    property string currentPage: "main" // "main", "winch", "wheels", "camera", "arm"
    property real winchMaxSpeed: 50.0
    property bool winchTorqueLimitEnabled: true
    property real winchTorqueLimit: 75.0
    property var pidValues: [1.0, 0.5, 0.1, 0.0]  // P, I, D, Feedforward
    property var coordinateValues: [10.5, 25.3, -5.2, 45.0, 90.0]  // X, Y, Z, Pitch, Yaw
    
    // Settings Item Component
    component SettingsItem: Rectangle {
        property string title: ""
        property string subtitle: ""
        property string icon: ""
        property bool showToggle: false
        property bool toggleValue: false
        property bool showArrow: true
        property string targetPage: ""
        
        signal clicked()
        signal toggled(bool value)
        
        width: parent.width
        height: subtitle !== "" ? 72 : 56
        color: mouseArea.pressed ? "#E0E0E0" : "white"
        
        // Bottom divider
        Rectangle {
            width: parent.width - 72
            height: 1
            color: "#E0E0E0"
            anchors.bottom: parent.bottom
            anchors.right: parent.right
        }
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 16
            
            // Icon
            Text {
                text: icon
                font.pixelSize: 24
                color: "#757575"
                Layout.preferredWidth: 32
            }
            
            // Text content
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                
                Text {
                    text: title
                    font.pixelSize: 16
                    color: "#212121"
                    Layout.fillWidth: true
                }
                
                Text {
                    visible: subtitle !== ""
                    text: subtitle
                    font.pixelSize: 14
                    color: "#757575"
                    Layout.fillWidth: true
                }
            }
            
            // Toggle Switch
            Switch {
                visible: showToggle
                checked: toggleValue
                Layout.preferredWidth: 52
                
                onToggled: parent.parent.parent.toggled(checked)
                
                indicator: Rectangle {
                    implicitWidth: 52
                    implicitHeight: 26
                    radius: 13
                    color: parent.checked ? "#4CAF50" : "#BDBDBD"
                    
                    Rectangle {
                        x: parent.parent.checked ? parent.width - width - 2 : 2
                        y: 2
                        width: 22
                        height: 22
                        radius: 11
                        color: "white"
                        
                        Behavior on x {
                            NumberAnimation { duration: 150 }
                        }
                    }
                }
            }
            
            // Arrow
            Text {
                visible: showArrow && !showToggle
                text: "❯"
                font.pixelSize: 14
                color: "#9E9E9E"
                Layout.preferredWidth: 16
            }
        }
        
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            enabled: !showToggle
            onClicked: {
                if (targetPage !== "") {
                    settingsMenu.currentPage = targetPage
                }
                parent.clicked()
            }
        }
    }
    
    // Settings Category Component
    component SettingsCategory: Rectangle {
        property string title: ""
        
        width: parent.width
        height: 48
        color: "#F5F5F5"
        
        Text {
            text: title.toUpperCase()
            anchors.left: parent.left
            anchors.leftMargin: 72
            anchors.verticalCenter: parent.verticalCenter
            font.pixelSize: 18
            font.weight: Font.Medium
            color: "#3F51B5"
        }
    }
    
    // Detailed Setting Item Component
    component DetailSettingItem: Rectangle {
        property string title: ""
        property string subtitle: ""
        property bool showSlider: false
        property bool showToggle: false
        property bool showSpinBox: false
        property bool showMultipleValues: false
        property bool showActionButton: false
        property bool showMultipleInputs: false
        property real minValue: 0
        property real maxValue: 100
        property real currentValue: 50
        property bool toggleValue: false
        property string unit: ""
        property var valueLabels: []  // ["X", "Y", "Z", "W"] for multiple values
        property var currentValues: []  // [1.0, 2.0, 3.0, 4.0] current values
        property var inputValues: []  // Temporary input values before applying
        property string buttonText: "Execute"
        property string buttonColor: "#3F51B5"
        property string applyButtonText: "Apply"
        
        signal valueChanged(real value)
        signal toggled(bool value)
        signal multipleValuesChanged(var values)
        signal actionButtonClicked()
        signal applyInputValues(var values)
        
        width: parent.width
        height: {
            if (showMultipleValues) return 120 + (valueLabels.length * 40)
            if (showMultipleInputs) return 140 + (valueLabels.length * 50)
            if (showActionButton) return 120
            if (showSlider || showSpinBox) return 96
            return 72
        }
        color: "white"
        
        // Bottom divider
        Rectangle {
            width: parent.width - 32
            height: 1
            color: "#E0E0E0"
            anchors.bottom: parent.bottom
            anchors.right: parent.right
        }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 8
            
            // Title row
            RowLayout {
                Layout.fillWidth: true
                
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    
                    Text {
                        text: title
                        font.pixelSize: 16
                        color: "#212121"
                    }
                    
                    Text {
                        visible: subtitle !== ""
                        text: subtitle
                        font.pixelSize: 14
                        color: "#757575"
                    }
                }
                
                // Toggle Switch
                Switch {
                    visible: showToggle
                    checked: toggleValue
                    Layout.preferredWidth: 52
                    
                    onToggled: parent.parent.parent.toggled(checked)
                    
                    indicator: Rectangle {
                        implicitWidth: 52
                        implicitHeight: 26
                        radius: 13
                        color: parent.checked ? "#4CAF50" : "#BDBDBD"
                        
                        Rectangle {
                            x: parent.parent.checked ? parent.width - width - 2 : 2
                            y: 2
                            width: 22
                            height: 22
                            radius: 11
                            color: "white"
                            
                            Behavior on x {
                                NumberAnimation { duration: 150 }
                            }
                        }
                    }
                }
                
                // SpinBox for numeric input
                SpinBox {
                    visible: showSpinBox
                    from: minValue * 10
                    to: maxValue * 10
                    value: currentValue * 10
                    stepSize: 10
                    Layout.preferredWidth: 120
                    
                    property int decimals: 1
                    property real realValue: value / 10
                    
                    validator: DoubleValidator {
                        bottom: Math.min(parent.from, parent.to)
                        top: Math.max(parent.from, parent.to)
                    }
                    
                    textFromValue: function(value, locale) {
                        return Number(value / 10).toLocaleString(locale, 'f', decimals) + " " + unit
                    }
                    
                    valueFromText: function(text, locale) {
                        return Number.fromLocaleString(locale, text.replace(unit, "").trim()) * 10
                    }
                    
                    onValueChanged: parent.parent.parent.valueChanged(realValue)
                }
            }
            
            // Multiple Values Input with Apply Button
            ColumnLayout {
                visible: showMultipleInputs
                Layout.fillWidth: true
                spacing: 12
                
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 12
                    
                    Repeater {
                        model: valueLabels.length
                        
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            
                            Text {
                                text: valueLabels[index] + ":"
                                font.pixelSize: 14
                                color: "#757575"
                                Layout.preferredWidth: 50
                            }
                            
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                border.color: textInput.activeFocus ? "#3F51B5" : "#BDBDBD"
                                border.width: textInput.activeFocus ? 2 : 1
                                radius: 4
                                color: "white"
                                
                                Behavior on border.color {
                                    ColorAnimation { duration: 150 }
                                }
                                
                                TextInput {
                                    id: textInput
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    text: {
                                        if (inputValues.length > index) {
                                            return inputValues[index].toString()
                                        } else if (currentValues.length > index) {
                                            return currentValues[index].toString()
                                        }
                                        return "0"
                                    }
                                    font.pixelSize: 14
                                    color: "#212121"
                                    selectByMouse: true
                                    selectionColor: "#3F51B5"
                                    verticalAlignment: TextInput.AlignVCenter
                                    
                                    // Numeric input validation
                                    validator: DoubleValidator {
                                        bottom: minValue
                                        top: maxValue
                                        decimals: 3
                                    }
                                    
                                    // Handle focus for touch devices
                                    onActiveFocusChanged: {
                                        if (activeFocus) {
                                            // On touch devices, this would trigger virtual keyboard
                                            selectAll()
                                        }
                                    }
                                    
                                    onTextChanged: {
                                        // Update temporary input values
                                        var newInputValues = inputValues.slice() || currentValues.slice()
                                        while (newInputValues.length <= index) {
                                            newInputValues.push(0)
                                        }
                                        
                                        var numValue = parseFloat(text)
                                        if (!isNaN(numValue)) {
                                            newInputValues[index] = numValue
                                            inputValues = newInputValues
                                        }
                                    }
                                    
                                    // Handle Enter key
                                    Keys.onReturnPressed: {
                                        focus = false
                                    }
                                    
                                    // Handle Tab key to move to next field
                                    Keys.onTabPressed: {
                                        if (index < valueLabels.length - 1) {
                                            parent.parent.parent.children[index + 1].children[1].children[0].focus = true
                                        }
                                    }
                                }
                                
                                // Unit label
                                Text {
                                    visible: unit !== ""
                                    text: unit
                                    anchors.right: parent.right
                                    anchors.rightMargin: 8
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.pixelSize: 12
                                    color: "#757575"
                                }
                                
                                // Touch-friendly tap area
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        textInput.focus = true
                                        textInput.forceActiveFocus()
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Apply and Reset buttons
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    
                    Button {
                        text: applyButtonText
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        
                        background: Rectangle {
                            color: parent.pressed ? Qt.darker("#4CAF50", 1.2) : "#4CAF50"
                            radius: 6
                            
                            Behavior on color {
                                ColorAnimation { duration: 150 }
                            }
                        }
                        
                        contentItem: Text {
                            text: parent.text
                            font.pixelSize: 14
                            font.weight: Font.Medium
                            color: "white"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        onClicked: {
                            var finalValues = inputValues.slice()
                            // Ensure we have values for all fields
                            while (finalValues.length < valueLabels.length) {
                                finalValues.push(0)
                            }
                            parent.parent.parent.applyInputValues(finalValues)
                        }
                    }
                    
                    Button {
                        text: "Reset"
                        Layout.preferredWidth: 80
                        Layout.preferredHeight: 40
                        
                        background: Rectangle {
                            color: parent.pressed ? Qt.darker("#757575", 1.2) : "#757575"
                            radius: 6
                            
                            Behavior on color {
                                ColorAnimation { duration: 150 }
                            }
                        }
                        
                        contentItem: Text {
                            text: parent.text
                            font.pixelSize: 14
                            color: "white"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        onClicked: {
                            // Reset input fields to current values
                            inputValues = currentValues.slice()
                            // Force update of text fields
                            for (var i = 0; i < valueLabels.length; i++) {
                                var textField = parent.parent.children[0].children[i].children[1].children[0]
                                if (textField && currentValues.length > i) {
                                    textField.text = currentValues[i].toString()
                                }
                            }
                        }
                    }
                }
            }
            
            // Multiple Values Input (original SpinBox version)
            GridLayout {
                visible: showMultipleValues
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 16
                rowSpacing: 8
                
                Repeater {
                    model: valueLabels.length
                    
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        
                        Text {
                            text: valueLabels[index] + ":"
                            font.pixelSize: 14
                            color: "#757575"
                            Layout.preferredWidth: 30
                        }
                        
                        SpinBox {
                            from: minValue * 100
                            to: maxValue * 100
                            value: (currentValues[index] || 0) * 100
                            stepSize: 10
                            Layout.fillWidth: true
                            
                            property int decimals: 2
                            property real realValue: value / 100
                            
                            textFromValue: function(value, locale) {
                                return Number(value / 100).toLocaleString(locale, 'f', decimals) + " " + unit
                            }
                            
                            valueFromText: function(text, locale) {
                                return Number.fromLocaleString(locale, text.replace(unit, "").trim()) * 100
                            }
                            
                            onValueChanged: {
                                var newValues = currentValues.slice()  // Copy array
                                newValues[index] = realValue
                                parent.parent.parent.parent.multipleValuesChanged(newValues)
                            }
                        }
                    }
                }
            }
            
            // Action Button
            Button {
                visible: showActionButton
                text: buttonText
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                
                background: Rectangle {
                    color: parent.pressed ? Qt.darker(buttonColor, 1.2) : buttonColor
                    radius: 8
                    
                    Behavior on color {
                        ColorAnimation { duration: 150 }
                    }
                }
                
                contentItem: Text {
                    text: parent.text
                    font.pixelSize: 16
                    font.weight: Font.Medium
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                onClicked: parent.parent.actionButtonClicked()
            }
            
            // Slider
            RowLayout {
                visible: showSlider
                Layout.fillWidth: true
                spacing: 16
                
                Text {
                    text: minValue + unit
                    font.pixelSize: 12
                    color: "#757575"
                }
                
                Slider {
                    Layout.fillWidth: true
                    from: minValue
                    to: maxValue
                    value: currentValue
                    
                    onValueChanged: parent.parent.parent.valueChanged(value)
                    
                    background: Rectangle {
                        x: parent.leftPadding
                        y: parent.topPadding + parent.availableHeight / 2 - height / 2
                        implicitWidth: 200
                        implicitHeight: 4
                        width: parent.availableWidth
                        height: implicitHeight
                        radius: 2
                        color: "#BDBDBD"
                        
                        Rectangle {
                            width: parent.parent.visualPosition * parent.width
                            height: parent.height
                            color: "#3F51B5"
                            radius: 2
                        }
                    }
                    
                    handle: Rectangle {
                        x: parent.leftPadding + parent.visualPosition * (parent.availableWidth - width)
                        y: parent.topPadding + parent.availableHeight / 2 - height / 2
                        implicitWidth: 20
                        implicitHeight: 20
                        radius: 10
                        color: parent.pressed ? "#303F9F" : "#3F51B5"
                    }
                }
                
                Text {
                    text: maxValue + unit
                    font.pixelSize: 12
                    color: "#757575"
                }
            }
        }
    }
    
    // Header Component
    component SettingsHeader: Rectangle {
        property string title: "Settings"
        property bool showBack: false
        
        Layout.fillWidth: true
        Layout.preferredHeight: 56
        color: "#3F51B5"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            
            Text {
                visible: showBack
                text: "⬅"
                font.pixelSize: 24
                color: "white"
                Layout.preferredWidth: 32
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: settingsMenu.currentPage = "main"
                }
            }
            
            Text {
                text: title
                font.pixelSize: 20
                font.weight: Font.Medium
                color: "white"
                Layout.fillWidth: true
            }
        }
    }
    
    StackLayout {
        anchors.fill: parent
        currentIndex: {
            switch(settingsMenu.currentPage) {
                case "main": return 0
                case "winch": return 1
                case "wheels": return 2
                case "camera": return 3
                case "arm": return 4
                default: return 0
            }
        }
        
        // Main Settings Page
        ScrollView {
            contentWidth: availableWidth
            clip: true
            
            ColumnLayout {
                width: parent.width
                spacing: 0
                
                SettingsHeader {
                    title: "Settings"
                    showBack: false
                }
                
                // Spacer
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    color: "#F5F5F5"
                }
                
                // Device Settings Category
                SettingsCategory {
                    title: "Base Settings"
                }
                
                SettingsItem {
                    title: "Winch"
                    subtitle: "Max speed: " + settingsMenu.winchMaxSpeed.toFixed(1) + " RPM"
                    targetPage: "winch"
                }
                
                SettingsItem {
                    title: "Wheels"
                    subtitle: "Wheel configuration and speed limits"
                    targetPage: "wheels"
                }
                
                SettingsItem {
                    title: "Camera"
                    subtitle: "Camera settings and calibration"
                    targetPage: "camera"
                }
                
                // Network Category
                SettingsCategory {
                    title: "End Effector Settings"
                }
                
                SettingsItem {
                    title: "Arm"
                    subtitle: "Retractable Arm configuration"
                    targetPage: "arm"
                }
                   
                // Bottom spacing
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 20
                    color: "transparent"
                }
            }
        }
        
        // Winch Settings Page
        ScrollView {
            contentWidth: availableWidth
            clip: true
            
            ColumnLayout {
                width: parent.width
                spacing: 0
                
                SettingsHeader {
                    title: "Winch Settings"
                    showBack: true
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    color: "#F5F5F5"
                }
                
                DetailSettingItem {
                    title: "Maximum Speed"
                    subtitle: "Set the maximum winch speed"
                    showSlider: true
                    minValue: 10
                    maxValue: 100
                    currentValue: settingsMenu.winchMaxSpeed
                    unit: " RPM"
                    
                    onValueChanged: function(value) {
                        settingsMenu.winchMaxSpeed = value
                    }
                }
                
                DetailSettingItem {
                    title: "Torque Limit"
                    subtitle: "Enable automatic torque limiting"
                    showToggle: true
                    toggleValue: settingsMenu.winchTorqueLimitEnabled
                    
                    onToggled: function(value) {
                        settingsMenu.winchTorqueLimitEnabled = value
                    }
                }
                
                DetailSettingItem {
                    title: "Torque Threshold"
                    subtitle: "Maximum torque before limiting"
                    showSpinBox: true
                    minValue: 25
                    maxValue: 100
                    currentValue: settingsMenu.winchTorqueLimit
                    unit: "%"
                    
                    onValueChanged: function(value) {
                        settingsMenu.winchTorqueLimit = value
                    }
                }
                
                DetailSettingItem {
                    title: "Emergency Stop"
                    subtitle: "Enable emergency stop functionality"
                    showToggle: true
                    toggleValue: true
                    
                    onToggled: function(value) {
                        console.log("Emergency stop:", value)
                    }
                }
                
                DetailSettingItem {
                    title: "PID Controller"
                    subtitle: "Set P, I, D, and Feedforward values"
                    showMultipleValues: true
                    valueLabels: ["P", "I", "D", "FF"]
                    currentValues: settingsMenu.pidValues
                    minValue: -10
                    maxValue: 10
                    unit: ""
                    
                    onMultipleValuesChanged: function(values) {
                        settingsMenu.pidValues = values
                        console.log("PID values updated:", values)
                    }
                }
                
                DetailSettingItem {
                    title: "Calibrate Winch"
                    subtitle: "Run winch calibration procedure"
                    showActionButton: true
                    buttonText: "Start Calibration"
                    buttonColor: "#FF9800"
                    
                    onActionButtonClicked: {
                        console.log("Starting winch calibration...")
                        // Call your backend function here
                        // Example: backendController.calibrateWinch()
                    }
                }
                
                DetailSettingItem {
                    title: "Reset to Factory Defaults"
                    subtitle: "Warning: This will reset all winch settings"
                    showActionButton: true
                    buttonText: "Reset Settings"
                    buttonColor: "#F44336"
                    
                    onActionButtonClicked: {
                        console.log("Resetting winch to factory defaults...")
                        // Call your backend reset function
                        settingsMenu.winchMaxSpeed = 50.0
                        settingsMenu.winchTorqueLimitEnabled = true
                        settingsMenu.winchTorqueLimit = 75.0
                        settingsMenu.pidValues = [1.0, 0.5, 0.1, 0.0]
                    }
                }
            }
        }
        
        // Placeholder pages for other settings
        ScrollView {
            contentWidth: availableWidth
            clip: true
            
            ColumnLayout {
                width: parent.width
                spacing: 0
                
                SettingsHeader { 
                    title: "Wheels Settings"
                    showBack: true 
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    color: "#F5F5F5"
                }
                
                DetailSettingItem {
                    title: "Wheel Position"
                    subtitle: "Set target position for all wheels"
                    showMultipleInputs: true
                    valueLabels: ["Front L", "Front R", "Rear L", "Rear R"]
                    currentValues: [0, 0, 0, 0]
                    minValue: -180
                    maxValue: 180
                    unit: "°"
                    applyButtonText: "Set Positions"
                    
                    onApplyInputValues: function(values) {
                        console.log("Wheel positions applied:", values)
                        // Call backend: backendController.setWheelPositions(values)
                    }
                }
                
                DetailSettingItem {
                    title: "Move to Position"
                    subtitle: "Execute wheel movement to set positions"
                    showActionButton: true
                    buttonText: "Move Wheels"
                    buttonColor: "#4CAF50"
                    
                    onActionButtonClicked: {
                        console.log("Moving wheels to position...")
                        // Call backend: backendController.moveWheelsToPosition()
                    }
                }
            }
        }
        
        ScrollView {
            contentWidth: availableWidth
            clip: true
            
            ColumnLayout {
                width: parent.width
                spacing: 0
                
                SettingsHeader { 
                    title: "Camera Settings"
                    showBack: true 
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    color: "#F5F5F5"
                }
                
                DetailSettingItem {
                    title: "Camera Position"
                    subtitle: "Set camera coordinates and orientation"
                    showMultipleInputs: true
                    valueLabels: ["X", "Y", "Z", "Pitch", "Yaw"]
                    currentValues: settingsMenu.coordinateValues
                    minValue: -100
                    maxValue: 100
                    unit: "mm"
                    applyButtonText: "Update Position"
                    
                    onApplyInputValues: function(values) {
                        settingsMenu.coordinateValues = values
                        console.log("Camera position applied:", values)
                        // Call backend: backendController.setCameraPosition(values)
                    }
                }
                
                DetailSettingItem {
                    title: "Auto Focus"
                    subtitle: "Run automatic camera focus routine"
                    showActionButton: true
                    buttonText: "Start Auto Focus"
                    buttonColor: "#2196F3"
                    
                    onActionButtonClicked: {
                        console.log("Starting camera auto focus...")
                        // Call backend: backendController.startAutoFocus()
                    }
                }
                
                DetailSettingItem {
                    title: "Capture Test Image"
                    subtitle: "Take a test photo with current settings"
                    showActionButton: true
                    buttonText: "Capture Image"
                    buttonColor: "#9C27B0"
                    
                    onActionButtonClicked: {
                        console.log("Capturing test image...")
                        // Call backend: backendController.captureTestImage()
                    }
                }
            }
        }
        
        ScrollView {
            contentWidth: availableWidth
            clip: true
            
            ColumnLayout {
                width: parent.width
                spacing: 0
                
                SettingsHeader { 
                    title: "Arm Settings"
                    showBack: true 
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    color: "#F5F5F5"
                }
                
                DetailSettingItem {
                    title: "Joint Positions"
                    subtitle: "Set target angles for arm joints"
                    showMultipleInputs: true
                    valueLabels: ["Base", "Shoulder", "Elbow", "Wrist"]
                    currentValues: [0, 90, -45, 0]
                    minValue: -180
                    maxValue: 180
                    unit: "°"
                    applyButtonText: "Move Joints"
                    
                    onApplyInputValues: function(values) {
                        console.log("Joint positions applied:", values)
                        // Call backend: backendController.setJointPositions(values)
                    }
                }
                
                DetailSettingItem {
                    title: "Move to Home Position"
                    subtitle: "Return arm to safe home position"
                    showActionButton: true
                    buttonText: "Go Home"
                    buttonColor: "#4CAF50"
                    
                    onActionButtonClicked: {
                        console.log("Moving arm to home position...")
                        // Call backend: backendController.moveArmHome()
                    }
                }
                
                DetailSettingItem {
                    title: "Emergency Stop"
                    subtitle: "Immediately stop all arm movement"
                    showActionButton: true
                    buttonText: "EMERGENCY STOP"
                    buttonColor: "#F44336"
                    
                    onActionButtonClicked: {
                        console.log("EMERGENCY STOP activated!")
                        // Call backend: backendController.emergencyStop()
                    }
                }
            }
        }
    }
}