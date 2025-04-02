import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Rectangle {
    id: page5Rect
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