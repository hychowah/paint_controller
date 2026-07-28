import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

GridLayout {
    id: root
    width: 200
    columns: 2
    columnSpacing: 10
    rowSpacing: 8

    required property var editor
    required property var numpad

    Text { text: "Turn Value:"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
    WorkflowParamField {
        fieldHeight: root.editor.paramFieldHeight
        numpad: root.numpad
        paramKey: "turn_value"
        defaultValue: 0
        getParamFn: function (k, d) { return root.editor.getParam(k, d) }
        updateParamFn: function (k, v) { root.editor.updateParam(k, v) }
    }
}
