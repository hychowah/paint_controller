import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../components/popups"

Popup {
    id: settingsPopup
    width: 500
    height: 650
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    anchors.centerIn: Overlay.overlay
    padding: 0
    
    background: Rectangle {
        color: "#2D2D2D"
        radius: 12
        border.color: "#4A4A4A"
        border.width: 2
        
        // Header accent
        Rectangle {
            width: parent.width
            height: 50
            color: "#3F51B5"
            radius: 12
            
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 12
                color: parent.color
            }
            
            Text {
                text: "Bird View Settings"
                font.pixelSize: 18
                font.bold: true
                color: "white"
                anchors.centerIn: parent
            }
        }
    }
    
    contentItem: Item {
        anchors.fill: parent
        
        Flickable {
            anchors.fill: parent
            anchors.topMargin: 60
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            anchors.bottomMargin: 70
            contentHeight: columnLayout.height
            clip: true
            
            ColumnLayout {
                id: columnLayout
                width: parent.width
                spacing: 15
                
                // Edit Points button
                Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    
                    background: Rectangle {
                        color: parent.pressed ? "#303F9F" : (parent.hovered ? "#3949AB" : "#3F51B5")
                        radius: 6
                        border.color: "#FFFFFF"
                        border.width: 2
                    }
                    
                    contentItem: RowLayout {
                        spacing: 10
                        
                        Text {
                            text: "✎"
                            color: "white"
                            font.pixelSize: 20
                        }
                        
                        Text {
                            text: "Edit Source Points (Click & Drag)"
                            color: "white"
                            font.pixelSize: 14
                            font.bold: true
                            Layout.fillWidth: true
                        }
                    }
                    
                    onClicked: {
                        birdViewController.editMode = true
                        settingsPopup.close()
                    }
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#4A4A4A"
                }
                
                // Zoom slider
                SettingSlider {
                    title: "Zoom"
                    minValue: 0.1
                    maxValue: 2.0
                    currentValue: birdViewController.zoom
                    stepSize: 0.01
                    decimals: 2
                    onValueChanged: birdViewController.zoom = value
                }
                
                // Horizontal offset slider
                SettingSlider {
                    title: "Horizontal Pan"
                    minValue: -1.0
                    maxValue: 1.0
                    currentValue: birdViewController.offsetX
                    stepSize: 0.01
                    decimals: 3
                    onValueChanged: birdViewController.offsetX = value
                }
                
                // Vertical offset slider
                SettingSlider {
                    title: "Vertical Pan"
                    minValue: -1.0
                    maxValue: 1.0
                    currentValue: birdViewController.offsetY
                    stepSize: 0.01
                    decimals: 3
                    onValueChanged: birdViewController.offsetY = value
                }
                
                // Crop enabled toggle
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    color: "transparent"
                    
                    RowLayout {
                        anchors.fill: parent
                        
                        Text {
                            text: "Crop Enabled"
                            color: "#E0E0E0"
                            font.pixelSize: 14
                            Layout.fillWidth: true
                        }
                        
                        Switch {
                            id: cropToggle
                            checked: birdViewController.cropEnabled
                            onCheckedChanged: birdViewController.cropEnabled = checked
                        }
                    }
                }
                
                // Crop width ratio slider
                SettingSlider {
                    title: "Crop Width"
                    minValue: 0.1
                    maxValue: 1.0
                    currentValue: birdViewController.cropWidthRatio
                    stepSize: 0.01
                    decimals: 3
                    enabled: birdViewController.cropEnabled
                    onValueChanged: birdViewController.cropWidthRatio = value
                }
                
                // Crop center X slider
                SettingSlider {
                    title: "Crop Center"
                    minValue: 0.0
                    maxValue: 1.0
                    currentValue: birdViewController.cropCenterX
                    stepSize: 0.01
                    decimals: 3
                    enabled: birdViewController.cropEnabled
                    onValueChanged: birdViewController.cropCenterX = value
                }
                
                // Distortion coefficient k1
                SettingSlider {
                    title: "Distortion K1"
                    minValue: 0.0
                    maxValue: 1.0
                    currentValue: birdViewController.k1
                    stepSize: 0.01
                    decimals: 3
                    onValueChanged: birdViewController.k1 = value
                }
                
                // Distortion coefficient k2
                SettingSlider {
                    title: "Distortion K2"
                    minValue: 0.0
                    maxValue: 1.0
                    currentValue: birdViewController.k2
                    stepSize: 0.01
                    decimals: 3
                    onValueChanged: birdViewController.k2 = value
                }
            }
        }
        
        // Bottom button bar
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 60
            color: "#1F1F1F"
            radius: 12
            
            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 12
                color: parent.color
            }
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 20
                
                Button {
                    text: "Save Settings"
                    Layout.preferredWidth: 140
                    Layout.preferredHeight: 40
                    
                    background: Rectangle {
                        color: parent.pressed ? "#1565C0" : (parent.hovered ? "#1976D2" : "#2196F3")
                        radius: 6
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: {
                        if (settingsManager && birdViewController) {
                            // Copy current bird view values to settings manager
                            settingsManager.bird_view_zoom = birdViewController.zoom
                            settingsManager.bird_view_offset_x = birdViewController.offsetX
                            settingsManager.bird_view_offset_y = birdViewController.offsetY
                            settingsManager.bird_view_crop_enabled = birdViewController.cropEnabled
                            settingsManager.bird_view_crop_width_ratio = birdViewController.cropWidthRatio
                            settingsManager.bird_view_crop_center_x = birdViewController.cropCenterX
                            settingsManager.bird_view_k1 = birdViewController.k1
                            settingsManager.bird_view_k2 = birdViewController.k2
                            settingsManager.bird_view_src_points = birdViewController.sourcePoints
                            
                            // Save all bird view settings to file
                            var success = true
                            success = success && settingsManager.saveSetting("bird_view_zoom")
                            success = success && settingsManager.saveSetting("bird_view_offset_x")
                            success = success && settingsManager.saveSetting("bird_view_offset_y")
                            success = success && settingsManager.saveSetting("bird_view_crop_enabled")
                            success = success && settingsManager.saveSetting("bird_view_crop_width_ratio")
                            success = success && settingsManager.saveSetting("bird_view_crop_center_x")
                            success = success && settingsManager.saveSetting("bird_view_k1")
                            success = success && settingsManager.saveSetting("bird_view_k2")
                            success = success && settingsManager.saveSetting("bird_view_src_points")
                            
                            if (success) {
                                confirmationPopup.messageTitle = "Saved"
                                confirmationPopup.messageText = "Bird view settings saved successfully"
                                confirmationPopup.messageType = "info"
                                confirmationPopup.open()
                            } else {
                                confirmationPopup.messageTitle = "Error"
                                confirmationPopup.messageText = "Failed to save settings"
                                confirmationPopup.messageType = "error"
                                confirmationPopup.open()
                            }
                        }
                    }
                }
                
                Button {
                    text: "Reset to Defaults"
                    Layout.preferredWidth: 180
                    Layout.preferredHeight: 40
                    
                    background: Rectangle {
                        color: parent.pressed ? "#E65100" : (parent.hovered ? "#FF6F00" : "#FF9800")
                        radius: 6
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: birdViewController.resetToDefaults()
                }
                
                Button {
                    text: "Close"
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 40
                    
                    background: Rectangle {
                        color: parent.pressed ? "#388E3C" : (parent.hovered ? "#43A047" : "#4CAF50")
                        radius: 6
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.pixelSize: 14
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: settingsPopup.close()
                }
            }
        }
    }
    
    // Custom slider component for consistency
    component SettingSlider: ColumnLayout {
        property string title: ""
        property real minValue: 0
        property real maxValue: 1
        property real currentValue: 0.5
        property real stepSize: 0.01
        property int decimals: 2
        property bool enabled: true
        signal valueChanged(real value)
        
        Layout.fillWidth: true
        spacing: 5
        opacity: enabled ? 1.0 : 0.5
        
        RowLayout {
            Layout.fillWidth: true
            
            Text {
                text: title
                color: "#E0E0E0"
                font.pixelSize: 14
                Layout.fillWidth: true
            }
            
            Text {
                text: currentValue.toFixed(decimals)
                color: "#4CAF50"
                font.pixelSize: 14
                font.family: "Courier New"
                font.bold: true
                Layout.preferredWidth: 60
                horizontalAlignment: Text.AlignRight
            }
        }
        
        Slider {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            from: minValue
            to: maxValue
            value: currentValue
            stepSize: stepSize
            enabled: parent.enabled
            
            onValueChanged: {
                if (pressed) {
                    parent.valueChanged(value)
                }
            }
            
            background: Rectangle {
                x: parent.leftPadding
                y: parent.topPadding + parent.availableHeight / 2 - height / 2
                width: parent.availableWidth
                height: 4
                radius: 2
                color: "#555555"
                
                Rectangle {
                    width: parent.width * parent.parent.visualPosition
                    height: parent.height
                    color: "#3F51B5"
                    radius: 2
                }
            }
            
            handle: Rectangle {
                x: parent.leftPadding + parent.visualPosition * (parent.availableWidth - width)
                y: parent.topPadding + parent.availableHeight / 2 - height / 2
                width: 20
                height: 20
                radius: 10
                color: parent.pressed ? "#5C6BC0" : "#3F51B5"
                border.color: "#FFFFFF"
                border.width: 2
            }
        }
    }
    
    // Confirmation popup for save operations
    CustomPopup {
        id: confirmationPopup
        width: 400
        height: 180
        dismissDelay: 2000
    }
}
