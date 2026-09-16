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

    def getPoints(self, turn_data):
        point_id = 0
        points = []
        for row in turn_data:
            points.append(Point(row, point_id, self.turnId))
            point_id += 1

        return points

    def save(self, foldername):
        id = self.turnId
        df = pd.DataFrame()

        for point in self.points:
            pdf = Point.to_df(point)
            df = pd.concat([df, pdf], ignore_index=True)

        df.to_csv(f'{foldername}/turn_{id}.csv')

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