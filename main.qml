import QtQuick
import Qt.labs.platform 1.1
import QtQuick.Controls 2.5
import QtQuick.Layouts 1.3

ApplicationWindow {
    id: root
    width: 640
    height: 480
    visible: true
    title: qsTr("Beam Profiler")

    property color windowColor: "#000000"
    property color backgroundColor: "#111111"
    property color borderColor: "#333333"
    property color hoverColor: "#666666"
    property color pressedColor: "#AAAAAA"
    property color confirmationColor: "#2CFF05"
    property color pressedConfirmationColor: "#339152"
    property color negationColor : "#FF3131"
    property color pressedNegationColor : "#B20000"
    property color textColor: "#FFFFFF"
    property color placeHolderTextColor: "#888888"
    property color triggerColor: "#0096FF"
    property color pressedTriggerColor: "#0077CC"

    property real displayScaleFactor: Math.min(root.width / 640, root.height / 480)

    Rectangle {
        id: background
        anchors.fill: parent
        color: "transparent"

        Rectangle{
            id: control_block
            height: parent.height
            width: parent.width * 0.35
            anchors.left: parent.left
            color: root.windowColor

            ScrollView {
                id: sleekScrollView
                anchors.fill: parent
                leftPadding: 10
                rightPadding: 20
                clip: true

                // Only allow vertical scrolling
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                // Custom vertical scrollbar
                ScrollBar.vertical: ScrollBar {
                    id: customScrollBar

                    width: 10
                    height: sleekScrollView.availableHeight

                    x: sleekScrollView.width - customScrollBar.width // Tiny offset from the right boundary
                    y: sleekScrollView.topPadding

                    contentItem: Rectangle {
                        implicitWidth: 6
                        implicitHeight: 50

                        radius: root.width / 2

                        color: customScrollBar.pressed? root.pressedColor: customScrollBar.hovered? root.hoverColor: root.borderColor

                        Behavior on color {
                            ColorAnimation {
                                duration: 150
                            }
                        }
                    }

                    background: Rectangle {
                        color: "transparent"
                    }
                }

                TapHandler {
                    onTapped: {
                        background.forceActiveFocus()
                    }
                }

                ColumnLayout{
                    id: control_column
                    width: sleekScrollView.availableWidth
                    spacing: 10

                    Rectangle{
                        width: parent.width
                        height: 0
                        color: root.windowColor
                    }

                    Label{
                        text: "CONNECT HP-34401A"
                        color: root.textColor
                        font.bold: true
                        font.pixelSize: 16 * root.displayScaleFactor
                        font.capitalization: Font.AllUppercase
                        font.family: "Courier"
                    }

                    Rectangle{
                        Layout.preferredHeight: 1
                        Layout.fillWidth: true
                        color: root.textColor
                    }

                    SectionLabel{
                        text: "USB PORT:"
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledComboBox{
                        id: comPortComboBox
                        displayScaleFactor: root.displayScaleFactor
                        Layout.fillWidth: true
                        model: bp_controller.comPortList

                        onCurrentTextChanged: {
                            bp_controller.updateComPort(currentText)
                        }
                    }

                    SectionLabel{
                        text: "BAUD RATE:"
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledComboBox{
                        id: baudRateComboBox
                        displayScaleFactor: root.displayScaleFactor
                        Layout.fillWidth: true
                        model: ["300", "600", "1200", "2400", "4800", "9600"]
                        currentIndex: 5

                        onCurrentTextChanged: {
                            bp_controller.updateBaudRate(currentText)
                        }
                    }

                    SectionLabel{
                        text: "GPIB ADDRESS:"
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledTextField{
                        id: gpibAddressField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Enter GPIB address")
                        bottomVal: 0
                        topVal: 30

                        onEditingFinished: {
                            const addr = Number(text)
                            if (!isNaN(addr))
                                bp_controller.updateGpibAddress(addr)
                        }
                    }

                    StyledButton{
                        id: multimeterConnectButton
                        enabled: bp_controller.canConnectMultimeter
                        displayScaleFactor: root.displayScaleFactor
                        displayText: "CONNECT MULTIMETER"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20 * root.displayScaleFactor
                        textColor: multimeterConnectButton.enabled ? (multimeterConnectButton.down ? root.textColor : root.confirmationColor): root.hoverColor
                        backgroundColor: multimeterConnectButton.enabled ? (multimeterConnectButton.pressed ? root.pressedConfirmationColor : (multimeterConnectButton.hovered ? root.hoverColor : root.windowColor)): root.windowColor
                        borderColor: multimeterConnectButton.enabled ? root.confirmationColor : root.hoverColor

                        onPressed: {
                            bp_controller.connectMultimeter()
                        }
                    }

                    SectionLabel{
                        text: "CONNECTION STATUS:"
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StatusDisplay{
                        displayText: bp_controller.isMultimeterConnected ? "CONNECTED" : "DISCONNECTED"
                        displayColor: bp_controller.isMultimeterConnected ? root.confirmationColor : root.negationColor
                        Layout.fillWidth: true
                    }

                    Rectangle{
                        width: parent.width
                        height: 5
                        color: root.windowColor
                    }

                    Label{
                        text: "CONFIGURE SETTINGS:"
                        color: root.textColor
                        font.bold: true
                        font.pointSize: 12 * root.displayScaleFactor
                        font.capitalization: Font.AllUppercase
                        font.family: "Courier"
                    }

                    Rectangle{
                        Layout.preferredHeight: 1
                        Layout.fillWidth: true
                        color: root.textColor
                    }

                    SectionLabel{
                        text: "RANGE (A):"
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledComboBox{
                        id: rangeComboBox
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                        Layout.fillWidth: true
                        model: ["Auto", "0.01", "0.1", "1", "3"]
                        currentIndex: 0

                        onCurrentTextChanged: {
                            bp_controller.updateCurrentRange(currentText)
                        }
                    }

                    SectionLabel{
                        text: "Integration Time (PLCs):"
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledComboBox{
                        id: integrationTimeComboBox
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                        Layout.fillWidth: true
                        model: ["0.02", "0.2", "1", "10", "100"]
                        currentIndex: 3

                        onCurrentTextChanged: {
                            bp_controller.updateIntegrationTime(currentText)
                        }
                    }

                    SectionLabel{
                        text: "AUTO-ZERO:"
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledComboBox{
                        id: autoZeroComboBox
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                        Layout.fillWidth: true
                        model: ["On", "Off"]
                        currentIndex: 0

                        onCurrentTextChanged: {
                            bp_controller.updateAutoZero(currentText)
                        }
                    }

                    SectionLabel{
                        text: "SAMPLES PER TRIGGER:"
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledTextField{
                        id: samplesPerTriggerField
                        enabled: bp_controller.canConfigureSettings
                        Layout.fillWidth: true
                        placeholderText: qsTr("Enter Samples Per Trigger")
                        bottomVal: 1
                        topVal: 50000

                        onEditingFinished: {
                            const addr = Number(text)
                            if (!isNaN(addr))
                                bp_controller.updateSamplesPerTrigger(addr)
                        }
                    }

                    SectionLabel{
                        text: "DISPLACEMENT PER SAMPLE (IN):"
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledComboBox{
                        id: displacementComboBox
                        enabled: bp_controller.canConfigureSettings
                        displayScaleFactor: root.displayScaleFactor
                        Layout.fillWidth: true

                        model: ["0.001", "0.005", "0.025", "0.1"]
                        currentIndex: 0

                        onCurrentTextChanged: {
                            bp_controller.updateDisplacementPerSample(currentText)
                        }
                    }

                    Rectangle{
                        width: parent.width
                        height: 5
                        color: root.windowColor
                    }

                    Label{
                        text: "MEASUREMENT CONTROL"
                        color: root.textColor
                        font.bold: true
                        font.pointSize: 12 * root.displayScaleFactor
                        font.capitalization: Font.AllUppercase
                        font.family: "Courier"
                    }

                    Rectangle{
                        Layout.preferredHeight: 1
                        Layout.fillWidth: true
                        color: root.textColor
                    }

                    StyledButton{
                        id: startMeasurementButton
                        enabled: !bp_controller.isMeasurementInProgress & bp_controller.isMultimeterConnected
                        displayScaleFactor: root.displayScaleFactor
                        displayText: "START MEASUREMENTS"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20 * root.displayScaleFactor
                        textColor: startMeasurementButton.enabled ? (startMeasurementButton.down ? root.textColor : root.confirmationColor) : root.hoverColor
                        backgroundColor: startMeasurementButton.pressed ? root.pressedConfirmationColor : (startMeasurementButton.enabled ? (startMeasurementButton.hovered ? root.hoverColor : root.windowColor) : root.windowColor)
                        borderColor: startMeasurementButton.enabled ? root.confirmationColor: root.hoverColor

                        onPressed: {
                            saveMeasurementFileDialog.open()
                        }

                        FileDialog {
                            id: saveMeasurementFileDialog
                            title: "Select Save Destination for Measurement"
                            fileMode: FileDialog.SaveFile
                            folder: defaultPaths["data"]
                            nameFilters: ["HDF5 File (*.hdf5)", "H5 File (*.h5)"]

                            onAccepted: {
                                bp_controller.beginMeasurement(saveMeasurementFileDialog.file.toString())
                            }
                        }
                    }

                    Rectangle{
                        width: parent.width
                        height: 2
                        color: root.windowColor
                    }

                    StyledButton{
                        id: triggerButton
                        enabled: bp_controller.isMeasurementInProgress
                        displayScaleFactor: root.displayScaleFactor
                        displayText: "TRIGGER MEASUREMENT"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20 * root.displayScaleFactor
                        textColor: triggerButton.enabled ? (triggerButton.down ? root.textColor : root.triggerColor) : root.hoverColor
                        backgroundColor: triggerButton.pressed ? root.pressedTriggerColor : (triggerButton.enabled ? (triggerButton.hovered ? root.hoverColor : root.windowColor) : root.windowColor)
                        borderColor: triggerButton.enabled ? root.pressedTriggerColor: root.hoverColor

                        onPressed: {
                            bp_controller.measurementTriggered()
                        }
                    }


                    Rectangle{
                        width: parent.width
                        height: 2
                        color: root.windowColor
                    }

                    StyledButton{
                        id: endMeasurementButton
                        enabled: bp_controller.isMeasurementInProgress
                        displayScaleFactor: root.displayScaleFactor
                        displayText: "END MEASUREMENT"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20 * root.displayScaleFactor
                        textColor: endMeasurementButton.enabled ? (endMeasurementButton.down ? root.textColor : root.negationColor) : root.hoverColor
                        backgroundColor: endMeasurementButton.pressed ? root.pressedNegationColor : (endMeasurementButton.enabled ? (endMeasurementButton.hovered ? root.hoverColor : root.windowColor) : root.windowColor)
                        borderColor: endMeasurementButton.enabled ? root.pressedNegationColor: root.hoverColor

                        onPressed: {
                            bp_controller.endMeasurement()
                        }
                    }

                    SectionLabel{
                        text: "GO TO MEASUREMENT ID:"
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StyledTextField{
                        id: measurementID
                        enabled: bp_controller.isMeasurementInProgress
                        Layout.fillWidth: true
                        placeholderText: qsTr("Enter Measurement ID")
                        bottomVal: 0
                        topVal: 1000

                        onEditingFinished: {
                            const current_id = Number(measurementID.text)
                            if (!isNaN(current_id))
                                bp_controller.updateDesiredMeasurementID(current_id)
                        }
                    }

                    StyledButton{
                        id: goToMeasurementButton
                        enabled: bp_controller.canGoToMeasurement
                        displayScaleFactor: root.displayScaleFactor
                        displayText: "GO TO"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20 * root.displayScaleFactor
                        textColor: goToMeasurementButton.enabled ? (goToMeasurementButton.down ? root.textColor : root.confirmationColor) : root.hoverColor
                        backgroundColor: goToMeasurementButton.pressed ? root.pressedConfirmationColor : (goToMeasurementButton.enabled ? (goToMeasurementButton.hovered ? root.hoverColor : root.windowColor) : root.windowColor)
                        borderColor: goToMeasurementButton.enabled ? root.confirmationColor : root.hoverColor

                        onPressed: {
                            bp_controller.goToMeasurement()
                        }
                    }

                    SectionLabel{
                        text: "CURRENT MEASUREMENT ID:"
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StatusDisplay{
                        displayText: bp_controller.currentMeasurementID
                        displayColor: root.triggerColor
                        Layout.fillWidth: true
                    }


                    SectionLabel{
                        text: "CURRENT DISPLACEMENT (IN):"
                        displayScaleFactor: root.displayScaleFactor
                    }

                    StatusDisplay{
                        displayText: bp_controller.currentDisplacement
                        displayColor: root.triggerColor
                        Layout.fillWidth: true
                    }

                    Rectangle{
                        width: parent.width
                        height: 1
                        color: root.windowColor
                    }

                    // Pushes everything above to the top
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
        }

        Rectangle{
            id: graph_block
            height: parent.height
            width: parent.width * 0.65
            anchors.right: parent.right
            color: root.windowColor

            TapHandler {
                onTapped: {
                    background.forceActiveFocus()
                }
            }

            WindowContainer {
                id: graphContainer
                anchors.fill: parent
                window: plotWindow
            }
        }
    }
}
