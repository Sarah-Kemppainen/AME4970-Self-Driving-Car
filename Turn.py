from Point import Point

from plot import plot_turn

import pandas as pd
import sys

class Turn:
    def __init__(self, turnId, turn_data, bounds):
        self.turnId = turnId
        self.type = turn_data[0]['type']
        self.bounds = bounds

        self.points = self.getPoints(turn_data)
        self.totalDist = self.getTotalDistance()
        self.min_speed_point = self.getMinSpeedPoint()
        self.max_steer_point = self.getMaxSteerPoint()

        self.size = len(self.points)

    def getPoints(self, turn_data):
        point_id = 0
        points = []
        for row in turn_data:
            p = Point(row, point_id, self.turnId)
            points.append(p)
            point_id += 1

        # Set recursive properties
        p_init = points[0]
        p_prev = None
        for p in points:
            p.setTime(p_init.timestamp)         # Set time
            p.setXY(p_init.lon, p_init.lat)     # Set Local XY position

            if p_prev != None:
                p.setDistance(p_prev.x, p_prev.y)   # Set distance
                p.setHeading(p_prev.x, p_prev.y)
            else:
                p.dist = 0

            p_prev = p

        spacer = 5   
        for i in range(spacer, len(points)-spacer):
            p_prev = points[i-spacer]
            p = points[i]
            p_next = points[i+spacer]

            p.setTurnRadius(p_prev.x, p_prev.y, p_next.x, p_next.y)
            p.setTurnAngle(p_prev.x, p_prev.y, p_next.x, p_next.y)

        for p in points:
            p.setCurvature()

        return points

    def getTotalDistance(self):
        dist = 0
        for point in self.points:
            dist = dist + point.dist

        return dist

    def getMinSpeedPoint(self):
        currPoint = self.points[0]

        for point in self.points:
            if point.speed <= currPoint.speed:
                currPoint = point

        return currPoint

    def getMaxSteerPoint(self):
        currPoint = self.points[0]
        
        for point in self.points:
            if point.steer_angle >= currPoint.steer_angle:
                currPoint = point

        return currPoint

    def save(self, foldername):
        id = self.turnId
        df = pd.DataFrame()

        for point in self.points:
            pdf = Point.to_df(point)
            df = pd.concat([df, pdf], ignore_index=True)

        df.to_csv(f'{foldername}/turn_{id}.csv')

    def plot(self):
        plot_turn(self)

    def to_df(self):
        data = {
            "turnId": [self.turnId],
            "type": [self.type],
            "llim_lon": [self.bounds[0][0]],
            "ulim_lon": [self.bounds[0][1]],
            "llim_lat": [self.bounds[1][0]],
            "ulim_lat": [self.bounds[1][1]],
            "total_dist [m]": [self.totalDist],
            "min_speed_pointId": [self.min_speed_point.pointId],
            "min_speed_x": [self.min_speed_point.x],
            "min_speed_y": [self.min_speed_point.y],
            "speed_min [mps]": [self.min_speed_point.speed],
            "steer_max": [self.max_steer_point.steer_angle],
            "size": [self.size],
        }
        return pd.DataFrame(data)

    # Print Functions
    def __str__(self):
        return (
            f"Turn("
            f"turnId={self.turnId}, "
            f"type={self.type}, "
            f"bounds={self.bounds}, "
            f"size={self.size}"
            f")"
        )