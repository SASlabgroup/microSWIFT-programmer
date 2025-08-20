import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import OBS_Calibration_Window

Window {
    id: appWindow
    width: mainScreen.width
    height: mainScreen.height
    visible: true
    title: "OBS Calibration_Window"

    // Main content
    OBS_Calibrator_Screen {
        id: mainScreen
    }

    // Calibration plot dialog always instantiated
    CalibrationPlot {
        id: calibrationPlotDialog
    }

    // Connect Python signal to open the dialog
    Connections {
        target: uiController
        function onPlotReady(imagePath) {
            calibrationPlotDialog.imagePath = imagePath
            calibrationPlotDialog.open()
        }
    }
}
