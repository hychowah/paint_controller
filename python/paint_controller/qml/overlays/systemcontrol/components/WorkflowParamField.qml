import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Shared read-only numpad-backed field used by workflow action param forms.
TextField {
    id: root
    Layout.fillWidth: true
    Layout.preferredWidth: 200
    readOnly: true
    color: "#FFFFFF"

    property int fieldHeight: 55
    property var numpad
    property bool ignoreChanges: false
    property string paramKey: ""
    property var defaultValue: 0
    property var getParamFn
    property var updateParamFn

    Layout.preferredHeight: fieldHeight

    background: Rectangle {
        color: "#2A2A2A"
        border.color: "#3A5A8C"
        border.width: 1
        radius: 4
    }

    Component.onCompleted: {
        root.ignoreChanges = true
        text = root.getParamFn(root.paramKey, root.defaultValue).toString()
        root.ignoreChanges = false
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            if (root.numpad) {
                root.numpad.targetField = root
                root.numpad.open()
            }
        }
    }

    onTextChanged: {
        if (!root.ignoreChanges) {
            var val = parseFloat(text)
            if (!isNaN(val)) {
                root.updateParamFn(root.paramKey, val)
            }
        }
    }
}
