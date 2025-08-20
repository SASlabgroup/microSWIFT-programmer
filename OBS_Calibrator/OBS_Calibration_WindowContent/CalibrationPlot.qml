import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15


Dialog {
    id: calibrationPlotDialog
    modal: true
    width: 600
    height: 500
    title: "Calibration Curve"

    // Property to receive image path from Python
    property string imagePath: ""

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        Image {
            id: plotImage
            source: imagePath !== "" ? "file://" + imagePath : ""
            fillMode: Image.PreserveAspectFit
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        Button {
            text: "Close"
            Layout.alignment: Qt.AlignHCenter
            onClicked: calibrationPlotDialog.close()
        }
    }
}
