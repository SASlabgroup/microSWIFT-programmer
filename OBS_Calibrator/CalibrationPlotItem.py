import numpy as np
import matplotlib.pyplot as plt
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider
from io import BytesIO


class CalibrationPlotItem(QObject):
    imageChanged = Signal()
    equationChanged = Signal()
    r2Changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self._equation = ""
        self._r2 = ""

    @Slot('QVariantList', 'QVariantList')
    def generate_plot(self, x_values, y_values):
        x = np.array(x_values)
        y = np.array(y_values)

        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs
        y_fit = slope * x + intercept

        # R² calculation
        ss_res = np.sum((y - y_fit) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        self._equation = f"y = {slope:.4f}x + {intercept:.4f}"
        self._r2 = f"R² = {r_squared:.4f}"
        self.equationChanged.emit()
        self.r2Changed.emit()

        # Plot
        fig, ax = plt.subplots()
        ax.scatter(x, y, color='blue', label='Sample Points')
        ax.plot(x, y_fit, color='red', label='Best Fit Line')
        ax.set_title("Calibration Curve")
        ax.set_xlabel("Sensor Value")
        ax.set_ylabel("NTU")
        ax.legend()

        # Save to buffer
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)

        # Convert to QImage
        self._image = QImage.fromData(buf.read())
        self.imageChanged.emit()

    def getImage(self):
        return self._image

    def getEquation(self):
        return self._equation

    def getR2(self):
        return self._r2

    image = Property(QImage, getImage, notify=imageChanged)
    equation = Property(str, getEquation, notify=equationChanged)
    r2 = Property(str, getR2, notify=r2Changed)


class CalibrationImageProvider(QQuickImageProvider):
    def __init__(self, calibration_plot_item):
        super().__init__(QQuickImageProvider.Image)
        self.calibration_plot_item = calibration_plot_item

    def requestImage(self, id, size, requestedSize):
        image = self.calibration_plot_item.getImage()
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image

