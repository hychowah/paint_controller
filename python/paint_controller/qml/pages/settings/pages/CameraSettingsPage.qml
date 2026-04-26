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
            title: "Camera Settings"
            showBack: true
            onBackClicked: root.backRequested()
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }
        
        SettingsItem {
            title: "Base-Top Calibration"
            subtitle: settingsManager
                ? "Saved zoom " + settingsManager.base_top_view_zoom.toFixed(2)
                    + ", crop " + (settingsManager.base_top_view_crop_enabled ? "enabled" : "disabled")
                    + ". Full calibration remains overlay-primary."
                : "The truthful camera calibration surface currently lives in the video overlay settings popup."
            showArrow: false
        }

        SettingsItem {
            title: "Route Scope"
            subtitle: "This route is summary-only for camera calibration in Stage 4. Live base-top adjustments, source points, save, and reset continue to run through the overlay popup."
            showArrow: false
        }
    }
}
