
import sys
from functools import partial
from pathlib import Path

import os

from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from Sensor_Thread import SensorThread
from Python.autogen.settings import url, import_paths

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"



class UIController(QObject):
    def __init__(self, root_object):

        def make_sample_count_updater(index):
            def updater(value):
                self.sensor_thread.set_sample_count(value)

            return updater

        super().__init__()
        self.root = root_object
        self.sensor_thread = SensorThread()
        self.active_component_index = None

        self.ntu_components = [
            self.root.findChild(QObject, f"ntuComponent{i}") for i in range(10)
        ]

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

        self.sensor_thread.proximity_read.connect(self.update_samples_text_area)
        self.sensor_thread.finished.connect(self.handle_sensor_finished)

        # Connect signal
        self.num_calibration_points_spinbox = self.root.findChild(QObject, "numCalibrationPointsSpinBox")
        self.num_calibration_points_spinbox.valueChanged.connect(self.update_ntu_components)

    def handle_sample_count_change(self, index, value):
        if self.active_component_index == index:
            self.sensor_thread.set_sample_count(value)

    def handle_sensor_finished(self, mean, stdev):
        if self.active_component_index is None:
            return

        component = self.ntu_components[self.active_component_index]

        average_spinbox = component.findChild(QObject, "averageSpinBox")
        stdev_spinbox = component.findChild(QObject, "stdevSpinBox")

        if average_spinbox:
            average_spinbox.setProperty("value", mean)

        if stdev_spinbox:
            if mean > 0 and stdev > 0.01 * mean:
                stdev_spinbox.setProperty("textColor", "red")
            else:
                stdev_spinbox.setProperty("textColor", "white")

            stdev_spinbox.setProperty("value", stdev)

    def update_ntu_components(self):
        # Get the current value from the spinbox
        value = self.num_calibration_points_spinbox.property("value")

        # Enable only the required number of NTU components
        for i in range(10):
            component = self.root.findChild(QObject, f"ntuComponent{i}")
            if component:
                component.setProperty("enabled", i < value)

    def start_sensor(self, index):
        component = self.ntu_components[index]
        num_samples_spinbox = component.findChild(QObject, "numSamplesSpinBox")
        if num_samples_spinbox:
            # Force read the current value directly
            sample_count = num_samples_spinbox.property("value")
            self.sensor_thread.set_sample_count(sample_count)

        self.active_component_index = index
        self.sensor_thread.start()

    def update_samples_text_area(self, value):
        if self.active_component_index is not None:
            component = self.ntu_components[self.active_component_index]
            text_area = component.findChild(QObject, "samplesTextArea")
            if text_area:
                current_text = text_area.property("text") or ""
                new_text = f"{current_text}\n{value}" if current_text else str(value)
                text_area.setProperty("text", new_text)


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
    ui = UIController(root_object)

    sys.exit(app.exec())
