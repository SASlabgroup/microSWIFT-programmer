import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import OBS_Calibration_Window

Window {
    id: appWindow
    width: mainScreen.width
    height: mainScreen.height
    visible: true
    title: "OBS Calibration"

    OBS_Calibrator_Screen { id: mainScreen }

    CalibrationPlot { id: calibrationPlotDialog }

    Connections {
        target: uiController
        function onPlotReady(path) {
            calibrationPlotDialog.plotSource = "file://" + path

            // safely pull the serial number from main screen property
            calibrationPlotDialog.serial = mainScreen.serialNumber

            calibrationPlotDialog.open()
        }
    }
}
