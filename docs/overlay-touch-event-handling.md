# Overlay Touch Event Handling

## Problem
When multiple overlays were displayed on top of each other, touch/mouse events would propagate through all visible overlays to underlying UI components. This caused unintended interactions with buttons and controls that were visually hidden behind overlays.

## Solution
Added `MouseArea` elements to all overlay components to consume touch/mouse events and prevent them from propagating to lower z-index layers.

## Implementation

### Z-Index Hierarchy
Overlays are stacked with the following z-index values (from lowest to highest):

1. **Main Content**: z: 0 (default)
2. **VideoFullscreenOverlay**: z: 500 - For fullscreen video display
3. **Lidar3DView**: z: 600 - For LiDAR point cloud visualization
4. **OverlayLayer**: z: 1000 - For left/right joystick control menus
5. **SystemControlMenu**: z: 1001 - For system settings and controls
6. **EmergencyOverlay**: z: 3000 - For emergency stop (highest priority)

### MouseArea Configuration

Each overlay now has a full-screen `MouseArea` that:
- Fills the entire overlay area
- Is `enabled` based on the overlay's visibility state
- Consumes all mouse/touch events by default (no event propagation)

#### SystemControlMenu
```qml
MouseArea {
    anchors.fill: parent
    enabled: showSystemMenu
    onClicked: overlayController.hide_menu()
}
```

#### VideoFullscreenOverlay
```qml
MouseArea {
    anchors.fill: parent
    enabled: root.active
    onClicked: root.active = false
}
```

#### OverlayLayer
Already had proper MouseArea elements:
```qml
MouseArea {
    anchors.fill: parent
    enabled: showLeftMenu
}
// ... and similar for right menu
```

#### EmergencyOverlay
Already had proper MouseArea:
```qml
MouseArea {
    anchors.fill: parent
    enabled: dimmer.visible
}
```

#### Lidar3DView
Has MouseArea for camera controls that also blocks events:
```qml
MouseArea {
    anchors.fill: parent
    // Handles camera rotation/zoom controls
    // Also blocks events from propagating to lower layers
}
```

## Testing Recommendations

To verify the fix works correctly:

1. **Single Overlay Test**: Open each overlay individually and verify:
   - Overlay responds to touch events
   - Underlying UI does not respond to touch events
   - Overlay can be closed by its designated method

2. **Multiple Overlay Test**: Open overlays in different combinations:
   - System menu + Emergency overlay
   - Video fullscreen + System menu
   - Lidar view + other overlays
   - Verify only the topmost overlay responds to events

3. **Touch Interaction Test**: With an overlay open:
   - Tap on buttons visible behind the overlay
   - Verify no action occurs on the underlying button
   - Verify the overlay handles the touch event appropriately

## QML MouseArea Behavior

Key properties of QML MouseArea that enable this fix:

- **Default Behavior**: MouseArea consumes mouse events by default, preventing them from reaching items with lower z-index
- **enabled**: When false, the MouseArea is transparent to events (events pass through)
- **propagateComposedEvents**: Default is false, meaning events don't propagate to overlapping items
- **z-index**: Higher z-index items receive events first

## Future Considerations

1. **Performance**: Multiple full-screen MouseAreas may have performance implications on low-end devices
2. **Touch Gestures**: If implementing multi-touch or gesture support, ensure MouseArea configuration supports it
3. **Focus Management**: Consider implementing focus management to prevent keyboard input from reaching hidden components
