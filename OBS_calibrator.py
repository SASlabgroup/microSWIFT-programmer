import statistics
import sys
import os
import time
import board
import adafruit_vcnl4010

import usb.core
import numpy as np

from PyQt6 import QtCore
from PyQt6.QtCore import QSize, QRect, Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QAction, QFontDatabase
from PyQt6.QtWidgets import QMainWindow, QDialog, QVBoxLayout, QLabel, QApplication, QPushButton, QWidget, QFrame, \
    QSizePolicy, QDoubleSpinBox, QTextEdit, QAbstractSpinBox, QMenuBar, QMenu, QStatusBar

CALIBRATOR_MAJOR_VERSION = 1
CALIBRATOR_MINOR_VERSION = 0
NUMBER_OF_SAMPLES = 30


class SensorThread(QThread):
    proximity_read = pyqtSignal(int)
    finished = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self) -> None:
        i2c = board.I2C()
        sensor = adafruit_vcnl4010.VCNL4010(i2c)
        i = 0
        samples = []
        self._running = True

        while self._running:
            # Read the sensor
            proximity = sensor.proximity
            samples.append(proximity)
            self.proximity_read.emit(proximity)
            i += 1

            if i < NUMBER_OF_SAMPLES:
                time.sleep(0.999)
            else:
                break


        if (self._running):
            mean = statistics.mean(samples)
            stdev = statistics.stdev(samples)

            self.finished.emit(mean, stdev)

    def stop(self) -> None:
        self._running = False




class HelpPopUpWindow(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("How does this thing even work??")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(
            """This tool is used for calibrating Optical BackScatter (OBS) turbidity sensors. The calibration 
procedure involves a 4-point calibration using 100, 250, 500, and 1000 NTU concentrations of 
Formazin solution. The solutions must be well-mixed during sampling to ensure proper suspension. A
mixing plate is the recommended tool for maintaining a well-mixed solution.

For each solution, 30 samples are taken at 1Hz data rate. The samples are averaged and when all
concentrations have been sampled, a best-fit line equation will be produced. Concentrations can be
sampled in any order, but the best-fit equation requires that all concentrations be sampled prior
to producing an equation.

Solution sampling:

Place the sensor head into the well-mixed solution, maintianing the sensor head view clear of
obstructions and 10-15cm from the bottom of the container.

Click the start button which corresponds to the solution concentration and wait for the sampling to
complete (30 seconds).

	If the sample series standard deviation is greater than 1% of the average value, the stdev
	value field will turn red and be considered invalid. If this occurs, press the reset button
	for the given solution value and re-run the sampling by pressing the start button.

After sampling all solutions and obtaining valid average results, press the "Find Equation" button 
to produce a polynomial best-fit line equation."""))
        self.setLayout(layout)




class OBSCalibratorApp(QMainWindow):
    ongoingSampling = 0

    ntu100Complete = False
    ntu250Complete = False
    ntu500Complete = False
    ntu1000Complete = False

    def __init__(self):
        super().__init__()
        self.setupUi()
        self.finishSetup()

    def setupUi(self) -> None:
        font_id = QFontDatabase.addApplicationFont("/Users/philbush/STM32CubeIDE/microSWIFT/microSWIFT-programmer/PT_Mono.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        custom_font11 = QFont(font_family, 11)
        custom_font12 = QFont(font_family, 12)

        self.setObjectName(u"MainWindow")
        self.resize(475, 745)
        self.setMinimumSize(QSize(475, 745))
        self.setMaximumSize(QSize(475, 745))

        self.setFont(custom_font12)
        self.actionReset = QAction(self)
        self.actionReset.setObjectName(u"actionReset")
        self.actionHow_To_UseThisTool = QAction(self)
        self.actionHow_To_UseThisTool.setObjectName(u"actionHow_To_UseThisTool")
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName(u"centralwidget")
        self.ntu100Frame = QFrame(self.centralwidget)
        self.ntu100Frame.setObjectName(u"ntu100Frame")
        self.ntu100Frame.setGeometry(QRect(5, 5, 111, 641))
        self.ntu100Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.ntu100Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.ntu100Label = QLabel(self.ntu100Frame)
        self.ntu100Label.setObjectName(u"ntu100Label")
        self.ntu100Label.setGeometry(QRect(0, 0, 111, 20))
        self.ntu100Label.setFont(custom_font12)
        self.ntu100Label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu100StartButton = QPushButton(self.ntu100Frame)
        self.ntu100StartButton.setObjectName(u"ntu100StartButton")
        self.ntu100StartButton.setGeometry(QRect(0, 15, 111, 32))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ntu100StartButton.sizePolicy().hasHeightForWidth())
        self.ntu100StartButton.setSizePolicy(sizePolicy)
        self.ntu100StartButton.setMinimumSize(QSize(111, 32))
        self.ntu100StartButton.setMaximumSize(QSize(111, 32))
        self.ntu100StartButton.setStyleSheet(u"")
        self.ntu100ResetButton = QPushButton(self.ntu100Frame)
        self.ntu100ResetButton.setObjectName(u"ntu100ResetButton")
        self.ntu100ResetButton.setGeometry(QRect(0, 40, 111, 32))
        self.ntu100AverageLabel = QLabel(self.ntu100Frame)
        self.ntu100AverageLabel.setObjectName(u"ntu100AverageLabel")
        self.ntu100AverageLabel.setGeometry(QRect(0, 65, 111, 21))
        self.ntu100AverageLabel.setFont(custom_font12)
        self.ntu100AverageLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu100AverageSpinBox = QDoubleSpinBox(self.ntu100Frame)
        self.ntu100AverageSpinBox.setObjectName(u"ntu100AverageSpinBox")
        self.ntu100AverageSpinBox.setGeometry(QRect(0, 85, 111, 21))
        self.ntu100AverageSpinBox.setReadOnly(True)
        self.ntu100AverageSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu100AverageSpinBox.setMaximum(65536.000000000000000)
        self.ntu100TextEdit = QTextEdit(self.ntu100Frame)
        self.ntu100TextEdit.setObjectName(u"ntu100TextEdit")
        self.ntu100TextEdit.setGeometry(QRect(5, 145, 101, 491))
        font1 = QFont()
        font1.setFamilies([u"PT Mono"])
        font1.setPointSize(14)
        self.ntu100TextEdit.setFont(font1)
        self.ntu100TextEdit.setLineWrapMode(QTextEdit.LineWrapMode.FixedColumnWidth)
        self.ntu100TextEdit.setLineWrapColumnOrWidth(10)
        self.ntu100TextEdit.setReadOnly(True)
        self.ntu100StdevLabel = QLabel(self.ntu100Frame)
        self.ntu100StdevLabel.setObjectName(u"ntu100StdevLabel")
        self.ntu100StdevLabel.setGeometry(QRect(0, 100, 111, 21))
        self.ntu100StdevLabel.setFont(custom_font12)
        self.ntu100StdevLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu100StdevSpinBox = QDoubleSpinBox(self.ntu100Frame)
        self.ntu100StdevSpinBox.setObjectName(u"ntu100StdevSpinBox")
        self.ntu100StdevSpinBox.setGeometry(QRect(0, 120, 111, 22))
        self.ntu100StdevSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu100StdevSpinBox.setMaximum(65536.000000000000000)
        self.ntu250Frame = QFrame(self.centralwidget)
        self.ntu250Frame.setObjectName(u"ntu250Frame")
        self.ntu250Frame.setGeometry(QRect(125, 5, 111, 641))
        self.ntu250Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.ntu250Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.ntu250TextEdit = QTextEdit(self.ntu250Frame)
        self.ntu250TextEdit.setObjectName(u"ntu250TextEdit")
        self.ntu250TextEdit.setGeometry(QRect(4, 145, 101, 491))
        self.ntu250TextEdit.setFont(font1)
        self.ntu250TextEdit.setLineWrapMode(QTextEdit.LineWrapMode.FixedColumnWidth)
        self.ntu250TextEdit.setLineWrapColumnOrWidth(10)
        self.ntu250TextEdit.setReadOnly(True)
        self.ntu250AverageSpinBox = QDoubleSpinBox(self.ntu250Frame)
        self.ntu250AverageSpinBox.setObjectName(u"ntu250AverageSpinBox")
        self.ntu250AverageSpinBox.setGeometry(QRect(0, 85, 111, 21))
        self.ntu250AverageSpinBox.setReadOnly(True)
        self.ntu250AverageSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu250AverageSpinBox.setMaximum(65536.000000000000000)
        self.ntu250AverageLabel = QLabel(self.ntu250Frame)
        self.ntu250AverageLabel.setObjectName(u"ntu250AverageLabel")
        self.ntu250AverageLabel.setGeometry(QRect(0, 65, 111, 21))
        self.ntu250AverageLabel.setFont(custom_font12)
        self.ntu250AverageLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu250ResetButton = QPushButton(self.ntu250Frame)
        self.ntu250ResetButton.setObjectName(u"ntu250ResetButton")
        self.ntu250ResetButton.setGeometry(QRect(1, 40, 111, 32))
        self.ntu250StartButton = QPushButton(self.ntu250Frame)
        self.ntu250StartButton.setObjectName(u"ntu250StartButton")
        self.ntu250StartButton.setGeometry(QRect(1, 15, 111, 32))
        self.ntu250Label = QLabel(self.ntu250Frame)
        self.ntu250Label.setObjectName(u"ntu250Label")
        self.ntu250Label.setGeometry(QRect(1, 0, 111, 20))
        self.ntu250Label.setFont(custom_font12)
        self.ntu250Label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu250StdevLabel = QLabel(self.ntu250Frame)
        self.ntu250StdevLabel.setObjectName(u"ntu250StdevLabel")
        self.ntu250StdevLabel.setGeometry(QRect(0, 100, 111, 21))
        self.ntu250StdevLabel.setFont(custom_font12)
        self.ntu250StdevLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu250StdevSpinBox = QDoubleSpinBox(self.ntu250Frame)
        self.ntu250StdevSpinBox.setObjectName(u"ntu250StdevSpinBox")
        self.ntu250StdevSpinBox.setGeometry(QRect(0, 120, 111, 22))
        self.ntu250StdevSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu250StdevSpinBox.setMaximum(65536.000000000000000)
        self.ntu50Frame = QFrame(self.centralwidget)
        self.ntu50Frame.setObjectName(u"ntu50Frame")
        self.ntu50Frame.setGeometry(QRect(245, 5, 111, 641))
        self.ntu50Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.ntu50Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.ntu500Label = QLabel(self.ntu50Frame)
        self.ntu500Label.setObjectName(u"ntu500Label")
        self.ntu500Label.setGeometry(QRect(0, 0, 111, 21))
        self.ntu500Label.setFont(custom_font12)
        self.ntu500Label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu500StartButton = QPushButton(self.ntu50Frame)
        self.ntu500StartButton.setObjectName(u"ntu500StartButton")
        self.ntu500StartButton.setGeometry(QRect(0, 15, 111, 32))
        self.ntu500ResetButton = QPushButton(self.ntu50Frame)
        self.ntu500ResetButton.setObjectName(u"ntu500ResetButton")
        self.ntu500ResetButton.setGeometry(QRect(0, 40, 111, 32))
        self.ntu500AverageLabel = QLabel(self.ntu50Frame)
        self.ntu500AverageLabel.setObjectName(u"ntu500AverageLabel")
        self.ntu500AverageLabel.setGeometry(QRect(0, 65, 111, 21))
        self.ntu500AverageLabel.setFont(custom_font12)
        self.ntu500AverageLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu500AverageSpinBox = QDoubleSpinBox(self.ntu50Frame)
        self.ntu500AverageSpinBox.setObjectName(u"ntu500AverageSpinBox")
        self.ntu500AverageSpinBox.setGeometry(QRect(0, 85, 111, 21))
        self.ntu500AverageSpinBox.setReadOnly(True)
        self.ntu500AverageSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu500AverageSpinBox.setMaximum(65536.000000000000000)
        self.ntu500TextEdit = QTextEdit(self.ntu50Frame)
        self.ntu500TextEdit.setObjectName(u"ntu500TextEdit")
        self.ntu500TextEdit.setGeometry(QRect(5, 145, 101, 491))
        self.ntu500TextEdit.setFont(font1)
        self.ntu500TextEdit.setLineWrapMode(QTextEdit.LineWrapMode.FixedColumnWidth)
        self.ntu500TextEdit.setLineWrapColumnOrWidth(10)
        self.ntu500TextEdit.setReadOnly(True)
        self.ntu500StdevLabel = QLabel(self.ntu50Frame)
        self.ntu500StdevLabel.setObjectName(u"ntu500StdevLabel")
        self.ntu500StdevLabel.setGeometry(QRect(0, 100, 111, 21))
        self.ntu500StdevLabel.setFont(custom_font12)
        self.ntu500StdevLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu500StdevSpinBox = QDoubleSpinBox(self.ntu50Frame)
        self.ntu500StdevSpinBox.setObjectName(u"ntu500StdevSpinBox")
        self.ntu500StdevSpinBox.setGeometry(QRect(0, 120, 111, 22))
        self.ntu500StdevSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu500StdevSpinBox.setMaximum(65536.000000000000000)
        self.ntu1000Frame = QFrame(self.centralwidget)
        self.ntu1000Frame.setObjectName(u"ntu1000Frame")
        self.ntu1000Frame.setGeometry(QRect(360, 5, 111, 641))
        self.ntu1000Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.ntu1000Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.ntu1000Label = QLabel(self.ntu1000Frame)
        self.ntu1000Label.setObjectName(u"ntu1000Label")
        self.ntu1000Label.setGeometry(QRect(0, 0, 111, 21))
        self.ntu1000Label.setFont(custom_font12)
        self.ntu1000Label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu1000StartButton = QPushButton(self.ntu1000Frame)
        self.ntu1000StartButton.setObjectName(u"ntu1000StartButton")
        self.ntu1000StartButton.setGeometry(QRect(0, 15, 111, 32))
        self.ntu1000ResetButton = QPushButton(self.ntu1000Frame)
        self.ntu1000ResetButton.setObjectName(u"ntu1000ResetButton")
        self.ntu1000ResetButton.setGeometry(QRect(0, 40, 111, 32))
        self.ntu1000AverageLabel = QLabel(self.ntu1000Frame)
        self.ntu1000AverageLabel.setObjectName(u"ntu1000AverageLabel")
        self.ntu1000AverageLabel.setGeometry(QRect(0, 65, 111, 21))
        self.ntu1000AverageLabel.setFont(custom_font12)
        self.ntu1000AverageLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu1000AverageSpinBox = QDoubleSpinBox(self.ntu1000Frame)
        self.ntu1000AverageSpinBox.setObjectName(u"ntu1000AverageSpinBox")
        self.ntu1000AverageSpinBox.setGeometry(QRect(0, 85, 111, 21))
        self.ntu1000AverageSpinBox.setReadOnly(True)
        self.ntu1000AverageSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu1000AverageSpinBox.setMaximum(65536.000000000000000)
        self.ntu1000TextEdit = QTextEdit(self.ntu1000Frame)
        self.ntu1000TextEdit.setObjectName(u"ntu1000TextEdit")
        self.ntu1000TextEdit.setGeometry(QRect(6, 145, 101, 491))
        self.ntu1000TextEdit.setFont(font1)
        self.ntu1000TextEdit.setLineWrapMode(QTextEdit.LineWrapMode.FixedColumnWidth)
        self.ntu1000TextEdit.setLineWrapColumnOrWidth(10)
        self.ntu1000TextEdit.setReadOnly(True)
        self.ntu1000StdevLabel = QLabel(self.ntu1000Frame)
        self.ntu1000StdevLabel.setObjectName(u"ntu1000StdevLabel")
        self.ntu1000StdevLabel.setGeometry(QRect(0, 100, 111, 21))
        self.ntu1000StdevLabel.setFont(custom_font12)
        self.ntu1000StdevLabel.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.ntu1000StdevSpinBox = QDoubleSpinBox(self.ntu1000Frame)
        self.ntu1000StdevSpinBox.setObjectName(u"ntu500StdevSpinBox_2")
        self.ntu1000StdevSpinBox.setGeometry(QRect(0, 120, 111, 22))
        self.ntu1000StdevSpinBox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ntu1000StdevSpinBox.setMaximum(65536.000000000000000)
        self.findEquationButton = QPushButton(self.centralwidget)
        self.findEquationButton.setObjectName(u"findEquationButton")
        self.findEquationButton.setGeometry(QRect(5, 650, 101, 32))
        self.findEquationButton.setFont(custom_font11)
        self.equationLineEdit = QTextEdit(self.centralwidget)
        self.equationLineEdit.setObjectName(u"equationLineEdit")
        self.equationLineEdit.setGeometry(QRect(115, 650, 356, 31))
        self.equationLineEdit.setFont(custom_font12)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(self)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 475, 37))
        self.menubar.setNativeMenuBar(False)
        self.menuMenu = QMenu(self.menubar)
        self.menuMenu.setObjectName(u"menuMenu")
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName(u"statusbar")
        self.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuMenu.menuAction())
        self.menuMenu.addAction(self.actionReset)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.actionHow_To_UseThisTool)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "OBS Calibrartor"))
        self.ntu100Label.setText(_translate("MainWindow", "100 NTU"))
        self.ntu100StartButton.setText(_translate("MainWindow", "Start"))
        self.ntu100ResetButton.setText(_translate("MainWindow", "Reset"))
        self.ntu100AverageLabel.setText(_translate("MainWindow", "Average"))
        self.ntu100TextEdit.setPlaceholderText(_translate("MainWindow",
                                                          "1                      2                      3                      4                      5                      6                      7                      8                      9                      10                      11                      12                      13                      14                      15                      16                      17                      18                      19                      20                      21                      22                      23                      24                      25                      26                      27                      28                      29                      30                     "))
        self.ntu100StdevLabel.setText(_translate("MainWindow", "Std Dev"))
        self.ntu250TextEdit.setPlaceholderText(_translate("MainWindow",
                                                          "1                      2                      3                      4                      5                      6                      7                      8                      9                      10                      11                      12                      13                      14                      15                      16                      17                      18                      19                      20                      21                      22                      23                      24                      25                      26                      27                      28                      29                      30                     "))
        self.ntu250AverageLabel.setText(_translate("MainWindow", "Average"))
        self.ntu250ResetButton.setText(_translate("MainWindow", "Reset"))
        self.ntu250StartButton.setText(_translate("MainWindow", "Start"))
        self.ntu250Label.setText(_translate("MainWindow", "250 NTU"))
        self.ntu250StdevLabel.setText(_translate("MainWindow", "Std Dev"))
        self.ntu500Label.setText(_translate("MainWindow", "500 NTU"))
        self.ntu500StartButton.setText(_translate("MainWindow", "Start"))
        self.ntu500ResetButton.setText(_translate("MainWindow", "Reset"))
        self.ntu500AverageLabel.setText(_translate("MainWindow", "Average"))
        self.ntu500TextEdit.setPlaceholderText(_translate("MainWindow",
                                                          "1                      2                      3                      4                      5                      6                      7                      8                      9                      10                      11                      12                      13                      14                      15                      16                      17                      18                      19                      20                      21                      22                      23                      24                      25                      26                      27                      28                      29                      30                     "))
        self.ntu500StdevLabel.setText(_translate("MainWindow", "Std Dev"))
        self.ntu1000Label.setText(_translate("MainWindow", "1000 NTU"))
        self.ntu1000StartButton.setText(_translate("MainWindow", "Start"))
        self.ntu1000ResetButton.setText(_translate("MainWindow", "Reset"))
        self.ntu1000AverageLabel.setText(_translate("MainWindow", "Average"))
        self.ntu1000TextEdit.setPlaceholderText(_translate("MainWindow",
                                                           "1                      2                      3                      4                      5                      6                      7                      8                      9                      10                      11                      12                      13                      14                      15                      16                      17                      18                      19                      20                      21                      22                      23                      24                      25                      26                      27                      28                      29                      30                     "))
        self.ntu1000StdevLabel.setText(_translate("MainWindow", "Std Dev"))
        self.findEquationButton.setText(_translate("MainWindow", "Find Equation"))
        self.equationLineEdit.setText(_translate("MainWindow", "Best Fit Equation: "))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu"))
        self.actionReset.setText(_translate("MainWindow", "Reset"))
        self.actionHow_To_UseThisTool.setText(_translate("MainWindow", "How To Use This Tool"))

    def finishSetup(self) -> None:
        # Instantiate the Sensor Thread
        self.sensorThread = SensorThread()

        # Disable the reset buttons
        self.ntu100ResetButton.setDisabled(True)
        self.ntu250ResetButton.setDisabled(True)
        self.ntu500ResetButton.setDisabled(True)
        self.ntu1000ResetButton.setDisabled(True)

        # Disable Find Equation Button
        self.findEquationButton.setDisabled(True)

        # Connect all the signals/slots
        self.connectUIElements()

    def connectUIElements(self) -> None:
        # On "Start" click, start button will disable reset button and start sampling
        self.ntu100StartButton.clicked.connect(lambda: self.startButtonClicked(100))
        self.ntu250StartButton.clicked.connect(lambda: self.startButtonClicked(250))
        self.ntu500StartButton.clicked.connect(lambda: self.startButtonClicked(500))
        self.ntu1000StartButton.clicked.connect(lambda: self.startButtonClicked(1000))

        # On "Reset" click,
        self.ntu100ResetButton.clicked.connect(lambda: self.resetButtonClicked(100))
        self.ntu250ResetButton.clicked.connect(lambda: self.resetButtonClicked(250))
        self.ntu500ResetButton.clicked.connect(lambda: self.resetButtonClicked(500))
        self.ntu1000ResetButton.clicked.connect(lambda: self.resetButtonClicked(1000))

        # On menu "Reset" clicked
        self.actionReset.triggered.connect(self.resetApplication)

        # On menu "How To Use This Tool" clicked
        self.actionHow_To_UseThisTool.triggered.connect(self.showHelp)

        # A sample has been taken by the sampling thread
        self.sensorThread.proximity_read.connect(self.displaySample)

        # Sampling is complete
        self.sensorThread.finished.connect(self.samplingComplete)

        self.findEquationButton.clicked.connect(self.findEquation)

    def startButtonClicked(self, ntu: int) -> None:
        self.ntu100StartButton.setDisabled(True)
        self.ntu250StartButton.setDisabled(True)
        self.ntu500StartButton.setDisabled(True)
        self.ntu1000StartButton.setDisabled(True)

        match ntu:
            case 100:
                self.ntu100ResetButton.setEnabled(True)
                self.ntu100TextEdit.clear()
                self.ongoingSampling = 100

            case 250:
                self.ntu250ResetButton.setEnabled(True)
                self.ntu250TextEdit.clear()
                self.ongoingSampling = 250

            case 500:
                self.ntu500ResetButton.setEnabled(True)
                self.ntu500TextEdit.clear()
                self.ongoingSampling = 500

            case 1000:
                self.ntu1000ResetButton.setEnabled(True)
                self.ntu1000TextEdit.clear()
                self.ongoingSampling = 1000

        self.sensorThread.start()



    def resetButtonClicked(self, ntu: int) -> None:
        match ntu:
            case 100:
                self.ntu100ResetButton.setDisabled(True)
                self.ntu100StartButton.setEnabled(True)
                self.ntu100Complete = False
            case 250:
                self.ntu250ResetButton.setDisabled(True)
                self.ntu250StartButton.setEnabled(True)
                self.ntu250Complete = False
            case 500:
                self.ntu500ResetButton.setDisabled(True)
                self.ntu500StartButton.setEnabled(True)
                self.ntu500Complete = False
            case 1000:
                self.ntu1000ResetButton.setDisabled(True)
                self.ntu1000StartButton.setEnabled(True)
                self.ntu1000Complete = False

        self.ongoingSampling = 0

        self.sensorThread.stop()

        self.checkforCompleteness()


    def resetApplication(self) -> None:
        self.setupUi()
        self.finishSetup()

    def showHelp(self) -> None:
        popup = HelpPopUpWindow()
        popup.exec()

    def displaySample(self, sample) -> None:
        match self.ongoingSampling:
            case 100:
                self.ntu100TextEdit.append(str(sample))

            case 250:
                self.ntu250TextEdit.append(str(sample))

            case 500:
                self.ntu500TextEdit.append(str(sample))

            case 1000:
                self.ntu1000TextEdit.append(str(sample))

    def samplingComplete(self, mean, stdev) -> None:
        checkStdev = lambda stdev, mean: (stdev / mean) < 0.01 if stdev != 0 else False

        match self.ongoingSampling:
            case 100:
                self.ntu100AverageSpinBox.setValue(mean)
                if checkStdev:
                    self.changeSpinBoxColor(self.ntu100StdevSpinBox, "black")
                    self.ntu100Complete = True
                else:
                    self.changeSpinBoxColor(self.ntu100StdevSpinBox, "red")
                    self.ntu100Complete = False

                self.ntu100StdevSpinBox.setValue(stdev)

            case 250:
                self.ntu250AverageSpinBox.setValue(mean)
                if checkStdev:
                    self.changeSpinBoxColor(self.ntu250StdevSpinBox, "black")
                    self.ntu250Complete = True
                else:
                    self.changeSpinBoxColor(self.ntu250StdevSpinBox, "red")
                    self.ntu250Complete = False

                self.ntu250StdevSpinBox.setValue(stdev)

            case 500:
                self.ntu500AverageSpinBox.setValue(mean)
                if checkStdev:
                    self.changeSpinBoxColor(self.ntu500StdevSpinBox, "black")
                    self.ntu500Complete = True
                else:
                    self.changeSpinBoxColor(self.ntu500StdevSpinBox, "red")
                    self.ntu500Complete = False

                self.ntu500StdevSpinBox.setValue(stdev)

            case 1000:
                self.ntu1000AverageSpinBox.setValue(mean)
                if checkStdev:
                    self.changeSpinBoxColor(self.ntu1000StdevSpinBox, "black")
                    self.ntu1000Complete = True
                else:
                    self.changeSpinBoxColor(self.ntu1000StdevSpinBox, "red")
                    self.ntu1000Complete = False

                self.ntu1000StdevSpinBox.setValue(stdev)

        self.ongoingSampling = 0

        self.checkforCompleteness()

    def changeSpinBoxColor(self, spinBox, color) -> None:
        spinBox.setStyleSheet(f"""
            QDoubleSpinBox {{
                color: {color};
            }}""")

    def checkforCompleteness(self) -> None:
        if (self.ntu1000Complete and self.ntu250Complete and self.ntu500Complete and self.ntu100Complete):
            self.findEquationButton.setEnabled(True)
        else:
            self.findEquationButton.setDisabled(True)

        if not self.ntu100Complete:
            self.ntu100StartButton.setEnabled(True)

        if not self.ntu250Complete:
            self.ntu250StartButton.setEnabled(True)

        if not self.ntu500Complete:
            self.ntu500StartButton.setEnabled(True)

        if not self.ntu1000Complete:
            self.ntu1000StartButton.setEnabled(True)

    def findEquation(self) -> None:
        x_points = [100.0, 250.0, 500.0, 1000.0]
        y_points = [self.ntu100AverageSpinBox.value(), self.ntu250AverageSpinBox.value(),
                    self.ntu500AverageSpinBox.value(), self.ntu1000AverageSpinBox.value()]

        # Fit a 3rd-degree polynomial
        coeffs = np.polyfit(x_points, y_points, 3)

        # Create a polynomial function from the coefficients
        poly_func = np.poly1d(coeffs)

        self.equationLineEdit.setText(self.format_polynomial_for_qtextedit(poly_func))

    def format_polynomial_for_qtextedit(self, poly_func):
        """
        Formats a numpy.poly1d object into an HTML string for QTextEdit display.
        """
        terms = []
        degree = poly_func.order
        coeffs = poly_func.coefficients
        for i, coeff in enumerate(coeffs):
            power = degree - i
            if abs(coeff) < 1e-6:
                continue  # Skip near-zero coefficients

            # Format coefficient
            coeff_str = f"{coeff:.4f}"
            if coeff > 0 and i != 0:
                coeff_str = f"+ {coeff_str}"
            elif coeff < 0:
                coeff_str = f"- {abs(coeff):.4f}"

            # Format term
            if power == 0:
                term = f"{coeff_str}"
            elif power == 1:
                term = f"{coeff_str}x"
            else:
                term = f"{coeff_str}x<sup>{power}</sup>"

            terms.append(term)

        return " ".join(terms)



def main():
    app = QApplication(sys.argv)

    obsCalibrator = OBSCalibratorApp()
    obsCalibrator.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()



