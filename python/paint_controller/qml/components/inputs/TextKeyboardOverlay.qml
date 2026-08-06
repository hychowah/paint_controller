import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"

/**
 * Full-screen touch text keyboard for naming (workflow Save as, etc.).
 *
 * Owns layout modes (letters / numbers / symbols), shift, and accept/cancel.
 * Callers pass title + initial text and handle accepted(string) / cancelled().
 *
 * Character set is filename-safe: A–Z a–z 0–9 _ -
 * Visual language mirrors NumpadNew / NumpadButton (CommonStyle, large targets).
 */
Popup {
    id: keyboard
    objectName: "textKeyboardOverlay"

    property string title: "Enter name"
    property string initialText: ""
    property string placeholderText: "name"
    property string text: ""
    property string mode: "letters"   // letters | numbers | symbols
    property bool shiftActive: false

    readonly property bool canAccept: text.trim().length > 0

    signal accepted(string text)
    signal cancelled()

    modal: true
    focus: true
    padding: 0
    closePolicy: Popup.CloseOnEscape
    dim: true
    anchors.centerIn: Overlay.overlay
    width: Overlay.overlay ? Overlay.overlay.width : (parent ? parent.width : 1280)
    height: Overlay.overlay ? Overlay.overlay.height : (parent ? parent.height : 800)

    property color buttonColor: CommonStyle.cardBackground
    property color buttonPressedColor: CommonStyle.buttonPressed
    property color buttonBorderColor: CommonStyle.borderFocused
    property color buttonTextColor: CommonStyle.textPrimary
    property color specialButtonColor: CommonStyle.backgroundL1
    property int buttonRadius: CommonStyle.radiusSm
    property int keyFontSize: Math.round(26 * CommonStyle.scaleFactor)
    property int specialFontSize: Math.round(20 * CommonStyle.scaleFactor)
    property int keySpacing: Math.round(6 * CommonStyle.scaleFactor)
    property int rowSpacing: Math.round(8 * CommonStyle.scaleFactor)

    readonly property var letterRow0: ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]
    readonly property var letterRow1: ["a", "s", "d", "f", "g", "h", "j", "k", "l"]
    readonly property var letterRow2: ["z", "x", "c", "v", "b", "n", "m"]
    readonly property var numberRow: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
    readonly property var symbolRow: ["_", "-"]

    function openFor(seed) {
        keyboard.text = (seed !== undefined && seed !== null) ? String(seed) : keyboard.initialText
        keyboard.mode = "letters"
        keyboard.shiftActive = false
        keyboard.open()
    }

    function appendChar(ch) {
        if (!ch || ch.length === 0)
            return
        var out = ch
        if (keyboard.mode === "letters" && keyboard.shiftActive)
            out = ch.toUpperCase()
        keyboard.text += out
        if (keyboard.mode === "letters" && keyboard.shiftActive)
            keyboard.shiftActive = false
    }

    function backspace() {
        if (keyboard.text.length > 0)
            keyboard.text = keyboard.text.slice(0, -1)
    }

    function clearText() {
        keyboard.text = ""
    }

    function toggleShift() {
        keyboard.shiftActive = !keyboard.shiftActive
    }

    function setMode(m) {
        keyboard.mode = m
        keyboard.shiftActive = false
    }

    function accept() {
        var trimmed = keyboard.text.trim()
        if (trimmed.length === 0)
            return
        keyboard.accepted(trimmed)
        keyboard.close()
    }

    function reject() {
        keyboard.cancelled()
        keyboard.close()
    }

    onOpened: {
        if (keyboard.text === "" && keyboard.initialText !== "")
            keyboard.text = keyboard.initialText
    }

    background: Rectangle {
        color: CommonStyle.backgroundL0
    }

    Overlay.modal: Rectangle {
        color: CommonStyle.overlayScrim
    }

    // Key chrome — sized by parent RowLayout, not self-expanding into free space
    component KeyButton: Rectangle {
        id: keyBtn
        property string label: ""
        property string insertChar: ""
        property bool isSpecial: false
        property bool isAccent: false
        property real flex: 1
        signal clicked()

        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.preferredWidth: flex * 10
        Layout.minimumWidth: Math.round(36 * CommonStyle.scaleFactor)
        Layout.minimumHeight: Math.round(44 * CommonStyle.scaleFactor)
        radius: keyboard.buttonRadius
        opacity: enabled ? 1.0 : 0.4
        color: {
            if (!enabled)
                return CommonStyle.backgroundL2
            if (mouseArea.pressed)
                return keyboard.buttonPressedColor
            if (isAccent)
                return CommonStyle.buttonPrimary
            if (isSpecial)
                return keyboard.specialButtonColor
            return keyboard.buttonColor
        }
        border.color: isAccent ? CommonStyle.accentSecondary : keyboard.buttonBorderColor
        border.width: 1

        Behavior on color {
            ColorAnimation { duration: 80 }
        }

        Text {
            anchors.centerIn: parent
            width: parent.width - 4
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            text: keyBtn.label
            color: keyBtn.isAccent ? CommonStyle.textOnPrimary : keyboard.buttonTextColor
            font.pixelSize: keyBtn.isSpecial ? keyboard.specialFontSize : keyboard.keyFontSize
            font.bold: keyBtn.isSpecial || keyBtn.isAccent
            font.family: CommonStyle.fontSans
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            enabled: keyBtn.enabled
            onClicked: {
                if (keyBtn.insertChar !== "")
                    keyboard.appendChar(keyBtn.insertChar)
                keyBtn.clicked()
            }
        }
    }

    component HeaderButton: Rectangle {
        id: hBtn
        property string label: ""
        property bool isAccent: false
        property bool isSpecial: true
        signal clicked()

        Layout.preferredWidth: Math.max(Math.round(120 * CommonStyle.scaleFactor), labelText.implicitWidth + 28)
        Layout.preferredHeight: Math.round(48 * CommonStyle.scaleFactor)
        Layout.fillWidth: false
        Layout.fillHeight: false
        radius: keyboard.buttonRadius
        opacity: enabled ? 1.0 : 0.4
        color: {
            if (!enabled)
                return CommonStyle.backgroundL2
            if (mouseArea.pressed)
                return keyboard.buttonPressedColor
            if (isAccent)
                return CommonStyle.buttonPrimary
            return keyboard.specialButtonColor
        }
        border.color: isAccent ? CommonStyle.accentSecondary : keyboard.buttonBorderColor
        border.width: 1

        Text {
            id: labelText
            anchors.centerIn: parent
            text: hBtn.label
            color: hBtn.isAccent ? CommonStyle.textOnPrimary : keyboard.buttonTextColor
            font.pixelSize: keyboard.specialFontSize
            font.bold: true
            font.family: CommonStyle.fontSans
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            enabled: hBtn.enabled
            onClicked: hBtn.clicked()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Math.round(12 * CommonStyle.scaleFactor)
        spacing: Math.round(10 * CommonStyle.scaleFactor)

        // ---- Header: size to content (never clipped by a short preferredHeight) ----
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: headerCol.implicitHeight + Math.round(24 * CommonStyle.scaleFactor)
            Layout.maximumHeight: Layout.preferredHeight
            Layout.fillHeight: false
            color: CommonStyle.backgroundL1
            radius: CommonStyle.radiusMd
            border.color: CommonStyle.borderDefault
            border.width: 1
            clip: true

            ColumnLayout {
                id: headerCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: Math.round(12 * CommonStyle.scaleFactor)
                spacing: Math.round(10 * CommonStyle.scaleFactor)

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.round(48 * CommonStyle.scaleFactor)
                    spacing: Math.round(10 * CommonStyle.scaleFactor)

                    Text {
                        text: keyboard.title
                        color: CommonStyle.textPrimary
                        font.pixelSize: Math.round(22 * CommonStyle.scaleFactor)
                        font.bold: true
                        font.family: CommonStyle.fontSans
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        verticalAlignment: Text.AlignVCenter
                    }

                    HeaderButton {
                        label: "Cancel"
                        onClicked: keyboard.reject()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.round(56 * CommonStyle.scaleFactor)
                    color: CommonStyle.inputBackground
                    radius: CommonStyle.radiusSm
                    border.color: CommonStyle.inputFocusBorder
                    border.width: 2

                    Text {
                        anchors.fill: parent
                        anchors.leftMargin: Math.round(12 * CommonStyle.scaleFactor)
                        anchors.rightMargin: Math.round(20 * CommonStyle.scaleFactor)
                        text: keyboard.text.length > 0 ? keyboard.text : keyboard.placeholderText
                        color: keyboard.text.length > 0 ? CommonStyle.textPrimary : CommonStyle.textDisabled
                        font.pixelSize: Math.round(24 * CommonStyle.scaleFactor)
                        font.family: CommonStyle.fontMono
                        font.bold: keyboard.text.length > 0
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideLeft
                    }

                    Rectangle {
                        id: caret
                        visible: keyboard.opened
                        width: 2
                        height: parent.height * 0.5
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        anchors.rightMargin: Math.round(12 * CommonStyle.scaleFactor)
                        color: CommonStyle.accentPrimary
                        opacity: caretBlink.lit ? 1 : 0

                        Timer {
                            id: caretBlink
                            property bool lit: true
                            interval: 530
                            running: keyboard.opened
                            repeat: true
                            onTriggered: lit = !lit
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.round(48 * CommonStyle.scaleFactor)
                    spacing: Math.round(10 * CommonStyle.scaleFactor)

                    HeaderButton {
                        label: "Clear"
                        onClicked: keyboard.clearText()
                    }

                    Item { Layout.fillWidth: true }

                    HeaderButton {
                        label: "Save ✓"
                        isAccent: true
                        enabled: keyboard.canAccept
                        onClicked: keyboard.accept()
                    }
                }
            }
        }

        // ---- Keyboard body: 4 equal-height rows ----
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: CommonStyle.backgroundL1
            radius: CommonStyle.radiusMd
            border.color: CommonStyle.borderDefault
            border.width: 1
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Math.round(10 * CommonStyle.scaleFactor)
                spacing: keyboard.rowSpacing

                // Row 1 — primary chars
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: keyboard.keySpacing

                    Repeater {
                        model: keyboard.mode === "numbers" ? keyboard.numberRow
                             : (keyboard.mode === "symbols" ? keyboard.symbolRow : keyboard.letterRow0)
                        delegate: KeyButton {
                            required property string modelData
                            label: keyboard.mode === "letters" && keyboard.shiftActive
                                   ? modelData.toUpperCase() : modelData
                            insertChar: modelData
                        }
                    }
                }

                // Row 2 — home row / spacer symbols
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: keyboard.keySpacing

                    Item {
                        visible: keyboard.mode === "letters"
                        Layout.preferredWidth: Math.round(20 * CommonStyle.scaleFactor)
                        Layout.fillHeight: true
                        Layout.fillWidth: false
                    }

                    Repeater {
                        model: keyboard.mode === "letters" ? keyboard.letterRow1 : []
                        delegate: KeyButton {
                            required property string modelData
                            label: keyboard.shiftActive ? modelData.toUpperCase() : modelData
                            insertChar: modelData
                        }
                    }

                    // Numbers / symbols: second row shows _ and - large
                    KeyButton {
                        visible: keyboard.mode !== "letters"
                        flex: 2
                        label: "_"
                        insertChar: "_"
                    }
                    KeyButton {
                        visible: keyboard.mode !== "letters"
                        flex: 2
                        label: "−"
                        insertChar: "-"
                    }

                    Item {
                        visible: keyboard.mode === "letters"
                        Layout.preferredWidth: Math.round(20 * CommonStyle.scaleFactor)
                        Layout.fillHeight: true
                        Layout.fillWidth: false
                    }
                }

                // Row 3 — shift + bottom letters + backspace
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: keyboard.keySpacing

                    KeyButton {
                        visible: keyboard.mode === "letters"
                        flex: 1.4
                        label: keyboard.shiftActive ? "⇧*" : "⇧"
                        isSpecial: true
                        isAccent: keyboard.shiftActive
                        onClicked: keyboard.toggleShift()
                    }

                    Repeater {
                        model: keyboard.mode === "letters" ? keyboard.letterRow2 : []
                        delegate: KeyButton {
                            required property string modelData
                            label: keyboard.shiftActive ? modelData.toUpperCase() : modelData
                            insertChar: modelData
                        }
                    }

                    // Non-letter modes: empty stretch so backspace stays right-aligned
                    Item {
                        visible: keyboard.mode !== "letters"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }

                    KeyButton {
                        flex: 1.4
                        label: "⌫"
                        isSpecial: true
                        onClicked: keyboard.backspace()
                    }
                }

                // Row 4 — mode switches + underscore (same height as letter rows)
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: keyboard.keySpacing

                    KeyButton {
                        flex: 1.3
                        label: keyboard.mode === "letters" ? "123" : "ABC"
                        isSpecial: true
                        onClicked: {
                            if (keyboard.mode === "letters")
                                keyboard.setMode("numbers")
                            else
                                keyboard.setMode("letters")
                        }
                    }

                    KeyButton {
                        flex: 1.3
                        label: "#+="
                        isSpecial: true
                        isAccent: keyboard.mode === "symbols"
                        onClicked: keyboard.setMode("symbols")
                    }

                    KeyButton {
                        flex: 2.4
                        label: "_"
                        insertChar: "_"
                    }

                    KeyButton {
                        flex: 1.3
                        label: "−"
                        insertChar: "-"
                    }
                }
            }
        }
    }
}
