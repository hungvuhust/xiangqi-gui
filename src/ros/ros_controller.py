#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal


class RosController(QObject):
    """
    Controller để tích hợp ROS2 với Xiangqi GUI
    Chạy trong thread riêng để không block GUI
    """

    # Signals để communication với GUI
    position_updated = pyqtSignal(str)  # Emit khi position được update từ ROS

    def __init__(self, parent=None):
        super().__init__(parent)
        self.node = None
        self.ros_thread = None
        self.is_running = False

    def start_service(self):
        """Khởi động ROS service trong thread riêng"""
        if self.is_running:
            print("⚠️  ROS service is already running")
            return

        self.ros_thread = threading.Thread(
            target=self._run_ros_service, daemon=True)
        self.ros_thread.start()
        print("🚀 Starting ROS service in background thread...")

    def stop_service(self):
        """Dừng ROS service"""
        self.is_running = False
        if self.node:
            self.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        print("🛑 ROS service stopped")

    def show_info(self):
        """Hiển thị thông tin ROS service"""
        if self.is_running:
            print("📡 ROS Service Status: RUNNING")
            print("🎯 Service Name: /get_xiangqi_fen")
            print("📋 Service Type: std_srvs/srv/Trigger")
            print("💡 Usage: ros2 service call /get_xiangqi_fen std_srvs/srv/Trigger")
        else:
            print("📡 ROS Service Status: STOPPED")
            print("💡 Use ROS > Start ROS Service to begin")

    def _run_ros_service(self):
        """Chạy ROS service trong thread riêng"""
        try:
            # Import trong thread để tránh conflict
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))

            from xiangqi_gui.ros_service_node import XiangqiRosService

            rclpy.init()
            self.node = XiangqiRosService()
            self.is_running = True

            print("✅ ROS service node created successfully")
            print("📡 Service available at: /get_xiangqi_fen")

            # Spin trong loop
            rclpy.spin(self.node)

        except Exception as e:
            print(f"❌ ROS service error: {e}")
        finally:
            self.is_running = False

    def update_position_in_ros(self, fen_string):
        """
        Cập nhật position trong ROS service khi GUI thay đổi

        Args:
            fen_string: FEN string từ GUI
        """
        if self.node and self.is_running:
            try:
                success = self.node.update_position(fen_string)
                if success:
                    print(f"📡 ROS position updated: {fen_string}")
                return success
            except Exception as e:
                print(f"❌ Error updating ROS position: {e}")
                return False
        return False

    def is_ros_available(self):
        """Kiểm tra ROS có available không"""
        try:
            import rclpy
            return True
        except ImportError:
            return False
