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
            title: "Winch Settings"
            showBack: true
            onBackClicked: root.backRequested()
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }

        SettingsCategory {
            title: "Available Here"
        }

        ManagedSettingSpinBox {

            settingsManager: root.settingsManager
            title: "Maximum Speed"
            subtitle: "Maximum winch speed limit"
            settingKey: "winch_max_speed_mmps"
            unit: " mm/s"
        }
        
        SettingsItem {
            title: "Route Scope"
            subtitle: "This route now owns persisted winch limit settings. Live motion, torque behavior, and operational controls remain on the dedicated winch surfaces."
            showArrow: false
        }
    }
}