#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point cho Xiangqi GUI
Game cờ tướng sử dụng PyQt5 với engine bên ngoài
"""

from src.gui.main_window import MainWindow
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Thêm thư mục src vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def main():
    """Hàm main khởi chạy ứng dụng"""
    # Thiết lập high DPI support trước khi tạo QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Xiangqi GUI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Xiangqi Dev")

    # Tạo và hiển thị cửa sổ chính
    window = MainWindow()
    window.show()

    # Chạy event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
