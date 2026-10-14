import numpy as np
import pandas as pd

A0 = -3.1394
A1 = 0.9821
A2 = np.array([-1.8182, 1.2586, -0.4677, 0.1094])
A3 = np.array([6.0117, -1.9295, 0.8045, -0.2024])
A4 = np.array([-0.0275, -0.0120, -0.2373, 0.1898])
A5 = np.array([16.2476, -1.1744])

EARTH_RADIUS = 6_371_000.0

class State:

    def __init__(self, time, lon, lat, speed, steer_angle, x, y, heading,):
        self.time = float(time)
        self.lon = float(lon)
        self.lat = float(lat)
        self.speed = float(speed)
        self.steer_angle = float(steer_angle)
        self.x = float(x)
        self.y = float(y)
        self.heading = float(heading)

        if np.isnan(self.heading):
            print("error")

        # Recursive
        self.F = np.zeros(4)
        self.L = np.zeros(4)
        self.DPHI = np.zeros(4)
        self.K = np.zeros(2)

    @staticmethod
    def calculateCurvature(p0, p1, p2):
        """
        Signed curvature through three points in (east, north) coordinates.
        Positive means a left turn.
        Returns curvature in 1/meters.
        """
        a = np.linalg.norm(p1 - p0)
        b = np.linalg.norm(p2 - p1)
        c = np.linalg.norm(p2 - p0)

        if min(a, b, c) < 1e-8:
            return 0.0

        # Twice the signed triangle area
        cross = (
            (p1[0] - p0[0]) * (p2[1] - p0[1])
            - (p1[1] - p0[1]) * (p2[0] - p0[0])
        )

        # Signed curvature = 4 * triangle area / (a * b * c)
        return 2.0 * cross / (a * b * c)

    def setVariables(self, wp1, wp3, wp5, wp10):
        waypoints = {
            1: wp1,
            3: wp3,
            5: wp5,
            10: wp10,
        }

        # Compass heading: clockwise from north.
        # Convert to radians.
        heading = np.deg2rad(self.heading)

        # Vehicle forward and left unit vectors in east/north coordinates.
        forward_vec = np.array([
            np.sin(heading),
            np.cos(heading),
        ])

        left_vec = np.array([
            -np.cos(heading),
            np.sin(heading),
        ])

        # Local tangent-plane conversion around the current position.
        earth_radius = 6_371_000.0
        lat0 = np.deg2rad(self.lat)
        lon0 = np.deg2rad(self.lon)

        for i, (t, wp) in enumerate(waypoints.items()):
            lat_wp = np.deg2rad(float(wp.lat))
            lon_wp = np.deg2rad(float(wp.lon))

            delta_lon = (lon_wp - lon0 + np.pi) % (2 * np.pi) - np.pi

            east = earth_radius * np.cos(lat0) * delta_lon
            north = earth_radius * (lat_wp - lat0)

            displacement = np.array([east, north])

            self.F[i] = np.dot(displacement, forward_vec)
            self.L[i] = np.dot(displacement, left_vec)

            self.DPHI[i] = np.arctan2(self.L[i], self.F[i])

            distance_sq = self.F[i]**2 + self.L[i]**2

        # Displacements in local east/north coordinates.
        p0 = np.array([0.0, 0.0])

        p1 = np.array([
            earth_radius * np.cos(lat0) *
            ((np.deg2rad(float(wp1.lon)) - lon0 + np.pi) % (2 * np.pi) - np.pi),
            earth_radius * (np.deg2rad(float(wp1.lat)) - lat0),
        ])

        p5 = np.array([
            earth_radius * np.cos(lat0) *
            ((np.deg2rad(float(wp5.lon)) - lon0 + np.pi) % (2 * np.pi) - np.pi),
            earth_radius * (np.deg2rad(float(wp5.lat)) - lat0),
        ])

        p10 = np.array([
            earth_radius * np.cos(lat0) *
            ((np.deg2rad(float(wp10.lon)) - lon0 + np.pi) % (2 * np.pi) - np.pi),
            earth_radius * (np.deg2rad(float(wp10.lat)) - lat0),
        ])

        # K[0] = curvature through point 0, WP5, WP10
        self.K[0] = self.calculateCurvature(p0, p5, p10)

        # K[1] = curvature through point 0, WP1, WP5
        self.K[1] = self.calculateCurvature(p0, p1, p5)


        return self.F, self.L, self.DPHI, self.K

    def getNext(self, speed):
        speed_next = float(speed)

        dt = 1e9

        t_next = self.time + dt

        # Predict the next steering angle from your fitted model.
        steer_angle_next = (
            A0
            + A1 * self.steer_angle
            + np.dot(A2, self.F)
            + np.dot(A3, self.L)
            + np.dot(A4, self.DPHI)
            + np.dot(A5, self.K)
        )

        # Estimate path curvature from the two waypoint-based curvatures.
        curvature = np.mean(self.K)

        # Update compass heading (clockwise from north).
        heading_rate_rad = -self.speed * curvature
        heading_next = (
            self.heading
            + np.degrees(heading_rate_rad * dt)
        ) % 360.0

        # Use midpoint heading for position propagation.
        heading_mid = np.radians(
            self.heading
            + 0.5 * (heading_next - self.heading
                    + 180.0) % 360.0 - 90.0
        )

        dx = self.speed * np.sin(heading_mid) * dt
        dy = self.speed * np.cos(heading_mid) * dt

        x_next = self.x + dx
        y_next = self.y + dy

        # Convert the position change to GPS coordinates.
        lat_next = self.lat + np.degrees(dy / EARTH_RADIUS)

        cos_lat = np.cos(np.radians(self.lat))
        if abs(cos_lat) < 1e-8:
            raise ValueError(
                "Longitude update is ill-conditioned near the poles"
            )

        lon_next = self.lon + np.degrees(
            dx / (EARTH_RADIUS * cos_lat)
        )
        lon_next = (lon_next + 180.0) % 360.0 - 180.0

        return State(
            t_next,
            lon_next,
            lat_next,
            speed_next,
            steer_angle_next,
            x_next,
            y_next,
            heading_next,
        )

    def to_df(self,):
        return pd.DataFrame([{
            "time [ns]": self.time,
            "lon [deg]": self.lon,
            "lat [deg]": self.lat,
            "speed [mps]": self.speed,
            "steer_angle [deg]": self.steer_angle,
            "x [m]": self.x,
            "y [m]": self.y,
            "heading": self.heading,
        }])