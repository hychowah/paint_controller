// CommonStyle.qml
pragma Singleton
import QtQuick 2.15

QtObject {
    // Colors
    readonly property color backgroundColor: "#FFFFFF"
    readonly property color secondaryBackground: "#9F9F9F"
    readonly property color borderColor: "#E0E0E0"
    readonly property color primaryColor: "#007bff"
    readonly property color secondaryColor: "#d1eafc"
    readonly property color successColor: "#a1f9c6"
    readonly property color selectedColor: "#58ff86"
    readonly property color dangerColor: "#ec3939"
    readonly property color textPrimary: "#000000"
    readonly property color textSecondary: "#6c757d"
    readonly property color textOnPrimary: "#FFFFFF"
    
    // Dimensions
    readonly property int radius: 15
    readonly property int smallRadius: 5
    readonly property int borderWidth: 1
    readonly property int defaultMargin: 10
    readonly property int defaultSpacing: 10
    
    // Fonts
    readonly property int fontSizeSmall: 14
    readonly property int fontSizeNormal: 16
    readonly property int fontSizeLarge: 20
    
    // Component heights
    readonly property int buttonHeight: 50
    readonly property int itemHeight: 60
    readonly property int statusBarHeight: 100
}