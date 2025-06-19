#!/usr/bin/env python3
"""
Test script để kiểm tra signal system
"""
from src.gui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    print("🚀 Khởi tạo MainWindow...")
    window = MainWindow()

    print("🎯 Test emit signal...")
    window._emit_position_changed()

    print("✅ Test hoàn thành!")

    # Không show window, chỉ test signal
    app.quit()
