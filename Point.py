import numpy as np
import pandas as pd
import sys

LAT0 = 35.1823543
LON0 = -97.435558

class Point:
    def __init__(self, point, pointId, turnId, initPoint="", prevPoint=""):
        self.turnId = turnId
        self.pointId = pointId
        self.type = point['type']
        self.timestamp = point['log_mono_ns']
        self.time = None

        self.lon = point['lon']
        self.lat = point['lat']
        self.speed = point['speed_mps']
        self.steer_angle = point['actual_steer_angle_deg']

        self.x, self.y = self.calcXY()

        if prevPoint != "":
            deltaX = self.x - prevPoint.x
            deltaY = self.y - prevPoint.y

            self.dist = np.sqrt((deltaX)**2 + (deltaY)**2)
            # self.heading = np.mod(np.atan2(deltaX, deltaY), 360)
            # self.delta_heading = (540 + prevPoint.heading - self.heading) % 360 - 180
        else:
            self.dist = 0
            # self.heading = 0
            # self.delta_heading = 0

        self.radius_of_curvature = self.getRadiusOfCurvature(prevPoint)
        # self.heading = self.getHeading(initPoint)

    def calcXY(self):
        x = (self.lon-LON0) * np.cos(LAT0) * 111320
        y = (self.lat-LAT0) * 110540
        return x, y

    def getRadiusOfCurvature(self, prevPoint):
        if prevPoint != "":
            return np.sqrt( (self.x-prevPoint.x)**2 + (self.y-prevPoint.y)**2)
        else:
            return 0

    # def getHeading(self, initPoint):
    #     if initPoint != "":
    #         deltaX = self.x - initPoint.x
    #         deltaY = self.y - initPoint.y

    #         return np.mod(np.atan2(deltaX, deltaY), 360)
    #     else:
    #         return 0

    def to_df(self):
        data = {
            "turnId": [self.turnId],
            "pointId": [self.pointId],
            "type": [self.type],
            "timestamp": [self.timestamp],
            "time [ns]": [self.time],
            "lon [deg]": [self.lon],
            "lat [deg]": [self.lat],
            "speed [mps]": [self.speed],
            "steer_angle [deg]": [self.steer_angle],
            "x [m]": [self.x],
            "y [m]": [self.y],
            "dist [m]": [self.dist],
            # "heading [deg]": [self.heading],
            # "delta_heading [deg]": [self.delta_heading],
        }

        return pd.DataFrame(data)

    # Print Functions
    def __str__(self):
        return (
            f"Point("
            f"pointId={self.pointId}, "
            f"turnId={self.turnId}, "
            f"timestamp={self.timestamp}, "
            f"time={self.time}, "
            f"lat={self.lat}, "
            f"lon={self.lon}, "
            f"speed={self.speed}, "
            f"steer_angle={self.steer_angle}, "
            f"x={self.x}, "
            f"y={self.y}"
            f")"
        )