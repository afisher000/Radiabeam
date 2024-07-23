# %%
# %%
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import serial
import re
import time
from epics import caput, caget

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
    
    def get_setpoint(self):
        current = caget(self.label + '_Current_RB')
        # print(f'{self.label} current: {current}')
        return current
    
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