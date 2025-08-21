import tempfile
from pathlib import Path

import sys
import os
import csv
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend for safe offscreen plotting
import matplotlib.pyplot as plt
import numpy as np
import shutil

from PySide6.QtCore import QObject, QUrl, Slot, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from Sensor_Thread import SensorThread
from Python.autogen.settings import url, import_paths

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

class UIController(QObject):
    plotReady = Signal(str)
    requestSaveFile = Signal()  # Signal to trigger QML FileDialog
    _pending_plot_data = None   # Store data temporarily before user picks path

    def __init__(self, sensor_thread):
        super().__init__()
        self.ntu_components = None
        self.serialNumberTextField = None
        self.find_equation_button = None
        self.saveSampleDataButton = None
        self.num_calibration_points_spinbox = None
        self.root = None
        self.sensor_thread = sensor_thread
        self.active_component_index = 1
        self.num_points = 1
        self.cal_point_complete = [False] * 10
        self.cal_points = [[0.0, 0.0] for _ in range(10)]

    def setup(self, root_object):
        """Call this after QML has loaded to bind UI objects."""
        self.root = root_object

        # Grab references to all the things we're going to need often
        self.ntu_components = [self.root.findChild(QObject, f"ntuComponent{i}") for i in range(10)]
        self.serialNumberTextField = self.root.findChild(QObject, "serialNumberTextField")
        self.num_calibration_points_spinbox = self.root.findChild(QObject, "numCalibrationPointsSpinBox")
        self.saveSampleDataButton = self.root.findChild(QObject, "saveSampleData")
        self.find_equation_button = self.root.findChild(QObject, "findEquationButton")

        # Set up the NTU Concentration Components
        for i, component in enumerate(self.ntu_components):
            if component:
                start_button = component.findChild(QObject, "startButton")
                if start_button:
                    start_button.clicked.connect(lambda idx=i: self.start_sensor(idx))

                reset_button = component.findChild(QObject, "resetButton")
                if reset_button:
                    reset_button.clicked.connect(lambda idx=i: self.reset_component(idx))

        self.sensor_thread.proximity_read.connect(self.update_samples_text_area)
        self.sensor_thread.finished.connect(self.handle_sensor_finished)
        self.find_equation_button.clicked.connect(self.compute_calibration_equation)

        # Connect signals
        self.num_calibration_points_spinbox.valueChanged.connect(self.update_ntu_components)

    @Slot()
    @Slot()
    def resetApplicationState(self):
        """Reset the app to its initial state after closing the plot popup."""
        for i, component in enumerate(self.ntu_components):
            if not component:
                continue

            # Reset sampling-related spinboxes
            num_samples_spinbox = component.findChild(QObject, "numSamplesSpinBox")
            if num_samples_spinbox:
                num_samples_spinbox.setProperty("value", 1)

            ntu_spinbox = component.findChild(QObject, "ntuConcentrationSpinBox")
            if ntu_spinbox:
                ntu_spinbox.setProperty("value", 0)

            # Reset text fields, mean, stdev, internal tracking
            self.reset_component(i)

        # Reset spinboxes outside NTU components
        if self.num_calibration_points_spinbox:
            self.num_calibration_points_spinbox.setProperty("value", 1)
            self.num_calibration_points_spinbox.setProperty("enabled", True)

        # Reset serial number field
        if self.serialNumberTextField:
            self.serialNumberTextField.setProperty("text", "0")

        # Reset buttons
        if self.find_equation_button:
            self.find_equation_button.setProperty("enabled", False)
        if self.saveSampleDataButton:
            self.saveSampleDataButton.setProperty("enabled", True)

        # Clear pending plot data
        self._pending_plot_data = None

    def enable_sampling_controls(self, component):
        for name in ["startButton", "numSamplesSpinBox", "ntuConcentrationSpinBox"]:
            field = component.findChild(QObject, name)
            if field:
                field.setProperty("enabled", True)

    @Slot(float, float)
    def handle_sensor_finished(self, mean, stdev):
        if self.active_component_index is None:
            return

        component = self.ntu_components[self.active_component_index]
        self.enable_sampling_controls(component)

        ntu_concentration = component.findChild(QObject, "ntuConcentrationSpinBox")
        average_spinbox = component.findChild(QObject, "averageSpinBox")
        stdev_spinbox = component.findChild(QObject, "stdevSpinBox")

        if average_spinbox:
            average_spinbox.setProperty("value", mean)

        if stdev_spinbox:
            stdev_spinbox.setProperty("value", stdev)
            if mean > 0 and stdev > 0.01 * mean:
                stdev_spinbox.setProperty("textColor", "red")
                self.cal_point_complete[self.active_component_index] = False
            else:
                stdev_spinbox.setProperty("textColor", "white")
                self.cal_point_complete[self.active_component_index] = True
                self.cal_points[self.active_component_index] = [mean, ntu_concentration.property("value")]
                self.checkFindEquation()

        for i in range(self.root.findChild(QObject, "numCalibrationPointsSpinBox").property("value")):
            self.ntu_components[i].setProperty("enabled", True)

        # Enable the save sample data button
        self.saveSampleDataButton.setProperty("enabled", True)
        # Enable the calibration points spinbox
        self.num_calibration_points_spinbox.setProperty("enabled", True)

    def reset_component(self, index):
        if self.sensor_thread.isRunning():
            self.sensor_thread.stop()
            self.sensor_thread.wait()

        component = self.ntu_components[index]
        self.enable_sampling_controls(component)

        samples_text_area = component.findChild(QObject, "samplesTextArea")
        if samples_text_area:
            samples_text_area.setProperty("text", "")

        average_spinbox = component.findChild(QObject, "averageSpinBox")
        if average_spinbox:
            average_spinbox.setProperty("value", 0)

        stdev_spinbox = component.findChild(QObject, "stdevSpinBox")
        if stdev_spinbox:
            stdev_spinbox.setProperty("value", 0)
            stdev_spinbox.setProperty("textColor", "white")

        self.cal_point_complete[index] = False
        self.checkFindEquation()

    def update_ntu_components(self):
        # Get the current value from the spinbox
        value = self.num_calibration_points_spinbox.property("value")
        self.num_points = value

        # Enable only the required number of NTU components
        for i in range(10):
            component = self.root.findChild(QObject, f"ntuComponent{i}")
            if component:
                component.setProperty("enabled", i < value)

        self.checkFindEquation()

    def start_sensor(self, index):
        component = self.ntu_components[index]
        self.active_component_index = index
        self.reset_component(index)

        # Force commit of spinbox value
        num_samples_spinbox = component.findChild(QObject, "numSamplesSpinBox")
        if num_samples_spinbox:
            sample_count = num_samples_spinbox.property("value")
            self.sensor_thread.set_sample_count(sample_count)

        self.active_component_index = index

        # Disable only the relevant fields
        for name in ["startButton", "numSamplesSpinBox", "ntuConcentrationSpinBox"]:
            field = component.findChild(QObject, name)
            if field:
                field.setProperty("enabled", False)

        self.saveSampleDataButton.setProperty("enabled", False)

        for i in range(10):
            self.ntu_components[i].setProperty("enabled", i == self.active_component_index)

        # Disable the calibration points spinbox
        self.num_calibration_points_spinbox.setProperty("enabled", False)
        # Start the sensor thread running
        self.sensor_thread.start()

    @Slot(int)
    def update_samples_text_area(self, value):
        if self.active_component_index is not None:
            component = self.ntu_components[self.active_component_index]
            text_area = component.findChild(QObject, "samplesTextArea")
            if text_area:
                current_text = text_area.property("text") or ""
                new_text = f"{current_text}\n{value}" if current_text else str(value)
                text_area.setProperty("text", new_text)

    @Slot(str)
    def saveSampleData(self, file_url):
        if not file_url or not file_url.startswith("file://"):
            print("No file selected or invalid path.")
            return

        file_path = file_url.replace("file://", "")
        file_path = os.path.expanduser(file_path)

        if not file_path.strip():
            print("File path is empty after processing.")
            return

        all_samples = []

        for i in range(self.num_points):
            if self.cal_point_complete[i]:
                component = self.ntu_components[i]

                try:
                    concentration_field = component.findChild(QObject, "ntuConcentrationSpinBox")
                    sample_area = component.findChild(QObject, "samplesTextArea")

                    if not concentration_field or not sample_area:
                        continue  # Skip if either child is missing

                    concentration = float(concentration_field.property("value"))
                    sample_lines = sample_area.property("text").splitlines()

                    for line in sample_lines:
                        line = line.strip()
                        if line:
                            try:
                                reading = int(line)
                                all_samples.append((concentration, reading))
                            except ValueError:
                                continue  # Skip invalid lines
                except Exception as e:
                    print(f"Error processing component: {e}")
                    continue

        # Sort samples by NTU concentration
        all_samples.sort(key=lambda x: x[0])

        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["NTU concentration", "sensor reading"])
                writer.writerows(all_samples)
            print(f"Sample data saved to {file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")

    def checkFindEquation(self):
        if self.num_points > 1:
            for i in range(self.num_points):
                if not self.cal_point_complete[i]:
                    self.find_equation_button.setProperty("enabled", False)
                    return

            self.find_equation_button.setProperty("enabled", True)

    import tempfile

    def compute_calibration_equation(self):
        # Only use the number of points specified
        self.cal_points = self.cal_points[:self.num_points]

        x = np.array([pt[0] for pt in self.cal_points]).reshape(-1, 1)
        y = np.array([pt[1] for pt in self.cal_points])

        model = LinearRegression()
        model.fit(x, y)

        y_pred = model.predict(x)
        r_squared = r2_score(y, y_pred)

        # Store plot data so it can be saved later
        self._pending_plot_data = (x, y, model.coef_[0], model.intercept_, r_squared)

        # Save plot to a temporary file for QML to display
        temp_path = os.path.join(tempfile.gettempdir(), "calibration_plot.png")
        self.plot_calibration_curve(x, y, model.coef_[0], model.intercept_, r_squared, temp_path)

        # Tell QML to open the dialog and show this temp file
        self.plotReady.emit(temp_path)

    def plot_calibration_curve(self, x, y, slope, intercept, r2, save_path):
        # Offscreen figure
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Scatter points and regression line
        ax.scatter(x, y, color='blue', label='Calibration Points')
        y_pred = slope * x + intercept
        ax.plot(x, y_pred, color='red', label='Regression Line')

        # Labels and title
        ax.set_xlabel('Sensor Reading')
        ax.set_ylabel('Measured Value')
        ax.set_title('Sensor Calibration Curve')
        ax.legend()

        # Equation text overlay
        equation_text = f"y = {slope:.2f}x + {intercept:.2f}\nR² = {r2:.4f}"
        ax.text(0.05, 0.95, equation_text, transform=ax.transAxes,
                fontsize=12, verticalalignment='top',
                bbox=dict(facecolor='white', alpha=0.5))

        # Save as PNG
        canvas.print_png(save_path)

    @Slot(str)
    def saveCalibrationPlot(self, file_url):
        if not self._pending_plot_data:
            print("No pending plot data.")
            return

        if not file_url or not file_url.startswith("file://"):
            print("Invalid file URL:", file_url)
            return

        x, y, slope, intercept, r2 = self._pending_plot_data
        file_path = os.path.expanduser(file_url[7:])  # strip file://

        try:
            self.plot_calibration_curve(x, y, slope, intercept, r2, file_path)
            print(f"Calibration plot saved to {file_path}")
        except Exception as e:
            print(f"Error saving calibration plot: {e}")

        self._pending_plot_data = None

    @Slot(str, str)
    def copy_file_to_destination(self, src, dest):
        try:
            shutil.copyfile(src, dest)
            print(f"Plot saved to {dest}")
        except Exception as e:
            print(f"Error saving plot: {e}")


if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    app_dir = Path(__file__).parent
    engine.addImportPath(os.fspath(app_dir))
    for path in import_paths:
        engine.addImportPath(os.fspath(app_dir / path))

    sensor_thread = SensorThread()
    controller = UIController(sensor_thread)

    # Expose controller BEFORE QML loads
    engine.rootContext().setContextProperty("uiController", controller)

    # Only load ONE entry QML file
    engine.load(QUrl("OBS_Calibrator/OBS_Calibration_WindowContent/App.qml"))
    # or:
    # engine.load(QUrl("OBS_Calibrator/OBS_Calibration_WindowContent/OBS_Calibrator_Screen.ui.qml"))

    if not engine.rootObjects():
        sys.exit(-1)

    root_object = engine.rootObjects()[0]
    controller.setup(root_object)

    app.aboutToQuit.connect(sensor_thread.stop)
    sys.exit(app.exec())
