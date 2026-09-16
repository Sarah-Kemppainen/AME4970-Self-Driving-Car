from Data import Data
from LLMInterface import LLMInterface

"""
class Data:
    data.raw      DataFrame of data parsed from 'gps' and 'lateral'
    data.turns    List of Turns (identified by entering and leaving a lat/lon region)

class Turn:
    data.turns[id].turnId     ID of Turn, type:int
    data.turns[id].type       Turn region, type:str
    data.turns[id].bounds     Bounds of turn region, [[llim_lat, ulim_lat], [llim_lon, ulim_lon]], type:list
    data.turns[id].points     List of Points
    data.turns[id].size       Number of points logged in turn, type:int

class Point:
    data.turns[id].points[id].pointId       ID of Point, type:int
    data.turns[id].points[id].turnId        ID of Turn that the Point is a part of, type:int
    data.turns[id].points[id].time          Time that the point was logged (in nanoseconds)
                                            Normalized to the first time instance in the raw data
    data.turns[id].points[id].lat           Point latitude [deg]
    data.turns[id].points[id].lon           Point longitude [deg]
    data.turns[id].points[id].speed         Speed at Point  [mps]
    data.turns[id].points[id].steer_angle   Steering angle at Point [deg]

    data.turns[id].points[id].x             Local X position [m] (origin at first position logged in raw data)
    data.turns[id].points[id].y             Local Y position [m] (origin at first position logged in raw data)
"""

SAVE_FOLDER = 'turn_data'

if __name__ == "__main__":
    data = Data()

    # # Prints readout of each turn
    # for turn in data.turns:
    #     print(turn)

    # # Prints every point within a turn from data file
    # # would not recommend uncommenting as there is ALOT of points
    # for turn in data.turns:
    #     for point in turn.points:
    #         print(point)

    # Prints the turn ID of the first turn logged
    print(data.turns[0].turnId)

    # Prints the local x, local y and steering angle
    # of the first point in the first turn logged
    print(data.turns[0].points[0].x)
    print(data.turns[0].points[0].y)
    print(data.turns[0].points[0].steer_angle)

    # Saves data to csv files
    data.save(SAVE_FOLDER)

    # llm = LLMInterface()