import pandas as pd

class DataParser:
    # The constructor method initializes the object's attributes
    def __init__(self, data_filename):
        self.data = pd.readcsv('data.csv')
        self.x_pos = calc_x_pos()
        self.Y_pos = calc_y_pos()

    # A method (function inside a class) to perform an action
    def calc_x_pos(self):
        return -99

    def calc_y_pos(self):
        return -999