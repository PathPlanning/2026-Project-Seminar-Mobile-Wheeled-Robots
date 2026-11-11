import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node


class CmdVelPublisher(Node):
    def __init__(self):
        super().__init__('cmd_vel_publisher')
        self.declare_parameter('linear_x', 0.2)
        self.declare_parameter('angular_z', 0.2)
        self.declare_parameter('rate', 10.0)
        self.declare_parameter('frame_id', 'base_link')

        self.linear_x = float(self.get_parameter('linear_x').value)
        self.angular_z = float(self.get_parameter('angular_z').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        rate = float(self.get_parameter('rate').value)

        self.publisher = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.timer = self.create_timer(1.0 / rate, self.publish)
        self.get_logger().info(
            f'Публикуем cmd_vel: linear.x={self.linear_x} m/s, '
            f'angular.z={self.angular_z} rad/s at {rate} Hz'
        )

    def publish(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.twist.linear.x = self.linear_x
        msg.twist.angular.z = self.angular_z
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
