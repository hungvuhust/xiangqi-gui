#!/usr/bin/env python3

from src.core.game_state import GameState
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import sys
import os
import threading
import time

# Add parent directory to path để import được main modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class XiangqiRosService(Node):
    """ROS2 Service Node để expose FEN của bàn cờ Xiangqi"""

    def __init__(self):
        super().__init__('xiangqi_ros_service')

        # Tạo GameState instance
        self.game_state = GameState()

        # Tạo service server
        self.srv = self.create_service(
            Trigger,
            'get_xiangqi_fen',
            self.get_fen_callback
        )

        self.get_logger().info('🚀 Xiangqi ROS Service started!')
        self.get_logger().info('📡 Service: /get_xiangqi_fen (std_srvs/srv/Trigger)')
        self.get_logger().info('📋 Call service to get current FEN position')

        # Load FEN từ file hoặc sử dụng position mặc định
        self.load_initial_position()

    def load_initial_position(self):
        """Load position ban đầu hoặc từ file save"""
        try:
            # Có thể load từ file save state nếu có
            save_file = os.path.join(os.path.dirname(
                __file__), '..', 'saved_position.fen')
            if os.path.exists(save_file):
                with open(save_file, 'r') as f:
                    fen = f.read().strip()
                    if self.game_state.load_from_fen(fen):
                        self.get_logger().info(
                            f'✅ Loaded saved position: {fen}')
                        return

            # Nếu không có file save, sử dụng position mặc định
            self.game_state.reset()
            self.get_logger().info('🎯 Using default starting position')

        except Exception as e:
            self.get_logger().error(f'❌ Error loading position: {e}')
            self.game_state.reset()

    def get_fen_callback(self, request, response):
        """
        Service callback để trả về FEN hiện tại

        Args:
            request: Trigger request (empty)
            response: Trigger response

        Returns:
            response với success=True và message=FEN string
        """
        try:
            # Lấy FEN từ game state hiện tại
            current_fen = self.game_state.to_fen()

            if current_fen:
                response.success = True
                response.message = current_fen

                self.get_logger().info(f'📤 FEN requested: {current_fen}')

                # Log thêm thông tin về position
                player = 'Đỏ' if self.game_state.current_player == 'red' else 'Đen'
                move_count = len(self.game_state.move_history)
                self.get_logger().info(
                    f'🎯 Current player: {player}, Moves: {move_count}')

            else:
                response.success = False
                response.message = "ERROR: Could not generate FEN"
                self.get_logger().error('❌ Failed to generate FEN')

        except Exception as e:
            response.success = False
            response.message = f"ERROR: {str(e)}"
            self.get_logger().error(f'❌ Service error: {e}')

        return response

    def update_position(self, fen_string):
        """
        Cập nhật position từ external source (để tích hợp với GUI)

        Args:
            fen_string: FEN string mới
        """
        try:
            if self.game_state.load_from_fen(fen_string):
                self.get_logger().info(f'🔄 Position updated: {fen_string}')

                # Save position to file
                save_file = os.path.join(os.path.dirname(
                    __file__), '..', 'saved_position.fen')
                os.makedirs(os.path.dirname(save_file), exist_ok=True)
                with open(save_file, 'w') as f:
                    f.write(fen_string)

                return True
            else:
                self.get_logger().error(f'❌ Invalid FEN: {fen_string}')
                return False
        except Exception as e:
            self.get_logger().error(f'❌ Error updating position: {e}')
            return False


def main(args=None):
    """Main entry point"""
    rclpy.init(args=args)

    try:
        node = XiangqiRosService()

        # Spin để service chạy liên tục
        rclpy.spin(node)

    except KeyboardInterrupt:
        print('\n🛑 Service interrupted by user')
    except Exception as e:
        print(f'❌ Service error: {e}')
    finally:
        # Cleanup
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
