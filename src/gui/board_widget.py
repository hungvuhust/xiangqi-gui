# -*- coding: utf-8 -*-
"""
Board Widget cho Xiangqi GUI
Widget hiển thị bàn cờ và xử lý tương tác người dùng với SVG support
"""

from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QSize, QRect, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QPixmap, QFont, QColor
from ..utils.constants import *
from ..utils.svg_renderer import image_renderer


class BoardWidget(QWidget):
    """Widget hiển thị bàn cờ tướng với PNG support"""

    # Signals
    piece_moved = pyqtSignal(str, str)  # from_pos, to_pos
    square_clicked = pyqtSignal(str)    # position
    # from_row, from_col, to_row, to_col
    move_made = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__()
        self.board_state = None
        self.selected_square = None
        self.possible_moves = []
        self.current_player = 'red'  # Thêm current_player tracking
        self.is_flipped = False
        self.chinese_coords = True  # False = a-i/0-9, True = 1-9 kiểu Trung Quốc

        # Engine hints
        self.engine_hint = None  # Tuple (from_row, from_col, to_row, to_col)
        # Tuple (from_row, from_col, to_row, to_col) cho ponder move
        self.engine_ponder = None

        # Multi-engine arrows
        self.multi_engine_arrows = {}  # {engine_name: [(from, to, color)]}

        # SVG pixmaps cache
        self.board_pixmap = None
        self.piece_pixmaps = {}

        self.init_ui()
        self.load_png_assets()
        self._init_board_state()

    def init_ui(self):
        """Khởi tạo UI"""
        # Tính kích thước widget dựa trên SVG + space cho coordinates
        coordinate_margin = 5  # Extra space cho coordinates ở 4 phía
        widget_width = int((BOARD_SVG_WIDTH * BOARD_SCALE_FACTOR +
                            2 * BOARD_MARGIN + coordinate_margin))
        widget_height = int((BOARD_SVG_HEIGHT * BOARD_SCALE_FACTOR +
                             2 * BOARD_MARGIN + coordinate_margin))

        self.setMinimumSize(widget_width, widget_height)
        # Cho phép scale lên
        self.setMaximumSize(widget_width * 2, widget_height * 2)
        self.setMouseTracking(True)

    def load_png_assets(self):
        """Load và cache các PNG assets"""
        # Load board PNG với kích thước gốc
        board_size = QSize(BOARD_SVG_WIDTH, BOARD_SVG_HEIGHT)

        # Sử dụng PNG gốc (có text đúng)
        self.board_pixmap = image_renderer.render_board_png(board_size)
        print("🔄 Sử dụng PNG rendering")

        # Nếu không có board_pixmap, fallback về method gốc
        if not self.board_pixmap:
            self.board_pixmap = image_renderer.render_board_png(board_size)
            print("⚠️ Fallback to original PNG rendering")

        if not self.board_pixmap:
            print("❌ Không thể load PNG bàn cờ!")
        else:
            print("✓ Load PNG bàn cờ thành công")

        # Load piece PNGs với kích thước phù hợp
        piece_size = QSize(PIECE_SIZE, PIECE_SIZE)

        pieces = ['R', 'N', 'B', 'A', 'K', 'C', 'P',  # Quân đỏ
                  'r', 'n', 'b', 'a', 'k', 'c', 'p']  # Quân đen

        for piece in pieces:
            pixmap = image_renderer.render_piece_png(piece, piece_size)
            if pixmap:
                self.piece_pixmaps[piece] = pixmap
                print(f"✓ Load PNG quân {piece} ({PIECE_SIZE}px)")
            else:
                print(f"❌ Không thể load PNG cho quân {piece}")

    def _init_board_state(self):
        """Khởi tạo trạng thái bàn cờ từ FEN"""
        board = [[None for _ in range(BOARD_WIDTH)]
                 for _ in range(BOARD_HEIGHT)]

        # Parse FEN để thiết lập vị trí ban đầu
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

    def reset_board(self):
        """Reset bàn cờ về vị trí ban đầu"""
        self._init_board_state()  # Gọi method này sẽ tự động set self.board_state
        self.selected_square = None
        self.possible_moves = []
        self.current_player = 'red'  # Reset về lượt đỏ
        self.update()

    def paintEvent(self, event):
        """Vẽ bàn cờ"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Vẽ nền
        painter.fillRect(self.rect(), QBrush(QColor(BOARD_COLOR)))

        # Vẽ bàn cờ PNG
        self._draw_board_png(painter)

        # Vẽ các quân cờ PNG
        self._draw_pieces_png(painter)

        # Vẽ selection và possible moves
        self._draw_selection(painter)

        # Vẽ engine hint arrow
        self._draw_engine_hint(painter)

        # Vẽ ponder move arrow
        self._draw_engine_ponder(painter)

        # Vẽ multi-engine arrows
        self._draw_multi_engine_arrows(painter)

        # Vẽ coordinates ở 4 phía bàn cờ
        self._draw_coordinates(painter)

        painter.end()

    def _draw_board_png(self, painter):
        """Vẽ bàn cờ từ PNG"""
        if self.board_pixmap:
            board_rect = self._get_board_rect()

            # Tính kích thước target với UI scale factor
            svg_aspect = BOARD_SVG_WIDTH / BOARD_SVG_HEIGHT  # 900/1000 = 0.9

            # Scale down 50% nhưng giữ aspect ratio
            max_width = int(board_rect.width() * UI_SCALE_FACTOR)
            max_height = int(board_rect.height() * UI_SCALE_FACTOR)

            # Fit vào kích thước scaled với đúng aspect ratio
            if max_width / max_height > svg_aspect:
                # Giới hạn bởi height
                target_height = max_height
                target_width = int(target_height * svg_aspect)
            else:
                # Giới hạn bởi width
                target_width = max_width
                target_height = int(target_width / svg_aspect)

            # Center board
            x_offset = (board_rect.width() - target_width) // 2
            y_offset = (board_rect.height() - target_height) // 2

            target_rect = QRect(
                board_rect.left() + x_offset,
                board_rect.top() + y_offset,
                target_width,
                target_height
            )

            # Scale SVG với smooth transformation
            scaled_pixmap = self.board_pixmap.scaled(
                target_rect.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Lưu target_rect để coordinate conversion sử dụng đúng
            self._actual_board_rect = target_rect

            painter.drawPixmap(target_rect, scaled_pixmap)

        else:
            # Fallback - vẽ bàn cờ cơ bản nếu không có SVG
            self._actual_board_rect = self._get_board_rect()
            self._draw_fallback_board(painter)

    def _draw_river_text_overlay(self, painter, board_rect):
        """Vẽ text 楚河漢界 overlay nếu SVG text bị sai"""
        # Font cho chữ Hán
        # 4% chiều cao board
        font_size = max(12, int(board_rect.height() * 0.04))
        font = QFont("SimHei", font_size, QFont.Bold)

        # Fallback fonts
        if not QFont(font).exactMatch():
            for font_family in ["Microsoft YaHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC", "Arial Unicode MS"]:
                font = QFont(font_family, font_size, QFont.Bold)
                if QFont(font).exactMatch():
                    break
            else:
                font = QFont("Arial", font_size, QFont.Bold)

        painter.setFont(font)
        painter.setPen(QPen(QColor(0, 0, 0), 2))

        # Vị trí text ở giữa board (river area)
        river_y = board_rect.top() + int(board_rect.height() * 0.52)

        # "楚河" bên trái
        chu_he_x = board_rect.left() + int(board_rect.width() * 0.22)
        painter.drawText(chu_he_x, river_y, "楚河")

        # "漢界" bên phải
        han_jie_x = board_rect.left() + int(board_rect.width() * 0.65)
        painter.drawText(han_jie_x, river_y, "漢界")

    def _draw_fallback_board(self, painter):
        """Vẽ bàn cờ cơ bản nếu không có SVG"""
        pen = QPen(QColor(GRID_COLOR), 2)
        painter.setPen(pen)

        board_rect = self._get_board_rect()

        # Vẽ đường ngang
        for row in range(BOARD_HEIGHT + 1):
            if row == 5:  # Đường giữa sông
                continue
            y = int(board_rect.top() + row *
                    (board_rect.height() / BOARD_HEIGHT))
            painter.drawLine(board_rect.left(), y, board_rect.right(), y)

        # Vẽ đường dọc
        for col in range(BOARD_WIDTH + 1):
            x = int(board_rect.left() + col *
                    (board_rect.width() / BOARD_WIDTH))
            # Vẽ đường dọc không qua sông ở giữa
            mid_y = int(board_rect.top() + 4.5 *
                        (board_rect.height() / BOARD_HEIGHT))
            painter.drawLine(x, board_rect.top(), x, mid_y)
            painter.drawLine(
                x, int(mid_y + (board_rect.height() / BOARD_HEIGHT)), x, board_rect.bottom())

        # Vẽ cung thành
        self._draw_palace_lines(painter, board_rect)

    def _draw_palace_lines(self, painter, board_rect):
        """Vẽ đường chéo cung thành"""
        pen = QPen(QColor(GRID_COLOR), 2)
        painter.setPen(pen)

        cell_w = board_rect.width() / BOARD_WIDTH
        cell_h = board_rect.height() / BOARD_HEIGHT

        # Cung trên (đen)
        top_left_x = int(board_rect.left() + 3 * cell_w)
        top_right_x = int(board_rect.left() + 5 * cell_w)
        top_top_y = int(board_rect.top())
        top_bottom_y = int(board_rect.top() + 2 * cell_h)

        painter.drawLine(top_left_x, top_top_y, top_right_x, top_bottom_y)
        painter.drawLine(top_right_x, top_top_y, top_left_x, top_bottom_y)

        # Cung dưới (đỏ)
        bottom_left_x = int(board_rect.left() + 3 * cell_w)
        bottom_right_x = int(board_rect.left() + 5 * cell_w)
        bottom_top_y = int(board_rect.top() + 7 * cell_h)
        bottom_bottom_y = int(board_rect.top() + 9 * cell_h)

        painter.drawLine(bottom_left_x, bottom_top_y,
                         bottom_right_x, bottom_bottom_y)
        painter.drawLine(bottom_right_x, bottom_top_y,
                         bottom_left_x, bottom_bottom_y)

    def _draw_pieces_png(self, painter):
        """Vẽ các quân cờ từ PNG"""
        # Sử dụng actual board rect sau khi scale PNG
        board_rect = getattr(self, '_actual_board_rect',
                             self._get_board_rect())

        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.board_state[row][col]
                if piece:
                    self._draw_piece_png(painter, piece, row, col, board_rect)

    def _draw_piece_png(self, painter, piece, row, col, board_rect):
        """Vẽ một quân cờ từ PNG"""
        # Option: Force sử dụng PNG pieces
        FORCE_FALLBACK_PIECES = False  # Set True để dùng custom pieces

        pixmap = self.piece_pixmaps.get(
            piece) if not FORCE_FALLBACK_PIECES else None

        if not pixmap:
            # Fallback - vẽ quân cờ text đẹp hơn
            self._draw_piece_fallback(painter, piece, row, col, board_rect)
            return

        # Xử lý coordinate transformation khi board bị flip
        if self.is_flipped:
            # Flip coordinates
            display_row = 9 - row
            display_col = 8 - col
        else:
            display_row = row
            display_col = col

        # Sử dụng hàm coordinate conversion với coordinates đã flip
        center_x, center_y = board_coords_to_pixel(
            display_row, display_col, board_rect)

        # Scale piece size theo tỷ lệ board
        scale_factor = min(board_rect.width() / BOARD_SVG_WIDTH,
                           board_rect.height() / BOARD_SVG_HEIGHT)
        scaled_piece_size = int(PIECE_SIZE * scale_factor)

        scaled_pixmap = pixmap.scaled(
            scaled_piece_size, scaled_piece_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Tính vị trí top-left để center quân cờ
        x = int(center_x - scaled_piece_size // 2)
        y = int(center_y - scaled_piece_size // 2)

        # Debug piece position cho quân đầu tiên
        if row == 0 and col == 0:
            print(
                f"🔍 Piece {piece} at ({row},{col}): pixel=({center_x:.0f},{center_y:.0f}), size={scaled_piece_size}")

        painter.drawPixmap(x, y, scaled_pixmap)

    def _draw_selection(self, painter):
        """Vẽ highlight cho ô được chọn và possible moves"""
        if self.selected_square is not None:
            # selected_square giờ là tuple (row, col) thay vì string
            row, col = self.selected_square

            # Vẽ corner highlights cho ô được chọn
            board_rect = getattr(self, '_actual_board_rect',
                                 self._get_board_rect())

            # Xử lý coordinate transformation khi board bị flip
            if self.is_flipped:
                display_row = 9 - row
                display_col = 8 - col
            else:
                display_row = row
                display_col = col

            pixel_x, pixel_y = board_coords_to_pixel(
                display_row, display_col, board_rect)

            # Tính kích thước ô
            square_width = board_rect.width() / 8
            square_height = board_rect.height() / 9

            # Vẽ corner highlights thay vì toàn bộ hình vuông
            corner_size = min(square_width, square_height) * \
                0.3  # 30% kích thước ô
            corner_thickness = 4

            painter.setPen(
                QPen(QColor(255, 255, 0), corner_thickness))  # Viền vàng
            painter.setBrush(QBrush())  # Không có fill

            # Tính vị trí góc
            left = pixel_x - square_width/2
            right = pixel_x + square_width/2
            top = pixel_y - square_height/2
            bottom = pixel_y + square_height/2

            # Vẽ 4 góc
            # Góc trên trái
            painter.drawLine(int(left), int(top), int(
                left + corner_size), int(top))
            painter.drawLine(int(left), int(top), int(
                left), int(top + corner_size))

            # Góc trên phải
            painter.drawLine(int(right - corner_size),
                             int(top), int(right), int(top))
            painter.drawLine(int(right), int(top), int(
                right), int(top + corner_size))

            # Góc dưới trái
            painter.drawLine(int(left), int(
                bottom - corner_size), int(left), int(bottom))
            painter.drawLine(int(left), int(bottom), int(
                left + corner_size), int(bottom))

            # Góc dưới phải
            painter.drawLine(int(right), int(
                bottom - corner_size), int(right), int(bottom))
            painter.drawLine(int(right - corner_size),
                             int(bottom), int(right), int(bottom))

        # Vẽ possible moves với dots
        if self.possible_moves:
            board_rect = getattr(self, '_actual_board_rect',
                                 self._get_board_rect())

            for move_row, move_col in self.possible_moves:
                # Xử lý coordinate transformation khi board bị flip
                if self.is_flipped:
                    display_row = 9 - move_row
                    display_col = 8 - move_col
                else:
                    display_row = move_row
                    display_col = move_col

                pixel_x, pixel_y = board_coords_to_pixel(
                    display_row, display_col, board_rect)

                # Kiểm tra có quân địch ở vị trí này không
                target_piece = self.board_state[move_row][move_col]

                if target_piece is not None:
                    # Có quân địch - vẽ chấm tím mờ (capture move)
                    # Viền tím mờ
                    painter.setPen(QPen(QColor(128, 0, 128, 180), 2))
                    # Fill tím mờ hơn
                    painter.setBrush(QBrush(QColor(128, 0, 128, 100)))
                else:
                    # Ô trống - vẽ chấm trắng mờ (normal move)
                    # Viền trắng mờ
                    painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
                    # Fill trắng mờ
                    painter.setBrush(QBrush(QColor(255, 255, 255, 120)))

                # Vẽ chấm tròn 10px
                dot_size = 10
                painter.drawEllipse(
                    int(pixel_x - dot_size/2),
                    int(pixel_y - dot_size/2),
                    dot_size,
                    dot_size
                )

    def _get_board_rect(self):
        """Lấy rectangle của bàn cờ"""
        return self.rect().adjusted(BOARD_MARGIN, BOARD_MARGIN, -BOARD_MARGIN, -BOARD_MARGIN)

    def mousePressEvent(self, event):
        """Xử lý click chuột trên bàn cờ"""
        if event.button() == Qt.LeftButton:
            # Chuyển đổi pixel coordinates thành board coordinates
            row, col = self.pixel_to_board_coords(event.x(), event.y())

            if row is not None and col is not None:
                print(f"🔍 Click at board position ({row},{col})")

                if self.selected_square is None:
                    # Chọn quân cờ
                    piece = self.board_state[row][col]
                    if piece is not None:
                        # Import GameState để kiểm tra
                        from ..core.game_state import GameState
                        temp_game_state = GameState()
                        temp_game_state.board = [r[:]
                                                 for r in self.board_state]
                        # Sử dụng current_player của BoardWidget
                        temp_game_state.current_player = self.current_player

                        # Kiểm tra có phải quân của player hiện tại không
                        if temp_game_state._is_player_piece(piece, temp_game_state.current_player):
                            self.selected_square = (row, col)
                            self.possible_moves = self.get_possible_moves(
                                row, col)
                            print(
                                f"✓ Chọn quân {piece} tại ({row},{col}), có {len(self.possible_moves)} nước đi")
                        else:
                            print(
                                f"❌ Không phải lượt của quân {piece} (lượt hiện tại: {self.current_player})")
                else:
                    # Thực hiện nước đi
                    from_row, from_col = self.selected_square

                    # Import GameState để validate
                    from ..core.game_state import GameState
                    temp_game_state = GameState()
                    temp_game_state.board = [r[:] for r in self.board_state]
                    temp_game_state.current_player = self.current_player

                    if temp_game_state.is_valid_move(from_row, from_col, row, col):
                        # Không modify board_state ở đây, để GameState xử lý
                        piece = self.board_state[from_row][from_col]
                        captured_piece = self.board_state[row][col]

                        print(
                            f"✓ Validation OK: {piece} từ ({from_row},{from_col}) đến ({row},{col})")
                        if captured_piece:
                            print(f"✓ Sẽ bắt quân {captured_piece}")

                        # Emit signal cho main window để GameState xử lý thực sự
                        print(
                            f"🚨 DEBUG: About to emit move_made signal - ({from_row},{from_col}) → ({row},{col})")
                        print(
                            f"🚨 DEBUG: BoardWidget current_player before emit: {self.current_player}")
                        self.move_made.emit(from_row, from_col, row, col)
                        print(f"🚨 DEBUG: move_made signal emitted successfully")

                        # Clear selection
                        self.selected_square = None
                        self.possible_moves = []
                    else:
                        print(
                            f"❌ Nước đi không hợp lệ từ ({from_row},{from_col}) đến ({row},{col})")
                        print(
                            f"🚨 DEBUG: BoardWidget validation failed. current_player: {self.current_player}")

                        # Nếu click vào quân khác của mình, chuyển selection
                        piece = self.board_state[row][col]
                        if piece is not None and temp_game_state._is_player_piece(piece, temp_game_state.current_player):
                            self.selected_square = (row, col)
                            self.possible_moves = self.get_possible_moves(
                                row, col)
                            print(
                                f"🔄 Chuyển chọn sang quân {piece} tại ({row},{col})")
                        else:
                            # Clear selection
                            self.selected_square = None
                            self.possible_moves = []

                self.update()  # Redraw board

    def pixel_to_board_coords(self, pixel_x, pixel_y):
        """Chuyển đổi tọa độ pixel thành coordinates bàn cờ"""
        # Sử dụng actual board rect sau khi scale SVG
        board_rect = getattr(self, '_actual_board_rect',
                             self._get_board_rect())

        if not board_rect.contains(QPoint(pixel_x, pixel_y)):
            return None, None

        result = pixel_to_board_coords(pixel_x, pixel_y, board_rect)

        if result:
            display_row, display_col = result

            # Xử lý coordinate transformation khi board bị flip
            if self.is_flipped:
                # Chuyển từ display coordinates về logic coordinates
                actual_row = 9 - display_row
                actual_col = 8 - display_col
            else:
                actual_row = display_row
                actual_col = display_col

            return actual_row, actual_col
        else:
            return None

    def _coords_to_pos(self, row, col):
        """Chuyển đổi tọa độ thành position string"""
        return f"{chr(ord('a') + col)}{row}"

    def _pos_to_coords(self, pos):
        """
        Chuyển đổi position string thành tọa độ board

        Args:
            pos: Position string như "e2" (UCI format)

        Returns:
            tuple: (row, col) trong board coordinates
        """
        if len(pos) != 2:
            return None

        try:
            # File: a-i (cột 0-8)
            col = ord(pos[0]) - ord('a')

            # Rank: 0-9 trong UCI cần đảo ngược thành board coordinates
            # UCI rank 0 (đỏ) = board row 9
            # UCI rank 9 (đen) = board row 0
            rank = int(pos[1])
            row = 9 - rank

            # Validate coordinates
            if 0 <= row < BOARD_HEIGHT and 0 <= col < BOARD_WIDTH:
                return row, col
            else:
                print(f"❌ Invalid coordinates for {pos}: row={row}, col={col}")
                return None

        except (ValueError, IndexError) as e:
            print(f"❌ Error parsing position {pos}: {e}")
            return None

    def get_possible_moves(self, row, col):
        """
        Lấy danh sách các nước đi có thể từ vị trí (row, col)

        Args:
            row: Row index
            col: Column index

        Returns:
            list: List of possible move positions (tuples of (row, col))
        """
        possible_moves = []
        piece = self.board_state[row][col]

        if piece is None:
            return possible_moves

        # Import GameState để validate moves
        from ..core.game_state import GameState
        temp_game_state = GameState()
        temp_game_state.board = [r[:] for r in self.board_state]
        temp_game_state.current_player = self.current_player

        # Kiểm tra tất cả các ô trên bàn cờ
        for to_row in range(10):
            for to_col in range(9):
                if temp_game_state.is_valid_move(row, col, to_row, to_col):
                    possible_moves.append((to_row, to_col))

        return possible_moves

    def undo_last_move(self):
        """Hoàn tác nước đi cuối"""
        # TODO: Implement undo logic
        self.update()

    def reload_png_assets(self):
        """Reload lại các PNG assets"""
        image_renderer.clear_cache()
        self.load_png_assets()
        self.update()

    def _draw_pieces_svg(self, painter):
        """Vẽ các quân cờ từ SVG"""
        # Sử dụng actual board rect sau khi scale SVG
        board_rect = getattr(self, '_actual_board_rect',
                             self._get_board_rect())

        for row in range(BOARD_HEIGHT):
            for col in range(BOARD_WIDTH):
                piece = self.board_state[row][col]
                if piece:
                    self._draw_piece_svg(painter, piece, row, col, board_rect)

    def _draw_piece_svg(self, painter, piece, row, col, board_rect):
        """Vẽ một quân cờ từ PNG"""
        # Option: Force sử dụng PNG pieces
        FORCE_FALLBACK_PIECES = False  # Set True để dùng custom pieces

        pixmap = self.piece_pixmaps.get(
            piece) if not FORCE_FALLBACK_PIECES else None

        if not pixmap:
            # Fallback - vẽ quân cờ text đẹp hơn
            self._draw_piece_fallback(painter, piece, row, col, board_rect)
            return

        # Sử dụng hàm coordinate conversion mới
        center_x, center_y = board_coords_to_pixel(row, col, board_rect)

        # Scale piece size theo tỷ lệ board
        scale_factor = min(board_rect.width() / BOARD_SVG_WIDTH,
                           board_rect.height() / BOARD_SVG_HEIGHT)
        scaled_piece_size = int(PIECE_SIZE * scale_factor)

        scaled_pixmap = pixmap.scaled(
            scaled_piece_size, scaled_piece_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Tính vị trí top-left để center quân cờ
        x = int(center_x - scaled_piece_size // 2)
        y = int(center_y - scaled_piece_size // 2)

        # Debug piece position cho quân đầu tiên
        if row == 0 and col == 0:
            print(
                f"🔍 Piece {piece} at ({row},{col}): pixel=({center_x:.0f},{center_y:.0f}), size={scaled_piece_size}")

        painter.drawPixmap(x, y, scaled_pixmap)

    def _draw_piece_fallback(self, painter, piece, row, col, board_rect):
        """Vẽ quân cờ fallback dạng text với background đẹp hơn"""
        center_x, center_y = board_coords_to_pixel(row, col, board_rect)

        # Scale piece size theo tỷ lệ board
        scale_factor = min(board_rect.width() / BOARD_SVG_WIDTH,
                           board_rect.height() / BOARD_SVG_HEIGHT)
        scaled_piece_size = int(PIECE_SIZE * scale_factor)
        radius = scaled_piece_size // 2

        # Màu quân cờ
        if piece.isupper():  # Quân đỏ
            circle_color = QColor("#FFD700")  # Gold
            border_color = QColor("#DC143C")  # Crimson
            text_color = QColor("#8B0000")    # Dark red
        else:  # Quân đen
            circle_color = QColor("#F5F5DC")  # Beige
            border_color = QColor("#2F4F4F")  # Dark slate gray
            text_color = QColor("#000000")    # Black

        # Vẽ background circle
        painter.setBrush(QBrush(circle_color))
        painter.setPen(QPen(border_color, 3))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius),
                            scaled_piece_size, scaled_piece_size)

        # Vẽ ký tự quân cờ
        font_size = max(8, int(radius * 0.8))
        font = QFont("SimHei", font_size, QFont.Bold)

        # Fallback font
        if not font.exactMatch():
            font = QFont("Arial Unicode MS", font_size, QFont.Bold)
            if not font.exactMatch():
                font = QFont("Arial", font_size, QFont.Bold)

        painter.setFont(font)
        painter.setPen(QPen(text_color, 2))

        piece_text = PIECE_NAMES_VN.get(piece, piece)

        # Center text trong circle
        text_rect = painter.fontMetrics().boundingRect(piece_text)
        text_x = int(center_x - text_rect.width() / 2)
        text_y = int(center_y + text_rect.height() / 3)

        painter.drawText(text_x, text_y, piece_text)

    def load_fen_position(self, fen_string):
        """
        Load position từ FEN string

        Args:
            fen_string: FEN notation

        Returns:
            bool: True nếu load thành công
        """
        from ..core.game_state import GameState

        # Tạo temporary game state để parse FEN
        temp_game_state = GameState()
        if temp_game_state.load_from_fen(fen_string):
            # Update board state
            self.board_state = temp_game_state.board

            # Clear selection
            self.selected_square = None
            self.possible_moves = []

            # Redraw
            self.update()
            return True
        else:
            print("❌ Không thể load FEN")
            return False

    def get_current_fen(self):
        """
        Lấy FEN của position hiện tại

        Returns:
            str: FEN notation
        """
        from ..core.game_state import GameState

        # Tạo game state từ board hiện tại
        game_state = GameState()
        game_state.board = [row[:] for row in self.board_state]  # Copy board

        return game_state.to_fen()

    def set_current_player(self, player):
        """
        Cập nhật player hiện tại

        Args:
            player: 'red' hoặc 'black'
        """
        self.current_player = player
        print(f"🔄 BoardWidget: Chuyển lượt sang {player}")

    def set_engine_hint(self, hint_move, ponder_move=None):
        """
        Cập nhật gợi ý từ engine

        Args:
            hint_move: String move notation (e.g., "c2d2") hoặc None để clear
            ponder_move: String ponder move notation (e.g., "g6g5") hoặc None
        """
        if hint_move and len(hint_move) == 4:
            # Parse UCI move notation: "c2d2" means c2 -> d2
            # UCI format: file (a-i) + rank (0-9)
            # Trong cờ tướng: rank 0 = phía đỏ (hàng 9 trong board), rank 9 = phía đen (hàng 0 trong board)
            try:
                # From position
                from_file = hint_move[0]  # 'a' đến 'i' (cột)
                from_rank = hint_move[1]  # '0' đến '9' (hàng)

                # To position
                to_file = hint_move[2]    # 'a' đến 'i' (cột)
                to_rank = hint_move[3]    # '0' đến '9' (hàng)

                # Chuyển đổi sang board coordinates (0-based)
                # File: a=0, b=1, c=2, ..., i=8
                from_col = ord(from_file) - ord('a')
                to_col = ord(to_file) - ord('a')

                # Rank: engine 0-9 cần đảo ngược thành board 9-0
                # Engine rank 0 (đỏ) = board row 9
                # Engine rank 9 (đen) = board row 0
                from_row = 9 - int(from_rank)
                to_row = 9 - int(to_rank)

                # Validate coordinates
                if (0 <= from_row < BOARD_HEIGHT and 0 <= from_col < BOARD_WIDTH and
                        0 <= to_row < BOARD_HEIGHT and 0 <= to_col < BOARD_WIDTH):

                    self.engine_hint = (from_row, from_col, to_row, to_col)
                    print(f"🤖 Engine gợi ý: {hint_move}")
                    print(
                        f"   Engine coords: ({from_file}{from_rank}) -> ({to_file}{to_rank})")
                    print(
                        f"   Board coords: ({from_row},{from_col}) -> ({to_row},{to_col})")
                else:
                    print(f"❌ Tọa độ engine hint không hợp lệ: {hint_move}")
                    self.engine_hint = None

            except (ValueError, IndexError) as e:
                print(f"❌ Lỗi parse engine move {hint_move}: {e}")
                self.engine_hint = None
        else:
            self.engine_hint = None

        # Parse ponder move
        if ponder_move and len(ponder_move) == 4:
            try:
                # From position
                from_file = ponder_move[0]
                from_rank = ponder_move[1]
                # To position
                to_file = ponder_move[2]
                to_rank = ponder_move[3]

                # Chuyển đổi sang board coordinates
                from_col = ord(from_file) - ord('a')
                to_col = ord(to_file) - ord('a')
                from_row = 9 - int(from_rank)
                to_row = 9 - int(to_rank)

                # Validate coordinates
                if (0 <= from_row < BOARD_HEIGHT and 0 <= from_col < BOARD_WIDTH and
                        0 <= to_row < BOARD_HEIGHT and 0 <= to_col < BOARD_WIDTH):

                    self.engine_ponder = (from_row, from_col, to_row, to_col)
                    print(f"🤖 Engine ponder: {ponder_move}")
                    print(
                        f"   Ponder coords: ({from_row},{from_col}) -> ({to_row},{to_col})")
                else:
                    print(f"❌ Tọa độ ponder không hợp lệ: {ponder_move}")
                    self.engine_ponder = None

            except (ValueError, IndexError) as e:
                print(f"❌ Lỗi parse ponder move {ponder_move}: {e}")
                self.engine_ponder = None
        else:
            self.engine_ponder = None

        self.update()  # Redraw để hiển thị hint

    def clear_engine_hint(self):
        """Xóa gợi ý engine"""
        self.engine_hint = None
        self.engine_ponder = None
        self.update()

    def _draw_engine_hint(self, painter):
        """Vẽ arrow để hiển thị gợi ý từ engine"""
        if self.engine_hint:
            from_row, from_col, to_row, to_col = self.engine_hint

            board_rect = getattr(self, '_actual_board_rect',
                                 self._get_board_rect())

            # Xử lý coordinate transformation khi board bị flip
            if self.is_flipped:
                display_from_row = 9 - from_row
                display_from_col = 8 - from_col
                display_to_row = 9 - to_row
                display_to_col = 8 - to_col
            else:
                display_from_row = from_row
                display_from_col = from_col
                display_to_row = to_row
                display_to_col = to_col

            from_x, from_y = board_coords_to_pixel(
                display_from_row, display_from_col, board_rect)
            to_x, to_y = board_coords_to_pixel(
                display_to_row, display_to_col, board_rect)

            # Debug info
            print(
                f"🏹 Vẽ mũi tên hint: ({from_row},{from_col}) -> ({to_row},{to_col})")
            print(
                f"   Pixel: ({from_x:.0f},{from_y:.0f}) -> ({to_x:.0f},{to_y:.0f})")
            print(f"   Board rect: {board_rect}")

            # Chọn màu dựa trên lượt chơi hiện tại với transparency
            if self.current_player == 'red':
                # Lượt đỏ -> màu tím với alpha 120 (47% opacity)
                arrow_color = QColor(128, 0, 128, 120)  # Purple with alpha
            else:
                # Lượt đen -> màu xanh với alpha 120 (47% opacity)
                arrow_color = QColor(0, 100, 255, 120)  # Blue with alpha

            # Vẽ mũi tên với màu trong suốt theo lượt chơi
            painter.setPen(QPen(arrow_color, 5))  # Độ dày 5px
            painter.setBrush(QBrush(arrow_color))

            # Tính toán vector và độ dài
            import math
            dx = to_x - from_x
            dy = to_y - from_y
            length = math.sqrt(dx*dx + dy*dy)

            if length > 0:
                # Normalize vector
                dx_norm = dx / length
                dy_norm = dy / length

                # Kích thước đầu mũi tên
                arrow_length = 15  # Độ dài đầu mũi tên
                arrow_width = 8   # Độ rộng đầu mũi tên

                start_x = from_x + dx_norm
                start_y = from_y + dy_norm
                end_x = to_x - dx_norm
                end_y = to_y - dy_norm

                # Vẽ thân mũi tên
                painter.drawLine(int(start_x), int(
                    start_y), int(end_x), int(end_y))

                # Tính điểm đầu mũi tên
                arrow_tip_x = end_x
                arrow_tip_y = end_y

                # Tính 2 điểm cánh mũi tên
                base_x = end_x - arrow_length * dx_norm
                base_y = end_y - arrow_length * dy_norm

                # Vector vuông góc
                perp_x = -dy_norm * arrow_width
                perp_y = dx_norm * arrow_width

                wing1_x = base_x + perp_x
                wing1_y = base_y + perp_y
                wing2_x = base_x - perp_x
                wing2_y = base_y - perp_y

                # Vẽ đầu mũi tên (tam giác)
                from PyQt5.QtGui import QPolygonF
                from PyQt5.QtCore import QPointF

                arrow_head = QPolygonF([
                    QPointF(arrow_tip_x, arrow_tip_y),
                    QPointF(wing1_x, wing1_y),
                    QPointF(wing2_x, wing2_y)
                ])

                painter.drawPolygon(arrow_head)

                # Vẽ circle nhỏ ở điểm bắt đầu để đánh dấu
                circle_radius = 6
                painter.setPen(QPen(arrow_color, 2))
                painter.drawEllipse(int(start_x - circle_radius), int(start_y - circle_radius),
                                    circle_radius * 2, circle_radius * 2)

    def _draw_engine_ponder(self, painter):
        """Vẽ arrow để hiển thị ponder move từ engine"""
        if self.engine_ponder:
            from_row, from_col, to_row, to_col = self.engine_ponder

            board_rect = getattr(self, '_actual_board_rect',
                                 self._get_board_rect())

            # Xử lý coordinate transformation khi board bị flip
            if self.is_flipped:
                display_from_row = 9 - from_row
                display_from_col = 8 - from_col
                display_to_row = 9 - to_row
                display_to_col = 8 - to_col
            else:
                display_from_row = from_row
                display_from_col = from_col
                display_to_row = to_row
                display_to_col = to_col

            from_x, from_y = board_coords_to_pixel(
                display_from_row, display_from_col, board_rect)
            to_x, to_y = board_coords_to_pixel(
                display_to_row, display_to_col, board_rect)

            # Debug info
            print(
                f"🏹 Vẽ mũi tên ponder: ({from_row},{from_col}) -> ({to_row},{to_col})")

            # Chọn màu cho ponder move (đối phương của current_player)
            if self.current_player == 'red':
                # Lượt đỏ -> ponder cho đen -> màu xanh mờ hơn
                ponder_color = QColor(0, 100, 255, 80)  # Blue with lower alpha
            else:
                # Lượt đen -> ponder cho đỏ -> màu tím mờ hơn
                # Purple with lower alpha
                ponder_color = QColor(128, 0, 128, 80)

            # Vẽ mũi tên ponder với màu mờ hơn và đường đứt nét
            # Đường đứt nét, mỏng hơn
            painter.setPen(QPen(ponder_color, 3, Qt.DashLine))
            painter.setBrush(QBrush(ponder_color))

            # Tính toán vector và độ dài
            import math
            dx = to_x - from_x
            dy = to_y - from_y
            length = math.sqrt(dx*dx + dy*dy)

            if length > 0:
                # Normalize vector
                dx_norm = dx / length
                dy_norm = dy / length

                # Kích thước đầu mũi tên nhỏ hơn cho ponder
                arrow_length = 12  # Nhỏ hơn bestmove
                arrow_width = 6   # Nhỏ hơn bestmove

                start_x = from_x + dx_norm * 8  # Offset nhiều hơn để tránh overlap
                start_y = from_y + dy_norm * 8
                end_x = to_x - dx_norm * 8
                end_y = to_y - dy_norm * 8

                # Vẽ thân mũi tên với đường đứt nét
                painter.drawLine(int(start_x), int(
                    start_y), int(end_x), int(end_y))

                # Tính điểm đầu mũi tên
                arrow_tip_x = end_x
                arrow_tip_y = end_y

                # Tính 2 điểm cánh mũi tên
                base_x = end_x - arrow_length * dx_norm
                base_y = end_y - arrow_length * dy_norm

                # Vector vuông góc
                perp_x = -dy_norm * arrow_width
                perp_y = dx_norm * arrow_width

                wing1_x = base_x + perp_x
                wing1_y = base_y + perp_y
                wing2_x = base_x - perp_x
                wing2_y = base_y - perp_y

                # Vẽ đầu mũi tên (tam giác) với solid line
                painter.setPen(QPen(ponder_color, 2))  # Solid cho triangle
                from PyQt5.QtGui import QPolygonF
                from PyQt5.QtCore import QPointF

                arrow_head = QPolygonF([
                    QPointF(arrow_tip_x, arrow_tip_y),
                    QPointF(wing1_x, wing1_y),
                    QPointF(wing2_x, wing2_y)
                ])

                painter.drawPolygon(arrow_head)

                # Vẽ square nhỏ ở điểm bắt đầu để phân biệt với circle của bestmove
                square_size = 8
                painter.setPen(QPen(ponder_color, 2))
                painter.drawRect(int(start_x - square_size/2), int(start_y - square_size/2),
                                 square_size, square_size)

    def flip_board(self):
        """Lật bàn cờ để xem từ góc nhìn đối phương"""
        self.is_flipped = not self.is_flipped
        self.update()  # Redraw board với flip state mới
        print(f"🔄 Board flipped: {self.is_flipped}")

    def toggle_coordinate_style(self):
        """Toggle giữa tọa độ quốc tế (a-i/0-9) và kiểu Trung Quốc (1-9)"""
        self.chinese_coords = not self.chinese_coords
        self.update()  # Redraw coordinates với style mới
        print(
            f"🔄 Coordinate style: {'Chinese (1-9)' if self.chinese_coords else 'International (a-i/0-9)'}")

    def _draw_coordinates(self, painter):
        """Vẽ tọa độ (coordinates) ở 4 phía bàn cờ"""
        board_rect = getattr(self, '_actual_board_rect',
                             self._get_board_rect())

        # Thiết lập font cho coordinates
        font_size = max(
            10, int(min(board_rect.width(), board_rect.height()) * 0.02))
        font = QFont("Arial", font_size, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#8B4513"), 2))  # Màu nâu đậm

        if self.chinese_coords:
            # Kiểu Trung Quốc: chỉ hiển thị số cột 1-9 từ phải qua trái (theo từng phía quân)
            self._draw_chinese_coordinates(painter, board_rect)
        else:
            # Kiểu quốc tế: hiển thị a-i và 0-9
            self._draw_international_coordinates(painter, board_rect)

    def _draw_international_coordinates(self, painter, board_rect):
        """Vẽ tọa độ kiểu quốc tế (a-i, 0-9)"""
        # Tọa độ cột (a-i)
        columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']

        # Tọa độ hàng (0-9 hoặc flip tùy theo is_flipped)
        if self.is_flipped:
            # Khi flip: hiển thị từ góc nhìn đen (0 ở trên, 9 ở dưới)
            rows = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        else:
            # Bình thường: từ góc nhìn đỏ (9 ở trên, 0 ở dưới)
            rows = ['9', '8', '7', '6', '5', '4', '3', '2', '1', '0']

        # Vẽ tọa độ cột ở trên và dưới
        for col_idx, col_char in enumerate(columns):
            if self.is_flipped:
                # Khi flip: đảo ngược thứ tự cột
                display_col = 8 - col_idx
            else:
                display_col = col_idx

            # Tính vị trí pixel cho cột
            pixel_x, _ = board_coords_to_pixel(0, display_col, board_rect)

            # Vẽ ở trên bàn cờ
            top_y = board_rect.top() - 15
            painter.drawText(int(pixel_x - 5), int(top_y), col_char)

            # Vẽ ở dưới bàn cờ
            bottom_y = board_rect.bottom() + 20
            painter.drawText(int(pixel_x - 5), int(bottom_y), col_char)

        # Vẽ tọa độ hàng ở trái và phải
        for row_idx, row_char in enumerate(rows):
            # Tính vị trí pixel cho hàng
            _, pixel_y = board_coords_to_pixel(row_idx, 0, board_rect)

            # Vẽ ở trái bàn cờ
            left_x = board_rect.left() - 20
            painter.drawText(int(left_x), int(pixel_y + 5), row_char)

            # Vẽ ở phải bàn cờ
            right_x = board_rect.right() + 10
            painter.drawText(int(right_x), int(pixel_y + 5), row_char)

    def _draw_chinese_coordinates(self, painter, board_rect):
        """Vẽ tọa độ kiểu Trung Quốc (1-9 từ phải qua trái theo từng phía quân)"""
        # Chỉ vẽ số cột, không vẽ số hàng

        # Số cột từ 1-9 (từ phải qua trái của từng phía)
        chinese_cols = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

        # Vẽ tọa độ cột ở trên (cho quân đen) và dưới (cho quân đỏ)
        for col_idx, col_num in enumerate(chinese_cols):
            if self.is_flipped:
                # Khi flip:
                # - Trên (quân đỏ): 1-9 từ phải qua trái
                # - Dưới (quân đen): 1-9 từ phải qua trái
                display_col_top = 8 - col_idx  # Trên: 1-9 từ phải qua trái
                display_col_bottom = col_idx  # Dưới: 1-9 từ trái qua phải
            else:
                # Bình thường:
                # - Trên (quân đen): 1-9 từ phải qua trái
                # - Dưới (quân đỏ): 1-9 từ phải qua trái
                display_col_top = col_idx  # Trên: 1-9 từ trái qua phải
                display_col_bottom = 8 - col_idx  # Dưới: 1-9 từ phải qua trái

            # Vẽ ở trên bàn cờ
            pixel_x_top, _ = board_coords_to_pixel(
                0, display_col_top, board_rect)
            top_y = board_rect.top() - 15
            painter.drawText(int(pixel_x_top - 5), int(top_y), col_num)

            # Vẽ ở dưới bàn cờ
            pixel_x_bottom, _ = board_coords_to_pixel(
                0, display_col_bottom, board_rect)
            bottom_y = board_rect.bottom() + 20
            painter.drawText(int(pixel_x_bottom - 5), int(bottom_y), col_num)

    def set_multi_engine_arrows(self, arrows_data: dict):
        """
        Đặt mũi tên từ nhiều engine với style mới

        Args:
            arrows_data: {engine_name: [{'from': pos, 'to': pos, 'color': str, 'style': str, 'opacity': float, ...}]}
        """
        self.multi_engine_arrows = arrows_data.copy()
        self.update()

    def clear_multi_engine_arrows(self):
        """Xóa tất cả mũi tên multi-engine"""
        self.multi_engine_arrows.clear()
        self.update()

    def _draw_multi_engine_arrows(self, painter):
        """Vẽ mũi tên từ nhiều engine với màu và style khác nhau"""
        if not self.multi_engine_arrows:
            return

        board_rect = getattr(self, '_actual_board_rect',
                             self._get_board_rect())

        # Color mapping với alpha channel
        color_map = {
            'red': QColor(255, 0, 0),
            'blue': QColor(0, 0, 255),
            'green': QColor(0, 200, 0),
            'orange': QColor(255, 165, 0),
            'purple': QColor(128, 0, 128),
            'brown': QColor(165, 42, 42),
            'cyan': QColor(0, 255, 255),
            'magenta': QColor(255, 0, 255)
        }

        offset_step = 1  # Offset mỗi arrow để tránh chồng lấp
        engine_index = 0

        for engine_name, arrows in self.multi_engine_arrows.items():
            for arrow_info in arrows:
                if isinstance(arrow_info, dict):
                    # New format: dict with style info
                    from_pos = arrow_info.get('from', '')
                    to_pos = arrow_info.get('to', '')
                    color_name = arrow_info.get('color', 'gray')
                    style = arrow_info.get('style', 'solid')
                    opacity = arrow_info.get('opacity', 1.0)
                    is_current_turn = arrow_info.get('is_current_turn', True)

                    # Parse positions
                    from_coords = self._pos_to_coords(from_pos)
                    to_coords = self._pos_to_coords(to_pos)

                    if from_coords and to_coords:
                        from_row, from_col = from_coords
                        to_row, to_col = to_coords

                        # Apply coordinate flipping if needed
                        if self.is_flipped:
                            from_row = BOARD_HEIGHT - 1 - from_row
                            from_col = BOARD_WIDTH - 1 - from_col
                            to_row = BOARD_HEIGHT - 1 - to_row
                            to_col = BOARD_WIDTH - 1 - to_col

                        # Calculate pixel positions với offset
                        from_x, from_y = board_coords_to_pixel(
                            from_row, from_col, board_rect)
                        to_x, to_y = board_coords_to_pixel(
                            to_row, to_col, board_rect)

                        # Apply offset để tránh overlap
                        offset_x = offset_step * engine_index * 0.5
                        offset_y = offset_step * engine_index * 0.3

                        from_x += offset_x
                        from_y += offset_y
                        to_x += offset_x
                        to_y += offset_y

                        # Get base color và apply opacity
                        base_color = color_map.get(
                            color_name, QColor(128, 128, 128))
                        alpha = int(255 * opacity)
                        arrow_color = QColor(
                            base_color.red(), base_color.green(), base_color.blue(), alpha)

                        # Create label cho engine
                        label = engine_name
                        if not is_current_turn:
                            # Đánh dấu gợi ý cho phe đối phương
                            label += " (phụ)"

                        # Draw arrow với style tương ứng
                        self._draw_styled_multi_arrow(
                            painter, from_x, from_y, to_x, to_y,
                            arrow_color, style, label, is_current_turn)

                elif isinstance(arrow_info, (list, tuple)) and len(arrow_info) >= 3:
                    # Old format compatibility: (from_pos, to_pos, color)
                    from_pos, to_pos, color_name = arrow_info[:3]

                    from_coords = self._pos_to_coords(from_pos)
                    to_coords = self._pos_to_coords(to_pos)

                    if from_coords and to_coords:
                        from_row, from_col = from_coords
                        to_row, to_col = to_coords

                        if self.is_flipped:
                            from_row = BOARD_HEIGHT - 1 - from_row
                            from_col = BOARD_WIDTH - 1 - from_col
                            to_row = BOARD_HEIGHT - 1 - to_row
                            to_col = BOARD_WIDTH - 1 - to_col

                        from_x, from_y = board_coords_to_pixel(
                            from_row, from_col, board_rect)
                        to_x, to_y = board_coords_to_pixel(
                            to_row, to_col, board_rect)

                        offset_x = offset_step * engine_index * 0.5
                        offset_y = offset_step * engine_index * 0.3

                        from_x += offset_x
                        from_y += offset_y
                        to_x += offset_x
                        to_y += offset_y

                        arrow_color = color_map.get(
                            color_name, QColor(128, 128, 128, 180))

                        self._draw_styled_multi_arrow(
                            painter, from_x, from_y, to_x, to_y,
                            arrow_color, 'solid', engine_name, True)

            engine_index += 1

    def _draw_styled_multi_arrow(self, painter, from_x, from_y, to_x, to_y, color, style='solid', label=None, is_current_turn=True):
        """Vẽ mũi tên multi-engine với style và opacity khác nhau"""
        # Set pen với style tương ứng
        pen_width = 3 if is_current_turn else 2

        if style == 'dashed':
            pen = QPen(color, pen_width, Qt.DashLine)
        else:
            pen = QPen(color, pen_width, Qt.SolidLine)

        painter.setPen(pen)
        painter.setBrush(QBrush(color))

        # Tính vector direction
        import math
        dx = to_x - from_x
        dy = to_y - from_y
        length = math.sqrt(dx*dx + dy*dy)

        if length < 10:  # Quá ngắn
            return

        # Normalize
        dx /= length
        dy /= length

        # Shorten arrow để không vẽ lên quân cờ
        from_x += dx
        from_y += dy
        to_x -= dx
        to_y -= dy

        # Vẽ shaft
        painter.drawLine(int(from_x), int(from_y), int(to_x), int(to_y))

        # Vẽ arrowhead
        arrow_length = 12 if is_current_turn else 10
        arrow_angle = 0.5

        # Arrowhead points
        ax1 = to_x - arrow_length * \
            (dx * math.cos(arrow_angle) - dy * math.sin(arrow_angle))
        ay1 = to_y - arrow_length * \
            (dy * math.cos(arrow_angle) + dx * math.sin(arrow_angle))

        ax2 = to_x - arrow_length * \
            (dx * math.cos(-arrow_angle) - dy * math.sin(-arrow_angle))
        ay2 = to_y - arrow_length * \
            (dy * math.cos(-arrow_angle) + dx * math.sin(-arrow_angle))

        # Draw arrowhead
        points = [QPoint(int(to_x), int(to_y)),
                  QPoint(int(ax1), int(ay1)),
                  QPoint(int(ax2), int(ay2))]

        from PyQt5.QtGui import QPolygon
        painter.drawPolygon(QPolygon(points))

        # Draw label nếu có
        if label and len(label) > 0:
            # Vị trí label ở giữa arrow
            label_x = (from_x + to_x) / 2
            label_y = (from_y + to_y) / 2 - 12

            # Short label (first few characters)
            short_label = label[:8] if len(label) > 8 else label

            font_size = 7 if is_current_turn else 6
            font = QFont("Arial", font_size, QFont.Bold)
            painter.setFont(font)

            # Text background với alpha
            text_rect = painter.fontMetrics().boundingRect(short_label)
            text_rect.moveCenter(QPoint(int(label_x), int(label_y)))
            text_rect.adjust(-2, -1, 2, 1)

            bg_alpha = 220 if is_current_turn else 180
            painter.fillRect(text_rect, QBrush(
                QColor(255, 255, 255, bg_alpha)))

            # Text color
            text_color = QColor(0, 0, 0, 255 if is_current_turn else 180)
            painter.setPen(QPen(text_color))
            painter.drawText(text_rect, Qt.AlignCenter, short_label)
