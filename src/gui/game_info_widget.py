# -*- coding: utf-8 -*-
"""
Game Info Widget cho Xiangqi GUI
Widget hiển thị thông tin về ván cờ (nước đi, thời gian, điểm số)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QGroupBox, QLCDNumber)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont


class GameInfoWidget(QWidget):
    """Widget hiển thị thông tin game"""

    def __init__(self):
        super().__init__()
        self.move_count = 0
        self.red_time = 0
        self.black_time = 0
        self.timer = QTimer()
        self.current_player_timer = True  # True = red, False = black

        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)

        # Thông tin thời gian
        time_group = QGroupBox("Thời Gian")
        time_layout = QVBoxLayout(time_group)

        # Thời gian quân đỏ
        red_time_layout = QHBoxLayout()
        red_time_layout.addWidget(QLabel("Đỏ:"))
        self.red_time_display = QLCDNumber(8)
        self.red_time_display.setStyleSheet("color: red")
        red_time_layout.addWidget(self.red_time_display)
        time_layout.addLayout(red_time_layout)

        # Thời gian quân đen
        black_time_layout = QHBoxLayout()
        black_time_layout.addWidget(QLabel("Đen:"))
        self.black_time_display = QLCDNumber(8)
        self.black_time_display.setStyleSheet("color: black")
        black_time_layout.addWidget(self.black_time_display)
        time_layout.addLayout(black_time_layout)

        layout.addWidget(time_group)

        # Thông tin ván cờ
        game_group = QGroupBox("Thông Tin Ván Cờ")
        game_layout = QVBoxLayout(game_group)

        # Số nước đi
        move_layout = QHBoxLayout()
        move_layout.addWidget(QLabel("Nước đi:"))
        self.move_count_label = QLabel("0")
        move_layout.addWidget(self.move_count_label)
        move_layout.addStretch()
        game_layout.addLayout(move_layout)

        # Lượt chơi hiện tại
        turn_layout = QHBoxLayout()
        turn_layout.addWidget(QLabel("Lượt:"))
        self.current_turn_label = QLabel("Đỏ")
        self.current_turn_label.setStyleSheet("font-weight: bold; color: red")
        turn_layout.addWidget(self.current_turn_label)
        turn_layout.addStretch()
        game_layout.addLayout(turn_layout)

        layout.addWidget(game_group)

        # Danh sách nước đi
        moves_group = QGroupBox("Nước Đi")
        moves_layout = QVBoxLayout(moves_group)

        self.moves_list = QListWidget()
        self.moves_list.setAlternatingRowColors(True)
        moves_layout.addWidget(self.moves_list)

        layout.addWidget(moves_group)

        # Engine analysis (nếu có)
        engine_group = QGroupBox("Phân Tích Engine")
        engine_layout = QVBoxLayout(engine_group)

        # Điểm đánh giá
        eval_layout = QHBoxLayout()
        eval_layout.addWidget(QLabel("Đánh giá:"))
        self.evaluation_label = QLabel("0.00")
        eval_layout.addWidget(self.evaluation_label)
        eval_layout.addStretch()
        engine_layout.addLayout(eval_layout)

        # Độ sâu tìm kiếm
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Độ sâu:"))
        self.depth_label = QLabel("0")
        depth_layout.addWidget(self.depth_label)
        depth_layout.addStretch()
        engine_layout.addLayout(depth_layout)

        # Nước đi tốt nhất
        best_move_layout = QHBoxLayout()
        best_move_layout.addWidget(QLabel("Nước đi tốt:"))
        self.best_move_label = QLabel("-")
        best_move_layout.addWidget(self.best_move_label)
        best_move_layout.addStretch()
        engine_layout.addLayout(best_move_layout)

        layout.addWidget(engine_group)

        layout.addStretch()

    def setup_timer(self):
        """Thiết lập timer cho đồng hồ"""
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Cập nhật mỗi giây

    def update_timer(self):
        """Cập nhật thời gian"""
        if self.current_player_timer:
            self.red_time += 1
        else:
            self.black_time += 1

        self.update_time_display()

    def update_time_display(self):
        """Cập nhật hiển thị thời gian"""
        red_minutes = self.red_time // 60
        red_seconds = self.red_time % 60
        red_time_str = f"{red_minutes:02d}:{red_seconds:02d}"

        black_minutes = self.black_time // 60
        black_seconds = self.black_time % 60
        black_time_str = f"{black_minutes:02d}:{black_seconds:02d}"

        self.red_time_display.display(red_time_str)
        self.black_time_display.display(black_time_str)

    def add_move(self, move):
        """Thêm nước đi vào danh sách"""
        self.move_count += 1

        # Format nước đi
        if self.move_count % 2 == 1:
            # Nước đi của quân đỏ
            move_text = f"{(self.move_count + 1) // 2}. {move}"
            self.current_turn_label.setText("Đen")
            self.current_turn_label.setStyleSheet(
                "font-weight: bold; color: black")
            self.current_player_timer = False
        else:
            # Nước đi của quân đen
            move_text = f"   {move}"
            self.current_turn_label.setText("Đỏ")
            self.current_turn_label.setStyleSheet(
                "font-weight: bold; color: red")
            self.current_player_timer = True

        self.moves_list.addItem(move_text)
        self.moves_list.scrollToBottom()

        self.move_count_label.setText(str(self.move_count))

    def remove_last_move(self):
        """Xóa nước đi cuối cùng"""
        if self.moves_list.count() > 0:
            self.moves_list.takeItem(self.moves_list.count() - 1)
            self.move_count -= 1
            self.move_count_label.setText(str(self.move_count))

            # Cập nhật lượt chơi
            if self.move_count % 2 == 0:
                self.current_turn_label.setText("Đỏ")
                self.current_turn_label.setStyleSheet(
                    "font-weight: bold; color: red")
                self.current_player_timer = True
            else:
                self.current_turn_label.setText("Đen")
                self.current_turn_label.setStyleSheet(
                    "font-weight: bold; color: black")
                self.current_player_timer = False

    def reset(self):
        """Reset tất cả thông tin"""
        self.move_count = 0
        self.red_time = 0
        self.black_time = 0
        self.current_player_timer = True

        self.moves_list.clear()
        self.move_count_label.setText("0")
        self.current_turn_label.setText("Đỏ")
        self.current_turn_label.setStyleSheet("font-weight: bold; color: red")

    def clear_moves(self):
        """Xóa danh sách nước đi nhưng giữ lại thông tin khác"""
        self.moves_list.clear()
        self.move_count = 0
        self.move_count_label.setText("0")
        # Reset về lượt đỏ
        self.current_turn_label.setText("Đỏ")
        self.current_turn_label.setStyleSheet("font-weight: bold; color: red")
        self.current_player_timer = True

        # Reset engine analysis với safe check
        self.evaluation_label.setText("0.00")
        self.evaluation_label.setStyleSheet(
            "font-weight: bold; color: #2E8B57;")

        if hasattr(self, 'advantage_label'):
            self.advantage_label.setText("Cân bằng")
            self.advantage_label.setStyleSheet("font-size: 10px; color: #666;")

        self.depth_label.setText("0")

        if hasattr(self, 'nodes_label'):
            self.nodes_label.setText("0")
        if hasattr(self, 'nps_label'):
            self.nps_label.setText("0 NPS")
        if hasattr(self, 'time_label'):
            self.time_label.setText("0ms")

        self.best_move_label.setText("-")

        if hasattr(self, 'pv_label'):
            self.pv_label.setText("-")

        self.update_time_display()

    def set_engine_info(self, evaluation=None, depth=None, best_move=None, nodes=None, nps=None, time_ms=None, pv=None):
        """Cập nhật thông tin từ engine với thông tin chi tiết"""
        if evaluation is not None:
            # Format evaluation score
            if isinstance(evaluation, (int, float)):
                eval_text = f"{evaluation:.2f}"

                # Xác định advantage (chỉ nếu có advantage_label)
                if hasattr(self, 'advantage_label'):
                    if evaluation > 100:
                        self.advantage_label.setText("Đỏ thắng thế")
                        self.advantage_label.setStyleSheet(
                            "font-size: 10px; color: #DC143C; font-weight: bold;")
                    elif evaluation > 50:
                        self.advantage_label.setText("Đỏ có lợi")
                        self.advantage_label.setStyleSheet(
                            "font-size: 10px; color: #FF6347;")
                    elif evaluation > 20:
                        self.advantage_label.setText("Đỏ hơi tốt")
                        self.advantage_label.setStyleSheet(
                            "font-size: 10px; color: #FFA500;")
                    elif evaluation > -20:
                        self.advantage_label.setText("Cân bằng")
                        self.advantage_label.setStyleSheet(
                            "font-size: 10px; color: #666;")
                    elif evaluation > -50:
                        self.advantage_label.setText("Đen hơi tốt")
                        self.advantage_label.setStyleSheet(
                            "font-size: 10px; color: #4169E1;")
                    elif evaluation > -100:
                        self.advantage_label.setText("Đen có lợi")
                        self.advantage_label.setStyleSheet(
                            "font-size: 10px; color: #0000CD;")
                    else:
                        self.advantage_label.setText("Đen thắng thế")
                        self.advantage_label.setStyleSheet(
                            "font-size: 10px; color: #000080; font-weight: bold;")

                # Set evaluation color
                if evaluation > 0:
                    self.evaluation_label.setStyleSheet(
                        "font-weight: bold; color: #DC143C;")
                elif evaluation < 0:
                    self.evaluation_label.setStyleSheet(
                        "font-weight: bold; color: #0000CD;")
                else:
                    self.evaluation_label.setStyleSheet(
                        "font-weight: bold; color: #2E8B57;")
            else:
                eval_text = str(evaluation)

            self.evaluation_label.setText(eval_text)

        if depth is not None:
            self.depth_label.setText(str(depth))

        if best_move is not None:
            self.best_move_label.setText(str(best_move))

        if nodes is not None and hasattr(self, 'nodes_label'):
            # Format nodes với đơn vị K, M
            if nodes >= 1000000:
                nodes_text = f"{nodes/1000000:.1f}M"
            elif nodes >= 1000:
                nodes_text = f"{nodes/1000:.1f}K"
            else:
                nodes_text = str(nodes)
            self.nodes_label.setText(nodes_text)

        if nps is not None and hasattr(self, 'nps_label'):
            # Format NPS với đơn vị
            if nps >= 1000000:
                nps_text = f"{nps/1000000:.1f}M NPS"
            elif nps >= 1000:
                nps_text = f"{nps/1000:.1f}K NPS"
            else:
                nps_text = f"{nps} NPS"
            self.nps_label.setText(nps_text)

        if time_ms is not None and hasattr(self, 'time_label'):
            # Format time
            if time_ms >= 1000:
                time_text = f"{time_ms/1000:.1f}s"
            else:
                time_text = f"{time_ms}ms"
            self.time_label.setText(time_text)

        if pv is not None and hasattr(self, 'pv_label'):
            # Format principal variation
            if isinstance(pv, list):
                pv_text = " ".join(pv[:8])  # Chỉ hiển thị 8 nước đầu
                if len(pv) > 8:
                    pv_text += "..."
            else:
                pv_text = str(pv)
            self.pv_label.setText(pv_text)

    def pause_timer(self):
        """Tạm dừng timer"""
        self.timer.stop()

    def resume_timer(self):
        """Tiếp tục timer"""
        self.timer.start(1000)

    def set_current_player(self, player):
        """
        Cập nhật player hiện tại

        Args:
            player: 'red' hoặc 'black'
        """
        if player == 'red':
            self.current_turn_label.setText("Đỏ")
            self.current_turn_label.setStyleSheet(
                "font-weight: bold; color: red")
            self.current_player_timer = True
        else:
            self.current_turn_label.setText("Đen")
            self.current_turn_label.setStyleSheet(
                "font-weight: bold; color: black")
            self.current_player_timer = False
