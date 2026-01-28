## Task: Add wheel travel position control mode to joystick control

**Understanding**: Add a new joystick control mode called "Wheel Travel" to OverlayLayer.qml menu. This mode allows the joystick to adjust a travel distance value (±500mm range) without immediately sending commands. Commands are only sent when a trigger button (e.g., A button) is pressed. Speed is fixed at 300 RPM.

**Complexity**: Medium

**KNOWLEDGE.md Check**: 
- "Python-to-QML Signal Timing" — Python signals may fire before Qt state updates
- "ROS2 Tips" — Position control publisher already exists

**File Classification**:
- [x] Python signal handler → identified async boundaries
- [x] ROS2/Hardware → verified controller abstraction (position publisher exists)

**Affected Files**:
1. `python/paint_controller/ui/overlay.py` — Add "Wheel Travel" to control_options list
   - Callers: OverlayLayer.qml (menu display)
   - Callees: None
   
2. `python/paint_controller/handlers/control_processor.py` — Add ControlConfig and handler for "Wheel Travel"
   - Callers: Main joystick processing loop
   - Callees: wheel_controller.command_position()
   
3. `python/paint_controller/handlers/input.py` — Add A button handler to send position command
   - Callers: QML button press signal
   - Callees: control_processor or wheel_controller

**Cross-Layer Impact**: Python↔ROS2 (uses existing wheel.py position publisher)

**Approach**:
1. Add "Wheel Travel" option to control_options in overlay.py (line ~31)
2. Add ControlConfig for "Wheel Travel" in control_processor.py with:
   - Scale: 500mm / 32768 (joystick max) = ~0.0153
   - min_interval: 0.1 (10Hz for display updates)
   - bidirectional: True (±500mm range)
   - Store accumulated travel value, don't send ROS command yet
3. Add handler `_process_wheel_travel()` to accumulate joystick input into travel value
4. Add properties to track left/right wheel travel values separately
5. Add `on_a_pressed()` handler in input.py to:
   - Check if Wheel Travel mode is active
   - Send position command with current travel values
   - Reset travel values to 0 after sending

**Implementation Details**:
- Store travel values: `_left_wheel_travel_mm` and `_right_wheel_travel_mm`
- Joystick updates these values but doesn't publish
- A button press publishes via `wheel_controller.command_position(left_mm, right_mm, 300, True)`
- After publishing, reset travel values to 0

**Risks**: 
- Need to handle both left and right joysticks correctly
- Must reset values after command sent
- Display should show current travel value

**Rollback Plan**: 
Revert changes to overlay.py, control_processor.py, and input.py. System will function as before without new control mode.
