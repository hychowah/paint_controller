import QtQuick 2.15

Item {
    id: root
    
    property real range_min: 0.05
    property real range_max: 40.0
    property real fixedMaxRange: 5.0  // This will determine the fixed scale
    
    LidarRenderer {
        id: renderer
        anchors.fill: parent
        pointColor: "red"
    }
    
    // Vertical reference line
    Rectangle {
        id: verticalLine
        width: 1
        height: parent.height
        color: "gray"
        anchors.horizontalCenter: parent.horizontalCenter
    }
    
    // Horizontal reference line
    Rectangle {
        id: horizontalLine
        width: parent.width
        height: 1
        color: "gray"
        anchors.verticalCenter: parent.verticalCenter
    }
    
    Timer {
        interval: 10
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
        
        for (let i = 0; i < ranges.length; i++) {
            let range = ranges[i];
            if (isFinite(range) && range >= root.range_min && range <= root.range_max) {
                let angle = angleMin + i * angleIncrement;
                let x = range * Math.cos(angle);
                let y = range * Math.sin(angle);
                points.push({x: x, y: y});
            }
        }
        
        renderer.updatePoints(points);
        renderer.updateScale(Math.min(root.width, root.height) / (2 * fixedMaxRange));
    }
    
    function updateFixedMaxRange(newMaxRange) {
        fixedMaxRange = newMaxRange;
        // Trigger a redraw of the plot
        updatePlot(/* pass the current ranges and parameters */);
    }
}