import QtQuick
import "../../../theme"


QtObject {
    id: style
    
    // Color scheme
    readonly property color panelBackground: CommonStyle.videoSurface
    readonly property color panelBackgroundLight: CommonStyle.backgroundL1
    readonly property color panelBorderEnabled: CommonStyle.videoBorderEnabled
    readonly property color panelBorderDisabled: CommonStyle.videoBorderDisabled
    readonly property color panelBorderWarning: CommonStyle.videoBorderWarning
    readonly property color labelColor: CommonStyle.textSecondary
    readonly property color valueColor: CommonStyle.textPrimary
    readonly property color dividerColor: CommonStyle.videoDivider
    readonly property color backgroundColor: CommonStyle.backgroundL0
    
    // TopBar specific colors
    readonly property color topBarTextColor: CommonStyle.textPrimary
    readonly property color batteryGoodColor: CommonStyle.statusSuccess
    readonly property color batteryMediumColor: CommonStyle.statusWarning
    readonly property color batteryLowColor: CommonStyle.statusError
    readonly property color signalExcellentColor: CommonStyle.statusSuccess
    readonly property color signalGoodColor: CommonStyle.statusWarning
    readonly property color signalFairColor: CommonStyle.accentMuted
    readonly property color signalPoorColor: CommonStyle.statusError
    readonly property color tempNormalColor: CommonStyle.statusSuccess
    readonly property color tempWarningColor: CommonStyle.statusWarning
    readonly property color tempCriticalColor: CommonStyle.statusError
    readonly property color timeColor: CommonStyle.accentMuted
    
    // Opacity values
    readonly property real panelOpacity: 0.95
    readonly property real borderOpacity: 0.8
    
    // Dimensions
    readonly property int panelWidth: CommonStyle.videoPanelWidth
    readonly property int panelHeight: CommonStyle.videoPanelHeight
    readonly property int smallPanelWidth: Math.round(panelWidth * 0.875)
    readonly property int smallPanelHeight: Math.round(panelHeight * 0.89)
    readonly property int sideMargin: CommonStyle.videoPanelSideMargin
    readonly property int panelRadius: CommonStyle.radiusSm
    readonly property int borderWidth: CommonStyle.borderWidthThick
    readonly property int panelMargins: CommonStyle.videoPanelPadding
    readonly property int contentSpacing: CommonStyle.spacingSm
    readonly property int dividerHeight: 1
    
    // TopBar specific dimensions
    readonly property int topBarHeight: CommonStyle.videoTopBarHeight
    readonly property int topBarSideMargin: CommonStyle.spacingSm + 2
    readonly property int topBarSidePanelWidth: CommonStyle.videoTopBarSideWidth
    readonly property int topBarBatteryWidth: Math.round(100 * CommonStyle.scaleFactor)
    readonly property int topBarNetworkWidth: Math.round(100 * CommonStyle.scaleFactor)
    readonly property int topBarLabelWidth: Math.round(25 * CommonStyle.scaleFactor)
    readonly property int topBarItemSpacing: CommonStyle.spacingSm
    readonly property int topBarCenterSpacing: CommonStyle.spacingLg + CommonStyle.spacingXs
    readonly property int topBarCenterPanelMargin: CommonStyle.spacingSm + 2
    readonly property real topBarDividerHeightRatio: 0.6
    
    // Signal bar dimensions
    readonly property int signalBarWidth: CommonStyle.videoSignalBarWidth
    readonly property int signalBar1Height: CommonStyle.videoSignalBarWidth
    readonly property int signalBar2Height: CommonStyle.videoSignalBarWidth + 2
    readonly property int signalBar3Height: CommonStyle.videoSignalBarWidth + 4
    readonly property real signalBarRadius1: 1.5
    readonly property real signalBarRadius2: 1
    readonly property int signalBarSpacing: CommonStyle.videoSignalBarSpacing
    readonly property real signalBarInactiveOpacity: 0.3
    
    // Font sizes
    readonly property int labelFontSize: CommonStyle.fontLabel - 1
    readonly property int valueFontSize: CommonStyle.fontHeading
    readonly property int titleFontSize: CommonStyle.fontHeading
    readonly property int topBarLabelFontSize: CommonStyle.fontCaption + 1
    readonly property int topBarValueFontSize: CommonStyle.fontLabel
    readonly property int topBarIconFontSize: CommonStyle.fontCaption - 1
    
    // Font properties
    readonly property real labelLetterSpacing: 0.5
    readonly property real valueLetterSpacing: -0.3
    readonly property string topBarFontFamily: CommonStyle.fontMono
    
    // Animation durations
    readonly property int colorAnimationDuration: CommonStyle.motionSlow
    readonly property int fadeAnimationDuration: CommonStyle.motionStandard
    
    // ControlInfoPanel reference dimensions (from VideoFullscreenOverlay)
    readonly property int controlPanelWidth: CommonStyle.videoControlPanelWidth
    readonly property int controlPanelHeight: CommonStyle.videoControlPanelHeight
    readonly property int controlPanelBottomMargin: CommonStyle.videoPanelBottomMargin
    readonly property int controlPanelSideMargin: CommonStyle.videoPanelSideMargin
}
