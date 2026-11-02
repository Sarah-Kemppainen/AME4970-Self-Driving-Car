import numpy as np

# Equation Constants
A0 = -2.835966355544321
A1 = -0.01721223176847263

F = np.array([-1.4737909609875783, 0.8146025085747989, 
              -0.21729929507412396, 0.07625892289767063])

L = np.array([4.885365740781355, -1.5523997104444465, 
              0.5893613353076292, -0.14803583749937488])

B = np.array([-0.019595646188824947, -0.020274669756973472, 
              -0.1696682069101535, 0.12490290134762093])

K = np.array([-7.204320741854705, -1.4194730228287347])

B0 = 1
B1 = 1

B2 = np.array([1, 1])


features = {}
rel_points = {}

# Speed planner constants
DT = 0.1                 # seconds between calls -- set this to your real update interval
START_SPEED = 4.0        # cruise / max speed (m/s)
MAX_ACCEL = 1.5          # m/s^2 (max allowable acceleration limit)
MAX_DECEL = -4.0         # m/s^2 (max allowable deacceleration limit)
MAX_LATERAL_ACCEL = 1.2  # m/s^2, lower = slows more for corners
SPEED_GAIN = 1.8         # proportional gain on speed error
#If the car brakes too abruptly or the ride feels jerky, lower the speed gain.
#If it’s still too fast entering corners, raise it, or lower MAX_LATERAL_ACCEL so the target speed is lower to begin with.

def lookahead_curvature(fwd, lat):
    # VIVASH's CODE
    """Curvature (1/m) of the arc from the car, along its heading, to a waypoint
    at forward distance fwd and lateral offset lat (car frame)."""
    d2 = fwd ** 2 + lat ** 2
    if d2 < 1e-9:
        return 0.0
    return 2.0 * abs(lat) / d2

def calculate_delta_speed(speed, curvature_ahead):
    # VIVASH's CODE
    # Speed planner: brakes earlier and harder for sharp turns
    if curvature_ahead > 1e-4:
        v_curve_limit = np.sqrt(MAX_LATERAL_ACCEL / curvature_ahead)
    else:
        v_curve_limit = START_SPEED
    target_v = min(START_SPEED, v_curve_limit)
    accel = np.clip(SPEED_GAIN * (target_v - speed), MAX_DECEL, MAX_ACCEL)
  
   # Simulator does v += accel * DT, so the plugin's delta speed is accel * DT
    delta_speed = accel * DT

    return delta_speed

def getSteerCmd(actual_x, actual_y, heading_deg, actual_steer_angle_deg, speed_mps, waypoints: dict):

    x = float(actual_x)
    y = float(actual_y)

    heading = float(heading_deg)
    steer = float(actual_steer_angle_deg)

    speed = float(speed_mps)

    # ------------------------------------------------------ #
    # ----- CALCUALTE LATERAL, FORWARD AND BETA ARRAYS ----- #
    # ------------------------------------------------------ #
    for wpid, (wpx, wpy) in waypoints.items():
        # print(f"Waypoint {wpid}: x={wpx}, y={wpy}")

        dx = float(wpx) - x
        dy = float(wpy) - y

        fwd = dx * np.sin(heading) + dy * np.cos(heading)
        lat = dx * np.cos(heading) + dy * np.sin(heading)
        beta = np.atan2(lat,fwd)

        features[f"F_{wpid}"] = ( float(fwd) )
        features[f"L_{wpid}"] = ( float(lat) )
        features[f"B_{wpid}"] = ( float(beta) )

        rel_points[f"P_rel_{wpid}"] = ( float(dx), float(dy) )

    # Create final arrays
    forward = np.array([features["F_1"], features["F_3"], features["F_5"], features["F_10"]])
    lateral = np.array([features["L_1"], features["L_3"], features["L_5"], features["L_10"]])
    beta = np.array([features["B_1"], features["B_3"], features["B_5"], features["B_10"]])

    # ------------------------------------- #
    # ----- CALCULATE CURVATURE ARRAY ----- #
    # ------------------------------------- #
    # P0 = (0.0, 0.0)
    p1 = rel_points["P_rel_1"]
    p5 = rel_points["P_rel_5"]
    p10 = rel_points["P_rel_10"]

    p1_norm = np.linalg.norm(p1)
    p5_norm = np.linalg.norm(p5)
    p10_norm = np.linalg.norm(p10)

    cross = p5[0] * p10[1] - p5[1] * p10[0]
    features["k_0_5_10"] = (2 * cross) / (p5_norm * p10_norm)

    cross = p1[0] * p5[1] - p1[1] * p5[0]
    features["k_0_1_5"] = (2 * cross) / (p1_norm * p5_norm)

    # create curvature array
    curvature = np.array([features["k_0_5_10"], features["k_0_1_5"]])

    # -------------------------------------- #
    # ----- APPLY DELTA STEER EQUATION ----- #
    # -------------------------------------- #
    delta_steer = A0 + A1 * steer + F @ forward + L @ lateral + B @ beta + K @ curvature
  
  # Curvature (1/m) toward waypoint 1 (~5-9 m ahead) for speed planning
    curvature_ahead = lookahead_curvature(features["F_1"], features["L_1"])
    delta_speed = calculate_delta_speed(speed, curvature_ahead) # B0 + B1 * speed + B2 @ curvature

    '''
    Example:
    Case 1: At 4 m/s the car sees waypoint 1 at fwd = 8, lat = 2:
      curvature = 2.0 * 2 / (64 + 4) ≈ 0.059 per meter
      curve speed limit = sqrt(1.2 / 0.059) ≈ 4.5 m/s, so target_v stays at 4.0 m/s
      (the car holds speed at 4 m/s limit)

    Case 2: With lat = 4:
      curvature = 2.0 * 4 / (64 + 16) = 0.1 per meter
      curve speed limit = sqrt(1.2 / 0.1) ≈ 3.5 m/s
      speed error = 3.5 − 4 = −0.5, so accel = 1.8 × (−0.5) = −0.9 m/s²
      delta_speed = −0.9 × 0.1 = −0.09 m/s, so the car eases off slightly
    '''
  
    # print(delta_steer)
    print(delta_speed)

    # Get final steering command
    cmd_steer = steer + delta_steer
    cmd_speed = speed + delta_speed

    stop_condition = False  # check_for_hazard('image.png') ==> False: don't stop, True: stop
    if (stop_condition):
        cmd_steer = 0

        # Sharp steer left/right?
        # cmd_steer = f()

    return cmd_steer, cmd_speed


if __name__ == '__main__':
    lat0 = 35.1823032
    lon0 = -97.4356217

    lat_prev, lon_prev = 35.1823032, -97.4356217
    lat_curr, lon_curr = 35.1822512, -97.4355002

    # Convert the difference into approximate meters
    dx = (lon_curr - lon_prev) * np.cos(np.radians(lat_prev)) * 111320
    dy = (lat_curr - lat_prev) * 110540

    actual_x = ((lon_curr - lon0) * np.cos(np.radians(lat0)) * 111320)
    actual_y = (lat_prev - lat0) * 110540

    heading_rad = np.arctan2(dy, dx)
    heading_deg = np.degrees(heading_rad)

    actual_steer_angle_deg = 0.13835

    speed_mps = 0.013

    waypoints={
        1:  (0.084392442,	-8.604599257),
        3:  (0.013216667,	-27.42315022),
        5:  (-0.207414881,	-46.85845355),
        10: (0.929423079,	-80.64046606),
    }

    # Call Steering Function
    cmd_steer_angle_deg, cmd_speed_mps = getSteerCmd(actual_x, actual_y, heading_deg, actual_steer_angle_deg, speed_mps, waypoints)
    # print(cmd_steer_angle_deg)
    print(cmd_speed_mps)
