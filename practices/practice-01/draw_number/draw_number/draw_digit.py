import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from turtlesim.msg import Pose

# Цифры заданы вершинами ломаной в единичном квадрате (u, v):
# u растёт вправо, v растёт вверх. Первая вершина - точка старта.
DIGITS = {
    1: [(0.2, 0.75), (0.7, 1.0), (0.7, 0.0)],
    5: [(1.0, 1.0), (0.0, 1.0), (0.0, 0.5), (1.0, 0.5), (1.0, 0.0), (0.0, 0.0)],
}

# Состояния автомата
WAIT_POSE, TURN, DRIVE, DONE = 'WAIT_POSE', 'TURN', 'DRIVE', 'DONE'


def wrap_to_pi(a: float) -> float:
    """Приводит угол к диапазону [-pi, pi]."""
    return math.atan2(math.sin(a), math.cos(a))


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class DigitDrawer(Node):
    def __init__(self):
        super().__init__('digit_drawer')

        self.declare_parameter('turtle', 'turtle1')
        self.declare_parameter('digit', 1)
        self.declare_parameter('width', 3.0)
        self.declare_parameter('height', 6.0)
        self.declare_parameter('linear_speed', 1.5)
        self.declare_parameter('angular_speed', 1.5)
        self.declare_parameter('angle_tolerance', 0.005)
        self.declare_parameter('k_ang', 4.0)
        self.declare_parameter('control_hz', 50.0)

        turtle = self.get_parameter('turtle').value
        digit = int(self.get_parameter('digit').value)
        self.width = float(self.get_parameter('width').value)
        self.height = float(self.get_parameter('height').value)
        self.lin_speed = float(self.get_parameter('linear_speed').value)
        self.ang_speed = float(self.get_parameter('angular_speed').value)
        self.angle_tol = float(self.get_parameter('angle_tolerance').value)
        self.k_ang = float(self.get_parameter('k_ang').value)
        hz = float(self.get_parameter('control_hz').value)

        if digit not in DIGITS:
            raise ValueError(f'Цифра {digit} не описана в DIGITS')
        self.shape = DIGITS[digit]

        # Замедление в конце отрезка для точной остановки
        self.slow_lin = 0.2 * self.lin_speed
        self.slow_zone_lin = 0.3      # ед.: последний участок едем медленно

        self.pose = None
        self.state = WAIT_POSE
        self.targets = []             # абсолютные координаты вершин (кроме старта)
        self.idx = 0                  # индекс текущей целевой вершины
        self.goal = (0.0, 0.0)        # вершина, к которой едем
        self.target_angle = 0.0
        self.seg_length = 0.0
        self.start_x = 0.0
        self.start_y = 0.0

        self.create_subscription(Pose, f'/{turtle}/pose', self.on_pose, 10)
        self.cmd_pub = self.create_publisher(Twist, f'/{turtle}/cmd_vel', 10)
        self.create_timer(1.0 / hz, self.on_timer)

        self.get_logger().info(
            f'Черепаха {turtle}, цифра {digit}, ждём первое сообщение pose...')

    # ---------- приём данных ----------
    def on_pose(self, msg: Pose):
        self.pose = msg

    def publish(self, v: float, w: float):
        cmd = Twist()
        cmd.linear.x = float(v)
        cmd.angular.z = float(w)
        self.cmd_pub.publish(cmd)

    # ---------- планирование ----------
    def build_targets(self):
        """Переводит вершины цифры в абсолютные координаты окна."""
        u0, v0 = self.shape[0]
        x0, y0 = self.pose.x, self.pose.y
        self.targets = [
            (x0 + (u - u0) * self.width, y0 + (v - v0) * self.height)
            for u, v in self.shape[1:]
        ]
        self.idx = 0

    def next_segment(self):
        """Готовит поворот и отрезок к очередной вершине."""
        if self.idx >= len(self.targets):
            self.state = DONE
            self.get_logger().info('Цифра нарисована, публикуем нулевую скорость')
            return
        tx, ty = self.targets[self.idx]
        self.goal = (tx, ty)
        dx, dy = tx - self.pose.x, ty - self.pose.y
        # Угол и длину считаем от фактического положения: ошибки не копятся
        self.target_angle = math.atan2(dy, dx)
        self.seg_length = math.hypot(dx, dy)
        self.state = TURN
        self.get_logger().info(
            f'Отрезок {self.idx + 1}/{len(self.targets)}: '
            f'угол {self.target_angle:.2f} рад, длина {self.seg_length:.2f}')

    # ---------- действия ----------
    def do_turn(self):
        err = wrap_to_pi(self.target_angle - self.pose.theta)
        if abs(err) < self.angle_tol:
            self.start_x, self.start_y = self.pose.x, self.pose.y
            self.state = DRIVE
            self.publish(0.0, 0.0)
            return
        # Пропорциональный поворот: чем ближе к цели, тем медленнее
        w = clamp(self.k_ang * err, -self.ang_speed, self.ang_speed)
        self.publish(0.0, w)

    def do_drive(self):
        # Сколько проехали вдоль направления отрезка
        along = ((self.pose.x - self.start_x) * math.cos(self.target_angle)
                 + (self.pose.y - self.start_y) * math.sin(self.target_angle))
        if along >= self.seg_length:
            self.idx += 1
            self.next_segment()
            self.publish(0.0, 0.0)
            return

        remaining = self.seg_length - along
        if remaining > self.slow_zone_lin:
            v = self.lin_speed
            # Подруливаем на вершину, чтобы линия получилась ровной
            gx, gy = self.goal
            err = wrap_to_pi(
                math.atan2(gy - self.pose.y, gx - self.pose.x) - self.pose.theta)
            w = clamp(self.k_ang * err, -self.ang_speed, self.ang_speed)
        else:
            v = self.slow_lin
            w = 0.0   # у самой цели направление шумит, не подруливаем
        self.publish(v, w)

    def on_timer(self):
        if self.pose is None:
            return
        if self.state == WAIT_POSE:
            self.build_targets()
            self.next_segment()

        if self.state == TURN:
            self.do_turn()
        elif self.state == DRIVE:
            self.do_drive()
        else:
            self.publish(0.0, 0.0)


def main(args=None):
    rclpy.init(args=args)
    node = DigitDrawer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()