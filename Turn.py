from Point import Point

import pandas as pd
import sys

class Turn:
    def __init__(self, turnId, turn_data, bounds):
        self.turnId = turnId
        self.type = turn_data[0]['type']
        self.bounds = bounds

        self.points = self.getPoints(turn_data)
        self.size = len(self.points)

        self.totalDist = self.getTotalDistance()
        self.min_speed_point = self.getMinSpeedPoint()

    def getPoints(self, turn_data):
        point_id = 0
        points = []
        for row in turn_data:
            if point_id != 0:
                prevPoint = points[point_id-1]
                currPoint = Point(row, point_id, self.turnId, points[0], prevPoint)
            else:
                currPoint = Point(row, point_id, self.turnId)

            points.append(currPoint)
            point_id += 1

        # Set regressive properties
        p_init = points[0]
        # p_prev = None
        for p in points:
            p.time = p.timestamp - p_init.timestamp
            # p_prev = p

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

    def save(self, foldername):
        id = self.turnId
        df = pd.DataFrame()

        for point in self.points:
            pdf = Point.to_df(point)
            df = pd.concat([df, pdf], ignore_index=True)

        df.to_csv(f'{foldername}/turn_{id}.csv')

    def to_df(self):
        data = {
            "turnId": [self.turnId],
            "type": [self.type],
            "llim_lon": [self.bounds[0][0]],
            "ulim_lon": [self.bounds[0][1]],
            "llim_lat": [self.bounds[1][0]],
            "ulim_lat": [self.bounds[1][1]],
            "size": [self.size],
            "total_dist [m]": [self.totalDist],
            "min_speed_pointId": [self.min_speed_point.pointId],
            "min_speed_x": [self.min_speed_point.x],
            "min_speed_y": [self.min_speed_point.y],
            "speed_min [mps]": [self.min_speed_point.speed],
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