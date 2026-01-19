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

*(Add entries as discovered)*
