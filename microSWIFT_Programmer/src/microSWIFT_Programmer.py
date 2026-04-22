#!/usr/bin/env python3

import platform
import struct
import sys
import os
import requests
import serial.tools.list_ports
import re
import subprocess
import argparse

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QTextCharFormat, QColor, QGuiApplication, QFont, QTextCursor
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QTextEdit, QFileDialog, QMainWindow
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, QThread, Qt

from datetime import datetime

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


def filename_from_url(url):
    """Derive a local filename from a URL. Falls back to a generic name."""
    from urllib.parse import urlparse
    name = os.path.basename(urlparse(url).path)
    if not name:
        name = "firmware.bin"
    return name


def download_microSWIFT_firmware(url=None):
    """Download firmware from `url` (defaults to DEFAULT_FIRMWARE_URL).

    Returns (success, local_file_path, error_message). `local_file_path` is
    populated even on failure (to the path that *would* have been used) so the
    caller can display it; `error_message` is empty on success.
    """
    if url is None:
        url = DEFAULT_FIRMWARE_URL

    # Rewrite GitHub blob URLs to raw URLs so users can paste either form
    url, _rewritten = normalize_firmware_url(url)

    valid, err = validate_firmware_url(url)
    if not valid:
        return False, "", err

    # Derive filename from the URL so user-supplied URLs save sensibly
    filename = filename_from_url(url)
    firmware_dir = get_resource_path('firmware')
    local_file_path = os.path.join(firmware_dir, filename)

    # Ensure the firmware directory exists
    try:
        os.makedirs(firmware_dir, exist_ok=True)
    except OSError as e:
        return False, local_file_path, "Could not create firmware directory: {e}".format(e=e)

    try:
        # Add a timeout (in seconds)
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

    def setFirmwarePath(self, path):
        """Set the firmware binary to flash on the next run."""
        self.firmware_path = path

    def run(self):
        firmwareBurnSuccessful = False
        configBurnSuccessful = False
        systemOS = platform.system()

        if systemOS == "Darwin":  # MacOS
            programmerPath = ("/Applications/STMicroelectronics/STM32Cube/STM32CubeProgrammer/"
                              "STM32CubeProgrammer.app/Contents/MacOs/bin/STM32_Programmer_CLI")
        elif systemOS == "Windows":
            programmerPath = (r"C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin"
                              r"\STM32_Programmer_CLI.exe")
        else:  # Linux
            # Common Linux installation paths
            potential_paths = [
                "/usr/local/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI",
                "/opt/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI",
                os.path.expanduser("~/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI")
            ]
            programmerPath = None
            for path in potential_paths:
                if os.path.exists(path):
                    programmerPath = path
                    break
            if not programmerPath:
                self.stderrAvailable.emit("Error: STM32CubeProgrammer not found on Linux")
                self.finished.emit()
                return

        # Get firmware paths
        firmware_path = self.firmware_path
        config_path = get_firmware_path("config.bin")
        zeros_path = get_firmware_path("zeros_64k.bin")

        # Bail out early if the firmware file isn't actually on disk
        if not firmware_path or not os.path.isfile(firmware_path):
            self.stderrAvailable.emit(
                "Error: firmware file not found: {p}".format(p=firmware_path))
            self.finished.emit()
            return

        # Define the command to run STM32CubeProgrammer
        command = [
            programmerPath,
            "--connect", "port=SWD",  # Specify the port (e.g., USB, JTAG)
            "--download", firmware_path,  # Firmware file to write to the device
            "--verify",  # Verify after programming
        ]

        # Burn the firmware first
        try:
            # On Windows, hide console windows from subprocess calls
            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)

            # Do other work while the subprocess is running
            while process.poll() is None:
                # Retrieve output (if needed)
                stdout, stderr = process.communicate()

                if stdout:
                    cleanedText = re.sub(r'\x1b\[[0-9;]*[mG]', '', stdout)
                    self.stdoutAvailable.emit(cleanedText)

            if process.returncode == 0:
                firmwareBurnSuccessful = True
            else:
                self.stderrAvailable.emit(f"\nProgramming Failed with code {process.returncode}")


        except subprocess.CalledProcessError as e:
            # If there's an error, show the error message
            self.stderrAvailable.emit(f"/nError: {e.stderr}")
            self.stderrAvailable.emit(e.stdout)
        except Exception as e:
            self.stderrAvailable.emit(f"Unexpected error: {str(e)}")

        if firmwareBurnSuccessful:
            command = [
                programmerPath,
                "--connect", "port=SWD",  # Specify the port (e.g., USB, JTAG)
                "--download", config_path,  # Firmware file to write to the device
                "0x083FFC00",  # download address
            ]

            # Burn the configuration bytes
            try:
                # On Windows, hide console windows from subprocess calls
                startupinfo = None
                if platform.system() == "Windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                
                process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)

                # Do other work while the subprocess is running
                while process.poll() is None:
                    # Retrieve output (if needed)
                    stdout, stderr = process.communicate()

                    if stdout:
                        cleanedText = re.sub(r'\x1b\[[0-9;]*[mG]', '', stdout)
                        self.stdoutAvailable.emit(cleanedText)

                if process.returncode != 0:
                    self.stderrAvailable.emit(f"\nProgramming Failed with code {process.returncode}")

                else:
                    configBurnSuccessful = True;

            except subprocess.CalledProcessError as e:
                # If there's an error, show the error message
                self.stderrAvailable.emit(f"/nError: {e.stderr}")
                self.stderrAvailable.emit(e.stdout)
            except Exception as e:
                self.stdoutAvailable.emit(f"Unexpected error: {str(e)}")

        if configBurnSuccessful:
            command = [
                programmerPath,
                "--connect", "port=SWD",  # Specify the port (e.g., USB, JTAG)
                "--download", zeros_path,  # Firmware file to write to the device
                "0x200C0000",  # download address
            ]

            # Burn the configuration bytes
            try:
                # On Windows, hide console windows from subprocess calls
                startupinfo = None
                if platform.system() == "Windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                
                process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)

                # Do other work while the subprocess is running
                while process.poll() is None:
                    # Retrieve output (if needed)
                    stdout, stderr = process.communicate()

                    if stdout:
                        cleanedText = re.sub(r'\x1b\[[0-9;]*[mG]', '', stdout)
                        self.stdoutAvailable.emit(cleanedText)

                if process.returncode != 0:
                    self.stderrAvailable.emit(f"\nProgramming Failed with code {process.returncode}")

            except subprocess.CalledProcessError as e:
                # If there's an error, show the error message
                self.stderrAvailable.emit(f"/nError: {e.stderr}")
                self.stderrAvailable.emit(e.stdout)
            except Exception as e:
                self.stderrAvailable.emit(f"Unexpected error: {str(e)}")

        self.finished.emit()


class ProgrammerApp(QMainWindow):
    device_connected = False
    stlink_port = ""
    configFilePath = None

    def __init__(self, bypasss_firmware_update, firmware_updated, firmware_path=""):
        super().__init__()
        self.bypass_firmware_update = bypasss_firmware_update
        self.firmware_updated = firmware_updated
        # Path to the firmware file currently queued for flashing. Set either by
        # the initial download at startup or by the user clicking "Download".
        self.firmware_path = firmware_path
        self.configFilePath = get_firmware_path("config.bin")
        self.setupUi()

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(640, 880)
        self.centralwidget = QtWidgets.QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.ctFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.ctFrame.setGeometry(QtCore.QRect(10, 10, 301, 81))
        self.ctFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.ctFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.ctFrame.setObjectName("ctFrame")
        self.layoutWidget = QtWidgets.QWidget(parent=self.ctFrame)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 10, 281, 61))
        self.layoutWidget.setObjectName("layoutWidget")
        self.ctVertLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.ctVertLayout.setContentsMargins(0, 0, 0, 0)
        self.ctVertLayout.setObjectName("ctVertLayout")
        self.ctEnableButton = QtWidgets.QRadioButton(parent=self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.ctEnableButton.setFont(font)
        self.ctEnableButton.setAutoExclusive(False)
        self.ctEnableButton.setObjectName("ctEnableButton")
        self.ctVertLayout.addWidget(self.ctEnableButton)
        self.tempEnableButton = QtWidgets.QRadioButton(parent=self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.tempEnableButton.setFont(font)
        self.tempEnableButton.setAutoExclusive(False)
        self.tempEnableButton.setObjectName("tempEnableButton")
        self.ctVertLayout.addWidget(self.tempEnableButton)
        self.lightFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.lightFrame.setGeometry(QtCore.QRect(10, 100, 301, 131))
        self.lightFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.lightFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.lightFrame.setObjectName("lightFrame")
        self.layoutWidget1 = QtWidgets.QWidget(parent=self.lightFrame)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 11, 286, 115))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.lightVerticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.lightVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.lightVerticalLayout.setObjectName("lightVerticalLayout")
        self.lightEnableHorizLayout = QtWidgets.QHBoxLayout()
        self.lightEnableHorizLayout.setObjectName("lightEnableHorizLayout")
        self.lightEnableButton = QtWidgets.QRadioButton(parent=self.layoutWidget1)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lightEnableButton.setFont(font)
        self.lightEnableButton.setObjectName("lightEnableButton")
        self.lightEnableHorizLayout.addWidget(self.lightEnableButton)
        self.lightMatchGNSSCheckbox = QtWidgets.QCheckBox(parent=self.layoutWidget1)
        self.lightMatchGNSSCheckbox.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lightMatchGNSSCheckbox.setFont(font)
        self.lightMatchGNSSCheckbox.setObjectName("lightMatchGNSSCheckbox")
        self.lightEnableHorizLayout.addWidget(self.lightMatchGNSSCheckbox)
        self.lightVerticalLayout.addLayout(self.lightEnableHorizLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lightGainLabel = QtWidgets.QLabel(parent=self.layoutWidget1)
        self.lightGainLabel.setEnabled(False)
        self.lightGainLabel.setObjectName("lightGainLabel")
        self.horizontalLayout.addWidget(self.lightGainLabel)
        self.lightGainComboBox = QtWidgets.QComboBox(parent=self.layoutWidget1)
        self.lightGainComboBox.setEnabled(False)
        self.lightGainComboBox.setObjectName("lightGainComboBox")
        self.horizontalLayout.addWidget(self.lightGainComboBox)
        self.lightVerticalLayout.addLayout(self.horizontalLayout)
        self.lightSamplesHorizLayout = QtWidgets.QHBoxLayout()
        self.lightSamplesHorizLayout.setObjectName("lightSamplesHorizLayout")
        self.lightNumSamplesLabel = QtWidgets.QLabel(parent=self.layoutWidget1)
        self.lightNumSamplesLabel.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lightNumSamplesLabel.setFont(font)
        self.lightNumSamplesLabel.setObjectName("lightNumSamplesLabel")
        self.lightSamplesHorizLayout.addWidget(self.lightNumSamplesLabel)
        self.lightNumSamplesSpinBox = QtWidgets.QSpinBox(parent=self.layoutWidget1)
        self.lightNumSamplesSpinBox.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lightNumSamplesSpinBox.setFont(font)
        self.lightNumSamplesSpinBox.setMaximum(1800)
        self.lightNumSamplesSpinBox.setProperty("value", 512)
        self.lightNumSamplesSpinBox.setObjectName("lightNumSamplesSpinBox")
        self.lightSamplesHorizLayout.addWidget(self.lightNumSamplesSpinBox)
        self.lightVerticalLayout.addLayout(self.lightSamplesHorizLayout)
        self.iridiumFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.iridiumFrame.setGeometry(QtCore.QRect(10, 360, 301, 80))
        self.iridiumFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.iridiumFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.iridiumFrame.setObjectName("iridiumFrame")
        self.layoutWidget2 = QtWidgets.QWidget(parent=self.iridiumFrame)
        self.layoutWidget2.setGeometry(QtCore.QRect(10, 10, 281, 67))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.iridiumVertLayout = QtWidgets.QVBoxLayout(self.layoutWidget2)
        self.iridiumVertLayout.setContentsMargins(0, 0, 0, 0)
        self.iridiumVertLayout.setObjectName("iridiumVertLayout")
        self.iridiumTxTimeHorizLayout = QtWidgets.QHBoxLayout()
        self.iridiumTxTimeHorizLayout.setObjectName("iridiumTxTimeHorizLayout")
        self.iridiumTxTimeLabel = QtWidgets.QLabel(parent=self.layoutWidget2)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.iridiumTxTimeLabel.setFont(font)
        self.iridiumTxTimeLabel.setObjectName("iridiumTxTimeLabel")
        self.iridiumTxTimeHorizLayout.addWidget(self.iridiumTxTimeLabel)
        self.iridiumTxTimeSpinBox = QtWidgets.QSpinBox(parent=self.layoutWidget2)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.iridiumTxTimeSpinBox.setFont(font)
        self.iridiumTxTimeSpinBox.setMaximum(60)
        self.iridiumTxTimeSpinBox.setProperty("value", 5)
        self.iridiumTxTimeSpinBox.setObjectName("iridiumTxTimeSpinBox")
        self.iridiumTxTimeHorizLayout.addWidget(self.iridiumTxTimeSpinBox)
        self.iridiumVertLayout.addLayout(self.iridiumTxTimeHorizLayout)
        self.iridiumTypeHorizLayoutr = QtWidgets.QHBoxLayout()
        self.iridiumTypeHorizLayoutr.setObjectName("iridiumTypeHorizLayoutr")
        self.iridiumTypeComboBox = QtWidgets.QComboBox(parent=self.layoutWidget2)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.iridiumTypeComboBox.setFont(font)
        self.iridiumTypeComboBox.setObjectName("iridiumTypeComboBox")
        self.iridiumTypeHorizLayoutr.addWidget(self.iridiumTypeComboBox)
        self.iridiumTypeLabel = QtWidgets.QLabel(parent=self.layoutWidget2)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.iridiumTypeLabel.setFont(font)
        self.iridiumTypeLabel.setObjectName("iridiumTypeLabel")
        self.iridiumTypeHorizLayoutr.addWidget(self.iridiumTypeLabel)
        self.iridiumVertLayout.addLayout(self.iridiumTypeHorizLayoutr)
        self.gnssFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.gnssFrame.setGeometry(QtCore.QRect(10, 450, 301, 111))
        self.gnssFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.gnssFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.gnssFrame.setObjectName("gnssFrame")
        self.layoutWidget_11 = QtWidgets.QWidget(parent=self.gnssFrame)
        self.layoutWidget_11.setGeometry(QtCore.QRect(10, 10, 281, 90))
        self.layoutWidget_11.setObjectName("layoutWidget_11")
        self.gnssVertLayout = QtWidgets.QVBoxLayout(self.layoutWidget_11)
        self.gnssVertLayout.setContentsMargins(0, 0, 0, 0)
        self.gnssVertLayout.setObjectName("gnssVertLayout")
        self.gnssSamplesHorizLayout = QtWidgets.QHBoxLayout()
        self.gnssSamplesHorizLayout.setObjectName("gnssSamplesHorizLayout")
        self.gnssNumSamplesLabel = QtWidgets.QLabel(parent=self.layoutWidget_11)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.gnssNumSamplesLabel.setFont(font)
        self.gnssNumSamplesLabel.setObjectName("gnssNumSamplesLabel")
        self.gnssSamplesHorizLayout.addWidget(self.gnssNumSamplesLabel)
        self.gnssNumSamplesSpinBox = QtWidgets.QSpinBox(parent=self.layoutWidget_11)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.gnssNumSamplesSpinBox.setFont(font)
        self.gnssNumSamplesSpinBox.setMaximum(32768)
        self.gnssNumSamplesSpinBox.setProperty("value", 4096)
        self.gnssNumSamplesSpinBox.setObjectName("gnssNumSamplesSpinBox")
        self.gnssSamplesHorizLayout.addWidget(self.gnssNumSamplesSpinBox)
        self.gnssVertLayout.addLayout(self.gnssSamplesHorizLayout)
        self.gnssHighPerformanceModeCheckBox = QtWidgets.QCheckBox(parent=self.layoutWidget_11)
        self.gnssHighPerformanceModeCheckBox.setObjectName("gnssHighPerformanceModeCheckBox")
        self.gnssVertLayout.addWidget(self.gnssHighPerformanceModeCheckBox)
        self.gnssSampleRateHorizLayout = QtWidgets.QHBoxLayout()
        self.gnssSampleRateHorizLayout.setObjectName("gnssSampleRateHorizLayout")
        self.gnssSampleRateComboBox = QtWidgets.QComboBox(parent=self.layoutWidget_11)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.gnssSampleRateComboBox.setFont(font)
        self.gnssSampleRateComboBox.setObjectName("gnssSampleRateComboBox")
        self.gnssSampleRateHorizLayout.addWidget(self.gnssSampleRateComboBox)
        self.gnssSampleRateLabel = QtWidgets.QLabel(parent=self.layoutWidget_11)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.gnssSampleRateLabel.setFont(font)
        self.gnssSampleRateLabel.setObjectName("gnssSampleRateLabel")
        self.gnssSampleRateHorizLayout.addWidget(self.gnssSampleRateLabel)
        self.gnssVertLayout.addLayout(self.gnssSampleRateHorizLayout)
        self.timingFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.timingFrame.setGeometry(QtCore.QRect(330, 250, 291, 111))
        self.timingFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.timingFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.timingFrame.setObjectName("timingFrame")
        self.verticalLayoutWidget = QtWidgets.QWidget(parent=self.timingFrame)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 271, 91))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.timingVertLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.timingVertLayout.setContentsMargins(0, 0, 0, 0)
        self.timingVertLayout.setObjectName("timingVertLayout")
        self.dutyCycleHorizLayout = QtWidgets.QHBoxLayout()
        self.dutyCycleHorizLayout.setObjectName("dutyCycleHorizLayout")
        self.dutyCycleLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.dutyCycleLabel.setFont(font)
        self.dutyCycleLabel.setObjectName("dutyCycleLabel")
        self.dutyCycleHorizLayout.addWidget(self.dutyCycleLabel)
        self.dutyCycleSpinBox = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.dutyCycleSpinBox.setFont(font)
        self.dutyCycleSpinBox.setMaximum(1440)
        self.dutyCycleSpinBox.setProperty("value", 30)
        self.dutyCycleSpinBox.setObjectName("dutyCycleSpinBox")
        self.dutyCycleHorizLayout.addWidget(self.dutyCycleSpinBox)
        self.timingVertLayout.addLayout(self.dutyCycleHorizLayout)
        self.gnssBufferTimeHorizLayout = QtWidgets.QHBoxLayout()
        self.gnssBufferTimeHorizLayout.setObjectName("gnssBufferTimeHorizLayout")
        self.gnssMaxAcqusitionTimeLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.gnssMaxAcqusitionTimeLabel.setFont(font)
        self.gnssMaxAcqusitionTimeLabel.setWhatsThis("")
        self.gnssMaxAcqusitionTimeLabel.setObjectName("gnssMaxAcqusitionTimeLabel")
        self.gnssBufferTimeHorizLayout.addWidget(self.gnssMaxAcqusitionTimeLabel)
        self.gnssMaxAcquisitionTimeSpinBox = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.gnssMaxAcquisitionTimeSpinBox.setFont(font)
        self.gnssMaxAcquisitionTimeSpinBox.setWhatsThis("")
        self.gnssMaxAcquisitionTimeSpinBox.setMaximum(10)
        self.gnssMaxAcquisitionTimeSpinBox.setProperty("value", 5)
        self.gnssMaxAcquisitionTimeSpinBox.setObjectName("gnssMaxAcquisitionTimeSpinBox")
        self.gnssBufferTimeHorizLayout.addWidget(self.gnssMaxAcquisitionTimeSpinBox)
        self.timingVertLayout.addLayout(self.gnssBufferTimeHorizLayout)
        self.trackingNumberHorizLayourt = QtWidgets.QHBoxLayout()
        self.trackingNumberHorizLayourt.setObjectName("trackingNumberHorizLayourt")
        self.trackingNumberLabel = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.trackingNumberLabel.setFont(font)
        self.trackingNumberLabel.setObjectName("trackingNumberLabel")
        self.trackingNumberHorizLayourt.addWidget(self.trackingNumberLabel)
        self.trackingNumberSpinBox = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.trackingNumberSpinBox.setFont(font)
        self.trackingNumberSpinBox.setMaximum(1000)
        self.trackingNumberSpinBox.setProperty("value", 100)
        self.trackingNumberSpinBox.setObjectName("trackingNumberSpinBox")
        self.trackingNumberHorizLayourt.addWidget(self.trackingNumberSpinBox)
        self.timingVertLayout.addLayout(self.trackingNumberHorizLayourt)
        self.graphicsView = QtWidgets.QGraphicsView(parent=self.centralwidget)
        self.graphicsView.setGeometry(QtCore.QRect(320, 10, 311, 231))
        self.graphicsView.setObjectName("graphicsView")
        self.statusAndProgFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.statusAndProgFrame.setGeometry(QtCore.QRect(340, 370, 271, 191))
        self.statusAndProgFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.statusAndProgFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.statusAndProgFrame.setObjectName("statusAndProgFrame")
        self.layoutWidget3 = QtWidgets.QWidget(parent=self.statusAndProgFrame)
        self.layoutWidget3.setGeometry(QtCore.QRect(10, 10, 251, 171))
        self.layoutWidget3.setObjectName("layoutWidget3")
        self.statusAndProgVertLayout = QtWidgets.QVBoxLayout(self.layoutWidget3)
        self.statusAndProgVertLayout.setContentsMargins(0, 0, 0, 0)
        self.statusAndProgVertLayout.setObjectName("statusAndProgVertLayout")
        self.devicePortLabel = QtWidgets.QLabel(parent=self.layoutWidget3)
        self.devicePortLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.devicePortLabel.setObjectName("devicePortLabel")
        self.statusAndProgVertLayout.addWidget(self.devicePortLabel)
        self.verifyButton = QtWidgets.QPushButton(parent=self.layoutWidget3)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.verifyButton.setFont(font)
        self.verifyButton.setObjectName("verifyButton")
        self.statusAndProgVertLayout.addWidget(self.verifyButton)
        self.programButton = QtWidgets.QPushButton(parent=self.layoutWidget3)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.programButton.setFont(font)
        self.programButton.setObjectName("programButton")
        self.statusAndProgVertLayout.addWidget(self.programButton)
        self.downloadConfigFile = QtWidgets.QPushButton(parent=self.layoutWidget3)
        self.downloadConfigFile.setObjectName("downloadConfigFile")
        self.statusAndProgVertLayout.addWidget(self.downloadConfigFile)
        self.turbidityFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.turbidityFrame.setGeometry(QtCore.QRect(10, 240, 301, 111))
        self.turbidityFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.turbidityFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.turbidityFrame.setObjectName("turbidityFrame")
        self.layoutWidget_2 = QtWidgets.QWidget(parent=self.turbidityFrame)
        self.layoutWidget_2.setGeometry(QtCore.QRect(10, 11, 281, 94))
        self.layoutWidget_2.setObjectName("layoutWidget_2")
        self.turbidityVerticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget_2)
        self.turbidityVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.turbidityVerticalLayout.setObjectName("turbidityVerticalLayout")
        self.turbidityEnableHorizLayout = QtWidgets.QHBoxLayout()
        self.turbidityEnableHorizLayout.setObjectName("turbidityEnableHorizLayout")
        self.turbidityEnableButton = QtWidgets.QRadioButton(parent=self.layoutWidget_2)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.turbidityEnableButton.setFont(font)
        self.turbidityEnableButton.setObjectName("turbidityEnableButton")
        self.turbidityEnableHorizLayout.addWidget(self.turbidityEnableButton)
        self.turbidityMatchGNSSCheckbox = QtWidgets.QCheckBox(parent=self.layoutWidget_2)
        self.turbidityMatchGNSSCheckbox.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.turbidityMatchGNSSCheckbox.setFont(font)
        self.turbidityMatchGNSSCheckbox.setObjectName("turbidityMatchGNSSCheckbox")
        self.turbidityEnableHorizLayout.addWidget(self.turbidityMatchGNSSCheckbox)
        self.turbidityVerticalLayout.addLayout(self.turbidityEnableHorizLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.turbiditySerialNumberLabel = QtWidgets.QLabel(parent=self.layoutWidget_2)
        self.turbiditySerialNumberLabel.setEnabled(False)
        self.turbiditySerialNumberLabel.setObjectName("turbiditySerialNumberLabel")
        self.horizontalLayout_2.addWidget(self.turbiditySerialNumberLabel)
        self.turbiditySerialNumberSpinBox = QtWidgets.QSpinBox(parent=self.layoutWidget_2)
        self.turbiditySerialNumberSpinBox.setEnabled(False)
        self.turbiditySerialNumberSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.turbiditySerialNumberSpinBox.setMaximum(65535)
        self.turbiditySerialNumberSpinBox.setObjectName("turbiditySerialNumberSpinBox")
        self.horizontalLayout_2.addWidget(self.turbiditySerialNumberSpinBox)
        self.turbidityVerticalLayout.addLayout(self.horizontalLayout_2)
        self.turbiditySamplesHorizLayout = QtWidgets.QHBoxLayout()
        self.turbiditySamplesHorizLayout.setObjectName("turbiditySamplesHorizLayout")
        self.turbidityNumSamplesLabel = QtWidgets.QLabel(parent=self.layoutWidget_2)
        self.turbidityNumSamplesLabel.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.turbidityNumSamplesLabel.setFont(font)
        self.turbidityNumSamplesLabel.setObjectName("turbidityNumSamplesLabel")
        self.turbiditySamplesHorizLayout.addWidget(self.turbidityNumSamplesLabel)
        self.turbidityNumSamplesSpinBox = QtWidgets.QSpinBox(parent=self.layoutWidget_2)
        self.turbidityNumSamplesSpinBox.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.turbidityNumSamplesSpinBox.setFont(font)
        self.turbidityNumSamplesSpinBox.setMaximum(3600)
        self.turbidityNumSamplesSpinBox.setProperty("value", 1024)
        self.turbidityNumSamplesSpinBox.setObjectName("turbidityNumSamplesSpinBox")
        self.turbiditySamplesHorizLayout.addWidget(self.turbidityNumSamplesSpinBox)
        self.turbidityVerticalLayout.addLayout(self.turbiditySamplesHorizLayout)

        # --- Firmware URL input panel ---
        self.firmwareUrlFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.firmwareUrlFrame.setGeometry(QtCore.QRect(10, 570, 621, 75))
        self.firmwareUrlFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.firmwareUrlFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.firmwareUrlFrame.setObjectName("firmwareUrlFrame")

        self.firmwareUrlVertLayoutWidget = QtWidgets.QWidget(parent=self.firmwareUrlFrame)
        self.firmwareUrlVertLayoutWidget.setGeometry(QtCore.QRect(8, 5, 605, 65))
        self.firmwareUrlVertLayout = QtWidgets.QVBoxLayout(self.firmwareUrlVertLayoutWidget)
        self.firmwareUrlVertLayout.setContentsMargins(0, 0, 0, 0)
        self.firmwareUrlVertLayout.setSpacing(2)

        # Row 1: URL entry + buttons
        self.firmwareUrlRow = QtWidgets.QHBoxLayout()
        self.firmwareUrlLabel = QtWidgets.QLabel(parent=self.firmwareUrlVertLayoutWidget)
        self.firmwareUrlLabel.setObjectName("firmwareUrlLabel")
        self.firmwareUrlRow.addWidget(self.firmwareUrlLabel)

        self.firmwareUrlLineEdit = QtWidgets.QLineEdit(parent=self.firmwareUrlVertLayoutWidget)
        self.firmwareUrlLineEdit.setObjectName("firmwareUrlLineEdit")
        self.firmwareUrlLineEdit.setText(DEFAULT_FIRMWARE_URL)
        self.firmwareUrlLineEdit.setClearButtonEnabled(True)
        self.firmwareUrlRow.addWidget(self.firmwareUrlLineEdit, stretch=1)

        self.useUrlButton = QtWidgets.QPushButton(parent=self.firmwareUrlVertLayoutWidget)
        self.useUrlButton.setObjectName("useUrlButton")
        self.firmwareUrlRow.addWidget(self.useUrlButton)

        self.resetUrlButton = QtWidgets.QPushButton(parent=self.firmwareUrlVertLayoutWidget)
        self.resetUrlButton.setObjectName("resetUrlButton")
        self.firmwareUrlRow.addWidget(self.resetUrlButton)

        self.firmwareUrlVertLayout.addLayout(self.firmwareUrlRow)

        # Row 2: active firmware file display (always shows what will be flashed)
        self.activeFirmwareLabel = QtWidgets.QLabel(parent=self.firmwareUrlVertLayoutWidget)
        self.activeFirmwareLabel.setObjectName("activeFirmwareLabel")
        self.activeFirmwareLabel.setWordWrap(True)
        self.activeFirmwareLabel.setStyleSheet("font-size: 11px;")
        self.firmwareUrlVertLayout.addWidget(self.activeFirmwareLabel)

        self.statusTextEdit = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.statusTextEdit.setGeometry(QtCore.QRect(10, 650, 621, 221))
        self.statusTextEdit.setObjectName("statusTextEdit")
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.finishSetup()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "microSWIFT Configurator Version "
                                                           "{major}.{minor}".format(major=PROGRAMMER_MAJOR_VERSION,
                                                                                    minor=PROGRAMMER_MINOR_VERSION)))
        self.ctEnableButton.setText(_translate("MainWindow", "Enable CT"))
        self.tempEnableButton.setText(_translate("MainWindow", "Enable Temperature"))
        self.lightEnableButton.setText(_translate("MainWindow", "Enable Light"))
        self.lightMatchGNSSCheckbox.setText(_translate("MainWindow", "Match GNSS period"))
        self.lightGainLabel.setText(_translate("MainWindow", "Gain"))
        self.lightNumSamplesLabel.setText(_translate("MainWindow", "Number of samples @ 0.5Hz"))
        self.iridiumTxTimeLabel.setText(_translate("MainWindow", "Iridium transmit time in mins"))
        self.iridiumTypeLabel.setText(_translate("MainWindow", "Iridium Modem Type"))
        self.gnssNumSamplesLabel.setText(_translate("MainWindow", "Number of GNSS samples"))
        self.gnssHighPerformanceModeCheckBox.setText(_translate("MainWindow", "Enable GNSS high performance mode"))
        self.gnssSampleRateLabel.setText(_translate("MainWindow", "GNSS Sampling Rate"))
        self.dutyCycleLabel.setText(_translate("MainWindow", "Total Duty Cycle (mins)"))
        self.gnssMaxAcqusitionTimeLabel.setText(_translate("MainWindow", "GNSS max time to fix (mins)"))
        self.trackingNumberLabel.setText(_translate("MainWindow", "microSWIFT Tracking number"))
        self.devicePortLabel.setText(_translate("MainWindow", "No Device Connected"))
        self.verifyButton.setText(_translate("MainWindow", "Verify"))
        self.programButton.setText(_translate("MainWindow", "Program"))
        self.downloadConfigFile.setText(_translate("MainWindow", "Download Config"))
        self.turbidityEnableButton.setText(_translate("MainWindow", "Enable Turbidity"))
        self.turbidityMatchGNSSCheckbox.setText(_translate("MainWindow", "Match GNSS period"))
        self.turbiditySerialNumberLabel.setText(_translate("MainWindow", "Serial Number"))
        self.turbidityNumSamplesLabel.setText(_translate("MainWindow", "Number of samples @ 1Hz"))
        self.firmwareUrlLabel.setText(_translate("MainWindow", "Firmware URL:"))
        self.useUrlButton.setText(_translate("MainWindow", "Download"))
        self.resetUrlButton.setText(_translate("MainWindow", "Reset to default"))
        self.activeFirmwareLabel.setText(
            _translate("MainWindow", "Active firmware: (none — download a file to continue)"))

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
        # Added functionality
        self.worker = Worker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.scene = QGraphicsScene()

        self.disableAllOptionalSensors()
        self.connectUIElements()
        self.fillComboBoxes()
        self.find_usb_port()
        self.displayPicture()

        self.lightGainComboBox.setCurrentIndex(2)

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

        if self.bypass_firmware_update:
            self.appendText("Firmware update bypassed.")
        elif self.firmware_updated:
            self.appendText("Firmware successfully updated from GitHub.")
        else:
            self.appendError("Unable to pull firmware from GitHub!")

        # Initialize the "active firmware file" display and Worker path based
        # on what actually exists on disk after startup.
        self.updateActiveFirmwareDisplay()

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
        get_int_from_str = lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else None
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

                      const char compile_date_flash[11];
                      const char compile_time_flash[9];
                    } microSWIFT_configuration;

                    In microSWIFT.ld:

                      /* Custom variables (firmware version, compile date/time, etc) */
                      .uservars :
                      {
                        /* Variables contained in type microSWIFT_configuration contained in configuration.h */
                        KEEP(*(.uservars.CONFIGURATION))
                        *(.uservars*);
                      } > USERVARS
                    '''

        current_datetime = datetime.now()

        # Format the date and time strings
        date = current_datetime.strftime("%m/%d/%Y")  # MM/DD/YYYY
        time = current_datetime.strftime("%H:%M:%S")  # HH:MM:SS
        date += "\x00"  # null terminated
        time += "\x00"  # null terminated

        v3f = self.iridiumTypeComboBox.currentText() == "V3F"

        configStruct = struct.pack("<LLLLLLLLLH??????11s9s",
                                   int(self.trackingNumberSpinBox.value()),
                                   int(self.gnssNumSamplesSpinBox.value()),
                                   int(self.dutyCycleSpinBox.value()),
                                   int(self.iridiumTxTimeSpinBox.value()),
                                   int(self.gnssMaxAcquisitionTimeSpinBox.value()),
                                   get_int_from_str(self.gnssSampleRateComboBox.currentText()),
                                   int(self.lightNumSamplesSpinBox.value()),
                                   int(self.lightGainComboBox.currentIndex()),
                                   int(self.turbidityNumSamplesSpinBox.value()),
                                   int(self.turbiditySerialNumberSpinBox.value()),
                                   bool(self.iridiumTypeComboBox.currentText() == "V3F"),
                                   bool(self.gnssHighPerformanceModeCheckBox.isChecked()),
                                   bool(self.ctEnableButton.isChecked()),
                                   bool(self.tempEnableButton.isChecked()),
                                   bool(self.lightEnableButton.isChecked()),
                                   bool(self.turbidityEnableButton.isChecked()),
                                   bytes(date.encode("utf-8")),
                                   bytes(time.encode("utf-8"))
                                   )

        num_bytes = len(configStruct)

        return configStruct
    def assembleBinaryConfigFile(self):
        with open(self.configFilePath, "wb") as configFile:
            configFile.write(self.assembleBinaryConfigStruct())

    def fillComboBoxes(self):
        # Iridium type drop box
        self.iridiumTypeComboBox.addItem("V3D")
        self.iridiumTypeComboBox.addItem("V3F")

        # GNSS sampling ratre drop box
        self.gnssSampleRateComboBox.addItem("4 Hz")
        self.gnssSampleRateComboBox.addItem("5 Hz")

        self.lightGainComboBox.addItem("0.5x")
        self.lightGainComboBox.addItem("1x")
        self.lightGainComboBox.addItem("2x")
        self.lightGainComboBox.addItem("4x")
        self.lightGainComboBox.addItem("8x")
        self.lightGainComboBox.addItem("16x")
        self.lightGainComboBox.addItem("32x")
        self.lightGainComboBox.addItem("64x")
        self.lightGainComboBox.addItem("128x")
        self.lightGainComboBox.addItem("256x")
        self.lightGainComboBox.addItem("512x")

    def disableAllOptionalSensors(self):
        self.lightNumSamplesLabel.setDisabled(True)
        self.lightNumSamplesSpinBox.setDisabled(True)

        self.turbidityNumSamplesLabel.setDisabled(True)
        self.turbidityNumSamplesSpinBox.setDisabled(True)

        self.programButton.setDisabled(True)
        self.downloadConfigFile.setDisabled(True)

    def connectUIElements(self):
        self.worker.stdoutAvailable.connect(self.appendText)
        self.worker.stderrAvailable.connect(self.appendError)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.reenableGUI)
        self.worker.finished.connect(self.threadFinished)

        self.ctEnableButton.clicked.connect(self.onCtEnabledClick)
        self.tempEnableButton.clicked.connect(self.onTempEnabledClick)
        self.lightEnableButton.clicked.connect(self.onLightEnabledClick)
        self.turbidityEnableButton.clicked.connect(self.onTurbidityEnabledClick)
        self.lightMatchGNSSCheckbox.clicked.connect(self.onLightMatchGnssClicked)
        self.turbidityMatchGNSSCheckbox.clicked.connect(self.onTurbidityMatchGnssClicked)

        self.verifyButton.clicked.connect(self.verifySettings)
        self.programButton.clicked.connect(self.programDevice)
        self.downloadConfigFile.clicked.connect(self.saveConfigAsFile)

        # Firmware URL buttons
        self.useUrlButton.clicked.connect(self.onUseUrlClicked)
        self.resetUrlButton.clicked.connect(self.onResetUrlClicked)
        self.firmwareUrlLineEdit.returnPressed.connect(self.onUseUrlClicked)

        self.lightNumSamplesSpinBox.valueChanged.connect(self.resetVerifyButton)
        self.lightGainComboBox.currentIndexChanged.connect(self.resetVerifyButton)
        self.turbidityNumSamplesSpinBox.valueChanged.connect(self.resetVerifyButton)
        self.iridiumTxTimeSpinBox.valueChanged.connect(self.resetVerifyButton)
        self.gnssNumSamplesSpinBox.valueChanged.connect(self.resetVerifyButton)
        self.gnssNumSamplesSpinBox.valueChanged.connect(self.onLightMatchGnssClicked)
        self.gnssNumSamplesSpinBox.valueChanged.connect(self.onTurbidityMatchGnssClicked)
        self.gnssSampleRateComboBox.currentIndexChanged.connect(self.onLightMatchGnssClicked)
        self.gnssSampleRateComboBox.currentIndexChanged.connect(self.onTurbidityMatchGnssClicked)
        self.dutyCycleSpinBox.valueChanged.connect(self.resetVerifyButton)
        self.gnssMaxAcquisitionTimeSpinBox.valueChanged.connect(self.resetVerifyButton)
        self.trackingNumberSpinBox.valueChanged.connect(self.resetVerifyButton)

        self.iridiumTypeComboBox.currentIndexChanged.connect(self.resetVerifyButton)
        self.gnssSampleRateComboBox.currentIndexChanged.connect(self.resetVerifyButton)

    def onCtEnabledClick(self):
        if self.ctEnableButton.isChecked():
            self.tempEnableButton.setChecked(False)

        self.resetVerifyButton()

    def onTempEnabledClick(self):
        if self.tempEnableButton.isChecked():
            self.ctEnableButton.setChecked(False)

        self.resetVerifyButton()

    def onLightEnabledClick(self):
        if self.lightEnableButton.isChecked():
            self.lightNumSamplesLabel.setEnabled(True)
            self.lightNumSamplesSpinBox.setEnabled(True)
            self.lightMatchGNSSCheckbox.setEnabled(True)
            self.lightGainLabel.setEnabled(True)
            self.lightGainComboBox.setEnabled(True)
        else:
            self.lightNumSamplesLabel.setDisabled(True)
            self.lightNumSamplesSpinBox.setDisabled(True)
            self.lightMatchGNSSCheckbox.setDisabled(True)
            self.lightGainLabel.setDisabled(True)
            self.lightGainComboBox.setDisabled(True)

        self.resetVerifyButton()

    def onLightMatchGnssClicked(self):
        get_int_from_str = lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else None
        if self.lightMatchGNSSCheckbox.isChecked():
            self.lightNumSamplesSpinBox.setDisabled(True)
            self.lightNumSamplesSpinBox.setValue(int((self.gnssNumSamplesSpinBox.value() /
                                                      get_int_from_str(self.gnssSampleRateComboBox.currentText()) / 2)))
        elif self.lightEnableButton.isChecked():
            self.lightNumSamplesSpinBox.setEnabled(True)

        self.resetVerifyButton()

    def onTurbidityEnabledClick(self):
        if self.turbidityEnableButton.isChecked():
            self.turbidityNumSamplesLabel.setEnabled(True)
            self.turbidityNumSamplesSpinBox.setEnabled(True)
            self.turbidityMatchGNSSCheckbox.setEnabled(True)
            self.turbiditySerialNumberLabel.setEnabled(True)
            self.turbiditySerialNumberSpinBox.setEnabled(True)
        else:
            self.turbidityNumSamplesLabel.setDisabled(True)
            self.turbidityNumSamplesSpinBox.setDisabled(True)
            self.turbidityMatchGNSSCheckbox.setDisabled(True)
            self.turbiditySerialNumberLabel.setDisabled(True)
            self.turbiditySerialNumberSpinBox.setDisabled(True)

        self.resetVerifyButton()

    def onTurbidityMatchGnssClicked(self):
        get_int_from_str = lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else None
        if self.turbidityMatchGNSSCheckbox.isChecked():
            self.turbidityNumSamplesSpinBox.setDisabled(True)
            self.turbidityNumSamplesSpinBox.setValue(int(self.gnssNumSamplesSpinBox.value() /
                                                         get_int_from_str(self.gnssSampleRateComboBox.currentText())))
        elif self.turbidityEnableButton.isChecked():
            self.turbidityNumSamplesSpinBox.setEnabled(True)

        self.resetVerifyButton()

    def find_usb_port(self):

        # List all available serial ports
        ports = serial.tools.list_ports.comports()

        stlink_ports = []
        
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

        for port in ports:
            # Method 1: Check if the port description contains STLINK (works on macOS/Linux)
            if "STLINK" in port.description.upper() or "ST-LINK" in port.description.upper():
                stlink_ports.append(port.device)
                break
                
        # Method 2: If no STLINK found by description, check by VID/PID (works on Windows)
        if not stlink_ports:
            for port in ports:
                # Check VID/PID attributes (most reliable method)
                if (hasattr(port, 'vid') and hasattr(port, 'pid') and 
                    port.vid == STMICRO_VID and port.pid in STLINK_PIDS):
                    stlink_ports.append(port.device)
                    break

        if stlink_ports:
            for device in stlink_ports:
                # Determine which ST-Link model was detected
                stlink_model = "ST-Link"
                for port in ports:
                    if port.device == device:
                        if hasattr(port, 'pid') and port.pid in STLINK_PIDS:
                            stlink_model = STLINK_PIDS[port.pid]
                        break
                
                # Keep status color for visibility
                self.devicePortLabel.setStyleSheet("font-size: 14px; color: green; font-weight: bold;")
                self.devicePortLabel.setText(f"{stlink_model} found on port {device}")
                self.device_connected = True
                self.stlink_port = device
                break
        else:
            # Keep status color for visibility
            self.devicePortLabel.setStyleSheet("font-size: 14px; color: red; font-weight: bold;")
            self.devicePortLabel.setText("STLink V3 not found on any USB port.")
            self.device_connected = False
            self.stlink_port = ""

        self.devicePortLabel.setWordWrap(True)

    def verifySettings(self):
        # For getting GNSS sample rate from drop down box
        get_int_from_str = lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else None

        settings_invalid = False
        verify_strings = []

        # Pull all the values from the UI
        light_enabled = self.lightEnableButton.isChecked()
        light_num_samples = self.lightNumSamplesSpinBox.value()
        turbidity_enabled = self.turbidityEnableButton.isChecked()
        turbidity_num_samples = self.turbidityNumSamplesSpinBox.value()
        iridium_tx_time = self.iridiumTxTimeSpinBox.value()
        num_gnss_samples = self.gnssNumSamplesSpinBox.value()
        gnss_sample_rate = get_int_from_str(self.gnssSampleRateComboBox.currentText())
        duty_cycle = self.dutyCycleSpinBox.value()
        gnss_window_buffer = self.gnssMaxAcquisitionTimeSpinBox.value()

        gnss_duration = (((num_gnss_samples / gnss_sample_rate) / 60) + 1) + gnss_window_buffer

        if (duty_cycle - gnss_duration - iridium_tx_time) < 0:
            verify_strings.append("Duty cycle not long enough to complete GNSS sample window.\n")
            settings_invalid = True

        if light_enabled:
            if ((duty_cycle - ((light_num_samples / 30) + 1) - iridium_tx_time) < 0):
                verify_strings.append("Duty cycle not long enough to complete Light sample window.\n")
                settings_invalid = True
            if (int((self.gnssNumSamplesSpinBox.value() / get_int_from_str(self.gnssSampleRateComboBox.currentText())
                     / 2)) > 1800):
                verify_strings.append("Max number of light samples is 1800.\n")
                settings_invalid = True

        if turbidity_enabled:
            if ((duty_cycle - ((turbidity_num_samples / 60) + 1) - iridium_tx_time) < 0):
                verify_strings.append("Duty cycle not long enough to complete Turbidity sample window.\n")
                settings_invalid = True
            if (int(self.gnssNumSamplesSpinBox.value() / get_int_from_str(self.gnssSampleRateComboBox.currentText()))
                    > 3600):
                verify_strings.append("Max number of turbidity samples is 3600.\n")
                settings_invalid = True

        if settings_invalid:
            self.programButton.setDisabled(True)
            self.downloadConfigFile.setDisabled(True)
            # Use a more subtle approach with text instead of background colors
            self.verifyButton.setText("❌ Verify - Settings Invalid")
            self.verifyButton.setStyleSheet("font-size: 16px; font-weight: bold;")

            write_string = "".join(verify_strings)

            self.writeError(write_string)
        else:
            self.programButton.setEnabled(True)
            self.downloadConfigFile.setEnabled(True)
            # Use a more subtle approach with text instead of background colors
            self.verifyButton.setText("✅ Verify - Settings Valid")
            self.verifyButton.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.writeText("Settings verified. You did a great job.")

    def resetVerifyButton(self):
        self.programButton.setDisabled(True)
        self.downloadConfigFile.setDisabled(True)
        # Reset button text to default
        self.verifyButton.setText("Verify")
        self.verifyButton.setStyleSheet("font-size: 16px;")
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
        """Refresh the 'Active firmware' label and gate the Program button on it.

        The Program button should only be usable if we actually have a firmware
        file on disk to flash.
        """
        path = self.firmware_path
        if path and os.path.isfile(path):
            size_kb = os.path.getsize(path) / 1024.0
            self.activeFirmwareLabel.setText(
                "Active firmware: {p}  ({kb:.1f} KB)".format(p=path, kb=size_kb))
            self.activeFirmwareLabel.setStyleSheet(
                "font-size: 11px; color: #0a7a2a;")
            # Hand the path to the worker so the next Program click uses it
            self.worker.setFirmwarePath(path)
        else:
            self.activeFirmwareLabel.setText(
                "Active firmware: (none — download a file to continue)")
            self.activeFirmwareLabel.setStyleSheet(
                "font-size: 11px; color: #a00;")
            # No firmware on disk: force-disable the Program button regardless
            # of whether settings have been verified.
            self.programButton.setDisabled(True)

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

        self.find_usb_port()

        if not self.device_connected:
            self.writeError("STLink programmer not detected.")
            return

        # Double-check we have a firmware file to flash — it could have been
        # deleted between download and program click.
        if not self.firmware_path or not os.path.isfile(self.firmware_path):
            self.writeError("No firmware file is loaded. Download one first.")
            self.updateActiveFirmwareDisplay()
            return

        self.assembleBinaryConfigFile()

        # Hand the current firmware path to the worker, then kick off the run
        self.worker.setFirmwarePath(self.firmware_path)

        self.writeText(
            "Running STM32 Programmer CLI, please wait.\n"
            "Flashing firmware: {p}".format(p=self.firmware_path))

        self.disableGUI()
        # Run the worker thread so the program will be non-blocking
        self.thread.start()

    def disableGUI(self):
        self.ctEnableButton.setDisabled(True)
        self.tempEnableButton.setDisabled(True)
        self.lightEnableButton.setDisabled(True)
        self.lightMatchGNSSCheckbox.setDisabled(True)
        self.lightNumSamplesSpinBox.setDisabled(True)
        self.turbidityEnableButton.setDisabled(True)
        self.turbidityMatchGNSSCheckbox.setDisabled(True)
        self.turbidityNumSamplesSpinBox.setDisabled(True)
        self.iridiumTxTimeSpinBox.setDisabled(True)
        self.iridiumTypeComboBox.setDisabled(True)
        self.gnssNumSamplesSpinBox.setDisabled(True)
        self.gnssHighPerformanceModeCheckBox.setDisabled(True)
        self.gnssSampleRateComboBox.setDisabled(True)
        self.dutyCycleSpinBox.setDisabled(True)
        self.gnssMaxAcquisitionTimeSpinBox.setDisabled(True)
        self.trackingNumberSpinBox.setDisabled(True)
        self.verifyButton.setDisabled(True)
        self.programButton.setDisabled(True)
        self.downloadConfigFile.setDisabled(True)
        # Lock URL controls while flashing so the firmware path can't change mid-run
        self.firmwareUrlLineEdit.setDisabled(True)
        self.useUrlButton.setDisabled(True)
        self.resetUrlButton.setDisabled(True)

    def reenableGUI(self):
        self.ctEnableButton.setEnabled(True)

        self.tempEnableButton.setEnabled(True)

        self.lightEnableButton.setEnabled(True)
        if self.lightEnableButton.isChecked():
            self.lightMatchGNSSCheckbox.setEnabled(True)
            self.lightNumSamplesSpinBox.setEnabled(True)

        self.turbidityEnableButton.setEnabled(True)
        if self.turbidityEnableButton.isChecked():
            self.turbidityMatchGNSSCheckbox.setEnabled(True)
            self.turbidityNumSamplesSpinBox.setEnabled(True)

        self.iridiumTxTimeSpinBox.setEnabled(True)
        self.iridiumTypeComboBox.setEnabled(True)
        self.gnssNumSamplesSpinBox.setEnabled(True)
        self.gnssHighPerformanceModeCheckBox.setEnabled(True)
        self.gnssSampleRateComboBox.setEnabled(True)
        self.dutyCycleSpinBox.setEnabled(True)
        self.gnssMaxAcquisitionTimeSpinBox.setEnabled(True)
        self.trackingNumberSpinBox.setEnabled(True)
        self.verifyButton.setEnabled(True)
        self.programButton.setEnabled(True)
        self.downloadConfigFile.setEnabled(True)
        # Unlock URL controls after flashing completes
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
        # os.remove(self.configFilePath)


def main():
    firmware_updated = False
    firmware_path = ""

    parser = argparse.ArgumentParser()

    parser.add_argument('--no_firmware_update', action='store_true',
                        help='Disable automatic firmware download')

    args = parser.parse_args()

    if not args.no_firmware_update:
        firmware_updated, firmware_path, _err = download_microSWIFT_firmware()

    # If the startup download was skipped or failed, fall back to whatever is
    # already on disk at the default location (if anything).
    if not firmware_path:
        candidate = get_firmware_path("microSWIFT_V2.2.elf")
        if os.path.isfile(candidate):
            firmware_path = candidate

    app = QtWidgets.QApplication(sys.argv)

    programmer = ProgrammerApp(args.no_firmware_update, firmware_updated, firmware_path)
    programmer.show()
    sys.exit(app.exec())





if __name__ == "__main__":
    main()


