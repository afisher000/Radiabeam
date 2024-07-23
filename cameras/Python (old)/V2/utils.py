# %%
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import serial
import re
import time

class CameraSettings:
    def __init__(self, SN='', COM='', label=''):
        # Camera inputs
        self.SN = SN
        self.COM = COM
        self.label = label
        
        # GUI parameters
        self.gain = 0
        self.exposure = 1000
        self.FWindex = 0
        return
    
class FilterWheel:
    def __init__(self, COM):
        self.COM = COM
        self.baud_rate = 19200
        self.timeout = 5

        self.conn = serial.Serial(self.COM, self.baud_rate, timeout=self.timeout)
        
        # Test communication
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
            self.filterID = int(re.search(r'\d+', self.conn.readline().decode().strip()).group)
            time.sleep(.1)
            self.conn.write(b'WHOME\n')

    
    def move(self, FWindex):
        # Move filter wheel
        self.conn.write(b'WFILTR\n')
        time.sleep(.2)
        self.conn.write(f'WGOTO{FWindex}\n'.encode())

    def close_conn(self):
        self.conn.close()

    
class VimbaCamera:
    # For TESTING
    def __init__(self, SN):
        self.SN = SN
        
    def open(self):
        pass

    def close(self):
        pass
    


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
