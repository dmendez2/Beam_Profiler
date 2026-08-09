import QtQuick
import QtQuick.Controls 2.5

TextField {
    id: inputField

    property color textColor: "#FFFFFF"
    property color placeHolderTextColor: "#888888"

    property color backgroundColor: "#111111"
    property color hoverColor: "#666666"
    property color pressedColor: "#AAAAAA"

    property int bottomVal: 0
    property int topVal: 1

    horizontalAlignment: Text.AlignHCenter

    color: textColor
    placeholderTextColor: placeHolderTextColor

    validator: IntValidator {
        bottom: inputField.bottomVal
        top: inputField.topVal
    }

    background: Rectangle {
        color: backgroundColor
        border.color: inputField.activeFocus? inputField.pressedColor: inputField.hoverColor
        border.width: 1
        radius: 4
    }
}
