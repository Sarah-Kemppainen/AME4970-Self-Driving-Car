import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


from State import State
from Waypoint import Waypoint

actual_data = None

def load_turn_data(turnIDs):
    turn_data = pd.DataFrame()
    time_offset = 0

    for i, id in enumerate(turnIDs):
        df = pd.read_csv(f'turn_data/turn_{id}.csv')

        # Reset time to start at 0 for the first turn,
        # and offset subsequent turns for continuous time
        df['time [ns]'] = df['time [ns]'] + time_offset

        # Update the offset for the next turn:
        # last timestamp + 1 second (10^9 ns)
        time_offset = df['time [ns]'].iloc[-1] + 10**9

        turn_data = pd.concat([turn_data, df], ignore_index=True)

    turn_data = turn_data.drop(
        columns=['Unnamed: 0', 'timestamp', 'type', 'pointId', 'turnId'],
        errors='ignore'
    )

    turn_data.to_csv("simulation_data/actual_turn_data.csv", index=False)

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

def updateState(id, currState):
    s = currState.getNext(speed=actual_data.iloc[1]['speed [mps]'])

    wp1, wp3, wp5, wp10 = initWaypoints(id)
    s.setVariables(wp1, wp3, wp5, wp10)

    return s

def plot(actual, sim):
    # Create the graph
    plt.plot(actual['time [ns]'], actual['steer_angle [deg]'], label='actual')
    plt.plot(sim['time [ns]'], sim['steer_angle [deg]'], label='simulated')

    # Add labels and title
    plt.xlabel("time [ns]")
    plt.ylabel("steering angle [deg]")
    plt.title("Steering Angle")

    # Display the graph
    plt.show()

        # Create the graph
    plt.plot(actual['lat [deg]'], actual['lon [deg]'], label='actual')
    plt.plot(sim['lat [deg]'], sim['lon [deg]'], label='simulated')

    # Add labels and title
    plt.xlabel("latitude [deg]")
    plt.ylabel("longitude [deg]")
    plt.title("Path")

    # Display the graph
    plt.show()



if __name__ == "__main__":

    simulated_data = pd.DataFrame()

    actual_data = load_turn_data([4,5,6,7])

    currState = initState(1, actual_data.iloc[1])
    simulated_data = pd.concat([simulated_data, currState.to_df()], ignore_index=True)

    for i in range(len(actual_data)):
        if i == 0 or i == 1:
            pass

        # if i == 10616:
        if i == (len(actual_data) - 10):
            break

        nextState = updateState(i, currState)
        simulated_data = pd.concat([simulated_data, nextState.to_df()], ignore_index=True)

        currState = nextState
    
    simulated_data.to_csv("simulation_data/simulated_durn_data.csv")

    plot(actual_data, simulated_data)