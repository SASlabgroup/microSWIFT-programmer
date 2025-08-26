pragma Singleton
import QtQuick

QtObject {
    readonly property int width: 800
    readonly property int height: 810

    readonly property string relativeFontDirectory: "fonts"

    // Load PT Mono font from embedded file
    readonly property FontLoader ptMonoFont: FontLoader {
        source: "../fonts/PTMono-Regular.ttf"
    }

    // Use loaded font or fallback to system PT Mono
    readonly property string defaultFontFamily: ptMonoFont.status === FontLoader.Ready ? ptMonoFont.name : "PT Mono, Consolas, Monaco, Menlo, monospace"
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
