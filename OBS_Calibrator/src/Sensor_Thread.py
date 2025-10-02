import os
import random
import statistics
import time
from PySide6.QtCore import Signal, QThread, Slot

# Set the BLINKA_MCP2221 environment variable before any hardware imports
os.environ["BLINKA_MCP2221"] = "1"

DELAY_TIME = 999

# Try to import hardware libraries, fall back to simulation if not available
try:
    import board
    import adafruit_vcnl4010
    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError, OSError) as e:
    print(f"Hardware libraries not available: {e}")
    print("Running in simulation mode.")
    HARDWARE_AVAILABLE = False


class ModifiedVCNL4010(adafruit_vcnl4010.VCNL4010):
    VCNL4010_IRLED = 0x83

    def __init__(self, i2c, led_current=200):
        super().__init__(i2c)
        self.set_led_current(led_current)

    def set_led_current(self, value):
        self._write_u8(self.VCNL4010_IRLED, value // 10)



class SensorThread(QThread):
    proximity_read = Signal(int)
    finished = Signal(float, float)
    hardware_status = Signal(bool)  # New signal to indicate hardware status

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sample_count = 10  # Default value
        self._running = False
        self.hardware_connected = False
        self.i2c = None
        self.sensor = None
        
        # Try to initialize hardware on startup
        self._test_hardware_connection()

    def _test_hardware_connection(self):
        """Test if hardware is available and can be initialized."""
        if not HARDWARE_AVAILABLE:
            self.hardware_connected = False
            self.hardware_status.emit(False)
            return
            
        try:
            # Try to initialize I2C and sensor
            self.i2c = board.I2C()
            self.sensor = ModifiedVCNL4010(self.i2c)
            self.sensor.set_led_current(50)
            # Test a quick read to verify sensor is responding
            _ = self.sensor.proximity
            self.hardware_connected = True
            print("Hardware connected successfully.")
        except (RuntimeError, OSError, ValueError, Exception) as e:
            print(f"Hardware connection failed: {e}")
            self.hardware_connected = False
            self.i2c = None
            self.sensor = None


        self.hardware_status.emit(self.hardware_connected)

    def set_sample_count(self, count: int):
        self.sample_count = count

    def run(self):
        self._running = True
        samples = []
        proximity = 0

        # If hardware is not connected, use simulation mode
        if not self.hardware_connected:
            print("Running in simulation mode - generating mock data")
            for i in range(self.sample_count):
                if self._running:
                    # Generate realistic mock sensor data
                    proximity = random.randint(32750, 32790)
                    samples.append(proximity)
                    self.proximity_read.emit(proximity)
                    if i < (self.sample_count - 1):
                        for j in range(DELAY_TIME):
                            if not self._running:
                                break
                            else:
                                time.sleep(0.001)
        else:
            # Use real hardware
            try:
                # Re-test connection in case hardware was disconnected
                if not self.sensor:
                    self.i2c = board.I2C()
                    self.sensor = adafruit_vcnl4010.VCNL4010(self.i2c)
                    
                for i in range(self.sample_count):
                    if self._running:
                        proximity = self.sensor.proximity
                        samples.append(proximity)
                        self.proximity_read.emit(proximity)
                        if i < (self.sample_count - 1):
                            for j in range(DELAY_TIME):
                                if not self._running:
                                    break
                                else:
                                    time.sleep(0.001)
            except (RuntimeError, OSError, ValueError, Exception) as e:
                print(f"Hardware error during sampling: {e}")
                print("Falling back to simulation mode")
                # Fall back to simulation for this run
                for i in range(self.sample_count):
                    if self._running:
                        proximity = random.randint(32750, 32790)
                        samples.append(proximity)
                        self.proximity_read.emit(proximity)
                        if i < (self.sample_count - 1):
                            for j in range(DELAY_TIME):
                                if not self._running:
                                    break
                                else:
                                    time.sleep(0.001)
                # Update hardware status
                self.hardware_connected = False
                self.hardware_status.emit(False)

        if self.sample_count >= 2 and self._running:
            mean = statistics.mean(samples)
            stdev = statistics.stdev(samples)
            self._running = False
        else:
            mean = proximity
            stdev = 0

        self.finished.emit(mean, stdev)

    @Slot()
    def stop(self):
        self._running = False


