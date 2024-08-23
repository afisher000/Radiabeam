from epics_utils import SteeringMagnet
import numpy as np
import time

# Define magnets, current ranges, and delay
magnet1 = SteeringMagnet('X', 1)
range1 = np.linspace(-1, 1, 5)

magnet2 = SteeringMagnet('Y', 1)
range2 = np.linspace(-1, 1, 5)

delay = 2

# 2D raster over steering
for current1 in range1:
    magnet1.setCurrent(current1)

    for current2 in range2:
        magnet2.setCurrent(current2)

        time.sleep(delay)

# Set to zero
magnet1.setCurrent(0)
magnet2.setCurrent(0)