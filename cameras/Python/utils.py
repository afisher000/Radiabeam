# %%
# %%
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import serial
import re
import time

class Settings:
    def __init__(self, SN='', COM='', label='', ID='', calibration=None):
        # Camera inputs
        self.SN = SN
        self.COM = COM
        self.label = label
        self.ID = ID
        self.calibration = calibration
        
        # GUI parameters
        self.gain = 0
        self.exposure = 1000
        self.FWindex = 0
        return
    
class FilterWheel:
    def __init__(self, COM):
        self.testing = 1
        self.COM = COM
        self.baud_rate = 19200
        self.timeout = 5

        
        if not self.testing:
            # Test communication
            self.conn = serial.Serial(self.COM, self.baud_rate, timeout=self.timeout)
            self.conn.write(b'WSMODE\n')
            time.sleep(.1)
            try:
                response = self.conn.readline().decode().strip()
            except Exception as e:
                print(f'Could not get response from IFW driver: {e}')
                raise

            # Home filter wheel
            if response=="!":
                self.conn.write(b'WFILTR\n')
                time.sleep(.1)
                self.filterID = int(re.search(r'\d+', self.conn.readline().decode().strip()).group())
                time.sleep(.1)
                self.conn.write(b'WHOME\n')

    
    def move(self, FWindex):
        if not self.testing:
            # Move filter wheel
            self.conn.write(b'WFILTR\n')
            time.sleep(.2)
            self.conn.write(f'WGOTO{FWindex}\n'.encode())

    def close_conn(self):
        if not self.testing:
            self.conn.close()

    

def gaussian_with_offset(x, amplitude, mean, sigma, offset):
    return amplitude * np.exp(-((x-mean)**2)/(2*sigma**2)) + offset

def objective_function(params, x_data, y_data):
    amplitude, mean, sigma, offset = params
    y_model = gaussian_with_offset(x_data, amplitude, mean, sigma, offset)
    return np.sum((y_data - y_model) ** 2)  # Sum of squared differences

def fit_gaussian_with_offset(proj):
    # Initial guess for the parameters
    initial_guess = [np.max(proj)-np.min(proj), np.argmax(proj), 10, np.min(proj)]
    
    # Perform the curve fitting
    x = np.arange(len(proj))
    params, params_covariance = curve_fit(gaussian_with_offset, x, proj, p0=initial_guess)
    amplitude, mean, sigma, offset = params

    return amplitude, mean, sigma, offset

def computeQueueMean(queue):
    return 0 if len(queue)==0 else sum(queue)/len(queue)

# %%