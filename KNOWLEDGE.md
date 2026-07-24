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

### NEVER Use qmlRegisterSingletonInstance in PySide6
`qmlRegisterSingletonInstance()` corrupts PySide6's QML type system when combined with implicit directory imports (no `qmldir`). Symptoms: `Cannot assign object of type "QQuickRectangle" to list property "data"` — affects ALL Rectangle children globally, not just the registered type. Even a minimal clean QObject triggers it. Known bug family: PYSIDE-2173, PYSIDE-2160, PYSIDE-2310. **Use `engine.rootContext().setContextProperty()` instead.** QML access uses lowercase instance name (`stateStore.X`) instead of type name (`StateStore.X`).

### Qt Button Keyboard Activation in Multi-Window Apps
Qt Buttons respond to Space/Enter keys when focused, even in secondary windows. In multi-monitor or multi-window setups, keyboard events can leak across windows causing unintended button activation. For critical buttons (EXIT, DELETE, etc.), use `focusPolicy: Qt.ClickFocus` (allows mouse clicks but prevents Tab navigation) and `activeFocusOnTab: false`. Add `Keys.onPressed` handler to explicitly block Space/Enter/Return keys with `event.accepted = true` to prevent keyboard triggering while preserving mouse click functionality.

### QT_QPA_PLATFORM Must Be Force-Assigned in Tests
`os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')` is silently overridden when `QT_QPA_PLATFORM=xcb` is already set in the shell (e.g. VS Code integrated terminal). `QApplication([])` then attempts a real display connection and calls `abort()`. **Fix**: Always force-assign `os.environ['QT_QPA_PLATFORM'] = 'offscreen'` at the top of `conftest.py`, before any Qt import.

### pytest qt_core_app Must Be an Alias of qt_app
Creating a second Qt application instance (e.g. a session-scoped `QCoreApplication` alongside a session-scoped `QApplication`) causes a fatal Qt assertion abort. In a pytest session, `QApplication` is a superset of `QCoreApplication`. **Fix**: `def qt_core_app(qt_app): return qt_app` — the alias satisfies any fixture requesting a core app without creating a second instance.

### QObject Cleanup Must Quiesce Timers And Worker Pools
When a Qt-facing controller owns `QTimer` polling and async worker callbacks, cleanup must stop and disconnect timers, prevent callbacks from holding the controller strongly, and wait for worker completion before QObject destruction. Prefer a dedicated `QThreadPool` per controller when teardown order matters, make cleanup idempotent, and call `cleanup()` explicitly in direct tests to avoid late callbacks into deleted Qt objects.

---

## ROS2 Tips

### Node Logger vs Module Logger in ROS2 Controllers
In ROS2 controller classes, `logger = logging.getLogger(__name__)` at module level routes to Python's stdlib logging sink, NOT to ROS2's node logger. During tests, `FakeLogger` only captures calls made to `self._node.get_logger()`. **Always use** `self._node.get_logger().warning(...)` / `.error(...)` etc. in controller instance methods. Module-level logger is acceptable only in pure utility modules with no node reference.

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

### py_compile Guard for Bypassed __init__.py
Conftest namespace stubs (`sys.modules["paint_controller"] = types.ModuleType(...)`) prevent pytest from ever executing `__init__.py`, so `SyntaxError` there is invisible to the test suite. Fix: Add a `py_compile.compile(path, doraise=True)` call in a dedicated test. This checks syntax without importing, bypasses no stubs, and fails immediately on any syntax error.

### `str()` on `(str, Enum)` Returns the Member Name, Not the Value
A class like `class JoystickControl(str, Enum)` still overrides `__str__` to return the member name (`JoystickControl.NONE`), not the string value (`"None"`). This bites any code that does `str(enum_member)` or passes the enum to a QML `str` property. **Fix**: use `.value` explicitly, or store the plain string when the value is what you need.

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

### QML Context Property Over Prop Drilling for Shared Managers
When a reusable QML component needs access to a Python manager (`settingsManager`, `teensyController`), inject it via `engine.rootContext().setContextProperty()` rather than threading it as a property through every intermediate parent. Context properties are globally available to all QML files without any import. Keep special-case logic outside the reusable component rather than adding conditional paths inside it.

### Dynamic Signal Connect/Disconnect for Lazy Frame Processing
For CPU-intensive frame pipelines (e.g. image transforms), add an `enabled` property whose setter calls `signal.connect(worker)` or `signal.disconnect(worker)`. When disabled, zero CPU is spent — no polling or flag-checks needed. Connect lazily on first enable if the upstream signal may not exist at construction time.

### QThread Worker Frame-Skip Flag for Real-Time Pipelines
In a QThread image worker, add a `_processing: bool` flag. If a new frame arrives while `_processing` is True, drop it rather than queuing it. This keeps latency bounded. A queue causes lag that appears as a growing delay rather than clean dropped frames.

### Reuse Existing Camera Stream Signal — Avoid Duplicate ROS Subscriptions
When adding a second consumer of a camera feed, connect to the existing `VideoStreamHandler` stream's `frameReady` signal instead of creating a new `rclpy` subscription for the same topic. Duplicate subscriptions double network traffic and introduce independent timing jitter between consumers.

### Touchscreen-Bound Controls in Dual-Monitor Setup
Interactive controls requiring touch must live on the secondary window that owns the touchscreen (built-in display), not the main UI on the external non-touch monitor. Use `visible: screenCount <= 1` on the main-window instance and add the same component to the secondary window. The secondary window always maps to the built-in screen.

---

## Architecture / Design Patterns

### Strangler Pattern for Dual-Inheritance God Class
A class inheriting from both a ROS `Node` and `QObject` becomes untestable and grows without bound. Split into focused single-inheritance classes (`PaintRosNode`, `StateStore`, `QtBridge`) with an explicit DI coordinator. Use the strangler pattern: create new classes alongside the old, rewire callers incrementally, then remove the old — safe rollback at every step.

### Explicit DI Bundle Over God-Object Attribute Access
Controllers that accept a large facade object and access arbitrary attributes create hidden coupling and prevent isolated testing. Replace with an explicit dataclass (e.g. `ControllerBundle`) that lists exactly which dependencies are required. Constructors become self-documenting and each controller is independently testable.

---

## Python Patterns (extended)

### MagicMock Fails for PySide6 Stubs — Use ModuleType Instead
`MagicMock` as a PySide6 stub fails with `typing.ForwardRef` errors at import time because PySide6 uses forward references internally. Use real (empty) stub modules via `types.ModuleType` + `sys.modules` pre-registration (the namespace-only pattern in `conftest.py`) rather than `MagicMock`.

### Preserving User-Controlled Fields Across ROS Status Callbacks
When a status callback replaces the full status dict on every incoming message, user-toggled fields not driven by hardware are silently overwritten each cycle. Define a constant tuple `_USER_CONTROLLED_FIELDS` and copy those values from the previous dict before replacing it. Prevents state loss for fields the operator manually enables/disables.

### Joystick Accumulation vs Direct Mapping
For position-based joystick controls (e.g. wheel travel distance), always accumulate: `value += joystick * scale * dt`. Direct mapping (`value = joystick * scale`) gives rate-like control where value mirrors stick position and resets to zero when the stick is released. Getting this wrong produces a control mode that behaves correctly during a sweep but resets when the stick centers.

### Dispatch Table for Control Mode Handlers
Replace if/elif chains on control mode names with a `_control_handlers: dict[str, Callable]` mapping mode strings to handler functions. New modes require one dict entry instead of a new elif branch. The dispatch path is independently testable and the set of handled modes is visible at a glance.

---

## Hardware / Controllers

### UDP Range Conversion: Document Scale Factors Inline
Hardware protocols often use different numeric ranges from ROS conventions (e.g. ESP32 feedback 0–10000 = 0.01% steps; command 0–1000 = 0.1% steps; application 0–100%). Add inline comments at every conversion site documenting both ranges and the formula. Silent factor errors produce calibration drift that is hard to trace without the formulas in context.

### QThread for Non-Blocking Hardware I/O
UDP `recvfrom()` and similar blocking socket calls should run in a `QThread` worker, not a `threading.Thread`. QThread integrates with Qt's signal/slot system so signals emitted from the worker arrive in the correct thread context without extra `QMetaObject.invokeMethod` plumbing.

### Conditional Keepalive for Hardware Commands
For hardware requiring a periodic heartbeat, re-send the last command only if idle > N seconds rather than on every timer tick. Track the last-send timestamp and gate re-sends behind an idle check. Avoids unnecessary bus traffic while keeping the connection alive.

### Deadzone Timeout Pattern for Continuous Motor Commands
When publishing continuous motor/speed commands, stop transmitting after the joystick stays in the deadzone for > N seconds (e.g. 1 s). Resume immediately when the stick exits. Prevents command flooding when the operator leaves the stick centered and reduces bus load during idle periods.

### QTimer-Based Hardware Command Ramping
For actuators that cannot handle step changes (e.g. thrust force), implement a QTimer that steps `_current` toward `_target` at a configurable `ramp_rate` (units/second) on each tick. Keep a separate `set_instant()` path for cases that must bypass the ramp. Expose `ramp_rate` as a user-configurable setting.

---

## Workflow / Scheduler

### Separate Original Schedule from Execution State for Loop Restarts
In a workflow executor, store the complete original schedule (`all_scheduled`) separately from the mutable execution-state copy (`_pending_position_triggers`). On loop restart, rebuild position triggers by filtering `all_scheduled` rather than only clearing the mutable list. Clearing without rebuilding silently drops all position-triggered actions after the first loop iteration.

### Implicit Dependency Tracking: Auto-Mark Reference Actions as Must-Complete
When a position-triggered action fires early (before its reference action finishes), the workflow engine must not proceed to completion. Automatically mark reference actions with a `must_complete_before_workflow_end` flag in the scheduler rather than requiring explicit entries in workflow YAML. The executor waits for all such actions before looping or ending. Matches the Kubernetes/Airflow job-dependency pattern.
