import numpy as np
import pandas as pd
import sys

LAT0 = 35.1823543
LON0 = -97.435558

class Point:
    def __init__(self, point, pointId, turnId, prevPoint=""):
        self.turnId = turnId
        self.pointId = pointId
        self.type = point['type']
        self.time = point['log_mono_ns']
        self.lon = point['lon']
        self.lat = point['lat']
        self.speed = point['speed_mps']
        self.steer_angle = point['actual_steer_angle_deg']

        self.x, self.y = self.calcXY()

        if prevPoint != "":
            self.dist = np.sqrt((self.x-prevPoint.x)**2 + (self.y-prevPoint.y)**2)
        else:
            self.dist = 0

    def calcXY(self):
        x = (self.lon-LON0) * np.cos(LAT0) * 111320
        y = (self.lat-LAT0) * 110540
        return x, y

    def to_df(self):
        data = {
            "turnId": [self.turnId],
            "pointId": [self.pointId],
            "type": [self.type],
            "time [ns]": [self.time],
            "lon [deg]": [self.lon],
            "lat [deg]": [self.lat],
            "speed [mps]": [self.speed],
            "steer_angle [deg]": [self.steer_angle],
            "x [m]": [self.x],
            "y [m]": [self.y],
            "dist [m]": [self.dist],
        }

        return pd.DataFrame(data)

    # Print Functions
    def __str__(self):
        return (
            f"Point("
            f"pointId={self.pointId}, "
            f"turnId={self.turnId}, "
            f"time={self.time}, "
            f"lat={self.lat}, "
            f"lon={self.lon}, "
            f"speed={self.speed}, "
            f"steer_angle={self.steer_angle}, "
            f"x={self.x}, "
            f"y={self.y}"
            f")"
        )