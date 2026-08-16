# This Python file uses the following encoding: ascii
import sys
import time
import h5py
import serial
import numpy as np
import pyqtgraph as pg
from pathlib import Path
import serial.tools.list_ports
from datetime import datetime, timezone

from PySide6 import QtGui
from PySide6.QtCore import Qt, QObject, Signal, Slot, Property, QPoint, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QDialog, QPushButton, QApplication

class PathManager:
    def __init__(self):
        self.base_dir = self._get_base_dir()

        self.data_dir = self.base_dir / "data"

        self._ensure_directories()

    def _get_base_dir(self) -> Path:
        # Works in dev and frozen apps
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        return Path(__file__).resolve().parent

    def _ensure_directories(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def as_qml_urls(self) -> dict:
        return {
                    "data": QUrl.fromLocalFile(str(self.data_dir)),
                }

class ErrorDialog(QDialog):
    dialogClosed = Signal()

    def __init__(self, title, message, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.resize(400, 180)

        self.setStyleSheet("""
            QDialog {
                background-color: #111111;
                border: 1px solid #333333;
                border-radius: 8px;
            }

            QLabel {
                color: white;
                font: bold 12pt "Courier";
            }

            QPushButton {
                background-color: #111111;
                color: #2CFF05;
                border: 1px solid #2CFF05;
                border-radius: 8px;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #333333;
            }
        """)

        layout = QVBoxLayout(self)

        # Custom title bar
        title_bar = QLabel(title)
        title_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_bar)

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # Button
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

class ScatterPlot(QWidget):

    def __init__(self):
        super().__init__()

        # Init class variables
        self.last_hovered_id = None

        # Setting background color of graph
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #111111;")

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#111111")

        # Setting font settings for tick labels
        font = QtGui.QFont("Courier")
        font.setPixelSize(16)
        font.setBold(True)

        self.plot.getAxis("bottom").setStyle(tickFont=font)
        self.plot.getAxis("left").setStyle(tickFont=font)

        # Setting up axis labels
        self.plot.setLabel("bottom", "Displacement", units="In", **{"color": "#FFFFFF", "font-size": "16pt"})
        self.plot.setLabel("left", "Current", units="A", **{"color": "#FFFFFF", "font-size": "16pt"})

        self.scatter = pg.ScatterPlotItem(size=10, brush="#2CFF05")
        self.plot.addItem(self.scatter)

        self.data = []

        layout = QVBoxLayout()
        layout.addWidget(self.plot)
        self.setLayout(layout)

        # FIX 1: Create a persistent custom label overlay nested inside the plot canvas
        self.custom_tooltip = QLabel(self.plot)
        self.custom_tooltip.setFont(QtGui.QFont("Courier", 10, QtGui.QFont.Weight.Bold))
        # Style it to look exactly like a classic tooltip with a small padding buffer
        self.custom_tooltip.setStyleSheet("""
            QLabel {
                background-color: #222222;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 3px;
            }
        """)
        self.custom_tooltip.setAttribute(Qt.WA_TransparentForMouseEvents, True) # Clicks pass right through it
        self.custom_tooltip.hide()

        # Intercept mouse movements across the plot canvas scene
        self.plot.scene().sigMouseMoved.connect(self.on_mouse_moved)

    @Slot(int, float, float)
    def addMeasurement(self, measurement_id, x, y):
        self.data.append({
            "id": measurement_id,
            "x": x,
            "y": y
        })

        points = [
            {
                "pos": (d["x"], d["y"]),
                "data": d
            }
            for d in self.data
        ]

        self.scatter.setData(points)

    @Slot(int, float, float)
    def editMeasurement(self, measurement_id, x, y):
        self.data[measurement_id] = {
            "id": measurement_id,
            "x": x,
            "y": y
        }

        points = [
            {
                "pos": (d["x"], d["y"]),
                "data": d
            }
            for d in self.data
        ]

        self.scatter.setData(points)

    @Slot()
    def clearMeasurements(self):
        self.data = []
        self.scatter.setData(x=[], y=[])

    def on_mouse_moved(self, evt):
        pos = evt  # Local pixel position relative to the plot scene

        if self.plot.sceneBoundingRect().contains(pos):
            mouse_point = self.plot.getViewBox().mapSceneToView(pos)
            hovered_points = self.scatter.pointsAt(mouse_point)

            if len(hovered_points) > 0:
                point = hovered_points[0]
                measurement = point.data()
                current_id = measurement['id']

                # Even if it's the same point, we update the position so the box follows
                # the mouse smoothly across the point's target hit circle, but don't re-render text
                text = f"ID: {current_id}\n({measurement['x']:.6f}, {measurement['y']:.6f})"
                self.custom_tooltip.setText(text)

                # Align the label slightly offset (15 pixels down and right) from the local mouse pixel
                local_pos = self.plot.mapFromScene(pos)
                self.custom_tooltip.move(local_pos + QPoint(15, 15))

                self.custom_tooltip.show()
                self.last_hovered_id = current_id
                return

        # Clear tracking state and hide if the mouse moves into empty space
        if self.last_hovered_id is not None:
            self.last_hovered_id = None
            self.custom_tooltip.hide()

class HP_34401A_Interface():
    def __init__(self):
        self.port = None
        self.gpib_address = None
        self.hp_34401a = None

    def write(self, command):
        if not command.endswith('\n'):
            command += '\n'

        self.hp_34401a.write(command.encode('ascii'))
        return

    def query(self, command):
        self.write(command)
        self.write('++read eoi')
        return self.hp_34401a.readline().decode('ascii').strip()

    def connect_instrument(self, gpib_address, port, baud_rate):
        self.port = port
        self.gpib_address = gpib_address
        gpib_cmd_str = f'++addr {gpib_address}'

        self.hp_34401a = serial.Serial(port, baudrate = baud_rate, timeout = 2)

        self.write('++mode 1')
        self.write(gpib_cmd_str)
        self.write('++auto 0')

        # 3. Clear any old errors on the instrument
        self.clear_event_register()

        # 4. Get Identity of Instrument
        response = self.query('*IDN?')

        if response:
            if 'HEWLETT-PACKARD,34401A' in response:
                self.beep()
                return True
            else:
                return False
        else:
            return False

    def reset_multimeter_to_startup_state(self):
        self.write('*RST')
        status = self.query('*OPC?').replace('\x00', '')

        if status == '1':
            return True
        else:
            return False

    def check_for_errors(self):
        error_status = self.query('SYST:ERR?').replace('\x00', '')
        return error_status

    def clear_event_register(self):
        self.write('*CLS')
        return

    def run_self_test(self):
        result = self.query('*TST?').replace('\x00', '')
        return result

    def beep(self):
        self.write('SYST:BEEP') # --> Make HP 34401A Beep
        return

    def log_current_status_to_display(self, message):
        formatted_message = message.upper()

        if len(formatted_message) > 12:
            formatted_message = formatted_message[0:12]

        self.write('SYST:BEEP') # --> Make HP 34401A Beep
        self.write(f'DISP:TEXT "{formatted_message}"') # --> Writes a message to the front panel display
        return

    def clear_message(self):
        self.write('DISP:TEXT:CLE') # --> Deletes the message from the front panel display

    def configure_dc_current_measurements(self, isAutoRange = True, isAutoZero = True, sampleCounts = 1, integrationTime = 10, currentRange = None):
        self.write('FUNC "CURR:DC"')
        self.write(f'CURR:DC:NPLC {integrationTime}') # Changes Integration Time Options are 0.02, 0.2, 1, 10, 100

        if isAutoRange:
            self.write('CURR:DC:RANG:AUTO ON') # --> Let multimeter automatically determine range of current and resolution based on input
        else:
            if currentRange is None or integrationTime is None:
                print('Failure, current range or integration time not set')
                return

            self.write(f'CURR:DC:RANG {currentRange}') # --> Range of current measurements expected

        # Changes the Autozero functionality. Autozero removes internal current offsets due to temperature fluctuations. It measures an internal baseline 'zero' current and subtracts the offset from 0 to your measurements.
        if isAutoZero:
            self.write('SENS:ZERO:AUTO ON')
        else:
            self.write('SENS:ZERO:AUTO ON')

        self.write(f'SAMP:COUN {sampleCounts}') # --> For reading multiple measurements per trigger (Can average)
        self.write('TRIG:SOUR IMM') # --> Trigger source comes internally from multimeter when measurement requested
        self.write('TRIG:DEL:AUTO ON') # --> Set No Trigger Delay
        return

    def take_measurement(self, samples_per_trigger):
        self.write('*CLS') # Clear any old errors unrelated to the current measurement
        self.write('*ESE 1') # Tell multimeter to flip bit 5 in the serial poll when all following commands are completed up to an '*OPC' command

        # Ensure that the previous commands have been read to ensure that a bit will flip when all following commands are completed
        status = self.query('*OPC?').replace('\x00', '')
        if status != '1':
            return None

        self.write('INIT') # Takes measurement and asks multimeter to store it in its local memory
        self.write('*OPC')

        # Start a timer. If the time for a measurement takes too long we can abort
        timeout_start = time.time()

        # This loop checks if Bit 5 on the status poll has been flipped
        while True:
            # Tell the Prologix adapter to run an IEEE-488 serial poll on address 22
            # (Replace '++spoll' with your specific adapter's poll command if different)
            self.write(f'++spoll {self.gpib_address}')

            # Read the single byte result back from the adapter
            poll_reply = self.hp_34401a.readline().decode('ascii').strip()

            if poll_reply.isdigit():
                status_byte = int(poll_reply)

                # Check if Bit 5 (decimal value 32) is flipped
                if status_byte & 32:
                    break  # Measurement finished so we exit the loop.

            # Assume each measurement takes 1 second max so if the time exceeds the number of samples then we quit
            if time.time() - timeout_start > samples_per_trigger:
                print("Error: HPIB Serial Poll Timeout.")
                return None

            time.sleep(0.05) # Keep the serial line happy

        # Measurements have been completed so read multimeter memory
        read_msg = self.query('FETCH?').replace('\x00', '') # Sends results from multimeter memory to computer through the GPIB Bus

        if read_msg == '':
            return None

        if samples_per_trigger == 1:
            result = float(read_msg)
            return result
        else:
            all_msgs = read_msg.split(',')
            print(all_msgs)
            if '' in all_msgs:
                return None

            results = np.array(all_msgs, dtype = float)
            averaged_result = np.mean(results)
            return averaged_result

class Beam_Profiler_Interface(QObject):
    comPortListChanged = Signal()
    canConnectMultimeterChanged = Signal()
    isMultimeterConnectedChanged = Signal()
    canConfigureSettingsChanged = Signal()
    isMeasurementInProgressChanged = Signal()
    canGoToMeasurementChanged = Signal()
    currentMeasurementIdChanged = Signal()
    currentDisplacementChanged = Signal()
    measurementCompleted = Signal(int, float, float)
    measurementEdited = Signal(int, float, float)
    clearPlot = Signal()

    def __init__(self):
        super().__init__()

        self.h5file = None
        self.displacements_dataset = None
        self.current_dataset = None
        self.timestamp_dataset = None

        self.error_dialog = None
        self.start_time = None

        self.current_com_port = None
        self.gpib_address = None
        self.baud_rate = None

        self.current_range = None
        self.integration_time = None
        self.displacement_per_sample = None

        self.is_usb_port = False
        self.can_connect_multimeter = False
        self.is_multimeter_connected = False
        self.can_configure_settings = False
        self.is_measurement_in_progress = False
        self.can_go_to_measurement = False

        self.is_auto_range = True
        self.is_auto_zero = True

        self.samples_per_trigger = 1

        self.current_measurement_id = 0
        self.desired_measurement_id = 0
        self.max_measurement_id = 0

        self.current_displacement = 0
        self.max_displacement = 0

        self.current_displacement_str = '0.000 Inches'

        self.multimeter = HP_34401A_Interface()
        self.find_com_ports()

        return

    def find_com_ports(self):
        ports = serial.tools.list_ports.comports()

        if not ports:
            self.is_usb_port = False
            self.com_port_list = ['No USB Ports Found']
        else:
            valid_ports = []
            for port in ports:
                if 'USB' in port.description:
                    valid_ports.append(port.device)

            if len(valid_ports) == 0:
                self.is_usb_port = True
                self.com_port_list = ['No USB Ports Found']
            else:
                self.is_usb_port = True
                self.com_port_list = valid_ports
        self.comPortListChanged.emit()
        return

    def open_h5_file(self, qt_file_path):
        url = QUrl(qt_file_path)
        file_path = ""
        if url.isValid():
            file_path = url.toLocalFile()
        else:
            self.error_dialog = ErrorDialog("File Error", "Error, File Path Not Valid")
            self.error_dialog.show()
            return False

        # Ensure correct extension
        if not file_path.endswith(".hdf5"):
            file_path += ".hdf5"

        # Open hdf5 file
        self.h5file = h5py.File(file_path, "w")

        # Set attributes relavent to current experiment
        ### Configured Multimeter Settings ###
        self.h5file.attrs["current_measurement_range (A)"] = self.current_range
        self.h5file.attrs["integration_time (PLCs)"] = self.integration_time
        self.h5file.attrs["is_auto_range"] = self.is_auto_range
        self.h5file.attrs["is_auto_zero"] = self.is_auto_zero
        self.h5file.attrs["samples_per_trigger"] = self.samples_per_trigger
        self.h5file.attrs["displacement_per_sample (In)"] = self.displacement_per_sample

        # Get the experiment start time
        start_date_utc, start_time_utc = datetime.now(timezone.utc).isoformat().split('T')
        start_date_local, start_time_local = datetime.now().astimezone().isoformat().split('T')

        ### Date-Time Attributes ###
        self.h5file.attrs["utc_experiment_start_date"] = start_date_utc
        self.h5file.attrs["utc_experiment_start_time"] = start_time_utc

        self.h5file.attrs["local_experiment_start_date"] = start_date_local
        self.h5file.attrs["local_experiment_start_time"] = start_time_local
        self.h5file.attrs["local_timezone"] = datetime.now().astimezone().tzname()

        self.displacements_dataset = self.h5file.create_dataset("displacement (In)",shape=(0,),maxshape=(None,),dtype=np.float64, chunks=True)
        self.current_dataset = self.h5file.create_dataset("current (A)",shape=(0,),maxshape=(None,),dtype=np.float64, chunks=True)
        self.timestamp_dataset = self.h5file.create_dataset("timestampe (s)",shape=(0,),maxshape=(None,),dtype=np.float64, chunks=True)
        return True

    def write_measurement(self, measurement_id, displacement, current):
        i = measurement_id

        self.displacements_dataset.resize((i+1,))
        self.current_dataset.resize((i+1,))
        self.timestamp_dataset.resize((i+1,))

        self.displacements_dataset[i] = displacement
        self.current_dataset[i] = current

        if measurement_id == 0:
            self.start_time = time.perf_counter()
            self.timestamp_dataset[i] = 0
        else:
            self.timestamp_dataset[i] = time.perf_counter() - self.start_time

        self.h5file.flush()
        return

    def edit_written_measurement(self, measurement_id, displacement, current):
        self.displacements_dataset[measurement_id] = displacement
        self.current_dataset[measurement_id] = current

        if measurement_id == 0 and self.max_measurement_id == 1:
            self.start_time = time.perf_counter()
            self.timestamp_dataset[measurement_id] = 0
        else:
            self.timestamp_dataset[measurement_id] = time.perf_counter() - self.start_time
        return

    def close_h5_file(self):
        # Ensure file exists
        if self.h5file is not None:

            ### Final Sample Attributes ###
            self.h5file.attrs["num_samples"] = self.max_measurement_id
            self.h5file.attrs["full_displacement (In)"] = self.max_displacement - self.displacement_per_sample

            # Get the experiment end time
            end_date_utc, end_time_utc = datetime.now(timezone.utc).isoformat().split('T')
            end_date_local, end_time_local = datetime.now().astimezone().isoformat().split('T')

            ### Date-Time Attributes ###
            self.h5file.attrs["utc_experiment_end_date"] = end_date_utc
            self.h5file.attrs["utc_experiment_end_time"] = end_time_utc

            self.h5file.attrs["local_experiment_end_date"] = end_date_local
            self.h5file.attrs["local_experiment_end_time"] = end_time_local

            ### Acquisition Completion Attribute ###
            self.h5file.attrs["acquisition_complete"] = True

            self.h5file.close()
            self.h5file = None
            self.displacements_dataset = None
            self.current_dataset = None
            self.timestamp_dataset = None
            return

    @Property(list, notify = comPortListChanged)
    def comPortList(self):
        return self.com_port_list

    @Property(bool, notify = canConnectMultimeterChanged)
    def canConnectMultimeter(self):
        return self.can_connect_multimeter

    @Property(bool, notify = isMultimeterConnectedChanged)
    def isMultimeterConnected(self):
        return self.is_multimeter_connected

    @Property(bool, notify = canConfigureSettingsChanged)
    def canConfigureSettings(self):
        return self.can_configure_settings

    @Property(bool, notify = isMeasurementInProgressChanged)
    def isMeasurementInProgress(self):
        return self.is_measurement_in_progress

    @Property(str, notify = currentMeasurementIdChanged)
    def currentMeasurementID(self):
        return str(self.current_measurement_id)

    @Property(str, notify = currentDisplacementChanged)
    def currentDisplacement(self):
        return self.current_displacement_str

    @Property(bool, notify = canGoToMeasurementChanged)
    def canGoToMeasurement(self):
        return self.can_go_to_measurement

    @Slot(str)
    def updateComPort(self, comPort):
        self.current_com_port = comPort

        if self.current_com_port is not None and self.gpib_address is not None and self.baud_rate is not None:
            self.can_connect_multimeter = True
            self.canConnectMultimeterChanged.emit()

        return

    @Slot(str)
    def updateBaudRate(self, baud_rate):
        self.baud_rate = int(baud_rate)

        if self.current_com_port is not None and self.gpib_address is not None and self.baud_rate is not None:
            self.can_connect_multimeter = True
            self.canConnectMultimeterChanged.emit()

        return

    @Slot(int)
    def updateGpibAddress(self, gpib_address):
        self.gpib_address = gpib_address

        if self.current_com_port is not None and self.gpib_address is not None and self.baud_rate is not None:
            self.can_connect_multimeter = True
            self.canConnectMultimeterChanged.emit()

        return

    @Slot()
    def connectMultimeter(self):
        self.is_multimeter_connected = self.multimeter.connect_instrument(self.gpib_address, self.current_com_port, self.baud_rate)
        self.isMultimeterConnectedChanged.emit()

        if self.is_multimeter_connected:
            self.can_configure_settings = True
            self.canConfigureSettingsChanged.emit()

            self.can_connect_multimeter = False
            self.canConnectMultimeterChanged.emit()
        else:
            self.error_dialog = ErrorDialog("Connnection Error", "Failed to Connect to Multimeter")
            self.error_dialog.show()

        return

    @Slot(str)
    def updateCurrentRange(self, current_range):
        print("Current Range: ", current_range)
        self.current_range = current_range

        if current_range == 'AUTO':
            self.is_auto_range = True

        return

    @Slot(str)
    def updateIntegrationTime(self, integration_time):
        print("Integration Time: ", integration_time)
        self.integration_time = integration_time
        return

    @Slot(str)
    def updateAutoZero(self, auto_zero_status):
        print("Auto-Zero Status: ", auto_zero_status)
        if auto_zero_status == 'On':
            self.is_auto_zero = True
        elif auto_zero_status == 'Off':
            self.is_auto_zero = False
        return

    @Slot(int)
    def updateSamplesPerTrigger(self, samples_per_trigger):
        print("Samples Per Trigger: ", samples_per_trigger)
        self.samples_per_trigger = samples_per_trigger
        return

    @Slot(str)
    def updateDisplacementPerSample(self, displacement_per_sample):
        print("Displacement Per Sample: ", displacement_per_sample)
        self.displacement_per_sample = float(displacement_per_sample)
        return

    @Slot(str)
    def beginMeasurement(self, qt_file_path):

        self.multimeter.configure_dc_current_measurements(self.is_auto_range, self.is_auto_zero, self.samples_per_trigger, self.integration_time, self.current_range)
        error_status = self.multimeter.check_for_errors()

        if error_status == '+0,"No error"':
            is_file_path_valid = self.open_h5_file(qt_file_path)

            if is_file_path_valid:
                self.clearPlot.emit()

                self.current_measurement_id = 0
                self.max_measurement_id = 0

                self.current_displacement = 0
                self.max_displacement = 0
                self.current_displacement_str = f'{self.current_displacement:.3f} Inches'

                self.can_configure_settings = False
                self.canConfigureSettingsChanged.emit()

                self.is_measurement_in_progress = True
                self.isMeasurementInProgressChanged.emit()

                self.multimeter.beep()
        else:
            self.error_dialog = ErrorDialog("Configuration Error", error_status)
            self.error_dialog.show()
        return

    @Slot()
    def measurementTriggered(self):
        current = self.multimeter.take_measurement(self.samples_per_trigger)
        error_status = self.multimeter.check_for_errors()

        if error_status == '+0,"No error"' and current is not None:
            if self.current_measurement_id == self.max_measurement_id:
                self.write_measurement(self.current_measurement_id, self.current_displacement, current)
                self.measurementCompleted.emit(self.current_measurement_id, self.current_displacement, current)

                self.current_measurement_id += 1
                self.max_measurement_id += 1

                self.current_displacement += self.displacement_per_sample
                self.max_displacement += self.displacement_per_sample
            else:
                self.edit_written_measurement(self.current_measurement_id, self.current_displacement, current)
                self.measurementEdited.emit(self.current_measurement_id, self.current_displacement, current)

                self.current_measurement_id = self.max_measurement_id
                self.current_displacement = self.max_displacement

            self.currentMeasurementIdChanged.emit()

            self.current_displacement_str = f'{self.current_displacement:.3f} Inches'
            self.currentDisplacementChanged.emit()

            self.multimeter.beep()
        elif current is None:
            self.multimeter.clear_event_register()
            self.error_dialog = ErrorDialog("Measurement Error", "No Reading Returned from Multimeter")
            self.error_dialog.show()
        else:
            self.error_dialog = ErrorDialog("Measurement Error", error_status)
            self.error_dialog.show()
        return

    @Slot()
    def endMeasurement(self):
        self.close_h5_file()

        self.can_go_to_measurement = False
        self.canGoToMeasurementChanged.emit()

        self.is_measurement_in_progress = False
        self.isMeasurementInProgressChanged.emit()

        self.can_configure_settings = True
        self.canConfigureSettingsChanged.emit()

        self.multimeter.beep()
        return

    @Slot(int)
    def updateDesiredMeasurementID(self, measurement_id):
        self.desired_measurement_id = measurement_id
        self.can_go_to_measurement = True
        self.canGoToMeasurementChanged.emit()
        return

    @Slot()
    def goToMeasurement(self):
        if (self.desired_measurement_id <= self.max_measurement_id) and (self.desired_measurement_id > 0):
            self.error_dialog = ErrorDialog("Measurement ID Error", "Please enter a valid measurement id")
            self.error_dialog.show()
            return

        self.current_measurement_id = self.desired_measurement_id
        self.currentMeasurementIdChanged.emit()

        self.current_displacement = self.current_measurement_id * self.displacement_per_sample
        self.current_displacement_str = f'{self.current_displacement:.3f} Inches'
        self.currentDisplacementChanged.emit()
        return

if __name__ == "__main__":
    # Set the Style
    QQuickStyle.setStyle("Fusion")

    # Instantiations
    app = QApplication(sys.argv)

    beam_profiler_controller = Beam_Profiler_Interface()
    default_paths = PathManager()

    scatterPlot = ScatterPlot()
    scatterPlot.setWindowTitle("Plot")
    scatterPlot.show()

    plot_window = scatterPlot.windowHandle()

    # Setting up the UI Engine
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bp_controller", beam_profiler_controller)
    engine.rootContext().setContextProperty("defaultPaths", default_paths.as_qml_urls())
    engine.rootContext().setContextProperty("plotWindow", plot_window)

    # Set up connections between controller and plot
    beam_profiler_controller.measurementCompleted.connect(scatterPlot.addMeasurement)
    beam_profiler_controller.measurementEdited.connect(scatterPlot.editMeasurement)
    beam_profiler_controller.clearPlot.connect(scatterPlot.clearMeasurements)

    # Run the engine
    qml_file = Path(__file__).resolve().parent / "main.qml"
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())
