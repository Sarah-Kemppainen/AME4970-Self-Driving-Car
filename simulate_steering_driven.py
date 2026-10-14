"""Train and diagnose a 20 Hz steering model from actual_turn_data.csv.

Changes from the previous script:
- Uses hard-coded coefficients exported from the original ridge fit; no training occurs at runtime.
- Resamples using timestamps (handles the three 1-second gaps in the supplied CSV).
- Uses one consistent local east/north coordinate system derived from GPS.
- Uses the dataset's route geometry and a chronological train/test split.
- Does not feed the previous predicted steering into the regression recursively.
- Separates model-only open-loop simulation from a feedback-assisted route-following
  baseline, so feedback performance is not misrepresented as model-only performance.

Offline research/demo only. Wheelbase, steering ratio, steering limits, and rate limits
must be verified before any real-vehicle use.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
INPUT_CSV = BASE / "simulation_data/actual_turn_data.csv"
OUTPUT_CSV = BASE / "simulation_data/steering_model_diagnostic.csv"
OUTPUT_PNG = BASE / "simulation_data/steering_model_diagnostic.png"

DT = 0.05  # 20 Hz
LOOKAHEAD_SECONDS = (1.0, 3.0, 5.0, 10.0)
TRAIN_FRACTION = 0.70
RIDGE_ALPHA = 25.0  # retained only as provenance; no runtime fitting is performed
EARTH_RADIUS_M = 6_371_000.0

# Hard-coded coefficients exported from fit_ridge() on the first 70% of the
# resampled actual_turn_data.csv data, using the 18 features returned by
# make_features() in exactly this order:
# For each lookahead (1, 3, 5, 10 s): [forward_m, lateral_left_m,
# bearing_rad, future_heading_change_rad], followed by two curvature features.
# The values are in RAW feature units (not standardized units).
# IMPORTANT: this fitted model tested worse than the current-steering baseline;
# these constants make the script reproducible, not validated for vehicle control.
REGRESSION_INTERCEPT = -5.714045377865119
REGRESSION_COEFFICIENTS = np.array([
    4.65818768291,       # 1 s forward distance [m]
    43.5198343511,       # 1 s lateral-left distance [m]
    506.834010548,       # 1 s bearing [rad]
    21.9936194135,       # 1 s heading change [rad]
    2.2303271018,        # 3 s forward distance [m]
    10.8454726242,       # 3 s lateral-left distance [m]
    11.7533657402,       # 3 s bearing [rad]
    -49.1531237296,      # 3 s heading change [rad]
    0.200477741404,      # 5 s forward distance [m]
    3.51816712949,       # 5 s lateral-left distance [m]
    -13.4762415935,      # 5 s bearing [rad]
    5.01326623299,       # 5 s heading change [rad]
    -1.47070183217,      # 10 s forward distance [m]
    0.0383183897329,     # 10 s lateral-left distance [m]
    -19.0990482329,      # 10 s bearing [rad]
    6.17691816115,       # 10 s heading change [rad]
    345.807378348,       # curvature feature 1 [1/m]
    -94.6190062814,      # curvature feature 2 [1/m]
], dtype=float)

# Illustrative only; replace with verified test-vehicle specifications.
WHEELBASE_M = 2.7
STEERING_RATIO = 15.0  # steering-wheel degrees per road-wheel degree
MAX_STEERING_WHEEL_DEG = 450.0
MAX_STEERING_RATE_DEG_S = 1000.0
PURE_PURSUIT_LOOKAHEAD_S = 0.75  # offline baseline; tune using verified vehicle dynamics


def wrap_rad(a):
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


def make_features(i, px, py, theta, rx, ry, theta_ref, dt):
    """Waypoint geometry in a consistent x=east, y=north, math-heading frame.
    Heading is radians, 0=east, positive counter-clockwise; left is positive.
    """
    forward = np.array([np.cos(theta), np.sin(theta)])
    left = np.array([-np.sin(theta), np.cos(theta)])
    origin = np.array([px, py])
    pts = []
    features = []
    for seconds in LOOKAHEAD_SECONDS:
        j = min(i + int(round(seconds / dt)), len(rx) - 1)
        p = np.array([rx[j] - px, ry[j] - py])
        pts.append(p)
        fwd = float(np.dot(p, forward))
        lat_left = float(np.dot(p, left))
        bearing = float(np.arctan2(lat_left, fwd))
        future_heading_change = float(wrap_rad(theta_ref[j] - theta))
        features.extend([fwd, lat_left, bearing, future_heading_change])
    features.extend([
        curvature_three_points(np.zeros(2), pts[2], pts[3]),
        curvature_three_points(np.zeros(2), pts[0], pts[2]),
    ])
    return np.asarray(features, dtype=float)


def interp_numeric(t_new, t_old, values):
    return np.interp(t_new, t_old, np.asarray(values, dtype=float))


def load_data():
    data = pd.read_csv(INPUT_CSV)
    required = ['time [ns]', 'lon [deg]', 'lat [deg]', 'speed [mps]', 'steer_angle [deg]']
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    data = data.dropna(subset=['time [ns]', 'lon [deg]', 'lat [deg]', 'speed [mps]', 'steer_angle [deg]'])
    data = data.sort_values('time [ns]').drop_duplicates('time [ns]').reset_index(drop=True)
    t_raw = (data['time [ns]'].to_numpy(dtype=float) - float(data['time [ns]'].iloc[0])) / 1e9
    duration = float(t_raw[-1])
    max_lookahead = max(LOOKAHEAD_SECONDS)
    t = np.arange(0.0, np.floor((duration - max_lookahead - DT) / DT) * DT + 1e-9, DT)
    if len(t) < 100:
        raise ValueError('Not enough data after resampling and lookahead trimming.')

    lat0 = float(data['lat [deg]'].iloc[0])
    lon0 = float(data['lon [deg]'].iloc[0])
    # Use GPS as the source of truth for path coordinates; do not mix in x/y columns,
    # which do not close at the same endpoint as the GPS path in the supplied CSV.
    east_raw = EARTH_RADIUS_M * np.cos(np.radians(lat0)) * np.radians(data['lon [deg]'].to_numpy() - lon0)
    north_raw = EARTH_RADIUS_M * np.radians(data['lat [deg]'].to_numpy() - lat0)
    x = interp_numeric(t, t_raw, east_raw)
    y = interp_numeric(t, t_raw, north_raw)
    speed = np.maximum(0.0, interp_numeric(t, t_raw, data['speed [mps]'].to_numpy()))
    steer = interp_numeric(t, t_raw, data['steer_angle [deg]'].to_numpy())

    # Estimate a smoothed mathematical heading from the GPS route tangent.
    # This is consistent with x=east, y=north and is independent of the CSV heading column.
    window = max(1, int(round(0.25 / DT)))
    theta = np.zeros(len(t), dtype=float)
    for i in range(len(t)):
        j0 = max(0, i - window)
        j1 = min(len(t) - 1, i + window)
        dx = x[j1] - x[j0]
        dy = y[j1] - y[j0]
        if np.hypot(dx, dy) < 1e-5:
            theta[i] = theta[i - 1] if i else 0.0
        else:
            theta[i] = np.arctan2(dy, dx)
    theta = np.unwrap(theta)
    return data, t_raw, t, x, y, speed, steer, theta, lat0, lon0


def predict(X, model=None):
    """Predict steering using fixed, hard-coded linear regression coefficients.

    `model` is accepted for compatibility with run_simulation(); it is ignored.
    X must use the same 18-feature ordering and units as make_features().
    """
    X = np.asarray(X, dtype=float)
    if X.shape[-1] != len(REGRESSION_COEFFICIENTS):
        raise ValueError(
            f"Expected {len(REGRESSION_COEFFICIENTS)} features, got {X.shape[-1]}"
        )
    return REGRESSION_INTERCEPT + X @ REGRESSION_COEFFICIENTS


def integrate_step(px, py, theta, speed, steering_wheel_deg, dt):
    road_rad = np.radians(steering_wheel_deg / STEERING_RATIO)
    yaw_rate = speed * np.tan(road_rad) / WHEELBASE_M
    theta_next = theta + yaw_rate * dt
    theta_mid = theta + 0.5 * yaw_rate * dt
    return (px + speed * np.cos(theta_mid) * dt,
            py + speed * np.sin(theta_mid) * dt,
            theta_next)


def run_simulation(t, rx, ry, theta_ref, speed, model, with_feedback):
    n = len(t)
    sx = np.zeros(n); sy = np.zeros(n); sth = np.zeros(n)
    raw_model = np.zeros(n); applied = np.zeros(n); route_cmd = np.zeros(n)
    sx[0], sy[0], sth[0] = rx[0], ry[0], theta_ref[0]
    previous = 0.0
    cumulative = np.r_[0.0, np.cumsum(np.hypot(np.diff(rx), np.diff(ry)))]

    for i in range(n - 1):
        feat = make_features(i, sx[i], sy[i], sth[i], rx, ry, theta_ref, DT)
        pred = float(predict(feat.reshape(1, -1), model)[0])
        raw_model[i] = pred
        model_cmd = float(np.clip(pred, -MAX_STEERING_WHEEL_DEG, MAX_STEERING_WHEEL_DEG))
        command = model_cmd

        if with_feedback:
            # Separate path-following baseline: pure pursuit aims at the recorded route.
            # This is NOT the learned model; it is included to distinguish a controller
            # that has route feedback from the model-only closed-loop result.
            j = min(i + int(round(PURE_PURSUIT_LOOKAHEAD_S / DT)), n - 1)
            p = np.array([rx[j] - sx[i], ry[j] - sy[i]])
            left = np.array([-np.sin(sth[i]), np.cos(sth[i])])
            lateral_left = float(np.dot(p, left))
            lookahead_distance = max(float(np.linalg.norm(p)), 1e-3)
            kappa_pp = 2.0 * lateral_left / (lookahead_distance ** 2)
            road_angle_pp = np.arctan(WHEELBASE_M * kappa_pp)
            route_cmd[i] = float(np.degrees(road_angle_pp) * STEERING_RATIO)
            command = route_cmd[i]

        max_change = MAX_STEERING_RATE_DEG_S * DT
        command = float(np.clip(command, previous - max_change, previous + max_change))
        command = float(np.clip(command, -MAX_STEERING_WHEEL_DEG, MAX_STEERING_WHEEL_DEG))
        applied[i] = command
        sx[i + 1], sy[i + 1], sth[i + 1] = integrate_step(
            sx[i], sy[i], sth[i], float(speed[i]), command, DT
        )
        previous = command

    raw_model[-1] = raw_model[-2]
    applied[-1] = applied[-2]
    route_cmd[-1] = route_cmd[-2]
    return sx, sy, sth, raw_model, applied, route_cmd


def main():
    _, t_raw, t, x, y, speed, steer, theta, lat0, lon0 = load_data()
    max_offset = int(round(max(LOOKAHEAD_SECONDS) / DT))
    rows = []
    for i in range(len(t) - 1):
        rows.append(make_features(i, x[i], y[i], theta[i], x, y, theta, DT))
    X = np.asarray(rows)
    target = steer[1:len(X)+1]
    n_train = int(len(X) * TRAIN_FRACTION)
    # No fitting here: use the fixed coefficients declared at the top of this file.
    model = None
    pred_all = predict(X)
    test_pred = pred_all[n_train:]
    test_y = target[n_train:]
    test_mae = float(np.mean(np.abs(test_pred - test_y)))
    test_rmse = float(np.sqrt(np.mean((test_pred - test_y)**2)))
    persistence = steer[:len(X)][n_train:]
    persistence_mae = float(np.mean(np.abs(persistence - test_y)))
    persistence_rmse = float(np.sqrt(np.mean((persistence - test_y)**2)))

    # Model-only simulation: this is the actual test of whether the predictor alone closes the loop.
    mx, my, mtheta, mraw, mapplied, _ = run_simulation(t, x, y, theta, speed, model, with_feedback=False)
    # Pure-pursuit is a separate route-following baseline; do not attribute its tracking to the learned model.
    hx, hy, htheta, hraw, happlied, route_cmd = run_simulation(t, x, y, theta, speed, model, with_feedback=True)

    model_err = np.hypot(mx - x, my - y)
    hybrid_err = np.hypot(hx - x, hy - y)
    out = pd.DataFrame({
        'time [s]': t,
        'reference_east [m]': x, 'reference_north [m]': y,
        'model_only_east [m]': mx, 'model_only_north [m]': my,
        'model_only_raw_steer [deg]': mraw, 'model_only_applied_steer [deg]': mapplied,
        'pure_pursuit_east [m]': hx, 'pure_pursuit_north [m]': hy,
        'model_prediction_in_pure_pursuit_run [deg]': hraw, 'pure_pursuit_steer [deg]': happlied,
        'pure_pursuit_raw_steer [deg]': route_cmd,
        'actual_steer [deg]': steer,
        'one_step_prediction [deg]': np.r_[pred_all, pred_all[-1]][:len(t)],
        'one_step_test_sample': np.arange(len(t)) >= n_train,
        'model_only_position_error [m]': model_err,
        'pure_pursuit_position_error [m]': hybrid_err,
    })
    out.to_csv(OUTPUT_CSV, index=False)

    fig, axes = plt.subplots(3, 1, figsize=(11, 14), constrained_layout=True)
    axes[0].plot(x, y, color='blue', linewidth=2, label='Actual GPS path')
    axes[0].plot(mx, my, color='red', linestyle='--', label='Learned model only (open loop)')
    axes[0].plot(hx, hy, color='green', linestyle='-.', label='Pure-pursuit route-following baseline')
    axes[0].set_title('Actual vs Simulated Path — Local GPS Coordinates')
    axes[0].set_xlabel('East [m]'); axes[0].set_ylabel('North [m]')
    axes[0].axis('equal'); axes[0].grid(True); axes[0].legend()

    axes[1].plot(t[1:len(pred_all)+1], target, color='blue', linewidth=1, label='Actual next-sample steering')
    axes[1].plot(t[1:len(pred_all)+1], pred_all, color='orange', alpha=0.85, label='Model one-step prediction')
    axes[1].plot(t[1:len(pred_all)+1], steer[:len(pred_all)], color='gray', linestyle=':', alpha=0.9, label='Persistence baseline (current steering)')
    axes[1].axvline(t[min(n_train, len(t)-1)], color='black', linestyle='--', label='Train/test split')
    axes[1].set_title(f'One-Step Steering Prediction (test MAE {test_mae:.1f}°; persistence {persistence_mae:.1f}°)')
    axes[1].set_xlabel('Time [s]'); axes[1].set_ylabel('Steering-wheel angle [deg]')
    axes[1].grid(True); axes[1].legend()

    axes[2].plot(t, steer, color='blue', alpha=0.8, label='Actual steering')
    axes[2].plot(t, mapplied, color='red', linestyle='--', label='Model-only applied steering')
    axes[2].plot(t, happlied, color='green', linestyle='-.', label='Pure-pursuit baseline steering')
    axes[2].set_title('Steering Commands Used in the Simulations')
    axes[2].set_xlabel('Time [s]'); axes[2].set_ylabel('Steering-wheel angle [deg]')
    axes[2].grid(True); axes[2].legend()
    fig.savefig(OUTPUT_PNG, dpi=160)
    plt.close(fig)

    print(f'Wrote {OUTPUT_CSV}')
    print(f'Wrote {OUTPUT_PNG}')
    print(f'Resampled samples: {len(t)} at 20 Hz; source duration {t_raw[-1]:.2f} s')
    print(f'Chronological evaluation split: {TRAIN_FRACTION:.0%} earlier samples / {1-TRAIN_FRACTION:.0%} later samples')
    print('Regression coefficients: hard-coded; no training/fitting performed at runtime.')
    print(f'One-step test MAE: {test_mae:.2f} deg; RMSE: {test_rmse:.2f} deg')
    print(f'Persistence baseline test MAE: {persistence_mae:.2f} deg; RMSE: {persistence_rmse:.2f} deg')
    print(f'Model-only path error: mean {model_err.mean():.2f} m, median {np.median(model_err):.2f} m, max {model_err.max():.2f} m')
    print(f'Pure-pursuit baseline path error: mean {hybrid_err.mean():.2f} m, median {np.median(hybrid_err):.2f} m, max {hybrid_err.max():.2f} m')
    print('NOTE: pure pursuit uses the recorded GPS route as a known reference. Its tracking is not proof that the learned model alone works.')

if __name__ == '__main__':
    main()
