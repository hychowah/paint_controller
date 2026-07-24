import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"
import "../../../components/popups"

Popup {
    id: settingsPopup
    width: 500
    height: 650
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    anchors.centerIn: Overlay.overlay
    padding: 0
    property var liveAdjustmentsLegality: settingsPopup.defaultLegality("Base Top View Live Adjustments")
    property var saveLegality: settingsPopup.defaultLegality("Base Top View Save")
    property var resetLegality: settingsPopup.defaultLegality("Base Top View Reset")
    readonly property bool liveAdjustmentsAllowed: liveAdjustmentsLegality.allowed !== false
    readonly property string liveAdjustmentsReason: liveAdjustmentsAllowed ? "" : String(liveAdjustmentsLegality.reason || "")
    readonly property bool saveAllowed: saveLegality.allowed !== false
    readonly property string saveReason: saveAllowed ? "" : String(saveLegality.reason || "")
    readonly property bool resetAllowed: resetLegality.allowed !== false
    readonly property string resetReason: resetAllowed ? "" : String(resetLegality.reason || "")

    function defaultLegality(title) {
        return {
            "allowed": true,
            "reason": "",
            "title": title,
        }
    }

    function refreshLegalities() {
        liveAdjustmentsLegality = actionLegality
            ? actionLegality.getActionLegality("camera.base_top_view.live_adjustments")
            : defaultLegality("Base Top View Live Adjustments")
        saveLegality = actionLegality
            ? actionLegality.getActionLegality("camera.base_top_view.save")
            : defaultLegality("Base Top View Save")
        resetLegality = actionLegality
            ? actionLegality.getActionLegality("camera.base_top_view.reset")
            : defaultLegality("Base Top View Reset")
    }

    Component.onCompleted: refreshLegalities()

    Connections {
        target: actionLegality

        function onLegalityChanged() {
            settingsPopup.refreshLegalities()
        }
    }
    
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
                text: "Base Top View Settings"
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

                Rectangle {
                    objectName: "baseTopViewLegalityBanner"
                    Layout.fillWidth: true
                    visible: !settingsPopup.liveAdjustmentsAllowed
                    color: CommonStyle.warningSurface
                    radius: 8
                    border.color: CommonStyle.statusWarning
                    border.width: 1
                    implicitHeight: warningText.implicitHeight + 16

                    Text {
                        id: warningText
                        anchors.fill: parent
                        anchors.margins: 8
                        text: settingsPopup.liveAdjustmentsReason
                        color: CommonStyle.warningText
                        wrapMode: Text.WordWrap
                        font.pixelSize: 13
                    }
                }
                
                // Edit Points button (disabled)
                Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50
                    enabled: false
                    opacity: 0.3
                    
                    background: Rectangle {
                        color: "#3F51B5"
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
                            text: "Edit Source Points (Disabled)"
                            color: "white"
                            font.pixelSize: 14
                            font.bold: true
                            Layout.fillWidth: true
                        }
                    }
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#4A4A4A"
                }
                
                // Zoom slider
                SettingSlider {
                    id: zoomSlider
                    objectName: "zoomSlider"
                    title: "Zoom"
                    minValue: 0.1
                    maxValue: 2.0
                    currentValue: baseTopViewStatus.zoom
                    stepSize: 0.01
                    decimals: 2
                    enabled: settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setZoom(value)) {
                            syncFromCurrentValue()
                        }
                    }
                }
                
                // Horizontal offset slider
                SettingSlider {
                    id: offsetXSlider
                    title: "Horizontal Pan"
                    minValue: -1.0
                    maxValue: 1.0
                    currentValue: baseTopViewStatus.offsetX
                    stepSize: 0.01
                    decimals: 3
                    enabled: settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setOffsetX(value)) {
                            syncFromCurrentValue()
                        }
                    }
                }
                
                // Vertical offset slider
                SettingSlider {
                    id: offsetYSlider
                    title: "Vertical Pan"
                    minValue: -1.0
                    maxValue: 1.0
                    currentValue: baseTopViewStatus.offsetY
                    stepSize: 0.01
                    decimals: 3
                    enabled: settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setOffsetY(value)) {
                            syncFromCurrentValue()
                        }
                    }
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
                            checked: baseTopViewStatus.cropEnabled
                            enabled: settingsPopup.liveAdjustmentsAllowed
                            opacity: enabled ? 1.0 : 0.5
                            onToggled: {
                                if (!baseTopViewActions.setCropEnabled(checked)) {
                                    cropToggle.checked = !checked
                                }
                            }
                        }
                    }
                }
                
                // Crop width ratio slider
                SettingSlider {
                    id: cropWidthSlider
                    title: "Crop Width"
                    minValue: 0.1
                    maxValue: 1.0
                    currentValue: baseTopViewStatus.cropWidthRatio
                    stepSize: 0.01
                    decimals: 3
                    enabled: baseTopViewStatus.cropEnabled && settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setCropWidthRatio(value)) {
                            syncFromCurrentValue()
                        }
                    }
                }
                
                // Crop center X slider
                SettingSlider {
                    id: cropCenterSlider
                    title: "Crop Center"
                    minValue: 0.0
                    maxValue: 1.0
                    currentValue: baseTopViewStatus.cropCenterX
                    stepSize: 0.01
                    decimals: 3
                    enabled: baseTopViewStatus.cropEnabled && settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setCropCenterX(value)) {
                            syncFromCurrentValue()
                        }
                    }
                }
                
                // Distortion coefficient k1
                SettingSlider {
                    id: k1Slider
                    title: "Distortion K1"
                    minValue: -1.0
                    maxValue: 1.0
                    currentValue: baseTopViewStatus.k1
                    stepSize: 0.01
                    decimals: 3
                    enabled: settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setK1(value)) {
                            syncFromCurrentValue()
                        }
                    }
                }
                
                // Distortion coefficient k2
                SettingSlider {
                    id: k2Slider
                    title: "Distortion K2"
                    minValue: -1.0
                    maxValue: 1.0
                    currentValue: baseTopViewStatus.k2
                    stepSize: 0.01
                    decimals: 3
                    enabled: settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setK2(value)) {
                            syncFromCurrentValue()
                        }
                    }
                }
                
                // Distortion coefficient k3
                SettingSlider {
                    id: k3Slider
                    title: "Distortion K3"
                    minValue: -2.0
                    maxValue: 2.0
                    currentValue: baseTopViewStatus.k3
                    stepSize: 0.01
                    decimals: 3
                    enabled: settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setK3(value)) {
                            syncFromCurrentValue()
                        }
                    }
                }
                
                // Distortion coefficient k4
                SettingSlider {
                    id: k4Slider
                    title: "Distortion K4"
                    minValue: -2.0
                    maxValue: 2.0
                    currentValue: baseTopViewStatus.k4
                    stepSize: 0.01
                    decimals: 3
                    enabled: settingsPopup.liveAdjustmentsAllowed
                    onValueChanged: function(value) {
                        if (!baseTopViewActions.setK4(value)) {
                            syncFromCurrentValue()
                        }
                    }
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

                Text {
                    objectName: "baseTopViewActionReason"
                    visible: !settingsPopup.saveAllowed || !settingsPopup.resetAllowed
                    text: !settingsPopup.saveAllowed ? settingsPopup.saveReason : settingsPopup.resetReason
                    color: CommonStyle.warningText
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    Layout.preferredWidth: 220
                }
                
                Button {
                    objectName: "saveSettingsButton"
                    text: "Save Settings"
                    Layout.preferredWidth: 140
                    Layout.preferredHeight: 40
                    enabled: settingsPopup.saveAllowed
                    
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
                        if (baseTopViewStatus) {
                            var success = baseTopViewActions.saveSettings()
                            
                            if (success) {
                                confirmationPopup.messageTitle = "Saved"
                                confirmationPopup.messageText = "Base top view settings saved successfully"
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
                    objectName: "resetDefaultsButton"
                    text: "Reset to Defaults"
                    Layout.preferredWidth: 180
                    Layout.preferredHeight: 40
                    enabled: settingsPopup.resetAllowed
                    
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
                    
                    onClicked: {
                        if (baseTopViewActions.resetToDefaults()) {
                            zoomSlider.syncFromCurrentValue()
                            offsetXSlider.syncFromCurrentValue()
                            offsetYSlider.syncFromCurrentValue()
                            cropToggle.checked = baseTopViewStatus.cropEnabled
                            cropWidthSlider.syncFromCurrentValue()
                            cropCenterSlider.syncFromCurrentValue()
                            k1Slider.syncFromCurrentValue()
                            k2Slider.syncFromCurrentValue()
                            k3Slider.syncFromCurrentValue()
                            k4Slider.syncFromCurrentValue()
                        } else {
                            confirmationPopup.messageTitle = "Blocked"
                            confirmationPopup.messageText = "Base top view reset rejected"
                            confirmationPopup.messageType = "error"
                            confirmationPopup.open()
                        }
                    }
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

        function syncFromCurrentValue() {
            valueSlider.value = currentValue
        }
        
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
            id: valueSlider
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
