# Valve Web Server

A modern, iPhone-friendly web interface for controlling valve position via ROS 2. This web server provides real-time control with an intuitive touch-optimized interface.

## Features

- **Modern iPhone UI**: Responsive design optimized for mobile devices
- **Scroll Wheel Control**: Intuitive circular wheel interface for valve position (0-100%)
- **Alternative Slider**: Touch-friendly slider control as an alternative
- **Real-time Feedback**: WebSocket-based communication for instant response
- **Quick Controls**: Preset buttons for common valve positions (25%, 50%, 75%, 100%)
- **Connection Status**: Real-time connection indicator
- **Release Button**: Quickly set valve to 0% (closed)
- **REST API**: Alternative JSON API for programmatic access

## Project Structure

```
valve_web_server/
├── app/
│   ├── valve_server.py          # Main Flask application with ROS 2 bridge
│   ├── templates/
│   │   └── index.html           # HTML template
│   └── static/
│       ├── css/
│       │   └── style.css        # Modern styling
│       └── js/
│           └── app.js           # Client-side logic
├── requirements.txt              # Python dependencies
├── run_server.sh                # Startup script
└── README.md                     # This file
```

## Prerequisites

- ROS 2 (Humble or newer)
- Python 3.8+
- pip (Python package manager)

## Installation

### 1. Clone or Download

The valve web server is already in your project at:
```bash
~/ros2_ws/src/paint_controller_ros2/valve_web_server/
```

### 2. Install Dependencies

```bash
cd ~/ros2_ws/src/paint_controller_ros2/valve_web_server/
pip install -r requirements.txt
```

Or use the automated startup script (which handles this):
```bash
chmod +x run_server.sh
```

## Usage

### Option 1: Using the Startup Script (Recommended)

```bash
cd ~/ros2_ws/src/paint_controller_ros2/valve_web_server/
chmod +x run_server.sh
./run_server.sh
```

The script will:
1. Set up the Python virtual environment
2. Install dependencies
3. Start the web server on `0.0.0.0:5000`

### Option 2: Manual Startup

```bash
# Source ROS 2 setup
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

# Navigate to the server directory
cd ~/ros2_ws/src/paint_controller_ros2/valve_web_server/

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the server
python3 app/valve_server.py
```

## Accessing from iPhone

1. **Get your computer's IP address**:
   ```bash
   hostname -I
   ```
   Or check your network settings.

2. **On your iPhone**:
   - Open Safari (or any web browser)
   - Navigate to: `http://<your-computer-ip>:5000`
   - Example: `http://192.168.1.100:5000`

3. **Add to Home Screen** (Optional):
   - Tap the Share button
   - Select "Add to Home Screen"
   - This creates a native-looking app icon

## Interface Controls

### Scroll Wheel
- **Drag around the circular wheel** to adjust valve position
- **Visual feedback** shows current position
- Smooth 0-100% range

### Slider
- **Swipe left/right** to adjust valve position
- Alternative to wheel control
- Can use both interchangeably

### Buttons

| Button | Action |
|--------|--------|
| **SEND** | Send the current selected value (0-100%) to the valve |
| **RELEASE** | Immediately set valve to 0% (closed position) |
| **Quick Buttons** | Preset values: 25%, 50%, 75%, 100% |

### Status Indicators
- **Connected** (green dot): Successfully connected to server
- **Disconnected** (red dot): Connection lost, trying to reconnect
- **Last Update Time**: Timestamp of the last command sent

## API Reference

### WebSocket Events

The server uses Socket.IO for real-time communication.

#### Client → Server

```javascript
// Send valve command
socket.emit('valve_command', {
    value: 75.5  // Float between 0.0 and 100.0
});
```

#### Server → Client

```javascript
// Status update (broadcast to all clients)
socket.on('status_update', {
    current_value: 75.5,
    timestamp: "2024-01-15T10:30:45.123456"
});

// Command acknowledgment
socket.on('command_ack', {
    value: 75.5,
    timestamp: "2024-01-15T10:30:45.123456"
});

// Error message
socket.on('error', {
    message: "Error description"
});
```

### REST API Endpoints

#### POST /api/valve/command
Send a valve control command.

```bash
curl -X POST http://localhost:5000/api/valve/command \
  -H "Content-Type: application/json" \
  -d '{"value": 75.5}'
```

Response:
```json
{
  "success": true,
  "value": 75.5,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### GET /api/valve/status
Get current valve status.

```bash
curl http://localhost:5000/api/valve/status
```

Response:
```json
{
  "success": true,
  "current_value": 75.5,
  "last_command_time": "2024-01-15T10:30:45.123456"
}
```

## ROS 2 Integration

The server publishes to the ROS 2 topic:
- **Topic**: `teensy/valve/turn/cmd`
- **Message Type**: `std_msgs/Float32`
- **Range**: 0.0 - 100.0

All valve commands are automatically published to this topic with clamping to the valid range.

## Troubleshooting

### Connection Issues

**Problem**: iPhone can't connect to server
- Check both devices are on the same network
- Verify firewall isn't blocking port 5000
- Try accessing from computer browser first: `http://localhost:5000`
- Use IP address, not hostname

**Problem**: "Disconnected from server" in UI
- Check server is still running
- Check network connection
- Try refreshing the page
- Restart the server

### ROS 2 Not Initialized

**Error**: "ROS 2 node not initialized"
- Ensure ROS 2 is sourced: `source /opt/ros/humble/setup.bash`
- Ensure workspace is sourced: `source ~/ros2_ws/install/setup.bash`
- Check `ros2 node list` shows `valve_web_server` node

### Python Dependencies

**Error**: Module not found
```bash
pip install -r requirements.txt --upgrade
```

## Development

### Modifying the UI

Edit `/app/templates/index.html` and `/app/static/css/style.css`

Changes are immediately visible in the browser (after refresh).

### Modifying the Backend

Edit `/app/valve_server.py`

Restart the server for changes to take effect:
```bash
# Stop current server (Ctrl+C)
# Restart: ./run_server.sh or python3 app/valve_server.py
```

### Adding Custom Endpoints

Edit `valve_server.py` to add new Flask routes:
```python
@app.route('/api/custom', methods=['GET'])
def custom_endpoint():
    return jsonify({'result': 'your data'})
```

## Performance Notes

- **Wheel Control**: Uses optimized touch event handling for smooth 60fps interaction
- **WebSocket**: Low-latency real-time communication (~10-50ms)
- **Mobile Optimized**: Minimal CSS animations, touch-friendly hit targets
- **Memory**: ~50-100MB RAM usage

## Security Considerations

⚠️ **Important**: This server is designed for local network use only.

- No authentication/authorization implemented
- No HTTPS support (use only on trusted networks)
- All connected clients can control the valve
- For production use, consider:
  - Adding authentication (Flask-Login)
  - Implementing HTTPS (gunicorn + SSL)
  - Rate limiting commands
  - Logging all commands

## License

Same as parent project

## Support

For issues or questions:
1. Check the ROS 2 logs: `journalctl -u ros2`
2. Check server terminal output for errors
3. Open browser console (F12) for client-side errors

## Future Enhancements

- [ ] Command history/logging
- [ ] Scheduling/automation
- [ ] Multiple valve support
- [ ] User authentication
- [ ] Data persistence
- [ ] Mobile app version
- [ ] Voice control
- [ ] Gesture controls
