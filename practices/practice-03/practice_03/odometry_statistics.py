import rclpy
from rclpy.time import Time
from tf2_ros import TransformException
from geometry_msgs.msg import TwistStamped
from rosgraph_msgs.msg import Clock
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from tf2_ros import Buffer, TransformListener
import math
from matplotlib import pyplot
from pathlib import Path

class OdometryStatistics(Node):
    def __init__(self):
        super().__init__('odometry_statistics')
        self.declare_parameter('duration', 100.0)
        self.duration = self.get_parameter('duration').value
        self.declare_parameter('noise', '0.1')
        self.noise = self.get_parameter('noise').value

        self.clock_sub = self.create_subscription(Clock, '/clock', self.clock_callback, 10)
        self.cmd_sub = self.create_subscription(TwistStamped, '/cmd_vel', self.cmd_callback, 10)

        self.tf2_buffer = Buffer(node=self)
        self.tf2_listener = TransformListener(self.tf2_buffer, self)
        self.timer = self.create_timer(0.1, self.collect_data)

        self.start_time = None
        self.linear_x_cmd = None
        self.angular_z_cmd = None
        self.sim_time = None
        self.last_time = None

        self.cmd_x = None
        self.cmd_y = None
        self.cmd_yaw = None

        self.gt_data = []
        self.odom_data = []
        self.cmd_data = []

    def cmd_callback(self, msg):
        self.linear_x_cmd = msg.twist.linear.x 
        self.angular_z_cmd = msg.twist.angular.z

    def clock_callback(self, msg):
        self.sim_time = msg.clock.sec + msg.clock.nanosec / (10**9)

    def find_closest_point(self, data, target_time):
        if not data:
            return None

        closest = min(data, key=lambda point: abs(point['time'] - target_time))

        if abs(closest['time'] - target_time) > 0.05:
            return None

        return closest

    def calculate_errors(self):
        odom_errors = []
        cmd_errors = []

        for data, errors in ((self.odom_data, odom_errors), (self.cmd_data, cmd_errors)):
            for point in data:
                gt_point = self.find_closest_point(self.gt_data, point['time'])

                if gt_point is None:
                    continue

                dx = point['x'] - gt_point['x']
                dy = point['y'] - gt_point['y']

                pose_error = math.sqrt(dx**2 + dy**2)

                angle_diff = point['yaw'] - gt_point['yaw']

                yaw_error = abs(math.atan2(math.sin(angle_diff), math.cos(angle_diff)))

                errors.append({'time': (point['time'] - self.start_time), 'pose': pose_error, 'yaw': yaw_error})

        return odom_errors, cmd_errors

    def collect_data(self):
        if self.sim_time is None:
            return

        if self.linear_x_cmd is None or self.angular_z_cmd is None:
            return

        try:
            gt = self.tf2_buffer.lookup_transform('map', 'base_link_gt', Time())
            odom = self.tf2_buffer.lookup_transform('map', 'base_link', Time())
        except TransformException:
            return

        q = gt.transform.rotation
        gt_x = gt.transform.translation.x
        gt_y = gt.transform.translation.y
        gt_yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y**2 + q.z**2))

        o = odom.transform.rotation
        odom_x = odom.transform.translation.x
        odom_y = odom.transform.translation.y
        odom_yaw = math.atan2(2.0 * (o.w * o.z + o.x * o.y), 1.0 - 2.0 * (o.y**2 + o.z**2))

        if self.start_time is None:
            self.start_time = self.sim_time
            self.cmd_x = gt_x
            self.cmd_y = gt_y
            self.cmd_yaw = gt_yaw

        if self.last_time is None:
            self.last_time = self.sim_time

        gt_time = gt.header.stamp.sec + gt.header.stamp.nanosec / (10**9)
        odom_time = odom.header.stamp.sec + odom.header.stamp.nanosec / (10**9)

        diff = self.sim_time - self.start_time

        dt = self.sim_time - self.last_time

        if dt < 0:
            self.get_logger().warn('Время симуляции сброшено')
            self.timer.cancel()
            return

        self.last_time = self.sim_time

        self.cmd_x += self.linear_x_cmd * math.cos(self.cmd_yaw) * dt
        self.cmd_y += self.linear_x_cmd * math.sin(self.cmd_yaw) * dt
        self.cmd_yaw += self.angular_z_cmd * dt

        self.gt_data.append({'time': gt_time, 'x': gt_x, 'y': gt_y, 'yaw': gt_yaw})
        self.odom_data.append({'time': odom_time, 'x': odom_x, 'y': odom_y, 'yaw': odom_yaw})
        self.cmd_data.append({'time': self.sim_time, 'x': self.cmd_x, 'y': self.cmd_y, 'yaw': self.cmd_yaw})

        self.get_logger().info(f'GT: {len(self.gt_data)} ODOM: {len(self.odom_data)} CMD: {len(self.cmd_data)}')
        
        if diff >= self.duration:
            self.timer.cancel()
            self.save_results()
            return

    def save_results(self):
        if not self.gt_data or not self.odom_data or not self.cmd_data:
            self.get_logger().warn('Недостаточно данных для графиков')
            return

        odom_errors, cmd_errors = self.calculate_errors()

        fig, axes = pyplot.subplots(3, 1, figsize=(10, 12))

        for data, label in [(self.gt_data, 'Ground Truth'), (self.odom_data, 'Encoder Odometry'), (self.cmd_data, 'Command Odometry')]:
            x = [point['x'] for point in data]
            y = [point['y'] for point in data]

            axes[0].plot(x, y, label=label)

        axes[0].set_title('Robot trajectories')
        axes[0].set_xlabel('X (m)')
        axes[0].set_ylabel('Y (m)')
        axes[0].set_aspect('equal', adjustable='box')
        axes[0].legend()
        axes[0].grid(True)

        for errors, label in [(odom_errors, 'Encoder Odometry'), (cmd_errors, 'Command Odometry')]:
            time = [point['time'] for point in errors]
            err = [point['pose'] for point in errors]

            axes[1].plot(time, err, label=label)

        axes[1].set_title('Position error')
        axes[1].set_xlabel('Time (s)')
        axes[1].set_ylabel('Position error (m)')
        axes[1].legend()
        axes[1].grid(True)

        for errors, label in [(odom_errors, 'Encoder Odometry'), (cmd_errors, 'Command Odometry')]:
            time = [point['time'] for point in errors]
            err = [point['yaw'] for point in errors]

            axes[2].plot(time, err, label=label)

        axes[2].set_title('Yaw error')
        axes[2].set_xlabel('Time (s)')
        axes[2].set_ylabel('Yaw error (rad)')
        axes[2].legend()
        axes[2].grid(True)

        results_dir = Path('practices/practice-03/results')
        results_dir.mkdir(parents=True, exist_ok=True)

        fig.tight_layout()
        fig.savefig(results_dir / f'noise_{self.noise}.png', dpi=150)
        pyplot.close(fig)

        self.get_logger().info('Графики сохранены')

def main(args=None):
    rclpy.init(args=args)
    node = OdometryStatistics()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
