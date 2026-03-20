"""
Fisheye Unwrapper - Real-Time Application
Main entry point for the application.
"""
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from gui.camera_dialog import CameraDialog
from gui.main_window import MainWindow


def main():
    """Main entry point."""
    # Enable OpenGL rendering for better performance
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Fisheye Unwrapper")
    
    # Disable unnecessary effects
    app.setEffectEnabled(Qt.UI_AnimateCombo, False)
    app.setEffectEnabled(Qt.UI_FadeMenu, False)
    
    # Show camera selection dialog
    camera_dialog = CameraDialog()
    result = camera_dialog.exec_()
    
    if result != CameraDialog.Accepted:
        # User canceled
        return 0
        
    # Get selected camera and resolution
    camera_index, resolution = camera_dialog.get_selection()
    
    if camera_index is None:
        QMessageBox.critical(None, "Error", "No camera selected.")
        return 1
        
    print(f"Starting with camera {camera_index} at {resolution[0]}x{resolution[1]}")
    
    # Create and show main window
    main_window = MainWindow(camera_index, resolution)
    main_window.show()
    
    # Run application
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
