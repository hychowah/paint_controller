# Knowledge Base

Reusable learnings from development. Check here before debugging.

---

## QML / Qt Patterns

### QML Loader Component Timing
When a `Loader`'s `sourceComponent` changes, it immediately destroys the old component and creates the new one. Attempting to show/update popups or render other UI elements during this transition can cause scene graph conflicts and crashes. Solution: Close any existing popups before triggering Loader changes, and defer new popups by 100-150ms using `QTimer.singleShot()` to let the Loader stabilize.

### Screen Property Access
Use `screen.width` not `screen.geometry.width`. Qt Screen objects expose dimensions directly.

### Window Visibility vs Visible
Never use both `visible` and `visibility` on a Window — causes conflicts. Use `visibility` exclusively with `Window.Hidden`, `Window.Windowed`, `Window.FullScreen`.

### Python-to-QML Signal Timing
Python signals may fire before Qt's internal state updates. Use a short Timer (100ms) to let Qt catch up before reading properties like `Qt.application.screens`.

### Qt.application.screens Staleness
Dynamic list but may have stale data immediately after screen changes. Always re-query after a delay, not in direct signal handler.

### Layout Children: Never Use parent.width/height
Inside `RowLayout`/`ColumnLayout`, children must NOT reference `parent.width * 0.30` — causes recursive rearrange errors. Use weight-based sizing: `Layout.fillWidth: true` + `Layout.preferredWidth: 3` (for 30% of total weight 10).

### QQuickView vs QQmlApplicationEngine
`QQmlApplicationEngine` requires `Window` or `ApplicationWindow` as QML root. For `Rectangle`-based components, use `QQuickView` with `SizeRootObjectToView` resize mode instead.

### Qt Button Keyboard Activation in Multi-Window Apps
Qt Buttons respond to Space/Enter keys when focused, even in secondary windows. In multi-monitor or multi-window setups, keyboard events can leak across windows causing unintended button activation. For critical buttons (EXIT, DELETE, etc.), use `focusPolicy: Qt.ClickFocus` (allows mouse clicks but prevents Tab navigation) and `activeFocusOnTab: false`. Add `Keys.onPressed` handler to explicitly block Space/Enter/Return keys with `event.accepted = true` to prevent keyboard triggering while preserving mouse click functionality.

---

## ROS2 Tips

*(Add entries as discovered)*

---

## Python Patterns

### Circular Import via Package `__init__.py`
If `core/__init__.py` re-exports from `application.py`, and `application.py` imports from `handlers/`, then any module in `handlers/` that imports from `core.something` will trigger the full `core/__init__.py` → `application.py` → `handlers/` chain before `handlers/` is ready. **Fix**: Place shared constants/utilities in a lightweight package (e.g. `utils/`) whose `__init__.py` is empty or has no cross-package imports.

### Thread Lock + Signal Pattern
When using `threading.Lock` to protect shared state in PySide6, **always emit signals OUTSIDE the lock**. Copy the needed values inside the lock, release it, then emit. Emitting inside a lock risks deadlock if the slot tries to acquire the same lock.

### `_make_setting_pair()` Factory for PySide6 Properties
To eliminate repetitive `@Property`/getter/setter boilerplate, define a schema dict and a factory function that returns `(Signal, Property)` tuples. Assign them as class attributes in one line per setting: `foo_changed, foo = _make_setting_pair("foo")`. Reduces ~200 lines to ~22 one-liners.

### TypedDict for QML-Compatible Typed Status
When QML accesses Python data via dict-style access (e.g., `model.all_status["field"]`), use `TypedDict` instead of `@dataclass` for type hints. TypedDict gives IDE autocomplete and type checking with zero runtime change — the underlying dict stays a plain dict that QML can consume.

### Test Imports: Namespace-Only Module Pre-Registration
When `package/__init__.py` re-exports heavy dependencies (PySide6, rclpy, hid), tests fail on import. Fix: In `conftest.py`, pre-register the package as a namespace-only module via `types.ModuleType` + `sys.modules` before any test imports. This lets tests import submodules directly without triggering the full `__init__.py` chain.

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
