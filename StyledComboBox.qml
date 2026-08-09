import QtQuick
import QtQuick.Controls 2.5

ComboBox {
    id: styledComboBox


    property real displayScaleFactor: 1

    property color textColor: "#FFFFFF"
    property color backgroundColor: "#111111"
    property color borderColor: "#333333"
    property color hoverColor: "#666666"
    property color pressedColor: "#AAAAAA"

    // Text displayed in the closed ComboBox
    contentItem: Text {
        text: styledComboBox.displayText
        color: styledComboBox.enabled ? styledComboBox.textColor : styledComboBox.hoverColor
        font.family: "Courier"
        font.bold: true
        font.pixelSize: 12 * styledComboBox.displayScaleFactor

        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
    }

    // Closed ComboBox background
    background: Rectangle {
        color: styledComboBox.pressed ? pressedColor: (styledComboBox.hovered ? styledComboBox.hoverColor : styledComboBox.borderColor)

        border.color: styledComboBox.borderColor
        border.width: 1
        radius: 12
    }

    // Dropdown menu
    popup: Popup {
        y: styledComboBox.height - 1
        width: styledComboBox.width

        padding: 1

        contentItem: ListView {
            clip: true

            implicitHeight: contentHeight
            model: styledComboBox.popup.visible ? styledComboBox.delegateModel: null

            currentIndex: styledComboBox.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: styledComboBox.backgroundColor
            border.color: styledComboBox.borderColor
            border.width: 1
            radius: 12
        }
    }

    // Individual items in dropdown
    delegate: ItemDelegate {
        width: styledComboBox.width
        height: 35

        highlighted: styledComboBox.highlightedIndex === index

        contentItem: Text {
            text: modelData
            color: styledComboBox.textColor
            font.pixelSize: 12 * styledComboBox.displayScaleFactor
            font.family: "Courier"
            font.bold: true

            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }

        background: Rectangle {
            color: parent.highlighted? styledComboBox.hoverColor: styledComboBox.backgroundColor
        }
    }
}
