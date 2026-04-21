#!/usr/bin/env python3
"""
System Monitor for getting device status via ACPI commands.
Monitors battery level, remaining time, and CPU temperature.
Runs in background QThread to avoid blocking UI.
"""

import logging
import subprocess
import re
import os
from typing import Optional

from PySide6.QtCore import QObject, Signal, Property, QTimer, QThread, Qt, Slot, QMetaObject, Q_ARG

logger = logging.getLogger(__name__)


class SystemMonitorWorker(QObject):
    """
    Worker that runs in a separate thread to fetch system metrics.
    Emits signals to main thread for UI updates.
    """
    
    # Signals emitted from worker thread to update main thread
    battery_level_updated = Signal(int)
    battery_remaining_time_updated = Signal(str)
    cpu_temperature_updated = Signal(float)
    power_status_updated = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._running = False
        
        # Timer runs in the worker's thread (not main thread)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_system_metrics)
        self.update_timer.setSingleShot(False)
    
    @Slot(int)
    def start_monitoring(self, interval_ms: int = 1000) -> None:
        """
        Start periodic monitoring in worker thread.
        
        Args:
            interval_ms: Update interval in milliseconds (default: 1000ms = 1s)
        """
        self._running = True
        # Do initial update immediately
        self._update_system_metrics()
        # Then start timer for subsequent updates
        self.update_timer.start(interval_ms)
    
    @Slot()
    def stop_monitoring(self) -> None:
        """Stop periodic monitoring"""
        self._running = False
        self.update_timer.stop()
    
    def _update_system_metrics(self) -> None:
        """Fetch and update all system metrics (runs in worker thread)"""
        # Update each metric independently so one failure doesn't block others
        self._update_battery_info()
        self._update_cpu_temperature()
    
    def _update_battery_info(self) -> None:
        """Fetch battery level, remaining time, and power status via acpi"""
        try:
            # Try to get battery info using acpi command
            result = subprocess.run(
                ['acpi', '-b'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout:
                self._parse_battery_info(result.stdout)
            else:
                # Fallback: try alternative method
                self._try_battery_fallback()
        
        except FileNotFoundError:
            # acpi command not installed
            self._try_battery_fallback()
        except subprocess.TimeoutExpired:
            self.error_occurred.emit("Battery info fetch timed out")
        except Exception as e:
            self.error_occurred.emit(f"Error fetching battery info: {e}")
    
    def _parse_battery_info(self, acpi_output: str) -> None:
        """
        Parse acpi battery output.
        Handles formats like:
        - "Battery 0: Charging, 52%, 01:16:02 until charged"
        - "Battery 0: Discharging, 45%, 02:30:45 remaining"
        - "Battery 0: Full, 100%"
        - "Adapter 0: on-line"
        """
        try:
            # Get first battery line only (ignore additional info lines)
            first_line = acpi_output.split('\n')[0].strip()
            
            if not first_line.startswith('Battery'):
                return
            
            # Extract battery percentage
            percent_match = re.search(r'(\d+)%', first_line)
            if percent_match:
                self.battery_level_updated.emit(int(percent_match.group(1)))
            
            # Extract remaining time (HH:MM:SS format)
            time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', first_line)
            if time_match:
                self.battery_remaining_time_updated.emit(time_match.group(0))
            else:
                # No time info available (likely full or error)
                self.battery_remaining_time_updated.emit("N/A")
            
            # Extract power status (Charging, Discharging, Full, etc)
            if 'Charging' in first_line:
                self.power_status_updated.emit("Charging")
            elif 'Discharging' in first_line:
                self.power_status_updated.emit("Discharging")
            elif 'Full' in first_line:
                self.power_status_updated.emit("Full")
            else:
                self.power_status_updated.emit("Unknown")
            
        except Exception as e:
            self.error_occurred.emit(f"Error parsing battery info: {e}")
    
    def _try_battery_fallback(self) -> None:
        """
        Fallback method to get battery info from sysfs if acpi is unavailable.
        Reads from /sys/class/power_supply/BAT*/
        """
        try:
            bat_path = '/sys/class/power_supply/'
            
            if not os.path.exists(bat_path):
                return
            
            # Find battery device
            for device in os.listdir(bat_path):
                if device.startswith('BAT'):
                    device_path = os.path.join(bat_path, device)
                    
                    # Get capacity
                    capacity_file = os.path.join(device_path, 'capacity')
                    if os.path.exists(capacity_file):
                        with open(capacity_file, 'r') as f:
                            self.battery_level_updated.emit(int(f.read().strip()))
                    
                    # Get status
                    status_file = os.path.join(device_path, 'status')
                    if os.path.exists(status_file):
                        with open(status_file, 'r') as f:
                            status = f.read().strip()
                            self.power_status_updated.emit(status if status else "Unknown")
                    
                    # Note: Remaining time is harder to calculate from sysfs
                    # Would need to read current draw and calculate
                    break
        
        except Exception as e:
            self.error_occurred.emit(f"Error in battery fallback: {e}")
    
    def _update_cpu_temperature(self) -> None:
        """Fetch CPU temperature via acpi or thermal zone"""
        try:
            # Try acpi thermal command first
            result = subprocess.run(
                ['acpi', '-t'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout:
                self._parse_cpu_temperature(result.stdout)
            else:
                self._try_temperature_fallback()
        
        except FileNotFoundError:
            # acpi not available, try fallback
            self._try_temperature_fallback()
        except subprocess.TimeoutExpired:
            self.error_occurred.emit("Temperature fetch timed out")
        except Exception as e:
            self.error_occurred.emit(f"Error fetching CPU temperature: {e}")
    
    def _parse_cpu_temperature(self, acpi_output: str) -> None:
        """
        Parse acpi thermal output.
        Expected formats:
        - "Thermal 0: ok, 44.0 degrees C"
        - "Thermal 0: ok, 45 degrees C"
        - Multiple lines (takes first thermal zone)
        """
        try:
            # Get first thermal zone line (ignore trip points and cooling devices)
            for line in acpi_output.split('\n'):
                if line.startswith('Thermal') and 'degrees' in line:
                    # Extract temperature (match float or int numbers)
                    temp_match = re.search(r'(\d+\.?\d*)\s*degrees?\s*C', line)
                    if temp_match:
                        self.cpu_temperature_updated.emit(float(temp_match.group(1)))
                        return
            
            # No thermal data found
            self.error_occurred.emit("No thermal zone found in acpi output")
        
        except Exception as e:
            self.error_occurred.emit(f"Error parsing temperature: {e}")
    
    def _try_temperature_fallback(self) -> None:
        """
        Fallback method to get CPU temperature from thermal zone files.
        Reads from /sys/class/thermal/thermal_zone*/temp
        """
        try:
            thermal_base = '/sys/class/thermal/'
            
            if not os.path.exists(thermal_base):
                return
            
            temps = []
            
            # Collect temperatures from all thermal zones
            for zone in os.listdir(thermal_base):
                if zone.startswith('thermal_zone'):
                    temp_file = os.path.join(thermal_base, zone, 'temp')
                    if os.path.exists(temp_file):
                        try:
                            with open(temp_file, 'r') as f:
                                # Temperature is in millidegrees Celsius
                                temp_millidegrees = int(f.read().strip())
                                temps.append(temp_millidegrees / 1000.0)
                        except (ValueError, IOError):
                            continue
            
            # Use average temperature
            if temps:
                avg_temp = sum(temps) / len(temps)
                self.cpu_temperature_updated.emit(avg_temp)
        
        except Exception as e:
            self.error_occurred.emit(f"Error in temperature fallback: {e}")


class SystemMonitor(QObject):
    """
    Main system monitor that manages a worker thread.
    
    Properties are updated via signals from worker thread.
    Safe for multi-threaded access - all properties are in main thread.
    """
    
    # Signals for property changes
    battery_level_changed = Signal(int)
    battery_remaining_time_changed = Signal(str)
    cpu_temperature_changed = Signal(float)
    power_status_changed = Signal(str)
    start_monitoring_requested = Signal(int)
    stop_monitoring_requested = Signal()
    
    def __init__(self):
        super().__init__()
        
        # State variables (protected by Qt's signal/slot system)
        self._battery_level = 0
        self._battery_remaining_time = "N/A"
        self._cpu_temperature = 0.0
        self._power_status = "Unknown"
        self._worker_ready = False
        self._pending_interval_ms: Optional[int] = None
        
        # Create worker and thread
        self.worker = SystemMonitorWorker()
        self.worker_thread = QThread()
        
        # Move worker to its own thread
        self.worker.moveToThread(self.worker_thread)
        
        # Connect worker signals to our slots (thread-safe signal/slot)
        self.worker.battery_level_updated.connect(self._on_battery_level_updated)
        self.worker.battery_remaining_time_updated.connect(self._on_battery_remaining_time_updated)
        self.worker.cpu_temperature_updated.connect(self._on_cpu_temperature_updated)
        self.worker.power_status_updated.connect(self._on_power_status_updated)
        self.start_monitoring_requested.connect(self.worker.start_monitoring, Qt.QueuedConnection)
        self.stop_monitoring_requested.connect(self.worker.stop_monitoring, Qt.QueuedConnection)
        
        # Start the worker thread
        self.worker_thread.started.connect(self._on_worker_thread_started)
        self.worker_thread.start()

    def _on_worker_thread_started(self) -> None:
        self._worker_ready = True
        if self._pending_interval_ms is not None:
            QMetaObject.invokeMethod(
                self.worker,
                "start_monitoring",
                Qt.QueuedConnection,
                Q_ARG(int, self._pending_interval_ms),
            )
            self._pending_interval_ms = None
    
    # Properties with change signals
    @Property(int, notify=battery_level_changed)
    def battery_level(self) -> int:
        return self._battery_level
    
    @Property(str, notify=battery_remaining_time_changed)
    def battery_remaining_time(self) -> str:
        return self._battery_remaining_time
    
    @Property(float, notify=cpu_temperature_changed)
    def cpu_temperature(self) -> float:
        return self._cpu_temperature
    
    @Property(str, notify=power_status_changed)
    def power_status(self) -> str:
        return self._power_status
    
    # Slots to receive updates from worker thread (run in main thread)
    def _on_battery_level_updated(self, level: int) -> None:
        if self._battery_level != level:
            self._battery_level = level
            self.battery_level_changed.emit(level)
    
    def _on_battery_remaining_time_updated(self, time_str: str) -> None:
        if self._battery_remaining_time != time_str:
            self._battery_remaining_time = time_str
            self.battery_remaining_time_changed.emit(time_str)
    
    def _on_cpu_temperature_updated(self, temp: float) -> None:
        if self._cpu_temperature != temp:
            self._cpu_temperature = temp
            self.cpu_temperature_changed.emit(temp)
    
    def _on_power_status_updated(self, status: str) -> None:
        if self._power_status != status:
            self._power_status = status
            self.power_status_changed.emit(status)
    
    def start_monitoring(self, interval_ms: int = 1000) -> None:
        """
        Start periodic system monitoring.
        
        Args:
            interval_ms: Update interval in milliseconds (default: 1000ms = 1s)
        """
        if not self._worker_ready:
            self._pending_interval_ms = interval_ms
            return

        QMetaObject.invokeMethod(
            self.worker,
            "start_monitoring",
            Qt.QueuedConnection,
            Q_ARG(int, interval_ms),
        )
    
    def stop_monitoring(self) -> None:
        """Stop periodic system monitoring"""
        QMetaObject.invokeMethod(self.worker, "stop_monitoring", Qt.QueuedConnection)
    
    def cleanup(self) -> None:
        """Clean up worker thread and resources"""
        try:
            self.stop_monitoring()
            self.worker_thread.quit()
            # Wait for thread to finish (max 2 seconds)
            if not self.worker_thread.wait(2000):
                logger.warning("Worker thread did not exit cleanly, forcing termination")
                self.worker_thread.terminate()
                self.worker_thread.wait()
            self._worker_ready = False
            self._pending_interval_ms = None
        except Exception as e:
            logger.error("Error cleaning up SystemMonitor: %s", e)
