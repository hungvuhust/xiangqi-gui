#!/usr/bin/env python3

"""
Test script để gọi Xiangqi ROS service
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import sys


class XiangqiServiceClient(Node):
    """Client để test Xiangqi ROS service"""

    def __init__(self):
        super().__init__('xiangqi_service_client')

        # Tạo service client
        self.cli = self.create_client(Trigger, 'get_xiangqi_fen')

        # Đợi service available
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('⏳ Waiting for /get_xiangqi_fen service...')

        self.get_logger().info('✅ Service available!')

    def call_service(self):
        """Gọi service để lấy FEN"""
        req = Trigger.Request()

        try:
            # Gọi service
            future = self.cli.call_async(req)
            rclpy.spin_until_future_complete(self, future)

            response = future.result()

            if response.success:
                print(f"✅ Success!")
                print(f"📋 FEN: {response.message}")

                # Parse FEN để hiển thị thông tin
                fen_parts = response.message.split()
                if len(fen_parts) >= 2:
                    current_player = "Đỏ" if fen_parts[1] == 'w' else "Đen"
                    print(f"🎯 Current player: {current_player}")

            else:
                print(f"❌ Service call failed!")
                print(f"📋 Error: {response.message}")

        except Exception as e:
            print(f"❌ Service call error: {e}")


def main(args=None):
    """Main entry point"""
    print("🚀 Xiangqi ROS Service Client")
    print("=" * 40)

    rclpy.init(args=args)

    try:
        client = XiangqiServiceClient()
        client.call_service()

    except KeyboardInterrupt:
        print('\n🛑 Client interrupted by user')
    except Exception as e:
        print(f'❌ Client error: {e}')
    finally:
        # Cleanup
        if 'client' in locals():
            client.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
