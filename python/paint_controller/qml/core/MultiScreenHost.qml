import QtQuick
import QtQuick.Window
import "../overlays"

/**
 * MultiScreenHost encapsulates the lifecycle of the secondary industrial-monitor
 * window. It reacts to shellState changes and manages creation, placement, and
 * destruction of the MultiScreenListUI window so MainWindow.qml stays focused
 * on shell composition rather than multi-screen window plumbing.
 */
Item {
    id: multiScreenHost

    required property var shellState
    required property var mainWindow

    property var multiScreenWindow: null

    Component {
        id: multiScreenComponent
        MultiScreenListUI {
            id: multiScreenTestWindow
        }
    }

    function toggleMultiScreenWindow() {
        var appScreens = Qt.application.screens
        console.log("MultiScreenHost: Found " + appScreens.length + " screens")

        if (multiScreenWindow === null) {
            var secondaryActive = shellState ? shellState.secondary_surface_active : false
            var secondaryIndex = shellState ? shellState.secondary_surface_screen_index : 0
            if (secondaryActive && appScreens.length > secondaryIndex) {
                ensureSecondaryScreenWindow(appScreens)
            } else {
                multiScreenWindow = multiScreenComponent.createObject(mainWindow)
                if (multiScreenWindow) {
                    multiScreenWindow.showWindow()
                    console.log("MultiScreenHost: window opened (windowed on primary)")
                }
            }
        } else {
            closeSecondaryScreenWindow()
            console.log("MultiScreenHost: window closed")
        }
    }

    function closeSecondaryScreenWindow() {
        if (multiScreenWindow !== null) {
            multiScreenWindow.hideWindow()
            multiScreenWindow.destroy()
            multiScreenWindow = null
        }
    }

    function ensureSecondaryScreenWindow(appScreens) {
        var secondaryActive = shellState ? shellState.secondary_surface_active : false
        var secondaryIndex = shellState ? shellState.secondary_surface_screen_index : 0
        var secondaryFullscreen = shellState ? shellState.secondary_surface_fullscreen : false

        if (!secondaryActive || appScreens.length <= secondaryIndex) {
            closeSecondaryScreenWindow()
            return
        }

        if (multiScreenWindow === null) {
            multiScreenWindow = multiScreenComponent.createObject(mainWindow)
            if (!multiScreenWindow) {
                return
            }
        }

        var secondaryScreen = appScreens[secondaryIndex]
        multiScreenWindow.screen = secondaryScreen
        multiScreenWindow.x = secondaryScreen.virtualX
        multiScreenWindow.y = secondaryScreen.virtualY
        multiScreenWindow.width = secondaryScreen.width
        multiScreenWindow.height = secondaryScreen.height
        multiScreenWindow.targetScreenIndex = secondaryIndex
        multiScreenWindow.fullscreenMode = secondaryFullscreen
        multiScreenWindow.showWindow()
    }

    function applyShellSurfacePolicy() {
        var appScreens = Qt.application.screens
        console.log("MultiScreenHost: Applying shell surface policy, Qt screens: " + appScreens.length)

        var mainScreenIndex = shellState ? shellState.main_surface_screen_index : 0
        var mainSurfaceScreen = appScreens[mainScreenIndex] || appScreens[0]
        if (mainSurfaceScreen && mainWindow) {
            mainWindow.screen = mainSurfaceScreen
            mainWindow.x = mainSurfaceScreen.virtualX
            mainWindow.y = mainSurfaceScreen.virtualY
            mainWindow.width = mainSurfaceScreen.width
            mainWindow.height = mainSurfaceScreen.height
        }

        var secondaryActive = shellState ? shellState.secondary_surface_active : false
        var secondaryIndex = shellState ? shellState.secondary_surface_screen_index : 0
        if (secondaryActive && appScreens.length > secondaryIndex) {
            ensureSecondaryScreenWindow(appScreens)
        } else {
            closeSecondaryScreenWindow()
        }
    }

    Connections {
        target: shellState

        function onScreen_count_changed(count) {
            console.log("MultiScreenHost: Screen configuration changed, shell policy count: " + count)
            screenUpdateTimer.restart()
        }
    }

    Timer {
        id: screenUpdateTimer
        interval: 100  // 100ms delay for Qt to update screen list
        repeat: false
        onTriggered: {
            applyShellSurfacePolicy()
        }
    }
}
