pragma Singleton
import QtQuick

QtObject {
    readonly property int width: 800
    readonly property int height: 800

    readonly property string relativeFontDirectory: "fonts"

    // Replace with a default font or configure via Python
    readonly property string defaultFontFamily: "PT Mono"
    readonly property int defaultFontSize: 14

    readonly property font font: Qt.font({
        family: defaultFontFamily,
        pixelSize: defaultFontSize
    })

    readonly property font largeFont: Qt.font({
        family: defaultFontFamily,
        pixelSize: defaultFontSize * 1.6
    })

    readonly property color backgroundColor: "#EAEAEA"
}
