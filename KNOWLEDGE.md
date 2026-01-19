# Knowledge Base

Reusable learnings from development. Check here before debugging.

---

## QML / Qt Patterns

### Screen Property Access
Use `screen.width` not `screen.geometry.width`. Qt Screen objects expose dimensions directly.

### Window Visibility vs Visible
Never use both `visible` and `visibility` on a Window — causes conflicts. Use `visibility` exclusively with `Window.Hidden`, `Window.Windowed`, `Window.FullScreen`.

### Python-to-QML Signal Timing
Python signals may fire before Qt's internal state updates. Use a short Timer (100ms) to let Qt catch up before reading properties like `Qt.application.screens`.

### Qt.application.screens Staleness
Dynamic list but may have stale data immediately after screen changes. Always re-query after a delay, not in direct signal handler.

---

## ROS2 Tips

*(Add entries as discovered)*

---

## Python Patterns

*(Add entries as discovered)*

---

## Debugging Techniques

*(Add entries as discovered)*

---

## Hardware / Steam Deck

### 7-inch Display Considerations
The Steam Deck has a 7-inch built-in display (1280x800 resolution). When designing UIs for this screen:
- Use larger font sizes than typical desktop apps (minimum 11-12px for body text, 14-16px for important values)
- Increase touch target sizes (minimum 44x44px for buttons)
- Reduce information density - prioritize key data over comprehensive displays
- Test readability at arm's length (~50cm viewing distance)
- Remember: The industrial monitor uses the full 1280x720 viewport on this 7-inch screen

### Multi-Screen Behavior
When an external monitor is connected:
- Main UI moves to external display (index 1)
- Industrial monitor appears fullscreen on built-in 7-inch display (index 0)
- When external disconnected, main UI returns to built-in display
