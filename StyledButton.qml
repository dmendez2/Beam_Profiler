import QtQuick
import QtQuick.Controls 2.5

Button {
    property color textColor: "#FFFFFF"
    property color backgroundColor: "#FFFFFF"
    property color borderColor: "#FFFFFF"

    property string displayText: ""
    property real displayScaleFactor: 1

    id: styledButton
    contentItem: Text {
        text: displayText
        color: textColor
        font.pixelSize: 12 * styledButton.displayScaleFactor
        font.bold: true
        font.family: "Courier"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        color: styledButton.backgroundColor
        border.color: styledButton.borderColor
        border.width: 1
        radius: 12
    }
}
