"""
Controls panel with sliders for adjusting fisheye unwrapping parameters.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QDoubleSpinBox, QPushButton, QGroupBox,
                             QComboBox, QCheckBox, QSpinBox, QFileDialog,
                             QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from utils.config import SLIDER_RANGES
from core.preset_manager import PresetManager


class ControlsPanel(QWidget):
    """Panel containing all parameter adjustment controls."""
    
    # Signals for parameter changes
    parameters_changed = pyqtSignal(dict)  # Emits parameter dictionary
    auto_detect_requested = pyqtSignal()
    snapshot_requested = pyqtSignal()
    recording_toggled = pyqtSignal(bool)  # True = start, False = stop
    show_circle_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.preset_manager = PresetManager()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.emit_parameters)
        
        self.pending_parameters = {}
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Fisheye Circle Parameters Group
        circle_group = QGroupBox("Fisheye Circle")
        circle_layout = QVBoxLayout()
        
        # Center X
        self.center_x_slider, self.center_x_spin = self.create_slider_spinbox(
            "Center X:", 
            SLIDER_RANGES['center_x'], 
            is_float=False
        )
        circle_layout.addLayout(self.create_param_layout("Center X:", self.center_x_slider, self.center_x_spin))
        
        # Center Y
        self.center_y_slider, self.center_y_spin = self.create_slider_spinbox(
            "Center Y:", 
            SLIDER_RANGES['center_y'], 
            is_float=False
        )
        circle_layout.addLayout(self.create_param_layout("Center Y:", self.center_y_slider, self.center_y_spin))
        
        # Radius
        self.radius_slider, self.radius_spin = self.create_slider_spinbox(
            "Radius:", 
            SLIDER_RANGES['radius'], 
            is_float=False
        )
        circle_layout.addLayout(self.create_param_layout("Radius:", self.radius_slider, self.radius_spin))
        
        # Auto detect and show circle buttons
        circle_btn_layout = QHBoxLayout()
        self.auto_detect_btn = QPushButton("Auto Detect Circle")
        self.auto_detect_btn.clicked.connect(self.auto_detect_requested.emit)
        circle_btn_layout.addWidget(self.auto_detect_btn)
        
        self.show_circle_check = QCheckBox("Show Circle Overlay")
        self.show_circle_check.setChecked(True)
        self.show_circle_check.toggled.connect(self.show_circle_toggled.emit)
        circle_btn_layout.addWidget(self.show_circle_check)
        circle_layout.addLayout(circle_btn_layout)
        
        circle_group.setLayout(circle_layout)
        layout.addWidget(circle_group)
        
        # FOV Parameters Group
        fov_group = QGroupBox("Field of View")
        fov_layout = QVBoxLayout()
        
        # FOV Horizontal
        self.fov_h_slider, self.fov_h_spin = self.create_slider_spinbox(
            "Horizontal:", 
            SLIDER_RANGES['fov_horizontal'], 
            is_float=True
        )
        fov_layout.addLayout(self.create_param_layout("Horizontal:", self.fov_h_slider, self.fov_h_spin))
        
        # FOV Vertical
        self.fov_v_slider, self.fov_v_spin = self.create_slider_spinbox(
            "Vertical:", 
            SLIDER_RANGES['fov_vertical'], 
            is_float=True
        )
        fov_layout.addLayout(self.create_param_layout("Vertical:", self.fov_v_slider, self.fov_v_spin))
        
        fov_group.setLayout(fov_layout)
        layout.addWidget(fov_group)
        
        # Distortion Parameters Group
        distortion_group = QGroupBox("Distortion Coefficients")
        distortion_layout = QVBoxLayout()
        
        # K1
        self.k1_slider, self.k1_spin = self.create_slider_spinbox(
            "K1:", 
            SLIDER_RANGES['distortion_k1'], 
            is_float=True,
            decimals=3
        )
        distortion_layout.addLayout(self.create_param_layout("K1:", self.k1_slider, self.k1_spin))
        
        # K2
        self.k2_slider, self.k2_spin = self.create_slider_spinbox(
            "K2:", 
            SLIDER_RANGES['distortion_k2'], 
            is_float=True,
            decimals=3
        )
        distortion_layout.addLayout(self.create_param_layout("K2:", self.k2_slider, self.k2_spin))
        
        distortion_group.setLayout(distortion_layout)
        layout.addWidget(distortion_group)
        
        # View Parameters Group
        view_group = QGroupBox("View Parameters")
        view_layout = QVBoxLayout()
        
        # Zoom
        self.zoom_slider, self.zoom_spin = self.create_slider_spinbox(
            "Zoom:", 
            SLIDER_RANGES['zoom'], 
            is_float=True
        )
        view_layout.addLayout(self.create_param_layout("Zoom:", self.zoom_slider, self.zoom_spin))
        
        # Rotation
        self.rotation_slider, self.rotation_spin = self.create_slider_spinbox(
            "Rotation:", 
            SLIDER_RANGES['rotation'], 
            is_float=True
        )
        view_layout.addLayout(self.create_param_layout("Rotation:", self.rotation_slider, self.rotation_spin))
        
        # Focal Length
        self.focal_slider, self.focal_spin = self.create_slider_spinbox(
            "Focal Length:", 
            SLIDER_RANGES['focal_length'], 
            is_float=True
        )
        view_layout.addLayout(self.create_param_layout("Focal Length:", self.focal_slider, self.focal_spin))
        
        view_group.setLayout(view_layout)
        layout.addWidget(view_group)
        
        # Presets Group
        presets_group = QGroupBox("Presets")
        presets_layout = QVBoxLayout()
        
        preset_select_layout = QHBoxLayout()
        preset_select_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.refresh_presets()
        preset_select_layout.addWidget(self.preset_combo)
        
        self.load_preset_btn = QPushButton("Load")
        self.load_preset_btn.clicked.connect(self.load_preset)
        preset_select_layout.addWidget(self.load_preset_btn)
        presets_layout.addLayout(preset_select_layout)
        
        preset_btn_layout = QHBoxLayout()
        self.save_preset_btn = QPushButton("Save As...")
        self.save_preset_btn.clicked.connect(self.save_preset)
        preset_btn_layout.addWidget(self.save_preset_btn)
        
        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.clicked.connect(self.delete_preset)
        preset_btn_layout.addWidget(self.delete_preset_btn)
        presets_layout.addLayout(preset_btn_layout)
        
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        # Recording Controls Group
        recording_group = QGroupBox("Recording")
        recording_layout = QVBoxLayout()
        
        recording_btn_layout = QHBoxLayout()
        
        self.snapshot_btn = QPushButton("📷 Take Snapshot")
        self.snapshot_btn.clicked.connect(self.snapshot_requested.emit)
        recording_btn_layout.addWidget(self.snapshot_btn)
        
        self.record_btn = QPushButton("⏺ Start Recording")
        self.record_btn.setCheckable(True)
        self.record_btn.toggled.connect(self.on_record_toggled)
        recording_btn_layout.addWidget(self.record_btn)
        
        recording_layout.addLayout(recording_btn_layout)
        
        self.record_label = QLabel("Ready")
        self.record_label.setAlignment(Qt.AlignCenter)
        recording_layout.addWidget(self.record_label)
        
        recording_group.setLayout(recording_layout)
        layout.addWidget(recording_group)
        
        # Add stretch at bottom
        layout.addStretch()
        
    def create_slider_spinbox(self, label, range_tuple, is_float=False, decimals=2):
        """Create linked slider and spinbox for a parameter."""
        min_val, max_val, default_val = range_tuple
        
        slider = QSlider(Qt.Horizontal)
        
        if is_float:
            # For float values, scale slider by 10^decimals
            scale = 10 ** decimals
            slider.setMinimum(int(min_val * scale))
            slider.setMaximum(int(max_val * scale))
            slider.setValue(int(default_val * scale))
            
            spinbox = QDoubleSpinBox()
            spinbox.setDecimals(decimals)
            spinbox.setMinimum(min_val)
            spinbox.setMaximum(max_val)
            spinbox.setValue(default_val)
            spinbox.setSingleStep(1.0 / scale)
            
            # Connect signals
            slider.valueChanged.connect(lambda v: spinbox.setValue(v / scale))
            spinbox.valueChanged.connect(lambda v: slider.setValue(int(v * scale)))
            spinbox.valueChanged.connect(lambda: self.on_parameter_changed())
        else:
            slider.setMinimum(int(min_val))
            slider.setMaximum(int(max_val))
            slider.setValue(int(default_val))
            
            spinbox = QSpinBox()
            spinbox.setMinimum(int(min_val))
            spinbox.setMaximum(int(max_val))
            spinbox.setValue(int(default_val))
            
            # Connect signals
            slider.valueChanged.connect(spinbox.setValue)
            spinbox.valueChanged.connect(slider.setValue)
            spinbox.valueChanged.connect(self.on_parameter_changed)
            
        return slider, spinbox
        
    def create_param_layout(self, label_text, slider, spinbox):
        """Create layout for parameter label, slider, and spinbox."""
        layout = QHBoxLayout()
        
        label = QLabel(label_text)
        label.setMinimumWidth(100)
        layout.addWidget(label)
        
        layout.addWidget(slider, stretch=2)
        layout.addWidget(spinbox)
        
        return layout
        
    def on_parameter_changed(self):
        """Handle parameter change with debouncing."""
        # Start/restart debounce timer
        self.debounce_timer.start(200)  # 200ms debounce
        
    def emit_parameters(self):
        """Emit current parameters after debounce."""
        params = self.get_parameters()
        self.parameters_changed.emit(params)
        
    def get_parameters(self):
        """Get all current parameter values."""
        return {
            'center_x': self.center_x_spin.value(),
            'center_y': self.center_y_spin.value(),
            'radius': self.radius_spin.value(),
            'fov_h': self.fov_h_spin.value(),
            'fov_v': self.fov_v_spin.value(),
            'k1': self.k1_spin.value(),
            'k2': self.k2_spin.value(),
            'zoom': self.zoom_spin.value(),
            'rotation': self.rotation_spin.value(),
            'focal_length': self.focal_spin.value()
        }
        
    def set_parameters(self, params):
        """Set parameter values (without triggering signals)."""
        # Block signals while updating
        widgets = [
            self.center_x_spin, self.center_y_spin, self.radius_spin,
            self.fov_h_spin, self.fov_v_spin, self.k1_spin, self.k2_spin,
            self.zoom_spin, self.rotation_spin, self.focal_spin
        ]
        
        for widget in widgets:
            widget.blockSignals(True)
            
        if 'center_x' in params:
            self.center_x_spin.setValue(params['center_x'])
        if 'center_y' in params:
            self.center_y_spin.setValue(params['center_y'])
        if 'radius' in params:
            self.radius_spin.setValue(params['radius'])
        if 'fov_h' in params or 'fov_horizontal' in params:
            self.fov_h_spin.setValue(params.get('fov_h', params.get('fov_horizontal')))
        if 'fov_v' in params or 'fov_vertical' in params:
            self.fov_v_spin.setValue(params.get('fov_v', params.get('fov_vertical')))
        if 'k1' in params:
            self.k1_spin.setValue(params['k1'])
        if 'k2' in params:
            self.k2_spin.setValue(params['k2'])
        if 'zoom' in params:
            self.zoom_spin.setValue(params['zoom'])
        if 'rotation' in params:
            self.rotation_spin.setValue(params['rotation'])
        if 'focal_length' in params:
            self.focal_spin.setValue(params['focal_length'])
            
        for widget in widgets:
            widget.blockSignals(False)
            
        # Emit once after all updates
        self.emit_parameters()
        
    def refresh_presets(self):
        """Refresh preset list."""
        self.preset_combo.clear()
        presets = self.preset_manager.list_presets()
        self.preset_combo.addItems(presets)
        
    def load_preset(self):
        """Load selected preset."""
        preset_name = self.preset_combo.currentText()
        if not preset_name:
            return
            
        params = self.preset_manager.load_preset(preset_name)
        if params:
            self.set_parameters(params)
            QMessageBox.information(self, "Preset Loaded", 
                                  f"Loaded preset: {preset_name}")
                                  
    def save_preset(self):
        """Save current parameters as preset."""
        name, ok = QInputDialog.getText(self, "Save Preset", 
                                        "Enter preset name:")
        if ok and name:
            params = self.get_parameters()
            params['name'] = name
            
            if self.preset_manager.save_preset(name, params):
                self.refresh_presets()
                # Select the newly saved preset
                index = self.preset_combo.findText(name)
                if index >= 0:
                    self.preset_combo.setCurrentIndex(index)
                QMessageBox.information(self, "Preset Saved", 
                                      f"Saved preset: {name}")
                                      
    def delete_preset(self):
        """Delete selected preset."""
        preset_name = self.preset_combo.currentText()
        if not preset_name:
            return
            
        reply = QMessageBox.question(self, "Delete Preset",
                                    f"Delete preset '{preset_name}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.preset_manager.delete_preset(preset_name):
                self.refresh_presets()
                QMessageBox.information(self, "Preset Deleted", 
                                      f"Deleted preset: {preset_name}")
                                      
    def on_record_toggled(self, checked):
        """Handle record button toggle."""
        if checked:
            self.record_btn.setText("⏹ Stop Recording")
            self.record_label.setText("Recording...")
            self.record_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.record_btn.setText("⏺ Start Recording")
            self.record_label.setText("Ready")
            self.record_label.setStyleSheet("")
            
        self.recording_toggled.emit(checked)
        
    def update_recording_info(self, frame_count, duration):
        """Update recording information display."""
        self.record_label.setText(f"Recording... {frame_count} frames ({duration:.1f}s)")
