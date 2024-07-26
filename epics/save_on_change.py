
# %%
from epics import caget
import numpy as np

mod_gain_pv = 'LLRF_AWG1_CH1_AmpModGainMan_SP'
mod_gain = caget(mod_gain_pv)

try:
    while True:
        new_mod_gain = caget(mod_gain_pv)
        if new_mod_gain != mod_gain:
            mod_gain = new_mod_gain
            hybridgun_forward = caget('LLRF_DAQ1_CH1_DataVoltage_RB')
            hybridgun_probe = caget('LLRF_DAQ1_CH3_DataVoltage_RB')

            np.save(f'Hybrid Waveforms/mod_gain={mod_gain:.4f}', 
                    np.array([hybridgun_forward, hybridgun_probe]))
            print(f'Mod Gain = {mod_gain:.4f}')
except KeyboardInterrupt:
    print("Script terminated by user.")

