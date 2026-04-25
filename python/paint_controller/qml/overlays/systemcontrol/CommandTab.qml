import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "./components"

Item {
    id: commandTab

    // Command definitions with their parameters
    readonly property var commandDefinitions: {
        "Move to Position": {
            description: "Move robot to specific coordinates",
            parameters: [
                { name: "X Position", type: "number", placeholder: "0.0", unit: "m" },
                { name: "Y Position", type: "number", placeholder: "0.0", unit: "m" },
                { name: "Z Position", type: "number", placeholder: "0.0", unit: "m" },
                { name: "Speed", type: "number", placeholder: "1.0", unit: "m/s" }
            ]
        },
        "Set Spray Gun Angle": {
            description: "Configure spray gun angle",
            parameters: [
                { name: "Angle", type: "number", placeholder: "0.0", unit: "degrees" },
                { name: "Speed", type: "number", placeholder: "1.0", unit: "degrees/s" }
            ]
        },
        "Demo": {
            description: "Run demo action",
            parameters: [
                { name: "Gimbal Angle", type: "number", placeholder: "0.0", unit: "degrees" },
                { name: "Gimbal Speed", type: "number", placeholder: "1.0", unit: "degrees/s" },
                { name: "Cable Length", type: "number", placeholder: "1.0", unit: "m" },
                { name: "Cable Speed", type: "number", placeholder: "0.5", unit: "m/s" },
                { name: "Force Y", type: "number", placeholder: "0.0", unit: "N" }
            ]
        },
        "Winch Control": {
            description: "Control winch movement",
            parameters: [
                { name: "Distance", type: "number", placeholder: "0", unit: "mm" },
                { name: "Speed", type: "number", placeholder: "500", unit: "mm/s" },
                { name: "Acceleration", type: "number", placeholder: "30", unit: "RPM/s" }
            ]
        },
        "Frequency Tap": {
            description: "Start Frequency Tap",
            parameters: [
                { name: "Power", type: "number", placeholder: "1.0", unit: "%" },
                { name: "Period", type: "number", placeholder: "1.0", unit: "s" }
            ]
        },
        "Tap Once": {
            description: "Tap once",
            parameters: [
                { name: "Power", type: "number", placeholder: "1.0", unit: "%" }
            ]
        },
        "Extend Arm": {
            description: "Extend the robotic arm",
            parameters: [
                { name: "Length", type: "number", placeholder: "1.0", unit: "mm" }
            ]
        }
    }

    property string selectedCommand: ""
    property var currentParameters: []
    property var parameterValues: ({})
    property bool selectedCommandSupported: selectedCommand !== "" && manualCommandHandler && manualCommandHandler.isCommandSupported(selectedCommand)

    ColumnLayout {
        anchors.fill: parent
        spacing: 20
        
        // Header
        Item {
            Layout.fillWidth: true
            height: 32
            
            Text {
                text: "Command Interface"
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
        
        // Command selection and parameters
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#252A36"
            border.color: "#3A5A8C"
            border.width: 1
            radius: 10
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20
                
                // Command Selection Section
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    Text {
                        text: "Select Command"
                        color: "#FFFFFF"
                        font.pixelSize: 16
                        font.bold: true
                    }
                    
                    // Command Dropdown
                    Rectangle {
                        Layout.fillWidth: true
                        height: 50
                        color: commandDropdown.activeFocus ? "#2A3040" : "#1A1A1A"
                        border.color: commandDropdown.activeFocus ? "#3A5A8C" : "#333333"
                        border.width: 1
                        radius: 8
                        
                        ComboBox {
                            id: commandDropdown
                            anchors.fill: parent
                            model: Object.keys(commandDefinitions)
                            
                            background: Rectangle {
                                color: "transparent"
                            }
                            
                            contentItem: Text {
                                leftPadding: 15
                                rightPadding: commandDropdown.indicator.width + commandDropdown.spacing
                                text: commandDropdown.displayText || "Select a command..."
                                font.pixelSize: 14
                                color: commandDropdown.displayText ? "#FFFFFF" : "#999999"
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            indicator: Text {
                                x: commandDropdown.width - width - 15
                                y: commandDropdown.topPadding + (commandDropdown.availableHeight - height) / 2
                                text: "▼"
                                font.pixelSize: 12
                                color: "#CCCCCC"
                            }
                            
                            popup: Popup {
                                y: commandDropdown.height - 1
                                width: commandDropdown.width
                                implicitHeight: contentItem.implicitHeight
                                padding: 1
                                
                                contentItem: ListView {
                                    clip: true
                                    implicitHeight: contentHeight
                                    model: commandDropdown.popup.visible ? commandDropdown.delegateModel : null
                                    currentIndex: commandDropdown.highlightedIndex
                                    
                                    ScrollIndicator.vertical: ScrollIndicator { }
                                }
                                
                                background: Rectangle {
                                    color: "#1A1A1A"
                                    border.color: "#3A5A8C"
                                    border.width: 1
                                    radius: 8
                                }
                            }
                            
                            delegate: ItemDelegate {
                                width: commandDropdown.width
                                height: 40
                                
                                contentItem: Text {
                                    text: modelData
                                    color: "#FFFFFF"
                                    font.pixelSize: 14
                                    verticalAlignment: Text.AlignVCenter
                                    leftPadding: 15
                                }
                                
                                background: Rectangle {
                                    color: parent.hovered ? "#2A3040" : "transparent"
                                }
                            }
                            
                            onCurrentTextChanged: {
                                selectedCommand = currentText
                                currentParameters = commandDefinitions[selectedCommand] ? commandDefinitions[selectedCommand].parameters : []
                                parameterValues = {}
                                commandDescription.text = commandDefinitions[selectedCommand] ? commandDefinitions[selectedCommand].description : ""
                            }
                        }
                    }
                    
                    // Command Description
                    Text {
                        id: commandDescription
                        Layout.fillWidth: true
                        text: {
                            if (!selectedCommand) {
                                return "Select a command to see its description"
                            }

                            var description = commandDefinitions[selectedCommand].description
                            if (!selectedCommandSupported) {
                                return description + " (Not yet available in the current backend)"
                            }
                            return description
                        }
                        color: "#CCCCCC"
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                }
                
                // Parameters Section
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 15
                    visible: currentParameters.length > 0
                    
                    Text {
                        text: "Parameters"
                        color: "#FFFFFF"
                        font.pixelSize: 16
                        font.bold: true
                    }
                    
                    // Scrollable parameter inputs
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 100
                        clip: true
                        
                        ScrollBar.vertical.policy: ScrollBar.AsNeeded
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        
                        ColumnLayout {
                            width: parent.width
                            spacing: 15
                            
                            // Dynamic parameter inputs
                            Repeater {
                                model: currentParameters
                                
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 5
                                    
                                    Text {
                                        text: modelData.name + (modelData.unit ? " (" + modelData.unit + ")" : "")
                                        color: "#FFFFFF"
                                        font.pixelSize: 14
                                    }
                                    
                                    // Number input
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 50
                                        color: "#1A1A1A"
                                        border.color: numberInputWrapper.activeFocus ? "#3A5A8C" : "#333333"
                                        border.width: 1
                                        radius: 6
                                        visible: modelData.type === "number"
                                        
                                        Behavior on border.color {
                                            ColorAnimation { duration: 150 }
                                        }
                                        
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 0
                                            spacing: 0
                                            
                                            TextInput {
                                                id: numberInputWrapper
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                                leftPadding: 10
                                                rightPadding: 10
                                                text: ""
                                                color: "#FFFFFF"
                                                font.pixelSize: 14
                                                verticalAlignment: TextInput.AlignVCenter
                                                
                                                onTextChanged: {
                                                    // Allow only numbers, minus sign, and decimal point
                                                    var filtered = text.replace(/[^0-9.\-]/g, '')
                                                    
                                                    // Ensure only one minus at start
                                                    if (filtered.indexOf('-') !== filtered.lastIndexOf('-')) {
                                                        filtered = filtered.replace(/-/g, '')
                                                    }
                                                    if (filtered.indexOf('-') > 0) {
                                                        filtered = filtered.replace('-', '')
                                                    }
                                                    
                                                    // Ensure only one decimal point
                                                    if (filtered.indexOf('.') !== filtered.lastIndexOf('.')) {
                                                        filtered = filtered.substring(0, filtered.lastIndexOf('.'))
                                                    }
                                                    
                                                    if (text !== filtered) {
                                                        text = filtered
                                                        return
                                                    }
                                                    
                                                    parameterValues[modelData.name] = text
                                                }
                                                
                                                onActiveFocusChanged: {
                                                    if (activeFocus) {
                                                        numberPad.targetField = numberInputWrapper
                                                        numberPad.open()
                                                    }
                                                }
                                            }
                                            
                                            // Numpad button in input field
                                            Rectangle {
                                                Layout.preferredWidth: 40
                                                Layout.fillHeight: true
                                                color: numpadButtonArea.containsMouse ? "#2A3F60" : "transparent"
                                                radius: 6
                                                
                                                Behavior on color {
                                                    ColorAnimation { duration: 150 }
                                                }
                                                
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "🔢"
                                                    font.pixelSize: 16
                                                    color: "#CCCCCC"
                                                }
                                                
                                                MouseArea {
                                                    id: numpadButtonArea
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    onClicked: {
                                                        numberPad.targetField = numberInputWrapper
                                                        numberPad.open()
                                                    }
                                                }
                                            }
                                        }

                                        // Placeholder text
                                        Text {
                                            anchors.fill: parent
                                            anchors.leftMargin: 10
                                            anchors.rightMargin: 50
                                            text: modelData.placeholder || ""
                                            color: "#666666"
                                            font.pixelSize: 14
                                            verticalAlignment: Text.AlignVCenter
                                            visible: numberInputWrapper.text === "" && !numberInputWrapper.activeFocus
                                        }
                                    }
                                    
                                    // Dropdown input
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 40
                                        color: "#1A1A1A"
                                        border.color: "#333333"
                                        border.width: 1
                                        radius: 6
                                        visible: modelData.type === "dropdown"
                                        
                                        ComboBox {
                                            id: paramDropdown
                                            anchors.fill: parent
                                            model: modelData.options || []
                                            
                                            background: Rectangle {
                                                color: "transparent"
                                                border.color: paramDropdown.activeFocus ? "#3A5A8C" : "transparent"
                                                border.width: 1
                                                radius: 6
                                            }
                                            
                                            contentItem: Text {
                                                leftPadding: 10
                                                rightPadding: paramDropdown.indicator.width + paramDropdown.spacing
                                                text: paramDropdown.displayText || modelData.placeholder
                                                font.pixelSize: 14
                                                color: paramDropdown.displayText ? "#FFFFFF" : "#999999"
                                                verticalAlignment: Text.AlignVCenter
                                            }
                                            
                                            indicator: Text {
                                                x: paramDropdown.width - width - 10
                                                y: paramDropdown.topPadding + (paramDropdown.availableHeight - height) / 2
                                                text: "▼"
                                                font.pixelSize: 10
                                                color: "#CCCCCC"
                                            }
                                            
                                            popup: Popup {
                                                y: paramDropdown.height - 1
                                                width: paramDropdown.width
                                                implicitHeight: contentItem.implicitHeight
                                                padding: 1
                                                
                                                contentItem: ListView {
                                                    clip: true
                                                    implicitHeight: contentHeight
                                                    model: paramDropdown.popup.visible ? paramDropdown.delegateModel : null
                                                    currentIndex: paramDropdown.highlightedIndex
                                                }
                                                
                                                background: Rectangle {
                                                    color: "#1A1A1A"
                                                    border.color: "#3A5A8C"
                                                    border.width: 1
                                                    radius: 6
                                                }
                                            }
                                            
                                            delegate: ItemDelegate {
                                                width: paramDropdown.width
                                                height: 35
                                                
                                                contentItem: Text {
                                                    text: modelData
                                                    color: "#FFFFFF"
                                                    font.pixelSize: 14
                                                    verticalAlignment: Text.AlignVCenter
                                                    leftPadding: 10
                                                }
                                                
                                                background: Rectangle {
                                                    color: parent.hovered ? "#2A3040" : "transparent"
                                                }
                                            }
                                            
                                            onCurrentTextChanged: {
                                                parameterValues[modelData.name] = currentText
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Bottom spacer to ensure last parameter isn't cut off
                            Item { 
                                Layout.fillWidth: true
                                height: 10
                            }
                        }
                    }
                }
                
                // Send Button Section
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 10
                    
                    Item {
                        Layout.fillWidth: true
                    }
                    
                    Rectangle {
                        id: sendButton
                        width: 140
                        height: 45
                        radius: 8
                        color: sendButtonArea.containsMouse && parent.enabled ? "#4CAF50" : (selectedCommandSupported ? "#3A8F3A" : "#444444")
                        border.color: selectedCommandSupported ? "#4CAF50" : "#666666"
                        border.width: 1
                        enabled: selectedCommand !== "" && selectedCommandSupported
                        
                        Behavior on color {
                            ColorAnimation { duration: 200 }
                        }
                        
                        MouseArea {
                            id: sendButtonArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: parent.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: {
                                if (parent.enabled) {
                                    sendCommand()
                                }
                            }
                        }
                        
                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            
                            Text {
                                text: "▶"
                                color: sendButton.enabled ? "#FFFFFF" : "#999999"
                                font.pixelSize: 12
                            }
                            
                            Text {
                                text: selectedCommand !== "" && !selectedCommandSupported ? "Unavailable" : "Send"
                                color: sendButton.enabled ? "#FFFFFF" : "#999999"
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }
                    }
                }
                
                // Spacer
                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }
    
    // Function to send command
    function sendCommand() {
        if (!selectedCommand) return
        
        console.log("Sending command:", selectedCommand)
        console.log("Parameters:", JSON.stringify(parameterValues))

        if (!manualCommandHandler) {
            console.log("manualCommandHandler is not available")
            return
        }

        if (manualCommandHandler.executeCommand(selectedCommand, parameterValues)) {
            showCommandFeedback()
        } else {
            console.log("Command rejected:", selectedCommand)
        }
    }
    
    // Visual feedback function
    function showCommandFeedback() {
        // You could add a temporary overlay or notification here
        console.log("Command sent successfully!")
    }
    
    // Numpad component for number input
    NumpadNew {
        id: numberPad
    }
}