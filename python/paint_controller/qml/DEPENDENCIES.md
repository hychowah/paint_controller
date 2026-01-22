# QML Module Dependencies

This document maps the dependencies between QML modules in the Paint Controller application.

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                        MainWindow.qml                        │
│                      (Application Root)                       │
└──────────────┬────────────────────────────────────────────────┘
               │
               ├──► CommonStyle (singleton) ◄──────────┐
               │                                       │
               ├──► Navigation ──────────────┐        │
               │    - TopBar                 │        │
               │    - SelectBar              │        │
               │                             │        │
               ├──► Pages ───────────────────┼────────┤
               │    - home/                  │        │
               │    - spray/                 │        │
               │    - workflow/              │        │
               │    - wheel/                 │        │
               │    - winch/                 │        │
               │    - tuning/                │        │
               │    - settings/              │        │
               │    - status/                │        │
               │    - misc/                  │        │
               │           │                 │        │
               │           └────────┐        │        │
               │                    ▼        ▼        │
               ├──► Components ◄────┴────────┴────────┤
               │    - buttons/                        │
               │    - displays/                       │
               │    - inputs/                         │
               │    - panels/                         │
               │    - popups/                         │
               │    - specialized/                    │
               │           │                          │
               │           └──────────────────────────┘
               │
               ├──► Overlays ────────────────┐
               │    - Emergency              │
               │    - lidar/                 │
               │    - systemcontrol/         │
               │    - video/                 │
               │           │                 │
               │           └─────────────────┤
               │                             │
               └──► Widgets ─────────────────┘
                    - actions/
```

## Module Import Matrix

### Core Modules
| Module | Imports | Imported By |
|--------|---------|-------------|
| CommonStyle | None (singleton) | All modules |
| MainWindow | All top-level modules | None (root) |

### Navigation
| Module | Imports | Imported By |
|--------|---------|-------------|
| TopBar | core | MainWindow |
| SelectBar | core, components.buttons | MainWindow |

### Components

#### Buttons
| Module | Imports | Imported By |
|--------|---------|-------------|
| ActionButton | core | pages, overlays |
| CustomButton | core | pages, navigation |
| MoveLengthButton | core | pages |
| NumpadButton | core | components.inputs |
| TouchSwitch | core | pages, overlays |

#### Displays
| Module | Imports | Imported By |
|--------|---------|-------------|
| BatteryDisplay | core | pages, overlays |
| DataDisplay | core | pages |
| DigitalGauge | core | pages |
| IMUCard | core | pages.status |
| LineGraph | core | pages |
| MetricPanel | core | pages, overlays |
| Sparkline | core | pages |
| WindVisualizer | core | pages.misc |
| TeensyArmCard | core | pages.status |
| ValvesCard | core | pages.status |
| WheelsCard | core | pages.status |
| WinchCard | core | pages.status |
| YawIndicatorDial | core | pages.home |
| PitchIndicatorDial | core | pages.home |
| MonospaceDataLabel | core | multiple |
| MonitorHeader | core | pages.status |
| IndustrialCard | core | pages.status |
| ProgressBarIndicator | core | pages |

#### Inputs
| Module | Imports | Imported By |
|--------|---------|-------------|
| KeyboardPopup | core, components.buttons | pages |
| Numpad | core, components.buttons | pages, overlays |
| NumpadNew | core, components.buttons | pages |
| TrajNumpad | core, components.buttons | pages.workflow |

#### Panels
| Module | Imports | Imported By |
|--------|---------|-------------|
| ConnectionStatusPanel | core | pages |
| ControlPanel | core | overlays |
| SettingsSection | core | pages.settings |

#### Popups
| Module | Imports | Imported By |
|--------|---------|-------------|
| CustomPopup | core | MainWindow |

#### Specialized
| Module | Imports | Imported By |
|--------|---------|-------------|
| PointCloudEffect | Qt3D | pages |
| PointCloudGeometry | Qt3D | pages |

### Pages

#### Home
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageHome | core, components.* | MainWindow |
| PageLauncher | core, components.* | MainWindow (as page5) |

#### Spray
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageSpray | core, components.* | MainWindow |

#### Workflow
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageWorkFlow | core, components.*, widgets.actions, pages.status | MainWindow |
| WorkFlowControl | core, components.* | PageWorkFlow |

#### Wheel
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageWheel | core, components.* | MainWindow |

#### Winch
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageWinch | core, components.* | MainWindow |

#### Tuning
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageTuning | core, components.* | MainWindow |

#### Settings
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageSettings | core, local components | MainWindow |
| MainSettingsPage | core | PageSettings |
| ArmSettingsPage | core | PageSettings |
| CameraSettingsPage | core | PageSettings |
| WheelsSettingsPage | core | PageSettings |
| WinchSettingsPage | core | PageSettings |
| DetailSettingItem | core | settings pages |
| SettingsCategory | core | settings pages |
| SettingsComponents | core | settings pages |
| SettingsHeader | core | PageSettings |
| SettingsItem | core | settings pages |

#### Status
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageMonitor | core, components.* | MainWindow |
| PageStatus | core, components.* | MainWindow |
| ExecutorPageStatus | core, components.* | PageStatus |
| PlannerPageStatus | core, components.* | PageStatus |
| TeensyStatus | core, components.displays | PageStatus |
| WheelStatus | core, components.displays | PageStatus |

#### Misc
| Module | Imports | Imported By |
|--------|---------|-------------|
| PageEnvironment | core, components.* | None (unused) |

### Overlays

#### Root Level
| Module | Imports | Imported By |
|--------|---------|-------------|
| EmergencyOverlay | core, components | MainWindow |
| MultiScreenListUI | core | MainWindow |
| OverlayLayer | core, components | MainWindow |

#### LiDAR
| Module | Imports | Imported By |
|--------|---------|-------------|
| Lidar2DView | core, Qt3D | MainWindow, LidarOverlay |
| Lidar3DView | core, Qt3D | MainWindow, LidarOverlay |
| LidarOverlay | core, lidar views | MainWindow |

#### System Control
| Module | Imports | Imported By |
|--------|---------|-------------|
| SystemControlMenu | core, tabs | MainWindow |
| CommandTab | core, components.* | SystemControlMenu |
| DeviceControlTab | core, components.* | SystemControlMenu |
| EditWorkFlowTab | core, components.*, widgets.actions | SystemControlMenu |
| SettingsTab | core, components.* | SystemControlMenu |
| WorkFlowTab | core, components.*, widgets.actions | SystemControlMenu |

#### Video
| Module | Imports | Imported By |
|--------|---------|-------------|
| VideoFullscreenOverlay | core, components.panels, video.components | MainWindow |
| BaseFrontOverlay | core | VideoFullscreenOverlay |
| ControlInfoPanel | core | VideoFullscreenOverlay |
| EndEffectorOverlay | core | VideoFullscreenOverlay |
| VideoOverlayStyle | core | VideoFullscreenOverlay |
| VideoOverlayTopBar | core | VideoFullscreenOverlay |
| WallDetectionOverlay | core | VideoFullscreenOverlay |
| WorkFlowStatusOverlay | core | VideoFullscreenOverlay |

### Widgets

#### Actions
| Module | Imports | Imported By |
|--------|---------|-------------|
| ActionItem | core | ActionSequence |
| ActionSequence | core, ActionItem | pages.workflow, overlays |
| SequenceList | core, ActionSequence | pages.workflow, overlays |

## Import Depth Analysis

### Level 0 (No Dependencies)
- CommonStyle.qml (singleton)

### Level 1 (Import only Core)
- Most components.buttons
- Most components.displays
- Most components.inputs
- Most components.panels
- Most components.popups

### Level 2 (Import Core + Components)
- Navigation modules
- Simple pages
- Simple overlays
- Widgets

### Level 3 (Import Core + Components + Other Pages/Modules)
- Complex pages (workflow, status)
- Complex overlays (systemcontrol, video)

## Circular Dependency Prevention

### Rules
1. **Core** modules should never import from non-core modules
2. **Components** can import from core and other components, but not pages/overlays
3. **Pages** and **Overlays** can import anything, but should not import each other
4. **Widgets** can import core and components

### Exceptions
- `PageWorkFlow` imports `pages.status` for workflow status display
- This is acceptable as it's unidirectional and not circular

## Heavy Dependencies

Modules with many imports (potential refactoring candidates):

1. **PageWorkFlow** - Imports 7+ modules
2. **SystemControlMenu** - Imports multiple tabs and components
3. **VideoFullscreenOverlay** - Imports multiple video components

## Unused Components

Components registered in qmldir but not imported anywhere:

1. **PageEnvironment** (pages.misc) - Previously Page5.qml, shows wind/lidar but not used in navigation

## Dependency Management Tips

1. **Before adding new imports**: Check if functionality already exists in a component you're already importing
2. **Keep import lists small**: If a page imports 10+ modules, consider refactoring
3. **Use local components**: For page-specific components, keep them in the same directory
4. **Avoid cross-page imports**: Pages should not import other pages (except for specific status displays)
5. **Document unusual dependencies**: Add comments explaining non-obvious imports

## Tools for Dependency Analysis

```bash
# Find all imports in a file
grep "^import" path/to/file.qml

# Find all files that import a specific module
grep -r "import.*modulename" python/paint_controller/qml/

# Count imports per file
for f in $(find python/paint_controller/qml -name "*.qml"); do 
    echo "$f: $(grep -c "^import" $f)"
done | sort -t: -k2 -n
```
