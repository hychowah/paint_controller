# Paint Controller

The `Paint Controller` is a ROS 2 node designed to provide a user interface for controlling the robot


### Setting Up Permissions
Before running the `Paint Controller`, configure permissions for the Steam Deck device to ensure proper access. Run the following commands to set permissions permanently:

```bash
sudo tee /etc/udev/rules.d/99-steam-deck.rules <<EOF
# Steam Deck HID
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Cloning and Building paint_interfaces
The `Paint Controller` depends on the `paint_interfaces` package. Follow these steps to clone and build it:

1. Navigate to your ROS 2 workspace's `src` directory:
   ```bash
   cd ~/ros2_workspace/src
   ```

2. Clone the `paint_interfaces` repository:
   ```bash
   git clone https://github.com/hychowah/paint_interfaces.git
   ```

3. Build the `paint_interfaces` package:
   ```bash
   cd ~/ros2_workspace
   colcon build --packages-select paint_interfaces
   ```

4. Source the workspace:
   ```bash
   source ~/ros2_workspace/install/setup.bash

## Running the UI
**Note:** Some text colors in the interface may not display correctly in dark system themes. Use a light theme for the best experience.

To run the `Paint Controller`, execute the following command from your ROS 2 workspace:
```bash
python paint_controller.py
```

Ensure your ROS 2 workspace is sourced before running the command.
   
## Steam Input Node
The Steam Input Node is deprecated. Button detection has been integrated directly into the `Paint Controller`, eliminating the need for a separate input node.

## Control
Control Menu Button

![menu_button](https://github.com/user-attachments/assets/1cb5f0d9-d7fa-4900-858a-e7bf89f65758)
![Screenshot from 2025-04-30 00-27-14](https://github.com/user-attachments/assets/4a8c3dcd-b281-4cb0-9894-9078ca2e8596)

Joystick Control Selection R4 & L4

![Steam-Deck-OLED-rear webp](https://github.com/user-attachments/assets/6945287c-9d6d-4ba9-81ca-25c86aa887ac)
![Screenshot from 2025-04-30 00-30-23](https://github.com/user-attachments/assets/a5875e38-b665-4c3f-8f43-fbde514861e6)

