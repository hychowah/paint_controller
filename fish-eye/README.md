# Fisheye Unwrapper - Optimized Version

Real-time fisheye lens correction with optimized Qt interface.

## Performance Optimization Summary

- **Original Issue**: QThread implementation caused lag (~10-15 FPS)
- **Root Cause**: Signal/slot overhead, NOT transformation algorithm
- **Solution**: Direct timer-based processing → 30+ FPS
- **Proof**: Transformation only ~9ms per frame (110 FPS theoretical)

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Integration Guide

See `INTEGRATION_GUIDE.py` for complete integration instructions.

### Minimal Usage:

```python
from core.processor import FisheyeProcessor
processor = FisheyeProcessor(1920, 1080)
processor.update_parameters(center_x=960, center_y=540, radius=599)
unwrapped = processor.process_frame(frame)
```

### Qt Integration (Timer-based - Recommended):

```python
from PyQt5.QtCore import QTimer
timer = QTimer()
timer.timeout.connect(process_and_display_frame)
timer.start(0)
```

## Key Files for Integration

- `core/processor.py` - Main transformation engine
- `core/preset_manager.py` - Preset management
- `utils/config.py` - Configuration constants
- `presets/*.json` - Parameter presets

## Features

✅ Real-time unwrapping (30+ FPS)  
✅ Interactive parameter adjustment  
✅ Auto circle detection  
✅ Preset save/load  
✅ Video recording  

## Why Not QThread?

QThread adds overhead for high-frequency operations. Direct timer approach is faster and simpler for video processing.

---

**Conclusion**: The transformation algorithm is fast. Use timer-based processing for optimal Qt performance.
