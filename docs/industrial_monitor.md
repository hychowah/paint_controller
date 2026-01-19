# Industrial Monitor UI

A dedicated monitoring interface designed for 1280x720 industrial displays, optimized for the Steam Deck built-in screen when an external monitor is connected.

## Overview

The Industrial Monitor provides real-time system telemetry and status visualization with a dark industrial theme. It automatically appears on the Steam Deck's built-in display when an external monitor is connected, while the main UI moves to the external display.

## Layout

### Top Header Bar (80px)

**Left Section - Telemetry:**
- ⚡ Voltage display (V)
- 🌡️ Temperature (°C)
- ⏱️ Loop time (ms)

**Middle Section - Status Badges (Passive):**
- Relay Status: Small badge showing relay on/off state
- System Enable: Large badge showing system enabled/disabled state

**Right Section - Emergency Control (Active):**
- Emergency Stop Button: Prominent red button (200x60px) with pulse effect

### Main Body (3-Column Layout)

**Left Column (30%) - Mobility & Fluids:**
- **Wheels Card:**
  - Left/Right wheel speed (m/s)
  - Current draw (A) with visual progress bar
- **Valves Card:**
  - Flow rate (L/min)
  - Valve position (%) with cyan position indicator

**Center Column (40%) - Core Operations:**
- **Teensy Arm Card:**
  - Extension distance (m) with green bar
  - Arm current vs Spray Gun current (vertical bar charts)
- **Winch Data Card:**
  - Cable length (m)
  - Cable speed (m/s) with directional arrow
  - Winch voltage (V)
  - Torque (Nm) - turns amber when >80% of max

**Right Column (30%) - Sensor Density:**
- **IMU Card:**
  - 4x4 grid: Data Type | X | Y | Z | Trend
  - Rows: Angle (°), Acceleration (g), Angular Acceleration
  - Mini sparkline graphs show last 10 samples for Z-axis values

## Design Principles

1. **Passive vs Active Separation**: Status information is displayed as labels/badges (not clickable), while the E-Stop button is the only active control element
2. **Monospace Numbers**: All numerical values use monospace fonts to prevent layout "shaking" as values update
3. **Color Coding**:
   - Red: Emergency/danger only
   - Green: Nominal/enabled states
   - Cyan: Fluid/motion indicators
   - Amber: Warnings (e.g., high torque)
4. **Visual Hierarchy**: 40% width for core operations (center), 30% for supporting info (sides)

## Data Sources

The monitor pulls real-time data from:
- `teensyController`: IMU, arm, valves, spray gun, system voltage/temp
- `wheelController`: Wheel speeds and motor currents
- `winchController`: Cable position, speed, and motor telemetry

## Components

New reusable components created:
- `IndustrialCard`: Dark-themed card container with rounded corners
- `MonospaceDataLabel`: Label+value+unit with monospace numbers
- `ProgressBarIndicator`: Horizontal progress bar for current/load visualization
- `Sparkline`: Mini line graph for trend visualization

## File Locations

```
python/paint_controller/qml/
├── pages/status/
│   └── PageIndustrialMonitor.qml    # Main industrial monitor page
├── components/displays/
│   ├── IndustrialCard.qml
│   ├── MonospaceDataLabel.qml
│   ├── ProgressBarIndicator.qml
│   └── Sparkline.qml
└── overlays/
    └── MultiScreenListUI.qml        # Window wrapper for secondary screen
```

## Activation

The industrial monitor automatically appears when:
1. A second monitor is connected to the Steam Deck
2. The main UI moves to the external display (index 1)
3. The industrial monitor opens fullscreen on the built-in display (index 0)

When the external monitor is disconnected, the industrial monitor window closes automatically.

## Customization

To adjust max values for progress bars:
- Wheel current max: Line 390, 432 - `maxValue: 10.0` (Amperes)
- Arm extension max: Line 657 - `maxValue: 2000` (millimeters)

To adjust color thresholds:
- Torque warning: Line 782 - `torquePercent > 80` (percent of max)
