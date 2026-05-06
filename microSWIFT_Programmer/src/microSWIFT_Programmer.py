#!/usr/bin/env python3

import platform
import struct
import sys
import os
import requests
import serial.tools.list_ports
import re
import subprocess

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QTextCharFormat, QColor, QGuiApplication, QFont, QTextCursor
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QTextEdit, QFileDialog, QMainWindow
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, QThread, Qt, QSettings

from datetime import datetime
import glob as glob_module

from config_types import CTConfig, LightConfig, TurbidityConfig, IridiumConfig, GNSSConfig, TimingConfig
from config_widgets import (
    CTConfigWidget, LightConfigWidget, AccelerometerConfigWidget,
    TurbidityConfigWidget, IridiumConfigWidget, GNSSConfigWidget,
    TimingConfigWidget,
)

PROGRAMMER_MAJOR_VERSION = 1
PROGRAMMER_MINOR_VERSION = 4


def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Development mode - look for resources relative to the src directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


def get_firmware_path(filename):
    """Get the path to a firmware file."""
    return get_resource_path(os.path.join('firmware', filename))


def get_ui_path(filename):
    """Get the path to a UI file."""
    return get_resource_path(os.path.join('resources', 'ui', filename))


def get_image_path(filename):
    """Get the path to an image file."""
    return get_resource_path(os.path.join('resources', 'images', filename))


# Default firmware URL — used on startup and when the user clicks "Reset to default"
DEFAULT_FIRMWARE_URL = "https://github.com/SASlabgroup/microSWIFT-V2-Binaries/raw/main/V2.2/microSWIFT_V2.2.elf"

# Cap download size to prevent a bad URL from exhausting disk (50 MB)
MAX_FIRMWARE_BYTES = 50 * 1024 * 1024


def normalize_firmware_url(url):
    """Rewrite common GitHub URL variants so they return the raw binary.

    GitHub's 'blob' URL (what users get from the address bar when viewing a
    file on github.com) returns an HTML page, not the file content. The 'raw'
    form returns the actual bytes. We transparently rewrite blob->raw so users
    can paste either one. Returns (normalized_url, was_rewritten).
    """
    if not url:
        return url, False
    stripped = url.strip()
    # Only touch github.com URLs; leave raw.githubusercontent.com and other
    # hosts alone.
    if "://github.com/" in stripped and "/blob/" in stripped:
        return stripped.replace("/blob/", "/raw/", 1), True
    return stripped, False


def validate_firmware_url(url):
    """Check a URL looks reasonable for firmware download.

    Returns (is_valid, error_message). Does not make any network calls.
    """
    from urllib.parse import urlparse

    if url is None:
        return False, "URL is empty."

    url = url.strip()
    if not url:
        return False, "URL is empty."

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, "Could not parse URL: {e}".format(e=e)

    if parsed.scheme not in ("http", "https"):
        return False, ("URL must start with http:// or https:// "
                       "(got '{s}').".format(s=parsed.scheme or "nothing"))

    if not parsed.netloc:
        return False, "URL is missing a host (e.g. github.com)."

    # Extract filename from path. GitHub 'raw' URLs end in the filename.
    filename = os.path.basename(parsed.path)
    if not filename:
        return False, "URL does not point to a file."

    return True, ""


def firmware_needs_config(path):
    """Return True if the firmware requires configuration flashing.

    Only firmware whose filename starts with 'microSWIFT_V2' needs the
    config.bin + zeros_64k.bin step.  All other .elf binaries are standalone.
    """
    return os.path.basename(path).startswith("microSWIFT_V2")


def filename_from_url(url):
    """Derive a local filename from a URL. Falls back to a generic name."""
    from urllib.parse import urlparse
    name = os.path.basename(urlparse(url).path)
    if not name:
        name = "firmware.bin"
    return name


def download_microSWIFT_firmware(url):
    """
    Download firmware from `url`.

    Returns (success, local_file_path, error_message). `local_file_path` is
    populated even on failure (to the path that *would* have been used) so the
    caller can display it; `error_message` is empty on success.
    """
    # Rewrite GitHub blob URLs to raw URLs so users can paste either form
    url, _rewritten = normalize_firmware_url(url)

    valid, err = validate_firmware_url(url)
    if not valid:
        return False, "", err

    # Derive filename from the URL so user-supplied URLs save sensibly
    filename = filename_from_url(url)
    firmware_dir = get_resource_path('firmware')
    local_file_path = os.path.join(firmware_dir, filename)

    try:
        os.makedirs(firmware_dir, exist_ok=True)
    except OSError as e:
        return False, local_file_path, "Could not create firmware directory: {e}".format(e=e)

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Raise an error on bad HTTP status

        # Catch the common mistake of pasting a GitHub "blob" URL or a link
        # to an HTML page. If the server advertises HTML, the bytes won't be
        # firmware no matter what the URL looks like.
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" in content_type:
            return False, local_file_path, (
                "Server returned an HTML page, not a binary file "
                "(Content-Type: {ct}). If this is a GitHub link, make sure "
                "you are using the 'raw' URL, not the 'blob' view URL."
            ).format(ct=content_type)

        # If the server reports an oversized file up front, bail before writing
        content_length = response.headers.get("Content-Length")
        if content_length and content_length.isdigit() and int(content_length) > MAX_FIRMWARE_BYTES:
            return False, local_file_path, (
                "File is too large ({n} bytes, limit {limit}).".format(
                    n=content_length, limit=MAX_FIRMWARE_BYTES))

        # Write the file (overwrite if exists)
        downloaded = 0
        first_bytes = b""
        with open(local_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                if len(first_bytes) < 16:
                    first_bytes += chunk[:16 - len(first_bytes)]
                downloaded += len(chunk)
                if downloaded > MAX_FIRMWARE_BYTES:
                    # Clean up a partial download so we never flash a truncated file
                    f.close()
                    try:
                        os.remove(local_file_path)
                    except OSError:
                        pass
                    return False, local_file_path, "Download exceeded size limit."
                f.write(chunk)

        # Sanity check: empty files are never valid firmware
        if os.path.getsize(local_file_path) == 0:
            try:
                os.remove(local_file_path)
            except OSError:
                pass
            return False, local_file_path, "Downloaded file is empty."

        # Magic-byte sniff: detect HTML saved under a .elf/.bin name. This
        # catches servers that return HTML without setting Content-Type, or
        # proxies/captive-portals that intercept the request. We don't hard-
        # require ELF magic because .bin files are raw binaries with no fixed
        # header — but HTML never starts with a valid firmware header.
        head = first_bytes.lstrip()[:16].lower()
        html_markers = (b"<!doctype", b"<html", b"<head", b"<body", b"<?xml")
        if any(head.startswith(m) for m in html_markers):
            try:
                os.remove(local_file_path)
            except OSError:
                pass
            return False, local_file_path, (
                "Downloaded file looks like an HTML page, not firmware. "
                "If this is a GitHub link, use the 'raw' URL, not the 'blob' URL.")

        # If the URL claims to be an .elf, we can additionally verify the ELF
        # magic bytes (0x7F 'E' 'L' 'F'). Non-ELF extensions skip this check.
        if filename.lower().endswith(".elf") and not first_bytes.startswith(b"\x7fELF"):
            try:
                os.remove(local_file_path)
            except OSError:
                pass
            return False, local_file_path, (
                "Downloaded .elf file is missing the ELF magic bytes. The URL "
                "may be pointing at the wrong file or returning a redirect page.")

        return True, local_file_path, ""
    except requests.Timeout:
        return False, local_file_path, "Download timed out after 10 seconds."
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        return False, local_file_path, "HTTP error {s} from server.".format(s=status)
    except requests.ConnectionError:
        return False, local_file_path, "Could not connect to server (check URL and network)."
    except requests.RequestException as e:
        return False, local_file_path, "Download failed: {e}".format(e=e)
    except OSError as e:
        return False, local_file_path, "Could not write file: {e}".format(e=e)


class Worker(QThread):
    finished = pyqtSignal()
    stdoutAvailable = pyqtSignal(str)
    stderrAvailable = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Path to the firmware .elf/.bin to flash. Set via setFirmwarePath() before run().
        self.firmware_path = get_firmware_path("microSWIFT_V2.2.elf")
        # ST-LINK serial number to target. When set, passed as sn=<serial> to
        # STM32CubeProgrammer so it uses a specific probe.
        self.stlink_serial = None
        # Whether to flash configuration after firmware (only for microSWIFT_V2*)
        self.flash_config = True

    def setFirmwarePath(self, path):
        """Set the firmware binary to flash on the next run."""
        self.firmware_path = path

    def setStlinkSerial(self, serial):
        """Set the ST-LINK serial number to target on the next run."""
        self.stlink_serial = serial

    def setFlashConfig(self, enabled):
        """Set whether configuration should be flashed after firmware."""
        self.flash_config = enabled

    def get_programmer_path(self):
        """Return the platform-specific path to STM32_Programmer_CLI, or None."""
        system = platform.system()
        if system == "Darwin":
            return ("/Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/"
                    "STM32CubeProgrammer.app/Contents/MacOs/bin/STM32_Programmer_CLI")
        elif system == "Windows":
            return (r"C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin"
                    r"\STM32_Programmer_CLI.exe")
        else:  # Linux
            for path in [
                "/usr/local/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI",
                "/opt/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI",
                os.path.expanduser("~/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI"),
            ]:
                if os.path.exists(path):
                    return path
            return None

    def _run_programmer(self, command):
        """Run an STM32CubeProgrammer command, emitting output via signals.

        Returns True if the process exited successfully, False otherwise.
        """
        try:
            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.Popen(
                command, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                startupinfo=startupinfo)

            while process.poll() is None:
                stdout, stderr = process.communicate()
                if stdout:
                    cleanedText = re.sub(r'\x1b\[[0-9;]*[mG]', '', stdout)
                    self.stdoutAvailable.emit(cleanedText)

            if process.returncode != 0:
                self.stderrAvailable.emit(
                    "\nProgramming Failed with code {}".format(process.returncode))
                return False
            return True

        except subprocess.CalledProcessError as e:
            self.stderrAvailable.emit("/nError: {}".format(e.stderr))
            self.stderrAvailable.emit(e.stdout)
        except Exception as e:
            self.stderrAvailable.emit("Unexpected error: {}".format(e))
        return False

    def flash_firmware(self, programmer_path, connect_args):
        """Flash the firmware .elf to the device. Returns True on success."""
        firmware_path = self.firmware_path
        if not firmware_path or not os.path.isfile(firmware_path):
            self.stderrAvailable.emit(
                "Error: firmware file not found: {p}".format(p=firmware_path))
            return False

        command = [programmer_path] + connect_args + [
            "--download", firmware_path,
            "--verify", "-rst"
        ]
        return self._run_programmer(command)

    def flash_configuration(self, programmer_path, connect_args):
        """Write config.bin and zeros_64k.bin to device memory. Returns True on success."""
        config_path = get_firmware_path("config.bin")
        command = [programmer_path] + connect_args + [
            "--download", config_path,
            "0x083FFC00",
        ]
        if not self._run_programmer(command):
            return False

        zeros_path = get_firmware_path("zeros_64k.bin")
        command = [programmer_path] + connect_args + [
            "--download", zeros_path,
            "0x200C0000",
        ]
        return self._run_programmer(command)

    def run(self):
        programmer_path = self.get_programmer_path()
        if not programmer_path:
            self.stderrAvailable.emit("Error: STM32CubeProgrammer not found")
            self.finished.emit()
            return

        connect_args = ["--connect", "port=SWD"]
        if self.stlink_serial:
            connect_args.append("sn={}".format(self.stlink_serial))

        if self.flash_firmware(programmer_path, connect_args):
            if self.flash_config:
                self.flash_configuration(programmer_path, connect_args)

        self.finished.emit()


class ProgrammerApp(QMainWindow):
    device_connected = False
    stlink_port = ""
    stlink_serial = ""
    configFilePath = None

    def __init__(self):
        super().__init__()
        self.firmware_path = get_firmware_path("microSWIFT_V2.2.elf")
        self.configFilePath = get_firmware_path("config.bin")
        self.stlink_devices = []
        self.firmware_files = []
        self._config_needed = True
        self.setupUi()

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.centralwidget = QtWidgets.QWidget()
        self.centralwidget.setObjectName("centralwidget")

        # ---- Top-level layout ----
        mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        mainLayout.setContentsMargins(4, 4, 4, 4)
        mainLayout.setSpacing(4)

        columnsLayout = QtWidgets.QHBoxLayout()
        columnsLayout.setSpacing(4)
        leftColumn = QtWidgets.QVBoxLayout()
        leftColumn.setSpacing(4)
        rightColumn = QtWidgets.QVBoxLayout()
        rightColumn.setSpacing(4)
        columnsLayout.addLayout(leftColumn, stretch=1)
        columnsLayout.addLayout(rightColumn, stretch=1)
        mainLayout.addLayout(columnsLayout)

        # ---- Helper for frame styling ----
        def styled_frame():
            frame = QtWidgets.QFrame(parent=self.centralwidget)
            frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
            frame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                                QtWidgets.QSizePolicy.Policy.Fixed)
            return frame

        font12 = QtGui.QFont()
        font12.setPointSize(12)
        font11 = QtGui.QFont()
        font11.setPointSize(11)

        # ---- Config widgets (left column) ----
        self.ctWidget = CTConfigWidget(parent=self.centralwidget)
        leftColumn.addWidget(self.ctWidget)

        self.lightWidget = LightConfigWidget(parent=self.centralwidget)
        leftColumn.addWidget(self.lightWidget)

        self.accelWidget = AccelerometerConfigWidget(parent=self.centralwidget)
        leftColumn.addWidget(self.accelWidget)

        self.turbidityWidget = TurbidityConfigWidget(parent=self.centralwidget)
        leftColumn.addWidget(self.turbidityWidget)

        self.iridiumWidget = IridiumConfigWidget(parent=self.centralwidget)
        leftColumn.addWidget(self.iridiumWidget)

        self.gnssWidget = GNSSConfigWidget(parent=self.centralwidget)
        leftColumn.addWidget(self.gnssWidget)

        leftColumn.addStretch(1)

        # ---- Graphics view (right column) ----
        self.graphicsView = QtWidgets.QGraphicsView(parent=self.centralwidget)
        self.graphicsView.setFixedHeight(231)
        self.graphicsView.setObjectName("graphicsView")
        rightColumn.addWidget(self.graphicsView)

        # ---- Timing widget (right column) ----
        self.timingWidget = TimingConfigWidget(parent=self.centralwidget)
        rightColumn.addWidget(self.timingWidget)

        # --- ST-LINK device selection frame (right column) ---
        self.stlinkFrame = styled_frame()
        self.stlinkFrame.setObjectName("stlinkFrame")
        self.stlinkVertLayout = QtWidgets.QVBoxLayout(self.stlinkFrame)
        self.stlinkVertLayout.setSpacing(4)
        self.stlinkVertLayout.setContentsMargins(4, 4, 4, 4)
        self.stlinkVertLayout.setObjectName("stlinkVertLayout")
        self.stlinkLabelHorizLayout = QtWidgets.QHBoxLayout()
        self.stlinkLabelHorizLayout.setObjectName("stlinkLabelHorizLayout")
        self.stlinkLabel = QtWidgets.QLabel(parent=self.stlinkFrame)
        self.stlinkLabel.setFont(font12)
        self.stlinkLabel.setObjectName("stlinkLabel")
        self.stlinkLabelHorizLayout.addWidget(self.stlinkLabel)
        self.stlinkRefreshButton = QtWidgets.QPushButton(parent=self.stlinkFrame)
        self.stlinkRefreshButton.setObjectName("stlinkRefreshButton")
        self.stlinkRefreshButton.setMaximumWidth(70)
        self.stlinkLabelHorizLayout.addWidget(self.stlinkRefreshButton)
        self.stlinkVertLayout.addLayout(self.stlinkLabelHorizLayout)
        self.stlinkComboBox = QtWidgets.QComboBox(parent=self.stlinkFrame)
        self.stlinkComboBox.setFont(font11)
        self.stlinkComboBox.setObjectName("stlinkComboBox")
        self.stlinkVertLayout.addWidget(self.stlinkComboBox)

        # --- Action buttons frame (right column) ---
        self.actionFrame = styled_frame()
        self.actionFrame.setObjectName("actionFrame")
        self.actionVertLayout = QtWidgets.QVBoxLayout(self.actionFrame)
        self.stlinkVertLayout.setSpacing(4)
        self.actionVertLayout.setContentsMargins(4, 4, 4, 4)
        self.actionVertLayout.setObjectName("actionVertLayout")
        self.verifyButton = QtWidgets.QPushButton(parent=self.actionFrame)
        self.verifyButton.setFont(font12)
        self.verifyButton.setObjectName("verifyButton")
        self.actionVertLayout.addWidget(self.verifyButton)
        self.programButton = QtWidgets.QPushButton(parent=self.actionFrame)
        self.programButton.setFont(font12)
        self.programButton.setObjectName("programButton")
        self.actionVertLayout.addWidget(self.programButton)
        self.downloadConfigFile = QtWidgets.QPushButton(parent=self.actionFrame)
        self.downloadConfigFile.setObjectName("downloadConfigFile")
        self.actionVertLayout.addWidget(self.downloadConfigFile)
        rightColumn.addWidget(self.actionFrame)

        rightColumn.addStretch(1)

        # --- Combined firmware panel: file selection + URL download (full width) ---
        self.firmwareUrlFrame = styled_frame()
        self.firmwareUrlFrame.setObjectName("firmwareUrlFrame")
        self.firmwareUrlVertLayout = QtWidgets.QVBoxLayout(self.firmwareUrlFrame)
        self.firmwareUrlVertLayout.setContentsMargins(4, 4, 4, 4)
        self.firmwareUrlVertLayout.setSpacing(4)

        # Row 1: "Available Firmware:" label + Refresh button
        self.firmwareLabelRow = QtWidgets.QHBoxLayout()
        self.firmwareLabel = QtWidgets.QLabel(parent=self.firmwareUrlFrame)
        self.firmwareLabel.setFont(font12)
        self.firmwareLabel.setObjectName("firmwareLabel")
        self.firmwareLabelRow.addWidget(self.firmwareLabel)
        self.firmwareRefreshButton = QtWidgets.QPushButton(parent=self.firmwareUrlFrame)
        self.firmwareRefreshButton.setObjectName("firmwareRefreshButton")
        self.firmwareRefreshButton.setMaximumWidth(70)
        self.firmwareLabelRow.addWidget(self.firmwareRefreshButton)
        self.firmwareUrlVertLayout.addLayout(self.firmwareLabelRow)

        # Row 2: Firmware file combo box
        self.firmwareComboBox = QtWidgets.QComboBox(parent=self.firmwareUrlFrame)
        self.firmwareComboBox.setFont(font11)
        self.firmwareComboBox.setObjectName("firmwareComboBox")
        self.firmwareUrlVertLayout.addWidget(self.firmwareComboBox)

        # Row 3: "Firmware URL:" label + Download button + Reset button
        self.firmwareUrlRow = QtWidgets.QHBoxLayout()
        self.firmwareUrlLabel = QtWidgets.QLabel(parent=self.firmwareUrlFrame)
        self.firmwareUrlLabel.setObjectName("firmwareUrlLabel")
        self.firmwareUrlRow.addWidget(self.firmwareUrlLabel)
        self.firmwareUrlRow.addStretch(1)
        self.useUrlButton = QtWidgets.QPushButton(parent=self.firmwareUrlFrame)
        self.useUrlButton.setObjectName("useUrlButton")
        self.firmwareUrlRow.addWidget(self.useUrlButton)
        self.resetUrlButton = QtWidgets.QPushButton(parent=self.firmwareUrlFrame)
        self.resetUrlButton.setObjectName("resetUrlButton")
        self.firmwareUrlRow.addWidget(self.resetUrlButton)
        self.firmwareUrlVertLayout.addLayout(self.firmwareUrlRow)

        # Row 4: URL text entry (full width)
        self.firmwareUrlLineEdit = QtWidgets.QLineEdit(parent=self.firmwareUrlFrame)
        self.firmwareUrlLineEdit.setObjectName("firmwareUrlLineEdit")
        self.firmwareUrlLineEdit.setText(DEFAULT_FIRMWARE_URL)
        self.firmwareUrlLineEdit.setClearButtonEnabled(True)
        self.firmwareUrlVertLayout.addWidget(self.firmwareUrlLineEdit)

        mainLayout.addWidget(self.stlinkFrame)
        mainLayout.addWidget(self.firmwareUrlFrame)

        # ---- Status text area (full width, expands) ----
        self.statusTextEdit = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.statusTextEdit.setObjectName("statusTextEdit")
        self.statusTextEdit.setReadOnly(True)
        self.statusTextEdit.setMinimumHeight(150)
        self.statusTextEdit.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                          QtWidgets.QSizePolicy.Policy.Expanding)
        mainLayout.addWidget(self.statusTextEdit, stretch=1)

        # ---- Config widgets list (used for bulk enable/disable) ----
        self._config_widgets = [
            self.ctWidget, self.lightWidget, self.accelWidget,
            self.turbidityWidget, self.iridiumWidget, self.gnssWidget,
            self.timingWidget,
        ]

        self.setCentralWidget(self.centralwidget)

        self._setWidgetLabels()
        self.finishSetup()

    def _setWidgetLabels(self):
        """Set text labels for non-config UI elements."""
        self.setWindowTitle("microSWIFT Configurator Version "
                            "{major}.{minor}".format(major=PROGRAMMER_MAJOR_VERSION,
                                                     minor=PROGRAMMER_MINOR_VERSION))
        self.stlinkLabel.setText("Available ST-LINKs:")
        self.stlinkRefreshButton.setText("Refresh")
        self.verifyButton.setText("Verify")
        self.programButton.setText("Program")
        self.downloadConfigFile.setText("Download Config")
        self.firmwareLabel.setText("Available Firmware:")
        self.firmwareRefreshButton.setText("Refresh")
        self.firmwareUrlLabel.setText("Firmware URL:")
        self.useUrlButton.setText("Download")
        self.resetUrlButton.setText("Reset to default")

    def adjust_font_color_based_on_background(self, text_edit: QTextEdit):
        """Adjusts font color in a QTextEdit based on background color."""
        # Get the background color from the QTextEdit's palette
        bg_color = text_edit.palette().color(text_edit.viewport().backgroundRole())

        red = bg_color.red()
        green = bg_color.green()
        blue = bg_color.blue()

        # Determine if the background is "close enough" to black or white
        is_black = bg_color.red() < 50 and bg_color.green() < 50 and bg_color.blue() < 50
        is_white = bg_color.red() > 200 and bg_color.green() > 200 and bg_color.blue() > 200

        # Decide font color
        if is_black:
            font_color = QColor(Qt.GlobalColor.white)
        elif is_white:
            font_color = QColor(Qt.GlobalColor.black)
        else:
            # For non-pure black/white backgrounds, you could calculate contrast or set a default
            # Here we default to black for safety
            font_color = QColor(Qt.GlobalColor.black)

        # Apply the font color to the entire document
        cursor = text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        format = QTextCharFormat()
        format.setForeground(font_color)
        cursor.mergeCharFormat(format)
        text_edit.mergeCurrentCharFormat(format)

    def finishSetup(self):
        self.worker = Worker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.scene = QGraphicsScene()

        self.connectUIElements()
        self.find_usb_port()
        self.displayPicture()

        self.loadSettings()

        self.statusTextEdit.setFont(QFont("Courier New"))

        (self.writeText
         ("           _        "
          "       ______       "
          " _____ _____ _____  "
          "   \r\n"
          " _ __ ___ (_) ___ _ "
          "__ ___/ ___\\ \\    "
          "  / /_ _|  ___|_   _"
          "|    \r\n"
          "| \'_ ` _ \\| |/ __|"
          " \'__/ _ \\___ \\\\ "
          "\\ /\\ / / | || |_  "
          "  | |      \r\n"
          "| | | | | | | (__| |"
          " | (_) |__) |\\ V  V"
          " /  | ||  _|   | |  "
          "    \r\n"
          "|_|_|_| |_|_|\\___|_"
          "|  \\___/____/  \\_/"
          "\\_/  |___|_|     |_"
          "|      \r\n"
          "|  _ \\ _ __ ___   _"
          "_ _ _ __ __ _ _ __ _"
          "__  _ __ ___   ___ _"
          " __ \r\n"
          "| |_) | \'__/ _ \\ /"
          " _` | \'__/ _` | \'_"
          " ` _ \\| \'_ ` _ \\ "
          "/ _ \\ \'__|\r\n"
          "|  __/| | | (_) | (_"
          "| | | | (_| | | | | "
          "| | | | | | |  __/ |"
          "   \r\n"
          "|_|   |_|  \\___/ \\"
          "__, |_|  \\__,_|_| |"
          "_| |_|_| |_| |_|\\__"
          "_|_|   \r\n"
          "                 |__"
          "_/                  "
          "                    "
          "   "
          "\r\r\nPlease ensure you are running the most recent version of this tool."
          "\r\nVisit https://github.com/SASlabgroup/microSWIFT-programmer"))


        # Populate the firmware file dropdown and select the active firmware.
        self.refreshFirmwareList()

    def saveConfigAsFile(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Save File")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]

            with open(selected_file, "wb") as config_file:
                config_file.write(self.assembleBinaryConfigStruct())
                self.writeText("Saved configuration file {file}".format(file=selected_file))


    def assembleBinaryConfigStruct(self):
        '''
                    Definition of configuration struct from configuration.h in firmware files

                    typedef struct __attribute__((packed)) microSWIFT_configuration
                    {
                      uint32_t tracking_number;
                      uint32_t gnss_samples_per_window;
                      uint32_t duty_cycle;
                      uint32_t iridium_max_transmit_time;
                      uint32_t gnss_max_acquisition_wait_time;
                      uint32_t gnss_sampling_rate;
                      uint32_t total_light_samples;
                      uint32_t light_sensor_gain;
                      uint32_t total_turbidity_samples;
                      uint16_t turbidity_serial_number;

                      bool iridium_v3f;
                      bool gnss_high_performance_mode;
                      bool ct_enabled;
                      bool temperature_enabled;
                      bool light_enabled;
                      bool turbidity_enabled;
                      bool accelerometer_enabled;

                      const char compile_date_flash[11];
                      const char compile_time_flash[9];
                    } microSWIFT_configuration;
                    '''
        ct = self.ctWidget.get_config()
        light = self.lightWidget.get_config()
        accel = self.accelWidget.get_config()
        turbidity = self.turbidityWidget.get_config()
        iridium = self.iridiumWidget.get_config()
        gnss = self.gnssWidget.get_config()
        timing = self.timingWidget.get_config()

        current_datetime = datetime.now()
        date = current_datetime.strftime("%m/%d/%Y") + "\x00"
        time = current_datetime.strftime("%H:%M:%S") + "\x00"

        return struct.pack("<LLLLLLLLLH???????11s9s",
                           timing.tracking_number,
                           gnss.num_samples,
                           timing.duty_cycle,
                           iridium.tx_time,
                           timing.gnss_max_acquisition_time,
                           gnss.sample_rate,
                           light.num_samples,
                           light.gain_index,
                           turbidity.num_samples,
                           turbidity.serial_number,
                           iridium.v3f,
                           gnss.high_performance_mode,
                           ct.ct_enabled,
                           ct.temperature_enabled,
                           light.enabled,
                           turbidity.enabled,
                           accel,
                           bytes(date.encode("utf-8")),
                           bytes(time.encode("utf-8")),
                           )
    def assembleBinaryConfigFile(self):
        with open(self.configFilePath, "wb") as configFile:
            configFile.write(self.assembleBinaryConfigStruct())

    def saveSettings(self):
        settings = QSettings("SASlabgroup", "microSWIFT_Programmer")
        for w in self._config_widgets:
            w.save_settings(settings)
        settings.setValue("stlinkSerial", self.stlink_serial)
        settings.setValue("firmwareUrl", self.firmwareUrlLineEdit.text())

    def loadSettings(self):
        settings = QSettings("SASlabgroup", "microSWIFT_Programmer")
        if not settings.contains("trackingNumber"):
            return
        for w in self._config_widgets:
            w.load_settings(settings)
        # ST-LINK — select by serial number if the device is currently connected
        saved_serial = settings.value("stlinkSerial", "")
        if saved_serial and self.stlink_devices:
            for i, dev in enumerate(self.stlink_devices):
                if dev['serial'] == saved_serial:
                    self.stlinkComboBox.setCurrentIndex(i)
                    break
        # Firmware URL
        url = settings.value("firmwareUrl", "")
        if url:
            self.firmwareUrlLineEdit.setText(url)

    def connectUIElements(self):
        self.worker.stdoutAvailable.connect(self.appendText)
        self.worker.stderrAvailable.connect(self.appendError)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.reenableGUI)
        self.worker.finished.connect(self.threadFinished)

        # Config widget signals → reset verify on any change
        for w in self._config_widgets:
            w.configChanged.connect(self.resetVerifyButton)

        # GNSS → Light/Turbidity cross-widget coordination
        self.gnssWidget.configChanged.connect(self._syncGNSSToSensors)

        # Non-config UI connections
        self.stlinkComboBox.currentIndexChanged.connect(self.onStlinkSelected)
        self.stlinkRefreshButton.clicked.connect(self.find_usb_port)

        self.firmwareComboBox.currentIndexChanged.connect(self.onFirmwareSelected)
        self.firmwareRefreshButton.clicked.connect(self.refreshFirmwareList)

        self.verifyButton.clicked.connect(self.verifySettings)
        self.programButton.clicked.connect(self.programDevice)
        self.downloadConfigFile.clicked.connect(self.saveConfigAsFile)

        self.useUrlButton.clicked.connect(self.onUseUrlClicked)
        self.resetUrlButton.clicked.connect(self.onResetUrlClicked)
        self.firmwareUrlLineEdit.returnPressed.connect(self.onUseUrlClicked)

        self.programButton.setDisabled(True)
        self.downloadConfigFile.setDisabled(True)

    def _syncGNSSToSensors(self):
        """Forward GNSS parameters to Light and Turbidity widgets for match-GNSS calculation."""
        gnss = self.gnssWidget.get_config()
        self.lightWidget.set_gnss_params(gnss.num_samples, gnss.sample_rate)
        self.turbidityWidget.set_gnss_params(gnss.num_samples, gnss.sample_rate)

    def find_usb_port(self):
        """Scan for all ST-LINK devices and populate the dropdown."""
        ports = serial.tools.list_ports.comports()

        # STMicroelectronics VID and known ST-Link PIDs
        STMICRO_VID = 0x0483
        STLINK_PIDS = {
            0x3744: "ST-LINK/V1",
            0x3748: "ST-LINK/V2",
            0x374A: "ST-LINK/V2",
            0x374B: "ST-LINK/V2-1",
            0x3752: "ST-LINK/V2-1",
            0x3753: "ST-LINK/V3 (bootloader)",
            0x3754: "ST-LINK/V3",
            0x3755: "ST-LINK/V3",
            0x3757: "ST-LINK/V3 MINIE",
            0x3758: "ST-LINK/V3 SET"
        }

        self.stlink_devices = []
        seen_ports = set()

        for port in ports:
            if port.device in seen_ports:
                continue

            stlink_model = None

            # Check by description (macOS/Linux)
            if "STLINK" in port.description.upper() or "ST-LINK" in port.description.upper():
                stlink_model = "ST-LINK"

            # Check by VID/PID (works on Windows and as fallback)
            if (hasattr(port, 'vid') and hasattr(port, 'pid') and
                    port.vid == STMICRO_VID and port.pid in STLINK_PIDS):
                stlink_model = STLINK_PIDS[port.pid]

            if stlink_model:
                seen_ports.add(port.device)
                serial_number = getattr(port, 'serial_number', None) or ""
                self.stlink_devices.append({
                    'model': stlink_model,
                    'port': port.device,
                    'serial': serial_number,
                })

        # Populate the combo box (block signals to avoid spurious callbacks)
        self.stlinkComboBox.blockSignals(True)
        self.stlinkComboBox.clear()

        if self.stlink_devices:
            for dev in self.stlink_devices:
                if dev['serial']:
                    label = "{port} (SN: {sn}) - {model}".format(
                        port=dev['port'], sn=dev['serial'], model=dev['model'])
                else:
                    label = "{port} - {model}".format(
                        port=dev['port'], model=dev['model'])
                self.stlinkComboBox.addItem(label)
            self.stlinkComboBox.setEnabled(True)
            self.stlinkComboBox.blockSignals(False)
            self.onStlinkSelected(0)
        else:
            self.stlinkComboBox.addItem("No ST-LINK devices found")
            self.stlinkComboBox.setEnabled(False)
            self.stlinkComboBox.blockSignals(False)
            self.device_connected = False
            self.stlink_port = ""
            self.stlink_serial = ""

    def refreshFirmwareList(self):
        """Scan the firmware directory for .elf files and populate the dropdown."""
        firmware_dir = get_resource_path('firmware')
        elf_files = []

        if os.path.isdir(firmware_dir):
            for path in sorted(glob_module.glob(os.path.join(firmware_dir, '*.elf'))):
                try:
                    stat = os.stat(path)
                    size_kb = stat.st_size / 1024.0
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    elf_files.append({
                        'path': path,
                        'name': os.path.basename(path),
                        'size_kb': size_kb,
                        'mtime': mtime,
                    })
                except OSError:
                    continue

        self.firmware_files = elf_files

        self.firmwareComboBox.blockSignals(True)
        self.firmwareComboBox.clear()

        if elf_files:
            for f in elf_files:
                label = "{name}  ({mtime}, {kb:.1f} KB)".format(
                    name=f['name'], mtime=f['mtime'], kb=f['size_kb'])
                self.firmwareComboBox.addItem(label)
            self.firmwareComboBox.setEnabled(True)
            self.firmwareComboBox.blockSignals(False)
            # If there's a currently active firmware, try to select it
            selected = -1
            if self.firmware_path:
                basename = os.path.basename(self.firmware_path)
                for i, f in enumerate(elf_files):
                    if f['name'] == basename:
                        selected = i
                        break
            if selected >= 0:
                self.firmwareComboBox.setCurrentIndex(selected)
            else:
                self.firmwareComboBox.setCurrentIndex(0)
            self.onFirmwareSelected(self.firmwareComboBox.currentIndex())
        else:
            self.firmwareComboBox.addItem("No .elf files found in firmware/")
            self.firmwareComboBox.setEnabled(False)
            self.firmwareComboBox.blockSignals(False)
            self.firmware_path = ""
            self.programButton.setDisabled(True)

    def _setConfigEnabled(self, enabled):
        """Enable or disable all configuration-related widgets.

        When re-enabling, each widget's set_config_enabled restores the correct
        internal state (e.g. Light sub-controls stay disabled if Light is off).
        """
        self._config_needed = enabled

        for w in self._config_widgets:
            w.set_config_enabled(enabled)

        if enabled:
            self.verifyButton.setVisible(True)
            self.verifyButton.setEnabled(True)
            self.downloadConfigFile.setVisible(True)
            self.resetVerifyButton()
        else:
            self.verifyButton.setVisible(False)
            self.downloadConfigFile.setVisible(False)
            if self.firmware_path and os.path.isfile(self.firmware_path):
                self.programButton.setEnabled(True)
            else:
                self.programButton.setDisabled(True)

    def onFirmwareSelected(self, index):
        """Handle firmware file selection from the dropdown."""
        if not self.firmware_files or index < 0 or index >= len(self.firmware_files):
            self.firmware_path = ""
            return
        self.firmware_path = self.firmware_files[index]['path']
        self.worker.setFirmwarePath(self.firmware_path)
        self._setConfigEnabled(firmware_needs_config(self.firmware_path))

    def onStlinkSelected(self, index):
        """Handle ST-LINK device selection from the dropdown."""
        if not self.stlink_devices or index < 0 or index >= len(self.stlink_devices):
            self.device_connected = False
            self.stlink_port = ""
            self.stlink_serial = ""
            return
        dev = self.stlink_devices[index]
        self.device_connected = True
        self.stlink_port = dev['port']
        self.stlink_serial = dev['serial']

    def verifySettings(self):
        light = self.lightWidget.get_config()
        turbidity = self.turbidityWidget.get_config()
        iridium = self.iridiumWidget.get_config()
        gnss = self.gnssWidget.get_config()
        timing = self.timingWidget.get_config()

        settings_invalid = False
        verify_strings = []

        gnss_duration = (((gnss.num_samples / gnss.sample_rate) / 60) + 1) + timing.gnss_max_acquisition_time

        if (timing.duty_cycle - gnss_duration - iridium.tx_time) < 0:
            verify_strings.append("Duty cycle not long enough to complete GNSS sample window.\n")
            settings_invalid = True

        if light.enabled:
            if ((timing.duty_cycle - ((light.num_samples / 30) + 1) - iridium.tx_time) < 0):
                verify_strings.append("Duty cycle not long enough to complete Light sample window.\n")
                settings_invalid = True
            if int(gnss.num_samples / gnss.sample_rate / 2) > 1800:
                verify_strings.append("Max number of light samples is 1800.\n")
                settings_invalid = True

        if turbidity.enabled:
            if ((timing.duty_cycle - ((turbidity.num_samples / 60) + 1) - iridium.tx_time) < 0):
                verify_strings.append("Duty cycle not long enough to complete Turbidity sample window.\n")
                settings_invalid = True
            if int(gnss.num_samples / gnss.sample_rate) > 3600:
                verify_strings.append("Max number of turbidity samples is 3600.\n")
                settings_invalid = True

        if settings_invalid:
            self.programButton.setDisabled(True)
            self.downloadConfigFile.setDisabled(True)
            self.verifyButton.setText("❌ Verify - Settings Invalid")
            self.verifyButton.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.writeError("".join(verify_strings))
        else:
            self.programButton.setEnabled(True)
            self.downloadConfigFile.setEnabled(True)
            self.verifyButton.setText("✅ Verify - Settings Valid")
            self.verifyButton.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.writeText("Settings verified. You did a great job.")

    def resetVerifyButton(self, clear_status=True):
        if not self._config_needed:
            # No config means no verify step; Program stays directly enabled
            return
        self.programButton.setDisabled(True)
        self.downloadConfigFile.setDisabled(True)
        # Reset button text to default
        self.verifyButton.setText("Verify")
        self.verifyButton.setStyleSheet("font-size: 16px;")
        if clear_status:
            self.writeText("Configure as desired and press the Verify button when ready.")

    def writeError(self, err_str):
        self.statusTextEdit.clear()

        char_format = QTextCharFormat()
        char_format.setForeground(QColor('red'))

        self.statusTextEdit.setCurrentCharFormat(char_format)

        self.statusTextEdit.setText(err_str)

    def writeText(self, err_str):
        self.statusTextEdit.clear()
        self.adjust_font_color_based_on_background(self.statusTextEdit)

        self.statusTextEdit.setText(err_str)

    def appendText(self, string):
        self.adjust_font_color_based_on_background(self.statusTextEdit)

        self.statusTextEdit.append(string)

    def appendError(self, string):
        char_format = QTextCharFormat()
        char_format.setForeground(QColor('red'))

        self.statusTextEdit.setCurrentCharFormat(char_format)

        self.statusTextEdit.append(string)

    def updateActiveFirmwareDisplay(self):
        """Refresh the firmware dropdown and gate the Program button.

        The Program button should only be usable if we actually have a firmware
        file on disk to flash.
        """
        self.refreshFirmwareList()

    def onResetUrlClicked(self):
        self.firmwareUrlLineEdit.setText(DEFAULT_FIRMWARE_URL)

    def onUseUrlClicked(self):
        """Validate the URL, download the firmware, and update the UI."""
        url = self.firmwareUrlLineEdit.text().strip()

        # Rewrite GitHub blob URLs to raw URLs transparently, and let the user
        # know we did it so they can paste the right form next time.
        normalized, rewritten = normalize_firmware_url(url)
        if rewritten:
            self.firmwareUrlLineEdit.setText(normalized)
            url = normalized

        valid, err = validate_firmware_url(url)
        if not valid:
            QtWidgets.QMessageBox.warning(self, "Invalid URL", err)
            return

        # Disable the button while the download runs so the user can't stack
        # multiple requests. This is a quick blocking download (same pattern as
        # the existing startup download) — small firmware file, short timeout.
        self.useUrlButton.setDisabled(True)
        self.resetUrlButton.setDisabled(True)
        self.firmwareUrlLineEdit.setDisabled(True)
        if rewritten:
            self.writeText(
                "Rewrote GitHub 'blob' URL to 'raw' URL.\n"
                "Downloading firmware from: {u}".format(u=url))
        else:
            self.writeText("Downloading firmware from: {u}".format(u=url))
        QGuiApplication.processEvents()  # let the label repaint before blocking

        try:
            success, path, error = download_microSWIFT_firmware(url)
        finally:
            self.useUrlButton.setEnabled(True)
            self.resetUrlButton.setEnabled(True)
            self.firmwareUrlLineEdit.setEnabled(True)

        if success:
            self.firmware_path = path
            self.appendText("Firmware downloaded to: {p}".format(p=path))
            self.updateActiveFirmwareDisplay()
            # Require re-verification since the firmware changed
            self.resetVerifyButton()
        else:
            self.appendError("Download failed: {e}".format(e=error))
            QtWidgets.QMessageBox.critical(
                self, "Download failed",
                "Could not download firmware:\n\n{e}".format(e=error))

    def programDevice(self):
        self.saveSettings()

        # Remember the user's selection before refreshing the device list
        prev_serial = self.stlink_serial

        self.find_usb_port()

        # Restore the previous selection if the device is still present
        if prev_serial and self.stlink_devices:
            for i, dev in enumerate(self.stlink_devices):
                if dev['serial'] == prev_serial:
                    self.stlinkComboBox.setCurrentIndex(i)
                    break

        if not self.device_connected:
            self.writeError("STLink programmer not detected.")
            return

        # Get the currently selected device
        idx = self.stlinkComboBox.currentIndex()
        if idx < 0 or idx >= len(self.stlink_devices):
            self.writeError("No ST-LINK device selected.")
            return
        dev = self.stlink_devices[idx]

        # Double-check we have a firmware file to flash — it could have been
        # deleted between download and program click.
        if not self.firmware_path or not os.path.isfile(self.firmware_path):
            self.writeError("No firmware file is loaded. Download one first.")
            self.updateActiveFirmwareDisplay()
            return

        if self._config_needed:
            self.assembleBinaryConfigFile()

        # Hand the current firmware path and ST-LINK serial to the worker
        self.worker.setFirmwarePath(self.firmware_path)
        self.worker.setStlinkSerial(dev['serial'])
        self.worker.setFlashConfig(self._config_needed)

        selected_label = self.stlinkComboBox.currentText()
        config_note = " (with configuration)" if self._config_needed else " (firmware only)"
        self.writeText(
            "Running STM32 Programmer CLI, please wait.\n"
            "Using: {dev}\n"
            "Flashing firmware{note}: {p}".format(
                dev=selected_label, note=config_note, p=self.firmware_path))

        self.disableGUI()
        # Run the worker thread so the program will be non-blocking
        self.thread.start()

    def disableGUI(self):
        for w in self._config_widgets:
            w.setEnabled(False)
        self.stlinkComboBox.setDisabled(True)
        self.stlinkRefreshButton.setDisabled(True)
        self.verifyButton.setDisabled(True)
        self.programButton.setDisabled(True)
        self.downloadConfigFile.setDisabled(True)
        self.firmwareComboBox.setDisabled(True)
        self.firmwareRefreshButton.setDisabled(True)
        self.firmwareUrlLineEdit.setDisabled(True)
        self.useUrlButton.setDisabled(True)
        self.resetUrlButton.setDisabled(True)

    def reenableGUI(self):
        if self._config_needed:
            for w in self._config_widgets:
                w.set_config_enabled(True)
            self.verifyButton.setEnabled(True)
            self.downloadConfigFile.setEnabled(True)
            self.resetVerifyButton(clear_status=False)
        else:
            self.programButton.setEnabled(True)

        self.stlinkComboBox.setEnabled(True)
        self.stlinkRefreshButton.setEnabled(True)
        self.firmwareComboBox.setEnabled(True)
        self.firmwareRefreshButton.setEnabled(True)
        self.firmwareUrlLineEdit.setEnabled(True)
        self.useUrlButton.setEnabled(True)
        self.resetUrlButton.setEnabled(True)

    def displayPicture(self):

        self.graphicsView.setScene(self.scene)
        pixmap = QPixmap(get_image_path("microSWIFT_pic.png"))
        pixmapItem = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmapItem)

    def threadFinished(self):
        self.thread.quit()
        self.thread.wait()


def main():
    app = QtWidgets.QApplication(sys.argv)
    programmer = ProgrammerApp()
    programmer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


