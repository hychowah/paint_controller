import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../"

Popup {
    id: keyboard
    width: 650
    height: 450
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
        color: "#80000000"  // Semi-transparent black
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
            duration: 200
            easing.type: Easing.OutQuad
        }
    }
    
    exit: Transition {
        NumberAnimation { 
            property: "y"
            from: parent.height - height
            to: parent.height
            duration: 200
            easing.type: Easing.InQuad
        }
    }
    
    // Background
    background: Rectangle {
        color: "#1a1a1a"
    }
    
    // Content
    ColumnLayout {
        anchors.fill: parent
        spacing: 8
        
        // Text input display
        Rectangle {
            Layout.fillWidth: true
            Layout.margins: 10
            Layout.preferredHeight: 60
            color: "#2d2d2d"
            radius: 8
            
            TextInput {
                id: textDisplay
                anchors.fill: parent
                anchors.margins: 15
                color: "#ffffff"
                font.pixelSize: 18
                font.family: "Sans"
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
                    color: "#0078d7"
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
                spacing: 10
                
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
        radius: 6
        color: {
            if (mouseArea.pressed)
                return accentKey ? "#0051a8" : specialKey ? "#333333" : "#222222";
            else if (toggled)
                return "#0078d7";
            else
                return accentKey ? "#0078d7" : specialKey ? "#444444" : "#3a3a3a";
        }
        
        border.color: Qt.lighter(color, 1.2)
        border.width: 1
        
        // Anti-aliasing for better appearance
        antialiasing: true
        
        // Smooth color transitions
        Behavior on color {
            ColorAnimation { duration: 50 }
        }
        
        // Key text
        Text {
            anchors.centerIn: parent
            text: buttonText
            color: "#ffffff"
            font.pixelSize: parent.width < 70 ? 30 : 36
            font.bold: true
            font.family: "Arial"
            style: Text.Outline
            styleColor: "#000000"
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