# -*- coding: utf-8 -*-
"""
Main Window cho Xiangqi GUI
Cửa sổ chính chứa bàn cờ và các controls
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QMenuBar, QMenu, QAction, QStatusBar, QToolBar,
                             QLabel, QPushButton, QTextEdit, QSplitter,
                             QMessageBox, QApplication, QDesktopWidget, QFileDialog,
                             QTabWidget, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon, QFont, QKeySequence

from .board_widget import BoardWidget
from .game_info_widget import GameInfoWidget
from .multi_engine_widget import MultiEngineWidget
from .setup_widget import SetupWidget
from .dialogs import FenDialog
from ..core.game_state import GameState
from ..utils.constants import *


class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""

    # Signals để thread-safe communication
    position_changed_signal = pyqtSignal(str, list)  # fen, moves

    def __init__(self):
        super().__init__()
        self.game_state = GameState()
        self.chinese_move_notation = True  # Flag để sử dụng ký hiệu Trung Quốc

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Khởi tạo giao diện"""
        self.setWindowTitle("Xiangqi GUI - Cờ Tướng")
        # Kích thước phù hợp với layout nhỏ gọn như ảnh tham khảo
        self.setMinimumSize(1000, 820)
        self.resize(1200, 820)  # Kích thước mặc định vừa phải

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

        # Left panel - Board (thu nhỏ để dành không gian)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Board widget - thu nhỏ canvas như trong ảnh
        self.board_widget = BoardWidget()
        left_layout.addWidget(self.board_widget)

        # Thêm stretch để board không bị kéo giãn
        left_layout.addStretch()

        # Right panel - Sử dụng TabWidget (tăng kích thước như trong ảnh)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)

        # Nút controls ở trên cùng
        controls_layout = QHBoxLayout()
        self.new_game_btn = QPushButton("Ván Mới")
        self.undo_btn = QPushButton("Hoàn Tác")

        controls_layout.addWidget(self.new_game_btn)
        controls_layout.addWidget(self.undo_btn)
        right_layout.addLayout(controls_layout)

        # Tab Widget cho các panel khác nhau
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Tab 1: Game Info
        game_info_tab = QWidget()
        game_info_layout = QVBoxLayout(game_info_tab)
        game_info_layout.setContentsMargins(5, 5, 5, 5)

        self.game_info_widget = GameInfoWidget()
        game_info_layout.addWidget(self.game_info_widget)

        self.tab_widget.addTab(game_info_tab, "🎮 Thông Tin Ván")

        # Tab 2: Multi-Engine Analysis
        multi_engine_tab = QWidget()
        multi_engine_layout = QVBoxLayout(multi_engine_tab)
        multi_engine_layout.setContentsMargins(5, 5, 5, 5)

        # Scroll area cho multi-engine widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.multi_engine_widget = MultiEngineWidget()
        scroll_area.setWidget(self.multi_engine_widget)
        multi_engine_layout.addWidget(scroll_area)

        self.tab_widget.addTab(multi_engine_tab, "🤖 Multi Engine")

        # Tab 3: Setup Mode
        setup_tab = QWidget()
        setup_layout = QVBoxLayout(setup_tab)
        setup_layout.setContentsMargins(5, 5, 5, 5)

        self.setup_widget = SetupWidget()
        setup_layout.addWidget(self.setup_widget)

        self.tab_widget.addTab(setup_tab, "🎯 Xếp Cờ")

        # Tab 4: Settings
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(15)

        # Board Settings Group
        board_group = QWidget()
        board_group_layout = QVBoxLayout(board_group)

        board_title = QLabel("🎯 Cài Đặt Bàn Cờ")
        board_title.setFont(QFont("Arial", 10, QFont.Bold))
        board_group_layout.addWidget(board_title)

        # Flip board button
        self.flip_board_btn = QPushButton("🔄 Lật Bàn Cờ")
        self.flip_board_btn.clicked.connect(self.flip_board)
        board_group_layout.addWidget(self.flip_board_btn)

        # Coordinate style button
        self.coord_style_btn = QPushButton(
            "📍 Toggle Tọa Độ (Trung Quốc/Quốc Tế)")
        self.coord_style_btn.clicked.connect(self.toggle_coordinate_style)
        board_group_layout.addWidget(self.coord_style_btn)

        settings_layout.addWidget(board_group)

        # Move Notation Group
        notation_group = QWidget()
        notation_group_layout = QVBoxLayout(notation_group)

        notation_title = QLabel("📝 Ký Hiệu Nước Đi")
        notation_title.setFont(QFont("Arial", 10, QFont.Bold))
        notation_group_layout.addWidget(notation_title)

        self.notation_style_btn = QPushButton(
            "🔤 Toggle Ký Hiệu (Trung Quốc/Quốc Tế)")
        self.notation_style_btn.clicked.connect(
            self.toggle_move_notation_style)
        notation_group_layout.addWidget(self.notation_style_btn)

        settings_layout.addWidget(notation_group)

        # Thêm stretch để đẩy các controls lên trên
        settings_layout.addStretch()

        self.tab_widget.addTab(settings_tab, "⚙️ Cài Đặt")

        # Thêm tab widget vào layout
        right_layout.addWidget(self.tab_widget)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Set splitter proportions (40% board, 60% info) - như trong ảnh tham khảo
        splitter.setSizes([400, 600])
        splitter.setCollapsible(0, False)  # Board không thể collapse
        splitter.setCollapsible(1, False)  # Info panel không thể collapse

        # Tạo menu bar
        self.create_menu_bar()

        # Tạo tool bar
        self.create_toolbar()

        # Tạo status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Tạo permanent label cho turn ở bên phải status bar
        self.turn_label = QLabel("Lượt: Đỏ")
        self.turn_label.setStyleSheet(
            "QLabel { color: blue; font-weight: bold; margin-left: 10px; }")
        self.status_bar.addPermanentWidget(self.turn_label)

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

        # Menu View
        view_menu = menubar.addMenu('&Hiển Thị')

        # Flip board action
        flip_board_action = QAction('&Lật Bàn Cờ', self)
        flip_board_action.setShortcut('Ctrl+F')
        flip_board_action.setStatusTip(
            'Lật bàn cờ (xem từ góc nhìn đối phương)')
        flip_board_action.triggered.connect(self.flip_board)
        view_menu.addAction(flip_board_action)

        view_menu.addSeparator()

        # Toggle coordinate style action
        toggle_coords_action = QAction('&Tọa Độ Kiểu Trung Quốc', self)
        toggle_coords_action.setCheckable(True)
        toggle_coords_action.setChecked(True)
        toggle_coords_action.setStatusTip(
            'Chuyển đổi giữa tọa độ a-i/0-9 và 1-9 kiểu Trung Quốc')
        toggle_coords_action.triggered.connect(self.toggle_coordinate_style)
        view_menu.addAction(toggle_coords_action)

        # Toggle move notation style action
        toggle_move_notation_action = QAction(
            '&Ký Hiệu Nước Đi Trung Quốc', self)
        toggle_move_notation_action.setCheckable(True)
        toggle_move_notation_action.setChecked(True)
        toggle_move_notation_action.setStatusTip(
            'Chuyển đổi giữa a1→b2 và "tướng 5 tấn 1"')
        toggle_move_notation_action.triggered.connect(
            self.toggle_move_notation_style)
        view_menu.addAction(toggle_move_notation_action)

        # Lưu reference để sử dụng sau
        self.coords_action = toggle_coords_action
        self.move_notation_action = toggle_move_notation_action

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

    def setup_connections(self):
        """Thiết lập kết nối signals/slots"""
        # Kết nối board widget signals
        self.board_widget.piece_moved.connect(self.on_piece_moved)
        self.board_widget.square_clicked.connect(self.on_square_clicked)
        self.board_widget.move_made.connect(self.on_move_made)

        # Multi-engine connections
        self.multi_engine_widget.hint_selected.connect(
            self.on_multi_engine_hint_selected)
        self.multi_engine_widget.engine_arrows_changed.connect(
            self.on_multi_engine_arrows_changed)

        # Setup widget connections
        self.setup_widget.position_changed.connect(
            self.on_setup_position_changed)
        self.setup_widget.mode_changed.connect(self.on_setup_mode_changed)

        # Tab widget connections - Detect khi user chuyển tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Kết nối signal position changed để tự động cập nhật multi-engine
        self.position_changed_signal.connect(
            self.multi_engine_widget.set_position)
        print(
            f"🔗 [SETUP] Connected position_changed_signal to multi_engine_widget.set_position")
        print(f"🔗 [SETUP] Signal connection completed")

        # Kết nối button signals
        self.new_game_btn.clicked.connect(self.new_game)
        self.undo_btn.clicked.connect(self.undo_move)

        # Set initial position cho multi-engine widget
        self._emit_position_changed()

    def _emit_position_changed(self):
        """Emit signal khi position thay đổi"""
        current_fen = self.game_state.to_fen()
        if current_fen:
            engine_moves = self.convert_moves_to_engine_notation(
                self.game_state.move_history)
            print(f"📡 Position changed: {len(engine_moves)} moves")
            if engine_moves:
                # Show last 3 moves
                print(f"📝 Latest moves: {engine_moves[-3:]}")
            self.position_changed_signal.emit(current_fen, engine_moves)
        else:
            print(f"❌ [SIGNAL] Cannot emit - no FEN available")

    def new_game(self):
        """Bắt đầu ván mới"""
        # Reset game state
        self.game_state.reset()

        # Đồng bộ board với game state
        self.board_widget.board_state = [row[:]
                                         for row in self.game_state.board]
        self.board_widget.set_current_player(self.game_state.current_player)
        self.board_widget.selected_square = None
        self.board_widget.possible_moves = []
        self.board_widget.update()

        # Reset UI
        self.game_info_widget.reset()
        self.game_info_widget.set_current_player(
            self.game_state.current_player)
        self.update_turn_label()

        self.update_status("✓ Đã bắt đầu ván mới")

        # Emit position changed để update multi-engine
        self._emit_position_changed()

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
            # ===== CRITICAL: Sync BoardWidget với GameState sau move thành công =====

            # 1. Sync board state từ GameState (GameState đã update board)
            self.board_widget.board_state = [row[:]
                                             for row in self.game_state.board]

            # 2. Sync current_player (GameState đã chuyển lượt)
            self.board_widget.current_player = self.game_state.current_player

            # 3. Clear selection và possible moves
            self.board_widget.selected_square = None
            self.board_widget.possible_moves = []

            # 4. Update board widget display
            self.board_widget.update()

            # Lấy thông tin move để hiển thị
            # Piece đã được di chuyển
            piece = self.game_state.board[to_row][to_col]
            captured_piece = self.game_state.captured_pieces[-1] if self.game_state.captured_pieces else None
            move_notation = self.game_state.move_history[-1] if self.game_state.move_history else ""

            # Update UI với notation đúng
            piece_name = self.get_piece_name(piece)

            # Format move dựa trên style đã chọn
            if self.chinese_move_notation:
                # Sử dụng Chinese notation
                from ..utils.constants import format_move_chinese_style
                formatted_move = format_move_chinese_style(
                    piece, from_row, from_col, to_row, to_col,
                    'red' if piece.isupper() else 'black')
            else:
                # Sử dụng international notation
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

            # Update turn label để hiển thị lượt tiếp theo
            self.update_turn_label()

            # Clear previous engine hint
            self.board_widget.clear_engine_hint()

            # Check for game end conditions
            self.check_game_end()

            # Update position cho multi-engine widget
            self._emit_position_changed()

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

    def undo_move(self):
        """Hoàn tác nước đi cuối"""
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
                self.update_turn_label()

                self.update_status(f"✓ Đã hoàn tác nước đi: {last_move}")

                # Update position cho multi-engine widget
                self._emit_position_changed()
            else:
                self.update_status("❌ Không thể hoàn tác nước đi")
        else:
            self.update_status("❌ Không có nước đi để hoàn tác")

    def redo_move(self):
        """Làm lại nước đi đã hoàn tác"""
        if self.game_state.can_redo():
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
                last_move = self.game_state.move_history[-1] if self.game_state.move_history else "unknown"
                formatted_move = self.format_move_for_display(
                    last_move, len(self.game_state.move_history) - 1)
                self.game_info_widget.add_move(formatted_move)
                self.game_info_widget.set_current_player(
                    self.game_state.current_player)
                self.update_turn_label()

                self.update_status(f"✓ Đã làm lại nước đi: {last_move}")

                # Update position cho multi-engine widget
                self._emit_position_changed()
            else:
                self.update_status("❌ Không thể làm lại nước đi")
        else:
            self.update_status("❌ Không có nước đi để làm lại")

    def update_turn_label(self):
        """Cập nhật label hiển thị lượt đi"""
        current_player = 'Đỏ' if self.game_state.current_player == 'red' else 'Đen'
        self.turn_label.setText(f"Lượt: {current_player}")

    def update_status(self, message):
        """Cập nhật status bar"""
        self.status_bar.showMessage(message)

    def show_about(self):
        """Hiển thị dialog về chương trình"""
        QMessageBox.about(self, "Về Chương Trình",
                          "Xiangqi GUI - Cờ Tướng\n\n"
                          "Phiên bản: 1.0\n"
                          "Hỗ trợ Multi-Engine Analysis\n\n"
                          "Tác giả: AI Assistant")

    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        # Stop multi-engine manager
        if hasattr(self, 'multi_engine_widget'):
            self.multi_engine_widget.closeEvent(event)

        super().closeEvent(event)

    def show_fen_dialog(self):
        """Hiển thị dialog để nhập FEN"""
        current_fen = self.board_widget.get_current_fen()
        fen_dialog = FenDialog(self, current_fen)

        if fen_dialog.exec_() == fen_dialog.Accepted:
            fen = fen_dialog.get_result_fen()
            if fen and self.board_widget.load_fen_position(fen):
                # Update game state
                self.game_state = GameState()
                success = self.game_state.load_from_fen(fen)

                if not success:
                    self.update_status("❌ FEN không hợp lệ")
                    return

                self.game_info_widget.reset()

                # Clear engine hint
                self.board_widget.clear_engine_hint()

                # Update position cho multi-engine widget
                self._emit_position_changed()

                self.update_status("✓ Đã load position từ FEN")
            else:
                self.update_status("❌ Không thể load FEN")

    def copy_current_fen(self):
        """Copy FEN của vị trí hiện tại"""
        fen = self.game_state.to_fen()
        QApplication.clipboard().setText(fen)
        self.update_status("FEN đã được sao chép vào clipboard")

    def flip_board(self):
        """Lật bàn cờ để xem từ góc nhìn đối phương"""
        # Toggle flip state của board widget
        self.board_widget.flip_board()

        # Đồng bộ với setup widget
        if hasattr(self, 'setup_widget'):
            self.setup_widget.sync_board_flip(self.board_widget.is_flipped)

        # Cập nhật status
        if self.board_widget.is_flipped:
            self.update_status("🔄 Đã lật bàn cờ - Xem từ góc nhìn quân Đen")
        else:
            self.update_status("🔄 Đã lật bàn cờ - Xem từ góc nhìn quân Đỏ")

    def toggle_coordinate_style(self):
        """Toggle giữa tọa độ quốc tế (a-i/0-9) và kiểu Trung Quốc (1-9)"""
        # Toggle coordinate style của board widget
        self.board_widget.toggle_coordinate_style()

        # Cập nhật status
        if self.board_widget.chinese_coords:
            self.update_status("📍 Đã chuyển sang tọa độ kiểu Trung Quốc (1-9)")
        else:
            self.update_status("📍 Đã chuyển sang tọa độ quốc tế (a-i/0-9)")

    def toggle_move_notation_style(self):
        """Toggle giữa ký hiệu nước đi quốc tế và kiểu Trung Quốc"""
        self.chinese_move_notation = not self.chinese_move_notation

        # Cập nhật status
        if self.chinese_move_notation:
            self.update_status("📝 Đã chuyển sang ký hiệu nước đi Trung Quốc")
        else:
            self.update_status("📝 Đã chuyển sang ký hiệu nước đi quốc tế")

        # Refresh game info để hiển thị lại moves với style mới
        self.refresh_move_history()

    def refresh_move_history(self):
        """Refresh lại history moves với style notation mới"""
        if hasattr(self, 'game_info_widget'):
            # Clear current moves và rebuild
            self.game_info_widget.clear_moves()

            # Rebuild từ game state history
            for i, move in enumerate(self.game_state.move_history):
                formatted_move = self.format_move_for_display(move, i)
                self.game_info_widget.add_move(formatted_move)

    def format_move_for_display(self, move, move_index=None):
        """
        Format move cho hiển thị dựa trên style đã chọn

        Args:
            move: Move notation (e.g., "e0e1")
            move_index: Index của move trong history (để xác định quân cờ)

        Returns:
            str: Formatted move
        """
        if self.chinese_move_notation and move_index is not None:
            # Kiểu Trung Quốc: cần thông tin về quân cờ đã di chuyển
            return self.format_move_chinese_from_history(move, move_index)
        else:
            # Kiểu quốc tế
            return self.format_move_notation(move, is_engine_notation=False)

    def format_move_chinese_from_history(self, move, move_index):
        """
        Format move theo kiểu Trung Quốc từ history
        """
        try:
            # Parse move notation
            if len(move) != 4:
                return move

            from_col = ord(move[0]) - ord('a')
            from_row = int(move[1])
            to_col = ord(move[2]) - ord('a')
            to_row = int(move[3])

            # Xác định quân cờ đã di chuyển từ history
            # Cần replay lại moves để biết quân gì đã di chuyển
            piece = self.get_piece_from_move_history(
                move_index, from_row, from_col)
            if piece:
                # Xác định player từ move index
                current_player = 'red' if move_index % 2 == 0 else 'black'

                # Sử dụng function từ constants.py
                from ..utils.constants import format_move_chinese_style
                return format_move_chinese_style(piece, from_row, from_col, to_row, to_col, current_player)
            else:
                # Fallback về notation cũ
                return self.format_move_notation(move, is_engine_notation=False)

        except Exception as e:
            print(f"Lỗi format move Chinese: {e}")
            return self.format_move_notation(move, is_engine_notation=False)

    def get_piece_from_move_history(self, move_index, from_row, from_col):
        """
        Lấy quân cờ đã di chuyển từ history bằng cách replay moves
        """
        try:
            # Tạo temporary game state để replay
            from ..core.game_state import GameState
            temp_game = GameState()

            # Replay tất cả moves cho đến move_index
            for i in range(move_index + 1):
                if i < len(self.game_state.move_history):
                    move = self.game_state.move_history[i]
                    if len(move) == 4:
                        move_from_col = ord(move[0]) - ord('a')
                        move_from_row = int(move[1])
                        move_to_col = ord(move[2]) - ord('a')
                        move_to_row = int(move[3])

                        if i == move_index:
                            # Đây là move chúng ta quan tâm
                            return temp_game.board[move_from_row][move_from_col]
                        else:
                            # Replay move này
                            temp_game.make_move(
                                move_from_row, move_from_col, move_to_row, move_to_col)
                            return None
        except Exception as e:
            print(f"Lỗi get piece from history: {e}")
            return None

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
        print(
            f"🔄 Converting {len(board_moves)} board moves to engine notation")

        for i, move in enumerate(board_moves):
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

                if i < 3 or i >= len(board_moves) - 3:  # Show first 3 and last 3
                    print(f"📝 Move {i+1}: {move} -> {engine_move}")

        print(f"✅ Converted to {len(engine_moves)} engine moves")
        return engine_moves

    def on_multi_engine_hint_selected(self, engine_name: str, move: str):
        """Xử lý khi user chọn hint từ multi-engine"""
        print(f"🎯 Chọn gợi ý từ {engine_name}: {move}")

        # Highlight move trên board
        if len(move) >= 4:
            from_pos = move[:2]
            to_pos = move[2:4]

            # Convert sang board coordinates
            from_coords = self.board_widget._pos_to_coords(from_pos)
            to_coords = self.board_widget._pos_to_coords(to_pos)

            if from_coords and to_coords:
                from_row, from_col = from_coords
                to_row, to_col = to_coords

                # Set engine hint để highlight
                self.board_widget.set_engine_hint(
                    (from_row, from_col, to_row, to_col))

                self.update_status(f"🤖 Gợi ý từ {engine_name}: {move}")

    def on_multi_engine_arrows_changed(self, arrows_data: dict):
        """Xử lý khi multi-engine arrows thay đổi"""
        # Update board widget với arrows mới
        self.board_widget.set_multi_engine_arrows(arrows_data)

    def on_setup_position_changed(self, fen):
        """Xử lý khi position thay đổi từ setup mode"""
        print(f"🎯 Setup position changed: {fen}")

        # Không cập nhật board widget hiện tại trong setup mode
        # Chỉ update multi-engine để phân tích position
        engine_moves = []  # Empty moves cho setup position
        self.position_changed_signal.emit(fen, engine_moves)

        self.update_status(
            "🎯 Position setup đã cập nhật - Multi-engine đang phân tích")

    def on_setup_mode_changed(self, mode):
        """Xử lý khi chuyển đổi mode"""
        if mode == 'play':
            # Chuyển sang chế độ chơi - load FEN từ setup widget
            fen = self.setup_widget.get_current_fen()

            if fen:
                try:
                    # Load FEN vào game state
                    from ..core.game_state import GameState
                    self.game_state = GameState()
                    success = self.game_state.load_from_fen(fen)

                    if not success:
                        self.update_status("❌ FEN không hợp lệ")
                        return

                    # Reset game state flags để đảm bảo chuyển lượt bình thường
                    self.game_state.game_over = False
                    self.game_state.winner = None
                    self.game_state.game_status = 'playing'

                    # Clear move history để bắt đầu fresh
                    self.game_state.move_history = []
                    self.game_state.board_history = []
                    self.game_state.captured_pieces = []
                    self.game_state.player_history = []

                    # Clear redo stacks
                    self.game_state.redo_board_history = []
                    self.game_state.redo_player_history = []
                    self.game_state.redo_captured_pieces = []
                    self.game_state.redo_move_history = []

                    # ===== CRITICAL: Sync BoardWidget hoàn toàn với GameState =====

                    # 1. Sync board state (deep copy để tránh reference issues)
                    self.board_widget.board_state = [
                        row[:] for row in self.game_state.board]

                    # 2. Force sync current_player (key fix)
                    self.board_widget.current_player = self.game_state.current_player

                    # 3. Clear board widget states
                    self.board_widget.selected_square = None
                    self.board_widget.possible_moves = []
                    self.board_widget.clear_engine_hint()

                    # 4. Force UI update
                    self.board_widget.update()
                    self.board_widget.repaint()  # Force repaint

                    # Update UI components
                    self.game_info_widget.reset()
                    self.game_info_widget.set_current_player(
                        self.game_state.current_player)
                    self.update_turn_label()

                    # Switch to game tab
                    self.tab_widget.setCurrentIndex(0)  # Game info tab

                    player_name = 'Đỏ' if self.game_state.current_player == 'red' else 'Đen'
                    self.update_status(
                        f"🎮 Đã chuyển sang chế độ chơi - Lượt: {player_name}")

                except Exception as e:
                    print(f"Lỗi load FEN: {e}")
                    import traceback
                    traceback.print_exc()
                    self.update_status("❌ Lỗi khi load FEN từ setup mode")
            else:
                self.update_status("❌ Không có vị trí nào để chơi")
        else:
            # Chuyển sang setup mode - load FEN từ trạng thái bàn cờ hiện tại
            try:
                # Lấy FEN hiện tại từ game state
                current_fen = self.game_state.to_fen()

                if current_fen:
                    # Load FEN vào setup widget để có thể chỉnh sửa trực tiếp
                    success = self.setup_widget.load_from_fen(current_fen)
                    if success:
                        self.update_status(
                            "🎯 Đã chuyển sang chế độ xếp cờ - Có thể chỉnh sửa vị trí hiện tại")
                    else:
                        # Fallback: sync board state trực tiếp
                        self.setup_widget.set_board_state(
                            self.game_state.board)
                        self.update_status("🎯 Đã chuyển sang chế độ xếp cờ")
                else:
                    # Fallback: sync board state trực tiếp
                    self.setup_widget.set_board_state(self.game_state.board)
                    self.update_status("🎯 Đã chuyển sang chế độ xếp cờ")

            except Exception as e:
                print(f"❌ Error loading FEN into setup mode: {e}")
                # Fallback: sync board state trực tiếp
                self.setup_widget.set_board_state(self.game_state.board)
                self.update_status("🎯 Đã chuyển sang chế độ xếp cờ")

    def on_tab_changed(self, index):
        """Xử lý khi user chuyển tab"""
        if index == 2:  # Setup tab (🎯 Xếp Cờ)
            # Load FEN vào setup widget khi chuyển tab
            current_fen = self.game_state.to_fen()
            success = self.setup_widget.load_from_fen(current_fen)
            if success:
                self.update_status(
                    "🎯 Đã chuyển sang chế độ xếp cờ - Có thể chỉnh sửa vị trí hiện tại")
            else:
                # Fallback: sync board state trực tiếp
                self.setup_widget.set_board_state(self.game_state.board)
                self.update_status("🎯 Đã chuyển sang chế độ xếp cờ")
