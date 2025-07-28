
/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/

import QtQuick
import QtQuick.Controls
import OBS_Calibration_Window

Rectangle {
    id: rectangle
    width: Constants.width
    height: 820
    color: "#1b1a1a"


    Grid {
        id: ntuComponentGrid
        x: 0
        y: 33
        width: 800
        height: 724
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

        NTUConcentrationComponent {
            id: ntuComponent0
            objectName: "ntuComponent0"
        }

        NTUConcentrationComponent {
            id: ntuComponent1
            enabled: false
            objectName: "ntuComponent1"
        }

        NTUConcentrationComponent {
            id: ntuComponent2
            enabled: false
            objectName: "ntuComponent2"
        }

        NTUConcentrationComponent {
            id: ntuComponent3
            enabled: false
            objectName: "ntuComponent3"
        }

        NTUConcentrationComponent {
            id: ntuComponent4
            enabled: false
            objectName: "ntuComponent4"
        }

        NTUConcentrationComponent {
            id: ntuComponent5
            enabled: false
            objectName: "ntuComponent5"
        }

        NTUConcentrationComponent {
            id: ntuComponent6
            enabled: false
            objectName: "ntuComponent6"
        }

        NTUConcentrationComponent {
            id: ntuComponent7
            enabled: false
            objectName: "ntuComponent7"
        }

        NTUConcentrationComponent {
            id: ntuComponent8
            enabled: false
            objectName: "ntuComponent8"
        }

        NTUConcentrationComponent {
            id: ntuComponent9
            enabled: false
            objectName: "ntuComponent9"
        }
    }

    Button {
        id: findEquationButton
        objectName: "findEquationButton"
        x: 8
        y: 780
        width: 200
        height: 32
        text: qsTr("Find Equation")
        enabled: true
        layer.enabled: false
        font.family: "PT Mono"
    }

    Button {
        id: saveSampleData
        objectName: "saveSampleData"
        x: 592
        y: 780
        width: 200
        height: 32
        text: qsTr("Save Sample Data")
        enabled: false
        font.family: "PT Mono"
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
    }

    Label {
        id: serialNumberLabel
        x: 342
        y: 763
        text: qsTr("Serial Number")
        font.family: "PT Mono"
    }

    TextField {
        id: serialNumberTextField
        objectName: "serialNumberTextField"
        x: 342
        y: 782
        width: 117
        height: 30
        text: "0"
        maximumLength: 10
        font.family: "PT Mono"
        placeholderText: qsTr("Text Field")

        validator: RegularExpressionValidator {
            regularExpression: /^[a-zA-Z0-9]*$/
        }
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

    Label {
        id: numCalibrationPointsLabel
        objectName: "numCalibrationPointsLabel"
        x: 395
        y: 14
        text: qsTr("Number of Calibration Points")
        font.family: "PT Mono"
    }

    states: [
        State {
            name: "clicked"
        }
    ]

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

    Component.onCompleted: {
        helpButton.onClicked.connect(() => helpPopup.open())
    }
}
