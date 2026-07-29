import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: root
    required property var settingsManager
    property var qtBridge
    contentWidth: availableWidth
    clip: true

    signal backRequested()
        
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Wheels Settings"
            showBack: true
            onBackClicked: root.backRequested()
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }

        SettingsCategory {
            title: "Travel And Speed"
        }

        ManagedSettingSpinBox {

            settingsManager: root.settingsManager
            title: "Track Maximum Speed"
            subtitle: "Upper speed limit for track and wheel motion"
            settingKey: "track_max_speed"
        }

        ManagedSettingSpinBox {

            settingsManager: root.settingsManager
            title: "Track Minimum Speed"
            subtitle: "Minimum speed used to overcome static friction"
            settingKey: "track_min_speed"
        }

        ManagedSettingSpinBox {

            settingsManager: root.settingsManager
            title: "Wheel Travel Maximum"
            subtitle: "Maximum wheel travel distance"
            settingKey: "wheel_travel_max"
            unit: " mm"
        }

        ManagedSettingSpinBox {

            settingsManager: root.settingsManager
            title: "Wheel Travel Rate"
            subtitle: "Adjustment rate for wheel travel commands"
            settingKey: "wheel_travel_rate"
            unit: " mm/s"
        }

        ManagedSettingSpinBox {

            settingsManager: root.settingsManager
            title: "Wheel Travel RPM"
            subtitle: "Fixed RPM used for wheel travel commands"
            settingKey: "wheel_travel_rpm"
            integerValue: true
        }
        
        SettingsItem {
            title: "Route Scope"
            subtitle: "This route owns persisted wheel and travel settings. Live wheel enabling and motion remain on the runtime status and wheel control surfaces."
            showArrow: false
        }
    }
}
