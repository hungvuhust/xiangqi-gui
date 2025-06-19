# -*- coding: utf-8 -*-
"""
UCCI Protocol Implementation
Giao thức UCCI (Universal Chinese Chess Interface) cho cờ tướng
"""

import subprocess
import threading
import queue
import time
import traceback
from typing import Optional, List, Callable


class UCCIEngine:
    """Class để giao tiếp với engine cờ tướng qua giao thức UCCI"""

    def __init__(self, engine_path: str, protocol: str = "auto"):
        """
        Khởi tạo engine

        Args:
            engine_path: Đường dẫn đến file executable của engine
            protocol: "auto" để auto-detect, "ucci" cho cờ tướng, "uci" cho cờ vua
        """
        self.engine_path = engine_path
        self.protocol = protocol.lower()
        self.detected_protocol = None  # Protocol được detect
        self.process = None
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.is_running = False
        self.engine_thread = None
        self.protocol_detected = False  # Flag để biết đã detect xong protocol

        # Callback functions
        self.on_bestmove: Optional[Callable[[str], None]] = None
        self.on_info: Optional[Callable[[str], None]] = None

    def start(self) -> bool:
        """
        Khởi động engine

        Returns:
            True nếu khởi động thành công, False nếu thất bại
        """
        try:
            self.process = subprocess.Popen(
                self.engine_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0
            )

            self.is_running = True
            self.engine_thread = threading.Thread(
                target=self._engine_communication)
            self.engine_thread.daemon = True
            self.engine_thread.start()

            # Auto-detect protocol hoặc sử dụng protocol đã chỉ định
            if self.protocol == "auto":
                self._detect_protocol()
            else:
                # Sử dụng protocol đã chỉ định
                self.detected_protocol = self.protocol
                self.protocol_detected = True
                self._send_init_command()

            return True

        except Exception as e:
            print(f"Lỗi khởi động engine: {e}")
            return False

    def stop(self):
        """Dừng engine"""
        if self.is_running:
            self.send_command("quit")
            self.is_running = False

            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None

    def send_command(self, command: str):
        """
        Gửi lệnh đến engine

        Args:
            command: Lệnh UCCI cần gửi
        """
        if self.process and self.is_running:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                print(f"Gửi: {command}")
            except Exception as e:
                print(f"Lỗi gửi lệnh: {e}")

    def new_game(self):
        """Bắt đầu ván cờ mới"""
        protocol = self.detected_protocol or self.protocol
        if protocol == "ucci":
            self.send_command("uccinewgame")
        else:  # UCI
            self.send_command("ucinewgame")

    def set_position(self, fen: str, moves: List[str] = None):
        """
        Thiết lập vị trí bàn cờ

        Args:
            fen: Chuỗi FEN mô tả vị trí
            moves: Danh sách nước đi từ vị trí FEN
        """
        command = f"position fen {fen}"
        if moves:
            command += " moves " + " ".join(moves)
        self.send_command(command)

    def go(self, depth: int = None, time_ms: int = None):
        """
        Yêu cầu engine tìm nước đi tốt nhất

        Args:
            depth: Độ sâu tìm kiếm
            time_ms: Thời gian suy nghĩ (milliseconds)
        """
        command = "go"
        if depth:
            command += f" depth {depth}"
        if time_ms:
            command += f" movetime {time_ms}"

        self.send_command(command)

    def go_infinite(self):
        """
        Yêu cầu engine phân tích liên tục (infinite analysis)
        """
        self.send_command("go infinite")

    def stop_search(self):
        """Dừng tìm kiếm"""
        self.send_command("stop")

    def make_move(self, move: str):
        """
        Thông báo cho engine về nước đi vừa thực hiện

        Args:
            move: Nước đi dạng UCCI (e.g., "h2e2")
        """
        # Engine sẽ nhận thông tin này qua set_position với moves history
        pass

    def get_hint(self, depth: int = 8):
        """
        Yêu cầu engine gợi ý nước đi

        Args:
            depth: Độ sâu tìm kiếm để gợi ý
        """
        self.go(depth=depth)

    def _detect_protocol(self):
        """Auto-detect protocol của engine"""
        print(f"🔍 Đang detect protocol cho engine: {self.engine_path}")

        # Thử UCCI trước (vì đây là app cờ tướng)
        import time
        time.sleep(0.1)  # Đợi engine khởi động

        print("🧪 Thử UCCI protocol...")
        self.send_command("ucci")

        # Đợi phản hồi trong 2 giây
        import threading
        timer = threading.Timer(2.0, self._try_uci_protocol)
        timer.start()

    def _try_uci_protocol(self):
        """Thử UCI protocol nếu UCCI không phản hồi"""
        if not self.protocol_detected:
            print("🧪 UCCI không phản hồi, thử UCI protocol...")
            self.send_command("uci")

            # Timeout cuối cùng
            import threading
            timer = threading.Timer(2.0, self._protocol_detection_failed)
            timer.start()

    def _protocol_detection_failed(self):
        """Xử lý khi không detect được protocol"""
        if not self.protocol_detected:
            print("❌ Không thể detect protocol, mặc định dùng UCCI")
            self.detected_protocol = "ucci"
            self.protocol_detected = True

    def _send_init_command(self):
        """Gửi lệnh khởi tạo theo protocol đã detect"""
        if self.detected_protocol == "ucci":
            self.send_command("ucci")
            print("✅ Sử dụng UCCI protocol")
        else:  # UCI
            self.send_command("uci")
            print("✅ Sử dụng UCI protocol")

    def get_detected_protocol(self) -> str:
        """Lấy protocol đã được detect"""
        return self.detected_protocol or "unknown"

    def _engine_communication(self):
        """Thread xử lý giao tiếp với engine"""
        while self.is_running and self.process:
            try:
                if self.process.poll() is not None:
                    # Engine đã thoát
                    print("Engine process đã kết thúc")
                    break

                line = self.process.stdout.readline()
                if not line:
                    continue

                line = line.strip()
                if line:
                    print(f"Nhận: {line}")
                    self._process_engine_output(line)

            except Exception as e:
                print(f"Lỗi giao tiếp engine: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                break

        print("Engine communication thread kết thúc")
        self.is_running = False

    def _process_engine_output(self, line: str):
        """
        Xử lý output từ engine

        Args:
            line: Dòng output từ engine
        """
        parts = line.split()
        if not parts:
            return

        command = parts[0]

        if command == "ucciok":
            print("✅ Engine hỗ trợ UCCI protocol")
            if not self.protocol_detected:
                self.detected_protocol = "ucci"
                self.protocol_detected = True

        elif command == "uciok":
            print("✅ Engine hỗ trợ UCI protocol")
            if not self.protocol_detected:
                self.detected_protocol = "uci"
                self.protocol_detected = True

        elif command == "readyok":
            print("Engine đã ready")

        elif command == "bestmove":
            if len(parts) >= 2:
                # Gửi toàn bộ dòng bestmove để parse cả bestmove và ponder
                if self.on_bestmove:
                    try:
                        # Gửi toàn bộ dòng thay vì chỉ move
                        self.on_bestmove(line)
                    except Exception as e:
                        print(f"Lỗi trong callback on_bestmove: {e}")
                        print(f"Traceback: {traceback.format_exc()}")

        elif command == "info":
            if self.on_info:
                try:
                    self.on_info(line)
                except Exception as e:
                    print(f"Lỗi trong callback on_info: {e}")
                    print(f"Traceback: {traceback.format_exc()}")

        elif command == "id":
            print(f"Engine info: {' '.join(parts[1:])}")


class UCCIEngineManager:
    """Manager để quản lý nhiều engine"""

    def __init__(self):
        self.engines = {}
        self.current_engine = None
        self.protocol = "auto"  # Tự động detect protocol

    def set_protocol(self, protocol: str):
        """
        Đặt protocol sử dụng (deprecated - sử dụng auto-detection)

        Args:
            protocol: "ucci", "uci", hoặc "auto" (khuyến nghị)
        """
        self.protocol = protocol.lower()
        if protocol == "auto":
            print("✅ Sử dụng auto-detection protocol cho engines")
        else:
            print(
                f"⚠️ Manual protocol đã được đặt thành: {self.protocol.upper()}")
            print("💡 Khuyến nghị sử dụng 'auto' để tự động detect protocol")

    def get_protocol(self) -> str:
        """Lấy protocol hiện tại"""
        return self.protocol

    def add_engine(self, name: str, path: str) -> bool:
        """
        Thêm engine mới

        Args:
            name: Tên engine
            path: Đường dẫn đến engine

        Returns:
            True nếu thành công
        """
        engine = UCCIEngine(path, self.protocol)
        if engine.start():
            self.engines[name] = engine
            return True
        return False

    def set_current_engine(self, name: str) -> bool:
        """
        Chọn engine hiện tại

        Args:
            name: Tên engine

        Returns:
            True nếu thành công
        """
        if name in self.engines:
            self.current_engine = self.engines[name]
            return True
        return False

    def get_current_engine(self) -> Optional[UCCIEngine]:
        """Lấy engine hiện tại"""
        return self.current_engine

    def stop_all_engines(self):
        """Dừng tất cả engine"""
        for engine in self.engines.values():
            engine.stop()
        self.engines.clear()
        self.current_engine = None


class MultiEngineManager:
    """Manager để quản lý và chạy nhiều engine cùng lúc"""

    def __init__(self):
        self.active_engines = {}  # {name: UCCIEngine}
        self.engine_results = {}  # {name: {'bestmove': str, 'evaluation': float, 'depth': int}}
        self.protocol = "auto"  # Tự động detect protocol
        self.position_fen = None
        self.position_moves = []

        # Callbacks cho từng engine
        self.on_engine_result = None  # Callback khi có kết quả từ engine

    def set_protocol(self, protocol: str):
        """Đặt protocol cho tất cả engine (deprecated - sử dụng auto-detection)"""
        self.protocol = protocol.lower()
        if protocol == "auto":
            print("✅ MultiEngine sử dụng auto-detection protocol")
        else:
            print(f"⚠️ MultiEngine manual protocol: {self.protocol.upper()}")
            print("💡 Khuyến nghị sử dụng 'auto' để tự động detect protocol")

    def add_engine(self, name: str, path: str, auto_start: bool = True) -> bool:
        """
        Thêm engine vào danh sách active

        Args:
            name: Tên engine
            path: Đường dẫn engine
            auto_start: Tự động start engine

        Returns:
            bool: True nếu thành công
        """
        try:
            # Sử dụng auto-detect protocol
            engine = UCCIEngine(path, "auto")

            # Setup callbacks cho engine này
            engine.on_bestmove = lambda line, engine_name=name: self._handle_engine_bestmove(
                engine_name, line)
            engine.on_info = lambda line, engine_name=name: self._handle_engine_info(
                engine_name, line)

            if auto_start and engine.start():
                self.active_engines[name] = engine
                self.engine_results[name] = {
                    'bestmove': None,
                    'evaluation': 0.0,
                    'depth': 0,
                    'nodes': 0,
                    'pv': [],
                    'protocol': 'detecting...'  # Thêm thông tin protocol
                }

                # Đợi một chút để protocol được detect
                import threading

                def update_protocol():
                    import time
                    time.sleep(3)  # Đợi 3 giây
                    if name in self.engine_results:
                        detected = engine.get_detected_protocol()
                        self.engine_results[name]['protocol'] = detected
                        print(f"✓ Engine {name} detected protocol: {detected}")

                threading.Thread(target=update_protocol, daemon=True).start()
                print(f"✓ Đã thêm engine: {name} (auto-detecting protocol...)")
                return True
            else:
                print(f"❌ Không thể start engine: {name}")
                return False

        except Exception as e:
            print(f"❌ Lỗi thêm engine {name}: {e}")
            return False

    def remove_engine(self, name: str):
        """Xóa engine khỏi danh sách active"""
        if name in self.active_engines:
            self.active_engines[name].stop()
            del self.active_engines[name]
            if name in self.engine_results:
                del self.engine_results[name]
            print(f"✓ Đã xóa engine: {name}")

    def get_active_engines(self) -> list:
        """Lấy danh sách tên engine đang active"""
        return list(self.active_engines.keys())

    def set_position_all(self, fen: str, moves: List[str] = None):
        """Đặt position cho tất cả engine"""
        self.position_fen = fen
        self.position_moves = moves or []

        for name, engine in self.active_engines.items():
            try:
                engine.set_position(fen, moves)
                print(f"✓ Đã set position cho {name}")
            except Exception as e:
                print(f"❌ Lỗi set position cho {name}: {e}")

    def start_analysis_all(self):
        """Bắt đầu analysis cho tất cả engine"""
        for name, engine in self.active_engines.items():
            try:
                engine.go_infinite()
                print(f"🔍 Bắt đầu analysis: {name}")
            except Exception as e:
                print(f"❌ Lỗi start analysis {name}: {e}")

    def stop_analysis_all(self):
        """Dừng analysis cho tất cả engine"""
        for name, engine in self.active_engines.items():
            try:
                engine.stop_search()
                print(f"⏹️ Dừng analysis: {name}")
            except Exception as e:
                print(f"❌ Lỗi stop analysis {name}: {e}")

    def get_hint_all(self, depth: int = 8):
        """Yêu cầu hint từ tất cả engine"""
        for name, engine in self.active_engines.items():
            try:
                engine.get_hint(depth)
                print(f"🤖 Yêu cầu hint từ {name}")
            except Exception as e:
                print(f"❌ Lỗi get hint {name}: {e}")

    def get_results(self) -> dict:
        """Lấy kết quả từ tất cả engine"""
        return self.engine_results.copy()

    def stop_all(self):
        """Dừng tất cả engine"""
        for name in list(self.active_engines.keys()):
            self.remove_engine(name)

    def _handle_engine_bestmove(self, engine_name: str, bestmove_line: str):
        """Xử lý bestmove từ engine"""
        try:
            parts = bestmove_line.split()
            if len(parts) >= 2:
                bestmove = parts[1]
                self.engine_results[engine_name]['bestmove'] = bestmove

                # Parse ponder move nếu có
                if len(parts) >= 4 and parts[2] == "ponder":
                    ponder = parts[3]
                    self.engine_results[engine_name]['ponder'] = ponder

                print(f"🎯 {engine_name} bestmove: {bestmove}")

                # Callback cho UI
                if self.on_engine_result:
                    self.on_engine_result(
                        engine_name, 'bestmove', self.engine_results[engine_name])

        except Exception as e:
            print(f"❌ Lỗi parse bestmove từ {engine_name}: {e}")

    def _handle_engine_info(self, engine_name: str, info_line: str):
        """Xử lý info từ engine"""
        try:
            parts = info_line.split()

            # Parse các thông tin từ info line
            i = 1  # Bỏ qua "info"
            while i < len(parts):
                if parts[i] == "depth" and i + 1 < len(parts):
                    self.engine_results[engine_name]['depth'] = int(
                        parts[i + 1])
                    i += 2
                elif parts[i] == "score" and i + 2 < len(parts):
                    if parts[i + 1] == "cp":
                        # Centipawn score
                        score = int(parts[i + 2]) / 100.0
                        self.engine_results[engine_name]['evaluation'] = score
                        i += 3
                    elif parts[i + 1] == "mate":
                        # Mate score
                        mate_moves = int(parts[i + 2])
                        self.engine_results[engine_name]['evaluation'] = float(
                            'inf') if mate_moves > 0 else float('-inf')
                        i += 3
                    else:
                        i += 1
                elif parts[i] == "nodes" and i + 1 < len(parts):
                    self.engine_results[engine_name]['nodes'] = int(
                        parts[i + 1])
                    i += 2
                elif parts[i] == "pv":
                    # Principal variation
                    pv = parts[i + 1:]
                    self.engine_results[engine_name]['pv'] = pv
                    break
                else:
                    i += 1

            # Callback cho UI nếu có depth và evaluation
            if (self.engine_results[engine_name]['depth'] > 0 and
                    self.on_engine_result):
                self.on_engine_result(
                    engine_name, 'info', self.engine_results[engine_name])

        except Exception as e:
            print(f"❌ Lỗi parse info từ {engine_name}: {e}")
