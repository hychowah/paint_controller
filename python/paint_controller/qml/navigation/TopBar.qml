// TopBar.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: topBar
    height: CommonStyle.shellTopBarHeight
    color: CommonStyle.chromeBackground
    z: 1  // Ensure top bar is above the StackView
    
    // Subtle gradient overlay for depth
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.05) }
            GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.1) }
        }
    }
    
    // Thin bottom line (more subtle than before)
    Rectangle {
        id: bottomLine
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: CommonStyle.borderDefault
    }
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: CommonStyle.spacingLg
        spacing: CommonStyle.spacingLg
        
        // App message with improved typography
        Text {
            text: stateStore.display_message || ""
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.shellMessageFont
            font.weight: Font.Medium
            opacity: 0.9  // Slightly reduced opacity for softer look
        }
        
        Item { Layout.fillWidth: true } // Spacer
        
        // Redesigned warning button
        Button {
            id: warningButton
            Layout.preferredHeight: CommonStyle.shellControlHeightMd
            focusPolicy: Qt.NoFocus  // Prevent gamepad A button from triggering this
            
            contentItem: Row {
                spacing: CommonStyle.spacingSm
                anchors.centerIn: parent
                
                Text {
                    text: "⚠️"
                    font.pixelSize: CommonStyle.shellMessageFont
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "Warnings (" + warningHandler.warnings.length + ")"
                    color: warningHandler.warnings.length === 0 ? CommonStyle.textStrong : CommonStyle.textPrimary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.shellWarningFont
                    font.weight: Font.Medium
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            background: Rectangle {
                color: warningHandler.warnings.length === 0 ? CommonStyle.sidebarButtonSelected : CommonStyle.buttonDanger
                radius: CommonStyle.shellControlHeightMd / 2
                
                // Add subtle gradient
                Rectangle {
                    anchors.fill: parent
                    radius: parent.radius
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.1) }
                        GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.1) }
                    }
                }
            }
            
            onClicked: warningPopup.open()
        }
        
        // Modern digital clock
        Rectangle {
            color: Qt.rgba(1, 1, 1, 0.08)
            radius: CommonStyle.radiusSm
            Layout.preferredHeight: CommonStyle.shellControlHeightMd
            Layout.preferredWidth: clockText.width + CommonStyle.spacingXl
            
            Text {
                id: clockText
                anchors.centerIn: parent
                text: Qt.formatDateTime(new Date(), "hh:mm:ss")
                color: CommonStyle.textPrimary
                font.family: CommonStyle.fontMono
                font.pixelSize: CommonStyle.shellClockFont
                font.weight: Font.Medium
                
                Timer {
                    interval: 1000
                    running: true
                    repeat: true
                    onTriggered: parent.text = Qt.formatDateTime(new Date(), "hh:mm:ss")
                }
            }
        }
    }
    
    // Modernized warning popup
    Popup {
        id: warningPopup
        parent: Overlay.overlay
        width: Math.min(Overlay.overlay.width * 0.8, 600)
        height: Math.min(Overlay.overlay.height * 0.8, 400)
        x: (Overlay.overlay.width - width) / 2
        y: (Overlay.overlay.height - height) / 2
        padding: CommonStyle.spacingXl
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        // Dark themed background matching the application style
        background: Rectangle {
            color: CommonStyle.cardBackground
            radius: CommonStyle.radiusMd
            border.width: 1
            border.color: CommonStyle.borderDefault
        }
        
        ColumnLayout {
            anchors.fill: parent
            spacing: CommonStyle.spacingLg
            
            // Header with line separator
            ColumnLayout {
                Layout.fillWidth: true
                spacing: CommonStyle.spacingSm
                
                Text {
                    text: "Warnings"
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontHeading
                    font.weight: Font.Medium
                    color: CommonStyle.textPrimary
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: CommonStyle.borderDefault
                }
            }
            
            // Warnings list
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                ListView {
                    id: listView
                    model: warningHandler.warnings
                    spacing: CommonStyle.spacingMd
                    boundsBehavior: Flickable.StopAtBounds
                    width: parent.width
                    
                    delegate: Rectangle {
                        width: ListView.view.width - CommonStyle.spacingXl
                        height: warningLayout.implicitHeight + CommonStyle.spacingXl
                        color: CommonStyle.warningSurface
                        radius: CommonStyle.radiusSm
                        border.width: 1
                        border.color: CommonStyle.buttonDanger
                        
                        RowLayout {
                            id: warningLayout
                            width: parent.width - CommonStyle.spacingXl
                            anchors.centerIn: parent  // Center in parent
                            spacing: CommonStyle.spacingLg
                            
                            Text {
                                text: "⚠️"
                                font.pixelSize: CommonStyle.fontBody
                            }
                            
                            Text {
                                text: modelData
                                color: CommonStyle.warningText
                                font.family: CommonStyle.fontSans
                                font.pixelSize: CommonStyle.fontCaption
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                            
                            Button {
                                text: "Dismiss"
                                Layout.alignment: Qt.AlignVCenter  // Vertical alignment
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.family: CommonStyle.fontSans
                                    font.pixelSize: CommonStyle.fontCaption
                                    color: CommonStyle.textPrimary
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                background: Rectangle {
                                    color: parent.hovered ? CommonStyle.buttonHover : CommonStyle.buttonSecondary
                                    radius: CommonStyle.radiusSm
                                    implicitHeight: CommonStyle.controlHeightMd - CommonStyle.spacingXs
                                    implicitWidth: Math.round(80 * CommonStyle.scaleFactor)
                                }
                                
                                onClicked: {
                                    if(warningHandler.warnings.length == 1) {
                                        warningPopup.close()
                                    }
                                    warningHandler.remove_warning(index)
                                }
                            }
                        }
                    }
                }
            }
            
            // Footer actions
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }  // Right-align the button
                
                Button {
                    text: "Clear All"
                    
                    contentItem: Text {
                        text: parent.text
                        font.family: CommonStyle.fontSans
                        font.pixelSize: CommonStyle.fontCaption
                        font.weight: Font.Medium
                        color: CommonStyle.textPrimary
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    background: Rectangle {
                        color: parent.hovered ? Qt.darker(CommonStyle.buttonDanger, 1.08) : CommonStyle.buttonDanger
                        radius: CommonStyle.radiusSm
                        implicitHeight: CommonStyle.controlHeightMd
                        implicitWidth: Math.round(100 * CommonStyle.scaleFactor)
                    }
                    
                    onClicked: {
                        warningHandler.clear()
                        warningPopup.close()
                    }
                }
            }
        }
    }
}