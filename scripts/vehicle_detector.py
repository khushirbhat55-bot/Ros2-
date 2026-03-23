import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int32
import cv2
import numpy as np

class VehicleDetector(Node):
    def __init__(self):
        super().__init__('vehicle_detector')

        # Subscribe to camera feed
        self.subscription = self.create_subscription(
            Image,
            '/world/indian_street/model/traffic_light_pole/link/link/sensor/traffic_camera/image',
            self.image_callback,
            10
        )

        # Publish vehicle count
        self.publisher = self.create_publisher(Int32, '/traffic/vehicle_count', 10)

        # Background subtractor for motion/vehicle detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )

        self.get_logger().info('Vehicle Detector started!')

    def image_callback(self, msg):
        # Convert ROS2 image to OpenCV
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame_bgr)

        # Remove shadows (shadows are gray=127, foreground is white=255)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Noise removal
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        # Find contours (each contour = potential vehicle)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        vehicle_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            # Filter small noise — only count objects above a minimum size
            if area > 500:
                vehicle_count += 1
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame_bgr, 'Vehicle', (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display count on frame
        cv2.putText(frame_bgr, f'Vehicle Count: {vehicle_count}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Publish count to ROS2 topic
        count_msg = Int32()
        count_msg.data = vehicle_count
        self.publisher.publish(count_msg)
        self.get_logger().info(f'Vehicles detected: {vehicle_count}')

        # Show the frame
        cv2.imshow('Vehicle Detection', frame_bgr)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = VehicleDetector()
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
