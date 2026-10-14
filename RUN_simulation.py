import numpy as np
import pandas as pd
from State import State
from Waypoint import Waypoint

DATA_FILE = 'simulation_data/actual_turn_data.csv'
OUTPUT_FILE = 'simulation_data/simulated_turn_data_fixed.csv'
RAW_DT_S = 0.01
SIM_DT_S = 0.05
SIM_STEP = int(round(SIM_DT_S / RAW_DT_S))  # 5 raw rows per 20 Hz step

def standard_heading_from_rows(a, b):
    lat0 = float(a['lat [deg]'])
    dx_east = (float(b['lon [deg]']) - float(a['lon [deg]'])) * np.cos(np.radians(lat0)) * 111320.0
    dy_north = (float(b['lat [deg]']) - float(a['lat [deg]'])) * 110540.0
    return np.degrees(np.arctan2(dx_east, dy_north)) % 360.0

def waypoint_at_seconds(data, i, seconds):
    # actual_turn_data is sampled every 0.01 s, so 1/3/5/10 sec = 100/300/500/1000 rows.
    offset = int(round(seconds / RAW_DT_S))
    r = data.iloc[i + offset]
    return Waypoint(r['lat [deg]'], r['lon [deg]'])

def set_state_waypoints(state, data, i):
    state.setVariables(
        waypoint_at_seconds(data, i, 1.0),
        waypoint_at_seconds(data, i, 3.0),
        waypoint_at_seconds(data, i, 5.0),
        waypoint_at_seconds(data, i, 10.0),
    )

def main():
    data = pd.read_csv(DATA_FILE)
    max_i = len(data) - int(round(10.0 / RAW_DT_S)) - SIM_STEP

    # Do NOT use the legacy heading column here; its convention differs from the model.
    heading0 = standard_heading_from_rows(data.iloc[0], data.iloc[1])
    r0 = data.iloc[0]
    state = State(r0['time [ns]'], r0['lon [deg]'], r0['lat [deg]'],
                  r0['speed [mps]'], r0['steer_angle [deg]'],
                  r0['x [m]'], r0['y [m]'], heading0)

    rows = [state.to_df()]
    i = 0
    while i <= max_i:
        set_state_waypoints(state, data, i)
        speed_next = data.iloc[min(i + SIM_STEP, len(data)-1)]['speed [mps]']
        state = state.getNext(speed_next)
        rows.append(state.to_df())
        i += SIM_STEP

    out = pd.concat(rows, ignore_index=True)
    out.to_csv(OUTPUT_FILE, index=False)
    print(out.head())
    print(out.tail())
    print('rows:', len(out))
    print('x range:', out['x [m]'].min(), out['x [m]'].max())
    print('y range:', out['y [m]'].min(), out['y [m]'].max())
    print('lat range:', out['lat [deg]'].min(), out['lat [deg]'].max())
    print('lon range:', out['lon [deg]'].min(), out['lon [deg]'].max())

if __name__ == '__main__':
    main()