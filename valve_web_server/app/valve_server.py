#!/usr/bin/env python3
"""
Flask-based web server for controlling valve via ROS 2
Provides REST API and WebSocket support for real-time control
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import threading
import json
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global ROS 2 node
ros_node = None
valve_publisher = None
lock = threading.Lock()


class ValveROSBridge(Node):
    """ROS 2 node that publishes valve control commands"""
    
    def __init__(self):
        super().__init__('valve_web_server')
        
        # Create publisher for valve control
        self.valve_pub = self.create_publisher(
            Float32,
            'teensy/valve/turn/cmd',
            1
        )
        
        self.get_logger().info('Valve ROS Bridge initialized')
        self.last_command = 0.0
        self.last_command_time = datetime.now()
    
    def publish_valve_command(self, value):
        """Publish valve command value (0.0-100.0)"""
        # Clamp value between 0.0 and 100.0
        clamped_value = max(0.0, min(100.0, float(value)))
        # Round to 1 decimal place
        clamped_value = round(clamped_value, 1)
        
        msg = Float32()
        msg.data = clamped_value
        
        self.valve_pub.publish(msg)
        self.last_command = clamped_value
        self.last_command_time = datetime.now()
        
        self.get_logger().info(f'Published valve command: {clamped_value}')
        return clamped_value


def init_ros():
    """Initialize ROS 2 node in a separate thread"""
    global ros_node, valve_publisher
    
    rclpy.init()
    ros_node = ValveROSBridge()
    valve_publisher = ros_node.valve_pub
    
    # Spin in a separate thread
    executor_thread = threading.Thread(target=spin_ros, daemon=True)
    executor_thread.start()


def spin_ros():
    """Keep ROS 2 node spinning"""
    while rclpy.ok():
        rclpy.spin_once(ros_node, timeout_sec=0.1)


# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'valve_control_server'
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    engineio_logger=True,
    socketio_logger=True
)


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/valve/command', methods=['POST'])
def set_valve_command():
    """REST API endpoint for setting valve command"""
    try:
        data = request.get_json()
        value = data.get('value')
        
        if value is None:
            return jsonify({'error': 'Missing value parameter'}), 400
        
        with lock:
            if ros_node is None:
                return jsonify({'error': 'ROS 2 node not initialized'}), 503
            
            command_value = ros_node.publish_valve_command(float(value))
        
        return jsonify({
            'success': True,
            'value': command_value,
            'timestamp': datetime.now().isoformat()
        })
    
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid value: {str(e)}'}), 400
    except Exception as e:
        logger.error(f'Error setting valve command: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/valve/status', methods=['GET'])
def get_valve_status():
    """REST API endpoint for getting current valve status"""
    try:
        with lock:
            if ros_node is None:
                return jsonify({'error': 'ROS 2 node not initialized'}), 503
            
            return jsonify({
                'success': True,
                'current_value': ros_node.last_command,
                'last_command_time': ros_node.last_command_time.isoformat()
            })
    except Exception as e:
        logger.error(f'Error getting valve status: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f'Client connected: {request.sid}')
    
    # Send current status to client
    if ros_node:
        emit('status_update', {
            'current_value': ros_node.last_command,
            'timestamp': datetime.now().isoformat()
        })


@socketio.on('valve_command')
def handle_valve_command(data):
    """Handle WebSocket valve command"""
    try:
        value = data.get('value')
        
        if value is None:
            emit('error', {'message': 'Missing value parameter'})
            return
        
        with lock:
            if ros_node is None:
                emit('error', {'message': 'ROS 2 node not initialized'})
                return
            
            command_value = ros_node.publish_valve_command(float(value))
        
        # Send acknowledgement to the sender
        emit('command_ack', {
            'value': command_value,
            'timestamp': datetime.now().isoformat()
        })
        
        # Only broadcast status update if not a deactivation command (0.0)
        if command_value != 0.0:
            socketio.emit('status_update', {
                'current_value': command_value,
                'timestamp': datetime.now().isoformat()
            }, to=None)
    
    except (ValueError, TypeError) as e:
        emit('error', {'message': f'Invalid value: {str(e)}'})
    except Exception as e:
        logger.error(f'Error handling valve command: {str(e)}')
        emit('error', {'message': 'Internal server error'})


@socketio.on_error_default
def default_error_handler(e):
    """Default error handler for WebSocket"""
    logger.error(f'WebSocket error: {str(e)}')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f'Client disconnected: {request.sid}')


def main():
    """Main entry point"""
    logger.info('Starting Valve Web Server...')
    
    # Initialize ROS 2
    init_ros()
    
    # Wait a moment for ROS to initialize
    import time
    time.sleep(1)
    
    # Start Flask server
    logger.info('Starting Flask server on 0.0.0.0:5000')
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
