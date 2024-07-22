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


mw_Ui, mw_Base = uic.loadUiType('image_window.ui')
class MainWindow(mw_Base, mw_Ui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setupGraphics()

        # Connect to ImageAcquisition class
        self.imageAcq = ImageAcquisition()
        self.imageAcq.image_ready.connect(self.update_image)


        self.acquireButton.clicked.connect(self.toggleAcquisition)
        self.acquireButton.setCheckable(True)
        self.acquireFlag = False

        self.roiButton.clicked.connect(self.toggleROI)
        self.roiButton.setCheckable(True)
        self.roiFlag = False

    def toggleAcquisition(self):
        self.acquireFlag = not self.acquireFlag

    def toggleROI(self):
        self.roiFlag = not self.roiFlag
        self.roi_item.setVisible(self.roiFlag)


    def setupGraphics(self):
        # Create graphicsScene, add to graphicsView
        self.imageView = pg.ImageView()
        self.imageLayout.addWidget(self.imageView)

        # Create ROI
        self.roi_item = pg.RectROI([0, 0], [100, 100], pen='r')
        self.roi_item.isVisible(False)
        self.imageView.addItem(self.roi_item)

        self.imageView.ui.roiBtn.hide()  # Hide default ROI button
        self.imageView.ui.histogram.hide()  # Hide histogram
        self.imageView.ui.menuBtn.hide()  # Hide the menu button (if available)


    def update_image(self, image):
        if self.acquireFlag:
            # Save zoom state
            view = self.imageView.getView()
            zoom_state = view.viewRange()

            # Add to imageView, apply zoom state
            self.imageView.setImage(image[0])
            view.setRange(xRange=zoom_state[0], yRange=zoom_state[1], padding=0)


# Application execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    # %%
