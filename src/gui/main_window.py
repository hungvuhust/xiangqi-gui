# -*- coding: utf-8 -*-
"""
Main Window cho Xiangqi GUI
Cửa sổ chính chứa bàn cờ và các controls
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QMenuBar, QMenu, QAction, QStatusBar, QToolBar,
                             QLabel, QPushButton, QTextEdit, QSplitter,
                             QMessageBox, QApplication, QDesktopWidget, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QKeySequence

from .board_widget import BoardWidget
from .game_info_widget import GameInfoWidget
from .dialogs import FenDialog
from ..core.game_state import GameState
from ..engine.ucci_protocol import UCCIEngineManager
from ..utils.constants import *


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""

    # Signals để thread-safe communication
    engine_bestmove_signal = pyqtSignal(str)
    engine_info_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.game_state = GameState()
        self.engine_manager = UCCIEngineManager()

        self.hints_enabled = True  # Track hint state

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("Xiangqi GUI - Cờ Tướng")
        self.setMinimumSize(1000, 700)  # Kích thước tối thiểu
        self.resize(1200, 800)  # Kích thước mặc định

        # Center window on screen
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

        # Tạo central widget với splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Splitter để chia layout
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Board
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Board widget
        self.board_widget = BoardWidget()
        self.board_widget.setMinimumSize(600, 650)  # Kích thước board hợp lý
        self.board_widget.setMaximumSize(800, 850)  # Giới hạn tối đa
        left_layout.addWidget(self.board_widget)

        # Right panel - Game info and controls
        right_panel = QWidget()
        right_panel.setMinimumWidth(300)  # Tối thiểu 300px cho panel phải
        right_panel.setMaximumWidth(450)  # Tối đa 450px
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)

        # Game info widget
        self.game_info_widget = GameInfoWidget()
        right_layout.addWidget(self.game_info_widget)

        # Nút controls
        controls_layout = QHBoxLayout()

        self.new_game_btn = QPushButton("Ván Mới")
        self.undo_btn = QPushButton("Hoàn Tác")
        self.hint_btn = QPushButton("Gợi Ý")

        controls_layout.addWidget(self.new_game_btn)
        controls_layout.addWidget(self.undo_btn)
        controls_layout.addWidget(self.hint_btn)

        right_layout.addLayout(controls_layout)

        # Text area để hiển thị log engine
        self.engine_log = QTextEdit()
        self.engine_log.setMaximumHeight(200)
        self.engine_log.setPlaceholderText("Log giao tiếp với engine...")
        right_layout.addWidget(QLabel("Engine Log:"))
        right_layout.addWidget(self.engine_log)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Set splitter proportions (70% board, 30% info)
        splitter.setSizes([700, 300])
        splitter.setCollapsible(0, False)  # Board không thể collapse
        splitter.setCollapsible(1, False)  # Info panel không thể collapse

        # Tạo menu bar
        self.create_menu_bar()

        # Tạo tool bar
        self.create_toolbar()

        # Tạo status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sẵn sàng - Lượt của Đỏ")

    def create_menu_bar(self):
        """Tạo menu bar"""
        menubar = self.menuBar()

        # Menu File
        file_menu = menubar.addMenu('&File')

        # New game action
        new_game_action = QAction('&New Game', self)
        new_game_action.setShortcut('Ctrl+N')
        new_game_action.setStatusTip('Bắt đầu ván cờ mới')
        new_game_action.triggered.connect(self.new_game)
        file_menu.addAction(new_game_action)

        file_menu.addSeparator()

        # FEN actions
        load_fen_action = QAction('&Load FEN...', self)
        load_fen_action.setShortcut('Ctrl+L')
        load_fen_action.setStatusTip('Load position từ FEN notation')
        load_fen_action.triggered.connect(self.show_fen_dialog)
        file_menu.addAction(load_fen_action)

        copy_fen_action = QAction('&Copy FEN', self)
        copy_fen_action.setShortcut('Ctrl+C')
        copy_fen_action.setStatusTip('Copy FEN của position hiện tại')
        copy_fen_action.triggered.connect(self.copy_current_fen)
        file_menu.addAction(copy_fen_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Thoát chương trình')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Engine
        engine_menu = menubar.addMenu('&Engine')

        load_engine_action = QAction('&Load Engine...', self)
        load_engine_action.setStatusTip('Load engine cờ tướng')
        load_engine_action.triggered.connect(self.load_engine_dialog)
        engine_menu.addAction(load_engine_action)

        engine_menu.addSeparator()

        toggle_hints_action = QAction('&Toggle Hints', self)
        toggle_hints_action.setCheckable(True)
        toggle_hints_action.setChecked(True)
        toggle_hints_action.setStatusTip('Bật/tắt gợi ý từ engine')
        toggle_hints_action.triggered.connect(self.toggle_engine_hints)
        engine_menu.addAction(toggle_hints_action)
        self.hints_enabled = True  # Track hint state

        # Menu View
        view_menu = menubar.addMenu('&Hiển Thị')

        flip_board_action = QAction('&Lật Bàn Cờ', self)
        flip_board_action.setShortcut('F')
        view_menu.addAction(flip_board_action)

        # Menu Help
        help_menu = menubar.addMenu('&Trợ Giúp')

        about_action = QAction('&Về Chương Trình...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Tạo toolbar với các nút thường dùng"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)

        # New game button
        new_action = QAction("Ván Mới", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_game)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        # Undo button
        undo_action = QAction("Hoàn Tác", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_move)
        toolbar.addAction(undo_action)

        # Redo button
        redo_action = QAction("Làm Lại", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_move)
        toolbar.addAction(redo_action)

        toolbar.addSeparator()

        # Engine analysis
        analyze_action = QAction("Phân Tích", self)
        analyze_action.triggered.connect(self.toggle_engine_analysis)
        toolbar.addAction(analyze_action)

    def setup_connections(self):
        """Thiết lập kết nối signals/slots"""
        # Kết nối board widget signals
        self.board_widget.piece_moved.connect(self.on_piece_moved)
        self.board_widget.square_clicked.connect(self.on_square_clicked)
        self.board_widget.move_made.connect(self.on_move_made)

        # Kết nối button signals
        self.new_game_btn.clicked.connect(self.new_game)
        self.undo_btn.clicked.connect(self.undo_move)
        self.hint_btn.clicked.connect(self.get_hint)

        # Kết nối engine signals (thread-safe)
        self.engine_bestmove_signal.connect(self.handle_engine_bestmove)
        self.engine_info_signal.connect(self.handle_engine_info)

    def new_game(self):
        """Bắt đầu ván cờ mới"""
        self.game_state.reset()
        self.board_widget.reset_board()
        self.game_info_widget.reset()

        # Đồng bộ current_player với BoardWidget
        self.board_widget.set_current_player(self.game_state.current_player)

        # Clear engine hint
        self.board_widget.clear_engine_hint()

        # Thông báo cho engine và request hint ban đầu
        if self.engine_manager.get_current_engine():
            engine = self.engine_manager.get_current_engine()
            engine.new_game()

            # Set initial position và request hint
            initial_fen = self.game_state.to_fen()
            if initial_fen:
                engine.set_position(initial_fen)
                engine.get_hint(depth=6)  # Request hint cho nước đi đầu tiên

        self.update_status("✓ Ván cờ mới đã bắt đầu - Lượt của Đỏ")

    def load_engine(self):
        """Tải engine từ file"""
        # TODO: Implement file dialog to select engine
        # Tạm thời hardcode path để test
        engine_path = "./engines/Fairy-Stockfish/fairy-stockfish"  # Ví dụ

        success = self.engine_manager.add_engine(
            "Fairy-Stockfish", engine_path)
        if success:
            self.engine_manager.set_current_engine("Fairy-Stockfish")
            engine = self.engine_manager.get_current_engine()

            # Setup callbacks
            engine.on_bestmove = self.on_engine_bestmove
            engine.on_info = self.on_engine_info

            self.update_status("Engine đã được tải thành công")
        else:
            self.update_status("Lỗi: Không thể tải engine")

    def on_piece_moved(self, from_pos, to_pos):
        """Xử lý khi quân cờ được di chuyển (deprecated - sử dụng on_move_made thay thế)"""
        # Method này không được sử dụng nữa, đã chuyển sang on_move_made
        print(
            f"⚠️ Deprecated method on_piece_moved được gọi: {from_pos} -> {to_pos}")
        pass

    def on_square_clicked(self, position):
        """Xử lý khi click vào ô cờ"""
        print(f"Square clicked: {position}")

    def on_move_made(self, from_row, from_col, to_row, to_col):
        """Xử lý khi thực hiện nước đi hợp lệ"""
        # Sử dụng GameState để thực hiện nước đi (đã bao gồm validation và history tracking)
        if self.game_state.make_move(from_row, from_col, to_row, to_col):
            # Đồng bộ current_player với BoardWidget
            self.board_widget.set_current_player(
                self.game_state.current_player)

            # Lấy thông tin move để hiển thị
            # Piece đã được di chuyển
            piece = self.game_state.board[to_row][to_col]
            captured_piece = self.game_state.captured_pieces[-1] if self.game_state.captured_pieces else None
            move_notation = self.game_state.move_history[-1] if self.game_state.move_history else ""

            # Update UI với notation đúng
            piece_name = self.get_piece_name(piece)
            formatted_move = self.format_move_notation(
                move_notation, is_engine_notation=False)
            if captured_piece:
                status_msg = f"✓ {piece_name} {formatted_move} - Bắt {self.get_piece_name(captured_piece)}"
            else:
                status_msg = f"✓ {piece_name} {formatted_move}"

            self.update_status(status_msg)

            # Update game info với formatted move
            self.game_info_widget.add_move(formatted_move)
            self.game_info_widget.set_current_player(
                self.game_state.current_player)

            # Clear previous engine hint
            self.board_widget.clear_engine_hint()

            # Check for game end conditions
            self.check_game_end()

            # Send move to engine và request hint cho nước đi tiếp theo
            if self.engine_manager.get_current_engine():
                engine = self.engine_manager.get_current_engine()

                # Update position với move history
                current_fen = self.game_state.to_fen()
                if current_fen:
                    # Convert moves từ board notation sang engine notation
                    engine_moves = self.convert_moves_to_engine_notation(
                        self.game_state.move_history)
                    engine.set_position(current_fen, engine_moves)

                # Request hint cho nước đi tiếp theo nếu hints enabled
                if self.hints_enabled:
                    engine.get_hint(depth=6)  # Depth 6 cho hint nhanh

                # Nếu analysis mode bật, phân tích position mới
                if hasattr(self, 'analysis_enabled') and self.analysis_enabled:
                    engine.go(depth=15)  # Phân tích sâu cho analysis mode
        else:
            self.update_status("❌ Nước đi không hợp lệ")

    def get_piece_name(self, piece):
        """Lấy tên tiếng Việt của quân cờ"""
        piece_names = {
            'K': 'Tướng', 'k': 'Tướng',
            'A': 'Sĩ', 'a': 'Sĩ',
            'B': 'Tượng', 'b': 'Tượng',
            'N': 'Mã', 'n': 'Mã',
            'R': 'Xe', 'r': 'Xe',
            'C': 'Pháo', 'c': 'Pháo',
            'P': 'Tốt', 'p': 'Tốt'
        }
        return piece_names.get(piece, piece)

    def check_game_end(self):
        """Kiểm tra điều kiện kết thúc game"""
        # TODO: Implement checkmate, stalemate detection
        pass

    def on_engine_bestmove(self, move):
        """Xử lý khi engine trả về nước đi tốt nhất"""
        # Emit signal for thread-safe communication
        self.engine_bestmove_signal.emit(move)

    def on_engine_info(self, info):
        """Xử lý thông tin từ engine"""
        # Emit signal for thread-safe communication
        self.engine_info_signal.emit(info)

    @pyqtSlot(str)
    def handle_engine_info(self, info):
        """Thread-safe xử lý info từ engine"""
        # Parse engine info và cập nhật game info widget
        if "depth" in info or "score" in info or "pv" in info:
            self.engine_log.append(info)

            # Parse thông tin từ engine info
            info_data = self.parse_engine_info(info)
            if info_data:
                self.game_info_widget.set_engine_info(**info_data)

    def parse_engine_info(self, info_line):
        """
        Parse thông tin từ engine info line

        Args:
            info_line: Dòng info từ engine

        Returns:
            dict: Thông tin đã parse hoặc None
        """
        try:
            parts = info_line.split()
            if not parts or parts[0] != "info":
                return None

            info_data = {}
            i = 1

            while i < len(parts):
                key = parts[i]

                if key == "depth" and i + 1 < len(parts):
                    info_data['depth'] = int(parts[i + 1])
                    i += 2

                elif key == "score" and i + 2 < len(parts):
                    score_type = parts[i + 1]  # "cp" hoặc "mate"
                    score_value = parts[i + 2]

                    if score_type == "cp":
                        # Centipawn score
                        cp_score = int(score_value)
                        # Chuyển đổi từ centipawn sang pawn (chia 100)
                        info_data['evaluation'] = cp_score / 100.0
                    elif score_type == "mate":
                        # Mate in X moves
                        mate_moves = int(score_value)
                        if mate_moves > 0:
                            info_data['evaluation'] = f"Chiếu tướng trong {mate_moves} nước"
                        else:
                            info_data['evaluation'] = f"Bị chiếu tướng trong {abs(mate_moves)} nước"
                    i += 3

                elif key == "nodes" and i + 1 < len(parts):
                    info_data['nodes'] = int(parts[i + 1])
                    i += 2

                elif key == "nps" and i + 1 < len(parts):
                    info_data['nps'] = int(parts[i + 1])
                    i += 2

                elif key == "time" and i + 1 < len(parts):
                    info_data['time_ms'] = int(parts[i + 1])
                    i += 2

                elif key == "pv":
                    # Principal variation - lấy tất cả moves còn lại
                    pv_moves = parts[i + 1:]
                    info_data['pv'] = pv_moves
                    break

                else:
                    i += 1

            return info_data if info_data else None

        except (ValueError, IndexError) as e:
            print(f"❌ Lỗi parse engine info: {e}")
            return None

    def undo_move(self):
        """Hoàn tác nước đi"""
        if self.game_state.can_undo():
            # Lưu thông tin move trước khi undo
            last_move = self.game_state.move_history[-1] if self.game_state.move_history else "unknown"

            # Undo trong GameState
            if self.game_state.undo_move():
                # Đồng bộ board với BoardWidget
                self.board_widget.board_state = [row[:]
                                                 for row in self.game_state.board]
                self.board_widget.set_current_player(
                    self.game_state.current_player)
                self.board_widget.selected_square = None
                self.board_widget.possible_moves = []
                self.board_widget.update()

                # Update UI
                self.game_info_widget.remove_last_move()
                self.game_info_widget.set_current_player(
                    self.game_state.current_player)

                self.update_status(f"✓ Đã hoàn tác nước đi: {last_move}")

                # Trigger analysis nếu analysis mode bật
                if hasattr(self, 'analysis_enabled') and self.analysis_enabled and self.engine_manager.get_current_engine():
                    engine = self.engine_manager.get_current_engine()
                    current_fen = self.game_state.to_fen()
                    if current_fen:
                        engine_moves = self.convert_moves_to_engine_notation(
                            self.game_state.move_history)
                        engine.set_position(current_fen, engine_moves)
                        engine.go(depth=15)
            else:
                self.update_status("❌ Không thể hoàn tác")
        else:
            self.update_status("❌ Không có nước đi để hoàn tác")

    def redo_move(self):
        """Làm lại nước đi"""
        if self.game_state.can_redo():
            # Lưu thông tin move trước khi redo
            next_move = self.game_state.redo_move_history[-1] if self.game_state.redo_move_history else "unknown"

            # Redo trong GameState
            if self.game_state.redo_move():
                # Đồng bộ board với BoardWidget
                self.board_widget.board_state = [row[:]
                                                 for row in self.game_state.board]
                self.board_widget.set_current_player(
                    self.game_state.current_player)
                self.board_widget.selected_square = None
                self.board_widget.possible_moves = []
                self.board_widget.update()

                # Update UI
                self.game_info_widget.set_current_player(
                    self.game_state.current_player)

                # Update move trong game info (thêm lại move)
                formatted_move = self.format_move_notation(
                    next_move, is_engine_notation=False)
                self.game_info_widget.add_move(formatted_move)

                self.update_status(f"✓ Làm lại nước đi: {formatted_move}")

                # Request hint cho position mới nếu hints enabled
                if self.hints_enabled and self.engine_manager.get_current_engine():
                    engine = self.engine_manager.get_current_engine()
                    current_fen = self.game_state.to_fen()
                    if current_fen:
                        engine_moves = self.convert_moves_to_engine_notation(
                            self.game_state.move_history)
                        engine.set_position(current_fen, engine_moves)
                        engine.get_hint(depth=6)

                # Trigger analysis nếu analysis mode bật
                if hasattr(self, 'analysis_enabled') and self.analysis_enabled and self.engine_manager.get_current_engine():
                    engine = self.engine_manager.get_current_engine()
                    current_fen = self.game_state.to_fen()
                    if current_fen:
                        engine_moves = self.convert_moves_to_engine_notation(
                            self.game_state.move_history)
                        engine.set_position(current_fen, engine_moves)
                        engine.go(depth=15)
            else:
                self.update_status("❌ Không thể làm lại nước đi")
        else:
            self.update_status("❌ Không có nước đi để làm lại")

    def get_hint(self):
        """Lấy gợi ý từ engine"""
        if self.engine_manager.get_current_engine():
            engine = self.engine_manager.get_current_engine()

            # Lấy FEN hiện tại thay vì INITIAL_POSITION
            current_fen = self.game_state.to_fen()
            if current_fen:
                # Chuyển đổi move history sang engine notation
                engine_moves = self.convert_moves_to_engine_notation(
                    self.game_state.move_history)
                engine.set_position(current_fen, engine_moves)
                engine.go(depth=ENGINE_DEPTH)
                self.update_status("Đang tìm nước đi tốt nhất...")
            else:
                self.update_status("❌ Không thể lấy FEN hiện tại")
        else:
            self.update_status("Chưa có engine được tải")

    def update_turn_label(self):
        """Cập nhật label hiển thị lượt chơi"""
        current_player = "Đỏ" if self.game_state.current_player == "red" else "Đen"
        self.status_bar.showMessage(f"Sẵn sàng - Lượt của {current_player}")

    def update_status(self, message):
        """Cập nhật status bar"""
        self.status_bar.showMessage(message)

    def show_about(self):
        """Hiển thị dialog về chương trình"""
        # TODO: Implement about dialog
        pass

    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        try:
            # Dừng tất cả engine trước khi thoát
            if hasattr(self, 'engine_manager'):
                self.engine_manager.stop_all_engines()

            # Clear engine log để giải phóng bộ nhớ
            if hasattr(self, 'engine_log'):
                self.engine_log.clear()

            # Disconnect signals
            if hasattr(self, 'engine_bestmove_signal'):
                self.engine_bestmove_signal.disconnect()
            if hasattr(self, 'engine_info_signal'):
                self.engine_info_signal.disconnect()

            print("Cleanup hoàn thành")
        except Exception as e:
            print(f"Lỗi trong cleanup: {e}")
        finally:
            event.accept()

    def show_fen_dialog(self):
        """Hiển thị dialog để nhập FEN"""
        current_fen = self.board_widget.get_current_fen()
        fen_dialog = FenDialog(self, current_fen)

        if fen_dialog.exec_() == fen_dialog.Accepted:
            fen = fen_dialog.get_result_fen()
            if fen and self.board_widget.load_fen_position(fen):
                # Update game state
                self.game_state.load_from_fen(fen)
                self.game_info_widget.reset()

                # Thông báo cho engine
                if self.engine_manager.get_current_engine():
                    engine = self.engine_manager.get_current_engine()
                    engine.new_game()
                    engine.set_position(fen)

                self.update_status("✓ Đã load position từ FEN")
            else:
                self.update_status("❌ Không thể load FEN")

    def copy_current_fen(self):
        """Copy FEN của vị trí hiện tại"""
        fen = self.game_state.to_fen()
        QApplication.clipboard().setText(fen)
        self.update_status("FEN đã được sao chép vào clipboard")

    def toggle_engine_analysis(self):
        """Toggle engine analysis mode on/off"""
        if not hasattr(self, 'analysis_enabled'):
            self.analysis_enabled = False

        self.analysis_enabled = not self.analysis_enabled

        if not self.analysis_enabled:
            # Tắt analysis - dừng engine analysis
            if self.engine_manager.get_current_engine():
                engine = self.engine_manager.get_current_engine()
                engine.stop_search()
            self.update_status("🔍 Đã tắt phân tích liên tục")
        else:
            # Bật analysis - bắt đầu phân tích position hiện tại
            if self.engine_manager.get_current_engine():
                engine = self.engine_manager.get_current_engine()
                current_fen = self.game_state.to_fen()
                if current_fen:
                    engine_moves = self.convert_moves_to_engine_notation(
                        self.game_state.move_history)
                    engine.set_position(current_fen, engine_moves)
                    # Phân tích sâu hơn cho analysis mode
                    engine.go(depth=15)  # Depth cao hơn cho analysis
                self.update_status("🔍 Đã bật phân tích liên tục (depth 15)")
            else:
                self.update_status("❌ Cần load engine trước khi phân tích")

    def toggle_engine_hints(self):
        """Toggle engine hints on/off"""
        self.hints_enabled = not self.hints_enabled

        if not self.hints_enabled:
            # Tắt hints - clear hint hiện tại
            self.board_widget.clear_engine_hint()
            self.update_status("🤖 Đã tắt gợi ý engine")
        else:
            # Bật hints - request hint cho position hiện tại
            if self.engine_manager.get_current_engine():
                engine = self.engine_manager.get_current_engine()
                current_fen = self.game_state.to_fen()
                if current_fen:
                    engine.set_position(current_fen)
                    engine.get_hint(depth=6)
            self.update_status("🤖 Đã bật gợi ý engine")

    def load_engine_dialog(self):
        """Hiển thị dialog để chọn engine file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn Engine Cờ Tướng",
            "./engines/",
            "Executable Files All Files (*)"
        )

        if file_path:
            self.load_engine_from_path(file_path)

    def load_engine_from_path(self, engine_path):
        """Load engine từ đường dẫn"""
        engine_name = f"Engine_{len(self.engine_manager.engines) + 1}"

        success = self.engine_manager.add_engine(engine_name, engine_path)
        if success:
            self.engine_manager.set_current_engine(engine_name)
            engine = self.engine_manager.get_current_engine()

            # Setup callbacks
            engine.on_bestmove = self.on_engine_bestmove
            engine.on_info = self.on_engine_info

            self.update_status(f"✓ Engine đã được tải: {engine_path}")

            # Request hint cho position hiện tại nếu hints enabled
            if self.hints_enabled:
                current_fen = self.game_state.to_fen()
                if current_fen:
                    engine.set_position(current_fen)
                    engine.get_hint(depth=6)
        else:
            self.update_status(f"❌ Không thể tải engine: {engine_path}")

    @pyqtSlot(str)
    def handle_engine_bestmove(self, bestmove_line):
        """Thread-safe xử lý bestmove từ engine"""
        if self.hints_enabled and bestmove_line:
            print(f"🤖 Engine response: {bestmove_line}")

            # Parse bestmove line: "bestmove b0c2 ponder g6g5"
            parts = bestmove_line.strip().split()
            bestmove = None
            ponder = None

            for i, part in enumerate(parts):
                if part == "bestmove" and i + 1 < len(parts):
                    bestmove = parts[i + 1]
                elif part == "ponder" and i + 1 < len(parts):
                    ponder = parts[i + 1]

            if bestmove:
                # Hiển thị hint trên board với cả bestmove và ponder
                self.board_widget.set_engine_hint(bestmove, ponder)

                # Update status với màu tương ứng
                player_name = "Đỏ" if self.game_state.current_player == 'red' else "Đen"
                arrow_color = "tím" if self.game_state.current_player == 'red' else "xanh"

                status_msg = f"🤖 Engine gợi ý cho {player_name} (mũi tên {arrow_color}): {bestmove}"
                if ponder:
                    opponent_name = "Đen" if self.game_state.current_player == 'red' else "Đỏ"
                    ponder_color = "xanh" if self.game_state.current_player == 'red' else "tím"
                    status_msg += f", dự đoán {opponent_name} (đứt nét {ponder_color}): {ponder}"

                self.update_status(status_msg)

                # Log vào engine log
                log_msg = f"Engine đề xuất: {bestmove}"
                if ponder:
                    log_msg += f", dự đoán: {ponder}"
                self.engine_log.append(log_msg)

                # Cập nhật best move trong game info widget
                formatted_move = self.format_move_notation(
                    bestmove, is_engine_notation=True)
                self.game_info_widget.set_engine_info(best_move=formatted_move)

    def format_move_notation(self, move, is_engine_notation=False):
        """
        Format move notation cho dễ đọc

        Args:
            move: Move notation (e.g., "c2d2")
            is_engine_notation: True nếu move dùng engine notation (0-9), False nếu board notation (0-9)

        Returns:
            str: Formatted move
        """
        if not move or len(move) != 4:
            return move

        try:
            # Parse move
            from_file = move[0]
            from_rank = int(move[1])
            to_file = move[2]
            to_rank = int(move[3])

            if is_engine_notation:
                # Engine notation: rank 0-9 (0=red bottom, 9=black top)
                # Hiển thị như engine notation
                from_pos = f"{from_file}{from_rank}"
                to_pos = f"{to_file}{to_rank}"
            else:
                # Board notation: rank 0-9 (0=black top, 9=red bottom)
                # Chuyển đổi sang engine notation để hiển thị
                display_from_rank = 9 - from_rank
                display_to_rank = 9 - to_rank
                from_pos = f"{from_file}{display_from_rank}"
                to_pos = f"{to_file}{display_to_rank}"

            return f"{from_pos} → {to_pos}"

        except (IndexError, ValueError):
            return move

    def convert_moves_to_engine_notation(self, board_moves):
        """
        Chuyển đổi moves từ board notation sang engine notation

        Args:
            board_moves: List moves trong board notation

        Returns:
            list: Moves trong engine notation
        """
        engine_moves = []

        for move in board_moves:
            if len(move) == 4:
                # Parse board move: e.g., "a9b8" (board notation)
                from_file = move[0]
                from_rank = int(move[1])
                to_file = move[2]
                to_rank = int(move[3])

                # Chuyển đổi sang engine notation (đảo ngược rank)
                # Board rank 0-9 -> Engine rank 9-0
                engine_from_rank = 9 - from_rank
                engine_to_rank = 9 - to_rank

                # Tạo engine move notation
                engine_move = f"{from_file}{engine_from_rank}{to_file}{engine_to_rank}"
                engine_moves.append(engine_move)

        return engine_moves
