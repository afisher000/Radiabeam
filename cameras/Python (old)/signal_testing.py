import sys
import time
import random
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton
from PyQt6.QtCore import pyqtSignal, QThread, QTimer

class MainWindow(QMainWindow):
    # Signals
    random_number_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.initUI()

        # Define raster scan and signals/slots
        self.raster_scan = RasterScan()
        self.random_number_signal.connect(self.raster_scan.handle_random_number)
        self.raster_scan.progress.connect(self.handle_progress)

        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_random_number)

    def initUI(self):
        self.button = QPushButton('Start Scan', self)
        self.button.clicked.connect(self.on_button_click)
        self.setCentralWidget(self.button)

    def on_button_click(self):
        self.raster_scan.start()        
        self.timer.start(1000)  # Start the timer to generate random numbers every second

    def generate_random_number(self):
        random_number = random.randint(0, 100)  # Generate a random number
        self.random_number_signal.emit(random_number)  # Emit the signal with the random number

    def handle_progress(self, value):
        if value>=0:
            print(f"Progress: {value}%")
        else:
            self.timer.stop()


class RasterScan(QThread):
    progress = pyqtSignal(int)  # Signal to communicate progress

    def __init__(self):
        super().__init__()
        self.number = None

    def run(self):
        # Simulate a long-running scan operation
        for i in range(100):
            time.sleep(0.1)  # Simulate work
            self.progress.emit(i)  # Update progress
        self.progress.emit(-1) #End signal

    def handle_random_number(self, number):
        self.number = number
        print(f"Received random number: {number}")


# Application execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
