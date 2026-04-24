pragma Singleton
import QtQuick
import "../theme" as Theme

QtObject {
	readonly property real scaleFactor: Theme.CommonStyle.scaleFactor

	readonly property string fontSans: Theme.CommonStyle.fontSans
	readonly property string fontMono: Theme.CommonStyle.fontMono

	readonly property color backgroundL0: Theme.CommonStyle.backgroundL0
	readonly property color backgroundL1: Theme.CommonStyle.backgroundL1
	readonly property color backgroundL2: Theme.CommonStyle.backgroundL2
	readonly property color backgroundL3: Theme.CommonStyle.backgroundL3
	readonly property color chromeBackground: Theme.CommonStyle.chromeBackground
	readonly property color windowBackground: Theme.CommonStyle.windowBackground
	readonly property color sidebarBackground: Theme.CommonStyle.sidebarBackground
	readonly property color sidebarButton: Theme.CommonStyle.sidebarButton
	readonly property color sidebarButtonSelected: Theme.CommonStyle.sidebarButtonSelected
	readonly property color cardBackground: Theme.CommonStyle.cardBackground
	readonly property color cardBackgroundAlt: Theme.CommonStyle.cardBackgroundAlt
	readonly property color cardBorder: Theme.CommonStyle.cardBorder
	readonly property color accentPrimary: Theme.CommonStyle.accentPrimary
	readonly property color accentSecondary: Theme.CommonStyle.accentSecondary
	readonly property color accentMuted: Theme.CommonStyle.accentMuted
	readonly property color statusSuccess: Theme.CommonStyle.statusSuccess
	readonly property color statusWarning: Theme.CommonStyle.statusWarning
	readonly property color statusError: Theme.CommonStyle.statusError
	readonly property color statusInfo: Theme.CommonStyle.statusInfo
	readonly property color textPrimary: Theme.CommonStyle.textPrimary
	readonly property color textSecondary: Theme.CommonStyle.textSecondary
	readonly property color textDisabled: Theme.CommonStyle.textDisabled
	readonly property color textStrong: Theme.CommonStyle.textStrong
	readonly property color textOnPrimary: Theme.CommonStyle.textOnPrimary
	readonly property color borderDefault: Theme.CommonStyle.borderDefault
	readonly property color borderFocused: Theme.CommonStyle.borderFocused
	readonly property color overlayScrim: Theme.CommonStyle.overlayScrim
	readonly property color inputBackground: Theme.CommonStyle.inputBackground
	readonly property color inputBorder: Theme.CommonStyle.inputBorder
	readonly property color inputFocusBorder: Theme.CommonStyle.inputFocusBorder
	readonly property color buttonPrimary: Theme.CommonStyle.buttonPrimary
	readonly property color buttonSecondary: Theme.CommonStyle.buttonSecondary
	readonly property color buttonDanger: Theme.CommonStyle.buttonDanger
	readonly property color buttonHover: Theme.CommonStyle.buttonHover
	readonly property color buttonPressed: Theme.CommonStyle.buttonPressed
	readonly property color warningSurface: Theme.CommonStyle.warningSurface
	readonly property color warningText: Theme.CommonStyle.warningText

	readonly property int spacingXs: Theme.CommonStyle.spacingXs
	readonly property int spacingSm: Theme.CommonStyle.spacingSm
	readonly property int spacingMd: Theme.CommonStyle.spacingMd
	readonly property int spacingLg: Theme.CommonStyle.spacingLg
	readonly property int spacingXl: Theme.CommonStyle.spacingXl
	readonly property int spacingXxl: Theme.CommonStyle.spacingXxl

	readonly property int fontDisplay: Theme.CommonStyle.fontDisplay
	readonly property int fontHeading: Theme.CommonStyle.fontHeading
	readonly property int fontBody: Theme.CommonStyle.fontBody
	readonly property int fontCaption: Theme.CommonStyle.fontCaption
	readonly property int fontLabel: Theme.CommonStyle.fontLabel

	readonly property int radiusSm: Theme.CommonStyle.radiusSm
	readonly property int radiusMd: Theme.CommonStyle.radiusMd
	readonly property int radiusLg: Theme.CommonStyle.radiusLg
	readonly property int borderWidthThin: Theme.CommonStyle.borderWidthThin
	readonly property int borderWidthThick: Theme.CommonStyle.borderWidthThick
	readonly property int controlHeightMd: Theme.CommonStyle.controlHeightMd
	readonly property int controlHeightLg: Theme.CommonStyle.controlHeightLg
	readonly property int topBarHeight: Theme.CommonStyle.topBarHeight
	readonly property int sidebarExpandedWidth: Theme.CommonStyle.sidebarExpandedWidth
	readonly property int sidebarCollapsedWidth: Theme.CommonStyle.sidebarCollapsedWidth
	readonly property int sidebarButtonRadius: Theme.CommonStyle.sidebarButtonRadius
	readonly property int sidebarButtonGap: Theme.CommonStyle.sidebarButtonGap
	readonly property int listRowHeight: Theme.CommonStyle.listRowHeight
	readonly property int cardRadius: Theme.CommonStyle.cardRadius
	readonly property int popupWidth: Theme.CommonStyle.popupWidth
	readonly property int popupHeight: Theme.CommonStyle.popupHeight

	readonly property int motionFast: Theme.CommonStyle.motionFast
	readonly property int motionStandard: Theme.CommonStyle.motionStandard
	readonly property int motionSlow: Theme.CommonStyle.motionSlow

	readonly property int shellTopBarHeight: Theme.CommonStyle.shellTopBarHeight
	readonly property int shellSidebarExpandedWidth: Theme.CommonStyle.shellSidebarExpandedWidth
	readonly property int shellSidebarCollapsedWidth: Theme.CommonStyle.shellSidebarCollapsedWidth
	readonly property int shellSidebarButtonRadius: Theme.CommonStyle.shellSidebarButtonRadius
	readonly property int shellSidebarButtonGap: Theme.CommonStyle.shellSidebarButtonGap
	readonly property int shellTopSpacerHeight: Theme.CommonStyle.shellTopSpacerHeight
	readonly property int shellControlHeightMd: Theme.CommonStyle.shellControlHeightMd
	readonly property int shellStatusBarHeight: Theme.CommonStyle.shellStatusBarHeight
	readonly property int shellMessageFont: Theme.CommonStyle.shellMessageFont
	readonly property int shellWarningFont: Theme.CommonStyle.shellWarningFont
	readonly property int shellClockFont: Theme.CommonStyle.shellClockFont
	readonly property int shellNavLabelFont: Theme.CommonStyle.shellNavLabelFont
	readonly property int shellExitFont: Theme.CommonStyle.shellExitFont
	readonly property int shellStatusTitleFont: Theme.CommonStyle.shellStatusTitleFont
	readonly property int shellStatusMetaFont: Theme.CommonStyle.shellStatusMetaFont

	readonly property color backgroundColor: Theme.CommonStyle.backgroundColor
	readonly property color secondaryBackground: Theme.CommonStyle.secondaryBackground
	readonly property color borderColor: Theme.CommonStyle.borderColor
	readonly property color primaryColor: Theme.CommonStyle.primaryColor
	readonly property color secondaryColor: Theme.CommonStyle.secondaryColor
	readonly property color successColor: Theme.CommonStyle.successColor
	readonly property color selectedColor: Theme.CommonStyle.selectedColor
	readonly property color dangerColor: Theme.CommonStyle.dangerColor
	readonly property int radius: Theme.CommonStyle.radius
	readonly property int smallRadius: Theme.CommonStyle.smallRadius
	readonly property int borderWidth: Theme.CommonStyle.borderWidth
	readonly property int defaultMargin: Theme.CommonStyle.defaultMargin
	readonly property int defaultSpacing: Theme.CommonStyle.defaultSpacing
	readonly property int fontSizeSmall: Theme.CommonStyle.fontSizeSmall
	readonly property int fontSizeNormal: Theme.CommonStyle.fontSizeNormal
	readonly property int fontSizeLarge: Theme.CommonStyle.fontSizeLarge
	readonly property int buttonHeight: Theme.CommonStyle.buttonHeight
	readonly property int itemHeight: Theme.CommonStyle.itemHeight
	readonly property int statusBarHeight: Theme.CommonStyle.statusBarHeight
}