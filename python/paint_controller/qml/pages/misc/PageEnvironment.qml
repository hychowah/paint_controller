import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"
import "../../components/buttons"
import "../../components/inputs"
import "../../components/displays"
import "../../components/panels"

Rectangle {
    id: pageEnvironmentRect
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
            windSpeed: windMonitor ? windMonitor.windSpeed || 0 : 0
            windDirection: windMonitor ? windMonitor.windDirection || 0 : 0
        }

        // Lidar visualization
        LidarVisualizer {
            Layout.fillWidth: true
            Layout.fillHeight: true
            points: uiData ? uiData.lidar_points || [] : []
            showGrid: true
        }
    }
}