import QtQuick
import QtQuick.Controls 2.5

Rectangle {
    id: display
    property string displayText: ""

    property color displayColor: "#FFFFFF"
    property color backgroundColor: "#111111"
    property color borderColor: "#333333"

    color: display.backgroundColor
    border.color: display.borderColor
    border.width: 1
    radius: 4
    height: 30

    Label{
        anchors.centerIn: parent
        text: display.displayText
        color: display.displayColor
        font.bold: true
        font.family: "Courier"
        font.pixelSize: 20
    }
}
