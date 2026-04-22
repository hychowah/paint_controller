// WindVisualizer.qml - Improved Responsive Version
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"

Rectangle {
    id: windVisualizer
    color: CommonStyle.cardBackgroundAlt
    radius: CommonStyle.radiusMd
    border.color: CommonStyle.cardBorder
    border.width: CommonStyle.borderWidthThin

    required property real windSpeed
    required property real windDirection
    
    // Responsive properties based on available space
    property bool isCompact: height < 300
    property real scaleFactor: Math.min(width / 250, height / 350)
    property real baseMargin: Math.max(5, 15 * scaleFactor)
    property real baseSpacing: Math.max(3, 10 * scaleFactor)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: baseMargin
        spacing: baseSpacing

        // Title - responsive size
        Label {
            text: "Wind Conditions"
            font.pixelSize: isCompact ? 14 : Math.max(12, 18 * scaleFactor)
            font.bold: true
            color: CommonStyle.textPrimary
            Layout.alignment: Qt.AlignHCenter
            // Remove the visible property entirely to always show
        }

        // Wind Direction Indicator - responsive
        Item {
            id: compassContainer
            Layout.preferredWidth: Math.min(parent.width - baseMargin * 2, 
                                          isCompact ? 80 : Math.max(60, 120 * scaleFactor))
            Layout.preferredHeight: Layout.preferredWidth
            Layout.alignment: Qt.AlignHCenter

            // Compass background
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: CommonStyle.inputBackground
                border.color: CommonStyle.cardBorder
                border.width: Math.max(1, 2 * scaleFactor)

                // Cardinal direction markers - only show in non-compact mode
                Repeater {
                    model: isCompact ? [] : ["N", "E", "S", "W"]
                    Label {
                        property real angle: index * 90 - 90
                        property real distance: parent.width/2 - Math.max(8, 15 * scaleFactor)
                        x: parent.width/2 - width/2 + Math.cos(angle * Math.PI/180) * distance
                        y: parent.height/2 - height/2 + Math.sin(angle * Math.PI/180) * distance
                        text: modelData
                        font.bold: true
                        font.pixelSize: Math.max(8, 10 * scaleFactor)
                        color: CommonStyle.textSecondary
                    }
                }

                // Center dot
                Rectangle {
                    anchors.centerIn: parent
                    width: Math.max(4, 6 * scaleFactor)
                    height: width
                    radius: width / 2
                    color: CommonStyle.textSecondary
                }
            }

            // Wind direction arrow - using a simple drawn arrow instead of image
            Canvas {
                id: directionArrow
                anchors.centerIn: parent
                width: parent.width * 0.6
                height: width
                rotation: windDirection

                Behavior on rotation {
                    RotationAnimation {
                        duration: 1000
                        direction: RotationAnimation.Shortest
                        easing.type: Easing.OutCubic
                    }
                }

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    
                    var centerX = width / 2
                    var centerY = height / 2
                    var arrowLength = Math.min(width, height) * 0.35
                    var arrowWidth = arrowLength * 0.3
                    
                    ctx.fillStyle = CommonStyle.accentPrimary
                    ctx.strokeStyle = CommonStyle.buttonPressed
                    ctx.lineWidth = Math.max(1, 2 * scaleFactor)
                    
                    // Draw arrow pointing up (north)
                    ctx.beginPath()
                    ctx.moveTo(centerX, centerY - arrowLength)  // Tip
                    ctx.lineTo(centerX - arrowWidth/2, centerY)  // Left base
                    ctx.lineTo(centerX + arrowWidth/2, centerY)  // Right base
                    ctx.closePath()
                    ctx.fill()
                    ctx.stroke()
                }
            }
        }

        // Wind Speed Display - compact horizontal layout for small spaces
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: isCompact ? 30 : Math.max(25, 50 * scaleFactor)
            color: CommonStyle.inputBackground
            radius: 5
            border.color: CommonStyle.cardBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: Math.max(3, 8 * scaleFactor)
                spacing: Math.max(3, 8 * scaleFactor)

                Label {
                    text: isCompact ? "Speed:" : "Wind Speed:"
                    font.pixelSize: Math.max(12, 12 * scaleFactor)
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(4, 6 * scaleFactor)
                    color: CommonStyle.cardBorder
                    radius: height / 2

                    Rectangle {
                        width: parent.width * Math.min(windSpeed / 30, 1)
                        height: parent.height
                        radius: height / 2
                        color: {
                            if (windSpeed < 10) return CommonStyle.statusSuccess
                            if (windSpeed < 20) return CommonStyle.statusWarning
                            return CommonStyle.statusError
                        }

                        Behavior on width {
                            NumberAnimation {
                                duration: 500
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                }

                Label {
                    text: windSpeed.toFixed(1) + " m/s"
                    font.pixelSize: Math.max(12, 14 * scaleFactor)
                    font.bold: true
                    color: {
                        if (windSpeed < 10) return CommonStyle.statusSuccess
                        if (windSpeed < 20) return CommonStyle.statusWarning
                        return CommonStyle.statusError
                    }
                }
            }
        }

        // Additional wind data - only show in non-compact mode or if there's enough space
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            rowSpacing: Math.max(2, 5 * scaleFactor)
            columnSpacing: Math.max(5, 10 * scaleFactor)
            visible: !isCompact || height > 250

            Label { 
                text: "Direction:"
                font.bold: true
                font.pixelSize: Math.max(8, 10 * scaleFactor)
            }
            Label { 
                text: windDirection.toFixed(0) + "°"
                font.pixelSize: Math.max(8, 10 * scaleFactor)
            }

            Label { 
                text: "Beaufort:"
                font.bold: true
                font.pixelSize: Math.max(8, 10 * scaleFactor)
            }
            Label { 
                text: {
                    if (windSpeed < 0.5) return "0 - Calm"
                    if (windSpeed < 1.5) return "1 - Light"
                    if (windSpeed < 3.3) return "2 - Light"
                    if (windSpeed < 5.5) return "3 - Gentle"
                    if (windSpeed < 7.9) return "4 - Moderate"
                    if (windSpeed < 10.7) return "5 - Fresh"
                    if (windSpeed < 13.8) return "6 - Strong"
                    if (windSpeed < 17.1) return "7 - High"
                    return "8+ - Gale"
                }
                font.pixelSize: Math.max(8, 10 * scaleFactor)
                wrapMode: Text.WordWrap
            }
        }

        // Spacer to push content up
        Item {
            Layout.fillHeight: true
            Layout.minimumHeight: 0
        }
    }

    // Update canvas when wind direction changes
    onWindDirectionChanged: {
        if (directionArrow.available) {
            directionArrow.requestPaint()
        }
    }

    // Update canvas when component is ready
    Component.onCompleted: {
        directionArrow.requestPaint()
    }
}