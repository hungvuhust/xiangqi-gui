"""
Widget hiển thị kết quả phân tích từ nhiều engine
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QCheckBox, QSpinBox, QComboBox, QGroupBox,
                             QHeaderView, QFrame, QSplitter, QFileDialog, QTextEdit,
                             QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from typing import Dict, List
import os

from ..engine.multi_engine_manager import MultiEngineManager
from ..utils.constants import format_move_chinese_style


class MultiEngineWidget(QWidget):
    """Widget hiển thị phân tích từ nhiều engine cùng lúc"""

    # Signals
    hint_selected = pyqtSignal(str, str)  # (engine_name, move)
    # {engine_name: [(from, to, color)]}
    engine_arrows_changed = pyqtSignal(dict)
    # {engine_name: {'bestmove': str, 'ponder': str, 'evaluation': float, 'depth': int}}
    analysis_info_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.multi_engine_manager = MultiEngineManager()

        # Connect signals
        self.multi_engine_manager.engine_result_updated.connect(
            self._on_engine_result_updated)

        self.available_engines = []  # Danh sách engine có sẵn
        self.current_fen = None
        self.current_moves = []
        self.current_player = 'red'  # Lượt hiện tại ('red' hoặc 'black')
        self.is_analysis_running = False

        # UI Update timer - giảm tần suất để tránh lag
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.setInterval(2000)  # Update mỗi 2 giây để giảm tải

        # Arrow update throttling
        self.arrow_update_timer = QTimer()
        self.arrow_update_timer.timeout.connect(self._update_arrows)
        self.arrow_update_timer.setSingleShot(True)  # Chỉ chạy một lần

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout(self)

        # Control panel
        control_group = QGroupBox("Điều Khiển Nhiều Engine")
        control_layout = QVBoxLayout(control_group)

        # Engine selection
        engine_layout = QVBoxLayout()

        # Engine path input
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Đường dẫn Engine:"))

        self.engine_path_edit = QLineEdit()
        self.engine_path_edit.setPlaceholderText(
            "Chọn file engine executable...")
        self.engine_path_edit.setReadOnly(True)
        path_layout.addWidget(self.engine_path_edit)

        self.browse_engine_btn = QPushButton("📁 Browse")
        self.browse_engine_btn.clicked.connect(self._browse_engine_file)
        path_layout.addWidget(self.browse_engine_btn)

        engine_layout.addLayout(path_layout)

        # Engine name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Tên Engine:"))

        self.engine_name_edit = QLineEdit()
        self.engine_name_edit.setPlaceholderText("Nhập tên cho engine...")
        name_layout.addWidget(self.engine_name_edit)

        engine_layout.addLayout(name_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.add_engine_btn = QPushButton("➕ Thêm Engine")
        self.add_engine_btn.clicked.connect(self._add_engine_from_path)
        # Disabled until path is selected
        self.add_engine_btn.setEnabled(False)
        button_layout.addWidget(self.add_engine_btn)

        self.remove_engine_btn = QPushButton("❌ Xóa Engine")
        self.remove_engine_btn.clicked.connect(self._remove_selected_engine)
        button_layout.addWidget(self.remove_engine_btn)

        button_layout.addStretch()
        engine_layout.addLayout(button_layout)

        control_layout.addLayout(engine_layout)

        # Analysis controls
        analysis_layout = QHBoxLayout()

        self.toggle_analysis_btn = QPushButton("🔍 Bắt Đầu Phân Tích")
        self.toggle_analysis_btn.clicked.connect(self._toggle_analysis)
        analysis_layout.addWidget(self.toggle_analysis_btn)

        analysis_layout.addWidget(QLabel("Depth:"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 20)
        self.depth_spin.setValue(8)
        analysis_layout.addWidget(self.depth_spin)

        self.get_hints_btn = QPushButton("Lấy Gợi Ý")
        self.get_hints_btn.clicked.connect(self._get_hints)
        analysis_layout.addWidget(self.get_hints_btn)

        analysis_layout.addStretch()
        control_layout.addLayout(analysis_layout)

        layout.addWidget(control_group)

        # Results table
        results_group = QGroupBox("Kết Quả Phân Tích")
        results_layout = QVBoxLayout(results_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Engine", "Protocol", "Đánh Giá", "Độ Sâu", "Nước Đi Tốt", "Nodes", "PV", "Trạng Thái"
        ])

        # Resize columns
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Engine name
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Protocol
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Evaluation
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Depth
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Best move
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Nodes
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # PV
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # Status

        self.results_table.setColumnWidth(0, 100)
        self.results_table.setColumnWidth(1, 60)   # Protocol
        self.results_table.setColumnWidth(2, 80)   # Evaluation
        self.results_table.setColumnWidth(3, 60)   # Depth
        self.results_table.setColumnWidth(4, 80)   # Best move
        self.results_table.setColumnWidth(5, 80)   # Nodes
        self.results_table.setColumnWidth(7, 80)   # Status

        # Double click to select move
        self.results_table.cellDoubleClicked.connect(
            self._on_cell_double_clicked)

        results_layout.addWidget(self.results_table)
        layout.addWidget(results_group)

        # Arrow display options
        arrow_group = QGroupBox("Hiển Thị Mũi Tên")
        arrow_layout = QHBoxLayout(arrow_group)

        self.show_arrows_cb = QCheckBox("Hiển thị mũi tên trên bàn cờ")
        self.show_arrows_cb.setChecked(True)
        self.show_arrows_cb.stateChanged.connect(self._update_arrows)
        arrow_layout.addWidget(self.show_arrows_cb)

        arrow_layout.addStretch()
        layout.addWidget(arrow_group)

        # Engine Log section
        log_group = QGroupBox("📋 Engine Logs")
        log_layout = QVBoxLayout(log_group)

        self.engine_log = QTextEdit()
        self.engine_log.setPlaceholderText(
            "Logs của các engines sẽ hiển thị ở đây...")
        self.engine_log.setFont(QFont("Consolas", 9))  # Font monospace
        self.engine_log.setMaximumHeight(150)  # Giới hạn chiều cao
        self.engine_log.setReadOnly(True)
        log_layout.addWidget(self.engine_log)

        # Clear log button
        clear_log_btn = QPushButton("🗑️ Clear Logs")
        clear_log_btn.clicked.connect(self._clear_logs)
        log_layout.addWidget(clear_log_btn)

        layout.addWidget(log_group)

    def _setup_connections(self):
        """Thiết lập connections cho UI"""
        # Enable/disable add button khi có path và name
        self.engine_path_edit.textChanged.connect(self._check_add_button_state)
        self.engine_name_edit.textChanged.connect(self._check_add_button_state)

    def _check_add_button_state(self):
        """Kiểm tra và enable/disable nút Add Engine"""
        has_path = bool(self.engine_path_edit.text().strip())
        has_name = bool(self.engine_name_edit.text().strip())
        self.add_engine_btn.setEnabled(has_path and has_name)

    def _browse_engine_file(self):
        """Browse để chọn file engine"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Chọn Engine Executable")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        # Filter cho executable files
        if os.name == 'nt':  # Windows
            file_dialog.setNameFilter(
                "Executable files (*.exe);;All files (*.*)")
        else:  # Linux/Mac
            file_dialog.setNameFilter("All files (*)")

        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                engine_path = selected_files[0]
                self.engine_path_edit.setText(engine_path)

                # Auto-generate engine name từ filename
                engine_filename = os.path.basename(engine_path)
                engine_name = os.path.splitext(engine_filename)[0]

                # Capitalize first letter
                engine_name = engine_name.replace(
                    '-', ' ').replace('_', ' ').title()

                if not self.engine_name_edit.text().strip():
                    self.engine_name_edit.setText(engine_name)

                print(f"📁 Đã chọn engine: {engine_path}")

    def _add_engine_from_path(self):
        """Thêm engine từ path đã chọn"""
        engine_path = self.engine_path_edit.text().strip()
        engine_name = self.engine_name_edit.text().strip()

        if not engine_path:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file engine!")
            return

        if not engine_name:
            # Auto generate name from filename
            engine_name = os.path.splitext(os.path.basename(engine_path))[0]
            self.engine_name_edit.setText(engine_name)

        if not os.path.exists(engine_path):
            QMessageBox.warning(
                self, "Lỗi", f"File engine không tồn tại:\n{engine_path}")
            return

        success = self.multi_engine_manager.add_engine(
            engine_name, engine_path)
        if success:
            self._log_message(f"✅ Đã thêm engine: {engine_name}")
            QMessageBox.information(
                self, "Thành công", f"✅ Đã thêm engine: {engine_name}")

            # Clear inputs
            self.engine_path_edit.clear()
            self.engine_name_edit.clear()
        else:
            self._log_message(f"❌ Không thể thêm engine: {engine_name}")
            QMessageBox.warning(
                self, "Lỗi", f"❌ Không thể thêm engine: {engine_name}")

    def _add_engine_from_path_direct(self, name: str, path: str):
        """Thêm engine trực tiếp (dùng cho test)"""
        success = self.multi_engine_manager.add_engine(name, path)
        if success:
            self._log_message(f"✅ Đã thêm engine: {name}")
            print(f"✅ Added engine: {name}")
        else:
            self._log_message(f"❌ Không thể thêm engine: {name}")
            print(f"❌ Failed to add engine: {name}")

    def _remove_selected_engine(self):
        """Xóa engine được chọn từ table"""
        current_row = self.results_table.currentRow()
        if current_row < 0:
            return

        engine_name_item = self.results_table.item(current_row, 0)
        if engine_name_item:
            engine_name = engine_name_item.text()
            self._log_message(f"🗑️ Đang xóa engine: {engine_name}")
            self.multi_engine_manager.remove_engine(engine_name)
            self._update_results_table()
            self._log_message(f"✅ Đã xóa engine: {engine_name}")

    def _toggle_analysis(self):
        """Toggle analysis state"""
        print(f"🔄 Toggle analysis - current state: {self.is_analysis_running}")
        if self.is_analysis_running:
            self._stop_analysis()
        else:
            self._start_analysis()
        print(f"🔄 Toggle analysis - new state: {self.is_analysis_running}")

    def _start_analysis(self):
        """Bắt đầu phân tích liên tục - LUÔN lấy FEN hiện tại"""
        active_engines = self.multi_engine_manager.get_active_engines()
        if not active_engines:
            QMessageBox.warning(
                self, "Lỗi", "❌ Chưa có engine nào được thêm!\nVui lòng thêm engine trước khi phân tích.")
            return

        # LUÔN LẤY FEN HIỆN TẠI từ main window - KHÔNG dùng cache cũ
        print("🔄 [MULTI-ENGINE] FORCE lấy FEN hiện tại từ main window...")
        current_fen, current_moves = self.get_current_position_from_main_window()

        if not current_fen:
            QMessageBox.warning(
                self, "Lỗi", "❌ Không thể lấy FEN hiện tại từ main window!\nVui lòng kiểm tra lại vị trí bàn cờ.")
            return

        # FORCE UPDATE current position - clear cache cũ
        print(f"🔄 [MULTI-ENGINE] CLEARING old cache...")
        print(
            f"🔄 [MULTI-ENGINE] Old FEN: {getattr(self, 'current_fen', 'None')}")
        print(f"🔄 [MULTI-ENGINE] New FEN: {current_fen}")

        self.current_fen = current_fen
        self.current_moves = current_moves or []

        print(
            f"🔍 Bắt đầu phân tích liên tục với {len(active_engines)} engines")
        print(f"📍 [MULTI-ENGINE] FEN THẬT SỰ HIỆN TẠI: {current_fen}")
        print(f"📝 [MULTI-ENGINE] Moves HIỆN TẠI: {current_moves}")

        # FORCE set position mới cho tất cả engines
        print("🔄 [MULTI-ENGINE] FORCE setting new position to all engines...")
        self.multi_engine_manager.set_position_all(current_fen, current_moves)

        # Đợi một chút để engines xử lý position
        import time
        time.sleep(0.1)

        # Bắt đầu infinite analysis VỚI FEN HIỆN TẠI
        print("🔄 [MULTI-ENGINE] Starting infinite analysis WITH CURRENT FEN...")
        self.multi_engine_manager.start_analysis_all(
            current_fen, current_moves)

        self.is_analysis_running = True
        self.toggle_analysis_btn.setText("⏹️ Dừng Phân Tích")

        # Start update timer
        self.update_timer.start()

        print("✅ Đã bắt đầu phân tích liên tục với FEN THẬT SỰ HIỆN TẠI")
        self._log_message(
            f"🔍 Bắt đầu phân tích với FEN: {current_fen[:30]}...")

    def _stop_analysis(self):
        """Dừng phân tích liên tục - THẬT SỰ TERMINATE ENGINES"""
        print("⏹️ FORCE stopping phân tích liên tục...")

        # Log danh sách engines sẽ dừng
        active_engines = self.multi_engine_manager.get_active_engines()
        print(f"🛑 Stopping {len(active_engines)} engines: {active_engines}")

        # THẬT SỰ FORCE STOP - terminate engine processes
        print("🛑 [MULTI-ENGINE] THẬT SỰ TERMINATE engine processes...")
        with self.multi_engine_manager.worker_lock:
            for worker in self.multi_engine_manager.workers.values():
                if worker.engine:
                    print(
                        f"🛑 [MULTI-ENGINE] Force terminating {worker.engine_name}...")
                    worker.engine.force_stop_analysis()

                    # Set worker status to stopped
                    with worker.result_lock:
                        worker.last_result['status'] = 'stopped'
                        worker.last_result['ignore_old_info'] = True

        # Stop analysis all (backup)
        self.multi_engine_manager.stop_analysis_all()

        # Update UI state
        self.is_analysis_running = False
        self.toggle_analysis_btn.setText("▶️ Bắt Đầu Phân Tích")

        # Stop update timer
        self.update_timer.stop()

        # Clear results to show stopped state
        self._clear_all_results()

        # Force update UI ngay lập tức để hiển thị trạng thái "stopped"
        self._update_display()

        # Log message to engine log
        self._log_message(
            "🛑 ĐÃ TERMINATE TẤT CẢ ENGINE PROCESSES - Engines đã dừng hoàn toàn!")

        print("✅ ĐÃ TERMINATE engine processes - không còn output nào nữa!")

    def _get_hints(self):
        """Lấy gợi ý từ tất cả engine"""
        print(f"🔍 DEBUG _get_hints: current_fen = {self.current_fen}")
        print(f"🔍 DEBUG _get_hints: current_moves = {self.current_moves}")

        active_engines = self.multi_engine_manager.get_active_engines()
        if not active_engines:
            QMessageBox.warning(
                self, "Lỗi", "❌ Chưa có engine nào được thêm!\nVui lòng thêm engine trước khi lấy gợi ý.")
            print("❌ Chưa có engine nào được thêm")
            return

        if not self.current_fen:
            # Thử lấy FEN từ main window
            print("⚠️ current_fen is None, trying to get from main window...")
            current_fen, current_moves = self.get_current_position_from_main_window()

            if current_fen:
                self.set_position(current_fen, current_moves)

            if not self.current_fen:
                QMessageBox.warning(
                    self, "Lỗi", "❌ Chưa có vị trí bàn cờ!\nVui lòng đặt vị trí bàn cờ trước.")
                print("❌ Chưa có vị trí bàn cờ")
                return

        depth = self.depth_spin.value()
        print(
            f"🤖 Yêu cầu gợi ý (depth {depth}) từ {len(active_engines)} engines")
        print(f"📋 Engines: {active_engines}")
        print(f"🎯 Position: {self.current_fen}")
        print(f"📝 Moves: {self.current_moves}")

        self.multi_engine_manager.set_position_all(
            self.current_fen, self.current_moves)
        self.multi_engine_manager.get_hint_all(depth)
        print(f"✅ Đã gửi yêu cầu gợi ý (depth {depth}) đến tất cả engine")

    def _update_display(self):
        """Update hiển thị kết quả"""
        self._update_results_table()
        self._update_arrows()
        self._update_analysis_info()

    def _update_results_table(self):
        """Update bảng kết quả"""
        active_engines = self.multi_engine_manager.get_active_engines()
        results = self.multi_engine_manager.get_results()

        self.results_table.setRowCount(len(active_engines))

        for row, engine_name in enumerate(active_engines):
            result = results.get(engine_name, {})

            # Engine name
            self.results_table.setItem(row, 0, QTableWidgetItem(engine_name))

            # Protocol
            protocol = result.get('protocol', 'unknown')
            protocol_item = QTableWidgetItem(protocol.upper())
            if protocol == "ucci":
                protocol_item.setToolTip("UCCI - Xiangqi protocol")
            elif protocol == "uci":
                protocol_item.setToolTip("UCI - Chess protocol")
            self.results_table.setItem(row, 1, protocol_item)

            # Evaluation
            eval_score = result.get('evaluation', 0.0)
            if eval_score == float('inf'):
                eval_text = "Chiến thắng"
            elif eval_score == float('-inf'):
                eval_text = "Thua"
            else:
                eval_text = f"{eval_score:+.2f}"
            self.results_table.setItem(row, 2, QTableWidgetItem(eval_text))

            # Depth
            depth = result.get('depth', 0)
            self.results_table.setItem(row, 3, QTableWidgetItem(str(depth)))

            # Best move
            bestmove = result.get('bestmove', '-')
            ponder = result.get('ponder', '')

            # Hiển thị cả bestmove và ponder
            if bestmove != '-' and ponder:
                move_text = f"{bestmove} (ponder: {ponder})"
            else:
                move_text = bestmove

            self.results_table.setItem(row, 4, QTableWidgetItem(move_text))

            # Nodes
            nodes = result.get('nodes', 0)
            nodes_text = f"{nodes:,}" if nodes > 0 else "-"
            self.results_table.setItem(row, 5, QTableWidgetItem(nodes_text))

            # Principal Variation
            pv = result.get('pv', [])
            pv_text = " ".join(pv[:5]) if pv else "-"  # Hiển thị 5 nước đầu
            self.results_table.setItem(row, 6, QTableWidgetItem(pv_text))

            # Status - hiển thị status thực tế từ engine
            engine_status = result.get('status', 'unknown')
            if engine_status == 'stopped':
                status = "⏹️ Đã dừng"
            elif engine_status == 'analyzing':
                status = "🔍 Đang phân tích"
            elif engine_status == 'ready':
                status = "✅ Sẵn sàng"
            elif engine_status == 'thinking':
                status = "🤔 Đang suy nghĩ"
            else:
                status = "❓ Không rõ"
            self.results_table.setItem(row, 7, QTableWidgetItem(status))

    def _update_arrows(self):
        """Update mũi tên trên bàn cờ với màu và style khác nhau"""
        if not self.show_arrows_cb.isChecked():
            self.engine_arrows_changed.emit({})
            return

        arrows_data = {}
        results = self.multi_engine_manager.get_results()

        if not results:
            return

        # Màu sắc cố định cho từng engine (giữ nguyên màu)
        base_colors = ['cyan', 'blue', 'green', 'orange',
                       'purple', 'brown', 'red', 'magenta']

        for i, (engine_name, result) in enumerate(results.items()):
            engine_arrows = []

            # Màu cơ bản cho engine này
            base_color = base_colors[i % len(base_colors)]

            # Bestmove (lượt hiện tại) - nét liền
            bestmove = result.get('bestmove')
            if bestmove and len(bestmove) >= 4:
                from_pos = bestmove[:2]
                to_pos = bestmove[2:4]

                engine_arrows.append({
                    'from': from_pos,
                    'to': to_pos,
                    'color': base_color,
                    'style': 'solid',
                    'opacity': 1.0,
                    'is_current_turn': True
                })

            # Ponder (lượt đối phương) - nét đứt
            ponder = result.get('ponder')
            if ponder and len(ponder) >= 4:
                from_pos = ponder[:2]
                to_pos = ponder[2:4]

                engine_arrows.append({
                    'from': from_pos,
                    'to': to_pos,
                    'color': base_color,
                    'style': 'dashed',
                    'opacity': 0.8,
                    'is_current_turn': False
                })

            if engine_arrows:
                arrows_data[engine_name] = engine_arrows

        if arrows_data:
            print(f"🏹 Updating arrows for {len(arrows_data)} engines")
            self.engine_arrows_changed.emit(arrows_data)

    def _update_analysis_info(self):
        """Update thông tin phân tích cho board widget"""
        results = self.multi_engine_manager.get_results()

        if not results:
            self.analysis_info_changed.emit({})
            return

        analysis_info = {}

        for engine_name, result in results.items():
            bestmove = result.get('bestmove', '')
            ponder = result.get('ponder', '')
            evaluation = result.get('evaluation', 0.0)
            depth = result.get('depth', 0)

            # Chỉ gửi info nếu có bestmove hợp lệ
            if bestmove and bestmove != 'none' and bestmove != '-':
                analysis_info[engine_name] = {
                    'bestmove': bestmove,
                    'ponder': ponder,
                    'evaluation': evaluation,
                    'depth': depth
                }

        if analysis_info:
            self.analysis_info_changed.emit(analysis_info)

    def _update_arrows_immediate(self):
        """Update arrows với throttling để tránh update quá thường xuyên"""
        if self.show_arrows_cb.isChecked():
            # Restart timer để delay update (throttling)
            self.arrow_update_timer.stop()
            self.arrow_update_timer.start(200)  # Delay 200ms

    def _get_move_player(self, move: str) -> str:
        """
        Xác định phe của nước đi dựa trên vị trí from

        Args:
            move: Nước đi dạng "e0e1"

        Returns:
            str: 'red' hoặc 'black'
        """
        if not move or len(move) < 2:
            return self.current_player

        from_pos = move[:2]
        try:
            from_row = int(from_pos[1])

            # Quân đỏ thường ở hàng 0-4, quân đen ở hàng 5-9
            # Nhưng tốt có thể qua sông nên cần check cẩn thận hơn
            if from_row <= 4:
                return 'red'
            else:
                return 'black'

        except (ValueError, IndexError):
            # Fallback về current player nếu không parse được
            return self.current_player

    def _on_cell_double_clicked(self, row: int, column: int):
        """Xử lý double click vào cell"""
        if column == 4:  # Best move column (đã shift vì thêm protocol column)
            engine_name_item = self.results_table.item(row, 0)
            bestmove_item = self.results_table.item(row, 4)

            if engine_name_item and bestmove_item:
                engine_name = engine_name_item.text()
                bestmove = bestmove_item.text()

                if bestmove != '-':
                    self.hint_selected.emit(engine_name, bestmove)
                    print(f"🎯 Chọn gợi ý từ {engine_name}: {bestmove}")

    def _clear_logs(self):
        """Clear engine logs"""
        self.engine_log.clear()
        print("🗑️ Cleared engine logs")

    def _clear_all_results(self):
        """Clear tất cả results UI và arrows - hiển thị trạng thái STOPPED"""
        try:
            print("🧹 [MULTI-ENGINE] Clearing all UI results and arrows...")

            # Clear arrows ngay lập tức
            if hasattr(self, 'engine_arrows'):
                self.engine_arrows.clear()
                self.engine_arrows_changed.emit({})  # Emit empty arrows
            else:
                # Emit empty arrows nếu chưa có engine_arrows
                self.engine_arrows_changed.emit({})

            # Clear results table và hiển thị trạng thái "STOPPED"
            active_engines = self.multi_engine_manager.get_active_engines()
            self.results_table.setRowCount(len(active_engines))

            for row, engine_name in enumerate(active_engines):
                # Engine name
                self.results_table.setItem(
                    row, 0, QTableWidgetItem(engine_name))

                # Protocol (giữ nguyên nếu có)
                self.results_table.setItem(row, 1, QTableWidgetItem("UCCI"))

                # Evaluation = STOPPED
                stopped_item = QTableWidgetItem("🛑 STOPPED")
                stopped_item.setToolTip("Engine đã dừng phân tích")
                self.results_table.setItem(row, 2, stopped_item)

                # Depth = 0
                self.results_table.setItem(row, 3, QTableWidgetItem("0"))

                # Best move = STOPPED
                self.results_table.setItem(
                    row, 4, QTableWidgetItem("🛑 STOPPED"))

                # Nodes = 0
                self.results_table.setItem(row, 5, QTableWidgetItem("0"))

            print("✅ [MULTI-ENGINE] Results table updated with STOPPED status")

            # Log message
            self._log_message(
                "🛑 TẤT CẢ ENGINES ĐÃ DỪNG - UI cleared và hiển thị trạng thái STOPPED")

            print(
                "✅ [MULTI-ENGINE] All UI results cleared and STOPPED status displayed")

        except Exception as e:
            print(f"❌ [MULTI-ENGINE] Error clearing UI results: {e}")

    def save_current_engines(self):
        """Lưu lại thông tin engines hiện tại"""
        try:
            self.saved_engines = []

            with self.multi_engine_manager.worker_lock:
                for name, worker in self.multi_engine_manager.workers.items():
                    engine_info = {
                        'name': name,
                        'path': worker.engine_path if hasattr(worker, 'engine_path') else None
                    }
                    self.saved_engines.append(engine_info)
                    print(
                        f"💾 [MULTI-ENGINE] Saved engine: {name} -> {engine_info['path']}")

            print(f"💾 [MULTI-ENGINE] Saved {len(self.saved_engines)} engines")
            self._log_message(f"💾 Saved {len(self.saved_engines)} engines")

        except Exception as e:
            print(f"❌ [MULTI-ENGINE] Error saving engines: {e}")
            self.saved_engines = []

    def restore_saved_engines(self):
        """Restore lại engines đã lưu"""
        try:
            if not hasattr(self, 'saved_engines') or not self.saved_engines:
                print("⚠️ [MULTI-ENGINE] No saved engines to restore")
                self._add_default_engines()  # Fallback
                return

            print(
                f"🔧 [MULTI-ENGINE] Restoring {len(self.saved_engines)} saved engines...")

            restored_count = 0
            for engine_info in self.saved_engines:
                name = engine_info.get('name')
                path = engine_info.get('path')

                if name and path:
                    if self.multi_engine_manager.add_engine(name, path):
                        print(f"✅ [MULTI-ENGINE] Restored engine: {name}")
                        self._log_message(f"✅ Restored engine: {name}")
                        restored_count += 1
                    else:
                        print(
                            f"❌ [MULTI-ENGINE] Failed to restore engine: {name}")
                        self._log_message(
                            f"❌ Failed to restore engine: {name}")
                else:
                    print(
                        f"⚠️ [MULTI-ENGINE] Invalid engine info: {engine_info}")

            # UI sẽ tự động update khi engines được add

            print(
                f"✅ [MULTI-ENGINE] Restored {restored_count}/{len(self.saved_engines)} engines")
            self._log_message(
                f"✅ Restored {restored_count}/{len(self.saved_engines)} engines")

        except Exception as e:
            print(f"❌ [MULTI-ENGINE] Error restoring engines: {e}")
            self._log_message(f"❌ Error restoring engines: {e}")
            # Fallback to default engines
            self._add_default_engines()

    def _add_default_engines(self):
        """Add lại default engines sau khi clear (fallback method)"""
        try:
            print("🔧 [MULTI-ENGINE] Adding default engines...")

            # Add Pikafish engine
            pikafish_path = "./engines/Pikafish/pikafish"
            if self.multi_engine_manager.add_engine("Pikafish", pikafish_path):
                print("✅ [MULTI-ENGINE] Added Pikafish engine")
                self._log_message("✅ Added Pikafish engine")
            else:
                print("❌ [MULTI-ENGINE] Failed to add Pikafish engine")
                self._log_message("❌ Failed to add Pikafish engine")

            # Add Fairy-Stockfish engine if exists
            fairy_path = "./engines/Fairy-Stockfish/fairy-stockfish"
            import os
            if os.path.exists(fairy_path):
                if self.multi_engine_manager.add_engine("Fairy-Stockfish", fairy_path):
                    print("✅ [MULTI-ENGINE] Added Fairy-Stockfish engine")
                    self._log_message("✅ Added Fairy-Stockfish engine")
                else:
                    print("❌ [MULTI-ENGINE] Failed to add Fairy-Stockfish engine")
                    self._log_message("❌ Failed to add Fairy-Stockfish engine")

            # UI sẽ tự động update khi engines được add

            print("✅ [MULTI-ENGINE] Default engines added")

        except Exception as e:
            print(f"❌ [MULTI-ENGINE] Error adding default engines: {e}")
            self._log_message(f"❌ Error adding default engines: {e}")

    def _log_message(self, message: str):
        """Thêm message vào engine log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"

        self.engine_log.append(formatted_message)

        # Auto scroll to bottom
        scrollbar = self.engine_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Cleanup khi đóng widget"""
        self._stop_analysis()
        self.multi_engine_manager.stop_all()
        super().closeEvent(event)

    def get_current_position_from_main_window(self):
        """Lấy position hiện tại từ main window - FORCE lấy FEN thật"""
        try:
            # Tìm main window qua QApplication
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if hasattr(widget, 'game_state') and hasattr(widget, 'convert_moves_to_engine_notation'):
                        # FORCE lấy FEN hiện tại thật sự
                        current_fen = widget.game_state.to_fen()
                        current_moves = widget.convert_moves_to_engine_notation(
                            widget.game_state.move_history)

                        print(f"🔄 [GET_POSITION] THẬT SỰ lấy từ main window:")
                        print(f"🔄 [GET_POSITION] Current FEN: {current_fen}")
                        print(
                            f"🔄 [GET_POSITION] Move count: {len(current_moves)}")
                        print(f"🔄 [GET_POSITION] Moves: {current_moves}")
                        print(
                            f"🔄 [GET_POSITION] Game state player: {getattr(widget.game_state, 'current_player', 'unknown')}")

                        # Validation
                        if not current_fen or current_fen.strip() == "":
                            print("❌ [GET_POSITION] FEN is empty!")
                            return None, None

                        if "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR" in current_fen:
                            print(
                                "⚠️ [GET_POSITION] Detected INITIAL position - this might be wrong!")

                        return current_fen, current_moves

            print("❌ [GET_POSITION] Could not find main window with game_state")
            return None, None
        except Exception as e:
            print(f"❌ [GET_POSITION] Lỗi khi lấy position từ main window: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def set_position(self, fen: str, moves: List[str] = None):
        """Đặt vị trí cho tất cả engine"""
        self.current_fen = fen
        self.current_moves = moves or []

        # Xác định lượt hiện tại từ số nước đã đi
        move_count = len(self.current_moves)
        self.current_player = 'red' if move_count % 2 == 0 else 'black'

        active_engines = self.multi_engine_manager.get_active_engines()
        print(
            f"📍 Multi-engine position updated: {len(active_engines)} engines, {len(self.current_moves)} moves")

        if active_engines:
            self.multi_engine_manager.set_position_all(fen, moves)
            # Logic restart analysis đã được xử lý trong EngineWorker._process_command
            # Không cần restart lại ở đây để tránh duplicate go infinite commands
        else:
            print("⚠️ [MULTI-ENGINE] Không có engine nào để cập nhật vị trí")

    def _on_engine_result_updated(self, engine_name: str, result: dict):
        """Slot nhận kết quả từ engine (thread-safe via Qt signals)"""
        bestmove = result.get('bestmove', 'none')
        ponder = result.get('ponder', '')
        evaluation = result.get('evaluation', 0)
        depth = result.get('depth', 0)
        status = result.get('status', 'unknown')

        # Log chi tiết kết quả
        if bestmove and bestmove != 'none':
            log_msg = f"🎯 {engine_name}: {bestmove}"
            if ponder:
                log_msg += f" (ponder: {ponder})"
            log_msg += f" (eval: {evaluation:.2f}, depth: {depth})"
            self._log_message(log_msg)

        # Log status changes
        if status in ['ready', 'failed', 'thinking', 'analyzing']:
            self._log_message(f"📊 {engine_name}: {status}")

        # Update sẽ được xử lý ngay lập tức để arrows nhanh hơn
        self._update_arrows_immediate()

    def reload_engines_with_new_position(self, fen: str, moves: List[str] = None):
        """Reload engines với position mới - XÓA TOÀN BỘ → LOAD LẠI → BẬT PHÂN TÍCH"""
        try:
            print(f"🔄 [MULTI-ENGINE] ===== XÓA & LOAD LẠI ENGINES =====")
            print(f"🔄 [MULTI-ENGINE] New FEN: {fen}")
            print(f"🔄 [MULTI-ENGINE] New moves: {moves}")

            # 1. LƯU LẠI danh sách engines hiện tại
            print("💾 [MULTI-ENGINE] Lưu lại danh sách engines...")
            self.save_current_engines()

            if not hasattr(self, 'saved_engines') or not self.saved_engines:
                print("⚠️ [MULTI-ENGINE] No engines to reload")
                return

            print(
                f"💾 [MULTI-ENGINE] Đã lưu {len(self.saved_engines)} engines: {[e['name'] for e in self.saved_engines]}")

            # 2. XÓA TOÀN BỘ engines khỏi danh sách
            print("🗑️ [MULTI-ENGINE] XÓA TOÀN BỘ engines...")
            self.multi_engine_manager.stop_all()  # Stop và clear tất cả

            # Clear UI
            self._clear_all_results()

            # Stop analysis UI state
            self.is_analysis_running = False
            self.toggle_analysis_btn.setText("▶️ Bắt Đầu Phân Tích")
            self.update_timer.stop()

            print("✅ [MULTI-ENGINE] Đã xóa toàn bộ engines")

            # 3. Đợi một chút để đảm bảo cleanup hoàn tất
            import time
            time.sleep(0.3)

            # 4. LOAD LẠI engines đã lưu
            print("🔄 [MULTI-ENGINE] LOAD LẠI engines...")
            self.restore_saved_engines()

            # 5. Đợi engines khởi động
            time.sleep(0.5)
            print("⏳ [MULTI-ENGINE] Đợi engines khởi động...")

            # 6. SET position mới cho tất cả engines
            print(f"📍 [MULTI-ENGINE] SET position mới cho engines...")
            self.current_fen = fen
            self.current_moves = moves or []
            self.multi_engine_manager.set_position_all(fen, moves)

            # 7. BẬT LẠI phân tích với position mới
            print("🚀 [MULTI-ENGINE] BẬT LẠI phân tích với position mới...")
            self.multi_engine_manager.start_analysis_all()
            self.is_analysis_running = True

            # 8. Update UI
            self.toggle_analysis_btn.setText("⏹️ Dừng Phân Tích")
            self.update_timer.start()

            active_engines = self.multi_engine_manager.get_active_engines()
            print(
                f"✅ [MULTI-ENGINE] Successfully XÓA & LOAD LẠI {len(active_engines)} engines")
            self._log_message(
                f"🔄 XÓA & LOAD LẠI {len(active_engines)} engines với position mới")

        except Exception as e:
            print(
                f"❌ [MULTI-ENGINE] Error trong quá trình xóa & load lại: {e}")
            import traceback
            traceback.print_exc()
            self._log_message(f"❌ Error xóa & load lại engines: {e}")
