# -*- coding: utf-8 -*-
"""
Image Renderer cho Xiangqi GUI
Utilities để load và render file PNG/SVG
"""

import os
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QPen
from PyQt5.QtCore import QSize, QRectF, Qt
from .constants import get_piece_png_path, get_board_png_path


class ImageRenderer:
    """Class để render PNG/SVG files thành QPixmap"""

    def __init__(self):
        self.image_cache = {}  # Cache để tránh load lại file

    def load_png_pixmap(self, png_path):
        """
        Load PNG file và tạo QPixmap

        Args:
            png_path: Đường dẫn đến file PNG

        Returns:
            QPixmap hoặc None nếu lỗi
        """
        if not os.path.exists(png_path):
            print(f"Không tìm thấy file PNG: {png_path}")
            return None

        if png_path in self.image_cache:
            return self.image_cache[png_path]

        try:
            pixmap = QPixmap(png_path)
            if not pixmap.isNull():
                self.image_cache[png_path] = pixmap
                return pixmap
            else:
                print(f"File PNG không hợp lệ: {png_path}")
                return None
        except Exception as e:
            print(f"Lỗi load PNG {png_path}: {e}")
            return None

    def render_png_to_pixmap(self, png_path, size):
        """
        Load PNG và scale thành kích thước chỉ định

        Args:
            png_path: Đường dẫn đến file PNG
            size: QSize - kích thước mong muốn

        Returns:
            QPixmap hoặc None nếu lỗi
        """
        original_pixmap = self.load_png_pixmap(png_path)
        if not original_pixmap:
            return None

        # Scale PNG với smooth transformation
        scaled_pixmap = original_pixmap.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        return scaled_pixmap

    def render_piece_png(self, piece, size):
        """
        Render PNG quân cờ thành QPixmap

        Args:
            piece: Ký tự quân cờ (e.g., 'R', 'n')
            size: QSize - kích thước mong muốn

        Returns:
            QPixmap hoặc None nếu lỗi
        """
        png_path = get_piece_png_path(piece)
        if not png_path:
            print(f"Không tìm thấy PNG cho quân cờ: {piece}")
            return None

        return self.render_png_to_pixmap(png_path, size)

    def render_board_png(self, size):
        """
        Render PNG bàn cờ thành QPixmap

        Args:
            size: QSize - kích thước mong muốn

        Returns:
            QPixmap hoặc None nếu lỗi
        """
        png_path = get_board_png_path()
        return self.render_png_to_pixmap(png_path, size)

    def clear_cache(self):
        """Xóa cache images"""
        self.image_cache.clear()


# Global instance
image_renderer = ImageRenderer()
