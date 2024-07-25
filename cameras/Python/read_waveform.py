# %%
from epics import caget
import numpy as np
import matplotlib.pyplot as plt

pv_name = 'LLRF_DAQ4_CH1_DataAmplitude_RB'
pv_name = 'LLRF_DAQ4_CH1_DataVoltage_RB'
waveform = caget(pv_name)   
plt.plot(waveform)
# %%
