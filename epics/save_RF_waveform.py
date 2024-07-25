# %%
from epics import caget
import numpy as np


mod_gain = caget('LLRF_AWG1_CH2_AmpModGainMan_SP')

while True:
    new_mod_gain = caget('LLRF_AWG1_CH2_AmpModGainMan_SP')
    if new_mod_gain != mod_gain:
        mod_gain = new_mod_gain
        linac1 = caget('LLRF_DAQ3_CH1_DataVoltage_RB')
        linac2 = caget('LLRF_DAQ4_CH1_DataVoltage_RB')
        np.save(f'Waveforms/mod_gain={mod_gain:.4f}', np.array([linac1, linac2]))

# %%
