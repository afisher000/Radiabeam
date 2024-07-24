# %%
# %%
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import serial
import re
import time
from epics import caput, caget

from PyQt6.QtCore import QThread, pyqtSignal
from vimba import Vimba


class FilterWheel:
    def __init__(self, COM):
        self.testing = False
        self.COM = COM
        self.baud_rate = 19200
        self.timeout = 5

        
        if not self.testing and self.COM:
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
        if not self.testing and self.COM:
            # Move filter wheel
            self.conn.write(b'WFILTR\n')
            time.sleep(.2)
            self.conn.write(f'WGOTO{FWindex}\n'.encode())

    def close_conn(self):
        if not self.testing and self.COM:
            self.conn.close()


class ImageAcquisition(QThread):
    image_ready = pyqtSignal(list)

    def __init__(self, ID):
        super().__init__()
        self.acquiring = False
        self.ID = ID
        self.gain = 0

    def run(self):
        print(f'Starting Cam {self.ID}')

        self.acquiring = True
        with Vimba.get_instance() as system:
            with system.get_camera_by_id(self.ID) as cam:
                while self.acquiring:
                    cam.get_feature_by_name('Gain').set(self.gain)

                    frame = cam.get_frame()
                    image = frame.as_numpy_ndarray()
                    self.image_ready.emit([image])

    def stop(self):
        print(f'Stopping Cam {self.ID}')
        self.acquiring = False
        self.wait() #wait for thread to stop

    def set(self, attribute, value):
        setattr(self, attribute, value)


class SteeringMagnets:
    def __init__(self):
        self.X1 = SteeringMagnet('BUN1_STM01_X')
        self.Y1 = SteeringMagnet('BUN1_STM01_Y')
        self.X2 = SteeringMagnet('BUN1_STM02_X')
        self.Y2 = SteeringMagnet('BUN1_STM02_Y')
        self.X3 = SteeringMagnet('BUN1_STM03_X')
        self.Y3 = SteeringMagnet('BUN1_STM03_Y')
        self.X4 = SteeringMagnet('BUN1_STM04_X')
        self.Y4 = SteeringMagnet('BUN1_STM04_Y')

class SteeringMagnet:
    def __init__(self, label):
        self.label = label

    def get_status(self):
        status = caget(self.label + '_SupplyOn_RB')
        # print(f'{self.label} status: {status}')
        return status
    
    def get_current(self):
        current = caget(self.label + '_Current_RB')
        # print(f'{self.label} current: {current}')
        return current
    
    def set_current(self, current):
        if abs(current)>4:
            raise ValueError('Max current limit is 4 amps')
        
        caput(self.label+'_Setpoint_SET', current)
        caput(self.label+'_Apply_SET.PROC', 1)
        time.sleep(.1)
        caput(self.label+'_Apply_SET.PROC', 1)

    
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