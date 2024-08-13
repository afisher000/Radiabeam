from epics_utils import SteeringMagnet, QuadMagnet
import numpy as np
import time

# Define magnets, current ranges, and delay
quad1 = QuadMagnet(1)
quad2 = QuadMagnet(2)
quad3 = QuadMagnet(3)

quads_start = np.array([2, -2, 2])
quads_end = np.array([4, -4, 4])

quad1_initial = quad1.getCurrent()
quad2_initial = quad2.getCurrent()
quad3_initial = quad3.getCurrent()

print(f'Initial: [ {quad1_initial}, {quad2_initial}, {quad3_initial}]')

current_noise = 0.0 # random noise is added to quad curent at each step
num_steps = 11
delay = 3

for j in range(num_steps):
    nominal = quads_start + (quads_end-quads_start)*(j)/(num_steps-1)
    noise = (2*np.random.random(3) - 1) * ( current_noise)
    values = nominal+noise

    quad1.setCurrent(values[0])
    quad2.setCurrent(values[1])
    quad3.setCurrent(values[2])
    print(f'Values: {values}')

    time.sleep(delay)


quad1.setCurrent(quad1_initial)
quad2.setCurrent(quad2_initial)
quad3.setCurrent(quad3_initial)