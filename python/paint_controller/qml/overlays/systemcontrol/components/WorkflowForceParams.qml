import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

GridLayout {
    id: root
    width: parent ? parent.width : 0
    columns: 2
    columnSpacing: 10
    rowSpacing: 8

    required property var editor
    required property var numpad

    Text { text: "Force X:"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
    WorkflowParamField {
        fieldHeight: root.editor.paramFieldHeight
        numpad: root.numpad
        paramKey: "fx"
        defaultValue: 0
        getParamFn: function (k, d) { return root.editor.getParam(k, d) }
        updateParamFn: function (k, v) { root.editor.updateParam(k, v) }
    }

    Text { text: "Force Y:"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
    WorkflowParamField {
        fieldHeight: root.editor.paramFieldHeight
        numpad: root.numpad
        paramKey: "fy"
        defaultValue: 0
        getParamFn: function (k, d) { return root.editor.getParam(k, d) }
        updateParamFn: function (k, v) { root.editor.updateParam(k, v) }
    }
}
