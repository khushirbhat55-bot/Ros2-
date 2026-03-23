import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class CarMover(Node):
    def __init__(self):
        super().__init__('car_mover')
        self.publisher = self.create_publisher(
            Twist,
            '/model/moving_car/cmd_vel',
            10
        )
        self.direction = 1
        self.speed = 3.0
        self.timer = self.create_timer(4.0, self.switch_direction)
        self.move_timer = self.create_timer(0.1, self.publish_velocity)
        self.get_logger().info('Car mover started! Car will loop in camera view.')

    def publish_velocity(self):
        msg = Twist()
        msg.linear.x = self.speed * self.direction
        self.publisher.publish(msg)

    def switch_direction(self):
        self.direction *= -1
        self.get_logger().info(f'Car direction: {"forward →" if self.direction == 1 else "← backward"}')

def main(args=None):
    rclpy.init(args=args)
    node = CarMover()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
