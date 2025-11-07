# VTK Point Cloud Visualization Integration

This document describes the VTK-based point cloud visualization system integrated into the paint controller application.

## Overview

The VTK (Visualization Toolkit) integration provides high-performance 3D point cloud rendering, capable of handling 10,000+ points in real-time compared to the previous QtQuick3D Repeater approach which was limited to ~2,000 points.

## Architecture

### Components

1. **VTKPointCloudWidget.py** - Main VTK rendering widget
   - Qt widget that embeds VTK rendering window
   - Provides camera controls, color modes, and UI controls
   - Handles point cloud updates from ROS

2. **UILidarController.py** (Modified)
   - Parses ROS PointCloud2 messages
   - Emits two formats:
     - `points_ready`: List of dicts for QML (backward compatible)
     - `points_ready_numpy`: NumPy array for VTK (high performance)

3. **paint_controller.py** (Modified)
   - Initializes VTK widget
   - Connects signals from LidarController to VTK widget
   - Handles toggle between VTK and QML overlays

### Signal Flow

```
ROS PointCloud2 Message
    ↓
UILidarController._pointcloud_callback()
    ↓
Parse to both formats
    ├─→ points_ready (list) → QML Lidar3DView (fallback)
    └─→ points_ready_numpy (np.ndarray) → VTK Widget
            ↓
        VTKPointCloudWidget.update_point_cloud()
            ↓
        VTK Rendering Pipeline
```

## Features

### VTK Widget Features

- **High Performance**: Renders 10,000+ points at 60 FPS
- **Interactive Camera**: 
  - Mouse drag to rotate (trackball style)
  - Mouse wheel to zoom
  - Reset button to restore default view
- **Color Modes**:
  - **Distance**: Rainbow gradient based on distance from origin (like RViz)
  - **Height**: Color based on Y-axis height
  - **Uniform**: Solid green color
  - **Intensity**: (Placeholder for future intensity data)
- **Display Options**:
  - Toggle coordinate axes (X=Red, Y=Green, Z=Blue)
  - Toggle ground grid
- **Real-time Updates**: Automatically updates when new point cloud data arrives

### Comparison: VTK vs QtQuick3D

| Feature | QtQuick3D Repeater | VTK |
|---------|-------------------|-----|
| Max Points (60 FPS) | ~2,000 | 10,000+ |
| Rendering Method | Individual sphere models | Optimized point cloud |
| Memory Usage | High (one Model per point) | Low (single polydata) |
| Setup Complexity | Simple (QML only) | Moderate (Python + VTK) |
| Dependencies | QtQuick3D 6.0 | VTK library |

## Installation

### Install VTK

```bash
# Ubuntu/Debian
sudo apt install python3-vtk9

# Or using pip
pip install vtk

# Or in conda environment
conda install -c conda-forge vtk
```

### Verify Installation

```bash
python3 -c "import vtk; print(f'VTK version: {vtk.VTK_VERSION}')"
```

Expected output: `VTK version: 9.x.x`

## Usage

### Toggle LiDAR View

Press the **A button** on Steam Deck (or configured input device) to toggle the LiDAR 3D view.

### Controls

- **Mouse Left Drag**: Rotate camera (trackball style)
- **Mouse Wheel**: Zoom in/out
- **Color Dropdown**: Change point coloring mode
- **Grid Checkbox**: Show/hide ground grid
- **Axes Checkbox**: Show/hide coordinate axes
- **Reset View**: Return camera to default position
- **Close [A]**: Hide the VTK window

## Configuration

### Maximum Points

Edit `UILidarController.py`, line ~65:

```python
def _parse_pointcloud2(self, msg: PointCloud2, max_points=10000):
```

Increase `max_points` for more detail (requires more GPU/CPU).

### Point Size

Edit `VTKPointCloudWidget.py`, line ~237:

```python
self.point_cloud_actor.GetProperty().SetPointSize(3)
```

Increase for larger points (1-10 recommended).

### Color Gradients

Modify `_generate_colors()` method in `VTKPointCloudWidget.py` to customize color schemes.

## Troubleshooting

### VTK Not Found

**Error**: `ModuleNotFoundError: No module named 'vtk'`

**Solution**: Install VTK:
```bash
pip install vtk
```

### Fallback to QML

If VTK is not installed, the system automatically falls back to the QML-based Lidar3DView with the 2,000 point limitation.

### Black/Blank Window

**Issue**: VTK window opens but shows nothing

**Solutions**:
1. Check that point cloud data is being received (check console logs)
2. Verify ROS topic `/unilidar/cloud` is publishing
3. Try clicking "Reset View" button
4. Check point cloud has valid data (not all NaN/Inf)

### Performance Issues

**Issue**: Lag or stuttering with large point clouds

**Solutions**:
1. Reduce `max_points` in `UILidarController.py`
2. Reduce point size in VTK widget
3. Disable anti-aliasing in VTK environment settings
4. Check system resources (CPU/GPU usage)

## Development

### Adding New Color Modes

1. Add mode to dropdown in `_create_control_panel()`:
   ```python
   self.color_combo.addItems(["Distance", "Height", "Uniform", "MyNewMode"])
   ```

2. Implement in `_generate_colors()`:
   ```python
   elif self.color_mode == "mynewmode":
       # Your color generation logic
       colors[:, 0] = ... # Red channel
       colors[:, 1] = ... # Green channel
       colors[:, 2] = ... # Blue channel
   ```

### Adding Point Intensity

To use intensity data from point cloud:

1. Parse intensity in `UILidarController._parse_pointcloud2()`:
   ```python
   intensity = struct.unpack_from('f', msg.data, offset + intensity_offset)[0]
   ```

2. Pass intensity to VTK widget (modify signal to include intensity)

3. Use in color generation

## Performance Benchmarks

Tested on Steam Deck (AMD APU):

| Points | QtQuick3D FPS | VTK FPS |
|--------|--------------|---------|
| 1,000  | 60 | 60 |
| 2,000  | 60 | 60 |
| 5,000  | 25-30 | 60 |
| 10,000 | 10-15 | 55-60 |
| 20,000 | 5-8 | 40-50 |

## Future Improvements

- [ ] Add point picking/selection
- [ ] Support intensity coloring from PointCloud2
- [ ] Add measurement tools (distance, angle)
- [ ] Export point cloud to file (PCD, PLY)
- [ ] Add multiple point cloud layers
- [ ] Implement frustum culling for very large clouds
- [ ] Add point cloud filtering (statistical outlier removal)
- [ ] Integrate with trajectory planning visualization

## References

- [VTK Documentation](https://vtk.org/documentation/)
- [VTK Examples](https://kitware.github.io/vtk-examples/site/)
- [Qt VTK Integration](https://vtk.org/Wiki/VTK/Tutorials/QtSetup)
- [ROS PointCloud2](http://docs.ros.org/en/api/sensor_msgs/html/msg/PointCloud2.html)
