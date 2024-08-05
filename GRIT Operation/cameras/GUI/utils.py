# %%
# %%
import numpy as np
from scipy.optimize import curve_fit
import serial
import re
import time
from epics import caput, caget, caget_many
from PyQt6.QtCore import QThread, pyqtSignal
# from vimba import Vimba



def definePVs():
    # Define pvs to read from epics
    pvs = {
        'gunphase':'LLRF_AWG1_CH1_PhaseMan_SP',
        'linacphase':'LLRF_AWG1_CH2_PhaseMan_SP',
        }

    # Loop over steerings
    for num in [1,2,3,4]:
        for coord in ['X', 'Y']:
            pvs[f'{coord}{num}'] = f'BUN1_STM0{num}_{coord}_Current_RB'
    return pvs

def getEpicsData(pvs, TESTING):
    # Read values of epics PVs
    short_names = list(pvs.keys())
    long_names = list(pvs.values())

    values = caget_many(long_names) if not TESTING else np.zeros(len(long_names))
    return dict(zip(short_names, values))

class ICT(QThread):
    charge_ready = pyqtSignal(float)

    def __init__(self, TESTING):
        super().__init__()
        self.delay = 0.5
        self.acquiring = True
        self.TESTING = TESTING

        
    def run(self):
        if self.TESTING:
            while self.acquiring:
                charge = 100*np.random.random()
                self.charge_ready.emit(charge)
                time.sleep(self.delay) # purposeful delay
        
        else:
            # ICT and serial settings
            port = 'COM1'
            baudrate = 115200
            termination = '\n\0'
            Qcal = 0.005 # picoCoulombs
            Ucal = 0.8722100 # volts
            try: 
                with serial.Serial(port=port, baudrate=baudrate, timeout=1) as ser:
                    # Wait for connection
                    time.sleep(2)

                    # Flush buffer
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()

                    # Continuously poll
                    while self.acquiring:
                        time.sleep(.05) #~10 Hz reprate
                        if ser.in_waiting: # ie. byte in buffer
                            buffer = ser.read_until(termination.encode()).decode('utf-8')
                            
                            # Maybe have received multiple responses
                            for response in buffer.split(termination):

                                # Voltage sample indicated by 'A' prefix
                                # Ex: 'A0:0123=00123ABC\n\0'
                                # or '{frame_type}{frame_number}:{4_char_counter}={8_char_value}{terminator}'
                                if response[0]=='A':
                                    hex_value = response[8:]
                                    volts = int(hex_value, 16) # Convert from microVolts

                                    # Apply calibration
                                    charge = Qcal * 10**(volts / Ucal) #picoCoulombs
                                    self.charge_ready.emit(charge)
                                    time.sleep(self.delay) # purposeful delay

            except serial.SerialException as e:
                print(f"Serial exception: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")
    
    def stop(self):
        print(f'Stopping ICT')
        self.acquiring = False
        self.wait() #wait for thread to stop

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
        self.delay = 0
        self.actionFlag = True #Set properties on startup

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
                time.sleep(.1) #simulates 10Hz trigger
                time.sleep(self.delay)

        else:
            # Actual data images
            with Vimba.get_instance() as system:
                with system.get_camera_by_id(self.ID) as cam:
                    cam.get_feature_by_name('TriggerSource').set('Line1')  # or 'Software' if you want to trigger via software

                    # Camera properties can only be changed within a "with" statement.
                    while self.acquiring:

                        # Set features if a value changed
                        if self.actionFlag:
                            self.actionFlag = False

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
                        time.sleep(self.delay) # purposeful delay


    def stop(self):
        print(f'Stopping Cam {self.ID}')
        self.acquiring = False
        self.wait() #wait for thread to stop

    def set(self, attribute, value):
        setattr(self, attribute, value)
        self.actionFlag = True
        print(f'Set {attribute} to {value}')


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