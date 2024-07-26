# %%
from epics import caget
import numpy as np
import time
import pandas as pd
import os

PV_names = {
    'integral_gain':'LLRF_CC_IntegralGain_SET',
    'prop_gain':'LLRF_CC_ProportionalGain_SET',
    'phase_error':'LLRF_CC_PhaseError_RB',
    'amp_error':'LLRF_CC_AmplitudeError_RB',
    'forward_power':'LLRF_DAQ1_CH1_MeanAmplitude_RB',
    'probe_power':'LLRF_DAQ1_CH3_MeanAmplitude_RB',
}

records = []
nsamples = 5*60
csv_file = 'feedback.csv'
for j in range(nsamples):
    print(j)
    record = {key:caget(pv_name) for key, pv_name in PV_names.items()}
    records.append(record)
    time.sleep(0.2)


if os.path.exists(csv_file):
    df_old = pd.read_csv(csv_file)
    df = pd.concat([df_old, pd.DataFrame(records)])
else:
    df = pd.DataFrame(records)

df.to_csv(csv_file, index=False)

import matplotlib.pyplot as plt
mask = df.integral_gain==.0001
array = df[mask].groupby(by='prop_gain')['forward_power'].std()
plt.plot(array)
plt.show()
