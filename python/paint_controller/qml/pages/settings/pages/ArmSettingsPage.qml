import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true

    signal backRequested()
    
    
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Arm Settings"
            showBack: true
            onBackClicked: root.backRequested()
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }

        SettingsCategory {
            title: "Arm Presets"
        }

        ManagedSettingSpinBox {
            title: "Retract Length"
            subtitle: "Persisted preset for arm retracted position"
            settingKey: "arm_retract_length"
            integerValue: true
            unit: " mm"
        }

        ManagedSettingSpinBox {
            title: "Extend Length"
            subtitle: "Persisted preset for arm extended position"
            settingKey: "arm_extend_length"
            integerValue: true
            unit: " mm"
        }

        SettingsCategory {
            title: "Live End Effector"
        }

        ManagedSettingSpinBox {
            title: "Thrust Force"
            subtitle: "Persisted and live-applied thrust force target"
            settingKey: "thrust_force"
        }

        ManagedSettingSpinBox {
            title: "Thrust Ramp Rate"
            subtitle: "How quickly thrust force ramps toward target"
            settingKey: "thrust_ramp_rate"
        }

        ManagedSettingSpinBox {
            title: "Valve Turn Maximum"
            subtitle: "Maximum valve turn value for live operation"
            settingKey: "valve_turn_max"
        }
        
        SettingsItem {
            title: "Route Scope"
            subtitle: "This mixed admin route now owns persisted arm presets and selected live end-effector settings. Direct motion controls still live on the runtime surfaces."
            showArrow: false
        }
    }
}