import re

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import pyqtSignal, QSettings

from config_types import AccelerometerConfig, CTConfig, LightConfig, TurbidityConfig, IridiumConfig, GNSSConfig, TimingConfig


def _bool_from_settings(settings, key, default=False):
    """Read a bool from QSettings, handling the string 'true'/'false' quirk."""
    val = settings.value(key, default)
    return val is True or val == "true"


class ConfigFrame(QtWidgets.QFrame):
    """Base class for config section frames."""
    configChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                           QtWidgets.QSizePolicy.Policy.Fixed)

    def set_config_enabled(self, enabled):
        """Enable/disable the frame for config mode.

        When re-enabling, _apply_internal_state() restores the correct
        enabled/disabled state for child widgets that depend on toggle buttons.
        """
        self.setEnabled(enabled)
        if enabled:
            self._apply_internal_state()

    def _apply_internal_state(self):
        """Re-apply internal enable/disable logic after frame re-enable."""
        pass

    def get_config(self):
        raise NotImplementedError

    def save_settings(self, settings):
        raise NotImplementedError

    def load_settings(self, settings):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# CT / Temperature
# ---------------------------------------------------------------------------

class CTConfigWidget(ConfigFrame):
    """CT and Temperature enable radio buttons (mutually exclusive)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font12 = QtGui.QFont()
        font12.setPointSize(12)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        self.ctEnableButton = QtWidgets.QRadioButton("Enable CT", parent=self)
        self.ctEnableButton.setFont(font12)
        self.ctEnableButton.setAutoExclusive(False)
        layout.addWidget(self.ctEnableButton)

        self.tempEnableButton = QtWidgets.QRadioButton("Enable Temperature", parent=self)
        self.tempEnableButton.setFont(font12)
        self.tempEnableButton.setAutoExclusive(False)
        layout.addWidget(self.tempEnableButton)

        self.ctEnableButton.clicked.connect(self._on_ct_clicked)
        self.tempEnableButton.clicked.connect(self._on_temp_clicked)

    def _on_ct_clicked(self):
        if self.ctEnableButton.isChecked():
            self.tempEnableButton.setChecked(False)
        self.configChanged.emit()

    def _on_temp_clicked(self):
        if self.tempEnableButton.isChecked():
            self.ctEnableButton.setChecked(False)
        self.configChanged.emit()

    def get_config(self):
        return CTConfig(
            ct_enabled=self.ctEnableButton.isChecked(),
            temperature_enabled=self.tempEnableButton.isChecked(),
        )

    def save_settings(self, settings):
        settings.setValue("ctEnabled", self.ctEnableButton.isChecked())
        settings.setValue("tempEnabled", self.tempEnableButton.isChecked())

    def load_settings(self, settings):
        self.ctEnableButton.setChecked(_bool_from_settings(settings, "ctEnabled"))
        self.tempEnableButton.setChecked(_bool_from_settings(settings, "tempEnabled"))
        self._on_ct_clicked()
        self._on_temp_clicked()


# ---------------------------------------------------------------------------
# Light
# ---------------------------------------------------------------------------

class LightConfigWidget(ConfigFrame):
    """Light sensor config: enable, match GNSS, gain, num samples."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font12 = QtGui.QFont()
        font12.setPointSize(12)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Row 1: enable + match GNSS
        enableRow = QtWidgets.QHBoxLayout()
        self.enableButton = QtWidgets.QRadioButton("Enable Light", parent=self)
        self.enableButton.setFont(font12)
        enableRow.addWidget(self.enableButton)
        self.matchGNSSCheckbox = QtWidgets.QCheckBox("Match GNSS period", parent=self)
        self.matchGNSSCheckbox.setEnabled(False)
        self.matchGNSSCheckbox.setFont(font12)
        enableRow.addWidget(self.matchGNSSCheckbox)
        layout.addLayout(enableRow)

        # Row 2: gain
        gainRow = QtWidgets.QHBoxLayout()
        self.gainLabel = QtWidgets.QLabel("Gain", parent=self)
        self.gainLabel.setEnabled(False)
        gainRow.addWidget(self.gainLabel)
        self.gainComboBox = QtWidgets.QComboBox(parent=self)
        self.gainComboBox.setEnabled(False)
        for g in ("0.5x", "1x", "2x", "4x", "8x", "16x", "32x", "64x", "128x", "256x", "512x"):
            self.gainComboBox.addItem(g)
        self.gainComboBox.setCurrentIndex(2)
        gainRow.addWidget(self.gainComboBox)
        layout.addLayout(gainRow)

        # Row 3: num samples
        samplesRow = QtWidgets.QHBoxLayout()
        self.numSamplesLabel = QtWidgets.QLabel("Number of samples @ 0.5Hz", parent=self)
        self.numSamplesLabel.setEnabled(False)
        self.numSamplesLabel.setFont(font12)
        samplesRow.addWidget(self.numSamplesLabel)
        self.numSamplesSpinBox = QtWidgets.QSpinBox(parent=self)
        self.numSamplesSpinBox.setEnabled(False)
        self.numSamplesSpinBox.setFont(font12)
        self.numSamplesSpinBox.setMaximum(1800)
        self.numSamplesSpinBox.setValue(512)
        samplesRow.addWidget(self.numSamplesSpinBox)
        layout.addLayout(samplesRow)

        # Internal signals
        self.enableButton.clicked.connect(self._on_enable_clicked)
        self.matchGNSSCheckbox.clicked.connect(self._on_match_gnss_clicked)
        self.numSamplesSpinBox.valueChanged.connect(self.configChanged)
        self.gainComboBox.currentIndexChanged.connect(self.configChanged)

        # Cached GNSS params for match-GNSS calculation
        self._gnss_num_samples = 4096
        self._gnss_sample_rate = 4

    def _apply_internal_state(self):
        self._on_enable_clicked()

    def _on_enable_clicked(self):
        enabled = self.enableButton.isChecked()
        self.numSamplesLabel.setEnabled(enabled)
        self.matchGNSSCheckbox.setEnabled(enabled)
        self.gainLabel.setEnabled(enabled)
        self.gainComboBox.setEnabled(enabled)
        if enabled:
            # If match GNSS is checked, samples spinbox stays disabled
            self.numSamplesSpinBox.setEnabled(not self.matchGNSSCheckbox.isChecked())
        else:
            self.numSamplesSpinBox.setEnabled(False)
        self.configChanged.emit()

    def _on_match_gnss_clicked(self):
        if self.matchGNSSCheckbox.isChecked():
            self.numSamplesSpinBox.setEnabled(False)
            self._recalc_matched_samples()
        elif self.enableButton.isChecked():
            self.numSamplesSpinBox.setEnabled(True)
        self.configChanged.emit()

    def _recalc_matched_samples(self):
        if self._gnss_sample_rate > 0:
            # Light samples at 0.5 Hz → divide by 2
            val = int(self._gnss_num_samples / self._gnss_sample_rate / 2)
            self.numSamplesSpinBox.setValue(val)

    def set_gnss_params(self, num_samples, sample_rate):
        """Called when GNSS values change, to update matched samples."""
        self._gnss_num_samples = num_samples
        self._gnss_sample_rate = sample_rate
        if self.matchGNSSCheckbox.isChecked():
            self._recalc_matched_samples()

    def get_config(self):
        return LightConfig(
            enabled=self.enableButton.isChecked(),
            num_samples=self.numSamplesSpinBox.value(),
            gain_index=self.gainComboBox.currentIndex(),
        )

    def save_settings(self, settings):
        settings.setValue("lightEnabled", self.enableButton.isChecked())
        settings.setValue("lightMatchGNSS", self.matchGNSSCheckbox.isChecked())
        settings.setValue("lightNumSamples", self.numSamplesSpinBox.value())
        settings.setValue("lightGainIndex", self.gainComboBox.currentIndex())

    def load_settings(self, settings):
        self.numSamplesSpinBox.setValue(int(settings.value("lightNumSamples", 512)))
        self.gainComboBox.setCurrentIndex(int(settings.value("lightGainIndex", 2)))
        self.matchGNSSCheckbox.setChecked(_bool_from_settings(settings, "lightMatchGNSS"))
        self.enableButton.setChecked(_bool_from_settings(settings, "lightEnabled"))
        self._on_enable_clicked()


# ---------------------------------------------------------------------------
# Accelerometer
# ---------------------------------------------------------------------------

class AccelerometerConfigWidget(ConfigFrame):
    """Accelerometer enable radio button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font12 = QtGui.QFont()
        font12.setPointSize(12)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        self.enableButton = QtWidgets.QRadioButton("Enable Accelerometer", parent=self)
        self.enableButton.setFont(font12)
        self.enableButton.setAutoExclusive(False)
        layout.addWidget(self.enableButton)

        self.enableButton.clicked.connect(self.configChanged)
        self.enableButton.clicked.connect(self._on_enable_clicked)

        self.continuousCheckbox = QtWidgets.QCheckBox("Run Accelerometer Continuously", parent=self)
        self.continuousCheckbox.setEnabled(False)
        self.continuousCheckbox.setFont(font12)
        layout.addWidget(self.continuousCheckbox)

    def _apply_internal_state(self):
        self._on_enable_clicked()

    def _on_enable_clicked(self):
        enabled = self.enableButton.isChecked()
        self.continuousCheckbox.setEnabled(enabled)


    def get_config(self):
        return AccelerometerConfig(self.enableButton.isChecked(), self.continuousCheckbox.isChecked())

    def save_settings(self, settings):
        settings.setValue("accelerometerEnabled", self.enableButton.isChecked())
        settings.setValue("accelerometerContinuous", self.continuousCheckbox.isChecked())

    def load_settings(self, settings):
        self.enableButton.setChecked(_bool_from_settings(settings, "accelerometerEnabled"))
        self.continuousCheckbox.setChecked(_bool_from_settings(settings, "accelerometerContinuous"))


# ---------------------------------------------------------------------------
# Turbidity
# ---------------------------------------------------------------------------

class TurbidityConfigWidget(ConfigFrame):
    """Turbidity sensor config: enable, match GNSS, serial number, num samples."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font12 = QtGui.QFont()
        font12.setPointSize(12)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Row 1: enable + match GNSS
        enableRow = QtWidgets.QHBoxLayout()
        self.enableButton = QtWidgets.QRadioButton("Enable Turbidity", parent=self)
        self.enableButton.setFont(font12)
        enableRow.addWidget(self.enableButton)
        self.matchGNSSCheckbox = QtWidgets.QCheckBox("Match GNSS period", parent=self)
        self.matchGNSSCheckbox.setEnabled(False)
        self.matchGNSSCheckbox.setFont(font12)
        enableRow.addWidget(self.matchGNSSCheckbox)
        layout.addLayout(enableRow)

        # Row 2: serial number
        serialRow = QtWidgets.QHBoxLayout()
        self.serialNumberLabel = QtWidgets.QLabel("Serial Number", parent=self)
        self.serialNumberLabel.setEnabled(False)
        serialRow.addWidget(self.serialNumberLabel)
        self.serialNumberSpinBox = QtWidgets.QSpinBox(parent=self)
        self.serialNumberSpinBox.setEnabled(False)
        self.serialNumberSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.serialNumberSpinBox.setMaximum(65535)
        serialRow.addWidget(self.serialNumberSpinBox)
        layout.addLayout(serialRow)

        # Row 3: num samples
        samplesRow = QtWidgets.QHBoxLayout()
        self.numSamplesLabel = QtWidgets.QLabel("Number of samples @ 1Hz", parent=self)
        self.numSamplesLabel.setEnabled(False)
        self.numSamplesLabel.setFont(font12)
        samplesRow.addWidget(self.numSamplesLabel)
        self.numSamplesSpinBox = QtWidgets.QSpinBox(parent=self)
        self.numSamplesSpinBox.setEnabled(False)
        self.numSamplesSpinBox.setFont(font12)
        self.numSamplesSpinBox.setMaximum(3600)
        self.numSamplesSpinBox.setValue(1024)
        samplesRow.addWidget(self.numSamplesSpinBox)
        layout.addLayout(samplesRow)

        # Internal signals
        self.enableButton.clicked.connect(self._on_enable_clicked)
        self.matchGNSSCheckbox.clicked.connect(self._on_match_gnss_clicked)
        self.numSamplesSpinBox.valueChanged.connect(self.configChanged)

        # Cached GNSS params for match-GNSS calculation
        self._gnss_num_samples = 4096
        self._gnss_sample_rate = 4

    def _apply_internal_state(self):
        self._on_enable_clicked()

    def _on_enable_clicked(self):
        enabled = self.enableButton.isChecked()
        self.numSamplesLabel.setEnabled(enabled)
        self.matchGNSSCheckbox.setEnabled(enabled)
        self.serialNumberLabel.setEnabled(enabled)
        self.serialNumberSpinBox.setEnabled(enabled)
        if enabled:
            self.numSamplesSpinBox.setEnabled(not self.matchGNSSCheckbox.isChecked())
        else:
            self.numSamplesSpinBox.setEnabled(False)
        self.configChanged.emit()

    def _on_match_gnss_clicked(self):
        if self.matchGNSSCheckbox.isChecked():
            self.numSamplesSpinBox.setEnabled(False)
            self._recalc_matched_samples()
        elif self.enableButton.isChecked():
            self.numSamplesSpinBox.setEnabled(True)
        self.configChanged.emit()

    def _recalc_matched_samples(self):
        if self._gnss_sample_rate > 0:
            # Turbidity samples at 1 Hz
            val = int(self._gnss_num_samples / self._gnss_sample_rate)
            self.numSamplesSpinBox.setValue(val)

    def set_gnss_params(self, num_samples, sample_rate):
        """Called when GNSS values change, to update matched samples."""
        self._gnss_num_samples = num_samples
        self._gnss_sample_rate = sample_rate
        if self.matchGNSSCheckbox.isChecked():
            self._recalc_matched_samples()

    def get_config(self):
        return TurbidityConfig(
            enabled=self.enableButton.isChecked(),
            num_samples=self.numSamplesSpinBox.value(),
            serial_number=self.serialNumberSpinBox.value(),
        )

    def save_settings(self, settings):
        settings.setValue("turbidityEnabled", self.enableButton.isChecked())
        settings.setValue("turbidityMatchGNSS", self.matchGNSSCheckbox.isChecked())
        settings.setValue("turbiditySerialNumber", self.serialNumberSpinBox.value())
        settings.setValue("turbidityNumSamples", self.numSamplesSpinBox.value())

    def load_settings(self, settings):
        self.serialNumberSpinBox.setValue(int(settings.value("turbiditySerialNumber", 0)))
        self.numSamplesSpinBox.setValue(int(settings.value("turbidityNumSamples", 1024)))
        self.matchGNSSCheckbox.setChecked(_bool_from_settings(settings, "turbidityMatchGNSS"))
        self.enableButton.setChecked(_bool_from_settings(settings, "turbidityEnabled"))
        self._on_enable_clicked()


# ---------------------------------------------------------------------------
# Iridium
# ---------------------------------------------------------------------------

class IridiumConfigWidget(ConfigFrame):
    """Iridium config: transmit time, modem type."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font12 = QtGui.QFont()
        font12.setPointSize(12)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Row 1: tx time
        txRow = QtWidgets.QHBoxLayout()
        txLabel = QtWidgets.QLabel("Iridium transmit time in mins", parent=self)
        txLabel.setFont(font12)
        txRow.addWidget(txLabel)
        self.txTimeSpinBox = QtWidgets.QSpinBox(parent=self)
        self.txTimeSpinBox.setFont(font12)
        self.txTimeSpinBox.setMaximum(60)
        self.txTimeSpinBox.setValue(5)
        txRow.addWidget(self.txTimeSpinBox)
        layout.addLayout(txRow)

        # Row 2: modem type
        typeRow = QtWidgets.QHBoxLayout()
        self.typeComboBox = QtWidgets.QComboBox(parent=self)
        self.typeComboBox.setFont(font12)
        self.typeComboBox.addItem("V3D")
        self.typeComboBox.addItem("V3F")
        typeRow.addWidget(self.typeComboBox)
        typeLabel = QtWidgets.QLabel("Iridium Modem Type", parent=self)
        typeLabel.setFont(font12)
        typeRow.addWidget(typeLabel)
        layout.addLayout(typeRow)

        self.txTimeSpinBox.valueChanged.connect(self.configChanged)
        self.typeComboBox.currentIndexChanged.connect(self.configChanged)

    def get_config(self):
        return IridiumConfig(
            tx_time=self.txTimeSpinBox.value(),
            v3f=(self.typeComboBox.currentText() == "V3F"),
        )

    def save_settings(self, settings):
        settings.setValue("iridiumTxTime", self.txTimeSpinBox.value())
        settings.setValue("iridiumTypeIndex", self.typeComboBox.currentIndex())

    def load_settings(self, settings):
        self.txTimeSpinBox.setValue(int(settings.value("iridiumTxTime", 5)))
        self.typeComboBox.setCurrentIndex(int(settings.value("iridiumTypeIndex", 0)))


# ---------------------------------------------------------------------------
# GNSS
# ---------------------------------------------------------------------------

class GNSSConfigWidget(ConfigFrame):
    """GNSS config: num samples, high performance mode, sample rate."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font12 = QtGui.QFont()
        font12.setPointSize(12)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Row 1: num samples
        samplesRow = QtWidgets.QHBoxLayout()
        samplesLabel = QtWidgets.QLabel("Number of GNSS samples", parent=self)
        samplesLabel.setFont(font12)
        samplesRow.addWidget(samplesLabel)
        self.numSamplesSpinBox = QtWidgets.QSpinBox(parent=self)
        self.numSamplesSpinBox.setFont(font12)
        self.numSamplesSpinBox.setMaximum(32768)
        self.numSamplesSpinBox.setValue(4096)
        samplesRow.addWidget(self.numSamplesSpinBox)
        layout.addLayout(samplesRow)

        # Row 2: high performance mode
        self.highPerformanceCheckBox = QtWidgets.QCheckBox(
            "Enable GNSS high performance mode", parent=self)
        layout.addWidget(self.highPerformanceCheckBox)

        # Row 3: sample rate
        rateRow = QtWidgets.QHBoxLayout()
        self.sampleRateComboBox = QtWidgets.QComboBox(parent=self)
        self.sampleRateComboBox.setFont(font12)
        self.sampleRateComboBox.addItem("4 Hz")
        self.sampleRateComboBox.addItem("5 Hz")
        rateRow.addWidget(self.sampleRateComboBox)
        rateLabel = QtWidgets.QLabel("GNSS Sampling Rate", parent=self)
        rateLabel.setFont(font12)
        rateRow.addWidget(rateLabel)
        layout.addLayout(rateRow)

        self.numSamplesSpinBox.valueChanged.connect(self.configChanged)
        self.highPerformanceCheckBox.clicked.connect(self.configChanged)
        self.sampleRateComboBox.currentIndexChanged.connect(self.configChanged)

    def _get_sample_rate_int(self):
        text = self.sampleRateComboBox.currentText()
        m = re.search(r'\d+', text)
        return int(m.group()) if m else 4

    def get_config(self):
        return GNSSConfig(
            num_samples=self.numSamplesSpinBox.value(),
            high_performance_mode=self.highPerformanceCheckBox.isChecked(),
            sample_rate=self._get_sample_rate_int(),
        )

    def save_settings(self, settings):
        settings.setValue("gnssNumSamples", self.numSamplesSpinBox.value())
        settings.setValue("gnssHighPerformanceMode", self.highPerformanceCheckBox.isChecked())
        settings.setValue("gnssSampleRateIndex", self.sampleRateComboBox.currentIndex())

    def load_settings(self, settings):
        self.numSamplesSpinBox.setValue(int(settings.value("gnssNumSamples", 4096)))
        self.highPerformanceCheckBox.setChecked(
            _bool_from_settings(settings, "gnssHighPerformanceMode"))
        self.sampleRateComboBox.setCurrentIndex(int(settings.value("gnssSampleRateIndex", 0)))


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

class TimingConfigWidget(ConfigFrame):
    """Timing config: duty cycle, GNSS max acquisition time, tracking number."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font12 = QtGui.QFont()
        font12.setPointSize(12)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Row 1: duty cycle
        dcRow = QtWidgets.QHBoxLayout()
        dcLabel = QtWidgets.QLabel("Total Duty Cycle (mins)", parent=self)
        dcLabel.setFont(font12)
        dcRow.addWidget(dcLabel)
        self.dutyCycleSpinBox = QtWidgets.QSpinBox(parent=self)
        self.dutyCycleSpinBox.setFont(font12)
        self.dutyCycleSpinBox.setMaximum(1440)
        self.dutyCycleSpinBox.setValue(30)
        dcRow.addWidget(self.dutyCycleSpinBox)
        layout.addLayout(dcRow)

        # Row 2: GNSS max acquisition time
        acqRow = QtWidgets.QHBoxLayout()
        acqLabel = QtWidgets.QLabel("GNSS max time to fix (mins)", parent=self)
        acqLabel.setFont(font12)
        acqRow.addWidget(acqLabel)
        self.gnssMaxAcquisitionTimeSpinBox = QtWidgets.QSpinBox(parent=self)
        self.gnssMaxAcquisitionTimeSpinBox.setFont(font12)
        self.gnssMaxAcquisitionTimeSpinBox.setMaximum(10)
        self.gnssMaxAcquisitionTimeSpinBox.setValue(5)
        acqRow.addWidget(self.gnssMaxAcquisitionTimeSpinBox)
        layout.addLayout(acqRow)

        # Row 3: tracking number
        trackRow = QtWidgets.QHBoxLayout()
        trackLabel = QtWidgets.QLabel("microSWIFT Tracking number", parent=self)
        trackLabel.setFont(font12)
        trackRow.addWidget(trackLabel)
        self.trackingNumberSpinBox = QtWidgets.QSpinBox(parent=self)
        self.trackingNumberSpinBox.setFont(font12)
        self.trackingNumberSpinBox.setMaximum(1000)
        self.trackingNumberSpinBox.setValue(100)
        trackRow.addWidget(self.trackingNumberSpinBox)
        layout.addLayout(trackRow)

        self.dutyCycleSpinBox.valueChanged.connect(self.configChanged)
        self.gnssMaxAcquisitionTimeSpinBox.valueChanged.connect(self.configChanged)
        self.trackingNumberSpinBox.valueChanged.connect(self.configChanged)

    def get_config(self):
        return TimingConfig(
            duty_cycle=self.dutyCycleSpinBox.value(),
            gnss_max_acquisition_time=self.gnssMaxAcquisitionTimeSpinBox.value(),
            tracking_number=self.trackingNumberSpinBox.value(),
        )

    def save_settings(self, settings):
        settings.setValue("dutyCycle", self.dutyCycleSpinBox.value())
        settings.setValue("gnssMaxAcquisitionTime", self.gnssMaxAcquisitionTimeSpinBox.value())
        settings.setValue("trackingNumber", self.trackingNumberSpinBox.value())

    def load_settings(self, settings):
        self.dutyCycleSpinBox.setValue(int(settings.value("dutyCycle", 30)))
        self.gnssMaxAcquisitionTimeSpinBox.setValue(int(settings.value("gnssMaxAcquisitionTime", 5)))
        self.trackingNumberSpinBox.setValue(int(settings.value("trackingNumber", 100)))
