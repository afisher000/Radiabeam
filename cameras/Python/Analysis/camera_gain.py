# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

csv_path = 'Scans/2024-07-26/2024-07-26-13-55-38.csv'
df = pd.read_csv(csv_path)

fig, ax = plt.subplots()
ax.plot(df['gain'], df['sum'])
ax.set_xlabel('Gain')
ax.set_ylabel('Pixel Sum')

