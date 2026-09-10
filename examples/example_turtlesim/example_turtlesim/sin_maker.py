import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TurtleSin(Node):
    def __init__(self):
        super().__init__('sin_maker')

        self.declare_parameter('topic', '/turtle1/cmd_vel')
        self.declare_parameter('rate_hz', 30.0)
        self.declare_parameter('linear_v', 1.5)
        self.declare_parameter('ang_amp', 2.0)
        self.declare_parameter('ang_freq', 0.3)

        topic = self.get_parameter('topic').value
        rate_hz = float(self.get_parameter('rate_hz').value)

        self.v = float(self.get_parameter('linear_v').value)
        self.amp = float(self.get_parameter('ang_amp').value)
        self.freq = float(self.get_parameter('ang_freq').value)

        self.publisher = self.create_publisher(Twist, topic, 10)
        self.t0 = self.get_clock().now()

        self.timer = self.create_timer(1.0 / rate_hz, self.on_timer)
        self.get_logger().info(
            f'Publishing to {topic}: v = {self.v}, w(t) = {self.amp} * sin(2 * pi * {self.freq} * t)'
        )

    def on_timer(self):
        now = self.get_clock().now()
        t = (now - self.t0).nanoseconds * 1e-9

        w = self.amp * math.sin(2.0 * math.pi * self.freq * t)

        msg = Twist()
        msg.linear.x = self.v
        msg.angular.z = w
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleSin()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()