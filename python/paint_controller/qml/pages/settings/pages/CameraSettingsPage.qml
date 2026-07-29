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
    property string calibrationSubtitle: "The truthful camera calibration surface currently lives in the video overlay settings popup."

    function refreshSummary() {
        if (!root.settingsManager) {
            calibrationSubtitle = "The truthful camera calibration surface currently lives in the video overlay settings popup."
            return
        }

        calibrationSubtitle = root.settingsManager.getCameraCalibrationSummary()
    }
    
    
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
            subtitle: root.calibrationSubtitle
            showArrow: false
        }

        SettingsItem {
            title: "Route Scope"
            subtitle: "This route is summary-only for camera calibration in Stage 4. Live base-top adjustments, source points, save, and reset continue to run through the overlay popup."
            showArrow: false
        }
    }

    Connections {
        target: root.settingsManager

        function onSetting_changed(key, value) {
            root.refreshSummary()
        }
    }

    Component.onCompleted: root.refreshSummary()
}
