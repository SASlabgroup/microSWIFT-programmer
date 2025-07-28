import QtQuick
import QtQuick.Controls

Frame {
    id: ntuConcentrationUnitFrame
    width: 145
    height: 350
    padding: 0
    leftPadding: 0
    topPadding: 0
    spacing: 10

    Flow {
        id: framedFlow
        x: 0
        y: 0
        width: 145
        height: 350
        padding: 1
        rightPadding: 1
        leftPadding: 1
        bottomPadding: 1
        topPadding: 1
        spacing: 5

        Button {
            id: startButton
            objectName: "startButton"
            width: 69
            text: qsTr("Start")
            font.family: "PT Mono"
        }

        Button {
            id: resetButton
            objectName: "resetButton"
            width: 69
            text: qsTr("Reset")
            font.family: "PT Mono"
            leftPadding: 9
        }

        Label {
            id: ntuConcentrationLabel
            objectName: "ntuConcentrationLabel"
            width: 69
            text: qsTr("NTU")
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 12
            font.family: "PT Mono"
        }

        Label {
            id: numSamplesLabel
            objectName: "numSamplesLabel"
            width: 69
            text: qsTr("Samples")
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 12
            font.family: "PT Mono"
        }

        SpinBox {
            id: ntuConcentrationSpinBox
            objectName: "ntuConcentrationSpinBox"
            width: 69
            font.pointSize: 12
            font.family: "PT Mono"
            hoverEnabled: false
            editable: true
            to: 10000
            up.indicator: Item {}
            down.indicator: Item {}
        }

        SpinBox {
            id: numSamplesSpinBox
            objectName: "numSamplesSpinBox"
            width: 69
            editable: true
            font.pointSize: 12
            font.family: "PT Mono"
            from: 1
            to: 256
            up.indicator: Item {}
            down.indicator: Item {}
            contentItem: TextInput {
                id: numSamplesSpinBoxTextInput
                text: numSamplesSpinBox.value.toString()
                font: numSamplesSpinBox.font
                color: numSamplesSpinBox.palette.text
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                validator: numSamplesSpinBox.validator
                inputMethodHints: Qt.ImhFormattedNumbersOnly
                enabled: numSamplesSpinBox.enabled

                onTextChanged: {
                    numSamplesSpinBox.value = parseInt(text)
                }
            }
        }

        Label {
            id: averageLabel
            objectName: "averageLabel"
            width: 69
            text: qsTr("Mean")
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 12
            font.family: "PT Mono"
        }

        Label {
            id: stdevLabel
            objectName: "stdevLabel"
            width: 69
            text: qsTr("Stdev")
            horizontalAlignment: Text.AlignHCenter
            font.pointSize: 12
            font.family: "PT Mono"
        }

        SpinBox {
            id: averageSpinBox
            objectName: "averageSpinBox"
            width: 69
            font.family: "PT Mono"
            to: 65536
            editable: false
            font.pointSize: 12
            up.indicator: Item {}
            down.indicator: Item {}
        }

        SpinBox {
            id: stdevSpinBox
            objectName: "stdevSpinBox"
            width: 69
            editable: false
            from: 0
            to: 65536
            font.pointSize: 12
            font.family: "PT Mono"
            property color textColor: "white"
            up.indicator: Item {}
            down.indicator: Item {}

            contentItem: TextInput {
                text: stdevSpinBox.value.toString()
                font: stdevSpinBox.font
                color: stdevSpinBox.enabled ? stdevSpinBox.textColor : stdevSpinBox.palette.disabled.text
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                readOnly: true
            }
        }

        ScrollView {
            width: 143
            height: 214

            TextArea {
                id: samplesTextArea
                objectName: "samplesTextArea"
                width: parent.width
                height: parent.height
                horizontalAlignment: Text.AlignLeft
                wrapMode: Text.WordWrap
                placeholderText: qsTr("")
                cursorVisible: true
                readOnly: true
                font.pointSize: 12
                font.family: "PT Mono"
            }
        }
    }
}
