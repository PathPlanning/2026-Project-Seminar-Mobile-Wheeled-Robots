import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point, Twist
from turtlesim.msg import Pose as TurtlePose


def wrap_to_pi(a: float) -> float:
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class GoalFollower(Node):
    def __init__(self):
        super().__init__("goal_follower")

        self.declare_parameter("turtle", "turtle2")
        self.declare_parameter("control_hz", 10.0)
        self.declare_parameter("goal_tolerance", 0.10)

        self.declare_parameter("k_lin", 1.5)
        self.declare_parameter("k_ang", 6.0)
        self.declare_parameter("max_lin", 1.0)
        self.declare_parameter("max_ang", 2.0)
        self.declare_parameter("slow_angle", 1.0)

        turtle = self.get_parameter("turtle").value
        self.pose_topic = f"/{turtle}/pose"
        self.cmd_topic = f"/{turtle}/cmd_vel"
        self.goal_topic = f"/{turtle}/goal"

        self.control_hz = float(self.get_parameter("control_hz").value)
        self.dt = 1.0 / self.control_hz
        self.tol = float(self.get_parameter("goal_tolerance").value)

        self.k_lin = float(self.get_parameter("k_lin").value)
        self.k_ang = float(self.get_parameter("k_ang").value)
        self.max_lin = float(self.get_parameter("max_lin").value)
        self.max_ang = float(self.get_parameter("max_ang").value)
        self.slow_angle = float(self.get_parameter("slow_angle").value)

        self.pose_ready = False
        self.pose = TurtlePose()
        self.has_goal = False
        self.goal_xy = (0.0, 0.0)

        self.pose_sub = self.create_subscription(TurtlePose, self.pose_topic, self.on_pose, 10)
        self.goal_sub = self.create_subscription(Point, self.goal_topic, self.on_goal, 10)
        self.cmd_pub = self.create_publisher(Twist, self.cmd_topic, 10)

        self.timer = self.create_timer(self.dt, self.on_timer)

        self.get_logger().info(
            f"GoalFollower started:\n"
            f"  pose: {self.pose_topic}\n"
            f"  goal: {self.goal_topic} (geometry_msgs/Point)\n"
            f"  cmd : {self.cmd_topic} (geometry_msgs/Twist)\n"
            f"  rate: {self.control_hz} Hz"
        )

    def on_pose(self, msg: TurtlePose):
        self.pose = msg
        self.pose_ready = True

    def on_goal(self, msg: Point):
        self.goal_xy = (float(msg.x), float(msg.y))
        self.has_goal = True
        self.get_logger().info(f"New goal: ({self.goal_xy[0]:.2f}, {self.goal_xy[1]:.2f})")

    def publish_stop(self):
        self.cmd_pub.publish(Twist())

    def on_timer(self):
        if not self.pose_ready or not self.has_goal:
            self.publish_stop()
            return

        x, y, theta = float(self.pose.x), float(self.pose.y), float(self.pose.theta)
        gx, gy = self.goal_xy

        dx, dy = gx - x, gy - y
        dist = math.hypot(dx, dy)

        if dist < self.tol:
            self.publish_stop()
            return

        angle_to_goal = math.atan2(dy, dx)
        ang_err = wrap_to_pi(angle_to_goal - theta)

        w = clamp(self.k_ang * ang_err, -self.max_ang, self.max_ang)
        v = min(self.k_lin * dist, self.max_lin)

        if abs(ang_err) > self.slow_angle:
            v *= 0.2

        cmd = Twist()
        cmd.linear.x = float(v)
        cmd.angular.z = float(w)
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = GoalFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()