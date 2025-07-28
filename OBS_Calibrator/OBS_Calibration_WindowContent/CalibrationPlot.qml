import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Item {
    width: 400
    height: 400

    Column {
        anchors.centerIn: parent
        spacing: 12

        Image {
            id: plotImage
            width: 360
            height: 240
            source: "image://calibrationPlot"
            fillMode: Image.PreserveAspectFit
        }

        Label {
            id: equationLabel
            text: calibrationPlot.equation
            font.family: "PT Mono"
            horizontalAlignment: Text.AlignHCenter
            width: parent.width
        }

        Label {
            id: r2Label
            text: calibrationPlot.r2
            font.family: "PT Mono"
            horizontalAlignment: Text.AlignHCenter
            width: parent.width
        }
    }
}

