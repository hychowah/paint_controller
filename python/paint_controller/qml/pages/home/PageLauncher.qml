import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"
import "../../components/displays"

Rectangle {
    id: pageHomeRect
    width: parent.width
    height: parent.height
    color: "#5E5C64"

    property color availableColor: "#7ED957"  // Softer green
    property color unavailableColor: "#FF5E3A"  // Softer red

    property real ledSize: 30
    
    // Function to show message popup
    function showMessage(message, type) {
        if (typeof messagePopup !== 'undefined') {
            messagePopup.messageTitle = "Button Action"
            messagePopup.messageText = message
            messagePopup.messageType = type
            messagePopup.open()
        }
    }
    
    // Reusable Input Field Component (top-level)
    component InputField: ColumnLayout {
        property string label: ""
        property string placeholder: ""
        property alias text: textField.text
        
        Layout.fillWidth: true
        spacing: 5
        
        Text {
            text: label
            color: "#ffffff"
            font.pixelSize: 14
        }
        
        TextField {
            id: textField
            Layout.fillWidth: true
            placeholderText: placeholder
            color: "#ffffff"
            
            background: Rectangle {
                color: "#5E5C64"
                border.color: "#6A6A74"
                border.width: 1
                radius: 5
            }
        }
    }
    
    // Reusable Settings Popup
    component SettingsPopup: Popup {
        property string popupTitle: ""
        property string deviceName: ""
        
        // Individual properties for each field
        property string ipAddress: ""
        property string port: "22"
        property string username: ""
        property string keyPath: ""
        
        signal applied(var data)
        
        id: popup
        anchors.centerIn: parent
        width: 400
        height: 400
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        // Function to load existing configuration
        function loadConfig() {
            if (deviceName !== "") {
                var configJson = sshHandler.get_device_config(deviceName)
                try {
                    var config = JSON.parse(configJson)
                    ipAddress = config.ip || ""
                    port = config.port || "22"
                    username = config.username || ""
                    keyPath = config.key_path || ""
                } catch (e) {
                    console.log("Error loading config:", e)
                }
            }
        }
        
        onOpened: loadConfig()
        
        background: Rectangle {
            color: "#4A4A54"
            radius: 10
            border.color: "#6A6A74"
            border.width: 1
        }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15
            
            Text {
                text: popup.popupTitle
                font.pixelSize: 18
                font.weight: Font.Medium
                color: "#ffffff"
                Layout.alignment: Qt.AlignHCenter
            }
            
            Rectangle {
                Layout.preferredWidth: parent.width * 0.8
                Layout.preferredHeight: 2
                radius: 1
                color: "#64B5F6"
                Layout.alignment: Qt.AlignHCenter
            }
            
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                ColumnLayout {
                    width: parent.parent.width
                    spacing: 12
                    
                    InputField {
                        label: "IP Address:"
                        placeholder: "192.168.1.100"
                        text: popup.ipAddress
                        onTextChanged: popup.ipAddress = text
                    }
                    
                    InputField {
                        label: "Port:"
                        placeholder: "22"
                        text: popup.port
                        onTextChanged: popup.port = text
                    }
                    
                    InputField {
                        label: "Username:"
                        placeholder: "pi"
                        text: popup.username
                        onTextChanged: popup.username = text
                    }
                    
                    InputField {
                        label: "SSH Key Path (optional):"
                        placeholder: "~/.ssh/id_rsa"
                        text: popup.keyPath
                        onTextChanged: popup.keyPath = text
                    }
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                Button {
                    text: "Cancel"
                    Layout.fillWidth: true
                    
                    background: Rectangle {
                        color: parent.pressed ? "#E53E3E" : (parent.hovered ? "#F56565" : "#FC8181")
                        radius: 5
                        border.color: "#E53E3E"
                        border.width: 1
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "#ffffff"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: popup.close()
                }
                
                Button {
                    text: "Apply"
                    Layout.fillWidth: true
                    
                    background: Rectangle {
                        color: parent.pressed ? "#4CAF50" : (parent.hovered ? "#5CBF60" : "#66BB6A")
                        radius: 5
                        border.color: "#4CAF50"
                        border.width: 1
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "#ffffff"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: {
                        var data = {
                            ip: popup.ipAddress,
                            port: popup.port,
                            username: popup.username,
                            key_path: popup.keyPath
                        }
                        popup.applied(data)
                        popup.close()
                    }
                }
            }
        }
    }
    
    // Base Settings Popup
    SettingsPopup {
        id: baseSettingsPopup
        popupTitle: "BASE SETTINGS"
        deviceName: "BASE"
        
        onApplied: function(data) {
            sshHandler.update_device_config("BASE", data.ip, data.port, data.username, data.key_path)
        }
    }
    
    // End Effector Settings Popup
    SettingsPopup {
        id: endEffectorPopup
        popupTitle: "END EFFECTOR SETTINGS"
        deviceName: "END_EFFECTOR"
        
        onApplied: function(data) {
            sshHandler.update_device_config("END_EFFECTOR", data.ip, data.port, data.username, data.key_path)
        }
    }
    
    // Reusable Control Card Component
    component ControlCard: Rectangle {
        property string deviceHost: ""
        property string deviceName: ""
        property string startButtonText: "START"
        property string stopButtonText: "STOP"
        property color startButtonColor: "#66BB6A"
        property color startButtonHoverColor: "#5CBF60"
        property color startButtonPressedColor: "#4CAF50"
        property color stopButtonColor: "#FC8181"
        property color stopButtonHoverColor: "#F56565"
        property color stopButtonPressedColor: "#E53E3E"
        
        // Size properties for easy customization
        property real cardHeight: 85
        property real buttonWidth: 120
        property real buttonHeight: 36
        property real titleFontSize: 18
        property real buttonFontSize: 12
        property real cardRadius: 10
        property real buttonRadius: 6
        property real cardMargins: 12
        property real titleButtonSpacing: 8
        property real buttonSpacing: 12
        
        Layout.fillWidth: true
        Layout.preferredHeight: cardHeight
        radius: cardRadius
        color: "#4A4A54"
        border.color: "#6A6A74"
        border.width: 1
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: cardMargins
            spacing: titleButtonSpacing
            
            Text {
                text: deviceName
                font.pixelSize: titleFontSize
                font.bold: true
                font.weight: Font.Medium
                color: "#ffffff"
                Layout.alignment: Qt.AlignLeft
                Layout.fillWidth: true
            }
            
            RowLayout {
                spacing: buttonSpacing
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Button {
                    text: startButtonText
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    Layout.maximumHeight: buttonHeight
                    
                    background: Rectangle {
                        radius: buttonRadius
                        color: parent.pressed ? startButtonPressedColor : (parent.hovered ? startButtonHoverColor : startButtonColor)
                        border.color: startButtonPressedColor
                        border.width: 1
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "#ffffff"
                        font.weight: Font.Medium
                        font.pixelSize: buttonFontSize
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: {
                        sshHandler.handle_device_command(deviceHost, deviceName, "start")
                    }
                }
                
                Button {
                    text: stopButtonText
                    Layout.preferredWidth: buttonWidth
                    Layout.preferredHeight: buttonHeight
                    Layout.maximumHeight: buttonHeight
                    
                    background: Rectangle {
                        radius: buttonRadius
                        color: parent.pressed ? stopButtonPressedColor : (parent.hovered ? stopButtonHoverColor : stopButtonColor)
                        border.color: stopButtonPressedColor
                        border.width: 1
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "#ffffff"
                        font.weight: Font.Medium
                        font.pixelSize: buttonFontSize
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: {
                        sshHandler.handle_device_command(deviceHost, deviceName, "stop")
                    }
                }
                
                // Spacer to push buttons to the left
                Item {
                    Layout.fillWidth: true
                }
            }
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 20
        
        // Title Section
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "transparent"
            
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12
                
                Text {
                    text: "PROGRAM LAUNCHER"
                    font.pixelSize: 32
                    font.weight: Font.Light
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Rectangle {
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: 2
                    radius: 1
                    color: "#64B5F6"
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
        
        // Main Content - Two Columns
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 40
        
            // Left Column - Base Settings
            Rectangle {
                Layout.fillHeight: true
                Layout.fillWidth: true
                color: "transparent"
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    
                    // Clickable Header
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        radius: 8
                        color: "#4A4A54"
                        border.color: "#6A6A74"
                        border.width: 1

                        // BASE SETTINGS text on the left
                        Text {
                            text: "BASE SETTINGS"
                            font.pixelSize: 25
                            font.bold: true
                            font.weight: Font.Medium
                            color: "#ffffff"
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 30
                        }

                        // LED aligned to the right
                        Rectangle {
                            id: ledIndicator
                            width: ledSize
                            height: ledSize
                            radius: ledSize / 2 // Circular LED
                            color: sshHandler.deviceAvailability.BASE ? availableColor : unavailableColor
                            border.color: "#ffffff"
                            border.width: 1
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.rightMargin: 30
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: baseSettingsPopup.open()
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                    
                    // Scrollable Control Cards
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: -1
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        ScrollBar.vertical.policy: ScrollBar.AsNeeded
                        
                        ColumnLayout {
                            width: parent.width
                            spacing: 12
                            
                            ControlCard {
                                deviceHost: "BASE"
                                deviceName: "Winch"
                            }
                            
                            ControlCard {
                                deviceHost: "BASE"
                                deviceName: "Wheel"
                            }
                            
                            ControlCard {
                                deviceHost: "BASE"
                                deviceName: "Camera"
                                startButtonText: "STREAM"
                                startButtonColor: "#64B5F6"
                                startButtonHoverColor: "#42A5F5"
                                startButtonPressedColor: "#2196F3"
                            }
                            
                            // Spacer at the bottom to ensure proper spacing
                            Item {
                                Layout.fillHeight: true
                                Layout.minimumHeight: 10
                            }
                        }
                    }
                }
            }
            
            // Right Column - End Effector
            Rectangle {
                Layout.fillHeight: true
                Layout.fillWidth: true
                color: "transparent"
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    
                    // Clickable Header
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        radius: 8
                        color: "#4A4A54"
                        border.color: "#6A6A74"
                        border.width: 1

                        // Manual layouting instead of RowLayout
                        Text {
                            text: "END EFFECTOR"
                            font.pixelSize: 25
                            font.bold: true
                            font.weight: Font.Medium
                            color: "#ffffff"
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 30
                        }

                        Rectangle {
                            id: endEffectorLedIndicator
                            width: ledSize
                            height: ledSize
                            radius: ledSize / 2
                            color: sshHandler.deviceAvailability.END_EFFECTOR ? availableColor : unavailableColor
                            border.color: "#ffffff"
                            border.width: 1
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.rightMargin: 30
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: endEffectorPopup.open()
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                    
                    // Control Cards
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: -1
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        ScrollBar.vertical.policy: ScrollBar.AsNeeded

                        ColumnLayout {
                            width: parent.width
                            spacing: 12
                            
                            ControlCard {
                                deviceHost: "END_EFFECTOR"
                                deviceName: "Teensy"
                            }
                            
                            ControlCard {
                                deviceHost: "END_EFFECTOR"
                                deviceName: "Wind Sensor"
                            }
                            
                            ControlCard {
                                deviceHost: "END_EFFECTOR"
                                deviceName: "Lidar"
                            }
                            
                            ControlCard {
                                deviceHost: "END_EFFECTOR"
                                deviceName: "Camera"
                                startButtonText: "STREAM"
                                startButtonColor: "#64B5F6"
                                startButtonHoverColor: "#42A5F5"
                                startButtonPressedColor: "#2196F3"
                            }

                            // Spacer at the bottom to ensure proper spacing
                            Item {
                                Layout.fillHeight: true
                                Layout.minimumHeight: 10
                            }
                        }
                    }
                    
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
        }
    }
}