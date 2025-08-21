import QtQuick 2.15
import QtQuick.Controls 2.15
import Qt.labs.platform 1.1
import QtQuick.Layouts 1.15

Popup {
    id: calibrationDialog
    property alias plotSource: plotImage.source
    property string serial: ""       // serial number from main screen
    modal: true
    focus: true
    width: 600
    height: 500
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    Column {
        anchors.fill: parent
        spacing: 10
        padding: 10

        Image {
            id: plotImage
            anchors.horizontalCenter: parent.horizontalCenter
            fillMode: Image.PreserveAspectFit
            width: parent.width
            height: parent.height - buttonRow.height - 20
        }

        Row {
            id: buttonRow
            spacing: 20
            anchors.horizontalCenter: parent.horizontalCenter

            Button {
                id: saveButton
                text: "Save Plot"
                onClicked: {
                    let downloadsPath = StandardPaths.standardLocations(StandardPaths.DownloadLocation)[0];
                    let filename = "calibration_plot_sn_" + calibrationDialog.serial + ".png";
                    plotSaveDialog.currentFile = downloadsPath + "/" + filename;
                    plotSaveDialog.open();
                }
            }

            Button {
                text: "Close"
                onClicked: calibrationDialog.close()
            }
        }
    }

    FileDialog {
        id: plotSaveDialog
        title: "Save Calibration Plot"
        nameFilters: ["PNG files (*.png)"]
        fileMode: FileDialog.SaveFile

        onAccepted: {
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
