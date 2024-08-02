# %%
test = 5

# %%
import sys
import os
import numpy as np

from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit
from PyQt6 import uic

from PIL import Image
from datetime import datetime
from collections import deque
from utils import fit_gaussian_with_offset, Settings, computeQueueMean, SteeringMagnets, Camera, FilterWheel
from scipy.ndimage import rotate

import pyqtgraph as pg
import pandas as pd
import concurrent.futures

''' 
WORK TO BE DONE
 - Add info to scanData including calibration, camera label and SN, filterwheel
 - Ellipse fitting is very slow?
'''

# GUI Window Class
mw_Ui, mw_Base = uic.loadUiType('window.ui')
class MainWindow(mw_Base, mw_Ui):
    TESTING = False
    image_h = 1024
    image_w = 1280
    SCAN_MAX_SHOTS = 1000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Read camera settings
        camera_settings = pd.read_csv('camera_settings.csv')
        self.settings = [Settings(**row.to_dict()) for _, row in camera_settings.iterrows()]
        self.filter_wheels = [FilterWheel(COM, self.TESTING) for COM in camera_settings['COM']]

        # Fill combo menus
        self.cameraCombo.addItems([label for label in camera_settings['label']])
        self.acqmodeCombo.addItems(["FreeRun", "Triggered"])
        self.colormapCombo.addItems(['viridis', 'turbo', 'plasma', 'inferno', 'magma'])
        self.filterCombo.addItems(['100%', '50%', '10%', '1%', '0%'])

        # Setup 
        self.setupGraphics() 
        self.setupQueues(self.shotsInput.value())

        # Establish communication with epics for reading/writing magnets
        self.magnets = SteeringMagnets(self.TESTING)

        # Connect to camera, connect callback, and start
        self.camera = Camera(self.get_setting('ID'), self.TESTING)
        self.camera.image_ready.connect(self.updateImage)
        self.camera.start()


        #----- Signals and slots (in order of gui) -----#
        # Acquisition
        self.acquireButton.clicked.connect(self.toggleAcquisition)
        self.acquireButton.setCheckable(True)
        self.acquireFlag = False
        
        self.acqmodeCombo.currentIndexChanged.connect(self.changeAcqMode)

        # Camera
        self.cameraCombo.currentIndexChanged.connect(self.changeCamera)
        self.gainInput.valueChanged.connect(self.changeGain)
        self.exposureInput.valueChanged.connect(self.changeExposure)
        self.colormapCombo.currentIndexChanged.connect(self.changeColormap)

        # Background
        self.setButton.clicked.connect(self.setBackground)
        self.subtractButton.clicked.connect(self.toggleBackgroundSubtraction)
        self.subtractButton.setCheckable(True)
        self.subtractFlag = False
        self.setFlag = False

        # Saving
        self.singleButton.clicked.connect(self.saveImage)
        self.continuousButton.clicked.connect(self.toggleSaveContinuous)
        self.continuousButton.setCheckable(True)
        self.continuousFlag = False


        # Filter Wheel
        self.filterCombo.currentIndexChanged.connect(self.changeFilter)

        # Image Analysis
        self.analyzeButton.clicked.connect(self.toggleAnalysis)
        self.analyzeButton.setCheckable(True)
        self.analysisFlag = False

        self.ellipseButton.clicked.connect(self.toggleEllipse)
        self.ellipseButton.setCheckable(True)
        self.ellipseFlag = False

        self.shotsInput.valueChanged.connect(self.changeShots)
        self.resetButton.clicked.connect(self.resetQueues)

        self.roiButton.clicked.connect(self.toggleROI)
        self.roiButton.setCheckable(True)
        self.roiFlag = False

        # Scan
        self.runscanButton.clicked.connect(self.toggleScan)
        self.runscanButton.setCheckable(True)
        self.scanFlag = False


    #----- Setup Functions -----#
    def setupGraphics(self):
        # Set image widget to correct aspect ratio
        scale = .5
        self.imageWidget.setFixedSize(int(self.image_w*scale), int(self.image_h*scale))

        # Create graphicsScene, add to graphicsView
        self.imageView = pg.ImageView()
        self.imageLayout.addWidget(self.imageView)
        self.imageView.setImage(np.zeros((self.image_w, self.image_h)), autoLevels=False, levels=(0,255), autoRange=False) 


        # Create ROI
        self.ROI = pg.RectROI([self.image_w//4, self.image_h//4], [self.image_w//2, self.image_h//2], pen='r')
        self.ROI.setVisible(False)
        self.imageView.addItem(self.ROI)

        # Create colormap
        self.imageView.setColorMap(pg.colormap.get(self.colormapCombo.currentText()))

        # Remove default pyqtgraph options
        self.imageView.ui.roiBtn.hide()  # Hide default ROI button
        self.imageView.ui.histogram.hide()  # Hide histogram
        self.imageView.ui.menuBtn.hide()  # Hide the menu button

        # Set image range and background
        view = self.imageView.getView()
        view.setLimits(xMin=0, yMin=0, xMax=self.image_w, yMax=self.image_h)
        view.setRange(xRange=(0, self.image_w), yRange=(0,self.image_h), padding=0)
        view.setBackgroundColor('w')

        # Ellipse
        self.ellipse = pg.PlotDataItem(pen=pg.mkPen(None), width=2)
        self.imageView.addItem(self.ellipse)



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

    def changeAcqMode(self, index):
        acqmode = self.acqmodeCombo.itemText(index)
        print(f'{acqmode}')
        self.camera.set('acqMode', acqmode)

    #----- Camera Functions -----#
    def changeCamera(self):
        # Stop acquisition
        print('Stop camera')
        self.camera.stop()

        # Change camera ID in camera and restart
        ID = self.get_setting('ID')
        self.camera.set('ID', ID)
        self.camera.start()

        # Change gui settings
        self.gainInput.setValue(self.get_setting('gain'))
        self.exposureInput.setValue(self.get_setting('exposure'))
        self.filterCombo.setCurrentIndex(self.get_setting('filter_index'))
    
    def changeGain(self, gain):
        self.set_setting('gain', gain)
        self.camera.set('gain', gain)

        # Background subtraction is removed when changing gain
        self.subtractFlag = False
        self.subtractButton.setChecked(False)
    
    def changeExposure(self, exposure):
        self.set_setting('exposure', exposure)
        self.camera.set('exposure', exposure)

    def changeColormap(self, index):
        colormap = self.colormapCombo.itemText(index)
        self.imageView.setColorMap(pg.colormap.get(colormap))
    
    #----- Background Functions -----#
    def setBackground(self):
        if not self.subtractFlag:
            self.background = self.image
            self.setFlag = True

    def toggleBackgroundSubtraction(self):
        if self.setFlag:
            self.subtractFlag = not self.subtractFlag

    #----- Saving Functions -----#
    def saveImage(self):
        pil_image = Image.fromarray(self.image)

        # Ensure image directory for today's date
        datestamp = datetime.now().strftime("%Y-%m-%d")
        image_dir = os.path.join('Images', datestamp)
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        # Save image with timestamp and label
        label = self.get_setting('label')
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        filepath = os.path.join(image_dir, f'{timestamp}_{label}.png')
        pil_image.save(filepath)

    def toggleSaveContinuous(self):
        self.continuousFlag = not self.continuousFlag

    #----- Scan Functions -----#
    def toggleScan(self):
        # Toggle scan flag
        self.scanFlag = not self.scanFlag

        # Reset scanData or save to file
        if self.scanFlag:
            self.scanData = []
        else:
            # Ensure image directory for today's date
            datestamp = datetime.now().strftime("%Y-%m-%d")
            scan_dir = os.path.join('Scans', datestamp)
            if not os.path.exists(scan_dir):
                os.makedirs(scan_dir)

            # Window to name file
            timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            default_filename = f'{timestamp} measurement.csv'
            filename, confirmation = QInputDialog.getText(self, 'File Name', 'Enter the file name:', QLineEdit.EchoMode.Normal, default_filename)
            
            # Save scan data
            if confirmation:
                filepath = os.path.join(scan_dir, filename)
                pd.DataFrame(self.scanData).to_csv(filepath, index=False)
              

    #----- Filter Wheel Functions -----#
    def changeFilter(self, filter_index):
        camera_index = self.cameraCombo.currentIndex()
        self.filter_wheels[camera_index].move(filter_index+1) #filter_index counts from 0, FilterWheel counts from 1
        self.set_setting('filter_index', filter_index)


    #----- Image Analysis Functions -----#
    def toggleAnalysis(self):
        self.analysisFlag = not self.analysisFlag
        self.resetQueues()

        if not self.analysisFlag and self.ellipseFlag:
            self.toggleEllipse()
    
    def toggleROI(self):
        self.roiFlag = not self.roiFlag
        self.ROI.setVisible(self.roiFlag)

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

    def changeShots(self, shots):
        self.setupQueues(shots)

    def resetQueues(self):
        self.xcQueue.clear()
        self.ycQueue.clear()
        self.xrmsQueue.clear()
        self.yrmsQueue.clear()
        self.pixelSumQueue.clear()
    
    #----- Main Image acquisition -----#

    def updateImage(self, image):
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

        # Read ROI
        if self.roiFlag:
            x1, y1 = self.ROI.pos()
            w, h = self.ROI.size()
            x1 = max(0, x1)
            y1 = max(0, y1)
            w = min(self.image_w-x1, w)
            h = min(self.image_h-y1, h)
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
                semi_major = np.sqrt(np.abs(eigvalues[0]))
                semi_minor = np.sqrt(np.abs(eigvalues[1]))
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
        self.avgLabel.setText(f'Avg. ({len(self.xcQueue)})')

        self.currentStats = {}
            #     # Timestamp
            #     'current_time':datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f"),

            #     # Image stats
            #     'xc':centroid_x, 'yc':centroid_y, 'xrms':xrms, 'yrms':yrms, 'sum':pixelSum,

            #     # Settings
            #     'filter_index':self.get_setting('filter_index'),
            #     'gain':self.get_setting('gain'),
            #     'exposure':self.get_setting('exposure'),
            #     'camera':self.get_setting('label'),
            #     'serial':self.get_setting('SN'),

            #     # Magnet currents
            #     'x1':self.magnets.X1.getCurrent(),
            #     'y1':self.magnets.Y1.getCurrent(),
            #     'x2':self.magnets.X2.getCurrent(),
            #     'y2':self.magnets.Y2.getCurrent(),
            #     'x3':self.magnets.X3.getCurrent(),
            #     'y3':self.magnets.Y3.getCurrent(),
            #     'x4':self.magnets.X4.getCurrent(),
            #     'y4':self.magnets.Y4.getCurrent(),
            # }
        

        # Append image stats and magnet values to scanData
        if self.scanFlag:

            self.scanData.append(currentStats)

            # Terminate if scanData > 100 shots (raise later)
            if len(self.scanData)>self.SCAN_MAX_SHOTS:
                self.runscanButton.setChecked(False)
                self.toggleScan() # call callback function manually



    #----- Functions to access settings -----#    
    def get_setting(self, attribute):
        index = self.cameraCombo.currentIndex()
        return getattr(self.settings[index], attribute)
    
    def set_setting(self, attribute, value):
        index = self.cameraCombo.currentIndex()
        setattr(self.settings[index], attribute, value)

    #----- Formatting functions -----#
    def format_units(self, pixels):
        #Return as mm or um.
        dist = pixels * self.get_setting('calibration')
        return f'{dist:.2f}mm' if dist>=1 else f'{dist*1000:.0f}um'

    def format_counts(self, count):
        return f'{count:.2e}'
            
    #----- Override close function -----#
    def closeEvent(self, event):
        # Stop cameras
        self.camera.stop()

        # Close filter wheels in parallel (take 10sec for each connection to close)
        print('Closing filter wheels')
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(lambda conn:conn.closeConnection(), self.filter_wheels)

        print('Closing window')
        event.accept()


# Run Application
if __name__=="__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


# %%