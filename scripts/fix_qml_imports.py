#!/usr/bin/env python3
"""
Fix QML import paths after reorganization
"""

import os
import re
from pathlib import Path

QML_ROOT = Path("/home/c3spray_deck/ros2_ws/src/paint_controller_ros2/qml")

# Mapping of old import paths to new ones based on file location
IMPORT_FIXES = {
    # MainWindow.qml in core/
    "core/MainWindow.qml": {
        r'import "pages"': 'import "../pages/home"\nimport "../pages/spray"\nimport "../pages/trajectory"\nimport "../pages/wheel"\nimport "../pages/winch"\nimport "../pages/tuning"\nimport "../pages/settings"\nimport "../pages/status"\nimport "../pages/misc"',
        r'import "bar"': 'import "../navigation"',
        r'import "components"': 'import "../components/buttons"\nimport "../components/inputs"\nimport "../components/displays"\nimport "../components/panels"\nimport "../components/popups"\nimport "../components/specialized/lidar"\nimport "../components/specialized/video"\nimport "../components/specialized/pointcloud"',
        r'import "overlays"': 'import "../overlays"',
    },
    
    # Pages that import from parent
    "pages/home/PageHome.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    "pages/spray/PageSpray.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    "pages/trajectory/PageTrajectory.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    "pages/wheel/PageWheel.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    "pages/winch/PageWinch.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    "pages/tuning/PageTuning.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    "pages/misc/Page5.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    
    # PageSettings
    "pages/settings/PageSettings.qml": {
        r'import "PageSettings"': 'import "."',
    },
    
    # PageStatus
    "pages/status/PageStatus.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
        r'import "PageStatus"': 'import "."',
    },
    "pages/status/TeensyStatus.qml": {
        r'import "\.\./?"': 'import "../../core"',
        r'import "\.\./\.\./components"': 'import "../../components/buttons"\nimport "../../components/inputs"\nimport "../../components/displays"\nimport "../../components/panels"',
    },
    "pages/status/WheelStatus.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    
    # Navigation
    "navigation/SelectBar.qml": {
        r'import "\.\./?"': 'import "../core"',
    },
    "navigation/TopBar.qml": {
        r'import "\.\./?"': 'import "../core"',
    },
    "navigation/PowerControlTab.qml": {
        r'import "\.\./components"': 'import "../components/buttons"\nimport "../components/panels"',
    },
    
    # Components - need to import CommonStyle from core
    "components/buttons/CustomButton.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/displays/MetricPanel.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/displays/DataDisplay.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/displays/DigitalGauge.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/displays/WindVisualizer.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/inputs/KeyboardPopup.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/inputs/Numpad.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/inputs/NumpadNew.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    "components/popups/CustomPopup.qml": {
        r'import "\.\./?"': 'import "../../core"',
    },
    
    # Panels with special imports
    "components/panels/CommandTab.qml": {
        r'import "\.\./components"': 'import "../buttons"',
    },
    
    # Widgets
    "widgets/actions/ActionSequence.qml": {
        r'import "components"': 'import "../../components/buttons"',
    },
}


def fix_imports_in_file(file_path: Path):
    """Fix imports in a single QML file"""
    relative_path = file_path.relative_to(QML_ROOT)
    rel_path_str = str(relative_path)
    
    if rel_path_str not in IMPORT_FIXES:
        return False
    
    print(f"Fixing imports in: {relative_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    fixes = IMPORT_FIXES[rel_path_str]
    
    for pattern, replacement in fixes.items():
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Updated {relative_path}")
        return True
    else:
        print(f"  - No changes needed for {relative_path}")
        return False


def main():
    print("Fixing QML import paths after reorganization...\n")
    
    fixed_count = 0
    for qml_file in QML_ROOT.rglob("*.qml"):
        if fix_imports_in_file(qml_file):
            fixed_count += 1
    
    print(f"\n✓ Fixed imports in {fixed_count} files")


if __name__ == "__main__":
    main()
