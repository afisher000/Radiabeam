# %%

# %%
# Imports
import sys
import os
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6 import uic

from PIL import Image
from datetime import datetime
from collections import deque
from utils import fit_gaussian_with_offset, Settings, FilterWheel, computeQueueMean
from scipy.ndimage import rotate

import pyqtgraph as pg
from vimba import Vimba

# Define camera settings
defined_settings = {
    '50-0536999326':{'COM':'COM4', 'label':'Cam Laser', 'SN':'50-0536999326', 'ID':'DEV_000F315D821E', 'calibration':17.5/1024},
    '50-0537035519':{'COM':'COM7', 'label':'Cam 2', 'SN':'50-0537035519', 'ID':'DEV_000F315E0F7F', 'calibration':18/1029},
}
    
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
                while self.is_acquiring():
                    cam.get_feature_by_name('Gain').set(self.gain)

                    frame = cam.get_frame()
                    image = frame.as_numpy_ndarray()
                    self.image_ready.emit([image])

    def is_acquiring(self):
        return self.acquiring
    
    def stop(self):
        print(f'Stopping Cam {self.ID}')
        self.acquiring = False
        self.wait()

    def set(self, attribute, value):
        setattr(self, attribute, value)



# GUI Window Class
mw_Ui, mw_Base = uic.loadUiType('main_window_2.0.ui')
class MainWindow(mw_Base, mw_Ui):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Setup
        # self.loadStylesheet('styles.css')
        self.setupGraphics() 
        self.setupCameras()
        self.setupQueues()

        # Connect to ImageAcquisition class
        self.imageAcq = ImageAcquisition(self.get_setting('ID'))
        self.imageAcq.image_ready.connect(self.update_image)
        self.imageAcq.start()


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
    
    def get_setting(self, attribute):
        return getattr(self.settings[self.menu_index], attribute)
    
    def set_setting(self, attribute, value):
        setattr(self.settings[self.menu_index], attribute, value)

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
        self.roi_item = pg.RectROI([1280//4, 1280//4], [1280//2, 1280//2], pen='r')
        self.roi_item.setVisible(False)
        self.imageView.addItem(self.roi_item)

        self.imageView.ui.roiBtn.hide()  # Hide default ROI button
        self.imageView.ui.histogram.hide()  # Hide histogram
        self.imageView.ui.menuBtn.hide()  # Hide the menu button (if available)
        self.imageView.getView().setRange(xRange=(0, 1280), yRange=(0,1280), padding=0)

        # Ellipse
        self.ellipse = pg.PlotDataItem(pen=pg.mkPen(None), width=2)
        self.imageView.addItem(self.ellipse)



    def setupCameras(self):
        # Build cameraCombo, settings, and filterwheels in user-defined order
        self.cameraCombo.clear()
        self.settings = []
        self.filter_wheels = []

        # unordered_indicies = [SN_to_index[SN] for SN in unordered_SNs]
        for SN, settings in defined_settings.items():

            # Add to combobox and settings list
            self.cameraCombo.addItem(settings['label'], settings['ID'])
            self.settings.append(Settings(**settings))
            self.filter_wheels.append(FilterWheel(COM=settings['COM']))

        self.menu_index = 0
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
        self.menu_index = index

        # Stop acquisition
        print('Stop camera')
        self.imageAcq.stop()

        # Change camera ID and restart
        self.imageAcq.set('ID', self.get_setting('ID'))
        self.imageAcq.start()

        # Change gui settings
        self.gainInput.setValue(self.get_setting('gain'))
        self.exposureInput.setValue(self.get_setting('exposure'))
        self.fwCombo.setCurrentIndex(self.get_setting('FWindex'))
        return
    
    def updateGain(self, gain):
        self.settings[self.menu_index].gain = gain
        self.imageAcq.set('gain', gain)

        # Background subtraction should be redone when changing gain
        self.subtractFlag = False
        self.subtractButton.setChecked(False)
        return
    
    def updateExposure(self, exposure):
        self.settings[self.menu_index].exposure = exposure
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
        self.filter_wheels[self.menu_index].move(FWindex)
        self.settings[self.menu_index].FWindex = FWindex


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
        # Had to be list for PyQt Signal, reorder dimensions
        self.image = image[0].squeeze()
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
        self.imageView.setImage(self.image.T) #pyqtgraph plots axes along x,y. Numpy plots along y,x
        view.setRange(xRange=zoom_state[0], yRange=zoom_state[1], padding=0)

        # Apply ROI
        if self.roiFlag:
            x1, y1 = self.roi_item.pos()
            w, h = self.roi_item.size()
        else:
            x1, y1 = 0, 0
            h, w = self.image.shape

        # Compute centroid and rms from gaussian fits (Can move to utils)
        if self.analysisFlag:
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
        self.xcInstant.setText(self.format_units(centroid_x))
        self.ycInstant.setText(self.format_units(centroid_y))
        self.xrmsInstant.setText(self.format_units(xrms))
        self.yrmsInstant.setText(self.format_units(yrms))
        if self.roiFlag:
            self.deltaxInstant.setText(self.format_units(w))
            self.deltayInstant.setText(self.format_units(h))
        else:
            self.deltaxInstant.setText(self.format_units(0)) #Show 0um when no ROI
            self.deltayInstant.setText(self.format_units(0))  


        # Append to queues. Print average beam stats
        self.xcQueue.append(centroid_x)
        self.ycQueue.append(centroid_y)
        self.xrmsQueue.append(xrms)
        self.yrmsQueue.append(yrms)
        self.xcAvg.setText(self.format_units(computeQueueMean(self.xcQueue)))
        self.ycAvg.setText(self.format_units(computeQueueMean(self.ycQueue)))
        self.xrmsAvg.setText(self.format_units(computeQueueMean(self.xrmsQueue)))
        self.yrmsAvg.setText(self.format_units(computeQueueMean(self.yrmsQueue)))

    def format_units(self, pixels):
        #Return as mm or um.
        dist = pixels * self.get_setting('calibration')
        return f'{dist:.2f}mm' if dist>=1 else f'{dist/1000:.0f}um'

        
    def closeEvent(self, event):
        self.imageAcq.stop()
        
        print('Closing filter wheels')
        for fw in self.filter_wheels:
            fw.close_conn()

        print('Closing window')
        event.accept()  # Ensure that the window is closed


# Run Application
if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


# %%