# %%
from epics import caput, caget
import time

# current = epics.caget('BUN1_STM01_X_Current_RB')
# state   = epics.caget('BUN1_STM01_X_SupplyOn_RB')
# setpoint = epics.caget('BUN1_STM01_X_Setpoint_SET')

class SteeringMagnets:
    def __init__(self):
        self.X1 = SteeringMagnet('BUN1_STM01_X')
        self.Y1 = SteeringMagnet('BUN1_STM01_Y')
        self.X2 = SteeringMagnet('BUN1_STM02_X')
        self.Y2 = SteeringMagnet('BUN1_STM02_Y')
        self.X3 = SteeringMagnet('BUN1_STM03_X')
        self.Y3 = SteeringMagnet('BUN1_STM03_Y')
        self.X4 = SteeringMagnet('BUN1_STM04_X')
        self.Y4 = SteeringMagnet('BUN1_STM04_Y')

class SteeringMagnet:
    def __init__(self, label):
        self.label = label

    def get_status(self):
        status = caget(self.label + '_SupplyOn_RB')
        print(f'{self.label} status: {status}')
        return status
    
    def get_current(self):
        current = caget(self.label + '_Current_RB')
        print(f'{self.label} current: {current}')
        return current

    def set_current(self, current):
        caput(self.label+'_Setpoint_SET', current)
        caput(self.label+'_Apply_SET', 1)
        time.sleep(.2)
        caput(self.label+'_Apply_SET', 0)
        return
    
SM = SteeringMagnets()


# Turn on power supply to 0.1 Amps
# caput('BUN1_STM01_X_Enable_SET', 1)
# caput('BUN1_STM01_X_Setpoint_SET', 0.1)

# Turn off
# epics.caput('BUN1_STM01_X_Enable_SET', 0)
# epics.caput('BUN1_STM01_X_Setpoint_SET', 0)
# %%
