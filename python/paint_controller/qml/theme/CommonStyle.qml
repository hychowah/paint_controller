pragma Singleton
import QtQuick

QtObject {
    property real scaleFactor: 1.0

    readonly property string fontSans: "Roboto"
    readonly property string fontMono: "Roboto Mono"

    readonly property color backgroundL0: "#0f1b24"
    readonly property color backgroundL1: "#172634"
    readonly property color backgroundL2: "#223447"
    readonly property color backgroundL3: "#36526a"
    readonly property color chromeBackground: "#1d354a"
    readonly property color windowBackground: "#56616b"
    readonly property color sidebarBackground: "#355f84"
    readonly property color sidebarButton: "#5a87ae"
    readonly property color sidebarButtonSelected: "#e7eef5"
    readonly property color cardBackground: "#243748"
    readonly property color cardBackgroundAlt: "#2f465b"
    readonly property color cardBorder: "#3e5972"
    readonly property color accentPrimary: "#4aa3ff"
    readonly property color accentSecondary: "#7ed7ff"
    readonly property color accentMuted: "#8fb6d9"
    readonly property color statusSuccess: "#5bd18b"
    readonly property color statusWarning: "#f3ba4c"
    readonly property color statusError: "#ef625d"
    readonly property color statusInfo: accentPrimary
    readonly property color textPrimary: "#f4f7fb"
    readonly property color textSecondary: "#abc0d1"
    readonly property color textDisabled: "#708395"
    readonly property color textStrong: "#08131b"
    readonly property color textOnPrimary: textPrimary
    readonly property color borderDefault: cardBorder
    readonly property color borderFocused: accentPrimary
    readonly property color overlayScrim: "#b8000000"
    readonly property color inputBackground: "#10202d"
    readonly property color inputBorder: "#45627a"
    readonly property color inputFocusBorder: borderFocused
    readonly property color buttonPrimary: accentPrimary
    readonly property color buttonSecondary: cardBackgroundAlt
    readonly property color buttonDanger: statusError
    readonly property color buttonHover: "#5eb0ff"
    readonly property color buttonPressed: "#2b82dc"
    readonly property color warningSurface: "#3a4857"
    readonly property color warningText: "#ffb398"
    readonly property color videoSurface: "#aa000000"
    readonly property color videoSurfaceStrong: "#cc000000"
    readonly property color videoBorderEnabled: statusSuccess
    readonly property color videoBorderDisabled: statusError
    readonly property color videoBorderWarning: statusWarning
    readonly property color videoDivider: borderDefault
    readonly property color videoCrosshair: "#80f4f7fb"
    readonly property color videoRecording: statusError
    readonly property color videoRuntime: accentPrimary
    readonly property color videoLoop: "#ffd36b"
    readonly property color videoAction: "#fff08a"

    readonly property int spacingXs: Math.round(4 * scaleFactor)
    readonly property int spacingSm: Math.round(8 * scaleFactor)
    readonly property int spacingMd: Math.round(12 * scaleFactor)
    readonly property int spacingLg: Math.round(16 * scaleFactor)
    readonly property int spacingXl: Math.round(24 * scaleFactor)
    readonly property int spacingXxl: Math.round(32 * scaleFactor)

    readonly property int fontDisplay: Math.round(24 * scaleFactor)
    readonly property int fontHeading: Math.round(20 * scaleFactor)
    readonly property int fontBody: Math.round(16 * scaleFactor)
    readonly property int fontCaption: Math.round(13 * scaleFactor)
    readonly property int fontLabel: Math.round(11 * scaleFactor)

    readonly property int radiusSm: Math.round(6 * scaleFactor)
    readonly property int radiusMd: Math.round(10 * scaleFactor)
    readonly property int radiusLg: Math.round(16 * scaleFactor)
    readonly property int borderWidthThin: 1
    readonly property int borderWidthThick: 2
    readonly property int controlHeightMd: Math.round(36 * scaleFactor)
    readonly property int controlHeightLg: Math.round(50 * scaleFactor)
    readonly property int topBarHeight: Math.round(56 * scaleFactor)
    readonly property int sidebarExpandedWidth: Math.round(150 * scaleFactor)
    readonly property int sidebarCollapsedWidth: Math.round(50 * scaleFactor)
    readonly property int sidebarButtonRadius: Math.round(20 * scaleFactor)
    readonly property int sidebarButtonGap: Math.round(20 * scaleFactor)
    readonly property int listRowHeight: Math.round(50 * scaleFactor)
    readonly property int cardRadius: radiusLg
    readonly property int popupWidth: Math.round(450 * scaleFactor)
    readonly property int popupHeight: Math.round(200 * scaleFactor)
    readonly property int videoPanelWidth: Math.round(160 * scaleFactor)
    readonly property int videoPanelHeight: Math.round(90 * scaleFactor)
    readonly property int videoPanelSideMargin: Math.round(20 * scaleFactor)
    readonly property int videoPanelBottomMargin: Math.round(40 * scaleFactor)
    readonly property int videoPanelPadding: spacingMd
    readonly property int videoControlPanelWidth: Math.round(200 * scaleFactor)
    readonly property int videoControlPanelHeight: Math.round(120 * scaleFactor)
    readonly property int videoTopBarHeight: Math.round(50 * scaleFactor)
    readonly property int videoTopBarSideWidth: Math.round(300 * scaleFactor)
    readonly property int videoSignalBarWidth: Math.max(3, Math.round(3 * scaleFactor))
    readonly property int videoSignalBarSpacing: Math.max(2, Math.round(2 * scaleFactor))
    readonly property int panelWidth: videoPanelWidth
    readonly property int panelHeight: videoPanelHeight
    readonly property int panelMargins: videoPanelPadding
    readonly property int contentSpacing: spacingSm
    readonly property int labelFontSize: fontLabel - 1
    readonly property int valueFontSize: fontHeading
    readonly property real labelLetterSpacing: 0.5
    readonly property real valueLetterSpacing: -0.3
    readonly property int controlPanelWidth: videoControlPanelWidth
    readonly property int controlPanelHeight: videoControlPanelHeight
    readonly property int controlPanelBottomMargin: videoPanelBottomMargin
    readonly property int controlPanelSideMargin: videoPanelSideMargin
    readonly property color labelColor: textSecondary
    readonly property color valueColor: textPrimary
    readonly property color dividerColor: videoDivider

    readonly property int motionFast: 150
    readonly property int motionStandard: 250
    readonly property int motionSlow: 300

    readonly property int shellTopBarHeight: 56
    readonly property int shellSidebarExpandedWidth: 150
    readonly property int shellSidebarCollapsedWidth: 50
    readonly property int shellSidebarButtonRadius: 20
    readonly property int shellSidebarButtonGap: 20
    readonly property int shellTopSpacerHeight: 50
    readonly property int shellControlHeightMd: 36
    readonly property int shellStatusBarHeight: 100
    readonly property int shellMessageFont: 16
    readonly property int shellWarningFont: 14
    readonly property int shellClockFont: 18
    readonly property int shellNavLabelFont: 15
    readonly property int shellExitFont: 20
    readonly property int shellStatusTitleFont: 12
    readonly property int shellStatusMetaFont: 10

    readonly property color backgroundColor: cardBackground
    readonly property color secondaryBackground: backgroundL3
    readonly property color borderColor: borderDefault
    readonly property color primaryColor: accentPrimary
    readonly property color secondaryColor: accentSecondary
    readonly property color successColor: statusSuccess
    readonly property color selectedColor: accentSecondary
    readonly property color dangerColor: statusError
    readonly property int radius: radiusLg
    readonly property int smallRadius: radiusSm
    readonly property int borderWidth: borderWidthThin
    readonly property int defaultMargin: spacingMd
    readonly property int defaultSpacing: spacingMd
    readonly property int fontSizeSmall: fontCaption
    readonly property int fontSizeNormal: fontBody
    readonly property int fontSizeLarge: fontHeading
    readonly property int buttonHeight: controlHeightLg
    readonly property int itemHeight: Math.round(60 * scaleFactor)
    readonly property int statusBarHeight: Math.round(100 * scaleFactor)
}