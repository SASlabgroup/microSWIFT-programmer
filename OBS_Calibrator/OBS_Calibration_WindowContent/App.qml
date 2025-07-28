import QtQuick
import OBS_Calibration_Window

Window {
    width: mainScreen.width
    height: mainScreen.height

    visible: true
    title: "OBS_Calibration_Window"

    OBS_Calibrator_Screen {
        id: mainScreen
    }

}

