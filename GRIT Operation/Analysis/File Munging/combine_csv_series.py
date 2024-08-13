import pandas as pd
import numpy as np
import os

# Specify directory of csvs (saved from series)
quadscan_dir = '../Images/2024-08-08/Quad_Scan1'

# Read into dataframes
dfs = []
paths = [os.path.join(quadscan_dir, file) for file in os.listdir(quadscan_dir)]
dfs = [pd.read_csv(path, index_col=0, header=None).squeeze('columns') for path in paths]

# Combine and save to single csv file 
df = pd.concat(dfs, axis=1).T.reset_index(drop=True)
df.to_csv(quadscan_dir + '.csv', index=False)