# %%
# %%
import numpy as np
from scipy.optimize import curve_fit
import serial
import re
import time
from epics import caput, caget
from PyQt6.QtCore import QThread, pyqtSignal
from vimba import Vimba

class FilterWheel:
    def __init__(self, COM, TESTING):
        self.TESTING = TESTING
        self.COM = COM if COM!='None' else None
        self.baud_rate = 19200
        self.timeout = 5

        
        if not self.TESTING and self.COM:
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
        if not self.TESTING and self.COM:
            # Move filter wheel
            self.conn.write(b'WFILTR\n')
            time.sleep(.2)
            self.conn.write(f'WGOTO{FWindex}\n'.encode())

    def closeConnection(self):
        if not self.TESTING and self.COM:
            self.conn.close()


class Camera(QThread):
    image_ready = pyqtSignal(list)

    def __init__(self, ID, TESTING):
        super().__init__()
        self.TESTING = TESTING
        self.acquiring = False
        self.ID = ID
        self.gain = 0
        self.exposure = 1000
        self.acqMode = 'FreeRun'

    def run(self):
        self.acquiring = True
        print(f'Starting Cam {self.ID}')

        if self.TESTING:
            # Generate 2d gaussian image
            while self.acquiring:
                width = 1280
                height = 1024                
                X, Y = np.meshgrid( np.arange(width), np.arange(height))
                xc, yc = np.array([height//2, width//2]) + 0*100*np.random.random(2)
                xrms, yrms = np.array([20,20]) + 0*2*np.random.random(2)
                image = (10 + 1.5**self.gain) * np.exp(-((X - xc)**2 / (2 * xrms**2) + (Y - yc)**2 / (2 * yrms**2)))
                image += 5*np.random.random(image.shape)
                image = np.clip(image, 0, 255)
                self.image_ready.emit([image.astype(np.uint8)])
                time.sleep(.2)

        else:
            # Actual data images
            with Vimba.get_instance() as system:
                with system.get_camera_by_id(self.ID) as cam:
                    cam.get_feature_by_name('TriggerSource').set('Line1')  # or 'Software' if you want to trigger via software

                    # Camera properties can only be changed within a "with" statement.
                    while self.acquiring:

                        # Set features
                        cam.get_feature_by_name('Gain').set(self.gain)
                        cam.get_feature_by_name('ExposureTimeAbs').set(self.exposure)
                        if self.acqMode == 'FreeRun':
                            cam.get_feature_by_name('TriggerMode').set('Off')
                            time.sleep(.2)
                        elif self.acqMode == 'Triggered':
                            cam.get_feature_by_name('TriggerMode').set('On')

                        # Get image and send to maingui 
                        frame = cam.get_frame()
                        image = frame.as_numpy_ndarray()
                        self.image_ready.emit([image])


    def stop(self):
        print(f'Stopping Cam {self.ID}')
        self.acquiring = False
        self.wait() #wait for thread to stop

    def set(self, attribute, value):
        setattr(self, attribute, value)
        print(f'Set {attribute} to {value}')


class SteeringMagnets:
    def __init__(self, TESTING):
        if TESTING:
            self.X1 = SteeringMagnetEmpty()
            self.Y1 = SteeringMagnetEmpty()
            self.X2 = SteeringMagnetEmpty()
            self.Y2 = SteeringMagnetEmpty()
            self.X3 = SteeringMagnetEmpty()
            self.Y3 = SteeringMagnetEmpty()
            self.X4 = SteeringMagnetEmpty()
            self.Y4 = SteeringMagnetEmpty()
        else:
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

    def setStatus(self):
        status = caget(self.label + '_SupplyOn_RB')
        return status
    
    def getCurrent(self):
        current = caget(self.label + '_Current_RB')
        return current
    
    def setCurrent(self, current):
        if abs(current)>4:
            raise ValueError('Max current limit is 4 amps')
        else:
            caput(self.label+'_Setpoint_SET', current)
            caput(self.label+'_Apply_SET.PROC', 1)
            time.sleep(.1)
            caput(self.label+'_Apply_SET.PROC', 1)


class SteeringMagnetEmpty:
    def getStatus(self):
        return 0
    def getCurrent(self):
        return 0
    def setCurrent(self):
        return

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
        self.filter_index = 0
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
    try:
        x = np.arange(len(proj))
        lbs = [0, 0, 0, 0]
        ubs = [np.max(proj), len(proj), len(proj)/2, np.max(proj)]
        maxfev = 1000
        params, _ = curve_fit(gaussian_with_offset, x, proj, p0=initial_guess, bounds=(lbs, ubs), maxfev=maxfev)
        return params #amplitude, mean, sigma, offset
    except:
        return (0, 0, 0, 0)

def computeQueueMean(queue):
    return 0 if len(queue)==0 else sum(queue)/len(queue)

# %%