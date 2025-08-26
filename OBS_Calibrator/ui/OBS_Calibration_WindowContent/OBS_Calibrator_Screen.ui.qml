import QtQuick
import QtQuick.Controls
import OBS_Calibration_Window
import QtQuick.Dialogs
import Qt.labs.platform 1.1

Rectangle {
    id: rectangle
    width: Constants.width
    height: Constants.height  // Use the constant height (800)
    // Remove hardcoded color to use system theme

    // Expose the serial number as a property for external access
    property string serialNumber: serialNumberTextField.text

    Grid {
        id: ntuComponentGrid
        x: 0
        y: 33
        width: 800
        height: 700  // Reduced to make room for bottom controls
        rightPadding: 27
        leftPadding: 23
        layoutDirection: Qt.LeftToRight
        verticalItemAlignment: Grid.AlignVCenter
        horizontalItemAlignment: Grid.AlignHCenter
        spacing: 7
        rows: 2
        columns: 5
        bottomPadding: 10
        topPadding: 10

        // NTU Components (0–9)
        NTUConcentrationComponent { id: ntuComponent0; objectName: "ntuComponent0" }
        NTUConcentrationComponent { id: ntuComponent1; enabled: false; objectName: "ntuComponent1" }
        NTUConcentrationComponent { id: ntuComponent2; enabled: false; objectName: "ntuComponent2" }
        NTUConcentrationComponent { id: ntuComponent3; enabled: false; objectName: "ntuComponent3" }
        NTUConcentrationComponent { id: ntuComponent4; enabled: false; objectName: "ntuComponent4" }
        NTUConcentrationComponent { id: ntuComponent5; enabled: false; objectName: "ntuComponent5" }
        NTUConcentrationComponent { id: ntuComponent6; enabled: false; objectName: "ntuComponent6" }
        NTUConcentrationComponent { id: ntuComponent7; enabled: false; objectName: "ntuComponent7" }
        NTUConcentrationComponent { id: ntuComponent8; enabled: false; objectName: "ntuComponent8" }
        NTUConcentrationComponent { id: ntuComponent9; enabled: false; objectName: "ntuComponent9" }
    }

    Button {
        id: findEquationButton
        objectName: "findEquationButton"
        x: 8
        y: 755  // Moved up to fit in 800px height
        width: 200
        height: 32
        text: qsTr("Find Equation")
        enabled: false
        font.family: "PT Mono"
    }

    Button {
        id: saveSampleData
        objectName: "saveSampleData"
        x: 592
        y: 755  // Moved up to fit in 800px height
        width: 200
        height: 32
        text: qsTr("Save Sample Data")
        enabled: true
        font.family: "PT Mono"

        onClicked: {
            // Get downloads path
            let downloadsPath = StandardPaths.standardLocations(StandardPaths.DownloadLocation)[0];

            // Prepopulate filename using serial number
            let filename = "calibration_sample_data_sn_" + serialNumber + ".csv";
            saveDialog.currentFile = downloadsPath + "/" + filename;

            saveDialog.open();
        }
    }

    Button {
        id: helpButton
        objectName: "helpButton"
        x: 5
        y: 5
        width: 145
        height: 30
        text: "Help Me!"
        font.family: "PT Mono"
        onClicked: helpPopup.open()
    }

    Label {
        id: numCalibrationPointsLabel
        objectName: "numCalibrationPointsLabel"
        x: 395
        y: 14
        text: qsTr("Number of Calibration Points")
        font.family: "PT Mono"
    }

    Label {
        id: serialNumberLabel
        x: 342
        y: 738  // Moved up to fit in 800px height
        text: qsTr("Serial Number")
        font.family: "PT Mono"
    }

    TextField {
        id: serialNumberTextField
        objectName: "serialNumberTextField"
        x: 342
        y: 757  // Moved up to fit in 800px height
        width: 117
        height: 30
        text: "0"
        maximumLength: 10
        font.family: "PT Mono"
        placeholderText: qsTr("Serial Number")
        validator: RegularExpressionValidator { regularExpression: /^[a-zA-Z0-9]*$/ }
    }

    SpinBox {
        id: numCalibrationPointsSpinBox
        objectName: "numCalibrationPointsSpinBox"
        x: 653
        y: 8
        width: 120
        height: 29
        font.family: "PT Mono"
        to: 10
        from: 1
    }

    Popup {
        id: helpPopup
        modal: true
        focus: true
        x: (rectangle.width - width) / 2
        y: (rectangle.height - height) / 2
        width: 320
        height: 200

        Rectangle {
            anchors.fill: parent
            color: "white"
            border.color: "gray"
            radius: 8

            Text {
                id: helpText
                text: "This application helps you calibrate NTU concentration values.\n\nEnter values, then click 'Find Equation'."
                wrapMode: Text.Wrap
                anchors.top: parent.top
                anchors.topMargin: 20
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width - 40
                horizontalAlignment: Text.AlignHCenter
                font.family: "PT Mono"
            }

            Button {
                id: closeButton
                text: "Close"
                anchors.top: helpText.bottom
                anchors.topMargin: 50
                anchors.horizontalCenter: parent.horizontalCenter
                onClicked: helpPopup.close()
                font.family: "PT Mono"
            }
        }
    }

    FileDialog {
        id: saveDialog
        title: "Save Sample Data"
        fileMode: FileDialog.SaveFile
        nameFilters: ["CSV files (*.csv)", "All files (*)"]

        onAccepted: {
            let path = saveDialog.fileUrl && saveDialog.fileUrl !== ""
                       ? saveDialog.fileUrl
                       : saveDialog.currentFile;

            if (path && path !== "") {
                console.log("Selected file:", path)
                uiController.saveSampleData(path)
            } else {
                console.log("No file selected")
            }
        }

        onRejected: {
            console.log("Save canceled")
        }
    }
}
