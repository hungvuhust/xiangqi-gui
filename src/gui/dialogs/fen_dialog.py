# -*- coding: utf-8 -*-
"""
FEN Dialog cho Xiangqi GUI
Dialog để input/export FEN notation
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QGroupBox,
                             QMessageBox, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class FenDialog(QDialog):
    """Dialog để nhập và xuất FEN notation"""

    def __init__(self, parent=None, current_fen=""):
        super().__init__(parent)
        self.current_fen = current_fen
        self.result_fen = ""

        self.init_ui()

    def init_ui(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("FEN Position")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # Current position group
        current_group = QGroupBox("Position Hiện Tại")
        current_layout = QVBoxLayout(current_group)

        self.current_fen_display = QTextEdit()
        self.current_fen_display.setPlainText(self.current_fen)
        self.current_fen_display.setMaximumHeight(80)
        self.current_fen_display.setFont(QFont("Courier", 10))
        current_layout.addWidget(QLabel("FEN hiện tại:"))
        current_layout.addWidget(self.current_fen_display)

        # Copy button cho current FEN
        copy_btn = QPushButton("Copy FEN")
        copy_btn.clicked.connect(self.copy_current_fen)
        current_layout.addWidget(copy_btn)

        layout.addWidget(current_group)

        # Load new position group
        load_group = QGroupBox("Load Position Mới")
        load_layout = QVBoxLayout(load_group)

        load_layout.addWidget(QLabel("Nhập FEN notation:"))

        self.fen_input = QTextEdit()
        self.fen_input.setMaximumHeight(80)
        self.fen_input.setFont(QFont("Courier", 10))
        self.fen_input.setPlaceholderText(
            "Ví dụ: rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w")
        load_layout.addWidget(self.fen_input)

        # Load buttons
        load_buttons = QHBoxLayout()

        load_btn = QPushButton("Load Position")
        load_btn.clicked.connect(self.load_position)
        load_buttons.addWidget(load_btn)

        reset_btn = QPushButton("Reset về Position Ban Đầu")
        reset_btn.clicked.connect(self.reset_to_initial)
        load_buttons.addWidget(reset_btn)

        load_layout.addLayout(load_buttons)

        layout.addWidget(load_group)

        # Example positions
        examples_group = QGroupBox("Positions Mẫu")
        examples_layout = QVBoxLayout(examples_group)

        # Add some example positions
        examples = [
            ("Position Ban Đầu",
             "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w "),
            ("Middlegame", "r1bak1b1r/4a4/2n1c1n2/p1p1p1p1p/9/9/P1P1P1P1P/2N1C1N2/4A4/R1BAKAB1R w "),
            ("Endgame", "3ak4/4a4/9/9/9/9/9/9/4A4/3AK4 w ")
        ]

        for name, fen in examples:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, f=fen: self.load_example(f))
            examples_layout.addWidget(btn)

        layout.addWidget(examples_group)

        # Dialog buttons
        buttons_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def copy_current_fen(self):
        """Copy FEN hiện tại vào clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_fen)
        QMessageBox.information(
            self, "Thông báo", "Đã copy FEN vào clipboard!")

    def load_position(self):
        """Load position từ FEN input"""
        fen_text = self.fen_input.toPlainText().strip()
        if not fen_text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập FEN notation!")
            return

        self.result_fen = fen_text
        self.accept()

    def reset_to_initial(self):
        """Reset về position ban đầu"""
        initial_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        self.result_fen = initial_fen
        self.accept()

    def load_example(self, fen):
        """Load example position"""
        self.fen_input.setPlainText(fen)

    def get_result_fen(self):
        """Lấy FEN result"""
        return self.result_fen
