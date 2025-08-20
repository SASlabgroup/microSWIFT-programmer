import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Popup {
    id: calibrationPlotDialog
    modal: true
    focus: true
    width: 600
    height: 500
    visible: false

    property string imagePath: ""

    Rectangle {
        anchors.fill: parent
        color: "#1b1a1a"
        border.color: "gray"
        radius: 8

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
}
