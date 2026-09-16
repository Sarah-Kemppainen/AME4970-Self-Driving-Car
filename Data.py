import pandas as pd
import numpy as np

from Turn import Turn

DT = 0.01 * 1e9 # Data Frequency in ns

GPS_DATA_FILENAME = 'data/gps.csv'
LATERAL_DATA_FILENAME = 'data/lateral.csv'

BOUND_A = [[-97.4365, -97.435], [35.181, 35.1825]]
BOUND_B = [[-97.438, -97.4365], [35.181, 35.1825]]
BOUND_C = [[-97.438, -97.4365], [35.1825, 35.184]]
BOUND_D = [[-97.4365, -97.435], [35.1825, 35.184]]

class Data:
    # The constructor method initializes the object's attributes
    def __init__(self, ):
        self.raw = self.getRawData()
        self.turns = self.getTurns()
        
    def getRawData(self):
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

        return df

    def getTurns(self):
        df = self.raw

        # Fill type column with empty strings
        df['type'] = np.full(len(df['log_mono_ns']), "")

        turn_logger = []
        turn_counter = 0
        turns = []

        for i, row in df.iterrows():
            if (BOUND_A[0][0] <= row['lon'] <= BOUND_A[0][1]) and (BOUND_A[1][0] <= row['lat'] <= BOUND_A[1][1]):
                currType = "A"
                currBounds = BOUND_A
            elif (BOUND_B[0][0] <= row['lon'] <= BOUND_B[0][1]) and (BOUND_B[1][0] <= row['lat'] <= BOUND_B[1][1]):
                currType = "B"
                currBounds = BOUND_B
            elif (BOUND_C[0][0] <= row['lon'] <= BOUND_C[0][1]) and (BOUND_C[1][0] <= row['lat'] <= BOUND_C[1][1]):
                currType = "C"
                currBounds = BOUND_C
            elif (BOUND_D[0][0] <= row['lon'] <= BOUND_D[0][1]) and (BOUND_D[1][0] <= row['lat'] <= BOUND_D[1][1]):
                currType = "D"
                currBounds = BOUND_D
            else:
                currType = ""

            df.loc[i, 'type'] = currType

            if currType:                                                        # Wont log NaN
                if i != 0 and currType != df.loc[i - 1, 'type']:      # Add Points to Turn if type doesnt change
                    if turn_logger:
                        turn = Turn(turn_counter, turn_logger, prevBounds)
                        turns.append(turn)
                                            
                        turn_logger = []
                        turn_counter += 1

                if currType != "":
                    turn_logger.append(df.loc[i])
                    prevBounds = currBounds

        # Close final turn
        if turn_logger:
            turns.append(Turn(turn_counter, turn_logger, prevBounds))


        return turns

    def save(self, foldername):
        self.raw.to_csv(f'{foldername}/raw_data.csv', index=False)

        df = pd.DataFrame()

        for turn in self.turns:
            turn.save(foldername)

            tdf = Turn.to_df(turn)
            df = pd.concat([df, tdf], ignore_index=True)
            
        df.to_csv(f'{foldername}/turns.csv')

        print(f"data successfully saved to folder: '{foldername}'")