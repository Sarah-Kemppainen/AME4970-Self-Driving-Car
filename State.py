import numpy as np
import pandas as pd

# 20 Hz model coefficients (predict steering 0.05 s ahead)
A0 = -3.1394
A1 = 0.9821
A2 = np.array([-1.8182, 1.2586, -0.4677, 0.1094])
A3 = np.array([6.0117, -1.9295, 0.8045, -0.2024])
A4 = np.array([-0.0275, -0.0120, -0.2373, 0.1898])
A5 = np.array([16.2476, -1.1744])

EARTH_RADIUS = 6_371_000.0
DT_S = 0.05
DT_NS = DT_S * 1e9

class State:
    def __init__(self, time, lon, lat, speed, steer_angle, x, y, heading):
        self.time = float(time)          # ns
        self.lon = float(lon)
        self.lat = float(lat)
        self.speed = float(speed)        # m/s
        self.steer_angle = float(steer_angle)
        self.x = float(x)
        self.y = float(y)
        self.heading = float(heading) % 360.0  # compass: 0 north, 90 east

        self.F = np.zeros(4)
        self.L = np.zeros(4)
        self.DPHI = np.zeros(4)
        self.K = np.zeros(2)

    @staticmethod
    def calculateCurvature(p0, p1, p2):
        a = np.linalg.norm(p1 - p0)
        b = np.linalg.norm(p2 - p1)
        c = np.linalg.norm(p2 - p0)
        if min(a, b, c) < 1e-8:
            return 0.0
        cross = ((p1[0]-p0[0])*(p2[1]-p0[1])
                 - (p1[1]-p0[1])*(p2[0]-p0[0]))
        return 2.0 * cross / (a*b*c)

    def setVariables(self, wp1, wp3, wp5, wp10):
        waypoints = [wp1, wp3, wp5, wp10]

        h = np.deg2rad(self.heading)
        # SAME convention as model training:
        # forward positive ahead, lateral positive to vehicle RIGHT.
        forward_vec = np.array([np.sin(h), np.cos(h)])
        right_vec = np.array([np.cos(h), -np.sin(h)])

        lat0 = np.deg2rad(self.lat)
        lon0 = np.deg2rad(self.lon)

        local_points = []
        for i, wp in enumerate(waypoints):
            lat_wp = np.deg2rad(wp.lat)
            lon_wp = np.deg2rad(wp.lon)
            dlon = (lon_wp - lon0 + np.pi) % (2*np.pi) - np.pi
            east = EARTH_RADIUS * np.cos(lat0) * dlon
            north = EARTH_RADIUS * (lat_wp - lat0)
            displacement = np.array([east, north])
            local_points.append(displacement)

            self.F[i] = np.dot(displacement, forward_vec)
            self.L[i] = np.dot(displacement, right_vec)

            # Model coefficients were trained using DEGREES, not radians.
            self.DPHI[i] = np.degrees(np.arctan2(self.L[i], self.F[i]))

        p0 = np.array([0.0, 0.0])
        p1, _, p5, p10 = local_points
        self.K[0] = self.calculateCurvature(p0, p5, p10)
        self.K[1] = self.calculateCurvature(p0, p1, p5)
        return self.F, self.L, self.DPHI, self.K

    def predictSteering(self):
        return (A0 + A1*self.steer_angle
                + np.dot(A2, self.F)
                + np.dot(A3, self.L)
                + np.dot(A4, self.DPHI)
                + np.dot(A5, self.K))

    def getNext(self, speed):
        speed_next = float(speed)
        t_next = self.time + DT_NS
        steer_angle_next = self.predictSteering()

        # NOTE: This propagates position using waypoint curvature, not predicted steering.
        # It is useful as a reference-path simulation, but is not yet a vehicle dynamics model.
        curvature = np.mean(self.K)
        speed_mid = 0.5 * (self.speed + speed_next)

        # Signed curvature: positive is left. Compass heading increases clockwise,
        # so left curvature decreases compass heading.
        heading_rate_rad_s = -speed_mid * curvature
        heading_next = (self.heading + np.degrees(heading_rate_rad_s * DT_S)) % 360.0

        # Proper shortest-angle midpoint heading.
        delta_heading = (heading_next - self.heading + 180.0) % 360.0 - 180.0
        heading_mid = np.radians((self.heading + 0.5*delta_heading) % 360.0)

        dx = speed_mid * np.sin(heading_mid) * DT_S
        dy = speed_mid * np.cos(heading_mid) * DT_S
        x_next = self.x + dx
        y_next = self.y + dy

        lat_next = self.lat + np.degrees(dy / EARTH_RADIUS)
        cos_lat = np.cos(np.radians(self.lat))
        lon_next = self.lon + np.degrees(dx / (EARTH_RADIUS * cos_lat))
        lon_next = (lon_next + 180.0) % 360.0 - 180.0

        return State(t_next, lon_next, lat_next, speed_next,
                     steer_angle_next, x_next, y_next, heading_next)

    def to_df(self):
        return pd.DataFrame([{
            'time [ns]': self.time,
            'lon [deg]': self.lon,
            'lat [deg]': self.lat,
            'speed [mps]': self.speed,
            'steer_angle [deg]': self.steer_angle,
            'x [m]': self.x,
            'y [m]': self.y,
            'heading': self.heading,
        }])