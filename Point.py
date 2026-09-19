import numpy as np
import pandas as pd
import sys

class Point:
    def __init__(self, point, pointId, turnId, initPoint="", prevPoint=""):
        self.turnId = turnId
        self.pointId = pointId
        self.type = point['type']
        self.timestamp = point['log_mono_ns']

        self.lon = point['lon']
        self.lat = point['lat']
        self.speed = point['speed_mps']
        self.steer_angle = point['actual_steer_angle_deg']

        # recursive variables
        self.time = None
        self.x = None
        self.y = None
        self.dist = None
        self.turn_radius = None
        self.curvature = None

    def setTime(self, t0):
        self.time = self.timestamp - t0

    def setXY(self, lon0, lat0):
        self.x = (self.lon-lon0) * np.cos(lat0) * 111320
        self.y = (self.lat-lat0) * 110540

    def setDistance(self, x_prev, y_prev):
        dx = self.x - x_prev
        dy = self.y - y_prev

        self.dist = np.sqrt(dx**2 + dy**2) 

    def setTurnRadius(self, x_prev, y_prev, x_next, y_next):
        x = self.x
        y = self.y

        a = np.hypot(x_next - x, y_next - y)
        b = np.hypot(x_next - x_prev, y_next - y_prev)
        c = np.hypot(x - x_prev, y - y_prev)

        cross = ((x - x_prev) * (y_next - y_prev)
                - (y - y_prev) * (x_next - x_prev))

        if abs(cross) < 1e-6:
            self.turn_radius = np.inf  # The line is pretty much straight
        else:
            self.turn_radius = (a * b * c) / (2 * abs(cross))  

    def setCurvature(self):
        if self.turn_radius:
            self.curvature = 1 / self.turn_radius

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
            "turn_radius": [self.turn_radius],
            "curvature": [self.curvature],
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
            f"y={self.y},"
            f"dist={self.dist},"
            f"turn_radius={self.turn_radius}"
            f")"
        )