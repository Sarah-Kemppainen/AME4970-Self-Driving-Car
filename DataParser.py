import pandas as pd
import numpy as np

DT = 0.01 * 1e9 # Data Frequency in ns

GPS_DATA_FILENAME = 'data/gps.csv'
LATERAL_DATA_FILENAME = 'data/lateral.csv'

class DataParser:
    # The constructor method initializes the object's attributes
    def __init__(self, ):
        self.data = self.getData()
        print(self.data)

    def getData(self):
        # Create df
        df = pd.DataFrame()

        # Read csvs
        gps_df = pd.read_csv(GPS_DATA_FILENAME)
        lateral_df = pd.read_csv(LATERAL_DATA_FILENAME)

        # Find standard start time
        t0 = max(gps_df['log_mono_ns'][0], lateral_df['log_mono_ns'][0])
        tf = min(gps_df['log_mono_ns'].iat[-1], lateral_df['log_mono_ns'].iat[-1])

        # Create new index
        t_idx = np.arange(t0, tf, DT)           # in ns

        # Remove data collected prior to t0
        for t in gps_df['log_mono_ns']:
            if t < t0:
                gps_df = gps_df.drop(gps_df[gps_df['log_mono_ns'] == t].index)
            else:
                break

        for t in lateral_df['log_mono_ns']:
            if t < t0:
                lateral_df = lateral_df.drop(lateral_df[lateral_df['log_mono_ns'] == t].index)
            else:
                break

        # Add relevant columns to new df
        df['log_mono_ns'] = t_idx - t0      # time [ns]
        df['lat'] =  np.interp(t_idx, gps_df['log_mono_ns'], gps_df['lat'])     # latitude [deg]
        df['lon'] =  np.interp(t_idx, gps_df['log_mono_ns'], gps_df['lon'])     # longitude [deg]
        df['speed_mps'] = np.interp(t_idx, gps_df['log_mono_ns'], gps_df['speed_mps'])     # speed [mps]
        df['actual_steer_angle_deg'] = np.interp(t_idx, lateral_df['log_mono_ns'], lateral_df['actual_steer_angle_deg'])

        df.to_csv('data.csv', index=False)

        return df

        