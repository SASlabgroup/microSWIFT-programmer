import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.platform 1.1  // For FileDialog
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

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
            onClicked: {
                // Set default filename in user's Downloads folder
                let downloadsPath = StandardPaths.standardLocations(StandardPaths.DownloadLocation)[0];
                plotSaveDialog.currentFile = downloadsPath + "/calibration_plot.png";
                plotSaveDialog.open();
            }
        }
    }

    FileDialog {
        id: plotSaveDialog
        title: "Save Calibration Plot"
        nameFilters: ["PNG files (*.png)"]
        fileMode: FileDialog.SaveFile

        onAccepted: {
            // Use fileUrl if defined, otherwise fallback to currentFile
            let path = plotSaveDialog.fileUrl && plotSaveDialog.fileUrl !== ""
                       ? plotSaveDialog.fileUrl
                       : plotSaveDialog.currentFile;

            if (path && path !== "") {
                console.log("Selected file:", path)
                uiController.saveCalibrationPlot(path)
            } else {
                console.log("No file selected")
            }
        }

        onRejected: {
            console.log("Save canceled")
        }
    }

}
