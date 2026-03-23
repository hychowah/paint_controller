#!/usr/bin/env python3
"""
VTK-based Point Cloud Visualization Widget for Qt
This provides high-performance rendering of large point clouds (10K+ points)
using VTK embedded in a Qt widget.
"""

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QCheckBox
from PySide6.QtCore import Qt, Signal, Slot
import collections
import logging

logger = logging.getLogger(__name__)

try:
    import vtk
    from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    logger.warning("VTK not available. Install with: pip install vtk")


class VTKPointCloudWidget(QWidget):
    """
    A Qt widget that displays point clouds using VTK.
    Much more efficient than QtQuick3D Repeater for large point clouds.
    """
    
    closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set window flags to ensure proper window creation
        self.setWindowFlags(Qt.Window)
        
        if not VTK_AVAILABLE:
            self._setup_error_ui()
            return
        
        self.points_data = collections.deque(maxlen=10)  # Store last 5 frames
        self.color_mode = "z-axis"  # "distance", "height", "uniform", "intensity", "z-axis"
        
        # VTK components
        self.vtk_widget = None
        self.renderer = None
        self.point_cloud_actor = None
        self.axes_actor = None
        self.grid_actor = None
        self.camera_info_actor = None
        
        self._setup_ui()
        self._setup_vtk()
        self._update_camera_info() # Set initial text
        
    def _setup_error_ui(self):
        """Show error message if VTK is not available"""
        layout = QVBoxLayout()
        error_label = QLabel("VTK not installed!\n\nInstall with:\npip install vtk")
        error_label.setStyleSheet("color: red; font-size: 16px;")
        error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(error_label)
        self.setLayout(layout)
        
    def _setup_ui(self):
        """Setup the Qt UI layout"""
        # Set a minimum size for the widget to ensure valid window
        self.setMinimumSize(400, 300)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # VTK render window - explicitly set parent
        self.vtk_widget = QVTKRenderWindowInteractor(parent=self)
        self.vtk_widget.setMinimumSize(400, 250)
        main_layout.addWidget(self.vtk_widget)
        
        # Bottom status bar
        self.status_label = QLabel("Points: 0")
        self.status_label.setStyleSheet("background-color: #1a1a1a; color: #00FF00; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #1a1a1a;")
        
    def _create_control_panel(self):
        """Create the top control panel"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #2a2a2a; padding: 5px;")
        layout = QHBoxLayout()
        
        # Title
        title = QLabel("LiDAR 3D View (VTK)")
        title.setStyleSheet("color: #00FF00; font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Color mode selector
        layout.addWidget(QLabel("Color:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Z-Axis", "Distance", "Height", "Uniform", "Intensity"])
        self.color_combo.setCurrentText("Z-Axis")
        self.color_combo.currentTextChanged.connect(self._on_color_mode_changed)
        layout.addWidget(self.color_combo)
        
        # Grid toggle
        self.grid_checkbox = QCheckBox("Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.stateChanged.connect(self._toggle_grid)
        layout.addWidget(self.grid_checkbox)
        
        # Axes toggle
        self.axes_checkbox = QCheckBox("Axes")
        self.axes_checkbox.setChecked(True)
        self.axes_checkbox.stateChanged.connect(self._toggle_axes)
        layout.addWidget(self.axes_checkbox)
        
        # Reset view button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self._reset_camera)
        layout.addWidget(reset_btn)
        
        # Zoom buttons
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self._zoom_in)
        layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self._zoom_out)
        layout.addWidget(zoom_out_btn)
        
        # Close button
        close_btn = QPushButton("Close [A]")
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)
        
        panel.setLayout(layout)
        return panel
        
    def _setup_vtk(self):
        """Setup VTK rendering pipeline"""
        # Get the render window first
        render_window = self.vtk_widget.GetRenderWindow()
        
        # Create renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(48/255, 48/255, 48/255)  # RViz background
        
        # Add renderer to render window
        render_window.AddRenderer(self.renderer)
        
        # Setup camera for XY plane (Z-up)
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(-6.4, -8.5, 3.1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0.2, 0.2, 1)
        camera.SetClippingRange(0.01, 1000) # Set near and far clipping planes
        
        # Add axes
        self._add_axes()
        
        # Add grid
        self._add_grid()
        
        # Add camera info text
        self._add_camera_info_text()
        
        # Setup interactor style (trackball camera)
        interactor_style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.GetRenderWindow().GetInteractor().SetInteractorStyle(interactor_style)
        
        # Add observer for camera changes to update the text
        self.renderer.GetActiveCamera().AddObserver("ModifiedEvent", self._update_camera_info)
    
    def _add_axes(self):
        """Add coordinate axes to the scene"""
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(1, 1, 1)  # RViz length
        axes.SetShaftTypeToCylinder()
        axes.SetCylinderRadius(0.02) # RViz radius is 0.1, but that's too thick
        axes.SetAxisLabels(1)  # Show X, Y, Z labels
        
        self.axes_actor = axes
        self.renderer.AddActor(axes)
        logger.debug("Axes added to renderer")
        
    def _add_grid(self):
        """Add a ground grid to the scene"""
        # Create a plane on the XY plane (Z=0)
        plane = vtk.vtkPlaneSource()
        plane.SetOrigin(-10, -10, 0)
        plane.SetPoint1(10, -10, 0)
        plane.SetPoint2(-10, 10, 0)
        plane.SetXResolution(20) # RViz Plane Cell Count
        plane.SetYResolution(20) # RViz Plane Cell Count
        
        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(plane.GetOutputPort())
        
        # Create actor
        self.grid_actor = vtk.vtkActor()
        self.grid_actor.SetMapper(mapper)
        self.grid_actor.GetProperty().SetColor(160/255, 160/255, 164/255)  # RViz color
        self.grid_actor.GetProperty().SetRepresentationToWireframe()
        self.grid_actor.GetProperty().SetLineWidth(1)
        self.grid_actor.GetProperty().SetOpacity(0.5) # RViz Alpha
        
        self.renderer.AddActor(self.grid_actor)
        logger.debug("Grid added to renderer")
        
    def _add_camera_info_text(self):
        """Add text actor for displaying camera info."""
        self.camera_info_actor = vtk.vtkTextActor()
        self.camera_info_actor.GetTextProperty().SetFontSize(12)
        self.camera_info_actor.GetTextProperty().SetColor(0.9, 0.9, 0.9)  # Light gray
        self.camera_info_actor.SetPosition(10, 10)  # Display coordinates
        self.renderer.AddActor2D(self.camera_info_actor)
        logger.debug("Camera info text actor added")

    def _update_camera_info(self, *args):
        """Update the text with the current camera viewpoint."""
        if not self.renderer or not self.camera_info_actor:
            return
        
        camera = self.renderer.GetActiveCamera()
        pos = camera.GetPosition()
        focal = camera.GetFocalPoint()
        up = camera.GetViewUp()
        
        info_text = (
            f"Pos: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})\n"
            f"Focal: ({focal[0]:.1f}, {focal[1]:.1f}, {focal[2]:.1f})\n"
            f"Up: ({up[0]:.1f}, {up[1]:.1f}, {up[2]:.1f})"
        )
        
        self.camera_info_actor.SetInput(info_text)
        
        # The render window will automatically update on interaction
        # but we might need to call it if changed programmatically
        if self.vtk_widget and self.vtk_widget.GetRenderWindow():
            self.vtk_widget.GetRenderWindow().Render()
        
    def update_point_cloud(self, points):
        """
        Update the point cloud visualization
        
        Args:
            points: List of dicts with 'x', 'y', 'z' keys, or numpy array of shape (N, 3)
        """
        if not VTK_AVAILABLE:
            return
            
        # Handle empty points
        if points is None:
            return
        
        # Check if points is empty (works for both list and numpy array)
        try:
            if len(points) == 0:
                return
        except:
            return
        
        logger.debug("Updating point cloud with %d points", len(points))
        
        self.points_data.append(points)
        
        # Combine points from recent frames
        all_points = np.vstack(self.points_data)
        
        # Convert points to numpy array
        if isinstance(all_points, list):
            points_array = np.array([[p['x'], p['y'], p['z']] for p in all_points])
        else:
            points_array = all_points
        
        # Update status
        self.status_label.setText(f"Points: {len(points_array)}")
        
        # Remove old point cloud if exists
        if self.point_cloud_actor:
            self.renderer.RemoveActor(self.point_cloud_actor)
        
        # Create VTK points
        vtk_points = vtk.vtkPoints()
        for point in points_array:
            vtk_points.InsertNextPoint(point[0], point[1], point[2])
        
        # Create polydata
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(vtk_points)
        
        # Create vertex cells for each point
        vertices = vtk.vtkCellArray()
        for i in range(len(points_array)):
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(i)
        polydata.SetVerts(vertices)
        
        # Generate colors based on mode
        colors = self._generate_colors(points_array)
        vtk_colors = vtk.vtkUnsignedCharArray()
        vtk_colors.SetNumberOfComponents(3)
        vtk_colors.SetName("Colors")
        
        for color in colors:
            vtk_colors.InsertNextTuple3(
                int(color[0] * 255),
                int(color[1] * 255),
                int(color[2] * 255)
            )
        
        polydata.GetPointData().SetScalars(vtk_colors)
        
        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        
        # Create actor
        self.point_cloud_actor = vtk.vtkActor()
        self.point_cloud_actor.SetMapper(mapper)
        self.point_cloud_actor.GetProperty().SetPointSize(2) # RViz Size (Pixels)
        
        # Add to renderer
        self.renderer.AddActor(self.point_cloud_actor)
        
        logger.debug("Point cloud actor created and added to renderer")
        
        # Force render if widget is visible
        if self.isVisible() and self.vtk_widget:
            self.vtk_widget.GetRenderWindow().Render()
            logger.debug("Render triggered")
        
    def _generate_colors(self, points_array):
        """Generate colors for points based on current color mode"""
        num_points = len(points_array)
        colors = np.zeros((num_points, 3))
        
        if self.color_mode == "uniform":
            # All green
            colors[:, 1] = 1.0
            
        elif self.color_mode == "height":
            # Color based on Y (height)
            y_values = points_array[:, 1]
            y_normalized = (y_values - y_values.min()) / (y_values.max() - y_values.min() + 1e-6)
            
            # Blue to green to red gradient
            colors[:, 0] = y_normalized  # Red channel
            colors[:, 1] = 1.0 - np.abs(y_normalized - 0.5) * 2  # Green channel
            colors[:, 2] = 1.0 - y_normalized  # Blue channel

        elif self.color_mode == "z-axis":
            # Color based on Z (depth), RViz style
            z_values = points_array[:, 2]
            z_min, z_max = z_values.min(), z_values.max()
            z_normalized = (z_values - z_min) / (z_max - z_min + 1e-6)
            
            # Create a lookup table (LUT) for rainbow colors
            lut = vtk.vtkLookupTable()
            lut.SetHueRange(0.667, 0.0) # Blue to Red
            lut.Build()

            rgb = [0.0, 0.0, 0.0]
            for i in range(num_points):
                lut.GetColor(z_normalized[i], rgb)
                colors[i] = rgb[:]
            
        elif self.color_mode == "distance":
            # Color based on distance from origin (rainbow)
            distances = np.linalg.norm(points_array, axis=1)
            max_dist = 10.0
            ratios = np.clip(distances / max_dist, 0, 1)
            
            # Rainbow gradient
            for i, ratio in enumerate(ratios):
                if ratio < 0.2:
                    t = ratio / 0.2
                    colors[i] = [0.5 - t * 0.5, 0, 1]
                elif ratio < 0.4:
                    t = (ratio - 0.2) / 0.2
                    colors[i] = [0, t, 1]
                elif ratio < 0.6:
                    t = (ratio - 0.4) / 0.2
                    colors[i] = [0, 1, 1 - t]
                elif ratio < 0.8:
                    t = (ratio - 0.6) / 0.2
                    colors[i] = [t, 1, 0]
                else:
                    t = (ratio - 0.8) / 0.2
                    colors[i] = [1, 1 - t, 0]
                    
        else:  # intensity or default
            # Uniform green as fallback
            colors[:, 1] = 1.0
            
        return colors
        
    @Slot(str)
    def _on_color_mode_changed(self, mode_text):
        """Handle color mode change"""
        self.color_mode = mode_text.lower()
        
        # Re-render with new colors
        if self.points_data:
            self.update_point_cloud(self.points_data)
            
    @Slot(int)
    def _toggle_grid(self, state):
        """Toggle grid visibility"""
        if self.grid_actor:
            self.grid_actor.SetVisibility(state == Qt.Checked)
            self.vtk_widget.GetRenderWindow().Render()
            
    @Slot(int)
    def _toggle_axes(self, state):
        """Toggle axes visibility"""
        if self.axes_actor:
            self.axes_actor.SetVisibility(state == Qt.Checked)
            self.vtk_widget.GetRenderWindow().Render()
            
    @Slot()
    def _reset_camera(self):
        """Reset camera to default position"""
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0, 12, 0)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, -1)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        
    @Slot()
    def _zoom_in(self):
        """Zoom the camera in"""
        if self.renderer:
            self.renderer.GetActiveCamera().Dolly(1.1)
            self.vtk_widget.GetRenderWindow().Render()

    @Slot()
    def _zoom_out(self):
        """Zoom the camera out"""
        if self.renderer:
            self.renderer.GetActiveCamera().Dolly(0.9)
            self.vtk_widget.GetRenderWindow().Render()
        
    @Slot()
    def _on_close(self):
        """Handle close button click"""
        self.close()
        
    def showEvent(self, event):
        """Handle widget show event"""
        super().showEvent(event)
        if VTK_AVAILABLE and self.vtk_widget:
            # Initialize interactor on first show
            if not self.vtk_widget.GetRenderWindow().GetInteractor().GetInitialized():
                self.vtk_widget.GetRenderWindow().GetInteractor().Initialize()
                logger.debug("Interactor initialized")
            
            # Reset camera to ensure everything is visible
            # self.renderer.ResetCamera() # This overrides custom viewpoints
            
            # Force a render to show axes, grid, and any existing point cloud
            self.vtk_widget.GetRenderWindow().Render()
            logger.debug("Initial render on show")
            
    def closeEvent(self, event):
        """Clean up VTK resources and signal closure"""
        self.closed.emit()
        if VTK_AVAILABLE and self.vtk_widget:
            # This can cause hangs, so we'll rely on application exit to clean up
            # self.vtk_widget.Finalize()
            pass
        super().closeEvent(event)
