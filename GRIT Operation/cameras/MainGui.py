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
from utils import fit_gaussian_with_offset, Settings, computeQueueMean, Camera, FilterWheel, getEpicsData
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
    TESTING = True
    image_h = 1024
    image_w = 1280
    hist_min = 100
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
        self.setupDirectories()

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
        self.imagescanButton.clicked.connect(self.toggleImageScan)
        self.imagescanButton.setCheckable(True)
        self.imagescanFlag = False
        self.scanButton.clicked.connect(self.toggleScan)
        self.scanButton.setCheckable(True)
        self.scanFlag = False

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




    #----- Setup Functions -----#
    def setupGraphics(self):
        # Set image widget to correct aspect ratio
        scale = .5
        self.imageWidget.setFixedSize(int(self.image_w*scale), int(self.image_h*scale))
        self.histWidget.setFixedSize(int(self.image_w*scale), int(0.2*self.image_h*scale))

        # Create Image and pixel histogram
        self.imageView = pg.ImageView()
        self.imageLayout.addWidget(self.imageView)
        self.imageView.setImage(np.zeros((self.image_w, self.image_h)), autoLevels=False, levels=(0,255), autoRange=False) 

        self.histPlot = pg.PlotWidget()
        self.histLayout.addWidget(self.histPlot)
        self.histPlot.clear()
        self.histPlot.plot(np.arange(257), np.zeros(256), stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))
        self.histPlot.setXRange(self.hist_min, 255)
        self.histPlot.setYRange(0, 1)
        self.histPlot.getAxis('bottom').setVisible(False)
        self.histPlot.getAxis('left').setVisible(False)

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

    def setupDirectories(self):
        datestamp = datetime.now().strftime("%Y-%m-%d")

        # Ensure image directory for today's date
        self.scan_dir = os.path.join('Scans', datestamp)
        if not os.path.exists(self.scan_dir):
            os.makedirs(self.scan_dir)

        # Ensure image directory for today's date
        self.image_dir = os.path.join('Images', datestamp)
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)

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
    def saveImage(self, imagescan=False):
        pil_image = Image.fromarray(self.image)

        # Save image and stats
        if imagescan:
            # Create scan directory
            scanimages_dir = os.path.join(self.image_dir, self.descriptionEdit.text())
            if not os.path.exists(scanimages_dir):
                os.makedirs(scanimages_dir)

            label = self.get_setting('label')
            timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            filepath = os.path.join(scanimages_dir, f'{timestamp}_{label}')

        else:
            stats = self.getStats()
            label = self.get_setting('label')
            timestamp = stats['timestamp']
            filepath = os.path.join(self.image_dir, f'{timestamp}_{label}_{self.descriptionEdit.text()}')
            pd.Series(stats).to_csv(filepath + '.csv')

        pil_image.save(filepath + '.png')
        

    def toggleImageScan(self):
        # Only allow click if scanButton not already clicked
        if self.scanButton.isChecked():
            self.imagescanButton.setChecked(False)
        else:
            self.imagescanFlag = not self.imagescanFlag
            self.toggleScanFlag()

            if self.scanFlag:
                self.scanData = []
            else:
                self.saveScanData(imagescan=True)
            
    def toggleScanFlag(self):
        # Lock descriptionEdit if currently scanning
        self.scanFlag = not self.scanFlag
        self.descriptionEdit.setReadOnly(self.scanFlag)


    def toggleScan(self):
        # Only allow click if imagescanButton not already clicked
        if self.imagescanButton.isChecked():
            self.scanButton.setChecked(False)
        else:
            self.toggleScanFlag()

            if self.scanFlag:
                self.scanData = []
            else:
                self.saveScanData(imagescan=False)



    def saveScanData(self, imagescan):
        # Window to name file
        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        if imagescan:
            scanimages_dir = os.path.join(self.image_dir, self.descriptionEdit.text())
            filepath = os.path.join(scanimages_dir, 'settings.csv')
        else:
            filepath = os.path.join(self.scan_dir, f'{timestamp}_{self.descriptionEdit.text()}.csv')
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
        if self.imagescanFlag:
           self.saveImage(imagescan=True)

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
        roi_image = self.image[int(y1):int(y1+h), int(x1):int(x1+w)]

        # Show new image (use transpose as pyqtgraph plots [xaxis, yaxis] and numpy plots [yaxis, xaxis])
        self.imageView.setImage(self.image.T, autoLevels=False, levels=(0,255), autoRange=False) 

        hist, bin_edges = np.histogram(roi_image, bins=256, range=(self.hist_min, 255))
        hist_normalized = hist / max(1, hist.max())
        self.histPlot.clear()
        self.histPlot.plot(bin_edges, hist_normalized, stepMode=True, fillLevel=0, brush=(0, 0, 255, 150))


        # Compute centroid and rms from gaussian fits (Can move to utils)
        if self.analysisFlag:

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
        self.imageStats = {'xc':centroid_x, 'yc':centroid_y, 'xrms':xrms, 'yrms':yrms, 'sum':pixelSum,
                           'roi_x':x1, 'roi_y':y1, 'roi_w':w, 'roi_h':h}

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


        

        # Append image stats and magnet values to scanData
        if self.scanFlag:

            self.scanData.append(self.getStats())

            # Terminate if scanData > 100 shots (raise later)
            if len(self.scanData)>self.SCAN_MAX_SHOTS:
                self.scanButton.setChecked(False)
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
    
    def getStats(self):
        # Read camera settings
        self.cameraStats = {
                'timestamp':datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                'filter_index':self.get_setting('filter_index'),
                'gain':self.get_setting('gain'),
                'exposure':self.get_setting('exposure'),
                'camera':self.get_setting('label'),
                'serial':self.get_setting('SN'),
            }
        # Return merged dictionaries
        return (self.cameraStats | self.imageStats | getEpicsData())

            
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