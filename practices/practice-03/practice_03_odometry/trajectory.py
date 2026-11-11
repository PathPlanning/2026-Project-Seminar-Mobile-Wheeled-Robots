import csv
import math

import numpy as np


def wrap_angle(angle):
    return (np.asarray(angle) + math.pi) % (2.0 * math.pi) - math.pi


def yaw_from_quaternion(x, y, z, w):
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def integrate_unicycle(pose, v, w, dt):
    x, y, yaw = pose
    if dt <= 0.0:
        return (x, y, yaw)
    if abs(w) < 1e-9:
        return (x + v * math.cos(yaw) * dt, y + v * math.sin(yaw) * dt, yaw)
    yaw_new = yaw + w * dt
    x_new = x + v / w * (math.sin(yaw_new) - math.sin(yaw))
    y_new = y - v / w * (math.cos(yaw_new) - math.cos(yaw))
    return (x_new, y_new, yaw_new)


class CommandIntegrator:
    def __init__(self, pose0, t0, v0, w0):
        self.pose = tuple(pose0)
        self.t = t0
        self.v = v0
        self.w = w0

    def advance(self, t_end, commands):
        for stamp, v, w in commands:
            if stamp > self.t:
                self.pose = integrate_unicycle(self.pose, self.v, self.w, stamp - self.t)
                self.t = stamp
            self.v, self.w = v, w
        if t_end > self.t:
            self.pose = integrate_unicycle(self.pose, self.v, self.w, t_end - self.t)
            self.t = t_end
        return self.pose


COLUMNS = [
    't',
    'gt_x', 'gt_y', 'gt_yaw',
    'enc_x', 'enc_y', 'enc_yaw',
    'cmd_x', 'cmd_y', 'cmd_yaw',
]


def compute_errors(data):
    d = np.asarray(data)
    return {
        'enc_pos': np.hypot(d[:, 4] - d[:, 1], d[:, 5] - d[:, 2]),
        'cmd_pos': np.hypot(d[:, 7] - d[:, 1], d[:, 8] - d[:, 2]),
        'enc_yaw': np.abs(wrap_angle(d[:, 6] - d[:, 3])),
        'cmd_yaw': np.abs(wrap_angle(d[:, 9] - d[:, 3])),
    }


def save_csv(path, data):
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(data)


def save_plot(path, data, noise_label):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    d = np.asarray(data)
    err = compute_errors(d)
    t = d[:, 0] - d[0, 0]

    fig = plt.figure(figsize=(15, 7))
    grid = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.1])
    ax_xy = fig.add_subplot(grid[:, 0])
    ax_pos = fig.add_subplot(grid[0, 1])
    ax_yaw = fig.add_subplot(grid[1, 1], sharex=ax_pos)

    ax_xy.plot(d[:, 1], d[:, 2], color='black', lw=2.0, label='Ground truth')
    ax_xy.plot(d[:, 4], d[:, 5], color='tab:blue', lw=1.5, label='Odometry (encoders)')
    ax_xy.plot(d[:, 7], d[:, 8], color='tab:orange', lw=1.5, ls='--', label='Odometry (commands)')
    ax_xy.plot(d[0, 1], d[0, 2], 'go', label='Start')
    ax_xy.set_aspect('equal', adjustable='datalim')
    ax_xy.set_xlabel('x, m')
    ax_xy.set_ylabel('y, m')
    ax_xy.set_title('Trajectories in the map frame')
    ax_xy.grid(True)
    ax_xy.legend(loc='best')

    ax_pos.plot(t, err['enc_pos'], color='tab:blue', label='Odometry (encoders)')
    ax_pos.plot(t, err['cmd_pos'], color='tab:orange', label='Odometry (commands)')
    ax_pos.set_ylabel('Position error, m')
    ax_pos.set_title('Position error relative to GT')
    ax_pos.grid(True)
    ax_pos.legend(loc='best')

    ax_yaw.plot(t, err['enc_yaw'], color='tab:blue', label='Odometry (encoders)')
    ax_yaw.plot(t, err['cmd_yaw'], color='tab:orange', label='Odometry (commands)')
    ax_yaw.set_xlabel('Time since experiment start, s')
    ax_yaw.set_ylabel('Yaw error, rad')
    ax_yaw.set_title('Yaw error relative to GT')
    ax_yaw.grid(True)
    ax_yaw.legend(loc='best')

    fig.suptitle(f'encoderNoise = {noise_label} rad', fontsize=14)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def summary(data):
    err = compute_errors(data)
    lines = []
    for key, name in (('enc', 'encoders'), ('cmd', 'commands')):
        pos, yaw = err[f'{key}_pos'], err[f'{key}_yaw']
        lines.append(
            f'{name:9s}: position error mean {pos.mean():.3f} m, max {pos.max():.3f} m, '
            f'final {pos[-1]:.3f} m | yaw error mean {yaw.mean():.3f} rad, '
            f'max {yaw.max():.3f} rad, final {yaw[-1]:.3f} rad'
        )
    return lines
