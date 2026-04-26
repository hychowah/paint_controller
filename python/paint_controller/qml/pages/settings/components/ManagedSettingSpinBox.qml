import QtQuick

DetailSettingItem {
    id: root

    required property string settingKey
    property bool integerValue: false
    property bool _ready: false

    showSpinBox: true
    minValue: settingsManager ? settingsManager.getMin(settingKey) : 0
    maxValue: settingsManager ? settingsManager.getMax(settingKey) : 100
    spinBoxDecimals: integerValue ? 0 : 1
    currentValue: {
        if (!settingsManager) {
            return 0
        }
        var value = settingsManager[settingKey]
        if (value === undefined || value === null) {
            return 0
        }
        return value
    }

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

    Component.onCompleted: {
        _ready = true
    }
}