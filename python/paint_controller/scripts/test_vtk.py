#!/usr/bin/env python3
"""
Test VTK installation and basic point cloud visualization
Run this before using the full paint controller to verify VTK works
"""

import sys
import os
import numpy as np

# Force Qt to use X11 backend for VTK compatibility (Wayland issues)
if 'QT_QPA_PLATFORM' not in os.environ:
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    print("Note: Setting QT_QPA_PLATFORM=xcb for VTK compatibility")
    print("")

def test_vtk_import():
    """Test if VTK can be imported"""
    print("=" * 60)
    print("Testing VTK Installation")
    print("=" * 60)
    
    try:
        import vtk
        print(f"✓ VTK imported successfully")
        print(f"  Version: {vtk.VTK_VERSION}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import VTK: {e}")
        print("\nInstall VTK with one of these commands:")
        print("  pip install vtk")
        print("  sudo apt install python3-vtk9")
        print("  conda install -c conda-forge vtk")
        return False

def test_qt_vtk():
    """Test Qt + VTK integration"""
    print("\n" + "=" * 60)
    print("Testing Qt + VTK Integration")
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        print("✓ PySide6 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PySide6: {e}")
        return False
    
    try:
        from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
        print("✓ QVTKRenderWindowInteractor imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import QVTKRenderWindowInteractor: {e}")
        print("\nThis may indicate VTK was not built with Qt support.")
        return False

def test_point_cloud_widget():
    """Test the VTKPointCloudWidget"""
    print("\n" + "=" * 60)
    print("Testing VTKPointCloudWidget")
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        import vtk
        
        # IMPORTANT: Create application FIRST, before importing VTK widget
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("✓ QApplication created successfully")
        
        # Now import and create VTK widget
        from paint_controller.widgets.vtk_pointcloud import VTKPointCloudWidget
        
        # Create widget
        widget = VTKPointCloudWidget()
        print("✓ VTKPointCloudWidget created successfully")
        
        # Set window properties BEFORE showing
        widget.setWindowTitle("VTK Test - Spiral Point Cloud")
        widget.resize(800, 600)
        
        # Generate test point cloud
        n_points = 1000
        t = np.linspace(0, 4 * np.pi, n_points)
        x = np.sin(t) * 2
        y = np.cos(t) * 2
        z = t / (4 * np.pi) * 4 - 2
        
        points = np.column_stack([x, y, z])
        
        print(f"  Generated test spiral with {n_points} points")
        
        # Show widget FIRST, then update (important for VTK initialization)
        widget.show()
        print("✓ Widget shown successfully")
        
        # Give the window system time to create the window
        app.processEvents()
        
        # Now update with point cloud data
        widget.update_point_cloud(points)
        print("✓ Point cloud updated successfully")
        
        print("\n" + "=" * 60)
        print("SUCCESS! VTK widget is working.")
        print("A window should appear with a spiral point cloud.")
        print("Close the window to exit.")
        print("=" * 60)
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"✗ Error testing VTKPointCloudWidget: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\nVTK Point Cloud Visualization Test Suite")
    print("This will verify that VTK is properly installed and working.\n")
    
    # Test 1: VTK import
    if not test_vtk_import():
        print("\n❌ FAILED: VTK is not installed or cannot be imported")
        return 1
    
    # Test 2: Qt + VTK integration
    if not test_qt_vtk():
        print("\n❌ FAILED: Qt + VTK integration is not working")
        return 1
    
    # Test 3: Full widget test
    print("\nAll preliminary tests passed!")
    print("Now testing the full VTK widget with visualization...")
    test_point_cloud_widget()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
