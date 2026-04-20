import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"
import "../../components/buttons"
import "../../components/inputs"
import "../../components/displays"
import "../../components/panels"

Rectangle {
    id: pageSensorsRect
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Wind data visualization
        WindVisualizer {
            Layout.preferredWidth: parent.width / 4
            Layout.fillHeight: true
            windSpeed: windMonitor.windSpeed || 0
            windDirection: windMonitor.windDirection || 0
        }

        // Lidar visualization
        LidarVisualizer {
            Layout.fillWidth: true
            Layout.fillHeight: true
            points: uiData.lidar_points || []
            showGrid: true
        }
    }
}