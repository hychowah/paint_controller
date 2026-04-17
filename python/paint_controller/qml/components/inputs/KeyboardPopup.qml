import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"

Popup {
    id: keyboard
    width: Math.round(650 * CommonStyle.scaleFactor)
    height: Math.round(450 * CommonStyle.scaleFactor)
    padding: 0
    margins: 0
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    
    // Position at bottom of screen
    y: parent.height - height
    x: 0
    
    // Dimming overlay for rest of the screen
    Overlay.modal: Rectangle {
        color: CommonStyle.overlayScrim
    }
    
    // Properties
    property string currentText: ""
    property bool shiftActive: false
    signal textUpdated(string text)
    
    // Animation for keyboard appearance
    enter: Transition {
        NumberAnimation { 
            property: "y"
            from: parent.height
            to: parent.height - height
            duration: CommonStyle.motionStandard
            easing.type: Easing.OutQuad
        }
    }
    
    exit: Transition {
        NumberAnimation { 
            property: "y"
            from: parent.height - height
            to: parent.height
            duration: CommonStyle.motionStandard
            easing.type: Easing.InQuad
        }
    }
    
    // Background
    background: Rectangle {
        color: CommonStyle.backgroundL0
    }
    
    // Content
    ColumnLayout {
        anchors.fill: parent
        spacing: CommonStyle.spacingSm
        
        // Text input display
        Rectangle {
            Layout.fillWidth: true
            Layout.margins: CommonStyle.spacingMd
            Layout.preferredHeight: CommonStyle.itemHeight
            color: CommonStyle.cardBackgroundAlt
            radius: CommonStyle.radiusMd
            
            TextInput {
                id: textDisplay
                anchors.fill: parent
                anchors.margins: CommonStyle.spacingLg
                color: CommonStyle.textPrimary
                font.pixelSize: CommonStyle.fontBody + 2
                font.family: CommonStyle.fontSans
                text: currentText
                clip: true
                onTextChanged: {
                    currentText = text
                    textUpdated(text)
                }
                
                // Cursor
                cursorVisible: true
                cursorDelegate: Rectangle {
                    visible: textDisplay.cursorVisible
                    color: CommonStyle.accentPrimary
                    width: 2
                    height: parent.height * 0.7
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
        
        // Main keyboard grid
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.bottomMargin: 10
            
            // QWERTY layout
            Column {
                anchors.fill: parent
                spacing: CommonStyle.spacingMd
                
                // Row 1 - Numbers
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 8
                    height: (parent.height - parent.spacing * 4) / 5
                    
                    Repeater {
                        model: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
                        
                        KeyButton {
                            width: (keyboard.width - 40) / 10
                            height: parent.height
                            buttonText: modelData
                            onClicked: textDisplay.text += buttonText
                        }
                    }
                }
                
                // Row 2 - QWERTYUIOP
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 5
                    height: (parent.height - parent.spacing * 4) / 5
                    
                    Repeater {
                        model: ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"]
                        
                        KeyButton {
                            width: (keyboard.width - 40) / 10
                            height: parent.height
                            buttonText: modelData
                            onClicked: textDisplay.text += shiftActive ? buttonText : buttonText.toLowerCase()
                        }
                    }
                }
                
                // Row 3 - ASDFGHJKL
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 5
                    height: (parent.height - parent.spacing * 4) / 5
                    
                    Item { width: (keyboard.width - 40) / 20; height: 1 } // Offset
                    
                    Repeater {
                        model: ["A", "S", "D", "F", "G", "H", "J", "K", "L"]
                        
                        KeyButton {
                            width: (keyboard.width - 40) / 10
                            height: parent.height
                            buttonText: modelData
                            onClicked: textDisplay.text += shiftActive ? buttonText : buttonText.toLowerCase()
                        }
                    }
                    
                    // Backspace
                    KeyButton {
                        width: (keyboard.width - 40) / 10 + (keyboard.width - 40) / 20
                        height: parent.height
                        buttonText: "⌫"
                        specialKey: true
                        onClicked: textDisplay.text = textDisplay.text.substring(0, textDisplay.text.length - 1)
                    }
                }
                
                // Row 4 - ZXCVBNM
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 5
                    height: (parent.height - parent.spacing * 4) / 5
                    
                    // Shift key
                    KeyButton {
                        width: (keyboard.width - 40) / 10 + (keyboard.width - 40) / 20
                        height: parent.height
                        buttonText: "⇧"
                        specialKey: true
                        toggled: shiftActive
                        onClicked: shiftActive = !shiftActive
                    }
                    
                    Repeater {
                        model: ["Z", "X", "C", "V", "B", "N", "M"]
                        
                        KeyButton {
                            width: (keyboard.width - 40) / 10
                            height: parent.height
                            buttonText: modelData
                            onClicked: textDisplay.text += shiftActive ? buttonText : buttonText.toLowerCase()
                        }
                    }
                    
                    // Special characters
                    KeyButton {
                        width: (keyboard.width - 40) / 10
                        height: parent.height
                        buttonText: "."
                        onClicked: textDisplay.text += "."
                    }
                    
                    KeyButton {
                        width: (keyboard.width - 40) / 10
                        height: parent.height
                        buttonText: ","
                        onClicked: textDisplay.text += ","
                    }
                }
                
                // Row 5 - Space and controls
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 5
                    height: (parent.height - parent.spacing * 4) / 5
                    
                    // Clear button
                    KeyButton {
                        width: (keyboard.width - 40) / 6
                        height: parent.height
                        buttonText: "Clear"
                        specialKey: true
                        onClicked: textDisplay.text = ""
                    }
                    
                    // Space button
                    KeyButton {
                        width: (keyboard.width - 40) / 2
                        height: parent.height
                        buttonText: "Space"
                        onClicked: textDisplay.text += " "
                    }
                    
                    // Done button
                    KeyButton {
                        width: (keyboard.width - 40) / 6
                        height: parent.height
                        buttonText: "Done"
                        accentKey: true
                        onClicked: keyboard.close()
                    }
                }
            }
        }
    }
    
    // Custom key button component
    component KeyButton: Rectangle {
        id: keyBase
        
        // Properties
        property string buttonText: ""
        property bool specialKey: false
        property bool accentKey: false
        property bool toggled: false
        
        // Signals
        signal clicked()
        
        // Styling
        radius: CommonStyle.radiusSm
        color: {
            if (mouseArea.pressed)
                return accentKey ? CommonStyle.buttonPressed : specialKey ? CommonStyle.backgroundL2 : CommonStyle.backgroundL1;
            else if (toggled)
                return CommonStyle.accentPrimary;
            else
                return accentKey ? CommonStyle.accentPrimary : specialKey ? CommonStyle.cardBackgroundAlt : CommonStyle.cardBackground;
        }
        
        border.color: Qt.lighter(color, 1.2)
        border.width: 1
        
        // Anti-aliasing for better appearance
        antialiasing: true
        
        // Smooth color transitions
        Behavior on color {
            ColorAnimation { duration: CommonStyle.motionFast }
        }
        
        // Key text
        Text {
            anchors.centerIn: parent
            text: buttonText
            color: CommonStyle.textPrimary
            font.pixelSize: parent.width < 70 ? Math.round(30 * CommonStyle.scaleFactor) : Math.round(36 * CommonStyle.scaleFactor)
            font.bold: true
            font.family: CommonStyle.fontSans
            style: Text.Outline
            styleColor: CommonStyle.backgroundL0
            renderType: Text.QtRendering
        }
        
        // Mouse handling
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            onClicked: parent.clicked()
        }
    }
    
    // Shadow effect component
    component DropShadow: Item {
        property real radius: 0
        property int samples: 0
        property color color: "black"
        property int horizontalOffset: 0
        property int verticalOffset: 0
    }
    
    // Function to update current text programmatically
    function updateText(newText) {
        currentText = newText;
        textDisplay.text = newText;
    }
}