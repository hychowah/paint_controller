#!/bin/bash
# VTK Installation Script for Paint Controller

echo "========================================="
echo "VTK Installation for Paint Controller"
echo "========================================="
echo ""

# Check if running on Ubuntu/Debian
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi

echo "Detected OS: $OS"
echo ""

# Function to test VTK installation
test_vtk() {
    python3 -c "import vtk; print('VTK Version:', vtk.VTK_VERSION)" 2>/dev/null
    return $?
}

# Check if VTK is already installed
echo "Checking for existing VTK installation..."
if test_vtk; then
    echo "✓ VTK is already installed!"
    echo ""
    read -p "Do you want to reinstall/upgrade? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping installation."
        exit 0
    fi
fi

echo ""
echo "Choose installation method:"
echo "1) System package manager (apt) - Recommended for Ubuntu/Debian"
echo "2) pip - Works on all systems but may require compilation"
echo "3) Cancel"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Installing VTK via apt..."
        if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
            sudo apt update
            sudo apt install -y python3-vtk9
        else
            echo "Warning: This doesn't appear to be Ubuntu/Debian"
            echo "Attempting to install anyway..."
            sudo apt update
            sudo apt install -y python3-vtk9
        fi
        ;;
    2)
        echo ""
        echo "Installing VTK via pip..."
        echo "Note: This may take a while and require build tools"
        pip3 install --user vtk
        ;;
    3)
        echo "Installation cancelled."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Testing VTK Installation"
echo "========================================="
echo ""

if test_vtk; then
    echo "✓ SUCCESS! VTK is now installed and working."
    echo ""
    echo "Next steps:"
    echo "1. Run the test script to verify the full integration:"
    echo "   cd ~/ros2_ws/src/paint_controller_ros2/python"
    echo "   python3 test_vtk.py"
    echo ""
    echo "2. Rebuild your ROS2 workspace:"
    echo "   cd ~/ros2_ws"
    echo "   colcon build --packages-select paint_controller_ros2"
    echo ""
    echo "3. Run your paint controller and press 'A' to toggle LiDAR view"
    echo ""
else
    echo "✗ FAILED! VTK installation was not successful."
    echo ""
    echo "Troubleshooting:"
    echo "1. Check that you have Python 3 development headers:"
    echo "   sudo apt install python3-dev"
    echo ""
    echo "2. Try the alternative installation method"
    echo ""
    echo "3. Check the VTK_INTEGRATION.md file for more details"
    echo ""
    exit 1
fi

exit 0
