"""
Preset manager for saving and loading fisheye unwrapping parameters.
"""
import json
import os
from pathlib import Path
from utils.config import DEFAULT_PRESETS


class PresetManager:
    """Manage saving and loading of fisheye unwrapping presets."""
    
    def __init__(self, preset_dir="presets"):
        self.preset_dir = Path(preset_dir)
        self.preset_dir.mkdir(exist_ok=True)
        
        # Initialize default presets if they don't exist
        self.create_default_presets()
        
    def create_default_presets(self):
        """Create default preset files if they don't exist."""
        for preset_id, preset_data in DEFAULT_PRESETS.items():
            preset_file = self.preset_dir / f"{preset_id}.json"
            if not preset_file.exists():
                self.save_preset(preset_id, preset_data)
                
    def save_preset(self, name, parameters):
        """
        Save preset parameters to JSON file.
        
        Args:
            name: Preset name (filename without extension)
            parameters: Dictionary of parameters to save
        """
        preset_file = self.preset_dir / f"{name}.json"
        
        try:
            with open(preset_file, 'w') as f:
                json.dump(parameters, f, indent=4)
            print(f"Saved preset: {name}")
            return True
        except Exception as e:
            print(f"Error saving preset {name}: {e}")
            return False
            
    def load_preset(self, name):
        """
        Load preset parameters from JSON file.
        
        Args:
            name: Preset name (filename without extension)
            
        Returns:
            Dictionary of parameters or None if not found
        """
        preset_file = self.preset_dir / f"{name}.json"
        
        if not preset_file.exists():
            print(f"Preset not found: {name}")
            return None
            
        try:
            with open(preset_file, 'r') as f:
                parameters = json.load(f)
            print(f"Loaded preset: {name}")
            return parameters
        except Exception as e:
            print(f"Error loading preset {name}: {e}")
            return None
            
    def list_presets(self):
        """
        Get list of available preset names.
        
        Returns:
            List of preset names (without .json extension)
        """
        presets = []
        
        for preset_file in self.preset_dir.glob("*.json"):
            presets.append(preset_file.stem)
            
        return sorted(presets)
        
    def delete_preset(self, name):
        """
        Delete a preset file.
        
        Args:
            name: Preset name (filename without extension)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        preset_file = self.preset_dir / f"{name}.json"
        
        if not preset_file.exists():
            print(f"Preset not found: {name}")
            return False
            
        try:
            preset_file.unlink()
            print(f"Deleted preset: {name}")
            return True
        except Exception as e:
            print(f"Error deleting preset {name}: {e}")
            return False
            
    def get_preset_info(self, name):
        """
        Get information about a preset without fully loading it.
        
        Args:
            name: Preset name
            
        Returns:
            Dictionary with 'name' and other metadata if available
        """
        parameters = self.load_preset(name)
        
        if parameters:
            return {
                'id': name,
                'name': parameters.get('name', name),
                'fov_h': parameters.get('fov_horizontal', 0),
                'fov_v': parameters.get('fov_vertical', 0)
            }
            
        return None
        
    def export_preset(self, name, export_path):
        """
        Export preset to a specific file path.
        
        Args:
            name: Preset name
            export_path: Full path where to export the preset
            
        Returns:
            True if exported successfully
        """
        parameters = self.load_preset(name)
        
        if parameters is None:
            return False
            
        try:
            with open(export_path, 'w') as f:
                json.dump(parameters, f, indent=4)
            print(f"Exported preset {name} to {export_path}")
            return True
        except Exception as e:
            print(f"Error exporting preset: {e}")
            return False
            
    def import_preset(self, import_path, new_name=None):
        """
        Import preset from a file.
        
        Args:
            import_path: Path to preset JSON file
            new_name: Optional new name for the preset
            
        Returns:
            True if imported successfully
        """
        try:
            with open(import_path, 'r') as f:
                parameters = json.load(f)
                
            if new_name is None:
                new_name = Path(import_path).stem
                
            return self.save_preset(new_name, parameters)
        except Exception as e:
            print(f"Error importing preset: {e}")
            return False
