# -*- coding: utf-8 -*-
"""
Game State cho Xiangqi
Quản lý trạng thái và logic cơ bản của game cờ tướng
"""

from ..utils.constants import INITIAL_POSITION, BOARD_WIDTH, BOARD_HEIGHT


class GameState:
    """Class quản lý trạng thái game cờ tướng"""

    def __init__(self):
        """Khởi tạo game state với position ban đầu"""
        self.board = self._create_initial_board()
        self.current_player = 'red'  # 'red' hoặc 'black'
        self.move_history = []
        self.game_status = 'playing'  # 'playing', 'checkmate', 'stalemate', 'draw'

        # FEN attributes
        self.active_color = 'w'  # 'w' for red/white, 'b' for black
        self.fullmove_number = 1
        self.halfmove_clock = 0
        self.game_over = False
        self.winner = None

        # Move history để undo
        self.board_history = []  # Lưu trạng thái board sau mỗi nước đi
        self.captured_pieces = []  # Lưu quân bị bắt để restore
        self.player_history = []  # Lưu lịch sử lượt chơi

        # Redo stacks
        self.redo_board_history = []
        self.redo_player_history = []
        self.redo_captured_pieces = []
        self.redo_move_history = []
        self.reset()

    def reset(self):
        """Reset game state về trạng thái ban đầu"""
        self.board = self._create_initial_board()
        self.current_player = 'red'
        self.move_history = []
        self.game_status = 'playing'
        self.active_color = 'w'
        self.fullmove_number = 1
        self.halfmove_clock = 0
        self.game_over = False
        self.winner = None

        # Clear move history
        self.board_history = []
        self.captured_pieces = []
        self.player_history = []

        # Clear redo stacks
        self.redo_board_history = []
        self.redo_player_history = []
        self.redo_captured_pieces = []
        self.redo_move_history = []

        print("🔄 GameState reset về trạng thái ban đầu")

    def _parse_fen(self, fen):
        """Parse FEN string thành board state"""
        board = [[None for _ in range(BOARD_WIDTH)]
                 for _ in range(BOARD_HEIGHT)]

        fen_parts = fen.split()
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

        return board

    def to_fen(self):
        """
        Chuyển game state hiện tại thành FEN string

        Returns:
            str: FEN notation
        """
        try:
            # Build board part
            fen_parts = []
            for row in self.board:
                rank_str = ""
                empty_count = 0

                for piece in row:
                    if piece is None:
                        empty_count += 1
                    else:
                        if empty_count > 0:
                            rank_str += str(empty_count)
                            empty_count = 0
                        rank_str += piece

                # Thêm empty squares cuối rank
                if empty_count > 0:
                    rank_str += str(empty_count)

                fen_parts.append(rank_str)

            board_fen = "/".join(fen_parts)

            # Map current_player sang active_color cho FEN
            active_color = 'w' if self.current_player == 'red' else 'b'

            # Build complete FEN
            fen = f"{board_fen} {active_color}"
            return fen

        except Exception as e:
            print(f"❌ Lỗi generate FEN: {e}")
            return None

    def is_valid_move(self, from_row, from_col, to_row, to_col):
        """
        Kiểm tra nước đi có hợp lệ không

        Args:
            from_row, from_col: Vị trí xuất phát
            to_row, to_col: Vị trí đích

        Returns:
            bool: True nếu nước đi hợp lệ
        """
        # Kiểm tra bounds
        if not self._is_valid_position(from_row, from_col) or not self._is_valid_position(to_row, to_col):
            return False

        # Kiểm tra có quân ở vị trí xuất phát không
        piece = self.board[from_row][from_col]
        if piece is None:
            return False

        # Kiểm tra có phải lượt của mình không
        if not self._is_player_piece(piece, self.current_player):
            return False

        # Kiểm tra không tự ăn quân mình
        target_piece = self.board[to_row][to_col]
        if target_piece and self._is_player_piece(target_piece, self.current_player):
            return False

        # Kiểm tra nước đi theo luật từng quân
        if not self._is_valid_piece_move(piece, from_row, from_col, to_row, to_col):
            return False

        # Kiểm tra không để vua bị chiếu sau nước đi
        if self._would_be_in_check_after_move(from_row, from_col, to_row, to_col):
            return False

        # Kiểm tra không vi phạm quy tắc tướng đối tướng sau nước đi
        if self._would_violate_flying_general_after_move(from_row, from_col, to_row, to_col):
            print(
                f"❌ Nước đi từ ({from_row},{from_col}) đến ({to_row},{to_col}) vi phạm quy tắc tướng đối tướng")
            return False

        return True

    def _is_valid_position(self, row, col):
        """Kiểm tra vị trí có trong bàn cờ không"""
        return 0 <= row < 10 and 0 <= col < 9

    def _is_player_piece(self, piece, player):
        """Kiểm tra quân có phải của player không"""
        if player == 'red':
            return piece.isupper()  # Red pieces are uppercase
        else:
            return piece.islower()  # Black pieces are lowercase

    def _is_valid_piece_move(self, piece, from_row, from_col, to_row, to_col):
        """
        Kiểm tra nước đi có hợp lệ theo luật của từng quân không
        """
        piece_type = piece.lower()

        if piece_type == 'k':  # King/General
            return self._is_valid_king_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'a':  # Advisor
            return self._is_valid_advisor_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'b':  # Bishop/Elephant
            return self._is_valid_bishop_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'n':  # Knight/Horse
            return self._is_valid_knight_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'r':  # Rook/Chariot
            return self._is_valid_rook_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'c':  # Cannon
            return self._is_valid_cannon_move(from_row, from_col, to_row, to_col)
        elif piece_type == 'p':  # Pawn/Soldier
            return self._is_valid_pawn_move(piece, from_row, from_col, to_row, to_col)

        return False

    def _is_valid_king_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra nước đi của Vua/Tướng"""
        # Chỉ di chuyển 1 ô theo chiều dọc hoặc ngang
        if abs(from_row - to_row) + abs(from_col - to_col) != 1:
            return False

        # Phải ở trong cung
        if not self._is_in_palace(to_row, to_col):
            return False

        return True

    def _is_valid_advisor_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra nước đi của Sĩ"""
        # Chỉ di chuyển chéo 1 ô
        if abs(from_row - to_row) != 1 or abs(from_col - to_col) != 1:
            return False

        # Phải ở trong cung
        return self._is_in_palace(to_row, to_col)

    def _is_valid_bishop_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra nước đi của Tượng/Voi"""
        # Di chuyển chéo 2 ô
        if abs(from_row - to_row) != 2 or abs(from_col - to_col) != 2:
            return False

        # Không được qua sông
        if not self._is_same_side_of_river(from_row, to_row):
            return False

        # Kiểm tra có bị chặn không (elephant eye)
        block_row = from_row + (to_row - from_row) // 2
        block_col = from_col + (to_col - from_col) // 2
        return self.board[block_row][block_col] is None

    def _is_valid_knight_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra nước đi của Mã"""
        row_diff = abs(from_row - to_row)
        col_diff = abs(from_col - to_col)

        # Mã đi chữ L (2-1 hoặc 1-2)
        if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)):
            return False

        # Kiểm tra có bị chặn chân không
        if row_diff == 2:  # Di chuyển theo chiều dọc
            block_row = from_row + (1 if to_row > from_row else -1)
            block_col = from_col
        else:  # Di chuyển theo chiều ngang
            block_row = from_row
            block_col = from_col + (1 if to_col > from_col else -1)

        return self.board[block_row][block_col] is None

    def _is_valid_rook_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra nước đi của Xe"""
        # Chỉ di chuyển theo đường thẳng
        if from_row != to_row and from_col != to_col:
            return False

        # Kiểm tra đường đi có bị chặn không
        return self._is_path_clear(from_row, from_col, to_row, to_col)

    def _is_valid_cannon_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra nước đi của Pháo"""
        # Chỉ di chuyển theo đường thẳng
        if from_row != to_row and from_col != to_col:
            return False

        target_piece = self.board[to_row][to_col]

        if target_piece is None:
            # Di chuyển bình thường - đường phải trống
            return self._is_path_clear(from_row, from_col, to_row, to_col)
        else:
            # Bắn quân - phải có đúng 1 quân làm giá đỡ
            return self._count_pieces_between(from_row, from_col, to_row, to_col) == 1

    def _is_valid_pawn_move(self, piece, from_row, from_col, to_row, to_col):
        """Kiểm tra nước đi của Tốt/Binh"""
        is_red = piece.isupper()

        # Chỉ di chuyển 1 ô
        if abs(from_row - to_row) + abs(from_col - to_col) != 1:
            return False

        # Trước khi qua sông chỉ đi thẳng
        if not self._has_crossed_river(from_row, is_red):
            # Chỉ được đi thẳng
            if from_col != to_col:
                return False
            # Đi đúng hướng
            if is_red:
                return to_row < from_row  # Red moves up (decreasing row)
            else:
                return to_row > from_row  # Black moves down (increasing row)
        else:
            # Sau khi qua sông có thể đi ngang hoặc tiến
            if from_row == to_row:  # Di chuyển ngang
                return True
            else:  # Di chuyển dọc
                if is_red:
                    return to_row < from_row  # Red continues up
                else:
                    return to_row > from_row  # Black continues down

    def make_move(self, from_row, from_col, to_row, to_col):
        """
        Thực hiện nước đi và lưu history để undo

        Args:
            from_row, from_col: Vị trí xuất phát
            to_row, to_col: Vị trí đích

        Returns:
            bool: True nếu thành công
        """
        # Validate move trước
        if not self.is_valid_move(from_row, from_col, to_row, to_col):
            return False

        # Kiểm tra xem nước đi có để tướng bị chiếu không
        if self._would_be_in_check_after_move(from_row, from_col, to_row, to_col):
            print("❌ Nước đi này sẽ để tướng bị chiếu")
            return False

        # Kiểm tra quy tắc tướng đối mặt
        if self._would_violate_flying_general_after_move(from_row, from_col, to_row, to_col):
            print("❌ Nước đi này vi phạm quy tắc tướng đối mặt")
            return False

        # Clear redo stacks khi có nước đi mới
        self.redo_board_history.clear()
        self.redo_player_history.clear()
        self.redo_captured_pieces.clear()
        self.redo_move_history.clear()

        # Lưu trạng thái hiện tại để undo
        self.board_history.append([row[:]
                                  for row in self.board])  # Deep copy board
        self.player_history.append(self.current_player)

        # Lưu quân bị bắt
        captured_piece = self.board[to_row][to_col]
        self.captured_pieces.append(captured_piece)

        # Thực hiện nước đi
        piece = self.board[from_row][from_col]
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None

        # Chuyển lượt
        old_player = self.current_player
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        self.active_color = 'b' if self.active_color == 'w' else 'w'

        # Update move history
        move_notation = f"{chr(ord('a') + from_col)}{from_row}{chr(ord('a') + to_col)}{to_row}"
        self.move_history.append(move_notation)

        print(f"✓ GameState: Thực hiện nước đi {move_notation}")

        # Kiểm tra game over sau nước đi
        self._check_game_over()

        return True

    def undo_move(self):
        """
        Hoàn tác nước đi cuối cùng

        Returns:
            bool: True nếu thành công
        """
        if not self.board_history:
            print("❌ Không có nước đi để hoàn tác")
            return False

        # Lưu trạng thái hiện tại vào redo stacks
        self.redo_board_history.append([row[:] for row in self.board])
        self.redo_player_history.append(self.current_player)
        self.redo_captured_pieces.append(
            self.captured_pieces[-1] if self.captured_pieces else None)
        self.redo_move_history.append(
            self.move_history[-1] if self.move_history else "unknown")

        # Restore board state
        self.board = self.board_history.pop()

        # Restore player
        self.current_player = self.player_history.pop()
        self.active_color = 'w' if self.current_player == 'red' else 'b'

        # Remove captured piece từ history
        self.captured_pieces.pop()

        # Remove move từ history
        undone_move = self.move_history.pop() if self.move_history else "unknown"

        print(f"✓ GameState: Hoàn tác nước đi {undone_move}")
        return True

    def can_undo(self):
        """Kiểm tra có thể undo không"""
        return len(self.board_history) > 0

    def redo_move(self):
        """
        Làm lại nước đi đã hoàn tác

        Returns:
            bool: True nếu thành công
        """
        if not self.redo_board_history:
            print("❌ Không có nước đi để làm lại")
            return False

        # Lưu trạng thái hiện tại vào undo stacks
        self.board_history.append([row[:] for row in self.board])
        self.player_history.append(self.current_player)

        # Restore từ redo stacks
        self.board = self.redo_board_history.pop()
        self.current_player = self.redo_player_history.pop()
        self.active_color = 'w' if self.current_player == 'red' else 'b'

        # Restore captured piece và move
        captured_piece = self.redo_captured_pieces.pop()
        redone_move = self.redo_move_history.pop()

        self.captured_pieces.append(captured_piece)
        self.move_history.append(redone_move)

        print(f"✓ GameState: Làm lại nước đi {redone_move}")
        return True

    def can_redo(self):
        """Kiểm tra có thể redo không"""
        return len(self.redo_board_history) > 0

    def get_possible_moves(self, pos):
        """
        Lấy danh sách nước đi có thể từ vị trí

        Args:
            pos: Vị trí dạng string (e.g., "a0")

        Returns:
            list: Danh sách vị trí có thể di chuyển đến
        """
        row, col = self._pos_to_coords(pos)

        if not self._is_valid_coords(row, col):
            return []

        piece = self.board[row][col]
        if piece is None:
            return []

        # TODO: Implement logic cho từng loại quân cờ
        # Hiện tại return empty list
        return []

    def _pos_to_coords(self, pos):
        """Chuyển đổi position string thành coordinates"""
        col = ord(pos[0]) - ord('a')
        row = int(pos[1])
        return row, col

    def _coords_to_pos(self, row, col):
        """Chuyển đổi coordinates thành position string"""
        return f"{chr(ord('a') + col)}{row}"

    def _is_valid_coords(self, row, col):
        """Kiểm tra coordinates có hợp lệ không"""
        return 0 <= row < BOARD_HEIGHT and 0 <= col < BOARD_WIDTH

    def _check_game_over(self):
        """Kiểm tra game đã kết thúc chưa"""
        current = self.current_player

        if self.is_checkmate(current):
            winner = 'black' if current == 'red' else 'red'
            print(f"🏆 {winner.upper()} thắng! {current.upper()} bị chiếu bí")
            return True

        if self.is_stalemate(current):
            print("🤝 Hòa cờ! Không có nước đi hợp lệ")
            return True

        if self.is_in_check(current):
            print(f"⚠️  {current.upper()} đang bị chiếu!")

        return False

    def is_in_check(self, player=None):
        """
        Kiểm tra có bị chiếu tướng không

        Args:
            player: "red" hoặc "black", None để dùng current_player

        Returns:
            bool: True nếu bị chiếu tướng
        """
        if player is None:
            player = self.current_player

        # Tìm vua của player
        king_piece = 'K' if player == 'red' else 'k'
        king_pos = None

        for row in range(10):
            for col in range(9):
                if self.board[row][col] == king_piece:
                    king_pos = (row, col)
                    break

        if not king_pos:
            return False  # Không tìm thấy vua

        # Kiểm tra có quân đối phương nào có thể tấn công vua không
        opponent_player = 'black' if player == 'red' else 'red'

        for row in range(10):
            for col in range(9):
                enemy_piece = self.board[row][col]
                if enemy_piece and self._is_player_piece(enemy_piece, opponent_player):
                    # Tạm thời set current_player để kiểm tra
                    old_player = self.current_player
                    self.current_player = opponent_player

                    # Kiểm tra quân địch có thể tấn công vua không
                    can_attack = self._is_valid_piece_move(
                        enemy_piece, row, col, king_pos[0], king_pos[1])

                    # Restore
                    self.current_player = old_player

                    if can_attack:
                        return True  # Bị chiếu

        return False  # Không bị chiếu

    def get_board_copy(self):
        """Lấy copy của board hiện tại"""
        return [row[:] for row in self.board]

    def load_from_fen(self, fen_string):
        """
        Load game state từ FEN string

        Xiangqi FEN format: 
        "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w"

        Args:
            fen_string: FEN notation string

        Returns:
            bool: True nếu load thành công
        """
        try:
            parts = fen_string.strip().split()
            if len(parts) < 1:
                return False

            # Parse board position (phần đầu tiên)
            board_fen = parts[0]
            new_board = self._parse_board_from_fen(board_fen)
            if new_board is None:
                return False

            # Update board state
            self.board = new_board

            # Parse các thông tin khác nếu có
            if len(parts) >= 2:
                self.active_color = parts[1]  # 'w' hoặc 'b'
                # Map active_color sang current_player
                if self.active_color == 'w':
                    self.current_player = 'red'  # White = Red trong xiangqi
                elif self.active_color == 'b':
                    self.current_player = 'black'  # Black = Black

            if len(parts) >= 6:
                self.fullmove_number = int(parts[5])

            print(f"✓ Load FEN thành công: {fen_string[:50]}...")
            print(
                f"✓ Active color: {self.active_color} → Current player: {self.current_player}")
            return True

        except Exception as e:
            print(f"❌ Lỗi parse FEN: {e}")
            return False

    def _parse_board_from_fen(self, board_fen):
        """
        Parse board position từ FEN notation

        Args:
            board_fen: Board part của FEN string

        Returns:
            list: 2D array representing board hoặc None nếu lỗi
        """
        try:
            # Tạo board rỗng 10x9
            board = [[None for _ in range(9)] for _ in range(10)]

            ranks = board_fen.split('/')
            if len(ranks) != 10:  # Xiangqi có 10 hàng
                print(f"❌ FEN sai: cần 10 ranks, có {len(ranks)}")
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
                                f"❌ FEN sai: quá nhiều pieces ở rank {rank_idx}")
                            return None
                        board[rank_idx][col_idx] = char
                        col_idx += 1

                if col_idx != 9:
                    print(
                        f"❌ FEN sai: rank {rank_idx} có {col_idx} columns thay vì 9")
                    return None

            return board

        except Exception as e:
            print(f"❌ Lỗi parse board FEN: {e}")
            return None

    def _create_initial_board(self):
        """Tạo board với position ban đầu của xiangqi"""
        # Tạo board rỗng 10x9
        board = [[None for _ in range(9)] for _ in range(10)]

        # Black pieces (hàng 0-2)
        board[0] = ['r', 'n', 'b', 'a', 'k', 'a', 'b', 'n', 'r']
        board[2] = [None, 'c', None, None, None, None, None, 'c', None]
        board[3] = ['p', None, 'p', None, 'p', None, 'p', None, 'p']

        # Red pieces (hàng 6-9)
        board[6] = ['P', None, 'P', None, 'P', None, 'P', None, 'P']
        board[7] = [None, 'C', None, None, None, None, None, 'C', None]
        board[9] = ['R', 'N', 'B', 'A', 'K', 'A', 'B', 'N', 'R']

        return board

    def _is_in_palace(self, row, col):
        """Kiểm tra vị trí có trong cung không"""
        # Red palace: rows 7-9, cols 3-5
        # Black palace: rows 0-2, cols 3-5
        return (3 <= col <= 5) and ((0 <= row <= 2) or (7 <= row <= 9))

    def _is_same_side_of_river(self, from_row, to_row):
        """Kiểm tra có cùng bên sông không (cho tượng/voi)"""
        # River is between rows 4 and 5
        return (from_row <= 4 and to_row <= 4) or (from_row >= 5 and to_row >= 5)

    def _has_crossed_river(self, row, is_red):
        """Kiểm tra tốt/binh đã qua sông chưa"""
        if is_red:
            return row <= 4  # Red crosses at row 4
        else:
            return row >= 5  # Black crosses at row 5

    def _is_path_clear(self, from_row, from_col, to_row, to_col):
        """Kiểm tra đường đi có trống không (cho xe)"""
        if from_row == to_row:  # Horizontal move
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col] is not None:
                    return False
        else:  # Vertical move
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col] is not None:
                    return False
        return True

    def _count_pieces_between(self, from_row, from_col, to_row, to_col):
        """Đếm số quân cờ giữa 2 vị trí (cho pháo)"""
        count = 0
        if from_row == to_row:  # Horizontal
            start_col = min(from_col, to_col) + 1
            end_col = max(from_col, to_col)
            for col in range(start_col, end_col):
                if self.board[from_row][col] is not None:
                    count += 1
        else:  # Vertical
            start_row = min(from_row, to_row) + 1
            end_row = max(from_row, to_row)
            for row in range(start_row, end_row):
                if self.board[row][from_col] is not None:
                    count += 1
        return count

    def _check_flying_general_rule(self, from_row, from_col, to_row, to_col):
        """Kiểm tra luật tướng đối tướng"""
        # Tạo board tạm thời sau nước đi
        temp_board = [row[:] for row in self.board]
        temp_board[to_row][to_col] = temp_board[from_row][from_col]
        temp_board[from_row][from_col] = None

        # Tìm vị trí 2 vua
        red_king_pos = None
        black_king_pos = None

        for row in range(10):
            for col in range(9):
                piece = temp_board[row][col]
                if piece == 'K':
                    red_king_pos = (row, col)
                elif piece == 'k':
                    black_king_pos = (row, col)

        if not red_king_pos or not black_king_pos:
            # Không tìm thấy vua (không bình thường nhưng không block move)
            return True

        # Kiểm tra có cùng cột và không có quân nào chặn giữa
        if red_king_pos[1] == black_king_pos[1]:  # Same column
            start_row = min(red_king_pos[0], black_king_pos[0]) + 1
            end_row = max(red_king_pos[0], black_king_pos[0])
            for row in range(start_row, end_row):
                if temp_board[row][red_king_pos[1]] is not None:
                    return True  # Có quân chặn giữa, OK
            return False  # Không có quân chặn, vi phạm luật

        return True  # Không cùng cột, OK

    def _would_be_in_check_after_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra sau nước đi có bị chiếu không"""
        # Tạo board tạm thời
        temp_board = [row[:] for row in self.board]
        piece = temp_board[from_row][from_col]
        temp_board[to_row][to_col] = piece
        temp_board[from_row][from_col] = None

        # Tìm vua của mình
        king_piece = 'K' if self.current_player == 'red' else 'k'
        king_pos = None

        for row in range(10):
            for col in range(9):
                if temp_board[row][col] == king_piece:
                    king_pos = (row, col)
                    break

        if not king_pos:
            print(f"⚠️ Không tìm thấy vua {king_piece} trên bàn cờ")
            return False  # Không tìm thấy vua

        # Kiểm tra có quân đối phương nào có thể tấn công vua không
        opponent_player = 'black' if self.current_player == 'red' else 'red'

        for row in range(10):
            for col in range(9):
                enemy_piece = temp_board[row][col]
                if enemy_piece and self._is_player_piece(enemy_piece, opponent_player):
                    # Tạm thời set board để kiểm tra
                    old_board = self.board
                    self.board = temp_board
                    old_player = self.current_player
                    self.current_player = opponent_player

                    # Kiểm tra quân địch có thể tấn công vua không
                    can_attack = self._is_valid_piece_move(
                        enemy_piece, row, col, king_pos[0], king_pos[1])

                    # Restore
                    self.board = old_board
                    self.current_player = old_player

                    if can_attack:
                        print(
                            f"🚨 Nước đi từ ({from_row},{from_col}) đến ({to_row},{to_col}) sẽ để {king_piece} tại {king_pos} bị chiếu bởi {enemy_piece} tại ({row},{col})")
                        return True  # Bị chiếu

        return False  # Không bị chiếu

    def _would_violate_flying_general_after_move(self, from_row, from_col, to_row, to_col):
        """Kiểm tra sau nước đi có vi phạm quy tắc tướng đối mặt không"""
        # Tạo board tạm thời
        temp_board = [row[:] for row in self.board]
        piece = temp_board[from_row][from_col]
        temp_board[to_row][to_col] = piece
        temp_board[from_row][from_col] = None

        # Tìm vị trí 2 vua
        red_king_pos = None
        black_king_pos = None

        for row in range(10):
            for col in range(9):
                piece = temp_board[row][col]
                if piece == 'K':
                    red_king_pos = (row, col)
                elif piece == 'k':
                    black_king_pos = (row, col)

        if not red_king_pos or not black_king_pos:
            # Không tìm thấy vua (không bình thường nhưng không block move)
            return False

        # Kiểm tra có cùng cột và không có quân nào chặn giữa
        if red_king_pos[1] == black_king_pos[1]:  # Same column
            start_row = min(red_king_pos[0], black_king_pos[0]) + 1
            end_row = max(red_king_pos[0], black_king_pos[0])
            for row in range(start_row, end_row):
                if temp_board[row][red_king_pos[1]] is not None:
                    return False  # Có quân chặn giữa, OK
            return True  # Không có quân chặn, vi phạm luật tướng đối mặt

        return False  # Không cùng cột, OK

    def is_checkmate(self, player=None):
        """
        Kiểm tra có bị chiếu bí (checkmate) không

        Args:
            player: "red" hoặc "black", None để dùng current_player

        Returns:
            bool: True nếu bị chiếu bí
        """
        if player is None:
            player = self.current_player

        # Nếu không bị chiếu thì không thể bị chiếu bí
        if not self.is_in_check(player):
            return False

        # Thử tất cả nước đi có thể của player
        for from_row in range(10):
            for from_col in range(9):
                piece = self.board[from_row][from_col]
                if piece and self._is_player_piece(piece, player):
                    # Thử tất cả vị trí có thể đi đến
                    for to_row in range(10):
                        for to_col in range(9):
                            # Kiểm tra nước đi có hợp lệ không
                            if self.is_valid_move(from_row, from_col, to_row, to_col):
                                # Thử nước đi tạm thời
                                temp_board = [row[:] for row in self.board]
                                temp_board[to_row][to_col] = temp_board[from_row][from_col]
                                temp_board[from_row][from_col] = None

                                # Kiểm tra sau nước đi có còn bị chiếu không
                                old_board = self.board
                                self.board = temp_board
                                still_in_check = self.is_in_check(player)
                                self.board = old_board

                                if not still_in_check:
                                    return False  # Có nước đi thoát được, không phải checkmate

        return True  # Không có nước đi nào thoát được, checkmate

    def is_stalemate(self, player=None):
        """
        Kiểm tra có bị hòa cờ (stalemate) không

        Args:
            player: "red" hoặc "black", None để dùng current_player

        Returns:
            bool: True nếu bị stalemate
        """
        if player is None:
            player = self.current_player

        # Nếu bị chiếu thì không thể stalemate
        if self.is_in_check(player):
            return False

        # Thử tất cả nước đi có thể của player
        for from_row in range(10):
            for from_col in range(9):
                piece = self.board[from_row][from_col]
                if piece and self._is_player_piece(piece, player):
                    # Thử tất cả vị trí có thể đi đến
                    for to_row in range(10):
                        for to_col in range(9):
                            # Kiểm tra nước đi có hợp lệ không
                            if self.is_valid_move(from_row, from_col, to_row, to_col):
                                return False  # Có nước đi hợp lệ, không phải stalemate

        return True  # Không có nước đi hợp lệ nào, stalemate
