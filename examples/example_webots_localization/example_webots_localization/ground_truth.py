import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.time import Time
from rosgraph_msgs.msg import Clock
from tf2_ros import TransformBroadcaster
from tf_transformations import quaternion_from_matrix


class GroundTruth:
    def init(self, webots_node, properties):
        self.supervisor = webots_node.robot
        self.robot = self.supervisor.getFromDef('TURTLEBOT')
        if self.robot is None:
            raise RuntimeError('The scene must contain DEF TURTLEBOT')

        if not rclpy.ok():
            rclpy.init(args=None)
        self.node = rclpy.create_node('ground_truth')
        self.clock_publisher = self.node.create_publisher(Clock, '/clock', 10)
        self.broadcaster = TransformBroadcaster(self.node)

    def step(self):
        rclpy.spin_once(self.node, timeout_sec=0.0)
        stamp = Time(seconds=self.supervisor.getTime()).to_msg()
        self.clock_publisher.publish(Clock(clock=stamp))

        # Webots exports the root Robot frame as base_link in its URDF.
        pose = np.array(self.robot.getPose()).reshape(4, 4)
        quaternion = quaternion_from_matrix(pose)

        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = 'map'
        transform.child_frame_id = 'base_link_gt'
        translation = transform.transform.translation
        translation.x = float(pose[0, 3])
        translation.y = float(pose[1, 3])
        translation.z = float(pose[2, 3])
        rotation = transform.transform.rotation
        rotation.x = float(quaternion[0])
        rotation.y = float(quaternion[1])
        rotation.z = float(quaternion[2])
        rotation.w = float(quaternion[3])
        self.broadcaster.sendTransform(transform)
