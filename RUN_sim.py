import pandas as pd
import numpy as np

INPUT_DATA_FILENAME = 'simulation_data/actual_turn_data.csv'

def wrap(a):
    return (a + np.pi) % (2.0 * np.pi) - np.pi

def curvature_three_points(p0, p1, p2):
    a = np.linalg.norm(p1 - p0)
    b = np.linalg.norm(p2 - p1)
    c = np.linalg.norm(p2 - p0)
    if min(a, b, c) < 1e-6:
        return 0.0
    cross = ((p1[0] - p0[0]) * (p2[1] - p0[1])
             - (p1[1] - p0[1]) * (p2[0] - p0[0]))
    return float(2.0 * cross / (a * b * c))

def load_data():
    df = pd.to_csv(INPUT_DATA_FILENAME)


if __name__ == "__main__":
    load_data()