from epics_utils import SteeringMagnet
import numpy as np
import time

# Define magnets, current ranges, and delay
magnet1 = SteeringMagnet('X', 1)
range1 = np.linspace(-1, 1, 5)

magnet2 = SteeringMagnet('Y', 1)
range2 = np.linspace(-1, 1, 5)

delay = 2

# Get current positions
initial1 = magnet1.getCurrent()
initial2 = magnet2.getCurrent()

# 2D raster over steering
for current1 in initial1 + range1:
    magnet1.setCurrent(current1)

    for current2 in initial2 + range2:
        magnet2.setCurrent(current2)

        time.sleep(delay)

# Set back to initial positions
magnet1.setCurrent(initial1)
magnet2.setCurrent(initial2)