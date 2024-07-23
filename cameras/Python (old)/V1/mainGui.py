# %%
# Imports
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QSize, Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout
from PyQt6 import QtWidgets, uic
from PIL import Image
from datetime import datetime
import os
from collections import deque
from vmbpy import VmbSystem
import utils
from utils import fit_gaussian_with_offset, CameraSettings, FilterWheel, VimbaCamera
import time
from scipy.ndimage import rotate
from matplotlib.patches import Ellipse

# Define camera settings
defined_camera_settings = {
    'SN-01':{'COM':'COM1', 'label':'Cam1', 'SN':'SN-01'},
    'SN-02':{'COM':'COM2', 'label':'Cam2', 'SN':'SN-02'},
    'SN-03':{'COM':'COM3', 'label':'Cam3', 'SN':'SN-03'},
}
    

# GUI Window Class
mw_Ui, mw_Base = uic.loadUiType('main_window.ui')
class MainWindow(mw_Base, mw_Ui):
    image_stats = pyqtSignal(list)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Setup
        self.loadStylesheet('styles.css')
        self.setupCanvas() 
        self.setupCameras()
        self.setupQueues()


        # Create a QTimer (for fake data acquisition)
        self.timer = QTimer()
        self.timer.timeout.connect(self.readImage)

        #----- Signals and slots (in order of gui) -----#
        # Acquisition
        self.runButton.clicked.connect(self.startCamera)
        self.stopButton.clicked.connect(self.stopCamera)

        # Camera
        self.cameraCombo.currentIndexChanged.connect(self.changeCamera)
        self.gainInput.valueChanged.connect(self.updateGain)
        self.exposureInput.valueChanged.connect(self.updateExposure)

        # Background
        self.setButton.clicked.connect(self.setBackground)
        self.subtractButton.clicked.connect(self.toggleBackgroundSubtraction)

        # Saving
        self.singleButton.clicked.connect(self.saveImage)
        self.continuousButton.clicked.connect(self.toggleSaveContinuous)

        # Filter Wheel
        self.fwCombo.currentIndexChanged.connect(self.changeFilterWheel)

        # Image Analysis
        self.analyzeButton.clicked.connect(self.toggleAnalysis)
        self.ellipseButton.clicked.connect(self.toggleEllipse)
        self.resetButton.clicked.connect(self.resetQueues)

        # Test Button
        self.testButton.clicked.connect(self.testFunction)

        #----- Flags and checkable buttons -----#
        self.subtractbackgroundFlag = False
        self.subtractButton.setCheckable(True)

        self.savecontinuousFlag = False
        self.continuousButton.setCheckable(True)

        self.analysisFlag = False
        self.analyzeButton.setCheckable(True)

        self.ellipseFlag = False
        self.ellipseButton.setCheckable(True)

        self.gainInput.setValue(7)
        self.startCamera()

    #----- Test Function -----#
    def testFunction(self):
        self.testButton.setEnabled(False) #Lock to avoid multiple scans
        self.rasterScan.start()
        return
    
    def update_progress(self, value):
        print(f"Scan progress: {value}%")
        # Update progress in GUI (e.g., a progress bar)

    #----- Setup Functions -----#
    def loadStylesheet(self, filename):
        with open(filename, 'r') as file:
            stylesheet = file.read()
            self.setStyleSheet(stylesheet)

    def setupCanvas(self):
        # Initialize image and background
        self.pixels = 100
        self.image      = np.ones((self.pixels, self.pixels))
        self.background = np.zeros((self.pixels, self.pixels))

        # Create the FigureCanvas and add to the widget layout
        self.figure, self.ax = plt.subplots(figsize=(7,7), dpi=100)
        self.ax.axis('off')
        self.ax.set_aspect('equal')
        self.ax.imshow(self.image, cmap='viridis', origin='lower', vmin=0, vmax=255)

        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.canvas = FigureCanvas(self.figure)
        layout = self.imageWidget.layout()
        layout.addWidget(self.canvas)

        # ROI
        self.roi = None
        self.roi_selector = RectangleSelector(self.ax, self.specifyROI, 
                                              useblit=True,
                                              button=[1],  # Only respond to left mouse button
                                              minspanx=5, minspany=5,
                                              spancoords='pixels',
                                              interactive=True,
                                              props=dict(edgecolor='green', linewidth=2, fill=False))
        self.roi_selector.set_active(True)

        # Ellipse
        self.ellipse = Ellipse(xy=(0,0), width=0, height=0,
                  angle=0, edgecolor='None', fc='None', lw=2)
        self.ax.add_patch(self.ellipse)
        
        return

    def setupCameras(self):
        # Define mapping from serial number to index 
        SN_to_index = {SN:index for index, SN in enumerate(defined_camera_settings)}

        # Load vimba cameras
        vimba = VmbSystem.get_instance()
        with vimba:
            unordered_cameras = vimba.get_all_cameras()
        unordered_SNs = [cam.get_feature_by_name('DeviceSerialNumber').get() for cam in unordered_cameras]

        # For testing
        unordered_SNs = np.array(['SN-03', 'SN-01', 'SN-02'])
        unordered_cameras = [VimbaCamera(SN) for SN in unordered_SNs]


        # Build cameraCombo, camera_settings, and filterwheels in user-defined order
        self.cameraCombo.clear()
        self.camera_settings = []
        self.filter_wheels = []

        unordered_indicies = [SN_to_index[SN] for SN in unordered_SNs]
        for index in np.argsort(unordered_indicies):
            # Get relevant camera, serial number, and settings
            camera = unordered_cameras[index]
            SN = unordered_SNs[index]
            settings = defined_camera_settings[SN]

            # Add to combobox and camera_settings list
            self.cameraCombo.addItem(settings['label'], camera)
            self.camera_settings.append(CameraSettings(**settings))
            self.filter_wheels.append(FilterWheel(COM=settings['COM']))

        # Set current camera and filterwheel
        menu_index = self.cameraCombo.currentIndex()
        self.current_camera = self.cameraCombo.itemData(menu_index)
        self.current_camera_settings = self.camera_settings[menu_index]
        self.current_filterwheel = self.filter_wheels[menu_index]
        return
    
    def setupQueues(self):
        self.queue_size = 20
        self.xcQueue = deque(maxlen=self.queue_size)
        self.ycQueue = deque(maxlen=self.queue_size)
        self.xrmsQueue = deque(maxlen=self.queue_size)
        self.yrmsQueue = deque(maxlen=self.queue_size)
        return

    #----- Acquisition Functions -----#
    def startCamera(self):
        self.timer.start(1000)
    
    def stopCamera(self):
        self.timer.stop()

    #----- Camera Functions -----#
    def changeCamera(self, index):
        # Read new camera and settings
        menu_index = self.cameraCombo.currentIndex()
        camera = self.cameraCombo.itemData(index)
        
        # Close previous camera
        if self.current_camera:
            self.current_camera.close()

        # Open new
        self.current_filterwheel = self.filter_wheels[menu_index]
        self.current_camera_settings = self.camera_settings[menu_index]
        self.current_camera = camera
        if self.current_camera:
            self.current_camera.open()
            print(f"Camera: {self.current_camera_settings.label}, SN={self.current_camera_settings.SN}")

        # Change gui settings
        self.gainInput.setValue(self.current_camera_settings.gain)
        self.exposureInput.setValue(self.current_camera_settings.exposure)
        self.fwCombo.setCurrentIndex(self.current_camera_settings.FWindex)
        return
    
    def updateGain(self, value):
        self.current_camera_settings.gain = value

        # Background subtraction should be redone when changing gain
        self.subtractbackgroundFlag = False
        self.subtractButton.setChecked(False)
        return
    
    def updateExposure(self, value):
        self.current_camera_settings.exposure = value
        return
    
    #----- Background Functions -----#
    def setBackground(self):
        if not self.subtractbackgroundFlag:
            self.background = self.image
        return

    def toggleBackgroundSubtraction(self):
        self.subtractbackgroundFlag = not self.subtractbackgroundFlag
        return

    #----- Saving Functions -----#
    def saveImage(self):
        pil_image = Image.fromarray((self.image*255).astype(np.uint8))

        # Ensure image directory for today's date
        datestamp = datetime.now().strftime("%Y-%m-%d")
        self.image_dir = os.path.join('Images', datestamp)
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

        # Save image
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filepath = os.path.join(self.image_dir, f'{timestamp}.png')
        pil_image.save(filepath)
        return

    def toggleSaveContinuous(self):
        self.savecontinuousFlag = not self.savecontinuousFlag
        return

    #----- Filter Wheel FUnctions -----#
    def changeFilterWheel(self, FWindex):
        self.current_filterwheel.move(FWindex)
        self.current_camera_settings.FWindex = FWindex


    #----- Image Analysis Functions -----#
    def toggleAnalysis(self):
        self.analysisFlag = not self.analysisFlag
        self.resetQueues()

        if not self.analysisFlag and self.ellipseFlag:
            self.toggleEllipse()
    
    def toggleEllipse(self):
        if self.analysisFlag:
            self.ellipseFlag = not self.ellipseFlag
            edgecolor = 'red' if self.ellipseFlag else 'none'
            self.ellipse.set_edgecolor(edgecolor)
        else:
            self.ellipseFlag = False
            self.ellipse.set_edgecolor('none')
            self.ellipseButton.setChecked(False)

    def resetQueues(self):
        self.xcQueue.clear()
        self.ycQueue.clear()
        self.xrmsQueue.clear()
        self.yrmsQueue.clear()

    def specifyROI(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)

        if abs(x2 - x1) < self.roi_selector.minspanx or abs(y2 - y1) < self.roi_selector.minspany or (x1 == x2 and y1 == y2):
            self.roi = None
        else:
            self.roi = (x1, y1, x2, y2)
        print(f"ROI selected: {self.roi}")

    
    #----- Main Image acquisition -----#

    def readImage(self):
        # Define parameters for the Gaussian distribution
        centroid_x = 50 + np.random.rand()*2
        centroid_y = 50 + np.random.rand()*2
        xrms = 3 + np.random.rand()
        yrms = 3 + np.random.rand()      

        # Create a grid of coordinates
        x = np.linspace(0, 100, self.pixels)
        y = np.linspace(0, 100, self.pixels)
        X, Y = np.meshgrid(x, y)

        # Image is gaussian with noise
        gaussian = ( (2 + 0.2*np.random.rand())**self.gainInput.value()) * np.exp(-((X - centroid_x) ** 2)/ (2*xrms**2)) * np.exp(-((Y - centroid_y) ** 2) / (2 * yrms**2))
        noise = 5 * np.random.rand(*gaussian.shape) + np.linspace(0, 50, self.pixels)
        self.image = gaussian + noise
        self.image = self.image.clip(0, 255)


        # Warn about saturation
        if self.image.max()>=255:
            self.gainLabel.setStyleSheet("background-color: red; color: white;")
        else:
            self.gainLabel.setStyleSheet("background-color: white; color: black;")

        # Remove background
        if self.subtractbackgroundFlag:
            self.image -= self.background

        # Save image
        if self.savecontinuousFlag:
            self.saveImage()

        # Plot the noisy Gaussian data
        self.ax.imshow(self.image, cmap='viridis', origin='lower', vmin=0, vmax=255)

        # Compute centroid and rms from gaussian fits (Can move to utils)
        if self.analysisFlag:
            if self.roi:
                x1, y1, x2, y2 = self.roi
            else:
                x1, y1 = 0, 0
                x2, y2 = self.pixels, self.pixels
            _, centroid_x, xrms, xbg = fit_gaussian_with_offset(self.image[y1:y2, x1:x2].sum(axis=0))
            _, centroid_y, yrms, ybg = fit_gaussian_with_offset(self.image[y1:y2, x1:x2].sum(axis=1))

            if self.ellipseFlag:
                bg = xbg/(x2-x1) + ybg/(y2-y1)
                rot45image = rotate(self.image[y1:y2, x1:x2], 45, cval = bg)
                _, _, sigma45, _ = fit_gaussian_with_offset(rot45image.sum(axis=0))

                rot135image = rotate(self.image[y1:y2, x1:x2], 135, cval = bg)
                _, _, sigma135, _ = fit_gaussian_with_offset(rot135image.sum(axis=0))

                centroid_x += x1
                centroid_y += y1
                sigmaxy     = np.abs((sigma45**2-sigma135**2)/2)

                beam_matrix = np.array([[xrms**2, -sigmaxy], [-sigmaxy, yrms**2]])
                eigvalues, eigvectors = np.linalg.eig(beam_matrix)

                # Draw ellipse
                semi_major = np.sqrt(eigvalues[0])
                semi_minor = np.sqrt(eigvalues[1])
                angle = np.degrees(np.arctan2(eigvectors[1, 0], eigvectors[0, 0]))

                self.ellipse.set_center( (centroid_x, centroid_y) )
                self.ellipse.width = 2*semi_major
                self.ellipse.height = 2*semi_minor
                self.ellipse.angle = angle

        else:
            centroid_x, centroid_y, xrms, yrms = 0, 0, 0, 0

        # Draw new image
        self.canvas.draw()

        # Print instantaneous beam stats
        self.xcInstant.setText(f"{centroid_x:.2f}")
        self.ycInstant.setText(f"{centroid_y:.2f}")
        self.xrmsInstant.setText(f"{xrms:.2f}")
        self.yrmsInstant.setText(f"{yrms:.2f}")

        # Append to queues. Print average beam stats
        self.xcQueue.append(centroid_x)
        self.ycQueue.append(centroid_y)
        self.xrmsQueue.append(xrms)
        self.yrmsQueue.append(yrms)
        self.xcAvg.setText(f"{utils.computeQueueMean(self.xcQueue):.2f}")
        self.ycAvg.setText(f"{utils.computeQueueMean(self.ycQueue):.2f}")
        self.xrmsAvg.setText(f"{utils.computeQueueMean(self.xrmsQueue):.2f}")
        self.yrmsAvg.setText(f"{utils.computeQueueMean(self.yrmsQueue):.2f}")
        return




# Run Application
if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


# %%
