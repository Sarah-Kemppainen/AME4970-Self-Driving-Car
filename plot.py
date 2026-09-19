import sys

from bokeh.plotting import figure, show, output_file
import numpy as np


from bokeh.layouts import gridplot, column, row


def plot_turn(turn):

    x = []
    y = []
    steer_angle = []
    dist = []
    speed = []
    turn_angle = []
    curvature = []

    currDist = 0

    for p in turn.points:
        x.append(p.x)
        y.append(p.y)
        steer_angle.append(p.steer_angle)
        speed.append(p.speed)
        turn_angle.append(p.turn_angle)
        curvature.append(p.curvature)

        
        currDist = currDist + p.dist
        dist.append(currDist)

    output_file(f"graphs/turn{turn.turnId}.html")

    # create a new plot
    s1 = figure(width=600, height=500) 
    s1.line(x, y, line_width=2, color='navy')
    s1.title.text = f"Path of Turn {turn.turnId} ({turn.type})"
    s1.title.align = "center"
    s1.xaxis.axis_label = "X"
    s1.yaxis.axis_label = "Y"

    # create a new plot
    s2 = figure(width=300, height=250) 
    s2.line(dist, steer_angle, line_width=2, color='navy')
    s2.title.text = f"Steering Angle vs. Distance"
    s2.title.align = "center"
    s2.xaxis.axis_label = "Distance [m]"
    s2.yaxis.axis_label = "Steering Angle [deg]"

    s3 = figure(width=300, height=250) 
    s3.line(dist, speed, line_width=2, color='navy')
    s3.title.text = f"Speed vs. Distance"
    s3.title.align = "center"
    s3.xaxis.axis_label = "Distance [m]"
    s3.yaxis.axis_label = "Speed [mps]"

    s4 = figure(width=300, height=250) 
    s4.line(dist, turn_angle, line_width=2, color='navy')
    s4.title.text = f"Turn Angle vs. Distance"
    s4.title.align = "center"
    s4.xaxis.axis_label = "Distance [m]"
    s4.yaxis.axis_label = "Turn Angle [deg]"

    s5 = figure(width=300, height=250) 
    s5.line(dist, curvature, line_width=2, color='navy')
    s5.title.text = f"Curvature vs. Distance"
    s5.title.align = "center"
    s5.xaxis.axis_label = "Distance [m]"
    s5.yaxis.axis_label = "Curvature"


    # NEW: put the subplots in a gridplot
    # p = gridplot([[s1, s2, s3]], toolbar_location=None)
    p = row(
        s1,
        column(s2, s4),
        column(s3, s5),
        sizing_mode="fixed",
    )

    # show the results
    show(p)


