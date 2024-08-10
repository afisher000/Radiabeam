from epics import caget, caput, caget_many
import time

class LLRF:
    def __init__(self, label):
        self.label = label

    def setPhase(self):
        caput(self.label + 'PhaseMan_SET??')

    def getPhase(self):
        phase = caget(self.label + 'PhaseMan_SP')
        return phase

# class SteeringMagnets:
#     def __init__(self):
#         # Add steering magnets via loop
#         for num in [1,2,3,4]:
#             for coord in ['X', 'Y']:
#                 setattr(self, f'{coord}{num}', f'BUN1_STM0{num}_{coord}')

class SteeringMagnet():
    def __init__(self, coord, num):
        self.label = f'BUN1_STM0{num}_{coord}'

    def setStatus(self):
        status = caget(self.label + '_SupplyOn_RB')
        return status
    
    def getCurrent(self):
        current = caget(self.label + '_Current_RB')
        return current
    
    def setCurrent(self, current):
        if abs(current)>5:
            current = current/abs(current)*4
            print('Saturated current at 4 amps')
        else:
            caput(self.label+'_Setpoint_SET', current)
            caput(self.label+'_Apply_SET.PROC', 1)
            time.sleep(.1)
            caput(self.label+'_Apply_SET.PROC', 1)

class QuadMagnet():
    def __init__(self, num):
        self.label = f'QUAD{num}'

    def setStatus(self):
        status = caget(self.label + '_SupplyOn_RB')
        return status
    
    def getCurrent(self):
        current = caget(self.label + '_Current_RB')
        return current
    
    def setCurrent(self, current):
        if abs(current)>4:
            current = current/abs(current)*4
            print('Saturated current at 4 amps')
        else:
            caput(self.label+'_Setpoint_SET', current)
            caput(self.label+'_Apply_SET.PROC', 1)
            time.sleep(.1)
            caput(self.label+'_Apply_SET.PROC', 1)