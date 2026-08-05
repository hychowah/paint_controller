import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "./components"

Item {
    id: commandTab
    required property var manualCommandHandler

    // TD-052: form catalog is Python-owned (manualCommandHandler.commandCatalog).
    readonly property var commandCatalog: manualCommandHandler ? manualCommandHandler.commandCatalog : []
    readonly property var commandLabels: {
        var labels = []
        for (var i = 0; i < commandCatalog.length; i++) {
            labels.push(commandCatalog[i].label)
        }
        return labels
    }

    property string selectedCommandId: ""
    property string selectedCommandLabel: ""
    property var currentParameters: []
    property var parameterValues: ({})
    property bool selectedCommandSupported: {
        if (!selectedCommandId || !manualCommandHandler)
            return false
        return manualCommandHandler.isCommandSupported(selectedCommandId)
    }

    function findCatalogEntry(label) {
        for (var i = 0; i < commandCatalog.length; i++) {
            if (commandCatalog[i].label === label)
                return commandCatalog[i]
        }
        return null
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 20

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

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        text: "Select Command"
                        color: "#FFFFFF"
                        font.pixelSize: 16
                        font.bold: true
                    }

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
                            model: commandTab.commandLabels

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
                                var entry = commandTab.findCatalogEntry(currentText)
                                selectedCommandLabel = currentText
                                selectedCommandId = entry ? entry.id : ""
                                currentParameters = entry ? entry.parameters : []
                                parameterValues = ({})
                                commandDescription.text = entry ? entry.description : ""
                            }
                        }
                    }

                    Text {
                        id: commandDescription
                        Layout.fillWidth: true
                        text: {
                            if (!selectedCommandId) {
                                return "Select a command to see its description"
                            }
                            var entry = null
                            for (var i = 0; i < commandCatalog.length; i++) {
                                if (commandCatalog[i].id === selectedCommandId) {
                                    entry = commandCatalog[i]
                                    break
                                }
                            }
                            if (!entry)
                                return ""
                            if (!selectedCommandSupported) {
                                return entry.description + " (Not yet available in the current backend)"
                            }
                            return entry.description
                        }
                        color: "#CCCCCC"
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }
                }

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
                                                    var filtered = text.replace(/[^0-9.\-]/g, '')
                                                    if (filtered.indexOf('-') !== filtered.lastIndexOf('-')) {
                                                        filtered = filtered.replace(/-/g, '')
                                                    }
                                                    if (filtered.indexOf('-') > 0) {
                                                        filtered = filtered.replace('-', '')
                                                    }
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

                            Item {
                                Layout.fillWidth: true
                                height: 10
                            }
                        }
                    }
                }

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
                        enabled: selectedCommandId !== "" && selectedCommandSupported

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
                                text: selectedCommandId !== "" && !selectedCommandSupported ? "Unavailable" : "Send"
                                color: sendButton.enabled ? "#FFFFFF" : "#999999"
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }
                    }
                }

                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }

    function sendCommand() {
        if (!selectedCommandId)
            return

        if (!manualCommandHandler) {
            console.log("manualCommandHandler is not available")
            return
        }

        if (manualCommandHandler.executeCommand(selectedCommandId, parameterValues)) {
            showCommandFeedback()
        } else {
            console.log("Command rejected:", selectedCommandId)
        }
    }

    function showCommandFeedback() {
        console.log("Command sent successfully!")
    }

    NumpadNew {
        id: numberPad
    }
}
