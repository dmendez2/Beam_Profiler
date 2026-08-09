import QtQuick
import QtQuick.Controls 2.5


Label{
    id: label
    property real displayScaleFactor: 1

    property color textColor: "#FFFFFF"
    property color hoverColor: "#666666"

    color: label.enabled ? label.textColor : label.hoverColor
    font.bold: true
    font.pixelSize: 12 * label.displayScaleFactor
    font.capitalization: Font.AllUppercase
}
