import QtQuick 2.15


QtObject {
    id: style
    
    // Color scheme
    readonly property color panelBackground: "#0D0D0D"
    readonly property color panelBackgroundLight: "#1A1A1A"
    readonly property color panelBorderEnabled: "#00FF00"
    readonly property color panelBorderDisabled: "#FF3333"
    readonly property color panelBorderWarning: "#FFAA00"
    readonly property color labelColor: "#FFFFFF"
    readonly property color valueColor: "#FFFFFF"
    readonly property color dividerColor: "#333333"
    readonly property color backgroundColor: "#000000"
    
    // Opacity values
    readonly property real panelOpacity: 0.95
    readonly property real borderOpacity: 0.8
    
    // Dimensions
    readonly property int panelWidth: 160
    readonly property int panelHeight: 90
    readonly property int smallPanelWidth: 140
    readonly property int smallPanelHeight: 80
    readonly property int sideMargin: 20
    readonly property int panelRadius: 8
    readonly property int borderWidth: 2
    readonly property int panelMargins: 12
    readonly property int contentSpacing: 10
    readonly property int dividerHeight: 1
    
    // Font sizes
    readonly property int labelFontSize: 10
    readonly property int valueFontSize: 20
    readonly property int titleFontSize: 20
    
    // Font properties
    readonly property real labelLetterSpacing: 0.5
    readonly property real valueLetterSpacing: -0.3
    
    // Animation durations
    readonly property int colorAnimationDuration: 300
    readonly property int fadeAnimationDuration: 200
    
    // ControlInfoPanel reference dimensions (from VideoFullscreenOverlay)
    readonly property int controlPanelWidth: 200
    readonly property int controlPanelHeight: 120
    readonly property int controlPanelBottomMargin: 40
    readonly property int controlPanelSideMargin: 20
}
