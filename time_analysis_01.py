from netkeiba_lib import time_list
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

while True:
    # course = input('place?: ')
    tr = input('track?: ')
    dst = input('distance?: ')
    data_frames = time_list(track=tr, distance=dst)
    sub_frames = data_frames.groupby('race_id')
    for name, sub_frame in sub_frames:
        cen = (sub_frame - sub_frame.mean()) / sub_frame.std()
        try:
            res = pd.concat([res, cen])
        except:
            res = cen
    else:
        print(np.corrcoef(res['agari'], res['time']))
        plt.scatter(res['agari'], res['time'] -  res['agari'], s=1)
        plt.show()
