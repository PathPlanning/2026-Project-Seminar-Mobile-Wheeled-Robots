import math

import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist


class DigitDrawer(Node):
    def __init__(self):
        super().__init__('digit_drawer')

        self.declare_parameter('turtle_name', 'turtle1')
        self.declare_parameter('digit', 0)

        self.turtle_name = self.get_parameter('turtle_name').value
        self.digit = self.get_parameter('digit').value

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.pose_subscriber = self.create_subscription(
            Pose,
            f'/{self.turtle_name}/pose',
            self.pose_callback,
            10
        )

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            f'/{self.turtle_name}/cmd_vel',
            10
        )

        self.segments = self.create_segments()
        self.segment_index = 0

        self.state = 'TURN'

        self.start_x = None
        self.start_y = None
        self.segment_distance = 0.0
        self.target_theta = 0.0

        self.angle_tolerance = 0.03
        self.distance_tolerance = 0.05

        self.timer = self.create_timer(
            0.05,
            self.control
        )

        self.get_logger().info(
            f'черепаха: {self.turtle_name}, цифра: {self.digit}'
        )

    def pose_callback(self, msg):
        self.x = msg.x
        self.y = msg.y
        self.theta = msg.theta

    def create_segments(self):
        if self.digit == 0:
            return [
                (2.0, 0.0),
                (0.0, 4.0),
                (-2.0, 0.0),
                (0.0, -4.0)
            ]

        if self.digit == 7:
            return [
                (2.0, 0.0),
                (-1.5, -4.0)
            ]

        self.get_logger().error(
            f'неизвестная цифра: {self.digit}'
        )

        return []

    def normalize_angle(self, angle):
        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )

    def stop(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.cmd_vel_publisher.publish(msg)

    def control(self):
        if not self.segments:
            self.state = 'DONE'

        if self.state == 'DONE':
            self.stop()
            return

        if self.segment_index >= len(self.segments):
            self.state = 'DONE'
            self.stop()
            self.get_logger().info(
                f'цифра {self.digit} готова'
            )
            return

        dx, dy = self.segments[self.segment_index]

        if self.state == 'TURN':
            self.target_theta = math.atan2(dy, dx)

            angle_error = self.normalize_angle(
                self.target_theta - self.theta
            )

            msg = Twist()

            if abs(angle_error) > self.angle_tolerance:
                msg.angular.z = (
                    1.0 if angle_error > 0 else -1.0
                )
                msg.linear.x = 0.0
                self.cmd_vel_publisher.publish(msg)

            else:
                self.stop()

                self.start_x = self.x
                self.start_y = self.y

                self.segment_distance = math.sqrt(
                    dx ** 2 + dy ** 2
                )

                self.state = 'MOVE'

        elif self.state == 'MOVE':
            distance = math.sqrt(
                (self.x - self.start_x) ** 2
                + (self.y - self.start_y) ** 2
            )

            msg = Twist()

            if distance < (
                self.segment_distance
                - self.distance_tolerance
            ):
                msg.linear.x = 1.0
                msg.angular.z = 0.0
                self.cmd_vel_publisher.publish(msg)

            else:
                self.stop()

                self.segment_index += 1

                if self.segment_index >= len(self.segments):
                    self.state = 'DONE'
                else:
                    self.state = 'TURN'


def main(args=None):
    rclpy.init(args=args)

    node = DigitDrawer()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()