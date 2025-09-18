# pthread Library Issue

## Problem
The application requires `LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0` to run properly due to conflicts between system pthread library and snap-installed libraries.

## Solution
Use the following alias (already added to ~/.bashrc):

```bash
alias run-paint-controller="LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ros2 run paint_controller_ros2 paint_controller_cpp"
```

## Usage
```bash
run-paint-controller
```

Instead of:
```bash
LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ros2 run paint_controller_ros2 paint_controller_cpp
```
