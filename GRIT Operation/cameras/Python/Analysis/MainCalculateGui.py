import sys
import numpy as np

from PyQt6.QtWidgets import QApplication, QLineEdit
from PyQt6 import uic

from steering_energy_measurement import steering_energy_measurement

# GUI Window Class
mw_Ui, mw_Base = uic.loadUiType('CalculateWindow.ui')
class MainWindow(mw_Base, mw_Ui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Connect the Calculate button to the function
        self.calculateButton.clicked.connect(self.calculate)
        
    def format_output(self, value):
        # Define the threshold value
        threshold = 10000.0
        formatted_value = f"{value:.2e}" if abs(value)>threshold else f"{value:.2f}"
        return formatted_value

    def calculate(self):
        # Retrieve values from line edits and convert them to float
        try:
            # Extract numerical values and convert to float
            self.dx = float(self.dxLineEdit.text())
            self.dz = float(self.dzLineEdit.text())
            self.current = float(self.currentLineEdit.text())  # Handle new line edit value
        except ValueError:
            self.dx = 0.0
            self.dz = 0.0
            self.current = 0.0
        
        # Perform the calculation (replace with your actual calculation logic)
        result = steering_energy_measurement(self.dx, self.dz, self.current)  # Updated to include current
        
        # Format the result using the format_output function
        formatted_result = self.format_output(result)
        
        # Display the formatted result in the output line edit
        if result is not None:
            self.outputLineEdit.setText(f"{formatted_result} MeV")
        else:
            self.outputLineEdit.setText("Error")

# Run Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()