// DetailSettingItem.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
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
    property int spinBoxDecimals: 1
    property var valueLabels: []
    property var currentValues: []
    property var inputValues: []
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
            
            Switch {
                visible: showToggle
                checked: toggleValue
                Layout.preferredWidth: 52
                
                onToggled: root.toggled(checked)
                
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
            
            SpinBox {
                visible: showSpinBox
                from: minValue * 10
                to: maxValue * 10
                value: currentValue * 10
                stepSize: 10
                Layout.preferredWidth: 120
                
                property int decimals: root.spinBoxDecimals
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
                
                onValueChanged: root.valueChanged(realValue)
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
                                
                                validator: DoubleValidator {
                                    bottom: minValue
                                    top: maxValue
                                    decimals: 3
                                }
                                
                                onActiveFocusChanged: {
                                    if (activeFocus) {
                                        selectAll()
                                    }
                                }
                                
                                onTextChanged: {
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
                                
                                Keys.onReturnPressed: {
                                    focus = false
                                }
                            }
                            
                            Text {
                                visible: unit !== ""
                                text: unit
                                anchors.right: parent.right
                                anchors.rightMargin: 8
                                anchors.verticalCenter: parent.verticalCenter
                                font.pixelSize: 12
                                color: "#757575"
                            }
                            
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
                        while (finalValues.length < valueLabels.length) {
                            finalValues.push(0)
                        }
                        root.applyInputValues(finalValues)
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
                        inputValues = currentValues.slice()
                    }
                }
            }
        }
        
        // Multiple Values Input (SpinBox version)
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
                            var newValues = currentValues.slice()
                            newValues[index] = realValue
                            root.multipleValuesChanged(newValues)
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
            
            onClicked: root.actionButtonClicked()
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
                
                onValueChanged: root.valueChanged(value)
                
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