# -*- coding: utf-8 -*-
"""
Constants cho Xiangqi GUI
Định nghĩa các hằng số về bàn cờ, quân cờ, và giao diện
"""

import os

# Kích thước bàn cờ
BOARD_WIDTH = 9   # 9 cột
BOARD_HEIGHT = 10  # 10 hàng

# Kích thước giao diện (pixel) - dựa trên SVG gốc 900x1000
BOARD_SVG_WIDTH = 900  # Revert về 900
BOARD_SVG_HEIGHT = 1000  # Revert về 1000
BOARD_SCALE_FACTOR = 0.7

# UI scaling factor (để scale down cho canvas nhỏ như trong ảnh tham khảo)
UI_SCALE_FACTOR = 0.75
# Piece size (tăng lên để không quá nhỏ)
PIECE_SIZE = int(120 * UI_SCALE_FACTOR)  # 120 * 0.5 = 60px thay vì 40px

# UI constants
BOARD_MARGIN = int(5 * UI_SCALE_FACTOR)

# Offset của board thực tế trong SVG (margin trong SVG)
BOARD_OFFSET_X = 50  # Vị trí bắt đầu board thực tế trong SVG
BOARD_OFFSET_Y = 50  # Vị trí bắt đầu board thực tế trong SVG
BOARD_ACTUAL_WIDTH = 800  # Kích thước thực tế board trong SVG
BOARD_ACTUAL_HEIGHT = 900  # Kích thước thực tế board trong SVG

# Màu sắc
BOARD_COLOR = "#DDDDDD"     # Màu nền bàn cờ (wheat)
GRID_COLOR = "#8B4513"      # Màu lưới (saddle brown)
RED_PIECE_COLOR = "#DC143C"  # Màu quân đỏ
BLACK_PIECE_COLOR = "#2F4F4F"  # Màu quân đen
HIGHLIGHT_COLOR = "#FFD700"  # Màu highlight nước đi (gold)
SELECTED_COLOR = "#7E1891"   # Màu quân được chọn (tomato)

# Vị trí ban đầu các quân cờ (theo ký hiệu FEN)
INITIAL_POSITION = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"

# Tên các quân cờ
PIECE_NAMES = {
    'r': 'chariot',    # Xe (đen)
    'n': 'horse',      # Mã (đen)
    'b': 'elephant',   # Tượng (đen)
    'a': 'advisor',    # Sĩ (đen)
    'k': 'king',       # Tướng (đen)
    'c': 'cannon',     # Pháo (đen)
    'p': 'soldier',    # Tốt (đen)
    'R': 'chariot',    # Xe (đỏ)
    'N': 'horse',      # Mã (đỏ)
    'B': 'elephant',   # Tượng (đỏ)
    'A': 'advisor',    # Sĩ (đỏ)
    'K': 'king',       # Tướng (đỏ)
    'C': 'cannon',     # Pháo (đỏ)
    'P': 'soldier',    # Tốt (đỏ)
}

# Tên tiếng Việt các quân cờ
PIECE_NAMES_VN = {
    'r': 'Xe',     'R': 'Xe',
    'n': 'Mã',     'N': 'Mã',
    'b': 'Tượng',  'B': 'Tượng',
    'a': 'Sĩ',     'A': 'Sĩ',
    'k': 'Tướng',  'K': 'Tướng',
    'c': 'Pháo',   'C': 'Pháo',
    'p': 'Tốt',    'P': 'Tốt',
}

# Engine settings
ENGINE_TIMEOUT = 10  # Timeout cho engine (giây)
ENGINE_DEPTH = 15    # Độ sâu tìm kiếm mặc định
ENGINE_TIME = 5000   # Thời gian suy nghĩ (ms)

# File paths
ASSETS_DIR = "assets"
IMAGES_DIR = f"{ASSETS_DIR}/images"
SOUNDS_DIR = f"{ASSETS_DIR}/sounds"
ENGINES_DIR = "engines"
CONFIG_DIR = "config"

# PNG paths (thay vì SVG)
BOARD_PNG_PATH = f"{IMAGES_DIR}/board/xiangqiboard_.png"
PIECES_DIR = f"{IMAGES_DIR}/pieces"

# PNG file mapping cho các quân cờ (thay vì SVG)
PIECE_PNG_MAPPING = {
    # Quân đỏ (uppercase)
    'R': 'red/rR.png',      # Xe đỏ
    'N': 'red/rN.png',      # Mã đỏ
    'B': 'red/rB.png',      # Tượng đỏ
    'A': 'red/rA.png',      # Sĩ đỏ
    'K': 'red/rK.png',      # Tướng đỏ
    'C': 'red/rC.png',      # Pháo đỏ
    'P': 'red/rP.png',      # Tốt đỏ

    # Quân đen (lowercase)
    'r': 'black/bR.png',    # Xe đen
    'n': 'black/bN.png',    # Mã đen
    'b': 'black/bB.png',    # Tượng đen
    'a': 'black/bA.png',    # Sĩ đen
    'k': 'black/bK.png',    # Tướng đen
    'c': 'black/bC.png',    # Pháo đen
    'p': 'black/bP.png',    # Tốt đen
}


def get_piece_png_path(piece):
    """
    Lấy đường dẫn PNG cho quân cờ

    Args:
        piece: Ký tự quân cờ (e.g., 'R', 'n', 'K')

    Returns:
        str: Đường dẫn đầy đủ đến file PNG
    """
    if piece in PIECE_PNG_MAPPING:
        return os.path.join(PIECES_DIR, PIECE_PNG_MAPPING[piece])
    return None


def get_board_png_path():
    """
    Lấy đường dẫn PNG cho bàn cờ

    Returns:
        str: Đường dẫn đến file PNG bàn cờ
    """
    return BOARD_PNG_PATH


def board_coords_to_pixel(row, col, board_rect):
    """
    Chuyển đổi tọa độ bàn cờ logic sang pixel trên widget

    Args:
        row: Hàng (0-9)
        col: Cột (0-8)
        board_rect: QRect của board widget

    Returns:
        tuple: (x, y) pixel coordinates
    """
    # Tính tỷ lệ scale từ SVG gốc sang board_rect hiện tại
    scale_x = board_rect.width() / BOARD_SVG_WIDTH
    scale_y = board_rect.height() / BOARD_SVG_HEIGHT

    # Xiangqi grid: 9 columns (0-8), 10 rows (0-9)
    # SVG board thực tế: 800x900 pixels bên trong margin 50px
    cell_width = BOARD_ACTUAL_WIDTH / 8  # 8 intervals for 9 columns
    cell_height = BOARD_ACTUAL_HEIGHT / 9  # 9 intervals for 10 rows

    # Tính vị trí trong SVG coordinate system
    svg_x = BOARD_OFFSET_X + col * cell_width
    svg_y = BOARD_OFFSET_Y + row * cell_height

    # Scale lên widget coordinates
    pixel_x = board_rect.left() + svg_x * scale_x
    pixel_y = board_rect.top() + svg_y * scale_y

    return pixel_x, pixel_y


def pixel_to_board_coords(pixel_x, pixel_y, board_rect):
    """
    Chuyển đổi pixel coordinates sang tọa độ bàn cờ logic

    Args:
        pixel_x, pixel_y: Tọa độ pixel
        board_rect: QRect của board widget

    Returns:
        tuple: (row, col) hoặc None nếu ngoài bàn cờ
    """
    # Chuyển về SVG coordinates
    scale_x = board_rect.width() / BOARD_SVG_WIDTH
    scale_y = board_rect.height() / BOARD_SVG_HEIGHT

    svg_x = (pixel_x - board_rect.left()) / scale_x
    svg_y = (pixel_y - board_rect.top()) / scale_y

    # Chuyển về board coordinates
    board_x = svg_x - BOARD_OFFSET_X
    board_y = svg_y - BOARD_OFFSET_Y

    # Xiangqi grid calculation
    cell_width = BOARD_ACTUAL_WIDTH / 8  # 8 intervals for 9 columns
    cell_height = BOARD_ACTUAL_HEIGHT / 9  # 9 intervals for 10 rows

    col = round(board_x / cell_width)
    row = round(board_y / cell_height)

    if 0 <= row < BOARD_HEIGHT and 0 <= col < BOARD_WIDTH:
        return row, col
    return None


def format_move_chinese_style(piece, from_row, from_col, to_row, to_col, current_player):
    """
    Chuyển đổi nước đi sang ký hiệu Trung Quốc

    Args:
        piece: Ký tự quân cờ (e.g., 'K', 'r')
        from_row, from_col: Vị trí xuất phát
        to_row, to_col: Vị trí đích
        current_player: 'red' hoặc 'black'

    Returns:
        str: Nước đi kiểu Trung Quốc (e.g., "tướng 5 tấn 1")
    """
    # Lấy tên quân cờ
    piece_name = PIECE_NAMES_VN.get(piece, piece)
    piece_type = piece.lower()

    # Chuyển đổi cột sang số Trung Quốc (1-9 từ phải qua trái theo từng phía)
    if piece.isupper():  # Quân đỏ
        col_num = 9 - from_col  # Đỏ: 1-9 từ phải qua trái
    else:  # Quân đen
        col_num = from_col + 1  # Đen: 1-9 từ trái qua phải

    # Kiểm tra quân nào có thể dùng "bình"
    can_use_horizontal = piece_type in ['k', 'r', 'c']  # Tướng, Xe, Pháo

    # Kiểm tra tốt đã qua sông (có thể dùng "bình")
    if piece_type == 'p':  # Tốt
        if piece.isupper():  # Tốt đỏ
            can_use_horizontal = from_row <= 4  # Đã qua sông (hàng 0-4)
        else:  # Tốt đen
            can_use_horizontal = from_row >= 5  # Đã qua sông (hàng 5-9)

    # Xác định loại di chuyển
    if from_col == to_col:
        # Di chuyển theo chiều dọc
        if piece.isupper():  # Quân đỏ
            if to_row < from_row:  # Đi lên (giảm row)
                move_type = "tấn"
                steps = from_row - to_row
            else:  # Đi xuống (tăng row)
                move_type = "thoái"
                steps = to_row - from_row
        else:  # Quân đen
            # Đi xuống (tăng row, nhưng là "tấn" theo góc nhìn đen)
            if to_row > from_row:
                move_type = "tấn"
                steps = to_row - from_row
            else:  # Đi lên (giảm row, nhưng là "thoái" theo góc nhìn đen)
                move_type = "thoái"
                steps = from_row - to_row
    else:
        # Di chuyển ngang hoặc chéo
        if can_use_horizontal and from_row == to_row:
            # Quân có thể dùng "bình" và di chuyển hoàn toàn ngang
            move_type = "bình"
            if piece.isupper():  # Quân đỏ
                steps = 9 - to_col  # Vị trí đích theo số Trung Quốc
            else:  # Quân đen
                steps = to_col + 1  # Vị trí đích theo số Trung Quốc
        else:
            # Quân không thể dùng "bình" (Tượng, Sĩ, Mã, Tốt chưa qua sông)
            # hoặc di chuyển chéo - dùng "tấn"/"thoái" + vị trí đích
            if piece.isupper():  # Quân đỏ
                if to_row < from_row:  # Về phía trên
                    move_type = "tấn"
                else:  # Về phía dưới
                    move_type = "thoái"
                steps = 9 - to_col  # Vị trí đích theo số Trung Quốc
            else:  # Quân đen
                if to_row > from_row:  # Về phía dưới (tấn cho đen)
                    move_type = "tấn"
                else:  # Về phía trên (thoái cho đen)
                    move_type = "thoái"
                steps = to_col + 1  # Vị trí đích theo số Trung Quốc

    return f"{piece_name} {col_num} {move_type} {steps}"


def get_piece_column_number(piece, col):
    """
    Lấy số cột theo kiểu Trung Quốc cho quân cờ

    Args:
        piece: Ký tự quân cờ
        col: Cột bàn cờ (0-8)

    Returns:
        int: Số cột (1-9)
    """
    if piece.isupper():  # Quân đỏ
        return 9 - col  # 1-9 từ phải qua trái
    else:  # Quân đen
        return col + 1  # 1-9 từ trái qua phải


def parse_chinese_move_direction(piece, from_row, to_row, from_col, to_col):
    """
    Phân tích hướng di chuyển theo kiểu Trung Quốc

    Returns:
        tuple: (move_type, value) - ("tấn"/"thoái"/"bình", số_bước/vị_trí_đích)
    """
    if from_col == to_col:
        # Di chuyển thẳng
        if piece.isupper():  # Quân đỏ
            if to_row < from_row:
                return "tấn", from_row - to_row
            else:
                return "thoái", to_row - from_row
        else:  # Quân đen
            if to_row > from_row:
                return "tấn", to_row - from_row
            else:
                return "thoái", from_row - to_row
    else:
        # Di chuyển ngang
        if piece.isupper():  # Quân đỏ
            return "bình", 9 - to_col
        else:  # Quân đen
            return "bình", to_col + 1
