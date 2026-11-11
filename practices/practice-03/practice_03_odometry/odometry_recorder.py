import os
import re

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from rclpy.time import Time
from rosgraph_msgs.msg import Clock
from tf2_ros import Buffer, TransformException, TransformListener

from practice_03_odometry import trajectory as traj


def stamp_to_sec(stamp):
    return stamp.sec + stamp.nanosec * 1e-9


class OdometryRecorder(Node):
    def __init__(self):
        super().__init__('odometry_recorder')
        self.declare_parameter('duration', 100.0)
        self.declare_parameter('sample_period', 0.1)
        self.declare_parameter('results_dir', 'results')
        self.declare_parameter('world_file', '')
        self.declare_parameter('encoder_noise', -1.0)
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('gt_frame', 'base_link_gt')
        self.declare_parameter('base_frame', 'base_link')

        self.duration = float(self.get_parameter('duration').value)
        self.sample_period = float(self.get_parameter('sample_period').value)
        self.results_dir = os.path.expanduser(str(self.get_parameter('results_dir').value))
        self.map_frame = str(self.get_parameter('map_frame').value)
        self.gt_frame = str(self.get_parameter('gt_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        self.noise = self._read_noise()
        self.noise_label = f'{self.noise:g}' if self.noise >= 0.0 else 'unknown'

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.create_subscription(Clock, '/clock', self.on_clock, 10)
        self.create_subscription(TwistStamped, '/cmd_vel', self.on_cmd, 100)

        self.sim_time = None
        self.commands = []
        self.cmd_applied = 0
        self.integrator = None
        self.t0 = None
        self.last_sample_t = None
        self.rows = []
        self.finished = False

        self.get_logger().info(
            f'Ожидание преобразований и команд. duration={self.duration} s (sim), '
            f'encoderNoise={self.noise_label}, results_dir={self.results_dir}'
        )

    def _read_noise(self):
        world = str(self.get_parameter('world_file').value)
        try:
            with open(world, encoding='utf-8') as f:
                match = re.search(r'^\s*encoderNoise\s+([-+0-9.eE]+)', f.read(), re.MULTILINE)
            if match:
                return float(match.group(1))
        except OSError:
            pass
        return float(self.get_parameter('encoder_noise').value)

    def on_cmd(self, msg):
        stamp = stamp_to_sec(msg.header.stamp)
        if stamp <= 0.0 and self.sim_time is not None:
            stamp = self.sim_time
        self.commands.append((stamp, msg.twist.linear.x, msg.twist.angular.z))

    def on_clock(self, msg):
        self.sim_time = stamp_to_sec(msg.clock)
        if not self.finished:
            self.process()


    def latest(self, frame, time=None):
        try:
            return self.tf_buffer.lookup_transform(
                self.map_frame, frame, Time() if time is None else time)
        except TransformException:
            return None

    @staticmethod
    def to_pose(transform):
        t = transform.transform.translation
        q = transform.transform.rotation
        return (t.x, t.y, traj.yaw_from_quaternion(q.x, q.y, q.z, q.w))


    def process(self):
        gt_latest = self.latest(self.gt_frame)
        odom_latest = self.latest(self.base_frame)
        if gt_latest is None or odom_latest is None:
            return


        t_q = min(stamp_to_sec(gt_latest.header.stamp), stamp_to_sec(odom_latest.header.stamp))
        if t_q <= 0.0:
            return

        if self.t0 is None:
            if not self.commands:
                return
            self.start(t_q)
            return

        if t_q < self.last_sample_t + self.sample_period:
            return
        self.sample(t_q)
        if t_q - self.t0 >= self.duration:
            self.finished = True

    def start(self, t_q):
        gt = self.latest(self.gt_frame, Time(seconds=t_q))
        odom = self.latest(self.base_frame, Time(seconds=t_q))
        if gt is None or odom is None:
            return
        self.t0 = t_q
        gt_pose = self.to_pose(gt)
        past = [c for c in self.commands if c[0] <= t_q]
        _, v0, w0 = past[-1] if past else self.commands[0]
        self.cmd_applied = len(past)
        self.integrator = traj.CommandIntegrator(gt_pose, t_q, v0, w0)
        self.last_sample_t = t_q - self.sample_period
        self.get_logger().info(
            f'Эксперимент начался с t0={t_q:.3f} s (sim). Начальная поза GT: '
            f'x={gt_pose[0]:.3f}, y={gt_pose[1]:.3f}, yaw={gt_pose[2]:.3f}'
        )
        self.sample(t_q)

    def sample(self, t_q):
        when = Time(seconds=t_q)
        gt = self.latest(self.gt_frame, when)
        odom = self.latest(self.base_frame, when)
        if gt is None or odom is None:
            return
        pending = [c for c in self.commands[self.cmd_applied:] if c[0] <= t_q]
        self.cmd_applied += len(pending)
        cmd_pose = self.integrator.advance(t_q, pending)

        g = self.to_pose(gt)
        e = self.to_pose(odom)
        self.rows.append([t_q, *g, *e, *cmd_pose])
        self.last_sample_t = t_q

    def save(self):
        if len(self.rows) < 2:
            self.get_logger().error('Собрано недостаточно данных, ничего не сохранено.')
            return
        os.makedirs(self.results_dir, exist_ok=True)
        base = f'noise_{self.noise_label}'.replace('.', '_')
        png = os.path.join(self.results_dir, base + '.png')
        csv_path = os.path.join(self.results_dir, base + '.csv')
        traj.save_csv(csv_path, self.rows)
        traj.save_plot(png, self.rows, self.noise_label)
        self.get_logger().info(f'Сохраненны {len(self.rows)} образцы в {csv_path}')
        self.get_logger().info(f'Сохранен сюжет в {png}')
        for line in traj.summary(self.rows):
            self.get_logger().info(line)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryRecorder()
    try:
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.1)
        if node.finished:
            node.save()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
