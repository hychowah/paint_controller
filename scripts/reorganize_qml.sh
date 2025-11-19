#!/bin/bash

# QML Reorganization Script
# This script reorganizes the QML folder structure for better maintainability

set -e  # Exit on error

QML_DIR="/home/c3spray_deck/ros2_ws/src/paint_controller_ros2/qml"

echo "Starting QML reorganization..."
echo "Working directory: $QML_DIR"

# Create new directory structure
echo "Creating new directory structure..."
mkdir -p "$QML_DIR/core"
mkdir -p "$QML_DIR/pages/home"
mkdir -p "$QML_DIR/pages/spray"
mkdir -p "$QML_DIR/pages/workflow"
mkdir -p "$QML_DIR/pages/wheel"
mkdir -p "$QML_DIR/pages/winch"
mkdir -p "$QML_DIR/pages/tuning"
mkdir -p "$QML_DIR/pages/settings"
mkdir -p "$QML_DIR/pages/status"
mkdir -p "$QML_DIR/pages/misc"
mkdir -p "$QML_DIR/components/buttons"
mkdir -p "$QML_DIR/components/inputs"
mkdir -p "$QML_DIR/components/displays"
mkdir -p "$QML_DIR/components/panels"
mkdir -p "$QML_DIR/components/popups"
mkdir -p "$QML_DIR/components/specialized/lidar"
mkdir -p "$QML_DIR/components/specialized/video"
mkdir -p "$QML_DIR/components/specialized/pointcloud"
mkdir -p "$QML_DIR/navigation"
mkdir -p "$QML_DIR/widgets/actions"

echo "Moving files to new locations..."

# Core files
mv "$QML_DIR/MainWindow.qml" "$QML_DIR/core/" 2>/dev/null || echo "MainWindow.qml already moved"
mv "$QML_DIR/CommonStyle.qml" "$QML_DIR/core/" 2>/dev/null || echo "CommonStyle.qml already moved"

# Pages - Home
mv "$QML_DIR/pages/PageHome.qml" "$QML_DIR/pages/home/" 2>/dev/null || echo "PageHome.qml already moved"
mv "$QML_DIR/pages/PageLauncher.qml" "$QML_DIR/pages/home/" 2>/dev/null || echo "PageLauncher.qml already moved"

# Pages - Spray
mv "$QML_DIR/pages/PageSpray.qml" "$QML_DIR/pages/spray/" 2>/dev/null || echo "PageSpray.qml already moved"

# Pages - WorkFlow
mv "$QML_DIR/pages/PageWorkFlow.qml" "$QML_DIR/pages/workflow/" 2>/dev/null || echo "PageWorkFlow.qml already moved"
mv "$QML_DIR/WorkFlowControl.qml" "$QML_DIR/pages/workflow/" 2>/dev/null || echo "WorkFlowControl.qml already moved"

# Pages - Wheel
mv "$QML_DIR/pages/PageWheel.qml" "$QML_DIR/pages/wheel/" 2>/dev/null || echo "PageWheel.qml already moved"

# Pages - Winch
mv "$QML_DIR/pages/PageWinch.qml" "$QML_DIR/pages/winch/" 2>/dev/null || echo "PageWinch.qml already moved"

# Pages - Tuning
mv "$QML_DIR/pages/PageTuning.qml" "$QML_DIR/pages/tuning/" 2>/dev/null || echo "PageTuning.qml already moved"

# Pages - Settings
mv "$QML_DIR/pages/PageSettings.qml" "$QML_DIR/pages/settings/" 2>/dev/null || echo "PageSettings.qml already moved"
mv "$QML_DIR/pages/PageSettings/"*.qml "$QML_DIR/pages/settings/" 2>/dev/null || echo "Settings files already moved"

# Pages - Status
mv "$QML_DIR/pages/PageStatus.qml" "$QML_DIR/pages/status/" 2>/dev/null || echo "PageStatus.qml already moved"
mv "$QML_DIR/pages/PageStatus/"*.qml "$QML_DIR/pages/status/" 2>/dev/null || echo "Status files already moved"
mv "$QML_DIR/ExecutorPageStatus.qml" "$QML_DIR/pages/status/" 2>/dev/null || echo "ExecutorPageStatus.qml already moved"
mv "$QML_DIR/PlannerPageStatus.qml" "$QML_DIR/pages/status/" 2>/dev/null || echo "PlannerPageStatus.qml already moved"

# Pages - Misc
mv "$QML_DIR/pages/Page5.qml" "$QML_DIR/pages/misc/" 2>/dev/null || echo "Page5.qml already moved"

# Components - Buttons
mv "$QML_DIR/components/CustomButton.qml" "$QML_DIR/components/buttons/" 2>/dev/null || echo "CustomButton.qml already moved"
mv "$QML_DIR/components/MoveLengthButton.qml" "$QML_DIR/components/buttons/" 2>/dev/null || echo "MoveLengthButton.qml already moved"
mv "$QML_DIR/components/NumpadButton.qml" "$QML_DIR/components/buttons/" 2>/dev/null || echo "NumpadButton.qml already moved"
mv "$QML_DIR/components/TouchSwitch.qml" "$QML_DIR/components/buttons/" 2>/dev/null || echo "TouchSwitch.qml already moved"
mv "$QML_DIR/overlays/ActionButton.qml" "$QML_DIR/components/buttons/" 2>/dev/null || echo "ActionButton.qml already moved"

# Components - Inputs
mv "$QML_DIR/components/Numpad.qml" "$QML_DIR/components/inputs/" 2>/dev/null || echo "Numpad.qml already moved"
mv "$QML_DIR/components/NumpadNew.qml" "$QML_DIR/components/inputs/" 2>/dev/null || echo "NumpadNew.qml already moved"
mv "$QML_DIR/components/TrajNumpad.qml" "$QML_DIR/components/inputs/" 2>/dev/null || echo "TrajNumpad.qml already moved"
mv "$QML_DIR/components/KeyboardPopup.qml" "$QML_DIR/components/inputs/" 2>/dev/null || echo "KeyboardPopup.qml already moved"

# Components - Displays
mv "$QML_DIR/components/DataDisplay.qml" "$QML_DIR/components/displays/" 2>/dev/null || echo "DataDisplay.qml already moved"
mv "$QML_DIR/components/DigitalGauge.qml" "$QML_DIR/components/displays/" 2>/dev/null || echo "DigitalGauge.qml already moved"
mv "$QML_DIR/components/MetricPanel.qml" "$QML_DIR/components/displays/" 2>/dev/null || echo "MetricPanel.qml already moved"
mv "$QML_DIR/LineGraph.qml" "$QML_DIR/components/displays/" 2>/dev/null || echo "LineGraph.qml already moved"
mv "$QML_DIR/components/WindVisualizer.qml" "$QML_DIR/components/displays/" 2>/dev/null || echo "WindVisualizer.qml already moved"

# Components - Panels
mv "$QML_DIR/components/ControlInfoPanel.qml" "$QML_DIR/components/panels/" 2>/dev/null || echo "ControlInfoPanel.qml already moved"
mv "$QML_DIR/overlays/ControlPanel.qml" "$QML_DIR/components/panels/" 2>/dev/null || echo "ControlPanel.qml already moved"
mv "$QML_DIR/bar/ConnectionStatusPanel.qml" "$QML_DIR/components/panels/" 2>/dev/null || echo "ConnectionStatusPanel.qml already moved"
mv "$QML_DIR/overlays/CommandTab.qml" "$QML_DIR/components/panels/" 2>/dev/null || echo "CommandTab.qml already moved"

# Components - Popups
mv "$QML_DIR/components/CustomPopup.qml" "$QML_DIR/components/popups/" 2>/dev/null || echo "CustomPopup.qml already moved"
mv "$QML_DIR/WarningDialog.qml" "$QML_DIR/components/popups/" 2>/dev/null || echo "WarningDialog.qml already moved"

# Components - Specialized - Lidar
mv "$QML_DIR/components/Lidar2DView.qml" "$QML_DIR/components/specialized/lidar/" 2>/dev/null || echo "Lidar2DView.qml already moved"
mv "$QML_DIR/components/Lidar3DView.qml" "$QML_DIR/components/specialized/lidar/" 2>/dev/null || echo "Lidar3DView.qml already moved"
mv "$QML_DIR/components/LidarOverlay.qml" "$QML_DIR/components/specialized/lidar/" 2>/dev/null || echo "LidarOverlay.qml already moved"

# Components - Specialized - Video
mv "$QML_DIR/components/VideoFullscreenOverlay.qml" "$QML_DIR/components/specialized/video/" 2>/dev/null || echo "VideoFullscreenOverlay.qml already moved"

# Components - Specialized - Point Cloud
mv "$QML_DIR/PointCloudGeometry.qml" "$QML_DIR/components/specialized/pointcloud/" 2>/dev/null || echo "PointCloudGeometry.qml already moved"
mv "$QML_DIR/PointCloudEffect.qml" "$QML_DIR/components/specialized/pointcloud/" 2>/dev/null || echo "PointCloudEffect.qml already moved"

# Overlays
mv "$QML_DIR/EmergencyOverlay.qml" "$QML_DIR/overlays/" 2>/dev/null || echo "EmergencyOverlay.qml already moved"
mv "$QML_DIR/overlays/OverlayLayer.qml" "$QML_DIR/overlays/" 2>/dev/null || echo "OverlayLayer.qml already moved"
mv "$QML_DIR/overlays/PowerControlMenu.qml" "$QML_DIR/overlays/" 2>/dev/null || echo "PowerControlMenu.qml already moved"

# Navigation
mv "$QML_DIR/bar/TopBar.qml" "$QML_DIR/navigation/" 2>/dev/null || echo "TopBar.qml already moved"
mv "$QML_DIR/bar/SelectBar.qml" "$QML_DIR/navigation/" 2>/dev/null || echo "SelectBar.qml already moved"
mv "$QML_DIR/overlays/PowerControlTab.qml" "$QML_DIR/navigation/" 2>/dev/null || echo "PowerControlTab.qml already moved"

# Widgets - Actions
mv "$QML_DIR/ActionItem.qml" "$QML_DIR/widgets/actions/" 2>/dev/null || echo "ActionItem.qml already moved"
mv "$QML_DIR/ActionSequence.qml" "$QML_DIR/widgets/actions/" 2>/dev/null || echo "ActionSequence.qml already moved"
mv "$QML_DIR/SequenceList.qml" "$QML_DIR/widgets/actions/" 2>/dev/null || echo "SequenceList.qml already moved"

# Clean up old empty directories
echo "Cleaning up old directories..."
rmdir "$QML_DIR/bar" 2>/dev/null || echo "bar directory not empty or already removed"
rmdir "$QML_DIR/overlays" 2>/dev/null || echo "overlays directory not empty or already removed"
rmdir "$QML_DIR/pages/PageSettings" 2>/dev/null || echo "PageSettings directory not empty or already removed"
rmdir "$QML_DIR/pages/PageStatus" 2>/dev/null || echo "PageStatus directory not empty or already removed"
rmdir "$QML_DIR/components" 2>/dev/null || echo "components directory not empty or already removed"
rmdir "$QML_DIR/pages" 2>/dev/null || echo "pages directory not empty or already removed"

echo "File reorganization complete!"
echo ""
echo "New structure created:"
echo "  - core/ (MainWindow, CommonStyle)"
echo "  - pages/ (organized by feature)"
echo "  - components/ (organized by type)"
echo "  - overlays/ (full-screen overlays)"
echo "  - navigation/ (top-level navigation)"
echo "  - widgets/ (domain-specific widgets)"
