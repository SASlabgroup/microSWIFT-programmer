// FloatSpinBox.qml
import QtQuick
import QtQuick.Controls

Item {
    id: root
    property real floatValue: internalSpinBox.value / scaleFactor
    property real from: 0.0
    property real to: 100.0
    property real stepSize: 0.1
    property int scaleFactor: 10  // Use 100 for two decimal places

    width: internalSpinBox.width
    height: internalSpinBox.height

    SpinBox {
        id: internalSpinBox
        anchors.fill: parent
        from: Math.round(root.from * scaleFactor)
        to: Math.round(root.to * scaleFactor)
        stepSize: Math.round(root.stepSize * scaleFactor)
        value: Math.round(root.floatValue * scaleFactor)
        editable: false

        contentItem: Text {
            text: (internalSpinBox.value / scaleFactor).toFixed(1)
            font: internalSpinBox.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
}
