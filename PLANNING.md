## Task: Add position control publisher to wheel.py

**Understanding**: The user wants to add a publisher in wheel.py to handle position control of the vehicle using the MoveVehiclePos message type. The message has fields: left_travel_mm, right_travel_mm, rpm_limit, and relative. The topic should be 'vehicle/position/cmd'.

**Complexity**: Low

**KNOWLEDGE.md Check**: None applicable (straightforward ROS2 publisher implementation)

**File Classification**:
- [x] ROS2/Hardware → verified controller abstraction

**Current State Analysis**:

After examining the code, I found that **the position control publisher is ALREADY FULLY IMPLEMENTED** in wheel.py:

1. **Line 6**: Imports `MoveVehiclePos` from `paint_interfaces.msg`
2. **Line 74**: Creates publisher `_pos_cmd_pub` for topic `'vehicle/position/cmd'` in `_setup_publishers()` method
3. **Lines 199-219**: Implements `command_position()` method that:
   - Creates a `MoveVehiclePos` message
   - Sets all four fields: `left_travel_mm`, `right_travel_mm`, `rpm_limit`, `relative`
   - Publishes the message to the topic
   - Updates last command time
4. **Lines 385-388**: Exposes `setPosition()` slot to QML that calls `command_position()`

**Affected Files**:
- `python/paint_controller/controllers/wheel.py` — NO CHANGES NEEDED (already implemented)

**Cross-Layer Impact**: None - feature already exists

**Approach**: 
The implementation is already complete and matches exactly what was requested:
- Message type: MoveVehiclePos ✓
- Topic: 'vehicle/position/cmd' ✓
- Message fields: left_travel_mm, right_travel_mm, rpm_limit, relative ✓
- QML-accessible via setPosition() slot ✓

**Conclusion**: 
No code changes are required. The position control publisher is already implemented and ready to use.

**Recommendation**:
1. Verify the implementation matches requirements
2. Confirm with user that this meets their needs
3. If needed, provide documentation or usage examples
