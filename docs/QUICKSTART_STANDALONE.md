# Quick Start: UI Development Without ROS

This guide shows how to set up and use paint_controller in standalone mode for UI development.

## Setup (One-time)

### 1. Install Python Dependencies

Only Qt/UI dependencies are needed (no ROS):

```bash
# Install PySide6 and core dependencies
pip install PySide6 numpy PyYAML hidapi

# Optional: Install for video streaming (if testing that part of UI)
pip install PyGObject  # requires system GStreamer packages
```

### 2. Install paint_controller

```bash
cd paint_controller
pip install -e .
```

## Running the UI

### Start in Standalone Mode

Simply run the application - it will automatically detect that ROS is not available:

```bash
paint_controller
```

You should see:
```
⚠️  ROS2 not available - running in standalone UI mode
✓ Running in standalone UI mode (no ROS)
```

The UI will launch and be fully functional for development.

## Development Workflow

### 1. Edit QML Files

QML files are in `python/paint_controller/qml/`:
- `qml/core/MainWindow.qml` - Main window
- `qml/pages/` - Different pages/views
- `qml/components/` - Reusable components
- `qml/overlays/` - Overlay UIs

### 2. Live Reload (Optional)

For hot-reload during development, you can modify QML files and they'll update when you navigate away and back, or restart the app.

### 3. Test UI Changes

- Navigation works normally
- Controls can be clicked/interacted with
- Settings can be changed
- Layouts can be verified

### 4. Mock Data (Optional)

If you need mock data for testing, you can add it to the controllers. For example:

```python
# In standalone mode, add a timer to update values
if not ROS2_AVAILABLE:
    self._mock_timer = QTimer()
    self._mock_timer.timeout.connect(self._update_mock_data)
    self._mock_timer.start(100)  # Update every 100ms

def _update_mock_data(self):
    """Update with mock data for UI testing"""
    import random
    self._status['voltage'] = 20 + random.uniform(-0.5, 0.5)
    self.status_changed.emit(self._status)
```

## What You Can Test

✅ **UI Layouts**
- Component positioning
- Responsive design
- Screen transitions
- Multi-monitor support

✅ **User Interactions**
- Button clicks
- Menu navigation
- Form inputs
- Gesture controls

✅ **Visual Design**
- Colors and themes
- Fonts and sizing
- Icons and graphics
- Animations

✅ **Settings**
- Configuration UI
- Persistence
- Validation

## What You Cannot Test

❌ **Hardware Integration**
- Motor control won't actually move motors
- Sensors won't return real data
- Video streams won't connect to cameras

❌ **ROS Communication**
- No topic/service calls
- No bag recording
- No cross-device messaging

For these, you'll need to test in a full ROS environment.

## Tips

### 1. Use Git Branches

Create a branch for UI work:
```bash
git checkout -b ui/my-feature
```

### 2. Focus on One Component

Work on one UI component at a time and test it thoroughly.

### 3. Document Changes

Update relevant documentation:
- QML comments for component behavior
- DEVNOTES.md for significant changes
- Screenshot if major visual change

### 4. Test With ROS Before PR

Before submitting a PR, test in a full ROS environment to ensure nothing broke.

## Common Issues

### Issue: "No module named 'PySide6'"

**Solution**: Install PySide6
```bash
pip install PySide6
```

### Issue: UI doesn't appear

**Solution**: Check X11/display settings
```bash
# On Linux, you may need:
export QT_QPA_PLATFORM=xcb
```

### Issue: Want to test with ROS

**Solution**: Install ROS and rclpy
```bash
# Follow ROS2 installation guide, then:
pip install rclpy
```

The app will automatically detect ROS and use it.

## Example: Adding a New UI Component

1. **Create the QML file**
   ```qml
   // qml/components/MyNewWidget.qml
   import QtQuick 2.15
   import QtQuick.Controls 2.15
   
   Rectangle {
       id: root
       width: 200
       height: 100
       color: "#29303b"
       
       property string displayText: "Hello"
       
       Text {
           anchors.centerIn: parent
           text: root.displayText
           color: "white"
       }
   }
   ```

2. **Import in your page**
   ```qml
   import "../components"
   
   MyNewWidget {
       displayText: "Test"
   }
   ```

3. **Run and test**
   ```bash
   paint_controller
   ```

4. **Iterate** - Make changes and restart to see updates

## Next Steps

Once your UI changes are working in standalone mode:

1. Test in full ROS environment
2. Verify hardware integration still works
3. Update documentation
4. Create PR with screenshots

---

**Questions?** Check `docs/STANDALONE_MODE.md` for more details.
