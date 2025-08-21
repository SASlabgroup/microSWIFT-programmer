import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.platform 1.1  // for FileDialog

Popup {
    id: calibrationDialog
    property alias plotSource: plotImage.source
    modal: true
    focus: true
    width: 600
    height: 500

    Column {
        anchors.fill: parent
        spacing: 10
        padding: 10

        Image {
            id: plotImage
            anchors.horizontalCenter: parent.horizontalCenter
            fillMode: Image.PreserveAspectFit
            width: parent.width
            height: parent.height - saveButton.height - 20
        }

        Button {
            id: saveButton
            text: "Save Plot"
            anchors.horizontalCenter: parent.horizontalCenter
            onClicked: plotSaveDialog.open()
        }
    }

    FileDialog {
        id: plotSaveDialog
        title: "Save Calibration Plot"
        nameFilters: ["PNG files (*.png)"]
        fileMode: FileDialog.SaveFile
        onAccepted: {
            uiController.saveCalibrationPlot(file)
        }
    }
}
