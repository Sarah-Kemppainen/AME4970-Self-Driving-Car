
import os
import pandas as pd

from bokeh.plotting import figure, show, output_file
from bokeh.layouts import column

# Input CSV files
actual_file = "simulation_data/actual_turn_data.csv"
simulated_file = "simulation_data/simulated_turn_data_fixed.csv"

# Load data
actual = pd.read_csv(actual_file)
simulated = pd.read_csv(simulated_file)

# Ensure data is ordered by time
actual = actual.sort_values("time [ns]")
simulated = simulated.sort_values("time [ns]")

# Create output directory if it doesn't exist
os.makedirs("graphs", exist_ok=True)

output_file("graphs/turn_comparison.html", title="Actual vs Simulated Turn")

# --------------------------------------------------
# Plot 1: Latitude / Longitude path
# --------------------------------------------------
p1 = figure(
    width=800,
    height=500,
    title="Actual vs Simulated Path",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

p1.line(
    actual["lon [deg]"],
    actual["lat [deg]"],
    line_width=2,
    color="navy",
    legend_label="Actual",
)

p1.line(
    simulated["lon [deg]"],
    simulated["lat [deg]"],
    line_width=2,
    color="firebrick",
    line_dash="dashed",
    legend_label="Simulated",
)

p1.xaxis.axis_label = "Longitude [deg]"
p1.yaxis.axis_label = "Latitude [deg]"
p1.legend.location = "top_left"
p1.legend.click_policy = "hide"
p1.match_aspect = True

# --------------------------------------------------
# Plot 2: Steering angle vs time
# --------------------------------------------------
p2 = figure(
    width=800,
    height=350,
    title="Steering Angle vs Time",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

p2.line(
    actual["time [ns]"],
    actual["steer_angle [deg]"],
    line_width=2,
    color="navy",
    legend_label="Actual",
)

p2.line(
    simulated["time [ns]"],
    simulated["steer_angle [deg]"],
    line_width=2,
    color="firebrick",
    line_dash="dashed",
    legend_label="Simulated",
)

p2.xaxis.axis_label = "Time [ns]"
p2.yaxis.axis_label = "Steering Angle [deg]"
p2.legend.location = "top_left"
p2.legend.click_policy = "hide"

# --------------------------------------------------
# Display both plots
# --------------------------------------------------
layout = column(p1, p2)

show(layout)
