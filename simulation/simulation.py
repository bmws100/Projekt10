import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDoubleSpinBox, QFrame
)
from PyQt6.QtCore import QTimer, Qt
import pyqtgraph as pg

# Voreinstellung für die Graphen-Farben
pg.setConfigOption('foreground', 'k')


class TemperatureMonitor(QMainWindow):

    def __init__(self):
        super().__init__()

        # --- Menüleiste hinzufügen ---
        self._create_menu_bar()

        # --- Fenstereinstellungen ---
        self.setWindowTitle("Temperatur-Monitor mit Grenzwert-Alarm")
        self.setGeometry(100, 100, 800, 600)

        # --- Daten für den Plot ---
        self.time_data = []
        self.temp_data = []
        self.time_counter = 0

        # --- Layout und Widgets initialisieren ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # --- UI-Komponenten erstellen ---
        self._create_plot()
        self._create_controls()
        self._create_status_display()

        layout.addWidget(self.plot_widget)
        layout.addWidget(self.controls_frame)
        layout.addWidget(self.status_label)

        # --- Timer für die Echtzeit-Simulation ---
        self.simulation_timer = QTimer()
        self.simulation_timer.setInterval(200)  # Update alle 200 ms
        self.simulation_timer.timeout.connect(self.update_plot_data)

        # --- NEU: Timer für den Blink-Effekt ---
        self.blink_timer = QTimer()
        self.blink_timer.setInterval(400)  # Wechselt die Farbe alle 400ms
        self.blink_timer.timeout.connect(self._toggle_blink_color)
        self.is_blinking = False
        self.blink_color = 'w'
        self.blink_toggle_state = False

        # --- Verbindungen (Signale und Slots) herstellen ---
        self._connect_signals()

        # --- Initialer Zustand ---
        self.update_limit_lines()
        self.stop_simulation()

    def _create_menu_bar(self):
        menubar = self.menuBar()
        datei_menu = menubar.addMenu("Datei")
        datei_menu.addAction("Beenden", self.close)
        # Andere Menüpunkte sind zur Vereinfachung weggelassen

    def _create_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', "Temperatur (°C)")
        self.plot_widget.setLabel('bottom', "Zeit (s)")
        self.plot_widget.showGrid(x=True, y=True)
        pen = pg.mkPen(color=(0, 115, 189), width=2)
        self.data_line = self.plot_widget.plot(self.time_data, self.temp_data, pen=pen)
        self.upper_limit_line = pg.InfiniteLine(angle=0, movable=False,
                                                pen=pg.mkPen('r', style=Qt.PenStyle.DashLine, width=2))
        self.lower_limit_line = pg.InfiniteLine(angle=0, movable=False,
                                                pen=pg.mkPen('b', style=Qt.PenStyle.DashLine, width=2))
        self.plot_widget.addItem(self.upper_limit_line)
        self.plot_widget.addItem(self.lower_limit_line)

    def _create_controls(self):
        self.controls_frame = QFrame()
        controls_layout = QHBoxLayout(self.controls_frame)
        max_label = QLabel("Max-Temp (°C):")
        self.max_temp_input = QDoubleSpinBox()
        self.max_temp_input.setRange(-50.0, 150.0)
        self.max_temp_input.setValue(25.0)
        min_label = QLabel("Min-Temp (°C):")
        self.min_temp_input = QDoubleSpinBox()
        self.min_temp_input.setRange(-50.0, 150.0)
        self.min_temp_input.setValue(15.0)
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_out_button = QPushButton("Zoom Out")
        controls_layout.addWidget(min_label)
        controls_layout.addWidget(self.min_temp_input)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(max_label)
        controls_layout.addWidget(self.max_temp_input)
        controls_layout.addStretch()
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.zoom_in_button)
        controls_layout.addWidget(self.zoom_out_button)

    def _create_status_display(self):
        self.status_label = QLabel("Bereit. Simulation starten.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "background-color: lightgrey; color: black; font-size: 16px; padding: 5px; border-radius: 5px;")

    def _connect_signals(self):
        self.start_button.clicked.connect(self.start_simulation)
        self.stop_button.clicked.connect(self.stop_simulation)
        self.max_temp_input.valueChanged.connect(self.update_limit_lines)
        self.min_temp_input.valueChanged.connect(self.update_limit_lines)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)

    def start_simulation(self):
        self.simulation_timer.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # Status beim Start zurücksetzen
        self.status_label.setText("Simulation läuft...")
        self.status_label.setStyleSheet(
            "background-color: #A5D6A7; color: black; font-size: 16px; padding: 5px; border-radius: 5px;")

    def stop_simulation(self):
        self.simulation_timer.stop()
        # NEU: Blink-Timer ebenfalls stoppen
        if self.is_blinking:
            self.blink_timer.stop()
            self.is_blinking = False

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Simulation gestoppt.")
        self.status_label.setStyleSheet(
            "background-color: lightgrey; color: black; font-size: 16px; padding: 5px; border-radius: 5px;")
        self.plot_widget.setBackground('w')

    def update_plot_data(self):
        self.time_counter += self.simulation_timer.interval() / 1000.0
        noise = np.random.normal(0, 0.2)
        temperature = 20 + 8 * np.sin(self.time_counter * 0.5) + noise
        self.time_data.append(self.time_counter)
        self.temp_data.append(temperature)
        if len(self.time_data) > 100:
            self.time_data.pop(0)
            self.temp_data.pop(0)
        self.data_line.setData(self.time_data, self.temp_data)
        self.check_limits(temperature)

    def update_limit_lines(self):
        self.upper_limit_line.setPos(self.max_temp_input.value())
        self.lower_limit_line.setPos(self.min_temp_input.value())

    def check_limits(self, current_temp):
        max_limit = self.max_temp_input.value()
        min_limit = self.min_temp_input.value()

        if current_temp > max_limit:
            self.status_label.setText(f"ALARM: Max-Temperatur überschritten! ({current_temp:.2f}°C)")
            self.status_label.setStyleSheet(
                "background-color: #EF5350; color: white; font-size: 16px; padding: 5px; border-radius: 5px;")
            # NEU: Startet das Blinken, falls es nicht schon läuft
            if not self.is_blinking:
                self.is_blinking = True
                self.blink_color = '#FFCDD2'  # Hellrot
                self.blink_timer.start()

        elif current_temp < min_limit:
            self.status_label.setText(f"ALARM: Min-Temperatur unterschritten! ({current_temp:.2f}°C)")
            self.status_label.setStyleSheet(
                "background-color: #42A5F5; color: white; font-size: 16px; padding: 5px; border-radius: 5px;")
            # NEU: Startet das Blinken, falls es nicht schon läuft
            if not self.is_blinking:
                self.is_blinking = True
                self.blink_color = '#BBDEFB'  # Hellblau
                self.blink_timer.start()
        else:
            # NEU: Stoppt das Blinken, wenn der Zustand wieder normal ist
            if self.is_blinking:
                self.is_blinking = False
                self.blink_timer.stop()
                self.plot_widget.setBackground('w')  # Hintergrund sicherheitshalber zurücksetzen

            self.status_label.setText(f"In Ordnung ({current_temp:.2f}°C)")
            self.status_label.setStyleSheet(
                "background-color: #A5D6A7; color: black; font-size: 16px; padding: 5px; border-radius: 5px;")
            # Falls nicht geblinkt wird, stelle sicher, dass der Hintergrund weiß ist
            if not self.is_blinking:
                self.plot_widget.setBackground('w')

    # NEU: Diese Methode wird vom blink_timer aufgerufen
    def _toggle_blink_color(self):
        """Wechselt die Hintergrundfarbe des Plots für den Blink-Effekt."""
        if self.blink_toggle_state:
            self.plot_widget.setBackground('w')  # Wechsel zu Weiß
        else:
            self.plot_widget.setBackground(self.blink_color)  # Wechsel zur Alarmfarbe

        # Zustand für den nächsten Tick umkehren
        self.blink_toggle_state = not self.blink_toggle_state

    def zoom_in(self):
        self.plot_widget.getViewBox().scaleBy(y=0.8)

    def zoom_out(self):
        self.plot_widget.getViewBox().scaleBy(y=1.25)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = TemperatureMonitor()
    main_win.show()
    sys.exit(app.exec())