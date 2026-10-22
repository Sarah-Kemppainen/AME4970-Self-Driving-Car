import numpy as np
import pandas as pd

from State import State
from Waypoint import Waypoint

actual_data = None

def load_turn_data(turnIDs):
    turn_data = pd.DataFrame()
    for id in turnIDs:
        df = pd.read_csv(f'turn_data/turn_{id}.csv')
        turn_data = pd.concat([turn_data, df], ignore_index=True)

    turn_data = turn_data.drop(columns=['Unnamed: 0', 'timestamp', 'type', 'pointId', 'turnId'])
    turn_data.to_csv("simulation_data/actual_turn_data.csv")

    return turn_data

def initWaypoints(id):
    dr = actual_data.iloc[id + 1]
    wp1 = Waypoint(dr['lat [deg]'], dr['lon [deg]'])

    dr = actual_data.iloc[id + 3]
    wp3 = Waypoint(dr['lat [deg]'], dr['lon [deg]'])

    dr = actual_data.iloc[id + 5]
    wp5 = Waypoint(dr['lat [deg]'], dr['lon [deg]'])

    dr = actual_data.iloc[id + 10]
    wp10 = Waypoint(dr['lat [deg]'], dr['lon [deg]'])

    return wp1, wp3, wp5, wp10


def initState(id, data_row):
    dr = data_row
    s = State(dr['time [ns]'], dr['lon [deg]'], dr['lat [deg]'], dr['speed [mps]'], dr['steer_angle [deg]'], dr['x [m]'], dr['y [m]'], dr['heading'])

    wp1, wp3, wp5, wp10 = initWaypoints(id)
    s.setVariables(wp1, wp3, wp5, wp10)

    return s
   

if __name__ == "__main__":

    simulated_data = pd.DataFrame()

    actual_data = load_turn_data([4,5,6,7])

    currState = initState(0, actual_data.iloc[0])
    simulated_data = pd.concat([simulated_data, currState.to_df()], ignore_index=True)


    nextState = currState.getNext(speed=actual_data.iloc[1]['speed [mps]'])
    print(nextState.steer_angle)
    simulated_data = pd.concat([simulated_data, nextState.to_df()], ignore_index=True)
    
    simulated_data.to_csv("simulation_data/simulated_durn_data.csv")