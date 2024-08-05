import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QLineEdit
from PyQt6 import uic

def steering_energy_measurement(dx, dz, current):
    ## Theory
    # Circular motion: qe * c0 * B = gamma * me * c0^2 / R
    # Arc length: L = R * theta  where  theta = dx/dz
    # Solve for gamma where L*B = LBoverA * current

    ## Calculation
    # Steering Magnet calibration
    dx=dx/1000
    LBoverA = 169*1e-4*1e-2 # Gauss*cm/A converted to Tesla*m/A

    ## Physical Constants
    qe      = 1.602e-19
    me      = 9.109e-31
    c0      = 299792458

    ## Angular deflection 
    theta   = dx/dz

    ## Output
    gamma   = (qe/me/c0) * (LBoverA) * current/theta
    beam_energy = gamma*0.511
    return beam_energy



# GUI Window Class
mw_Ui, mw_Base = uic.loadUiType('CalculateWindow.ui')
class MainWindow(mw_Base, mw_Ui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Connect signals and slots
        self.calculateButton.clicked.connect(self.calculate)

        
    def format_output(self, value):
        # Define the threshold value
        threshold = 10000.0
        formatted_value = f"{value:.2e} MeV" if abs(value)>threshold else f"{value:.2f} MeV"
        return formatted_value

    def calculate(self):
        # Read from lineEdits
        try:
            dx = float(self.dxLineEdit.text())
            dz = float(self.dzLineEdit.text())
            current = float(self.currentLineEdit.text())
        except ValueError:
            dx = 0.0
            dz = 0.0
            current = 0.0
        
        # Perform the calculation
        result = steering_energy_measurement(dx, dz, current)
                
        # Format and display result
        if result:
            self.outputLineEdit.setText(self.format_output(result))
        else:
            self.outputLineEdit.setText("Error")


# Run Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()