# -*- coding: utf-8 -*-
"""
Setup Widget cho Xiangqi GUI
Widget cho phép người dùng xếp cờ tùy ý
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QGridLayout, QButtonGroup, QRadioButton,
                             QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap, QIcon
from ..utils.constants import *
from ..utils.svg_renderer import image_renderer


class SetupWidget(QWidget):
    """Widget cho mode xếp cờ"""

    # Signals
    position_changed = pyqtSignal(str)  # Emit FEN when position changes
    mode_changed = pyqtSignal(str)  # Emit mode: 'setup' or 'play'

    def __init__(self):
        super().__init__()
        self.board_state = None
        self.selected_piece = None
        self.setup_mode = True
        self.board_flipped = False  # Thêm flag để biết có lật bàn cờ không
        self.current_fen = None  # Lưu FEN sau khi apply

        # Valid positions cho từng loại quân
        self.valid_positions = {
            'K': self._get_red_king_positions(),    # Tướng đỏ - chỉ cung đỏ
            'k': self._get_black_king_positions(),  # Tướng đen - chỉ cung đen
            'A': self._get_red_advisor_positions(),  # Sĩ đỏ - chỉ cung đỏ
            'a': self._get_black_advisor_positions(),  # Sĩ đen - chỉ cung đen
            'B': self._get_red_bishop_positions(),  # Tượng đỏ - chỉ đất đỏ
            'b': self._get_black_bishop_positions(),  # Tượng đen - chỉ đất đen
            'R': self._get_all_positions(),         # Xe đỏ
            'r': self._get_all_positions(),         # Xe đen
            'N': self._get_all_positions(),         # Mã đỏ
            'n': self._get_all_positions(),         # Mã đen
            'C': self._get_all_positions(),         # Pháo đỏ
            'c': self._get_all_positions(),         # Pháo đen
            'P': self._get_red_pawn_positions(),    # Tốt đỏ
            'p': self._get_black_pawn_positions()   # Tốt đen
        }

        self.init_ui()
        self.reset_to_standard_position()

    def init_ui(self):
        """Khởi tạo giao diện"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🎯 Xếp Cờ Tướng")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Control buttons
        controls = QHBoxLayout()

        self.standard_btn = QPushButton("📋 Vị Trí Chuẩn")
        self.standard_btn.clicked.connect(self.reset_to_standard_position)
        controls.addWidget(self.standard_btn)

        self.clear_btn = QPushButton("🧹 Bàn Cờ Trống")
        self.clear_btn.clicked.connect(self.clear_board)
        controls.addWidget(self.clear_btn)

        self.empty_btn = QPushButton("⬜ Hoàn Toàn Trống")
        self.empty_btn.clicked.connect(self.reset_to_completely_empty)
        controls.addWidget(self.empty_btn)

        self.apply_btn = QPushButton("✅ Apply Bàn Cờ")
        self.apply_btn.clicked.connect(self.apply_board)
        self.apply_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        controls.addWidget(self.apply_btn)

        # Nút Back to Setup (ẩn ban đầu)
        self.back_btn = QPushButton("🔙 Quay Lại Xếp Cờ")
        self.back_btn.clicked.connect(self.back_to_setup)
        self.back_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
        self.back_btn.hide()  # Ẩn ban đầu
        controls.addWidget(self.back_btn)

        layout.addLayout(controls)

        # Main content
        content = QHBoxLayout()

        # Left: Board
        self.board_widget = SetupBoardWidget()
        self.board_widget.piece_placed.connect(self.on_piece_placed)
        self.board_widget.piece_removed.connect(self.on_piece_removed)
        content.addWidget(self.board_widget, 3)  # Tăng tỷ lệ board

        # Right: Piece palette
        palette_frame = QFrame()
        palette_frame.setFrameStyle(QFrame.StyledPanel)
        palette_frame.setMinimumWidth(250)  # Đảm bảo width tối thiểu
        palette_layout = QVBoxLayout(palette_frame)

        palette_title = QLabel("🏺 Bảng Quân Cờ")
        palette_title.setFont(QFont("Arial", 12, QFont.Bold))
        palette_title.setAlignment(Qt.AlignCenter)
        palette_layout.addWidget(palette_title)

        self.piece_palette = PiecePalette()
        self.piece_palette.piece_selected.connect(self.on_piece_selected)
        palette_layout.addWidget(self.piece_palette)

        content.addWidget(palette_frame, 2)  # Tăng tỷ lệ palette
        layout.addLayout(content)

        # Status
        self.status_label = QLabel(
            "✨ Chế độ xếp cờ - Chọn quân từ bảng bên phải, chuột phải để xóa quân")
        self.status_label.setStyleSheet(
            "QLabel { color: blue; font-weight: bold; }")
        layout.addWidget(self.status_label)

    def reset_to_standard_position(self):
        """Reset về vị trí chuẩn"""
        # Parse FEN position
        board = [[None for _ in range(BOARD_WIDTH)]
                 for _ in range(BOARD_HEIGHT)]

        fen_parts = INITIAL_POSITION.split()
        board_fen = fen_parts[0]

        row = 0
        col = 0

        for char in board_fen:
            if char == '/':
                row += 1
                col = 0
            elif char.isdigit():
                col += int(char)
            else:
                if row < BOARD_HEIGHT and col < BOARD_WIDTH:
                    board[row][col] = char
                col += 1

        self.board_state = board
        self.board_widget.set_board_state(board)
        self.piece_palette.reset_to_standard()  # Cập nhật palette
        self.emit_position_changed()
        self.status_label.setText("📋 Đã reset về vị trí chuẩn")

    def clear_board(self):
        """Xóa hết quân cờ nhưng giữ nguyên 2 tướng trong cung"""
        # Tạo bàn cờ trống
        self.board_state = [[None for _ in range(
            BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

        # Giữ nguyên 2 tướng trong cung để người dùng biết bên nào là màu nào
        self.board_state[0][4] = 'k'  # Tướng đen ở cung đen (hàng 0)
        self.board_state[9][4] = 'K'  # Tướng đỏ ở cung đỏ (hàng 9)

        self.board_widget.set_board_state(self.board_state)

        # Reset palette: chỉ giảm 2 tướng (đã đặt trên bàn), còn lại đầy đủ
        self.piece_palette.reset_to_empty()
        self.piece_palette.piece_placed_on_board('k')  # Giảm tướng đen
        self.piece_palette.piece_placed_on_board('K')  # Giảm tướng đỏ

        self.emit_position_changed()
        self.status_label.setText(
            "🧹 Đã xóa hết quân cờ (giữ 2 tướng để phân biệt màu)")

    def on_piece_selected(self, piece):
        """Xử lý khi chọn quân từ palette"""
        self.selected_piece = piece
        self.board_widget.set_selected_piece(piece)
        if piece:
            piece_name = PIECE_NAMES_VN.get(piece, piece)
            color = "Đỏ" if piece.isupper() else "Đen"
            self.status_label.setText(
                f"🎯 Đã chọn {piece_name} {color} - Click để đặt, chuột phải để xóa quân")
        else:
            self.status_label.setText(
                "✨ Chế độ xếp cờ - Chọn quân từ bảng bên phải, chuột phải để xóa quân")

    def on_piece_placed(self, row, col, piece):
        """Xử lý khi đặt quân lên bàn"""

        if self.board_state:
            # Xóa quân cũ nếu có
            old_piece = self.board_state[row][col]
            if old_piece:

                self.piece_palette.piece_removed_from_board(old_piece)

            # Đặt quân mới
            self.board_state[row][col] = piece

            self.piece_palette.piece_placed_on_board(piece)

            self.emit_position_changed()
            piece_name = PIECE_NAMES_VN.get(piece, piece)
            color = "Đỏ" if piece.isupper() else "Đen"
            self.status_label.setText(
                f"✅ Đã đặt {piece_name} {color} tại ({row+1},{col+1})")

    def on_piece_removed(self, row, col):
        """Xử lý khi xóa quân khỏi bàn"""
        if self.board_state and self.board_state[row][col]:
            piece = self.board_state[row][col]

            self.board_state[row][col] = None
            self.piece_palette.piece_removed_from_board(piece)

            self.emit_position_changed()
            self.status_label.setText(f"❌ Đã xóa quân tại ({row+1},{col+1})")

    def emit_position_changed(self):
        """Emit signal khi position thay đổi"""
        fen = self.board_to_fen()
        if fen:
            self.position_changed.emit(fen)

    def board_to_fen(self):
        """Chuyển board state thành FEN"""
        if not self.board_state:
            return None

        fen_rows = []
        for row in range(BOARD_HEIGHT):
            fen_row = ""
            empty_count = 0

            for col in range(BOARD_WIDTH):
                piece = self.board_state[row][col]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece

            if empty_count > 0:
                fen_row += str(empty_count)

            fen_rows.append(fen_row)

        board_fen = "/".join(fen_rows)
        return f"{board_fen} w - - 0 1"  # Default to red's turn

    def get_board_state(self):
        """Lấy board state hiện tại"""
        return self.board_state

    def set_board_state(self, board_state):
        """Set board state"""
        self.board_state = [row[:]
                            for row in board_state] if board_state else None
        if self.board_widget:
            self.board_widget.set_board_state(self.board_state)

        # Đồng bộ palette với board state
        self.sync_palette_with_board()

    def sync_palette_with_board(self):
        """Đồng bộ palette với board state hiện tại"""
        if not self.board_state:
            self.piece_palette.reset_to_empty()
            return

        # Đếm số quân hiện có trên bàn
        pieces_on_board = {}
        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.board_state[row][col]
                if piece:
                    pieces_on_board[piece] = pieces_on_board.get(piece, 0) + 1

        # Tính số quân còn lại trong palette
        total_pieces = {
            'R': 2, 'N': 2, 'B': 2, 'A': 2, 'K': 1, 'C': 2, 'P': 5,
            'r': 2, 'n': 2, 'b': 2, 'a': 2, 'k': 1, 'c': 2, 'p': 5
        }

        remaining_pieces = {}
        for piece, total in total_pieces.items():
            used = pieces_on_board.get(piece, 0)
            remaining_pieces[piece] = max(0, total - used)

        # Cập nhật palette
        self.piece_palette.piece_counts = remaining_pieces
        self.piece_palette.update_display()

    def set_board_flipped(self, flipped):
        """Set board flip state"""
        self.board_flipped = flipped
        # Trigger redraw của board widget
        if hasattr(self, 'board_widget'):
            self.board_widget.update()

    def _get_red_king_positions(self):
        """Vị trí hợp lệ cho Tướng đỏ - cung đỏ"""
        positions = set()
        # Cung đỏ ở bottom (hàng 7-9, cột 3-5) - logical coordinates
        for row in range(7, 10):
            for col in range(3, 6):
                positions.add((row, col))
        return positions

    def _get_black_king_positions(self):
        """Vị trí hợp lệ cho Tướng đen - cung đen"""
        positions = set()
        # Cung đen ở top (hàng 0-2, cột 3-5) - logical coordinates
        for row in range(0, 3):
            for col in range(3, 6):
                positions.add((row, col))
        return positions

    def _get_red_advisor_positions(self):
        """Vị trí hợp lệ cho Sĩ đỏ - chỉ cung đỏ"""
        red_advisor_coords = [(7, 3), (7, 5), (8, 4), (9, 3), (9, 5)]
        return set(red_advisor_coords)

    def _get_black_advisor_positions(self):
        """Vị trí hợp lệ cho Sĩ đen - chỉ cung đen"""
        black_advisor_coords = [(0, 3), (0, 5), (1, 4), (2, 3), (2, 5)]
        return set(black_advisor_coords)

    def _get_red_bishop_positions(self):
        """Vị trí hợp lệ cho Tượng đỏ - chỉ đất đỏ (hàng 5-9)"""
        red_bishop_coords = [(5, 2), (5, 6), (7, 0),
                             (7, 4), (7, 8), (9, 2), (9, 6)]
        return set(red_bishop_coords)

    def _get_black_bishop_positions(self):
        """Vị trí hợp lệ cho Tượng đen - chỉ đất đen (hàng 0-4)"""
        black_bishop_coords = [(0, 2), (0, 6), (2, 0),
                               (2, 4), (2, 8), (4, 2), (4, 6)]
        return set(black_bishop_coords)

    def _get_red_pawn_positions(self):
        """Vị trí hợp lệ cho Tốt Đỏ (P) - logical coordinates"""
        positions = set()

        # Bên này sông (hàng 5-6) - chỉ 5 vị trí cố định
        for col in [0, 2, 4, 6, 8]:
            positions.add((5, col))
            positions.add((6, col))
        # Qua sông (hàng 0-4) - có thể ở bất kỳ đâu
        for row in range(0, 5):
            for col in range(9):
                positions.add((row, col))

        return positions

    def _get_black_pawn_positions(self):
        """Vị trí hợp lệ cho Tốt Đen (p) - logical coordinates"""
        positions = set()

        # Bên này sông (hàng 3-4) - chỉ 5 vị trí cố định
        for col in [0, 2, 4, 6, 8]:
            positions.add((3, col))
            positions.add((4, col))
        # Qua sông (hàng 5-9) - có thể ở bất kỳ đâu
        for row in range(5, 10):
            for col in range(9):
                positions.add((row, col))

        return positions

    def _get_pawn_positions(self):
        """DEPRECATED - dùng _get_red_pawn_positions() và _get_black_pawn_positions()"""
        # Không dùng nữa vì đã tách riêng theo màu
        return set()

    def _get_all_positions(self):
        """Tất cả vị trí trên bàn cờ"""
        positions = set()
        for row in range(10):
            for col in range(9):
                positions.add((row, col))
        return positions

    def is_valid_position(self, piece, row, col):
        """Kiểm tra vị trí có hợp lệ cho quân này không"""
        if not (0 <= row < 10 and 0 <= col < 9):
            return False

        # Kiểm tra vị trí cơ bản có hợp lệ không
        if (row, col) not in self.valid_positions.get(piece, set()):
            return False

        # Kiểm tra thêm giới hạn đặc biệt cho một số loại quân
        return self._check_special_constraints(piece, row, col)

    def _check_special_constraints(self, piece, row, col):
        """Kiểm tra các giới hạn đặc biệt cho từng loại quân"""
        if not self.board_state:
            return True

        # Kiểm tra cho Tốt Đen (p)
        if piece == 'p':
            return self._check_black_pawn_constraints(row, col)

        # Kiểm tra cho Tốt Đỏ (P)
        elif piece == 'P':
            return self._check_red_pawn_constraints(row, col)

        # Kiểm tra cho Tướng - chỉ được 1 quân
        elif piece in ['K', 'k']:
            return self._check_king_constraints(piece, row, col)

        # Kiểm tra cho Sĩ - chỉ được 2 quân mỗi bên
        elif piece in ['A', 'a']:
            return self._check_advisor_constraints(piece, row, col)

        # Kiểm tra cho Tượng - chỉ được 2 quân mỗi bên
        elif piece in ['B', 'b']:
            return self._check_bishop_constraints(piece, row, col)

        return True

    def _get_picked_position(self):
        """Lấy vị trí đang được picked (nếu có)"""
        # Tìm board widget để lấy picked position
        if hasattr(self, 'board_widget') and hasattr(self.board_widget, 'picked_position'):
            return self.board_widget.picked_position
        return None

    def _check_black_pawn_constraints(self, row, col):
        """Kiểm tra giới hạn cho Tốt Đen"""
        if not self.board_state:
            return True

        # Lấy vị trí đang được picked để bỏ qua khi đếm
        picked_pos = self._get_picked_position()

        # Đếm số tốt đen hiện có (bỏ qua vị trí picked)
        black_pawns_on_board = 0
        black_pawns_on_own_side = 0  # Ở hàng 3-4

        for r in range(10):
            for c in range(9):
                # Bỏ qua vị trí đang được picked
                if picked_pos and (r, c) == picked_pos:
                    continue

                if self.board_state[r][c] == 'p':
                    black_pawns_on_board += 1
                    # Nếu ở bên này sông (hàng 3-4)
                    if r in [3, 4]:
                        black_pawns_on_own_side += 1

        # Nếu đã có 5 tốt đen thì không thể đặt thêm
        if black_pawns_on_board >= 5:
            return False

        # Nếu muốn đặt ở bên này sông (hàng 3-4)
        if row in [3, 4]:
            # Kiểm tra xem đã có tốt ở vị trí này chưa
            if self.board_state[row][col] is not None:
                return False

            # Chỉ cho phép tối đa 5 tốt ở bên này sông
            # và chỉ ở các cột 0,2,4,6,8
            if col not in [0, 2, 4, 6, 8]:
                return False

            # Đếm số tốt đen đã có ở bên này sông
            if black_pawns_on_own_side >= 5:
                return False

        return True

    def _check_red_pawn_constraints(self, row, col):
        """Kiểm tra giới hạn cho Tốt Đỏ"""
        if not self.board_state:
            return True

        # Lấy vị trí đang được picked để bỏ qua khi đếm
        picked_pos = self._get_picked_position()

        # Đếm số tốt đỏ hiện có (bỏ qua vị trí picked)
        red_pawns_on_board = 0
        red_pawns_on_own_side = 0  # Ở hàng 5-6

        for r in range(10):
            for c in range(9):
                # Bỏ qua vị trí đang được picked
                if picked_pos and (r, c) == picked_pos:
                    continue

                if self.board_state[r][c] == 'P':
                    red_pawns_on_board += 1
                    # Nếu ở bên này sông (hàng 5-6)
                    if r in [5, 6]:
                        red_pawns_on_own_side += 1

        # Nếu đã có 5 tốt đỏ thì không thể đặt thêm
        if red_pawns_on_board >= 5:
            return False

        # Nếu muốn đặt ở bên này sông (hàng 5-6)
        if row in [5, 6]:
            # Kiểm tra xem đã có tốt ở vị trí này chưa
            if self.board_state[row][col] is not None:
                return False

            # Chỉ cho phép ở các cột 0,2,4,6,8
            if col not in [0, 2, 4, 6, 8]:
                return False

            # Đếm số tốt đỏ đã có ở bên này sông
            if red_pawns_on_own_side >= 5:
                return False

        return True

    def _check_king_constraints(self, piece, row, col):
        """Kiểm tra chỉ có 1 tướng mỗi bên"""
        if not self.board_state:
            return True

        # Lấy vị trí đang được picked để bỏ qua khi đếm
        picked_pos = self._get_picked_position()

        count = 0
        for r in range(10):
            for c in range(9):
                # Bỏ qua vị trí đang được picked
                if picked_pos and (r, c) == picked_pos:
                    continue

                if self.board_state[r][c] == piece:
                    count += 1

        return count < 1

    def _check_advisor_constraints(self, piece, row, col):
        """Kiểm tra chỉ có 2 sĩ mỗi bên"""
        if not self.board_state:
            return True

        # Lấy vị trí đang được picked để bỏ qua khi đếm
        picked_pos = self._get_picked_position()

        count = 0
        for r in range(10):
            for c in range(9):
                # Bỏ qua vị trí đang được picked
                if picked_pos and (r, c) == picked_pos:
                    continue

                if self.board_state[r][c] == piece:
                    count += 1

        return count < 2

    def _check_bishop_constraints(self, piece, row, col):
        """Kiểm tra chỉ có 2 tượng mỗi bên"""
        if not self.board_state:
            return True

        # Lấy vị trí đang được picked để bỏ qua khi đếm
        picked_pos = self._get_picked_position()

        count = 0
        for r in range(10):
            for c in range(9):
                # Bỏ qua vị trí đang được picked
                if picked_pos and (r, c) == picked_pos:
                    continue

                if self.board_state[r][c] == piece:
                    count += 1

        return count < 2

    def sync_board_flip(self, flipped):
        """Đồng bộ flip state từ main window"""
        self.board_widget.set_board_flipped(flipped)

    def get_current_fen(self):
        """Lấy FEN hiện tại từ board state"""
        if not self.board_state:
            return None

        # Kiểm tra có ít nhất 2 tướng trước khi tạo FEN
        kings = self.find_kings()
        if len(kings) < 2:
            return None

        # Nếu đã có current_fen (đã apply), return luôn
        if self.current_fen:
            return self.current_fen

        # Chưa apply, hỏi user chọn turn
        turn = self.ask_for_turn()
        if turn is None:
            return None  # User cancelled

        return self.board_to_fen_with_turn(turn)

    def validate_board_and_get_fen(self):
        """Validate bàn cờ và lấy FEN với turn được chọn"""
        if not self.board_state:
            QMessageBox.warning(self, "Lỗi", "Không có bàn cờ để validate!")
            return None

        # Check có đúng 2 tướng không
        kings = self.find_kings()
        if len(kings) != 2:
            if len(kings) < 2:
                QMessageBox.warning(self, "Lỗi Bàn Cờ",
                                    f"Thiếu tướng! Hiện tại chỉ có {len(kings)} tướng, cần đúng 2 tướng (1 đỏ, 1 đen).")
            else:
                QMessageBox.warning(self, "Lỗi Bàn Cờ",
                                    f"Quá nhiều tướng! Hiện tại có {len(kings)} tướng, chỉ được có 2 tướng (1 đỏ, 1 đen).")
            return None

        # Check có đúng 1 tướng đỏ và 1 tướng đen không
        red_king = None
        black_king = None
        for king_pos, king_piece in kings:
            if king_piece == 'K':
                if red_king:
                    QMessageBox.warning(
                        self, "Lỗi Bàn Cờ", "Có quá nhiều tướng đỏ! Chỉ được có 1 tướng đỏ.")
                    return None
                red_king = king_pos
            elif king_piece == 'k':
                if black_king:
                    QMessageBox.warning(
                        self, "Lỗi Bàn Cờ", "Có quá nhiều tướng đen! Chỉ được có 1 tướng đen.")
                    return None
                black_king = king_pos

        if not red_king or not black_king:
            QMessageBox.warning(self, "Lỗi Bàn Cờ",
                                "Cần có đúng 1 tướng đỏ và 1 tướng đen!")
            return None

        # Check 2 tướng có đối mặt không
        if self.kings_facing_each_other(red_king, black_king):
            QMessageBox.warning(self, "Lỗi Bàn Cờ",
                                "Hai tướng không được đối mặt nhau trên cùng một cột mà không có quân cản!")
            return None

        # Tất cả validation pass, hỏi user chọn turn
        turn = self.ask_for_turn()
        if turn is None:
            return None  # User cancelled

        # Tạo FEN với turn được chọn
        fen = self.board_to_fen_with_turn(turn)
        return fen

    def find_kings(self):
        """Tìm tất cả tướng trên bàn cờ"""
        kings = []
        for row in range(10):
            for col in range(9):
                piece = self.board_state[row][col]
                if piece in ['K', 'k']:
                    kings.append(((row, col), piece))
        return kings

    def kings_facing_each_other(self, red_king_pos, black_king_pos):
        """Check xem 2 tướng có đối mặt nhau không"""
        red_row, red_col = red_king_pos
        black_row, black_col = black_king_pos

        # Chỉ check nếu cùng cột
        if red_col != black_col:
            return False

        # Check có quân cản giữa 2 tướng không
        min_row = min(red_row, black_row)
        max_row = max(red_row, black_row)

        for row in range(min_row + 1, max_row):
            if self.board_state[row][red_col] is not None:
                return False  # Có quân cản

        return True  # Không có quân cản = đối mặt

    def ask_for_turn(self):
        """Hỏi user chọn lượt đi tiếp theo"""
        msg = QMessageBox()
        msg.setWindowTitle("Chọn Lượt Đi")
        msg.setText("Bàn cờ hợp lệ!\nVui lòng chọn lượt đi tiếp theo:")
        msg.setIcon(QMessageBox.Question)

        red_btn = msg.addButton("🔴 Đỏ đi", QMessageBox.YesRole)
        black_btn = msg.addButton("⚫ Đen đi", QMessageBox.NoRole)
        cancel_btn = msg.addButton("❌ Hủy", QMessageBox.RejectRole)

        msg.exec_()

        if msg.clickedButton() == red_btn:
            return 'w'  # White/Red turn
        elif msg.clickedButton() == black_btn:
            return 'b'  # Black turn
        else:
            return None  # Cancelled

    def board_to_fen_with_turn(self, turn):
        """Chuyển board state thành FEN với turn được chọn"""
        if not self.board_state:
            return None

        fen_rows = []
        for row in range(10):
            fen_row = ""
            empty_count = 0

            for col in range(9):
                piece = self.board_state[row][col]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece

            if empty_count > 0:
                fen_row += str(empty_count)

            fen_rows.append(fen_row)

        board_fen = "/".join(fen_rows)
        return f"{board_fen} {turn} - - 0 1"

    def reset_to_completely_empty(self):
        """Reset về bàn cờ hoàn toàn trống"""
        self.board_state = [[None for _ in range(
            BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.board_widget.set_board_state(self.board_state)
        self.piece_palette.reset_to_empty()
        self.emit_position_changed()
        self.status_label.setText("⬜ Đã tạo bàn cờ hoàn toàn trống")

    def apply_board(self):
        """Validate và apply bàn cờ hiện tại"""
        print(f"🚀 [SETUP] ===== APPLY BOARD CALLED =====")
        fen = self.validate_board_and_get_fen()
        print(f"🚀 [SETUP] Validated FEN: {fen}")
        if fen:
            self.current_fen = fen  # Lưu FEN đã apply
            self.position_changed.emit(fen)

            # Load lại toàn bộ engine như khi tạo ván mới
            self._reload_engines()

            self.status_label.setText(
                "✅ Đã apply bàn cờ thành công! Đang restart engines như ván mới... 🔄")

            # Chuyển sang play mode
            self.setup_mode = False
            self.board_widget.set_setup_mode(False)
            self.mode_changed.emit('play')

            # Show back button, hide apply button
            self.apply_btn.hide()
            self.back_btn.show()
        else:
            self.status_label.setText(
                "❌ Không thể apply - vui lòng kiểm tra lại bàn cờ")

    def load_from_fen(self, fen_string):
        """
        Load FEN string vào setup widget để chỉnh sửa

        Args:
            fen_string: FEN notation string

        Returns:
            bool: True nếu load thành công
        """
        try:
            print(f"🎯 SetupWidget: Loading FEN: {fen_string[:50]}...")

            # Parse FEN để lấy board state và active color
            parts = fen_string.strip().split()
            if len(parts) < 1:
                print("❌ SetupWidget: Invalid FEN format")
                return False

            # Parse board position
            board_fen = parts[0]
            board = self._parse_fen_to_board(board_fen)
            if board is None:
                print("❌ SetupWidget: Failed to parse board from FEN")
                return False

            # Update board state
            self.board_state = board
            self.board_widget.set_board_state(board)

            # Sync palette với board hiện tại
            self.sync_palette_with_board()

            # Emit position changed để multi-engine có thể phân tích
            self.emit_position_changed()

            print(f"✅ SetupWidget: Successfully loaded FEN")
            self.status_label.setText(
                "🎯 Đã load vị trí hiện tại vào setup mode - Có thể chỉnh sửa")

            return True

        except Exception as e:
            print(f"❌ SetupWidget: Error loading FEN: {e}")
            return False

    def _parse_fen_to_board(self, board_fen):
        """
        Parse board FEN thành board state

        Args:
            board_fen: Board part của FEN string

        Returns:
            list: 2D board array hoặc None nếu lỗi
        """
        try:
            # Tạo board rỗng 10x9
            board = [[None for _ in range(9)] for _ in range(10)]

            ranks = board_fen.split('/')
            if len(ranks) != 10:  # Xiangqi có 10 hàng
                print(f"❌ SetupWidget: FEN needs 10 ranks, got {len(ranks)}")
                return None

            for rank_idx, rank in enumerate(ranks):
                col_idx = 0
                for char in rank:
                    if char.isdigit():
                        # Số ô trống
                        col_idx += int(char)
                    else:
                        # Quân cờ
                        if col_idx >= 9:  # Xiangqi có 9 cột
                            print(
                                f"❌ SetupWidget: Too many pieces in rank {rank_idx}")
                            return None
                        board[rank_idx][col_idx] = char
                        col_idx += 1

                if col_idx != 9:
                    print(
                        f"❌ SetupWidget: Rank {rank_idx} has {col_idx} columns instead of 9")
                    return None

            return board

        except Exception as e:
            print(f"❌ SetupWidget: Error parsing board FEN: {e}")
            return None

    def _reload_engines(self):
        """Reload engines hiện có với FEN mới từ setup mode"""
        try:
            print(f"🎯 [SETUP] ===== RELOADING ENGINES CALLED ===== ")
            print(f"🎯 [SETUP] Current FEN: {self.current_fen}")
            print("🎯 [SETUP] Reloading engines with new FEN...")

            # Tìm main window để access multi-engine manager
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'multi_engine_widget'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'multi_engine_widget'):
                multi_engine_widget = main_window.multi_engine_widget

                if multi_engine_widget and self.current_fen:
                    # 1. FORCE UPDATE main window game state với FEN mới từ setup
                    if hasattr(main_window, 'game_state'):
                        print(
                            f"🎯 [SETUP] Updating main window with new FEN: {self.current_fen[:50]}...")

                        # Load FEN vào main window game state
                        success = main_window.game_state.load_from_fen(
                            self.current_fen)
                        if success:
                            # Update board widget với game state mới
                            main_window.board_widget.board_state = [
                                row[:] for row in main_window.game_state.board]
                            main_window.board_widget.set_current_player(
                                main_window.game_state.current_player)
                            main_window.board_widget.update()
                            print(
                                "✅ [SETUP] Successfully updated main window game state")
                        else:
                            print(
                                "❌ [SETUP] Failed to load FEN into main window game state")

                    # 2. Clear board widget hints
                    if hasattr(main_window, 'board_widget'):
                        main_window.board_widget.clear_engine_hint()
                        main_window.board_widget.selected_square = None
                        main_window.board_widget.possible_moves = []
                        main_window.board_widget.update()
                        print("✓ [SETUP] Cleared board widget state")

                    # 3. Reload engines với FEN mới (method đơn giản)
                    current_moves = main_window.convert_moves_to_engine_notation(
                        main_window.game_state.move_history) if hasattr(main_window, 'convert_moves_to_engine_notation') else []

                    multi_engine_widget.reload_engines_with_new_position(
                        self.current_fen, current_moves)

                    # 4. Emit position changed để sync với các components khác
                    if hasattr(main_window, '_emit_position_changed'):
                        main_window._emit_position_changed()
                        print(
                            "🚀 [SETUP] Called _emit_position_changed() for sync")

                    # Update status
                    self.status_label.setText(
                        "🎉 Engines đã được reload với FEN mới! 🔄")
                    print("✅ [SETUP] Engine reload completed successfully")

                else:
                    print("❌ [SETUP] No multi_engine_widget or current_fen")
            else:
                print(
                    "❌ [SETUP] Could not find main window with multi_engine_widget")

        except Exception as e:
            print(f"❌ [SETUP] Error reloading engines: {e}")
            import traceback
            traceback.print_exc()

    def back_to_setup(self):
        """Quay lại chế độ xếp cờ"""
        self.setup_mode = True
        self.board_widget.set_setup_mode(True)
        self.current_fen = None  # Reset current_fen
        self.status_label.setText(
            "✨ Chế độ xếp cờ - Chọn quân từ bảng bên phải, chuột phải để xóa quân")

        # Show apply button, hide back button
        self.apply_btn.show()
        self.back_btn.hide()


class SetupBoardWidget(QWidget):
    """Board widget cho setup mode"""

    # Signals
    piece_placed = pyqtSignal(int, int, str)  # row, col, piece
    piece_removed = pyqtSignal(int, int)      # row, col

    def __init__(self):
        super().__init__()
        self.board_state = None
        self.selected_piece = None  # Quân được chọn từ palette
        self.picked_piece = None    # Quân được pick up từ bàn cờ
        self.picked_position = None  # Vị trí của quân được pick up
        self.setup_mode = True
        self.highlight_positions = set()
        self.board_pixmap = None
        self.piece_pixmaps = {}

        # Scale factor để board nhỏ hơn bàn cờ chính (45%)
        self.board_scale = BOARD_SCALE_FACTOR_SETUP

        # Tính kích thước dựa trên scale
        board_width = int(BOARD_SVG_WIDTH * self.board_scale)
        board_height = int(BOARD_SVG_HEIGHT * self.board_scale)

        self.setMinimumSize(board_width + 40, board_height + 40)
        self.setMouseTracking(True)
        self.load_assets()

    def load_assets(self):
        """Load assets"""
        # Board với scale factor
        board_width = int(BOARD_SVG_WIDTH * self.board_scale)
        board_height = int(BOARD_SVG_HEIGHT * self.board_scale)
        board_size = QSize(board_width, board_height)

        # Load board gốc rồi scale
        original_board = image_renderer.render_board_png(
            QSize(BOARD_SVG_WIDTH, BOARD_SVG_HEIGHT))
        if original_board:
            self.board_pixmap = original_board.scaled(
                board_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            self.board_pixmap = None

        # Pieces
        piece_size = QSize(PIECE_SIZE, PIECE_SIZE)
        pieces = ['R', 'N', 'B', 'A', 'K', 'C',
                  'P', 'r', 'n', 'b', 'a', 'k', 'c', 'p']

        for piece in pieces:
            pixmap = image_renderer.render_piece_png(piece, piece_size)
            if pixmap:
                self.piece_pixmaps[piece] = pixmap

    def set_board_state(self, board_state):
        """Set board state"""
        self.board_state = board_state
        self.update()

    def set_selected_piece(self, piece):
        """Set selected piece từ palette"""
        self.selected_piece = piece
        self.update_highlights()

    def set_setup_mode(self, setup_mode):
        """Set setup mode"""
        self.setup_mode = setup_mode
        if not setup_mode:
            self.selected_piece = None
            self.picked_piece = None
            self.picked_position = None
            self.highlight_positions.clear()
        self.update()

    def update_highlights(self):
        """Update highlighted positions"""
        self.highlight_positions.clear()

        # Lấy flip state từ parent
        parent = self.parent()
        while parent and not hasattr(parent, 'is_valid_position'):
            parent = parent.parent()

        if not parent:
            return

        # Nếu có quân được pick up từ bàn cờ
        if self.picked_piece and self.setup_mode:
            for row in range(10):
                for col in range(9):
                    # Cho phép di chuyển đến vị trí hợp lệ (trừ vị trí hiện tại)
                    if (row, col) != self.picked_position and parent.is_valid_position(self.picked_piece, row, col):
                        self.highlight_positions.add((row, col))

        # Nếu có quân được chọn từ palette
        elif self.selected_piece and self.setup_mode:
            for row in range(10):
                for col in range(9):
                    if parent.is_valid_position(self.selected_piece, row, col):
                        self.highlight_positions.add((row, col))

        self.update()

    def paintEvent(self, event):
        """Vẽ board"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Vẽ board
        if self.board_pixmap:
            board_rect = self.get_board_rect()
            # Board đã được scale từ trước, chỉ cần draw thẳng
            painter.drawPixmap(board_rect.topLeft(), self.board_pixmap)

            # Lưu actual board rect để dùng cho coordinate conversion
            self._actual_board_rect = board_rect

        # Vẽ highlights
        self.draw_highlights(painter)

        # Vẽ pieces
        self.draw_pieces(painter)

    def get_board_rect(self):
        """Lấy rectangle của board"""
        # Tính board rect dựa trên kích thước đã scale
        widget_rect = self.rect()
        margin = 20

        # Tính kích thước board sau scale
        board_width = int(BOARD_SVG_WIDTH * self.board_scale)
        board_height = int(BOARD_SVG_HEIGHT * self.board_scale)

        # Center board trong widget
        x = (widget_rect.width() - board_width) // 2
        y = (widget_rect.height() - board_height) // 2

        # Đảm bảo không âm
        x = max(margin, x)
        y = max(margin, y)

        from PyQt5.QtCore import QRect
        return QRect(x, y, board_width, board_height)

    def calc_piece_position(self, row, col, board_rect):
        """Tính vị trí piece dùng hàm chuẩn từ constants"""
        from ..utils.constants import board_coords_to_pixel
        return board_coords_to_pixel(row, col, board_rect)

    def draw_highlights(self, painter):
        """Vẽ highlight positions"""
        if not self.highlight_positions:
            return

        board_rect = getattr(self, '_actual_board_rect', self.get_board_rect())

        # Lấy flip state từ parent SetupWidget
        parent_widget = self.parent()
        while parent_widget and not hasattr(parent_widget, 'board_flipped'):
            parent_widget = parent_widget.parent()

        board_flipped = parent_widget.board_flipped if parent_widget else False

        painter.setPen(QPen(QColor(255, 255, 0, 180), 3))
        painter.setBrush(QBrush(QColor(255, 255, 0, 50)))

        for row, col in self.highlight_positions:
            # Nếu board bị flip, transform tọa độ hiển thị
            display_row, display_col = row, col
            if board_flipped:
                display_row = 9 - row
                display_col = 8 - col

            # Tính tọa độ trực tiếp cho setup widget với display coordinates
            center_x, center_y = self.calc_piece_position(
                display_row, display_col, board_rect)

            # Vẽ circle nhỏ ở center
            painter.drawEllipse(int(center_x - 8), int(center_y - 8), 16, 16)

    def draw_pieces(self, painter):
        """Vẽ pieces"""
        if not self.board_state:
            return

        board_rect = getattr(self, '_actual_board_rect', self.get_board_rect())

        # Lấy flip state từ parent SetupWidget
        parent_widget = self.parent()
        while parent_widget and not hasattr(parent_widget, 'board_flipped'):
            parent_widget = parent_widget.parent()

        board_flipped = parent_widget.board_flipped if parent_widget else False

        for row in range(10):
            for col in range(9):
                piece = self.board_state[row][col]
                if piece:
                    pixmap = self.piece_pixmaps.get(piece)
                    if pixmap:
                        # Nếu board bị flip, transform tọa độ hiển thị
                        display_row, display_col = row, col
                        if board_flipped:
                            display_row = 9 - row
                            display_col = 8 - col

                        # Tính tọa độ dùng hàm chuẩn với display coordinates
                        center_x, center_y = self.calc_piece_position(
                            display_row, display_col, board_rect)

                        # Tính scale factor như board_widget
                        scale_factor = min(board_rect.width() / BOARD_SVG_WIDTH,
                                           board_rect.height() / BOARD_SVG_HEIGHT)
                        scaled_piece_size = int(PIECE_SIZE * scale_factor)

                        scaled_pixmap = pixmap.scaled(
                            scaled_piece_size, scaled_piece_size,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)

                        # Nếu quân này đang được pick up thì vẽ mờ và highlight 4 góc
                        if self.picked_position == (row, col):
                            # Vẽ mờ 50%
                            painter.setOpacity(0.5)
                            painter.drawPixmap(
                                int(center_x - scaled_piece_size // 2),
                                int(center_y - scaled_piece_size // 2),
                                scaled_pixmap)
                            painter.setOpacity(1.0)

                            # Vẽ 4 góc đỏ
                            self.draw_picked_highlight(
                                painter, center_x, center_y, scaled_piece_size)
                        else:
                            # Vẽ bình thường
                            painter.drawPixmap(
                                int(center_x - scaled_piece_size // 2),
                                int(center_y - scaled_piece_size // 2),
                                scaled_pixmap)

    def draw_picked_highlight(self, painter, center_x, center_y, piece_size):
        """Vẽ highlight 4 góc cho quân được pick up"""
        painter.setPen(QPen(QColor(255, 0, 0), 3))  # Đỏ
        corner_size = 8
        offset = piece_size // 2

        # 4 góc quanh quân cờ
        corners = [
            (center_x - offset, center_y - offset),  # Top-left
            (center_x + offset - corner_size, center_y - offset),  # Top-right
            (center_x - offset, center_y + offset - corner_size),  # Bottom-left
            (center_x + offset - corner_size, center_y +
             offset - corner_size)  # Bottom-right
        ]

        for x, y in corners:
            painter.drawRect(int(x), int(y), corner_size, corner_size)

    def mousePressEvent(self, event):
        """Xử lý mouse click với pick-and-place mechanism"""
        if not self.setup_mode:
            return

        row, col = self.pixel_to_board_coords(event.x(), event.y())

        # Click trong bàn cờ
        if row is not None and col is not None:

            # Chuột phải - xóa quân
            if event.button() == Qt.RightButton:
                if self.board_state and self.board_state[row][col]:
                    # Xóa quân tại vị trí này
                    self.piece_removed.emit(row, col)

                # Clear picked state nếu có
                if self.picked_piece:
                    self.picked_piece = None
                    self.picked_position = None
                    self.update_highlights()

                return

            # Chuột trái - đặt/di chuyển quân
            elif event.button() == Qt.LeftButton:
                # Nếu đang có quân picked up
                if self.picked_piece:
                    # Di chuyển quân đến vị trí mới
                    parent = self.parent()
                    while parent and not hasattr(parent, 'is_valid_position'):
                        parent = parent.parent()

                    if parent and parent.is_valid_position(self.picked_piece, row, col):
                        # Xóa quân khỏi vị trí cũ
                        if self.picked_position:
                            old_row, old_col = self.picked_position
                            self.piece_removed.emit(old_row, old_col)

                        # Đặt quân ở vị trí mới
                        self.piece_placed.emit(row, col, self.picked_piece)

                        # Clear picked state
                        self.picked_piece = None
                        self.picked_position = None
                        self.update_highlights()

                # Nếu có quân từ palette được chọn
                elif self.selected_piece:
                    # Đặt quân từ palette
                    parent = self.parent()
                    while parent and not hasattr(parent, 'is_valid_position'):
                        parent = parent.parent()

                    if parent and parent.is_valid_position(self.selected_piece, row, col):
                        self.piece_placed.emit(row, col, self.selected_piece)

                        # Clear selection sau khi đặt thành công
                        self.selected_piece = None
                        self.update_highlights()

                        # Notify parent để clear palette selection
                        setup_parent = parent
                        if hasattr(setup_parent, 'piece_palette'):
                            setup_parent.piece_palette.clear_selection()

                # Nếu không có gì được chọn, pick up quân tại vị trí này
                else:
                    if self.board_state and self.board_state[row][col]:
                        self.picked_piece = self.board_state[row][col]
                        self.picked_position = (row, col)
                        self.update_highlights()

        # Click ra ngoài bàn cờ - chỉ clear selection
        else:
            # Clear picked state
            if self.picked_piece:
                self.picked_piece = None
                self.picked_position = None
                self.update_highlights()

            # Clear selected piece
            if self.selected_piece:
                self.selected_piece = None
                self.update_highlights()

                # Notify parent để clear palette selection
                parent = self.parent()
                while parent and not hasattr(parent, 'piece_palette'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'piece_palette'):
                    parent.piece_palette.clear_selection()

    def pixel_to_board_coords(self, x, y):
        """Chuyển pixel coords thành board coords dùng hàm chuẩn"""
        board_rect = getattr(self, '_actual_board_rect', self.get_board_rect())

        from ..utils.constants import pixel_to_board_coords
        from PyQt5.QtCore import QPoint

        if not board_rect.contains(QPoint(x, y)):
            return None, None

        result = pixel_to_board_coords(x, y, board_rect)

        if result:
            row, col = result

            # Nếu board bị flip, cần reverse transform tọa độ
            # Lấy flip state từ parent SetupWidget
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, 'board_flipped'):
                parent_widget = parent_widget.parent()

            board_flipped = parent_widget.board_flipped if parent_widget else False

            if board_flipped:
                # Reverse transform: display coords → logical coords
                row = 9 - row
                col = 8 - col

            return row, col
        else:
            return None, None

    def clear_picked_state(self):
        """Clear picked state khi cần thiết"""
        self.picked_piece = None
        self.picked_position = None
        self.update_highlights()

    def update_position(self, game_state):
        """Cập nhật vị trí từ game state"""
        self.board_state = game_state
        self.update()

    def set_board_flipped(self, flipped):
        """Đặt trạng thái flip cho board widget"""
        # Delegate đến parent SetupWidget để cập nhật logic
        parent_widget = self.parent()
        while parent_widget and not isinstance(parent_widget, SetupWidget):
            parent_widget = parent_widget.parent()

        if parent_widget and isinstance(parent_widget, SetupWidget):
            parent_widget.set_board_flipped(flipped)

        # Trigger update để redraw
        self.update()


class PiecePalette(QWidget):
    """Palette chứa các quân cờ để chọn"""

    # Signal
    piece_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.piece_pixmaps = {}
        self.selected_piece = None

        # Quản lý số lượng quân còn lại
        self.piece_counts = {
            # Quân đỏ
            'R': 2, 'N': 2, 'B': 2, 'A': 2, 'K': 1, 'C': 2, 'P': 5,
            # Quân đen
            'r': 2, 'n': 2, 'b': 2, 'a': 2, 'k': 1, 'c': 2, 'p': 5
        }
        self.piece_buttons = {}  # Lưu reference đến buttons

        self.setMinimumWidth(220)  # Đổi từ FixedWidth thành MinimumWidth
        self.load_assets()
        self.init_ui()

    def load_assets(self):
        """Load piece assets"""
        piece_size = QSize(40, 40)  # Smaller for palette
        pieces = ['R', 'N', 'B', 'A', 'K', 'C',
                  'P', 'r', 'n', 'b', 'a', 'k', 'c', 'p']

        for piece in pieces:
            pixmap = image_renderer.render_piece_png(piece, piece_size)
            if pixmap:
                self.piece_pixmaps[piece] = pixmap

    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)

        # Red pieces - hiển thị theo số lượng còn lại
        red_label = QLabel("🔴 Quân Đỏ")
        red_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(red_label)
        self.red_grid = QGridLayout()
        self.red_grid.setSpacing(3)
        layout.addLayout(self.red_grid)

        # Black pieces - hiển thị theo số lượng còn lại
        black_label = QLabel("⚫ Quân Đen")
        black_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(black_label)

        self.black_grid = QGridLayout()
        self.black_grid.setSpacing(3)
        layout.addLayout(self.black_grid)
        layout.addStretch()

        # Khởi tạo với bàn cờ trống (hiển thị tất cả quân)
        self.update_display()

    def update_display(self):
        """Cập nhật hiển thị dựa trên số lượng còn lại"""
        # Xóa các widget cũ
        self.clear_grid(self.red_grid)
        self.clear_grid(self.black_grid)
        self.piece_buttons.clear()

        # Red pieces
        red_pieces = ['R', 'N', 'B', 'A', 'K', 'C', 'P']
        pos = 0
        for piece in red_pieces:
            count = self.piece_counts[piece]
            for i in range(count):
                btn = self.create_piece_button(piece, f"red_{piece}_{i}")
                self.red_grid.addWidget(btn, pos // 4, pos % 4)
                self.piece_buttons[f"red_{piece}_{i}"] = btn
                pos += 1

        # Black pieces
        black_pieces = ['r', 'n', 'b', 'a', 'k', 'c', 'p']
        pos = 0
        for piece in black_pieces:
            count = self.piece_counts[piece]
            for i in range(count):
                btn = self.create_piece_button(piece, f"black_{piece}_{i}")
                self.black_grid.addWidget(btn, pos // 4, pos % 4)
                self.piece_buttons[f"black_{piece}_{i}"] = btn
                pos += 1

    def clear_grid(self, grid_layout):
        """Xóa tất cả widget trong grid"""
        while grid_layout.count():
            child = grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def piece_placed_on_board(self, piece):
        """Gọi khi đặt quân lên bàn cờ - giảm số lượng"""
        if piece in self.piece_counts and self.piece_counts[piece] > 0:
            self.piece_counts[piece] -= 1
            self.update_display()

    def piece_removed_from_board(self, piece):
        """Gọi khi xóa quân khỏi bàn cờ - tăng số lượng"""
        if piece in self.piece_counts:
            self.piece_counts[piece] += 1
            self.update_display()

    def reset_to_standard(self):
        """Reset về vị trí chuẩn - tất cả quân đã được đặt"""
        self.piece_counts = {
            'R': 0, 'N': 0, 'B': 0, 'A': 0, 'K': 0, 'C': 0, 'P': 0,
            'r': 0, 'n': 0, 'b': 0, 'a': 0, 'k': 0, 'c': 0, 'p': 0
        }
        self.update_display()

    def reset_to_empty(self):
        """Reset về bàn cờ trống - tất cả quân có sẵn"""
        self.piece_counts = {
            'R': 2, 'N': 2, 'B': 2, 'A': 2, 'K': 1, 'C': 2, 'P': 5,
            'r': 2, 'n': 2, 'b': 2, 'a': 2, 'k': 1, 'c': 2, 'p': 5
        }
        self.update_display()

    def create_piece_button(self, piece, unique_id=None):
        """Tạo button cho piece"""
        btn = QPushButton()
        btn.setFixedSize(45, 45)  # Nhỏ hơn một chút vì có nhiều quân hơn

        pixmap = self.piece_pixmaps.get(piece)
        if pixmap:
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(QSize(35, 35))

        piece_name = PIECE_NAMES_VN.get(piece, piece)
        btn.setToolTip(f"{piece_name} ({'Đỏ' if piece.isupper() else 'Đen'})")

        btn.clicked.connect(lambda checked, p=piece: self.select_piece(p))
        return btn

    def select_piece(self, piece):
        """Chọn piece"""
        self.selected_piece = piece
        self.piece_selected.emit(piece)

    def clear_selection(self):
        """Xóa selection"""
        self.selected_piece = None
        self.piece_selected.emit("")  # Empty string để xóa
