#!/usr/bin/env python3

from src.utils.shared_state import get_for_ros
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import sys
import os

# Add parent directory to path để import được main modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class XiangqiRosService(Node):
    """ROS2 Service Node để đọc shared state từ main GUI"""

    def __init__(self):
        super().__init__('xiangqi_ros_service')

        # Tạo service servers
        self.fen_srv = self.create_service(
            Trigger,
            'get_xiangqi_fen',
            self.get_fen_callback
        )

        self.next_move_srv = self.create_service(
            Trigger,
            'get_next_move',
            self.get_next_move_callback
        )

        self.get_logger().info('🚀 Xiangqi ROS Service started!')
        self.get_logger().info('📡 Services available:')
        self.get_logger().info('  - /get_xiangqi_fen (get current FEN from shared state)')
        self.get_logger().info('  - /get_next_move (get best move from shared engine results)')
        self.get_logger().info('🔗 Reading data from shared state (main GUI)')

    def get_fen_callback(self, request, response):
        """
        Service callback để trả về FEN hiện tại từ shared state

        Args:
            request: Trigger request (empty)
            response: Trigger response

        Returns:
            response với success=True và message=FEN string
        """
        try:
            # Lấy data từ shared state
            game_info = get_for_ros()

            if game_info and 'fen' in game_info:
                current_fen = game_info['fen']

                response.success = True
                response.message = current_fen

                self.get_logger().info(f'📤 FEN requested: {current_fen}')

                # Log thêm thông tin về position
                current_player = game_info.get('current_player', 'unknown')
                move_count = game_info.get('move_count', 0)
                game_status = game_info.get('game_status', 'unknown')

                player_vn = 'Đỏ' if current_player == 'red' else 'Đen'
                self.get_logger().info(
                    f'🎯 Current player: {player_vn}, Moves: {move_count}, Status: {game_status}')

            else:
                response.success = False
                response.message = "ERROR: No game data available in shared state"
                self.get_logger().error('❌ No FEN data in shared state')

        except Exception as e:
            response.success = False
            response.message = f"ERROR: {str(e)}"
            self.get_logger().error(f'❌ Service error: {e}')

        return response

    def get_next_move_callback(self, request, response):
        """
        Service callback để trả về best move từ shared engine results

        Args:
            request: Trigger request (empty)
            response: Trigger response

        Returns:
            response với success=True và message=move notation (e.g., "e2e4")
        """
        try:
            # Lấy data từ shared state
            game_info = get_for_ros()

            if game_info:
                best_move = game_info.get('best_move')
                engine_results = game_info.get('engine_results', {})

                if best_move and best_move != 'None':
                    response.success = True
                    response.message = best_move

                    self.get_logger().info(
                        f'🤖 Best move from shared state: {best_move}')

                    # Log thêm thông tin engine analysis
                    current_player = game_info.get('current_player', 'unknown')
                    player_vn = 'Đỏ' if current_player == 'red' else 'Đen'

                    # Tìm engine info cho best move
                    engine_info = ""
                    for engine_name, result in engine_results.items():
                        if result.get('bestmove') == best_move:
                            evaluation = result.get('evaluation', 0)
                            depth = result.get('depth', 0)
                            nodes = result.get('nodes', 0)
                            engine_info = f"from {engine_name} (eval:{evaluation:.2f}, depth:{depth}, nodes:{nodes})"
                            break

                    self.get_logger().info(
                        f'🎯 Move for {player_vn} {engine_info}')

                else:
                    response.success = False
                    response.message = "ERROR: No best move available in shared state"
                    self.get_logger().error('❌ No best move in shared state')

            else:
                response.success = False
                response.message = "ERROR: No game data available in shared state"
                self.get_logger().error('❌ No game data in shared state')

        except Exception as e:
            response.success = False
            response.message = f"ERROR: {str(e)}"
            self.get_logger().error(f'❌ Next move service error: {e}')

        return response


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
