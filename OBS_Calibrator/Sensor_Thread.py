import random
# import board
# import adafruit_vcnl4010
import statistics
import time
from PySide6.QtCore import Signal, QThread


class SensorThread(QThread):
    proximity_read = Signal(int)
    finished = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sample_count = 10  # Default value
    def set_sample_count(self, count: int):
        self.sample_count = count
    def run(self):
        # i2c = board.I2C()
        # sensor = adafruit_vcnl4010.VCNL4010(i2c)
        samples = []

        for i in range(self.sample_count):
            # proximity = sensor.proximity
            proximity = random.randint(0,65535)
            samples.append(proximity)
            self.proximity_read.emit(proximity)
            time.sleep(0.999)

        if self.sample_count >= 2:
            mean = statistics.mean(samples)
            stdev = statistics.stdev(samples)
            self.finished.emit(mean, stdev)

    def stop(self):
        self._running = False


