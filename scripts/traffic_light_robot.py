import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import cv2
import numpy as np

class TrafficLightRobot(Node):
    def __init__(self):
        super().__init__('traffic_light_robot')

        # Subscribe to robot camera
        self.subscription = self.create_subscription(
            Image,
            '/robot_camera/image',
            self.image_callback,
            10
        )

        # Publisher to move robot
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Traffic light timer
        self.light_state = 'RED'
        self.timer_count = 0

        # Timer — runs every 1 second
        self.timer = self.create_timer(1.0, self.traffic_light_timer)

        self.get_logger().info('Traffic Light Robot started!')

    def traffic_light_timer(self):
        self.timer_count += 1

        # RED for 5 seconds, GREEN for 5 seconds, YELLOW for 2 seconds
        if self.light_state == 'RED' and self.timer_count >= 5:
            self.light_state = 'GREEN'
            self.timer_count = 0
            self.get_logger().info('🟢 Light changed to GREEN!')

        elif self.light_state == 'GREEN' and self.timer_count >= 5:
            self.light_state = 'YELLOW'
            self.timer_count = 0
            self.get_logger().info('🟡 Light changed to YELLOW!')

        elif self.light_state == 'YELLOW' and self.timer_count >= 2:
            self.light_state = 'RED'
            self.timer_count = 0
            self.get_logger().info('🔴 Light changed to RED!')

        # Control robot based on light state
        twist = Twist()
        if self.light_state == 'RED':
            twist.linear.x = 0.0
            twist.angular.z = 0.0
        elif self.light_state == 'YELLOW':
            twist.linear.x = 0.3
            twist.angular.z = 0.0
        elif self.light_state == 'GREEN':
            twist.linear.x = 1.0
            twist.angular.z = 0.0

        self.cmd_pub.publish(twist)

    def image_callback(self, msg):
        # Convert ROS image to OpenCV
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Show light state on camera feed
        if self.light_state == 'RED':
            label = 'RED - STOP'
            color = (0, 0, 255)
        elif self.light_state == 'YELLOW':
            label = 'YELLOW - SLOW'
            color = (0, 255, 255)
        else:
            label = 'GREEN - GO'
            color = (0, 255, 0)

        cv2.putText(frame_bgr, label, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        cv2.imshow('Robot Camera - Traffic Light Detection', frame_bgr)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = TrafficLightRobot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
