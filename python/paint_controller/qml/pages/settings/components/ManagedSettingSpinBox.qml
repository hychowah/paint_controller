import QtQuick

DetailSettingItem {
    id: root

    required property string settingKey
    required property var settingsManager
    property bool integerValue: false
    property bool _ready: false
    property real settingValue: 0

    function refreshValue() {
        if (!root.settingsManager) {
            root.settingValue = 0
            return
        }

        root.settingValue = integerValue
            ? root.settingsManager.getInt(settingKey)
            : root.settingsManager.getFloat(settingKey)
    }

    showSpinBox: true
    minValue: root.settingsManager ? root.settingsManager.getMin(settingKey) : 0
    maxValue: root.settingsManager ? root.settingsManager.getMax(settingKey) : 100
    spinBoxDecimals: integerValue ? 0 : 1
    currentValue: root.settingValue

    onValueChanged: function(value) {
        if (!_ready || !root.settingsManager) {
            return
        }
        var ok = integerValue
            ? root.settingsManager.applyInt(settingKey, Math.round(value))
            : root.settingsManager.applyFloat(settingKey, value)
        // TD-036: gate deny must not leave the spinbox stuck on the rejected value.
        if (!ok) {
            root.refreshValue()
        }
    }

    Connections {
        target: root.settingsManager

        function onSetting_changed(key, value) {
            if (key === root.settingKey) {
                root.refreshValue()
            }
        }
    }

    Component.onCompleted: {
        root.refreshValue()
        _ready = true
    }
}