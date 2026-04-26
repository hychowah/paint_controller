import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

Rectangle {
    id: controlPanel
    required property string controlName
    required property string controlStatus
    property bool enabledState: false
    required property string iconText
    property bool selfContained: false
    property string actionKey: ""
    property var legalityModel: null
    property var legality: controlPanel.defaultLegality()
    readonly property bool actionAllowed: !actionKey || !legalityModel || legality.allowed !== false
    readonly property string blockedReason: actionAllowed ? "" : String(legality.reason || "")
    
    signal clicked()

    function defaultLegality() {
        return {
            "allowed": true,
            "reason": "",
            "title": controlName,
        }
    }

    function refreshLegality() {
        legality = legalityModel && actionKey !== ""
            ? legalityModel.getActionLegality(actionKey)
            : defaultLegality()
    }
    
    height: blockedReason !== "" ? CommonStyle.itemHeight + CommonStyle.spacingLg : CommonStyle.itemHeight
    radius: CommonStyle.radiusMd
    color: !actionAllowed
        ? CommonStyle.warningSurface
        : (enabledState ? CommonStyle.cardBackground : CommonStyle.backgroundL1)
    border.color: !actionAllowed
        ? CommonStyle.statusWarning
        : (enabledState ? CommonStyle.borderFocused : CommonStyle.inputBorder)
    border.width: 1
    opacity: enabled ? 1.0 : 0.65
    
    // This ensures consistent layout across all control panels
    Layout.fillWidth: true

    Component.onCompleted: refreshLegality()
    onActionKeyChanged: refreshLegality()
    onLegalityModelChanged: refreshLegality()

    Connections {
        target: legalityModel

        function onLegalityChanged() {
            controlPanel.refreshLegality()
        }
    }
    
    // Subtle transition animations
    Behavior on color {
        ColorAnimation { duration: CommonStyle.motionStandard }
    }
    
    Behavior on border.color {
        ColorAnimation { duration: CommonStyle.motionStandard }
    }
    
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        enabled: controlPanel.enabled && controlPanel.actionAllowed
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: {
            if (controlPanel.selfContained) {
                controlPanel.enabledState = !controlPanel.enabledState
                controlPanel.controlStatus = controlPanel.enabledState ? "Enabled" : "Disabled"
            }
            controlPanel.clicked()
        }
        // Hover effect
        onEntered: {
            if (enabled) {
                parent.color = enabledState ? CommonStyle.cardBackgroundAlt : CommonStyle.backgroundL2
            }
        }
        
        onExited: {
            parent.color = !controlPanel.actionAllowed
                ? CommonStyle.warningSurface
                : (enabledState ? CommonStyle.cardBackground : CommonStyle.backgroundL1)
        }
    }
    
    // Use Row instead of RowLayout for more consistent sizing
    Row {
        anchors {
            fill: parent
            margins: CommonStyle.spacingMd
            // Add right margin to create space between toggle and right edge
            rightMargin: CommonStyle.spacingLg
        }
        spacing: CommonStyle.spacingMd
        
        // Icon
        Rectangle {
            width: CommonStyle.controlHeightMd
            height: CommonStyle.controlHeightMd
            radius: width / 2
            color: enabledState ? CommonStyle.borderFocused : CommonStyle.textDisabled
            anchors.verticalCenter: parent.verticalCenter
            
            Text {
                anchors.centerIn: parent
                text: controlPanel.iconText
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontBody
                color: CommonStyle.textPrimary
                font.bold: true
            }
            
            // Color transition
            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionStandard }
            }
        }
        
        // Text with status - using a Rectangle with Column inside to fill available space
        Rectangle {
            width: parent.width - 36 - 10 - 52 - 5 // parent width minus icon width, spacing, switch width, and extra margin
            height: parent.height - 20
            color: "transparent" // Make this visible for debugging: "#550000"
            anchors.verticalCenter: parent.verticalCenter
            
            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: Math.max(2, CommonStyle.spacingXs)
                
                Text {
                    text: controlPanel.controlName
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody
                    font.bold: true
                    color: CommonStyle.textPrimary
                }
                
                Text {
                    text: controlPanel.controlStatus
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption
                    color: enabledState ? CommonStyle.accentMuted : CommonStyle.textDisabled
                    wrapMode: Text.WordWrap
                    visible: controlPanel.controlStatus !== ""
                    
                    // Color transition
                    Behavior on color {
                        ColorAnimation { duration: CommonStyle.motionStandard }
                    }
                }

                Text {
                    text: controlPanel.blockedReason
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption
                    color: CommonStyle.warningText
                    wrapMode: Text.WordWrap
                    visible: controlPanel.blockedReason !== ""
                }
            }
        }
        
        // Toggle switch - simple Rectangle with fixed width
        Rectangle {
            width: 52
            height: 28
            radius: 14
            color: enabledState ? CommonStyle.borderFocused : CommonStyle.textDisabled
            anchors.verticalCenter: parent.verticalCenter
            
            Rectangle {
                width: 22
                height: 22
                radius: 11
                color: CommonStyle.textPrimary
                anchors.verticalCenter: parent.verticalCenter
                x: enabledState ? parent.width - width - 3 : 3
                
                Behavior on x {
                    NumberAnimation { 
                        duration: CommonStyle.motionStandard
                        easing.type: Easing.OutCubic
                    }
                }
            }
            
            // Color transition
            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionStandard }
            }
        }
    }
}