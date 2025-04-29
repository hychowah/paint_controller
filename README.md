# Paint Controller

The `Paint Controller` is a ROS 2 node designed to provide a user interface for controlling the robot

## Running the Controller
To run the Controller, use the following command:
```bash
python paint_controller.py
```

##  the Steam Input Node
* button detection has been integrated into program, input_node is no longer used.

## Control
Control Menu Button

![menu_button](https://github.com/user-attachments/assets/1cb5f0d9-d7fa-4900-858a-e7bf89f65758)
![Screenshot from 2025-04-30 00-27-14](https://github.com/user-attachments/assets/4a8c3dcd-b281-4cb0-9894-9078ca2e8596)

Joystick Control Selection R4 & L4

![Steam-Deck-OLED-rear webp](https://github.com/user-attachments/assets/6945287c-9d6d-4ba9-81ca-25c86aa887ac)
![Screenshot from 2025-04-30 00-30-23](https://github.com/user-attachments/assets/a5875e38-b665-4c3f-8f43-fbde514861e6)



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
