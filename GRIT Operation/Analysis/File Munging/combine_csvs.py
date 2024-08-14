import pandas as pd
import numpy as np
import os

# Specify directory of csvs (saved from series)
quadscan_dir = '../../Scans/2024-08-13/Quadscan'


# Read into dataframes
dfs = []
paths = [os.path.join(quadscan_dir, file) for file in os.listdir(quadscan_dir)]
dfs = [pd.read_csv(path) for path in paths]

# Combine and save to single csv file 
df = pd.concat(dfs, axis=0).reset_index(drop=True)
df.to_csv(quadscan_dir + '.csv', index=False)
