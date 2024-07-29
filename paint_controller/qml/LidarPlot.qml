import QtQuick 2.15

Item {
    id: root
    
    property real range_min: 0.05
    property real range_max: 40.0

    LidarRenderer {
        id: renderer
        anchors.fill: parent
        pointColor: "red"
    }

    Timer {
        interval: 10  // Update every 100ms
        running: true
        repeat: true
        onTriggered: {
            lidar_visualizer.update_plot()
        }
    }

    Connections {
        target: lidar_visualizer
        function onNew_scan_data(ranges, angleMin, angleIncrement, rangeMin, rangeMax) {
            root.range_min = rangeMin
            root.range_max = rangeMax
            updatePlot(ranges, angleMin, angleIncrement)
        }
    }

    function updatePlot(ranges, angleMin, angleIncrement) {
        var points = [];
        var maxRange = 0;

        for (let i = 0; i < ranges.length; i++) {
            let range = ranges[i];
            if (isFinite(range) && range >= root.range_min && range <= root.range_max) {
                let angle = angleMin + i * angleIncrement;
                let x = range * Math.cos(angle);
                let y = range * Math.sin(angle);
                points.push({x: x, y: y});

                maxRange = Math.max(maxRange, range);
            }
        }

        renderer.updatePoints(points);
        renderer.updateScale(Math.min(root.width, root.height) / (2 * maxRange));
    }
}