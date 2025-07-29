
from pathlib import Path

import sys
import os
import csv

from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from Sensor_Thread import SensorThread
from Python.autogen.settings import url, import_paths

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

class UIController(QObject):
    def __init__(self, root_object):

        super().__init__()
        self.root = root_object
        self.sensor_thread = SensorThread()
        self.active_component_index = None
        self.num_points = 1
        self.cal_point_complete = [False] * 10

        # Grab references to all the things we're going to need often
        self.ntu_components = [self.root.findChild(QObject, f"ntuComponent{i}") for i in range(10)]
        self.serialNumberTextField = self.root.findChild(QObject, "serialNumberTextField")
        self.num_calibration_points_spinbox = self.root.findChild(QObject, "numCalibrationPointsSpinBox")
        self.saveSampleDataButton = self.root.findChild(QObject, "saveSampleData")

        # Set up the NTU Concentration Components
        for i, component in enumerate(self.ntu_components):
            if component:
                start_button = component.findChild(QObject, "startButton")
                if start_button:
                    start_button.clicked.connect(lambda idx=i: self.start_sensor(idx))

                num_samples_spinbox = component.findChild(QObject, "numSamplesSpinBox")
                if num_samples_spinbox:
                    sample_count = num_samples_spinbox.property("value")
                    num_samples_spinbox.valueChanged.connect(
                        lambda  value=sample_count, idx=i: self.handle_sample_count_change(idx, value)
                    )

                reset_button = component.findChild(QObject, "resetButton")
                if reset_button:
                    reset_button.clicked.connect(lambda idx=i: self.reset_component(idx))

        self.sensor_thread.proximity_read.connect(self.update_samples_text_area)
        self.sensor_thread.finished.connect(self.handle_sensor_finished)

        # Connect signals
        self.num_calibration_points_spinbox.valueChanged.connect(self.update_ntu_components)

    def handle_sample_count_change(self, index, value):
        if self.active_component_index == index:
            self.sensor_thread.set_sample_count(value)

    def _enable_sampling_controls(self, component):
        for name in ["startButton", "numSamplesSpinBox", "ntuConcentrationSpinBox"]:
            field = component.findChild(QObject, name)
            if field:
                field.setProperty("enabled", True)

    def handle_sensor_finished(self, mean, stdev):
        if self.active_component_index is None:
            return

        component = self.ntu_components[self.active_component_index]
        self._enable_sampling_controls(component)

        average_spinbox = component.findChild(QObject, "averageSpinBox")
        stdev_spinbox = component.findChild(QObject, "stdevSpinBox")

        if average_spinbox:
            average_spinbox.setProperty("value", mean)

        if stdev_spinbox:
            stdev_spinbox.setProperty("value", stdev)
            if mean > 0 and stdev > 0.01 * mean:
                stdev_spinbox.setProperty("textColor", "red")
            else:
                stdev_spinbox.setProperty("textColor", "white")
                self.cal_point_complete[self.active_component_index] = True

        for i in range(self.root.findChild(QObject, "numCalibrationPointsSpinBox").property("value")):
            self.ntu_components[i].setProperty("enabled", True)

        # Enable the save sample data button
        self.saveSampleDataButton.setProperty("enabled", True)

    def reset_component(self, index):
        if self.sensor_thread.isRunning():
            self.sensor_thread.stop()
            self.sensor_thread.wait()

        component = self.ntu_components[index]
        self._enable_sampling_controls(component)

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

    def update_ntu_components(self):
        # Get the current value from the spinbox
        value = self.num_calibration_points_spinbox.property("value")
        self.num_points = value

        # Enable only the required number of NTU components
        for i in range(10):
            component = self.root.findChild(QObject, f"ntuComponent{i}")
            if component:
                component.setProperty("enabled", i < value)

    def start_sensor(self, index):
        component = self.ntu_components[index]
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


        self.sensor_thread.start()

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

        for component in self.ntu_components:
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



if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    app_dir = Path(__file__).parent

    engine.addImportPath(os.fspath(app_dir))
    for path in import_paths:
        engine.addImportPath(os.fspath(app_dir / path))

    engine.load(os.fspath(app_dir/url))
    if not engine.rootObjects():
        sys.exit(-1)

    root_object = engine.rootObjects()[0]
    controller = UIController(root_object)  # Your controller class instance
    engine.rootContext().setContextProperty("controller", controller)

    engine.load(QUrl("OBS_Calibrator/OBS_Calibration_WindowContent/OBS_Calibrator_Screen.ui.qml"))

    sys.exit(app.exec())