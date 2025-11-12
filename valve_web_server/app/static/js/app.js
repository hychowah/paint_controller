/**
 * Valve Control Web Application
 * iPhone-friendly web interface for valve control
 */

class ValveController {
    constructor() {
        this.currentValue = 0;
        this.lastValue = 0;
        this.isConnected = false;
        this.isDragging = false;
        this.socket = null;
        this.suppressNextStatusUpdate = false;
        
        this.initElements();
        this.initSocketIO();
        this.attachEventListeners();
        // Hide loading overlay after connection or after 3 seconds timeout
        this.setupLoadingOverlayHide();
    }

    /**
     * Setup loading overlay to hide when connected or after timeout
     */
    setupLoadingOverlayHide() {
        // Hide after 3 seconds regardless
        setTimeout(() => {
            if (this.elements.loadingOverlay) {
                this.elements.loadingOverlay.classList.add('hidden');
            }
        }, 3000);
    }

    /**
     * Initialize DOM elements
     */
    initElements() {
        this.elements = {
            valueDisplay: document.getElementById('valueDisplay'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.querySelector('.status-text'),
            statusDot: document.querySelector('.status-dot'),
            wheel: document.getElementById('valveWheel'),
            slider: document.getElementById('valveSlider'),
            sliderTrack: document.getElementById('sliderTrack'),
            quickBtns: document.querySelectorAll('.quick-btn'),
            statusMessages: document.getElementById('statusMessages'),
            lastUpdateTime: document.getElementById('lastUpdateTime'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            wheelIndicator: document.querySelector('.wheel-indicator'),
            wheelCenter: document.querySelector('.wheel-center')
        };
    }

    /**
     * Initialize Socket.IO connection
     */
    initSocketIO() {
        console.log('Initializing Socket.IO...');
        
        // Wait for socket.io to be available
        if (typeof io === 'undefined') {
            console.error('Socket.IO library not loaded!');
            this.showMessage('Socket.IO library failed to load', 'error');
            setTimeout(() => this.initSocketIO(), 1000);
            return;
        }
        
        console.log('Socket.IO library loaded, connecting...');
        
        // Initialize socket with explicit settings
        this.socket = io({
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: Infinity,
            transports: ['websocket', 'polling']
        });

        console.log('Socket object created:', this.socket);

        this.socket.on('connect', () => {
            console.log('✓✓✓ SOCKET CONNECTED ✓✓✓');
            this.setConnected(true);
            this.showMessage('Connected to server', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('✗ Disconnected from server');
            this.setConnected(false);
            this.showMessage('Disconnected from server', 'error');
        });

        this.socket.on('status_update', (data) => {
            console.log('Status update:', data);
            // Skip updating UI if we just sent a deactivation command
            if (this.suppressNextStatusUpdate && data && data.current_value === 0) {
                console.log('Suppressing status update for deactivation');
                this.suppressNextStatusUpdate = false;
                return;
            }
            if (data && typeof data.current_value !== 'undefined') {
                this.updateValue(data.current_value);
            }
            if (data && data.timestamp) {
                this.updateLastUpdateTime(data.timestamp);
            }
        });

        this.socket.on('command_ack', (data) => {
            console.log('Command acknowledged:', data);
            // Skip updating UI if we just sent a deactivation command
            if (this.suppressNextStatusUpdate && data && data.value === 0) {
                console.log('Suppressing command_ack update for deactivation');
                this.suppressNextStatusUpdate = false;
                return;
            }
            if (data && typeof data.value !== 'undefined') {
                this.updateValue(data.value);
            }
            if (data && data.timestamp) {
                this.updateLastUpdateTime(data.timestamp);
            }
        });

        this.socket.on('error', (data) => {
            console.error('Error from server:', data);
            const msg = data && data.message ? data.message : 'Unknown error';
            this.showMessage(`Error: ${msg}`, 'error');
        });

        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.setConnected(false);
            this.showMessage('Connection error. Retrying...', 'error');
        });

        this.socket.on('connect_timeout', () => {
            console.error('Connection timeout');
            this.setConnected(false);
            this.showMessage('Connection timeout', 'error');
        });
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Wheel control
        this.elements.wheel.addEventListener('touchstart', (e) => this.handleWheelStart(e));
        this.elements.wheel.addEventListener('touchmove', (e) => this.handleWheelMove(e));
        this.elements.wheel.addEventListener('touchend', () => this.handleWheelEnd());
        this.elements.wheel.addEventListener('mousedown', (e) => this.handleWheelStart(e));
        document.addEventListener('mousemove', (e) => this.handleWheelMove(e));
        document.addEventListener('mouseup', () => this.handleWheelEnd());

        // Slider control
        this.elements.slider.addEventListener('input', (e) => this.handleSliderInput(e));

        // Control button - Press to send value, release to send 0
        const controlBtn = document.getElementById('controlBtn');
        if (controlBtn) {
            controlBtn.addEventListener('mousedown', (e) => this.handleButtonDown(e));
            controlBtn.addEventListener('mouseup', (e) => this.handleButtonUp(e));
            controlBtn.addEventListener('touchstart', (e) => this.handleButtonDown(e), { passive: false });
            controlBtn.addEventListener('touchend', (e) => this.handleButtonUp(e), { passive: false });
            controlBtn.addEventListener('touchcancel', (e) => this.handleButtonUp(e), { passive: false });
            this.elements.controlBtn = controlBtn;
        } else {
            console.error('Control button not found');
        }

        // Quick control buttons
        this.elements.quickBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickButton(e));
        });

        // Prevent default touch behaviors
        document.addEventListener('touchmove', (e) => {
            if (e.target === this.elements.wheel) {
                e.preventDefault();
            }
        }, { passive: false });
    }

    /**
     * Handle wheel start
     */
    handleWheelStart(e) {
        if (e.button !== undefined && e.button !== 0) return; // Only left mouse button
        this.isDragging = true;
        this.handleWheelMove(e);
    }

    /**
     * Handle wheel movement
     */
    handleWheelMove(e) {
        if (!this.isDragging) return;

        const touch = e.touches?.[0] || e;
        const rect = this.elements.wheel.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const x = touch.clientX - centerX;
        const y = touch.clientY - centerY;

        let angle = Math.atan2(y, x) * (180 / Math.PI) + 90;
        angle = (angle + 360) % 360;

        // Convert angle to value (0-100) with 1 decimal place
        const value = (angle / 360) * 100;
        const roundedValue = Math.round(value * 10) / 10;
        this.updateValue(roundedValue);
        
        // Update wheel rotation
        this.elements.wheel.style.transform = `rotate(${angle}deg)`;
    }

    /**
     * Handle wheel end
     */
    handleWheelEnd() {
        this.isDragging = false;
    }

    /**
     * Handle slider input
     */
    handleSliderInput(e) {
        const value = parseFloat(e.target.value);
        // Round to 1 decimal place
        const roundedValue = Math.round(value * 10) / 10;
        this.updateValue(roundedValue);
        
        // Update visual slider track
        const percentage = (roundedValue / 100) * 100;
        this.elements.sliderTrack.style.width = `${percentage}%`;
    }

    /**
     * Update displayed value and all controls
     */
    updateValue(value) {
        value = Math.max(0, Math.min(100, parseFloat(value)));
        // Round to 1 decimal place
        value = Math.round(value * 10) / 10;
        this.currentValue = value;

        // Update display with 1 decimal place
        if (this.elements.valueDisplay) {
            this.elements.valueDisplay.textContent = value.toFixed(1);
        }

        // Update slider
        if (this.elements.slider) {
            this.elements.slider.value = value;
        }
        
        if (this.elements.sliderTrack) {
            const percentage = (value / 100) * 100;
            this.elements.sliderTrack.style.width = `${percentage}%`;
        }

        // Update wheel angle
        if (this.elements.wheel) {
            const angle = (value / 100) * 360;
            this.elements.wheel.style.transform = `rotate(${angle}deg)`;
        }
    }

    /**
     * Handle button down (press) - Send current value
     */
    handleButtonDown(e) {
        if (e) {
            e.preventDefault();
        }

        console.log('Button pressed. Connected:', this.isConnected);

        if (!this.isConnected) {
            this.showMessage('Not connected to server', 'error');
            return;
        }

        if (!this.socket) {
            console.error('Socket not initialized');
            this.showMessage('Socket not initialized', 'error');
            return;
        }

        // Add pressed class for visual feedback
        if (this.elements.controlBtn) {
            this.elements.controlBtn.classList.add('pressed');
        }

        // Send current value
        console.log('Sending valve command:', this.currentValue);
        this.socket.emit('valve_command', { value: this.currentValue });
        this.showMessage(`Activated: ${this.currentValue}%`, 'success');
    }

    /**
     * Handle button up (release) - Send 0.0 but keep UI display
     */
    handleButtonUp(e) {
        if (e) {
            e.preventDefault();
        }

        console.log('Button released. Connected:', this.isConnected);

        if (!this.isConnected) {
            this.showMessage('Not connected to server', 'error');
            return;
        }

        if (!this.socket) {
            console.error('Socket not initialized');
            this.showMessage('Socket not initialized', 'error');
            return;
        }

        // Remove pressed class
        if (this.elements.controlBtn) {
            this.elements.controlBtn.classList.remove('pressed');
        }

        // Flag to suppress the status_update response from affecting UI
        this.suppressNextStatusUpdate = true;

        // Send 0.0 value (deactivate) but don't update UI display
        console.log('Sending deactivate command (0.0)');
        this.socket.emit('valve_command', { value: 0.0 });
        this.showMessage('Deactivated (0.0)', 'success');
        // Note: currentValue stays the same, UI display is not reset
    }

    /**
     * Handle quick control buttons
     */
    handleQuickButton(e) {
        const value = e.target.getAttribute('data-value');
        this.updateValue(value);
        
        // Automatically send command
        if (this.isConnected) {
            this.socket.emit('valve_command', { value: parseInt(value) });
            this.showMessage(`Quick set: ${value}%`, 'success');
        }
    }

    /**
     * Set connection status
     */
    setConnected(connected) {
        console.log('setConnected called with:', connected);
        this.isConnected = connected;
        
        if (connected) {
            console.log('Setting UI to connected state');
            this.elements.statusDot.classList.remove('error');
            this.elements.statusDot.classList.add('connected');
            this.elements.statusText.textContent = 'Connected';
            console.log('UI updated: Connected');
        } else {
            console.log('Setting UI to disconnected state');
            this.elements.statusDot.classList.remove('connected');
            this.elements.statusDot.classList.add('error');
            this.elements.statusText.textContent = 'Disconnected';
            console.log('UI updated: Disconnected');
        }
    }

    /**
     * Show status message
     */
    showMessage(text, type = 'info') {
        const message = document.createElement('div');
        message.className = `status-message ${type}`;
        message.textContent = text;

        this.elements.statusMessages.appendChild(message);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            message.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => message.remove(), 300);
        }, 3000);

        // Keep max 3 messages
        while (this.elements.statusMessages.children.length > 3) {
            this.elements.statusMessages.firstChild.remove();
        }
    }

    /**
     * Update last update time
     */
    updateLastUpdateTime(timestamp) {
        if (!timestamp) return;

        const date = new Date(timestamp);
        const time = date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });

        this.elements.lastUpdateTime.textContent = `Last update: ${time}`;
    }

    /**
     * Hide loading overlay
     */
    hideLoadingOverlay() {
        setTimeout(() => {
            this.elements.loadingOverlay.classList.add('hidden');
        }, 500);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Valve Controller...');
    window.valveController = new ValveController();
});

// Prevent default scrolling on iOS
document.addEventListener('touchmove', (e) => {
    if (e.target.closest('.wheel')) {
        e.preventDefault();
    }
}, { passive: false });
