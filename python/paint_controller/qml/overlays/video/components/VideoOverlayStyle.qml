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
    
    // TopBar specific colors
    readonly property color topBarTextColor: "#FFFFFF"
    readonly property color batteryGoodColor: "#00FF00"
    readonly property color batteryMediumColor: "#FFAA00"
    readonly property color batteryLowColor: "#FF3333"
    readonly property color signalExcellentColor: "#00FF00"
    readonly property color signalGoodColor: "#FFAA00"
    readonly property color signalFairColor: "#FF8800"
    readonly property color signalPoorColor: "#FF3333"
    readonly property color tempNormalColor: "#00FF00"
    readonly property color tempWarningColor: "#FFAA00"
    readonly property color tempCriticalColor: "#FF3333"
    readonly property color timeColor: "#AAAAFF"
    
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
    
    // TopBar specific dimensions
    readonly property int topBarHeight: 50
    readonly property int topBarSideMargin: 10
    readonly property int topBarSidePanelWidth: 300
    readonly property int topBarBatteryWidth: 100
    readonly property int topBarNetworkWidth: 100
    readonly property int topBarLabelWidth: 25
    readonly property int topBarItemSpacing: 8
    readonly property int topBarCenterSpacing: 20
    readonly property int topBarCenterPanelMargin: 10
    readonly property real topBarDividerHeightRatio: 0.6
    
    // Signal bar dimensions
    readonly property int signalBarWidth: 3
    readonly property int signalBar1Height: 3
    readonly property int signalBar2Height: 5
    readonly property int signalBar3Height: 7
    readonly property real signalBarRadius1: 1.5
    readonly property real signalBarRadius2: 1
    readonly property int signalBarSpacing: 2
    readonly property real signalBarInactiveOpacity: 0.3
    
    // Font sizes
    readonly property int labelFontSize: 10
    readonly property int valueFontSize: 20
    readonly property int titleFontSize: 20
    readonly property int topBarLabelFontSize: 14
    readonly property int topBarValueFontSize: 11
    readonly property int topBarIconFontSize: 12
    
    // Font properties
    readonly property real labelLetterSpacing: 0.5
    readonly property real valueLetterSpacing: -0.3
    readonly property string topBarFontFamily: "Courier New"
    
    // Animation durations
    readonly property int colorAnimationDuration: 300
    readonly property int fadeAnimationDuration: 200
    
    // ControlInfoPanel reference dimensions (from VideoFullscreenOverlay)
    readonly property int controlPanelWidth: 200
    readonly property int controlPanelHeight: 120
    readonly property int controlPanelBottomMargin: 40
    readonly property int controlPanelSideMargin: 20
}
