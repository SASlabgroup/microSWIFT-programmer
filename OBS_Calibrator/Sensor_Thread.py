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
        self._running = False
    def set_sample_count(self, count: int):
        self.sample_count = count
    def run(self):
        self._running = True
        # i2c = board.I2C()
        # sensor = adafruit_vcnl4010.VCNL4010(i2c)
        samples = []
        proximity = 0

        for i in range(self.sample_count):
            if self._running:
                # proximity = sensor.proximity
                proximity = random.randint(0,65535)
                samples.append(proximity)
                self.proximity_read.emit(proximity)
                if i < (self.sample_count - 1):
                    for i in range(999):
                        if not self._running:
                            break
                        else:
                            time.sleep(0.001)

        if self.sample_count >= 2 and self._running:
            mean = statistics.mean(samples)
            stdev = statistics.stdev(samples)

            self._running = False
        else:
            mean = proximity
            stdev = 0

        self.finished.emit(mean, stdev)


    def stop(self):
        self._running = False


