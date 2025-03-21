# Paint Controller

The `Paint Controller` is a ROS 2 node designed to provide a user interface for controlling the robot

## Running the Controller
To run the Controller, use the following command:
```bash
python paint_controller.py
```

## Running the Steam Input Node
To run the Steam Input Node, use the following command:
```bash
python steam_input_node.py
```

### Remarks:
You should set the permissions for the Steam Deck device before running the Steam Input Node.

Use the command below to fix device permissions permanently:
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