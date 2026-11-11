import math

import numpy as np

from practice_03_odometry import trajectory as traj


def test_circle_returns_to_start():
    v, w = 0.2, 0.2
    period = 2 * math.pi / w
    integ = traj.CommandIntegrator((1.0, 0.0, math.pi / 2), 0.0, v, w)
    cmds = [(0.1 * k, v, w) for k in range(1, int(period / 0.1))]
    pose = integ.advance(period, cmds)
    assert abs(pose[0] - 1.0) < 1e-6 and abs(pose[1]) < 1e-6


def test_circle_center_and_radius():
    integ = traj.CommandIntegrator((1.0, 0.0, math.pi / 2), 0.0, 0.2, 0.2)
    x, y, _ = integ.advance(5.0, [])
    assert abs(math.hypot(x, y) - 1.0) < 1e-9


def test_yaw_and_wrap():
    q = (0.0, 0.0, math.sin(0.4), math.cos(0.4))
    assert abs(traj.yaw_from_quaternion(*q) - 0.8) < 1e-9
    assert abs(traj.wrap_angle(3 * math.pi / 2) + math.pi / 2) < 1e-9
