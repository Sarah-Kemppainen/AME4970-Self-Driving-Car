from Data import Data

"""
How to use the Data Class:

class Data:
    data.raw      DataFrame of data parsed from 'gps' and 'lateral'
    data.turns    List of Turns (identified by entering and leaving a lat/lon region)

class Turn:
    data.turns[id].turnId           ID of Turn, type:int
    data.turns[id].type             Turn region, type:str
    data.turns[id].bounds           Bounds of turn region, [[llim_lat, ulim_lat], [llim_lon, ulim_lon]], type:list
    data.turns[id].points           List of Points
    data.turns[id].totalDist        Total distance traveled in Turn
    data.turns[id].min_speed_point  Point where the minimum speed occurs (Point stores x, y, speed, steer angle, time, etc.)
    data.turns[id].max_steer_point  Point where the maximum steering angle occurs
    data.turns[id].size             Number of points logged in turn, type:int

class Point:
    data.turns[id].points[id].pointId       ID of Point, type:int
    data.turns[id].points[id].turnId        ID of Turn that the Point is a part of, type:int
    data.turns[id].points[id].timestamp     Timestamp of when the point was logged (in nanoseconds)
                                            Normalized to the first time instance in the raw data
    data.turns[id].points[id].time          Time that the point was logged (in nanoseconds)
                                            Normalized to the first time instance of the turn
    data.turns[id].points[id].lat           Point latitude [deg]
    data.turns[id].points[id].lon           Point longitude [deg]
    data.turns[id].points[id].speed         Speed at Point  [mps]
    data.turns[id].points[id].steer_angle   Steering angle at Point [deg]

    data.turns[id].points[id].x             Local X position [m] (origin at first position logged in raw data)
    data.turns[id].points[id].y             Local Y position [m] (origin at first position logged in raw data)
    data.turns[id].points[id].dist          Distance [m] between current point and previous point
    data.turns[id].points[id].turn_radius
    data.turns[id].points[id].curvature
    data.turns[id].points[id].heading
    data.turns[id].points[id].turn_angle
"""

SAVE_FOLDER = 'turn_data'

if __name__ == "__main__":
    # Create Data instance
    data = Data()

    # # Prints readout of each turn
    for turn in data.turns:
        print(turn)

    # # Prints every point within a turn from data file
    # # would not recommend uncommenting as there is ALOT of points
    # for turn in data.turns:
    #     for point in turn.points:
    #         print(point)

    # Prints the turn ID, type and total distance of the first turn logged
    print(data.turns[0].turnId)
    print(data.turns[0].type)
    print(data.turns[0].totalDist)

    # Prints the local x, local y, and steering angle of
    # the first point logged in the first turn
    print(data.turns[0].points[0].x)
    print(data.turns[0].points[0].y)
    print(data.turns[0].points[0].steer_angle)

    # Prints the distance between the 99th point and the 100th point of Turn 0
    print(data.turns[0].points[100].dist)         

    # min_speed_point is a Point object with attributes (x, y, speed, steer_angle, etc.)
    print(type(data.turns[0].min_speed_point))
    print(data.turns[0].min_speed_point.x)
    print(data.turns[0].min_speed_point.y)
    print(data.turns[0].min_speed_point.speed)

    # Saves data to csv files
    data.save(SAVE_FOLDER)

    # Plotting
    data.plot(id=0)   # Plots turn 0
    # data.plot()         # Plots all turns