import QtQuick

DetailSettingItem {
    id: root

    required property string settingKey
    property bool integerValue: false
    property bool _ready: false
    property real settingValue: 0

    function refreshValue() {
        if (!settingsManager) {
            root.settingValue = 0
            return
        }

        root.settingValue = integerValue
            ? settingsManager.getInt(settingKey)
            : settingsManager.getFloat(settingKey)
    }

    showSpinBox: true
    minValue: settingsManager ? settingsManager.getMin(settingKey) : 0
    maxValue: settingsManager ? settingsManager.getMax(settingKey) : 100
    spinBoxDecimals: integerValue ? 0 : 1
    currentValue: root.settingValue

    onValueChanged: function(value) {
        if (!_ready || !settingsManager) {
            return
        }
        var ok = integerValue
            ? settingsManager.applyInt(settingKey, Math.round(value))
            : settingsManager.applyFloat(settingKey, value)
        // TD-036: gate deny must not leave the spinbox stuck on the rejected value.
        if (!ok) {
            root.refreshValue()
        }
    }

    Connections {
        target: settingsManager

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