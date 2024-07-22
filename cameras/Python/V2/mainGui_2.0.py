# %%

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
from PyQt6.QtGui import QPixmap, QImage
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
import threading
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QBrush, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PyQt6.QtCore import QRectF
import pyqtgraph as pg
import PyQt6.QtCore as QtCore


# Define camera settings
defined_camera_settings = {
    'SN-01':{'COM':'COM1', 'label':'Cam1', 'SN':'SN-01'},
    'SN-02':{'COM':'COM2', 'label':'Cam2', 'SN':'SN-02'},
    'SN-03':{'COM':'COM3', 'label':'Cam3', 'SN':'SN-03'},
}
    
class ImageAcquisition(QThread):
    image_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.readImage)
        self.timer.start(100)


    def run(self):
        pass

    def readImage(self):
        pixels = 300

        # Define parameters for the Gaussian distribution
        centroid_x = 100 + np.random.rand()*0
        centroid_y = 100 + np.random.rand()*0
        xrms = 10 + 3*np.random.rand()
        yrms = 10 + 3*np.random.rand()      

        # Create a grid of coordinates
        x = np.arange(pixels)
        y = np.arange(pixels)
        X, Y = np.meshgrid(x, y)

        # create gaussian with noise
        gaussian = 200* np.exp(-((X - centroid_x) ** 2)/ (2*xrms**2)) * np.exp(-((Y - centroid_y) ** 2) / (2 * yrms**2))
        noise = 5 * np.random.rand(*gaussian.shape) + np.linspace(0, 50, pixels)
        image = (gaussian + noise).clip(0, 255)
        
        # Emit image
        self.image_ready.emit([image])


# GUI Window Class
mw_Ui, mw_Base = uic.loadUiType('main_window_2.0.ui')
class MainWindow(mw_Base, mw_Ui):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Connect to ImageAcquisition class
        self.imageAcq = ImageAcquisition()
        self.imageAcq.image_ready.connect(self.update_image)

        # Setup
        self.loadStylesheet('styles.css')
        self.setupGraphics() 
        self.setupCameras()
        self.setupQueues()


        #----- Signals and slots (in order of gui) -----#
        # Acquisition
        self.acquireButton.clicked.connect(self.toggleAcquisition)

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

        self.roiButton.clicked.connect(self.toggleROI)


        #----- Flags and checkable buttons -----#
        self.acquireFlag = False
        self.acquireButton.setCheckable(True)

        self.roiFlag = False
        self.roiButton.setCheckable(True)

        self.subtractFlag = False
        self.subtractButton.setCheckable(True)

        self.continuousFlag = False
        self.continuousButton.setCheckable(True)

        self.analysisFlag = False
        self.analyzeButton.setCheckable(True)

        self.ellipseFlag = False
        self.ellipseButton.setCheckable(True)
    
    def update_progress(self, value):
        print(f"Scan progress: {value}%")
        # Update progress in GUI (e.g., a progress bar)

    #----- Setup Functions -----#
    def loadStylesheet(self, filename):
        with open(filename, 'r') as file:
            stylesheet = file.read()
            self.setStyleSheet(stylesheet)

    def setupGraphics(self):
        # Create graphicsScene, add to graphicsView
        self.imageView = pg.ImageView()
        self.imageLayout.addWidget(self.imageView)

        # Create ROI
        self.roi_item = pg.RectROI([0, 0], [100, 100], pen='r')
        self.roi_item.setVisible(False)
        self.imageView.addItem(self.roi_item)

        self.imageView.ui.roiBtn.hide()  # Hide default ROI button
        self.imageView.ui.histogram.hide()  # Hide histogram
        self.imageView.ui.menuBtn.hide()  # Hide the menu button (if available)

        # Ellipse
        self.ellipse = pg.PlotDataItem(pen=pg.mkPen(None), width=2)
        self.imageView.addItem(self.ellipse)



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
    def toggleAcquisition(self):
        self.acquireFlag = not self.acquireFlag

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
        self.subtractFlag = False
        self.subtractButton.setChecked(False)
        return
    
    def updateExposure(self, value):
        self.current_camera_settings.exposure = value
        return
    
    #----- Background Functions -----#
    def setBackground(self):
        if not self.subtractFlag:
            self.background = self.image
        return

    def toggleBackgroundSubtraction(self):
        self.subtractFlag = not self.subtractFlag
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
        self.continuousFlag = not self.continuousFlag
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
    
    def toggleROI(self):
        self.roiFlag = not self.roiFlag
        self.roi_item.setVisible(self.roiFlag)

    def toggleEllipse(self):
        if self.analysisFlag:
            self.ellipseFlag = not self.ellipseFlag
            edgecolor = 'green' if self.ellipseFlag else None
            self.ellipse.setPen(pg.mkPen(edgecolor))
        else:
            self.ellipseFlag = False
            self.ellipse.setPen(pg.mkPen(None))
            self.ellipseButton.setChecked(False)
        pass

    def resetQueues(self):
        self.xcQueue.clear()
        self.ycQueue.clear()
        self.xrmsQueue.clear()
        self.yrmsQueue.clear()
    
    #----- Main Image acquisition -----#

    def update_image(self, image):
        self.image = image[0] # Had to be list for PyQt Signal
        if not self.acquireFlag:
            return

        # Warn about saturation
        if self.image.max()>=255:
            self.gainLabel.setStyleSheet("background-color: red; color: white;")
        else:
            self.gainLabel.setStyleSheet("background-color: white; color: black;")

        # Remove background
        if self.subtractFlag:
            self.image -= self.background

        # Save image
        if self.continuousFlag:
            self.saveImage()

        # Show new image        
        view = self.imageView.getView()
        zoom_state = view.viewRange()
        self.imageView.setImage(self.image)
        view.setRange(xRange=zoom_state[0], yRange=zoom_state[1], padding=0)

        # Compute centroid and rms from gaussian fits (Can move to utils)
        if self.analysisFlag:

            # Apply ROI
            if self.roiFlag:
                x1, y1 = self.roi_item.pos()
                w, h = self.roi_item.size()
            else:
                x1, y1 = 0, 0
                h, w = self.image.shape

            roi_image = self.image[int(y1):int(y1+h), int(x1):int(x1+w)]

            # Apply gaussian fits
            _, centroid_x, xrms, xbg = fit_gaussian_with_offset(roi_image.sum(axis=0))
            _, centroid_y, yrms, ybg = fit_gaussian_with_offset(roi_image.sum(axis=1))
            centroid_x += int(x1)
            centroid_y += int(y1)
            
            if self.ellipseFlag:
                bg = xbg/w + ybg/h
                rot45image = rotate(roi_image, 45, cval = bg)
                _, _, sigma45, _ = fit_gaussian_with_offset(rot45image.sum(axis=0))

                rot135image = rotate(roi_image, 135, cval = bg)
                _, _, sigma135, _ = fit_gaussian_with_offset(rot135image.sum(axis=0))


                sigmaxy     = np.abs((sigma45**2-sigma135**2)/2)

                beam_matrix = np.array([[xrms**2, -sigmaxy], [-sigmaxy, yrms**2]])
                eigvalues, eigvectors = np.linalg.eig(beam_matrix)

                # Draw ellipse
                semi_major = np.sqrt(eigvalues[0])
                semi_minor = np.sqrt(eigvalues[1])
                angle = np.degrees(np.arctan2(eigvectors[1, 0], eigvectors[0, 0]))

                t = np.linspace(0, 2*np.pi, 100)
                x = semi_major*np.cos(t)
                y = semi_minor*np.sin(t)
                xpoints = centroid_x + x*np.cos(angle) - y*np.sin(angle)
                ypoints = centroid_y + x*np.sin(angle) + y*np.cos(angle)
                self.ellipse.setData(xpoints, ypoints)

        else:
            centroid_x, centroid_y, xrms, yrms = 0, 0, 0, 0


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

    def closeEvent(self, event):
        for filterWheel in self.filter_wheels:
            filterWheel.close_conn()
        event.accept()  # Ensure that the window is closed

# Run Application
if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


# %%
