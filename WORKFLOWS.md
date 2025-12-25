# Workflow System Guide

The Paint Controller includes a powerful YAML-based workflow system that allows you to automate complex sequences of operations without writing code. This guide explains how to create, configure, and run workflows.

## Table of Contents

- [Overview](#overview)
- [Workflow Structure](#workflow-structure)
- [Action Types](#action-types)
- [Creating Workflows](#creating-workflows)
- [Running Workflows](#running-workflows)
- [Advanced Features](#advanced-features)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The workflow system provides:

- **YAML-based definitions**: Easy to read and write
- **Time-based sequencing**: Actions execute at specified times or sequentially
- **Parallel execution**: Run multiple actions simultaneously
- **Hardware abstraction**: Work with hardware through simple action names
- **Progress tracking**: Monitor workflow execution state
- **Error handling**: Graceful failure recovery

### Components

1. **WorkFlowRunner**: Manages workflow lifecycle (load, start, stop, pause)
2. **WorkFlowExecutor**: Executes individual actions
3. **Scheduler**: Manages time-based action scheduling
4. **Actions**: Predefined operations on hardware
5. **Hardware**: Abstraction layer for hardware controllers

## Workflow Structure

### Basic Structure

```yaml
name: workflow_name
description: Brief description of what this workflow does
actions:
  - id: unique_action_id
    name: action_display_name
    type: action_type
    params:
      param1: value1
      param2: value2
    wait_for_completion: true
    start_time: 0.0
```

### Field Definitions

#### Workflow-Level Fields

- **name** (required): Unique identifier for the workflow
- **description** (optional): Human-readable description
- **actions** (required): List of actions to execute

#### Action-Level Fields

- **id** (required): Unique identifier for this action
- **name** (optional): Display name for the action
- **type** (required): Type of action to execute (see [Action Types](#action-types))
- **params** (required): Dictionary of parameters specific to the action type
- **wait_for_completion** (optional, default: false): Whether to wait for action completion before proceeding
- **start_time** (optional, default: 0.0): Time in seconds from workflow start when this action should begin

## Action Types

### Winch Actions

#### winch_absolute

Move winch to an absolute position.

**Parameters:**
- `length` (float): Target position in millimeters
- `speed` (float): Movement speed in mm/s

**Example:**
```yaml
- id: move_to_top
  type: winch_absolute
  params:
    length: 5000
    speed: 150
  wait_for_completion: true
```

#### winch_relative

Move winch relative to current position.

**Parameters:**
- `length` (float): Distance to move in millimeters (positive = extend, negative = retract)
- `speed` (float): Movement speed in mm/s

**Example:**
```yaml
- id: move_down_1m
  type: winch_relative
  params:
    length: -1000
    speed: 100
  wait_for_completion: true
```

#### winch_stop

Stop all winch movement immediately.

**Parameters:** None

**Example:**
```yaml
- id: stop_winch
  type: winch_stop
  params: {}
```

### Wheel Actions

#### wheel_move

Control wheel movement (base locomotion).

**Parameters:**
- `linear_x` (float): Forward/backward velocity in m/s
- `linear_y` (float): Left/right velocity in m/s (for omnidirectional bases)
- `angular_z` (float): Rotational velocity in rad/s
- `duration` (float): How long to apply the command (seconds)

**Example:**
```yaml
- id: move_forward
  type: wheel_move
  params:
    linear_x: 0.5
    linear_y: 0.0
    angular_z: 0.0
    duration: 3.0
  wait_for_completion: true
```

#### wheel_stop

Stop all wheel movement.

**Parameters:** None

**Example:**
```yaml
- id: stop_wheels
  type: wheel_stop
  params: {}
```

### Timing Actions

#### wait

Pause workflow execution for a specified duration.

**Parameters:**
- `duration` (float): Time to wait in seconds

**Example:**
```yaml
- id: wait_5_seconds
  type: wait
  params:
    duration: 5.0
  wait_for_completion: true
```

### Parallel Actions

#### parallel

Execute multiple actions simultaneously.

**Parameters:**
- `actions` (list): List of action definitions to run in parallel

**Example:**
```yaml
- id: move_both
  type: parallel
  params:
    actions:
      - type: winch_absolute
        params:
          length: 3000
          speed: 150
      - type: wheel_move
        params:
          linear_x: 0.3
          duration: 2.0
  wait_for_completion: true
```

### Teensy Actions

#### teensy_valve_control

Control valve state via Teensy.

**Parameters:**
- `valve_id` (int): Valve identifier
- `state` (bool): true = open, false = close

**Example:**
```yaml
- id: open_valve_1
  type: teensy_valve_control
  params:
    valve_id: 1
    state: true
```

### Camera/Video Actions

#### camera_snapshot

Take a snapshot from a camera.

**Parameters:**
- `camera_id` (int or string): Camera identifier
- `save_path` (string): Where to save the snapshot

**Example:**
```yaml
- id: take_photo
  type: camera_snapshot
  params:
    camera_id: "front_camera"
    save_path: "/tmp/snapshot.jpg"
```

## Creating Workflows

### Step 1: Define Workflow Metadata

Start with a name and description:

```yaml
name: painting_sequence
description: Complete painting operation sequence
```

### Step 2: List Actions

Add actions in the order you want them to execute:

```yaml
actions:
  - id: initialize
    name: Move to start position
    type: winch_absolute
    params:
      length: 1000
      speed: 100
    wait_for_completion: true
```

### Step 3: Add Timing

Use `start_time` for time-based sequencing:

```yaml
actions:
  - id: action1
    type: winch_absolute
    params:
      length: 1000
      speed: 100
    start_time: 0.0
    
  - id: action2
    type: wheel_move
    params:
      linear_x: 0.5
      duration: 2.0
    start_time: 5.0  # Starts 5 seconds after workflow begins
```

### Step 4: Save Workflow

Save the file in `resource/workflows/` with a `.yaml` extension:

```bash
resource/workflows/my_workflow.yaml
```

## Running Workflows

### From GUI

1. Open the Paint Controller application
2. Navigate to the Workflow page
3. Click "Load Workflow"
4. Select your workflow file
5. Click "Start" to begin execution

### Programmatically

```python
from paint_controller.services.workflow import WorkFlowRunner

# Create runner with hardware reference
runner = WorkFlowRunner(hardware_controllers)

# Load workflow
success = runner.load_workflow("path/to/workflow.yaml")

if success:
    # Start execution
    runner.start()
    
    # Monitor progress
    while runner.is_running():
        progress = runner.get_progress()
        print(f"Progress: {progress}%")
        time.sleep(0.5)
    
    # Check completion status
    if runner.is_completed():
        print("Workflow completed successfully")
    elif runner.is_failed():
        print(f"Workflow failed: {runner.get_error()}")
```

### From ROS 2

```bash
# Trigger workflow via ROS service (if implemented)
ros2 service call /workflow/load paint_interfaces/srv/LoadWorkflow "{path: 'workflows/my_workflow.yaml'}"
ros2 service call /workflow/start std_srvs/srv/Trigger
```

## Advanced Features

### Sequential vs. Parallel Execution

#### Sequential (Default)
Actions with `wait_for_completion: true` run one after another:

```yaml
actions:
  - id: step1
    type: winch_absolute
    params:
      length: 1000
      speed: 100
    wait_for_completion: true
    
  - id: step2  # Waits for step1 to complete
    type: wheel_move
    params:
      linear_x: 0.5
      duration: 2.0
    wait_for_completion: true
```

#### Parallel
Actions without `wait_for_completion` or with explicit `parallel` type:

```yaml
actions:
  - id: concurrent_actions
    type: parallel
    params:
      actions:
        - type: winch_absolute
          params:
            length: 2000
            speed: 100
        - type: wheel_move
          params:
            linear_x: 0.3
            duration: 5.0
    wait_for_completion: true
```

### Time-Based Sequencing

Use `start_time` for precise timing:

```yaml
actions:
  - id: t0_action
    type: winch_absolute
    params:
      length: 1000
      speed: 100
    start_time: 0.0
    
  - id: t2_action
    type: wheel_move
    params:
      linear_x: 0.5
      duration: 1.0
    start_time: 2.0
    
  - id: t5_action
    type: winch_stop
    params: {}
    start_time: 5.0
```

All actions with `start_time` run based on workflow start time, not relative to each other.

### Conditional Logic (Future)

*Note: Not yet implemented*

Planned support for conditions:

```yaml
- id: check_and_move
  type: conditional
  condition:
    type: sensor_check
    sensor: lidar
    operator: less_than
    value: 1000
  then:
    - type: winch_stop
      params: {}
  else:
    - type: winch_absolute
      params:
        length: 2000
        speed: 100
```

### Loops (Future)

*Note: Not yet implemented*

Planned support for loops:

```yaml
- id: paint_pattern
  type: loop
  iterations: 5
  actions:
    - type: winch_relative
      params:
        length: -200
        speed: 50
      wait_for_completion: true
    - type: wait
      params:
        duration: 1.0
```

## Examples

### Example 1: Simple Ascent

Move winch to top position:

```yaml
name: ascend
description: Move winch to top position
actions:
  - id: ascend_to_top
    name: Move to 5000mm
    type: winch_absolute
    params:
      length: 5000
      speed: 150
    wait_for_completion: true
```

**File**: `resource/workflows/ascend.yaml`

### Example 2: Descent with Pause

Descend with a pause in the middle:

```yaml
name: descend_with_pause
description: Descend with a pause at mid-point
actions:
  - id: descend_to_mid
    type: winch_absolute
    params:
      length: 2500
      speed: 100
    wait_for_completion: true
    
  - id: pause
    type: wait
    params:
      duration: 3.0
    wait_for_completion: true
    
  - id: descend_to_bottom
    type: winch_absolute
    params:
      length: 0
      speed: 100
    wait_for_completion: true
```

### Example 3: Coordinated Movement

Move winch and wheels simultaneously:

```yaml
name: coordinated_movement
description: Move base while adjusting winch
actions:
  - id: simultaneous_move
    type: parallel
    params:
      actions:
        - type: winch_relative
          params:
            length: -500
            speed: 80
        - type: wheel_move
          params:
            linear_x: 0.4
            linear_y: 0.0
            angular_z: 0.0
            duration: 6.0
    wait_for_completion: true
```

### Example 4: Timed Sequence

Execute actions at specific times:

```yaml
name: timed_painting_sequence
description: Painting with precise timing
actions:
  - id: start_position
    type: winch_absolute
    params:
      length: 1000
      speed: 100
    start_time: 0.0
    wait_for_completion: true
    
  - id: open_valve
    type: teensy_valve_control
    params:
      valve_id: 1
      state: true
    start_time: 2.0
    
  - id: begin_painting
    type: winch_relative
    params:
      length: -2000
      speed: 50
    start_time: 3.0
    
  - id: close_valve
    type: teensy_valve_control
    params:
      valve_id: 1
      state: false
    start_time: 40.0
```

### Example 5: Complete Painting Roll

Full painting operation on a roll:

```yaml
name: descend_a_roll
description: Complete painting sequence for one roll
actions:
  - id: move_to_start
    name: Position at top
    type: winch_absolute
    params:
      length: 5000
      speed: 150
    wait_for_completion: true
    
  - id: prepare
    name: Wait for stabilization
    type: wait
    params:
      duration: 2.0
    wait_for_completion: true
    
  - id: start_paint
    name: Open paint valve
    type: teensy_valve_control
    params:
      valve_id: 1
      state: true
    
  - id: paint_descend
    name: Descend while painting
    type: winch_absolute
    params:
      length: 100
      speed: 50
    wait_for_completion: true
    
  - id: stop_paint
    name: Close paint valve
    type: teensy_valve_control
    params:
      valve_id: 1
      state: false
    
  - id: return_to_top
    name: Return to start position
    type: winch_absolute
    params:
      length: 5000
      speed: 150
    wait_for_completion: true
```

**File**: `resource/workflows/descend_a_roll.yaml`

## Troubleshooting

### Workflow Won't Load

**Problem**: Workflow file doesn't load or shows syntax error.

**Solutions**:
1. Validate YAML syntax with a YAML linter
2. Check that all required fields are present
3. Verify file path is correct
4. Check file permissions

```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('workflow.yaml'))"
```

### Action Not Executing

**Problem**: Action appears to start but doesn't do anything.

**Solutions**:
1. Verify hardware is connected and operational
2. Check ROS 2 topics are active
3. Verify parameter values are within valid ranges
4. Check logs for error messages

### Workflow Hangs

**Problem**: Workflow starts but never completes.

**Solutions**:
1. Check if action with `wait_for_completion: true` is waiting indefinitely
2. Verify hardware provides completion feedback
3. Add timeouts to actions
4. Check for deadlocks in parallel actions

### Timing Issues

**Problem**: Actions don't execute at expected times.

**Solutions**:
1. Verify `start_time` values are correct
2. Check system clock and time synchronization
3. Ensure previous actions complete before timed actions
4. Use sequential actions if precise timing isn't critical

### Parameter Errors

**Problem**: "Invalid parameter" or "Missing parameter" errors.

**Solutions**:
1. Check action documentation for required parameters
2. Verify parameter types (float vs int vs string)
3. Check for typos in parameter names
4. Ensure parameter values are within valid ranges

## Best Practices

### 1. Start Simple
Begin with simple, sequential workflows before adding complexity.

### 2. Use Descriptive IDs
Make action IDs and names clear and descriptive:
```yaml
# Good
- id: move_to_painting_start_position

# Less clear
- id: action1
```

### 3. Add Comments
YAML supports comments - use them:
```yaml
actions:
  # Move to starting position before painting
  - id: initial_position
    type: winch_absolute
    params:
      length: 5000  # 5 meters from bottom
      speed: 150
```

### 4. Test Incrementally
Test each action individually before combining them.

### 5. Use wait_for_completion Wisely
Only wait for completion when necessary to avoid unnecessary delays.

### 6. Version Control
Keep workflows in version control to track changes and revert if needed.

### 7. Document Assumptions
Document any assumptions about hardware state or configuration.

### 8. Safety First
Always include emergency stop procedures and safe starting positions.

## Extending the Workflow System

### Adding New Action Types

1. **Define action function** in `services/workflow/actions.py`:

```python
def execute_my_action(hardware, params):
    """
    Execute custom action.
    
    Args:
        hardware: Hardware controller reference
        params: Dictionary of parameters
            - my_param (type): Description
    """
    value = params.get('my_param')
    hardware.my_controller.do_something(value)
```

2. **Register in executor** in `services/workflow/workflow_executor.py`:

```python
ACTION_HANDLERS = {
    'my_action': execute_my_action,
    # ... other actions
}
```

3. **Document** the new action type in this file

4. **Test** with a simple workflow

### Custom Hardware Integration

To add hardware to workflows, ensure your controller is registered in the hardware reference passed to WorkFlowRunner.

## Conclusion

The workflow system provides a powerful way to automate complex operations without writing code. By combining simple actions with timing and parallelization, you can create sophisticated automated sequences for your robotic painting system.

For more information:
- See [ARCHITECTURE.md](ARCHITECTURE.md) for workflow system architecture
- See [API_REFERENCE.md](API_REFERENCE.md) for WorkFlowRunner API
- Check `resource/workflows/` for more examples
