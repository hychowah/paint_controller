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
        if (integerValue) {
            settingsManager.applyInt(settingKey, Math.round(value))
            return
        }
        settingsManager.applyFloat(settingKey, value)
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