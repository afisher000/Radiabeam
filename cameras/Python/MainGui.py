import sys
import os
import numpy as np

from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit
from PyQt6 import uic

from PIL import Image
from datetime import datetime
from collections import deque
from utils import fit_gaussian_with_offset, Settings, computeQueueMean, SteeringMagnets, ImageAcquisition, FilterWheel
from scipy.ndimage import rotate

import pyqtgraph as pg
import pandas as pd
import concurrent.futures

''' 
WORK TO BE DONE
 - Add info to scanData including calibration, camera label and SN, filterwheel
 - Ellipse fitting is very slow?
 - Add exposure to camera


'''

defined_settings = {
    '50-0537011139':{'label':'Cam 1', 'COM':'COM2', 'SN':'50-0537011139', 'ID':'DEV_000F315DB043', 'calibration':18/736},
    '50-0537035519':{'label':'Cam 2', 'COM':'COM4', 'SN':'50-0537035519', 'ID':'DEV_000F315E0F7F', 'calibration':18/1029},
    '50-0536999326':{'label':'Cam Laser', 'COM':None, 'SN':'50-0536999326', 'ID':'DEV_000F315D821E', 'calibration':17.5/1024},
    '50-0536976126':{'label':'Cam 4', 'COM':'COM6', 'SN':'50-0536976126', 'ID':'DEV_000F315D277E', 'calibration':18/1024},
    '50-0536999325':{'label':'Beam Dump', 'COM':'COM7', 'SN':'50-0536999325', 'ID':'DEV_000F315D821D', 'calibration':18/1074},
}

# GUI Window Class
mw_Ui, mw_Base = uic.loadUiType('window.ui')
class MainWindow(mw_Base, mw_Ui):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.image_h = 1024
        self.image_w = 1280

        # Setup
        self.setupGraphics() 
        self.setupCameras()
        self.setupFilterWheels()
        self.setupQueues(self.shotsInput.value())
        self.magnets = SteeringMagnets()
        self.triggerCombo.addItems(["Freerun", "Trigger"])



        # Connect to ImageAcquisition class
        self.imageAcq = ImageAcquisition(self.get_setting('ID'))
        self.imageAcq.image_ready.connect(self.update_image)
        self.imageAcq.start()


        #----- Signals and slots (in order of gui) -----#
        # Acquisition
        self.acquireButton.clicked.connect(self.toggleAcquisition)
        self.acquireButton.setCheckable(True)
        self.acquireFlag = False
        
        self.triggerCombo.currentIndexChanged.connect(self.updateTriggerMode)


        # Camera
        self.cameraCombo.currentIndexChanged.connect(self.changeCamera)
        self.gainInput.valueChanged.connect(self.updateGain)
        self.exposureInput.valueChanged.connect(self.updateExposure)

        # Background
        self.setButton.clicked.connect(self.setBackground)
        self.subtractButton.clicked.connect(self.toggleBackgroundSubtraction)
        self.subtractButton.setCheckable(True)
        self.subtractFlag = False

        # Saving
        self.singleButton.clicked.connect(self.saveImage)
        self.continuousButton.clicked.connect(self.toggleSaveContinuous)
        self.continuousButton.setCheckable(True)
        self.continuousFlag = False


        # Filter Wheel
        self.fwCombo.currentIndexChanged.connect(self.changeFilterWheel)

        # Image Analysis
        self.analyzeButton.clicked.connect(self.toggleAnalysis)
        self.analyzeButton.setCheckable(True)
        self.analysisFlag = False

        self.ellipseButton.clicked.connect(self.toggleEllipse)
        self.ellipseButton.setCheckable(True)
        self.ellipseFlag = False

        self.shotsInput.valueChanged.connect(self.updateShots)
        self.resetButton.clicked.connect(self.resetQueues)

        self.roiButton.clicked.connect(self.toggleROI)
        self.roiButton.setCheckable(True)
        self.roiFlag = False

        # Scan
        self.runscanButton.clicked.connect(self.toggleScan)
        self.runscanButton.setCheckable(True)
        self.scanFlag = False


    #---- Functions to access gui settings -----#    
    def get_setting(self, attribute):
        return getattr(self.settings[self.menu_index], attribute)
    
    def set_setting(self, attribute, value):
        setattr(self.settings[self.menu_index], attribute, value)


    #----- Setup Functions -----#
    def setupGraphics(self):
        # Set widget to correct size
        scale = 0.5
        # self.imageWidget.setFixedSize(int(self.image_w*scale), int(self.image_h*scale))

        # Create graphicsScene, add to graphicsView
        self.imageView = pg.ImageView()
        self.imageLayout.addWidget(self.imageView)


        # Create ROI
        self.roi_item = pg.RectROI([self.image_w//4, self.image_h//4], [self.image_w//2, self.image_h//2], pen='r')
        self.roi_item.setVisible(False)
        self.imageView.addItem(self.roi_item)
        self.imageView.setColorMap(pg.colormap.get('viridis')) #'viridis', 'plasma', 'inferno', 'magma', 'cividis'

        self.imageView.ui.roiBtn.hide()  # Hide default ROI button
        self.imageView.ui.histogram.hide()  # Hide histogram
        self.imageView.ui.menuBtn.hide()  # Hide the menu button (if available)

        view = self.imageView.getView()
        view.setRange(xRange=(0, self.image_w), yRange=(0,self.image_h), padding=0)
        view.setBackgroundColor('w')

        # Ellipse
        self.ellipse = pg.PlotDataItem(pen=pg.mkPen(None), width=2)
        self.imageView.addItem(self.ellipse)

    def setupCameras(self):
        ''' Create settings object and initialize camera combobox'''
        self.cameraCombo.clear()
        self.settings = []

        for SN, settings in defined_settings.items():
            self.cameraCombo.addItem(settings['label'], settings['ID'])
            self.settings.append(Settings(**settings))

        self.menu_index = 0
    
    def setupFilterWheels(self):
        ''' Initialize FilterWheel objects. '''
        self.filter_wheels = []
        for _, settings in defined_settings.items():
            self.filter_wheels.append(FilterWheel(COM=settings['COM']))


    def setupQueues(self, queue_size):
        ''' Setup Queues for image stat averages.'''
        self.xcQueue = deque(maxlen=queue_size)
        self.ycQueue = deque(maxlen=queue_size)
        self.xrmsQueue = deque(maxlen=queue_size)
        self.yrmsQueue = deque(maxlen=queue_size)
        self.pixelSumQueue = deque(maxlen=queue_size)

    #----- Acquisition Functions -----#
    def toggleAcquisition(self):
        self.acquireFlag = not self.acquireFlag

    def updateTriggerMode(self, index):
        triggerMode = self.triggerCombo.itemText(index)
        self.imageAcq.set('triggerMode', triggerMode)

    #----- Camera Functions -----#
    def changeCamera(self, index):
        self.menu_index = index

        # Stop acquisition
        print('Stop camera')
        self.imageAcq.stop()

        # Change camera ID in imageAcq and restart
        self.imageAcq.set('ID', self.get_setting('ID'))
        self.imageAcq.start()

        # Change gui settings
        self.gainInput.setValue(self.get_setting('gain'))
        self.exposureInput.setValue(self.get_setting('exposure'))
        self.fwCombo.setCurrentIndex(self.get_setting('FWindex'))
    
    def updateGain(self, gain):
        self.settings[self.menu_index].gain = gain
        self.imageAcq.set('gain', gain)

        # Background subtraction should be redone when changing gain
        self.subtractFlag = False
        self.subtractButton.setChecked(False)
    
    def updateExposure(self, exposure):
        self.settings[self.menu_index].exposure = exposure
        self.imageAcq.set('exposure', exposure)
    
    #----- Background Functions -----#
    def setBackground(self):
        if not self.subtractFlag:
            self.background = self.image


    def toggleBackgroundSubtraction(self):
        self.subtractFlag = not self.subtractFlag

    #----- Saving Functions -----#
    def saveImage(self):
        pil_image = Image.fromarray(self.image)

        # Ensure image directory for today's date
        datestamp = datetime.now().strftime("%Y-%m-%d")
        image_dir = os.path.join('Images', datestamp)
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        # Save image
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filepath = os.path.join(image_dir, f'{timestamp}.png')
        pil_image.save(filepath)

    def toggleSaveContinuous(self):
        self.continuousFlag = not self.continuousFlag

    #----- Scan Functions -----#
    def toggleScan(self):
        # Reset scanData or save to file
        if not self.scanFlag:
            self.scanData = []
        else:
            # Ensure image directory for today's date
            datestamp = datetime.now().strftime("%Y-%m-%d")
            scan_dir = os.path.join('Scans', datestamp)
            if not os.path.exists(scan_dir):
                os.makedirs(scan_dir)

            # Window to name file
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            default_filename = f'{timestamp}_measurement.csv'
            filename, ok = QInputDialog.getText(self, 'File Name', 'Enter the file name:', QLineEdit.EchoMode.Normal, default_filename)
                
            # Save scan data
            filepath = os.path.join(scan_dir, filename)
            pd.DataFrame(self.scanData).to_csv(filepath, index=False)

        # Toggle flag
        self.scanFlag = not self.scanFlag
        

    #----- Filter Wheel Functions -----#
    def changeFilterWheel(self, FWindex):
        #FWindex counts from 0, FilterWheel counts from 1
        self.filter_wheels[self.menu_index].move(FWindex+1) 
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

    def updateShots(self, shots):
        self.setupQueues(shots)

    def resetQueues(self):
        self.xcQueue.clear()
        self.ycQueue.clear()
        self.xrmsQueue.clear()
        self.yrmsQueue.clear()
        self.pixelSumQueue.clear()
    
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

        # Remove background (convert to int16 to handle negatives)
        if self.subtractFlag:
            difference = self.image.astype(np.int16) - self.background.astype(np.int16)
            self.image = np.clip(difference, 0, 255).astype(np.uint8)

        # Save image
        if self.continuousFlag:
           self.saveImage()

        # Show new image (use transpose as pyqtgraph plots [xaxis, yaxis] and numpy plots [yaxis, xaxis])
        self.imageView.setImage(self.image.T, autoLevels=False, levels=(0,255), autoRange=False) 
        # view = self.imageView.getView()
        # self.imageView.getView().setLimits(minXRange=0, maxXRange=self.image_w, minYRange=0, maxYRange=self.image_h)#Min=0, yMin=0, xMax=self.image_w, yMax=self.image_h)

        # view.setLimits( maxXRange=self.image_w)
        # view.setLimits( maxYRange=self.image_h)
        # view.setLimits(yMin=0, yMax=self.image_h, maxYRange=self.image_h)

        # Read ROI
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
            pixelSum = roi_image.sum()
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
            centroid_x, centroid_y, xrms, yrms, pixelSum = 0, 0, 0, 0, 0


        # Print instantaneous beam stats and roi dimensions
        self.xcInstant.setText(self.format_units(centroid_x))
        self.ycInstant.setText(self.format_units(centroid_y))
        self.xrmsInstant.setText(self.format_units(xrms))
        self.yrmsInstant.setText(self.format_units(yrms))
        self.pixelSumInstant.setText(self.format_counts(pixelSum))
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
        self.pixelSumQueue.append(pixelSum)
        self.xcAvg.setText(self.format_units(computeQueueMean(self.xcQueue)))
        self.ycAvg.setText(self.format_units(computeQueueMean(self.ycQueue)))
        self.xrmsAvg.setText(self.format_units(computeQueueMean(self.xrmsQueue)))
        self.yrmsAvg.setText(self.format_units(computeQueueMean(self.yrmsQueue)))
        self.pixelSumAvg.setText(self.format_counts(computeQueueMean(self.pixelSumQueue)))

        # Append image stats and magnet values to scanData
        if self.scanFlag:
            currentStats = {
                # Image stats
                'xc':centroid_x, 'yc':centroid_y, 'xrms':xrms, 'yrms':yrms, 'sum':pixelSum,

                # Settings
                'FWindex':self.get_setting('FWindex'),
                'gain':self.get_setting('gain'),
                'exposure':self.get_setting('exposure'),
                'camera':self.get_setting('label'),

                # Magnet currents
                'x1':self.magnets.X1.get_current(),
                'y1':self.magnets.Y1.get_current(),
                'x2':self.magnets.X2.get_current(),
                'y2':self.magnets.Y2.get_current(),
                'x3':self.magnets.X3.get_current(),
                'y3':self.magnets.Y3.get_current(),
                'x4':self.magnets.X4.get_current(),
                'y4':self.magnets.Y4.get_current(),
            }
            self.scanData.append(currentStats)


    def format_units(self, pixels):
        #Return as mm or um.
        dist = pixels * self.get_setting('calibration')
        return f'{dist:.2f}mm' if dist>=1 else f'{dist*1000:.0f}um'

    def format_counts(self, count):
        return f'{count:.2e}'
            

    def closeEvent(self, event):
        # Stop cameras
        self.imageAcq.stop()

        # Close filter wheels in parallel (take 10sec for each connection to close)
        print('Closing filter wheels')
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(lambda conn:conn.close_conn(), self.filter_wheels)

        print('Closing window')
        event.accept()


# Run Application
if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


# %%