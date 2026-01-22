# QML Structure Documentation

## Overview

This directory contains all QML UI components for the Paint Controller application. The structure is organized by functional areas with explicit module definitions via `qmldir` files.

## Directory Structure

```
qml/
├── core/                    # Core application components
│   ├── CommonStyle.qml     # Singleton - Global styling constants
│   └── MainWindow.qml      # Main application window
│
├── navigation/             # Navigation UI components
│   ├── TopBar.qml         # Top navigation bar
│   └── SelectBar.qml      # Side navigation/selection bar
│
├── components/            # Reusable UI components
│   ├── buttons/          # Button widgets
│   ├── displays/         # Data display widgets (gauges, graphs, cards)
│   ├── inputs/           # Input widgets (keyboards, numpads)
│   ├── panels/           # Panel containers
│   ├── popups/           # Popup dialogs
│   └── specialized/      # Complex/specialized components
│       └── pointcloud/   # 3D point cloud visualization
│
├── pages/                # Main application pages
│   ├── home/            # Home and launcher pages
│   ├── spray/           # Spray control page
│   ├── workflow/        # Workflow management
│   ├── wheel/           # Wheel controls
│   ├── winch/           # Winch controls
│   ├── tuning/          # System tuning page
│   ├── settings/        # Settings pages and components
│   ├── status/          # Status monitoring pages
│   └── misc/            # Other pages (e.g., environment monitoring)
│
├── overlays/            # Modal overlay components
│   ├── EmergencyOverlay.qml
│   ├── OverlayLayer.qml
│   ├── lidar/          # LiDAR visualization overlays
│   ├── systemcontrol/  # System control menu
│   └── video/          # Video streaming overlays
│       ├── VideoFullscreenOverlay.qml
│       └── components/ # Video overlay sub-components
│
└── widgets/            # Specialized widget modules
    └── actions/        # Action sequence widgets
```

## Module System

Each directory contains a `qmldir` file that defines the QML module. This provides:
- **Explicit module names** for clear imports
- **Version management** for components
- **Better IDE support** and auto-completion
- **Reduced import path complexity**

### Example qmldir File

```qml
module components.buttons
ActionButton 1.0 ActionButton.qml
CustomButton 1.0 CustomButton.qml
TouchSwitch 1.0 TouchSwitch.qml
```

## Import Patterns

### Current Pattern (Relative Imports)
```qml
import "../../core"
import "../../components/buttons"
import "../../components/displays"
```

### With Module System (Future Enhancement)
```qml
import core 1.0
import components.buttons 1.0
import components.displays 1.0
```

**Note**: The application currently uses relative imports. The qmldir files are in place to support future migration to module-based imports and to document the module structure.

## Component Categories

### Core Components
- **CommonStyle.qml**: Singleton providing global styling constants (colors, fonts, sizes)
- **MainWindow.qml**: Root application window, manages page navigation and overlays

### Navigation Components
- **TopBar**: Title bar with system information
- **SelectBar**: Side navigation bar with page selection buttons

### Reusable Components

#### Buttons
Standard button widgets with various styles and behaviors.

#### Displays
Data visualization components:
- Gauges (digital, dial indicators)
- Cards (IMU, wheels, winch, valves)
- Graphs (line graphs, sparklines)
- Indicators (battery, progress bars)

#### Inputs
User input components:
- Keyboard popups
- Numeric keypads (standard and trajectory-specific)

#### Panels
Container components for organizing related UI elements.

#### Specialized
Complex components requiring multiple files or special handling:
- **pointcloud/**: 3D point cloud visualization using Qt3D

### Pages
Full-screen pages accessible via navigation. Each page typically imports multiple components to build its UI.

**Naming Convention**: `Page[Name].qml` (e.g., `PageHome.qml`, `PageSpray.qml`)

### Overlays
Modal UI layers that appear on top of the main content:
- **Emergency**: Critical emergency shutdown UI
- **LiDAR**: 2D/3D LiDAR visualization
- **System Control**: System settings and control menu
- **Video**: Fullscreen video with DJI-style overlay controls

### Widgets
Specialized widget collections for specific features:
- **actions/**: Action sequence visualization and management

## Dependency Guidelines

### Import Order
1. Qt modules (QtQuick, QtQuick.Controls, etc.)
2. Core modules (CommonStyle)
3. Local components (buttons, displays, etc.)
4. Relative imports for co-located files

### Example
```qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"
import "../../components/buttons"
import "../../components/displays"
import "."  // For sibling files in same directory
```

### Dependency Rules
- **Pages** may import: core, components, navigation, widgets
- **Components** may import: core, other components
- **Overlays** may import: core, components
- **Core** should not import from other modules (avoid circular dependencies)

## Adding New Components

1. **Determine the category**: Is it a button, display, page, overlay, etc.?
2. **Create the QML file** in the appropriate directory with descriptive name
3. **Update the qmldir** file in that directory to register the component
4. **Follow naming conventions**:
   - PascalCase for file names
   - Descriptive names (avoid generic names like "Custom", "New", etc.)
   - Pages should start with "Page" prefix
5. **Add appropriate imports** following the import order guidelines

## Naming Conventions

### File Names
- **Pages**: `Page[Feature].qml` (e.g., `PageWorkflow.qml`)
- **Components**: `[Purpose][Type].qml` (e.g., `ActionButton.qml`, `BatteryDisplay.qml`)
- **Avoid**: Generic names like `Page5.qml`, `CustomThing.qml`

### IDs
- Use camelCase
- Make IDs descriptive of the element's purpose
- Example: `pageHomeRect`, `actionButton`, `batteryDisplay`

## Maintenance Tips

1. **Keep modules focused**: Each module should have a clear, single purpose
2. **Avoid deep nesting**: Maximum 3-4 levels of directory nesting
3. **Document complex components**: Add comments for non-obvious behavior
4. **Update qmldir files**: When adding/removing/renaming components, update the qmldir
5. **Check imports**: After moving files, verify all imports are still correct

## Testing Changes

After making structural changes:

```bash
# Build the ROS2 packages
cd ~/ros2_ws
colcon build --packages-select paint_controller_ros2

# Run the application
paint_controller
```

Verify that:
- Application starts without QML errors
- All pages load correctly
- Navigation works as expected
- No missing component warnings in console

## Common Issues

### Import Errors
**Symptom**: `module "X" is not installed` or `Cannot find QML module`
**Solution**: Check that the directory has a `qmldir` file and paths are correct

### Circular Dependencies
**Symptom**: Application hangs or crashes on startup
**Solution**: Review import chains, ensure core components don't import from higher-level modules

### Missing Components
**Symptom**: `Component is not ready` or blank areas in UI
**Solution**: Verify qmldir registration and import paths

## Future Improvements

- [ ] Migrate from relative imports to module-based imports
- [ ] Add QML type documentation comments
- [ ] Consider splitting large pages into sub-components
- [ ] Implement component unit testing framework
- [ ] Create component style guide and examples

## Related Documentation

- Main project README: `/README.md`
- ROS2 documentation: `/src/README.md`
- Python backend: `/python/paint_controller/README.md` (if exists)
